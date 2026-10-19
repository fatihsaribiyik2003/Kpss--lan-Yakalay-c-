"""Verilen gerçek ilan günüyle uçtan uca doğrulama; uygulamanın parçası değildir."""
import argparse
import datetime as dt
import json
from watcher.core import Store,Engine

parser=argparse.ArgumentParser()
parser.add_argument('--directory',default='test-data/real')
args=parser.parse_args()
store=Store(args.directory)
engine=Engine(store,lambda s:print(s,flush=True))
engine.discover(dt.date(2026,10,18))
engine.drain()
with store.connect() as db:
    rows=db.execute('SELECT title,status,pages,error FROM documents').fetchall()
    print(json.dumps([dict(r) for r in rows],ensure_ascii=False),flush=True)
for row in store.results():
    print(json.dumps({k:row[k] for k in ['title','terms','hit_pages','status']},ensure_ascii=False),flush=True)
