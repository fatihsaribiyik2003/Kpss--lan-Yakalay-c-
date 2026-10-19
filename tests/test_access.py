import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from watcher import access
from watcher.core import Store, Engine, today


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.key=Ed25519PrivateKey.generate()
        self.public=self.key.public_key().public_bytes_raw().hex()
        self.patcher=patch('watcher.access.PUBLIC_KEY_HEX',self.public)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.store=Store(Path(self.temp.name)/'data')
        self.engine=Engine(self.store)
        self.addCleanup(self.close_log)

    def close_log(self):
        for handler in self.engine.log.handlers[:]:
            handler.close()
            self.engine.log.removeHandler(handler)

    def test_default_window_is_7_days_and_legacy_start_is_ignored(self):
        self.store.set_setting('start_date','2000-01-01')
        self.assertEqual(self.store.scan_days(),7)
        self.assertEqual(self.store.scan_start(),today()-dt.timedelta(days=6))

    def test_normal_user_cannot_select_more_than_7(self):
        for days in [0,-1,True,'7',8,90]:
            with self.assertRaises((ValueError,PermissionError)):
                self.store.set_scan_days(days)
        self.store.set_scan_days(1)
        self.assertEqual(self.store.scan_start(),today())

    def test_direct_database_edit_does_not_unlock_history(self):
        self.store.set_setting('scan_days',365)
        self.assertEqual(self.store.scan_days(),7)

    def test_valid_owner_grant_persists_after_restart(self):
        self.store.set_scan_days(90,self.key)
        reopened=Store(self.store.directory)
        self.assertEqual(reopened.scan_days(),90)
        self.store.set_setting('scan_days',91)
        self.assertEqual(self.store.scan_days(),7)

    def test_forged_or_foreign_grants_are_rejected(self):
        with self.assertRaises(PermissionError):
            self.store.set_scan_days(90,Ed25519PrivateKey.generate())
        self.store.set_scan_days(90,self.key)
        grant=self.store.setting('admin_grant')
        grant['payload']['days']=365
        self.store.set_setting('admin_grant',grant)
        self.store.set_setting('scan_days',365)
        self.assertEqual(self.store.scan_days(),7)
        self.store.set_scan_days(90,self.key)
        other=Store(Path(self.temp.name)/'other')
        other.set_setting('scan_days',90)
        other.set_setting('admin_grant',self.store.setting('admin_grant'))
        self.assertEqual(other.scan_days(),7)
        with patch('watcher.access.machine_identity',return_value='other-device'):
            self.assertEqual(self.store.scan_days(),7)

    def test_locking_revokes_persisted_extended_range(self):
        self.store.set_scan_days(365,self.key)
        self.store.set_scan_days(7)
        self.assertIsNone(self.store.setting('admin_grant'))
        self.assertEqual(self.store.scan_days(),7)

    def test_old_pending_and_error_documents_are_not_downloaded(self):
        old=(today()-dt.timedelta(days=20)).isoformat()
        with self.store.connect() as db:
            for status in ['pending','error']:
                db.execute('INSERT INTO documents(url,day,title,status) VALUES(?,?,?,?)',
                           ('https://www.resmigazete.gov.tr/'+status+'.pdf',old,'Eski ilan',status))
        with patch.object(self.engine,'fetch',side_effect=AssertionError('Aralık dışı indirme')) as fetch:
            self.engine.drain()
            self.engine.discover(today()-dt.timedelta(days=20))
        fetch.assert_not_called()
        self.store.set_scan_days(30,self.key)
        with patch.object(self.engine,'process',side_effect=lambda doc:self.mark_done(doc['id'])) as process:
            self.engine.drain()
        self.assertEqual(process.call_count,2)

    def mark_done(self,doc_id):
        with self.store.connect() as db:
            db.execute("UPDATE documents SET status='done' WHERE id=?",(doc_id,))

    def test_cycle_does_not_expand_to_old_pinned_start(self):
        self.store.set_setting('start_date','2000-01-01')
        self.store.set_scan_days(3)
        with patch.object(self.engine,'discover') as discover:
            self.engine.cycle()
        self.assertEqual([call.args[0] for call in discover.call_args_list],
                         [today()-dt.timedelta(days=i) for i in range(3)])

    def test_scan_window_rolls_with_current_day(self):
        self.store.set_scan_days(2)
        next_day=today()+dt.timedelta(days=1)
        with patch('watcher.core.today',return_value=next_day):
            self.assertEqual(self.store.scan_start(),next_day-dt.timedelta(days=1))

    def test_range_shrinks_during_cycle(self):
        visits=[]
        def discover(day):
            visits.append(day)
            self.store.set_scan_days(1)
        with patch.object(self.engine,'discover',side_effect=discover):
            self.engine.cycle()
        self.assertEqual(visits,[today()])

    def test_current_pdf_stops_at_page_boundary_when_range_shrinks(self):
        import pymupdf
        pdf=pymupdf.open()
        pdf.new_page()
        pdf.new_page()
        path=Path(self.temp.name)/'two-pages.pdf'
        pdf.save(path)
        yesterday=(today()-dt.timedelta(days=1)).isoformat()
        with self.store.connect() as db:
            db.execute('INSERT INTO documents(url,day,title,path) VALUES(?,?,?,?)',
                       ('https://www.resmigazete.gov.tr/test.pdf',yesterday,'Eski PDF',str(path)))
        def read_page(page):
            self.store.set_scan_days(1)
            return 'KPSS','metin','ok'
        with patch.object(self.engine.reader,'page',side_effect=read_page) as reader:
            self.engine.drain()
        self.assertEqual(reader.call_count,1)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT status FROM documents').fetchone()[0],'pending')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM pages').fetchone()[0],1)

    def test_client_cannot_create_owner_vault(self):
        vault=access.OwnerVault(Path(self.temp.name)/'empty-vault')
        self.assertFalse(vault.available())
        with self.assertRaises(PermissionError):
            vault.create_password('test-password-only-123')

    def test_owner_password_encryption_and_wrong_password(self):
        directory=Path(self.temp.name)/'owner'
        directory.mkdir()
        (directory/'owner.json').write_text(json.dumps({'public_key':self.public}),'utf-8')
        (directory/'owner-bootstrap.dpapi').write_bytes(self.key.private_bytes_raw())
        vault=access.OwnerVault(directory)
        with patch('watcher.access.dpapi',side_effect=lambda data,**kwargs:data):
            with self.assertRaises(ValueError):
                vault.create_password('short')
            vault.create_password('test-password-only-123')
        self.assertFalse(vault.bootstrap.exists())
        self.assertIn(b'ENCRYPTED PRIVATE KEY',vault.pem.read_bytes())
        metadata=json.loads((directory/'owner.json').read_text('utf-8'))
        self.assertEqual(metadata['password_hash']['algorithm'],'pbkdf2-sha256')
        self.assertNotIn('test-password-only-123',(directory/'owner.json').read_text('utf-8'))
        with self.assertRaises(ValueError):
            vault.unlock('incorrect-password')
        self.assertEqual(vault.unlock('test-password-only-123').public_key().public_bytes_raw().hex(),self.public)

    def test_password_hash_uses_unique_salt_and_rejects_wrong_password(self):
        first=access.password_record('demo1234')
        second=access.password_record('demo1234')
        self.assertNotEqual(first['salt'],second['salt'])
        self.assertNotEqual(first['digest'],second['digest'])
        self.assertTrue(access.verify_password('demo1234',first))
        self.assertFalse(access.verify_password('incorrect',first))
        self.assertFalse(access.verify_password('demo1234',{'algorithm':'plain'}))

    def test_legacy_vault_migrates_and_forged_hash_cannot_unlock_key(self):
        directory=Path(self.temp.name)/'legacy-owner'
        directory.mkdir()
        metadata_path=directory/'owner.json'
        metadata_path.write_text(json.dumps({'public_key':self.public}),'utf-8')
        encrypted=self.key.private_bytes(access.serialization.Encoding.PEM,
                  access.serialization.PrivateFormat.PKCS8,
                  access.serialization.BestAvailableEncryption(b'legacy-test-password'))
        (directory/'owner-private.pem').write_bytes(encrypted)
        vault=access.OwnerVault(directory)
        vault.unlock('legacy-test-password')
        metadata=json.loads(metadata_path.read_text('utf-8'))
        self.assertTrue(access.verify_password('legacy-test-password',metadata['password_hash']))
        metadata['password_hash']=access.password_record('different-test-password')
        metadata_path.write_text(json.dumps(metadata),'utf-8')
        with self.assertRaises(ValueError):
            vault.unlock('different-test-password')


if __name__=='__main__':
    unittest.main()
