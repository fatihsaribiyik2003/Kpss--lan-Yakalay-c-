from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
import unicodedata
import uuid
from contextlib import contextmanager
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from .access import NORMAL_MAX_DAYS, sign_grant, valid_grant
from .candidate import analyze, default_profile, fingerprint, ANALYSIS_VERSION

ROOT = 'https://www.resmigazete.gov.tr'
DEFAULT_TERMS = ['KPSS', 'lisans', 'bilişim', 'bilgisayar', 'yazılım']


def today():
    # Türkiye yıl boyunca UTC+3 kullanır; işletim sistemi saat diliminden bağımsız.
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)).date()


def normalize(text):
    text = text.replace('ı', 'i').replace('İ', 'I').casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                   if not unicodedata.combining(c))


def matches(text, terms):
    text = re.sub(r'\s+', ' ', text).strip()
    normalized = normalize(text)
    found = []
    for term in terms:
        needle = normalize(term.strip())
        if not needle:
            continue
        pattern = r'(?<!\w)' + re.escape(needle).replace(r'\ ', r'\s+') + r'(?!\w)'
        # Ekli kelimeleri de kapsa: "bilişimde", "bilgisayarların" gibi.
        pattern = pattern.removesuffix(r'(?!\w)') + r'\w*'
        for m in list(re.finditer(pattern, normalized))[:3]:
            found.append({'term': term, 'excerpt': text[max(0, m.start()-85):m.end()+155]})
    return found


def default_dir():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'KPSSIlanYakalayici'


class PDFLinks(HTMLParser):
    def __init__(self, base):
        super().__init__()
        self.base, self.links, self.current, self.parts = base, [], None, []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            href = dict(attrs).get('href', '')
            absolute = urljoin(self.base, href)
            parsed = urlparse(absolute)
            if parsed.scheme == 'https' and parsed.hostname in ('www.resmigazete.gov.tr', 'resmigazete.gov.tr') and parsed.path.lower().endswith('.pdf'):
                self.current, self.parts = absolute, []

    def handle_data(self, data):
        if self.current:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self.current:
            self.links.append((self.current, re.sub(r'\s+', ' ', ''.join(self.parts)).strip().rstrip(':')))
            self.current = None


