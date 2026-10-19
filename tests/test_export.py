import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from watcher.desktop import Desktop


class ExportTests(unittest.TestCase):
    def test_visible_unread_application_export_keeps_date_and_escapes_formula(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'visible.csv'
            row={'day':'2026-10-19','title':'=FORMULA','assessment':None,'status':'pending','hit_pages':'','url':'https://example.org/x.pdf','applied_at':'2026-10-19T12:00:00+03:00'}
            app=SimpleNamespace(root=None,current_rows={'1':row},status=Mock())
            with patch('watcher.desktop.filedialog.asksaveasfilename',return_value=str(path)):
                Desktop.export(app)
            with path.open(encoding='utf-8-sig',newline='') as stream:
                rows=list(csv.reader(stream,delimiter=';'))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[1][1],"'=FORMULA")
            self.assertEqual(rows[1][-2],'Başvuruldu')
            self.assertEqual(rows[1][-1],row['applied_at'])
