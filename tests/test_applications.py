import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf
from watcher.core import Store,Engine,today
from watcher.candidate import listing_matches


class ApplicationTests(unittest.TestCase):
    def test_tracking_persists_across_restart_profile_and_scan_range_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            s=Store(directory)
            day=(today()-dt.timedelta(days=100)).isoformat()
            with s.connect() as db:
                doc=db.execute('INSERT INTO documents(url,day,title) VALUES(?,?,?)',('https://example.org/old.pdf',day,'Eski ilan')).lastrowid
            self.assertFalse(listing_matches(s.listing_results()[0],'applied'))
            s.set_applied(doc)
            stamp=s.listing_results()[0]['applied_at']
            s.set_applied(doc)
            self.assertEqual(s.listing_results()[0]['applied_at'],stamp)
            s.set_scan_days(1)
            profile=s.setting('candidate_profile');profile['has_kpss']=False
            s.set_setting('candidate_profile',profile)
            rows=Store(directory).listing_results()
            self.assertTrue(listing_matches(rows[0],'applied','Mühendis / bilişim'))
            self.assertEqual(rows[0]['applied_at'],stamp)
            self.assertTrue(listing_matches(rows[0],'applied',query='ESKİ'))
            self.assertFalse(listing_matches(rows[0],'applied',query='başka'))
            s.set_applied(doc,False)
            self.assertFalse(listing_matches(s.listing_results()[0],'applied'))
            self.assertEqual(len(s.listing_results()),1)
            with self.assertRaises(ValueError):
                s.set_applied(9999)

    def test_native_order_migration_preserves_ocr_and_application_without_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            s=Store(directory)
            pdf=Path(directory)/'pdf'/'saved.pdf'
            with pymupdf.open() as document:
                page=document.new_page()
                page.insert_text((50,60),'NATIVE ORIGINAL ORDER')
                document.save(pdf)
            with s.connect() as db:
                doc=db.execute("INSERT INTO documents(url,day,title,status,hash,path) VALUES(?,?,?,'done','hash',?)",('https://example.org/x.pdf',today().isoformat(),'OCR test',str(pdf))).lastrowid
                db.execute('INSERT INTO pages VALUES(?,?,?,?,?)',('hash',1,'OCR INFORMATION','OCR','ok'))
            s.set_applied(doc)
            engine=Engine(s)
            try:
                with patch.object(engine,'fetch',side_effect=AssertionError('No fetch')),patch.object(engine.reader,'page',side_effect=AssertionError('No OCR')):
                    engine.refresh_text_order()
                    engine.reindex()
                with s.connect() as db:
                    text=db.execute('SELECT text FROM pages').fetchone()[0]
                self.assertIn('NATIVE ORIGINAL ORDER',text)
                self.assertIn('OCR INFORMATION',text)
                self.assertEqual(text.count('NATIVE ORIGINAL ORDER'),1)
                self.assertTrue(s.listing_results()[0]['applied_at'])
            finally:
                for handler in engine.log.handlers[:]:
                    handler.close();engine.log.removeHandler(handler)
