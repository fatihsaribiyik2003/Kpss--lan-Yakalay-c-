import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf

from watcher.core import Store, Engine, PDFLinks, matches, today


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name)
        self.store.set_setting('start_date',today().isoformat())
        self.engine=Engine(self.store)
        self.addCleanup(self.close_log)

    def close_log(self):
        for handler in self.engine.log.handlers[:]:
            handler.close()
            self.engine.log.removeHandler(handler)

    def pdf(self):
        pdf=pymupdf.open()
        p=pdf.new_page()
        p.insert_text((40,60),'KPSS bilgisayar yazilim lisans ' * 8)
        return pdf.tobytes()

    def test_turkish_and_inflections(self):
        hits=matches('BİLİŞİM personeli, Bilgisayarın, YAZILIM, lisans mezunu KPSS', ['bilişim','bilgisayar','yazılım','lisans','KPSS'])
        self.assertEqual({h['term'] for h in hits},{'bilişim','bilgisayar','yazılım','lisans','KPSS'})
        self.assertFalse(matches('önlisans akademikpss',['lisans','KPSS']))

    def test_links_only_official_pdf(self):
        parser=PDFLinks('https://www.resmigazete.gov.tr/ilanlar/a.htm')
        parser.feed('<a href="a.pdf">Kurum &amp; birim</a><a href="https://evil.test/a.pdf">x</a>')
        self.assertEqual(parser.links,[('https://www.resmigazete.gov.tr/ilanlar/a.pdf','Kurum & birim')])

    def test_daily_discovery_and_second_run_does_not_download_pdf(self):
        pdf=self.pdf()
        calls=[]
        def fetch(url,*args):
            calls.append(url)
            return pdf if url.endswith('.pdf') else b'<a href="1.pdf">Kurum</a>'
        with patch.object(self.engine,'fetch',side_effect=fetch):
            self.engine.cycle()
            self.engine.cycle()
        self.assertEqual(sum(u.endswith('.pdf') for u in calls),1)
        self.assertEqual(len(self.store.results()),1)
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT status FROM documents').fetchone()[0],'done')

    def test_identical_pdf_at_two_urls_uses_page_cache(self):
        day=today().isoformat()
        with self.store.connect() as db:
            for suffix in ['a','b']:
                db.execute('INSERT INTO documents(url,day,title) VALUES(?,?,?)',('https://www.resmigazete.gov.tr/'+suffix+'.pdf',day,suffix))
        with patch.object(self.engine,'fetch',return_value=self.pdf()),patch.object(self.engine.reader,'page',return_value=('KPSS yazilim','metin','ok')) as reader:
            self.engine.drain()
        self.assertEqual(reader.call_count,1)
        self.assertEqual(len(self.store.results()),2)

    def test_bad_response_is_retryable_and_never_no_match(self):
        with self.store.connect() as db:
            db.execute('INSERT INTO documents(url,day,title) VALUES(?,?,?)',('https://www.resmigazete.gov.tr/a.pdf',today().isoformat(),'a'))
        with patch.object(self.engine,'fetch',return_value=b'Access denied'):
            self.engine.drain()
        with self.store.connect() as db:
            row=db.execute('SELECT * FROM documents').fetchone()
        self.assertEqual(row['status'],'error')
        self.assertGreater(row['retry'],0)

    def test_low_confidence_remains_visible_as_partial(self):
        with self.store.connect() as db:
            db.execute('INSERT INTO documents(url,day,title) VALUES(?,?,?)',('https://www.resmigazete.gov.tr/a.pdf',today().isoformat(),'a'))
        with patch.object(self.engine,'fetch',return_value=self.pdf()),patch.object(self.engine.reader,'page',return_value=('KPSS','OCR','review')):
            self.engine.drain()
        self.assertEqual(self.store.results()[0]['status'],'partial')
        self.assertEqual(len(self.store.failures()),1)

    def test_keyword_changes_reuse_text_without_reading_pdf(self):
        with self.store.connect() as db:
            db.execute('INSERT INTO documents(url,day,title) VALUES(?,?,?)',('https://www.resmigazete.gov.tr/a.pdf',today().isoformat(),'a'))
        with patch.object(self.engine,'fetch',return_value=self.pdf()):
            self.engine.drain()
        self.store.set_setting('terms',['yokkelime'])
        with patch.object(self.engine,'fetch',side_effect=AssertionError('Yeniden indirme olmamalı')):
            self.engine.reindex()
        self.assertEqual(len(self.store.results()),0)

    def test_interrupted_document_continues_from_cached_page(self):
        import hashlib
        pdf=pymupdf.open()
        pdf.new_page().insert_text((40,60),'KPSS ' * 30)
        pdf.new_page().insert_text((40,60),'bilgisayar ' * 30)
        content=pdf.tobytes()
        digest=hashlib.sha256(content).hexdigest()
        path=Path(self.temp.name)/'resume.pdf'
        path.write_bytes(content)
        with self.store.connect() as db:
            db.execute("INSERT INTO documents(url,day,title,status,path) VALUES(?,?,?,'processing',?)",('https://www.resmigazete.gov.tr/a.pdf',today().isoformat(),'Yarım kalan',str(path)))
            db.execute('INSERT INTO pages VALUES(?,?,?,?,?)',(digest,1,'KPSS','metin','ok'))
        with patch.object(self.engine,'discover'),patch.object(self.engine.reader,'page',return_value=('bilgisayar','metin','ok')) as reader:
            self.engine.cycle()
        self.assertEqual(reader.call_count,1)
        self.assertEqual(self.store.results()[0]['status'],'done')

    def test_successful_old_day_is_not_downloaded_again(self):
        old=today()-dt.timedelta(days=10)
        with self.store.connect() as db:
            db.execute('INSERT INTO days VALUES(?,?,?,?,?)',(old.isoformat(),'done',0,0,None))
        with patch.object(self.engine,'fetch',side_effect=AssertionError('Eski tamamlanmış dizin yeniden okunmamalı')) as fetch:
            self.engine.discover(old)
        fetch.assert_not_called()

    def test_calendar_only_marks_days_with_all_pdfs_scanned(self):
        with self.store.connect() as db:
            for day in ['2026-10-16','2026-10-17','2026-10-18','2026-10-19']:
                db.execute('INSERT INTO days VALUES(?,?,?,?,?)',(day,'done',0,0,None))
            for day,status in [('2026-10-16','done'),('2026-10-17','done'),
                               ('2026-10-17','pending'),('2026-10-18','partial'),('2026-10-18','error')]:
                db.execute('INSERT INTO documents(url,day,title,status) VALUES(?,?,?,?)',(day+status,day,'Kurum',status))
        self.assertEqual(self.store.scanned_days(),{'2026-10-16'})
        with self.store.connect() as db:
            db.execute("UPDATE documents SET status='done' WHERE status IN ('pending','error')")
        self.assertEqual(self.store.scanned_days(),{'2026-10-16','2026-10-17','2026-10-18'})


if __name__=='__main__':
    unittest.main()
