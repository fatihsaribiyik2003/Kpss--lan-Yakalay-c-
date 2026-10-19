import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from watcher.core import Store
from watcher.desktop import Desktop


class DesktopActions(unittest.TestCase):
    def test_manual_check_resumes_paused_scanner_and_preserves_user_records(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            store.set_setting('paused',True)
            profile=store.setting('candidate_profile')
            with store.connect() as db:
                doc=db.execute("INSERT INTO documents(url,day,title) VALUES('https://example.org/test.pdf','2026-10-19','Test')").lastrowid
            store.set_applied(doc)
            stamp=store.listing_results()[0]['applied_at']
            app=SimpleNamespace(store=store,pause_button=Mock(),engine=SimpleNamespace(wake=threading.Event()),status=Mock())
            Desktop.check_now(app)
            self.assertFalse(store.setting('paused'))
            self.assertTrue(app.engine.wake.is_set())
            self.assertEqual(store.setting('candidate_profile'),profile)
            self.assertEqual(store.listing_results()[0]['applied_at'],stamp)