class Store:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / 'pdf').mkdir(exist_ok=True)
        self.path = self.directory / 'ilanlar.sqlite3'
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS days(day TEXT PRIMARY KEY, status TEXT, checked REAL, retry REAL DEFAULT 0, error TEXT);
            CREATE TABLE IF NOT EXISTS documents(
              id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL, day TEXT NOT NULL, title TEXT,
              status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0, retry REAL DEFAULT 0,
              error TEXT, path TEXT, hash TEXT, pages INTEGER DEFAULT 0, updated REAL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS pages(
              hash TEXT, page INTEGER, text TEXT NOT NULL, method TEXT, quality TEXT,
              PRIMARY KEY(hash,page));
            CREATE TABLE IF NOT EXISTS hits(
              doc INTEGER, page INTEGER, term TEXT, excerpt TEXT,
              UNIQUE(doc,page,term,excerpt));
            CREATE TABLE IF NOT EXISTS notices(doc INTEGER PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS candidate_reviews(
              doc INTEGER PRIMARY KEY, version INTEGER NOT NULL, fingerprint TEXT NOT NULL,
              category TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS hits_doc ON hits(doc);
            ''')
        defaults = {'start_date': (today()-dt.timedelta(days=6)).isoformat(),
                    'scan_days': 7, 'admin_grant': None, 'installation_id': str(uuid.uuid4()),
                    'terms': DEFAULT_TERMS, 'interval_minutes': 30,
                    'candidate_profile':default_profile(today()),
                    'profile_view':'Önerilen + kontrol gereken', 'profile_route':'Her iki yol',
                    'paused': False, 'autostart': True}
        for key, value in defaults.items():
            with self.connect() as db:
                db.execute('INSERT OR IGNORE INTO settings VALUES(?,?)', (key, json.dumps(value)))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def setting(self, key):
        with self.connect() as db:
            row = db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
            return json.loads(row[0]) if row else None

    def set_setting(self, key, value):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', (key, json.dumps(value)))

    def scan_days(self):
        requested = self.setting('scan_days')
        maximum = (today()-dt.date(2000,1,1)).days+1
        if type(requested) is not int or not 1 <= requested <= maximum:
            return NORMAL_MAX_DAYS
        if requested <= NORMAL_MAX_DAYS:
            return requested
        return requested if valid_grant(self.setting('admin_grant'), self.setting('installation_id'), requested) else NORMAL_MAX_DAYS

    def scan_start(self):
        return today()-dt.timedelta(days=self.scan_days()-1)

    def in_scan_range(self, day):
        if isinstance(day, str):
            day=dt.date.fromisoformat(day)
        return self.scan_start() <= day <= today()

    def set_scan_days(self, days, private_key=None):
        maximum = (today()-dt.date(2000,1,1)).days+1
        if type(days) is not int or not 1 <= days <= maximum:
            raise ValueError(f'Gün sayısı 1–{maximum} arasında olmalı.')
        if days > NORMAL_MAX_DAYS and private_key is None:
            raise PermissionError('7 günden eski taramalar için proje yöneticisi yetkisi gerekir.')
        grant = sign_grant(private_key,self.setting('installation_id'),days) if days > NORMAL_MAX_DAYS else None
        with self.connect() as db:
            db.executemany('INSERT OR REPLACE INTO settings VALUES(?,?)',
                           [('scan_days',json.dumps(days)),('admin_grant',json.dumps(grant))])

    def results(self):
        with self.connect() as db:
            return db.execute('''SELECT d.*, GROUP_CONCAT(DISTINCT h.term) terms,
              GROUP_CONCAT(DISTINCT h.page) hit_pages FROM documents d JOIN hits h ON h.doc=d.id
              GROUP BY d.id ORDER BY d.day DESC,d.id DESC''').fetchall()

    def failures(self):
        with self.connect() as db:
            return db.execute("SELECT * FROM documents WHERE status IN ('error','partial') ORDER BY day DESC").fetchall()

    def profile_results(self):
        current=fingerprint(self.setting('candidate_profile'))
        with self.connect() as db:
            rows=db.execute('''SELECT d.*,r.payload,r.category,
              (SELECT GROUP_CONCAT(DISTINCT term) FROM hits WHERE doc=d.id) terms
              FROM documents d JOIN candidate_reviews r ON r.doc=d.id
              WHERE d.status IN ('done','partial') AND r.version=? AND r.fingerprint=?
              ORDER BY d.day DESC,d.id DESC''',(ANALYSIS_VERSION,current)).fetchall()
        result=[]
        for row in rows:
            item=dict(row)
            item['assessment']=json.loads(item.pop('payload'))
            item['hit_pages']=','.join(str(p) for p in item['assessment']['pages'])
            result.append(item)
        return result

    def scanned_days(self):
        with self.connect() as db:
            return {row[0] for row in db.execute('''
                SELECT day FROM days WHERE status='done'
                AND EXISTS (SELECT 1 FROM documents WHERE documents.day=days.day)
                AND NOT EXISTS (SELECT 1 FROM documents WHERE documents.day=days.day
                                AND status NOT IN ('done','partial'))
            ''')}


class Reader:
    def __init__(self):
        self.ocr = None

    def page(self, page):
        text = page.get_text('text', sort=True).strip()
        image_area = sum(r.get('bbox', (0,0,0,0))[2] and
                         max(0, r['bbox'][2]-r['bbox'][0])*max(0,r['bbox'][3]-r['bbox'][1])
                         for r in page.get_image_info())
        needs_ocr = len(text) < 80 or image_area > page.rect.get_area() * .35
        if not needs_ocr:
            return text, 'metin', 'ok'
        if self.ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
        import pymupdf
        import numpy as np
        pix = page.get_pixmap(matrix=pymupdf.Matrix(2.2, 2.2), alpha=False)
        array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        result, _ = self.ocr(array)
        if not result:
            # Boş veya harita sayfası da olabilir; sessizce "eşleşme yok" sayma.
            return text, 'OCR', 'review'
        ocr_text = '\n'.join(item[1] for item in result)
        confidences = [float(item[2]) for item in result]
        quality = 'ok' if sum(confidences)/len(confidences) >= .80 else 'review'
        return text + '\n' + ocr_text, 'OCR', quality


class Stopped(Exception):
    pass


class OutsideScanRange(Exception):
    pass


class Engine:
    def __init__(self, store, callback=None, notification=None):
        self.store, self.callback, self.notification = store, callback, notification
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.reader = Reader()
        self.state = 'Başlatılıyor…'
        self.lock = threading.Lock()
        self.live_checked = time.monotonic()
        self.log = logging.getLogger('ilan.'+str(store.path))
        self.log.setLevel(logging.INFO)
        if not self.log.handlers:
            handler = RotatingFileHandler(store.directory/'uygulama.log', maxBytes=2_000_000, backupCount=3, encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            self.log.addHandler(handler)

    def report(self, text):
        self.state = text
        self.log.info(text)
        if self.callback:
            self.callback(text)

    def check_stop(self):
        if self.stop.is_set():
            raise Stopped()

    def fetch(self, url, max_size=60_000_000):
        self.check_stop()
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) KPSSIlanYakalayici/1.0', 'Accept': '*/*'})
        with urlopen(request, timeout=35) as response:
            final = urlparse(response.url)
            if final.scheme != 'https' or final.hostname not in ('www.resmigazete.gov.tr', 'resmigazete.gov.tr'):
                raise ValueError('Beklenmeyen indirme adresi')
            chunks, total = [], 0
            declared = response.headers.get('Content-Length')
            while True:
                self.check_stop()
                chunk = response.read(128*1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_size:
                    raise ValueError('Dosya boyut sınırını aştı; inceleme gerekli')
                chunks.append(chunk)
            if declared and declared.isdigit() and total != int(declared):
                raise IOError('İndirme yarım kaldı; dosya yeniden indirilecek')
            return b''.join(chunks)

    def discover(self, day):
        if not self.store.in_scan_range(day):
            return
        now = time.time()
        with self.store.connect() as db:
            old = db.execute('SELECT * FROM days WHERE day=?', (day.isoformat(),)).fetchone()
        if old and old['retry'] > now:
            return
        if old and old['status'] == 'done' and day < today()-dt.timedelta(days=3):
            return
        if old and old['status'] == 'done' and now-old['checked'] < self.store.setting('interval_minutes')*60:
            return
        stamp = day.strftime('%Y%m%d')
        url = f'{ROOT}/ilanlar/eskiilanlar/{day:%Y/%m}/{stamp}-4.htm'
        try:
            self.report(f'{day:%d.%m.%Y} ilan bağlantıları kontrol ediliyor')
            raw = self.fetch(url, 5_000_000)
            # Word kaynaklı eski sayfalarda Windows-1254 kullanılır.
            enc = re.search(br'charset\s*=\s*["\']?([\w-]+)', raw[:5000], re.I)
            encoding = enc.group(1).decode('ascii') if enc else 'utf-8'
            try:
                html = raw.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                html = raw.decode('cp1254', errors='replace')
            parser = PDFLinks(url)
            parser.feed(html)
            if not parser.links:
                raise ValueError('İlan bağlantısı bulunamadı; sayfa henüz yayımlanmamış veya yapısı değişmiş olabilir')
            with self.store.connect() as db:
                for pdf, title in parser.links:
                    db.execute('INSERT OR IGNORE INTO documents(url,day,title) VALUES(?,?,?)', (pdf, day.isoformat(), title))
                db.execute('INSERT OR REPLACE INTO days VALUES(?,?,?,?,?)', (day.isoformat(),'done',now,0,None))
        except Stopped:
            raise
        except Exception as exc:
            missing = isinstance(exc, HTTPError) and exc.code == 404
            wait = 21600 if missing else 1800
            # Eski tarihte bulunmayan sayfalar haftalık yeniden kontrol edilir.
            if missing and day < today()-dt.timedelta(days=7):
                wait = 7*86400
            with self.store.connect() as db:
                db.execute('INSERT OR REPLACE INTO days VALUES(?,?,?,?,?)', (day.isoformat(),'missing' if missing else 'error',now,now+wait,str(exc)))
            self.log.warning('İlan dizini %s: %s', day, exc)

    def process(self, doc):
        import pymupdf
        self.check_stop()
        if not self.store.in_scan_range(doc['day']):
            return
        with self.store.connect() as db:
            db.execute("UPDATE documents SET status='processing', updated=? WHERE id=?", (time.time(),doc['id']))
        try:
            path = Path(doc['path']) if doc['path'] else None
            if not path or not path.exists():
                self.report(f"PDF indiriliyor: {doc['title']}")
                content = self.fetch(doc['url'])
                if not content.lstrip().startswith(b'%PDF-'):
                    raise ValueError('Sunucu PDF yerine farklı bir içerik döndürdü')
                with pymupdf.open(stream=content, filetype='pdf') as validation:
                    if not len(validation):
                        raise ValueError('İndirilen PDF sayfa içermiyor')
                digest = hashlib.sha256(content).hexdigest()
                path = self.store.directory / 'pdf' / (digest+'.pdf')
                temporary = path.with_suffix('.part')
                temporary.write_bytes(content)
                temporary.replace(path)
            else:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.store.connect() as db:
                db.execute('UPDATE documents SET path=?,hash=? WHERE id=?', (str(path),digest,doc['id']))
            with pymupdf.open(path) as pdf:
                if pdf.needs_pass:
                    raise ValueError('Şifreli PDF okunamıyor')
                if not len(pdf):
                    raise ValueError('PDF sayfa içermiyor')
                for i,page in enumerate(pdf):
                    self.check_stop()
                    if not self.store.in_scan_range(doc['day']):
                        raise OutsideScanRange()
                    # Uzun geçmiş taramasında yeni günlük ilanların keşfi beklemesin.
                    if (not self.store.setting('paused') and
                            time.monotonic()-self.live_checked >= self.store.setting('interval_minutes')*60):
                        self.live_checked = time.monotonic()
                        self.discover(today())
                    with self.store.connect() as db:
                        cached = db.execute('SELECT * FROM pages WHERE hash=? AND page=?',(digest,i+1)).fetchone()
                    if cached:
                        continue
                    self.report(f"{doc['title']} • sayfa {i+1}/{len(pdf)} okunuyor")
                    text, method, quality = self.reader.page(page)
                    with self.store.connect() as db:
                        db.execute('INSERT OR REPLACE INTO pages VALUES(?,?,?,?,?)',(digest,i+1,text,method,quality))
                with self.store.connect() as db:
                    db.execute('UPDATE documents SET pages=? WHERE id=?', (len(pdf),doc['id']))
            self.index(doc['id'],digest)
            with self.store.connect() as db:
                review = db.execute("SELECT COUNT(*) FROM pages WHERE hash=? AND quality!='ok'", (digest,)).fetchone()[0]
                db.execute('UPDATE documents SET status=?,error=?,retry=0,updated=? WHERE id=?',
                           ('partial' if review else 'done',f'{review} sayfada OCR kesinliği düşük veya okunabilir metin yok; kontrol gerekli.' if review else None,time.time(),doc['id']))
        except (Stopped, OutsideScanRange):
            with self.store.connect() as db:
                db.execute("UPDATE documents SET status='pending' WHERE id=?",(doc['id'],))
            if self.stop.is_set():
                raise Stopped()
        except Exception as exc:
            attempts = doc['attempts']+1
            delay = min(86400, 60*(2**min(attempts,10)))
            with self.store.connect() as db:
                if isinstance(exc, (pymupdf.FileDataError, pymupdf.EmptyFileError)):
                    db.execute('UPDATE documents SET path=NULL,hash=NULL WHERE id=?',(doc['id'],))
                db.execute("UPDATE documents SET status='error',attempts=?,retry=?,error=?,updated=? WHERE id=?",(attempts,time.time()+delay,str(exc),time.time(),doc['id']))
            self.log.exception('PDF işlenemedi: %s',doc['url'])

    def index(self, doc_id, digest):
        terms = self.store.setting('terms')
        with self.store.connect() as db:
            pages = db.execute('SELECT * FROM pages WHERE hash=? ORDER BY page',(digest,)).fetchall()
            db.execute('DELETE FROM hits WHERE doc=?',(doc_id,))
            for page in pages:
                for hit in matches(page['text'],terms):
                    db.execute('INSERT OR IGNORE INTO hits VALUES(?,?,?,?)',(doc_id,page['page'],hit['term'],hit['excerpt']))
        self.review_profile(doc_id,digest)

    def review_profile(self, doc_id, digest):
        profile=self.store.setting('candidate_profile')
        with self.store.connect() as db:
            pages=db.execute('SELECT * FROM pages WHERE hash=? ORDER BY page',(digest,)).fetchall()
        result=analyze(pages,profile)
        with self.store.connect() as db:
            db.execute('INSERT OR REPLACE INTO candidate_reviews VALUES(?,?,?,?,?)',
                       (doc_id,ANALYSIS_VERSION,fingerprint(profile),result['category'],json.dumps(result,ensure_ascii=False)))

    def refresh_profile(self):
        profile_hash=fingerprint(self.store.setting('candidate_profile'))
        with self.store.connect() as db:
            docs=db.execute('''SELECT d.id,d.hash FROM documents d LEFT JOIN candidate_reviews r ON r.doc=d.id
              WHERE d.hash IS NOT NULL AND d.status IN ('done','partial')
              AND (r.doc IS NULL OR r.version!=? OR r.fingerprint!=?)''',(ANALYSIS_VERSION,profile_hash)).fetchall()
        if docs:
            self.report(f'{len(docs)} kayıtlı PDF aday profiline göre değerlendiriliyor • yeniden indirme/OCR yapılmaz')
        for doc in docs:
            self.check_stop()
            self.review_profile(doc['id'],doc['hash'])

    def reindex(self):
        # Kelimeler değişince PDF indirme/OCR tekrarı yok; saklanan metin kullanılır.
        with self.store.connect() as db:
            docs = db.execute("SELECT id,hash FROM documents WHERE hash IS NOT NULL AND status IN ('done','partial')").fetchall()
        for doc in docs:
            self.check_stop()
            self.index(doc['id'],doc['hash'])

    def notify(self):
        with self.store.connect() as db:
            rows = db.execute('''SELECT DISTINCT d.id,d.title FROM documents d JOIN candidate_reviews r ON r.doc=d.id
                WHERE r.category IN ('pre_match','review') AND d.day>=? AND d.day<=?
                AND d.id NOT IN (SELECT doc FROM notices)''',(self.store.scan_start().isoformat(),today().isoformat())).fetchall()
        if rows and self.notification:
            if self.notification(len(rows),rows[0]['title']):
                with self.store.connect() as db:
                    db.executemany('INSERT OR IGNORE INTO notices VALUES(?)',[(r['id'],) for r in rows])

    def cycle(self):
        if not self.lock.acquire(blocking=False):
            return
        try:
            self.refresh_profile()
            # Çökme/elektrik kesintisinde yarım kalan dosyalar sayfa önbelleğiyle sürdürülür.
            with self.store.connect() as db:
                db.execute("UPDATE documents SET status='pending' WHERE status='processing'")
            day = today()
            while day >= self.store.scan_start():
                self.check_stop()
                if self.store.setting('paused'):
                    self.report('Tarama duraklatıldı')
                    return
                self.discover(day)
                self.drain()
                day -= dt.timedelta(days=1)
            self.drain()
            self.notify()
            self.store.set_setting('last_cycle',time.time())
            self.report('Kontrol tamamlandı • yeni ilanlar için bekleniyor')
        finally:
            self.lock.release()

    def drain(self):
        while True:
            self.check_stop()
            self.refresh_profile()
            if self.store.setting('paused'):
                break
            with self.store.connect() as db:
                doc = db.execute("SELECT * FROM documents WHERE status IN ('pending','error') AND retry<=? AND day>=? AND day<=? ORDER BY day DESC,id LIMIT 1",(time.time(),self.store.scan_start().isoformat(),today().isoformat())).fetchone()
            if doc is None:
                break
            self.process(doc)
            self.notify()

    def run(self):
        while not self.stop.is_set():
            self.wake.clear()
            try:
                if not self.store.setting('paused'):
                    self.cycle()
                else:
                    self.report('Tarama duraklatıldı')
            except Stopped:
                break
            except Exception:
                self.log.exception('Kontrol döngüsü başarısız; otomatik yeniden denenecek')
                self.report('Geçici hata • sonraki kontrolde yeniden denenecek')
            self.wake.wait(max(60,self.store.setting('interval_minutes')*60))

    def close(self):
        self.stop.set()
        self.wake.set()
