from __future__ import annotations

import csv
import ctypes
import datetime as dt
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser

from .core import Store, Engine, today
from .calendar_widget import ScanCalendar


def autostart(enabled):
    if os.name != 'nt':
        return
    import winreg
    if getattr(sys, 'frozen', False):
        command = subprocess.list2cmdline([sys.executable, '--background'])
    else:
        pythonw = str(Path(sys.executable).with_name('pythonw.exe'))
        command = subprocess.list2cmdline([pythonw,str(Path(__file__).resolve().parent.parent/'main.py'),'--background'])
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        if enabled:
            winreg.SetValueEx(key,'KPSSIlanYakalayici',0,winreg.REG_SZ,command)
        else:
            try:
                winreg.DeleteValue(key,'KPSSIlanYakalayici')
            except FileNotFoundError:
                pass


class Desktop:
    def __init__(self, directory, background=False, startup=True):
        self.store = Store(directory)
        self.messages = queue.Queue()
        self.engine = Engine(self.store, self.messages.put, self.notify)
        self.root = tk.Tk()
        self.root.title('KPSS İlan Yakalayıcı')
        self.root.geometry('1160x760')
        self.root.minsize(900,600)
        self.root.configure(bg='#f4f6fa')
        self.root.protocol('WM_DELETE_WINDOW',self.hide)
        self.tray = None
        self.current_rows = {}
        self.result_snapshot = None
        self.error_snapshot = None
        self.log_snapshot = None
        self.reindex_requested = threading.Event()
        self.status = tk.StringVar(value='Otomatik takip hazırlanıyor…')
        self.summary = tk.StringVar()
        self.build_ui()
        self.make_tray()
        if startup:
            try:
                autostart(self.store.setting('autostart'))
            except Exception as exc:
                self.engine.log.warning('Otomatik başlangıç ayarlanamadı: %s',exc)
                self.messages.put('Windows başlangıcı ayarlanamadı; Ayarlar bölümünden tekrar deneyin.')
        if background and self.tray:
            self.root.withdraw()
        self.thread = threading.Thread(target=self.work,daemon=True,name='ilan-tarayici')
        self.thread.start()
        self.refresh()
        self.root.after(500,self.poll)

    def work(self):
        # Tüm OCR ve veritabanı yeniden indeksleme işlemleri tek iş parçacığında.
        while not self.engine.stop.is_set():
            self.engine.wake.clear()
            try:
                if self.reindex_requested.is_set():
                    self.reindex_requested.clear()
                    self.engine.report('Saklanan metinler yeni kelimelerle filtreleniyor')
                    self.engine.reindex()
                if not self.store.setting('paused'):
                    self.engine.cycle()
                else:
                    self.engine.report('Tarama duraklatıldı')
            except Exception as exc:
                if self.engine.stop.is_set():
                    break
                self.engine.log.exception('Arka plan taraması başarısız')
                self.messages.put(f'Geçici hata; yeniden denenecek: {exc}')
            if self.reindex_requested.is_set():
                continue
            self.engine.wake.wait(max(60,self.store.setting('interval_minutes')*60))

    def build_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10))
        style.configure('TFrame',background='#f4f6fa')
        style.configure('TLabel',background='#f4f6fa',foreground='#18243c')
        style.configure('Title.TLabel',font=('Segoe UI',24,'bold'))
        style.configure('Muted.TLabel',foreground='#57677e')
        style.configure('TButton',padding=(12,8))
        style.configure('Treeview',rowheight=34,font=('Segoe UI',10),background='white',fieldbackground='white')
        style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),padding=8)
        outer = ttk.Frame(self.root,padding=22)
        outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='KPSS İlan Yakalayıcı',style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer,text='Resmî Gazete • otomatik PDF ve OCR taraması • veriler bu bilgisayarda',style='Muted.TLabel').pack(anchor='w',pady=(4,14))
        ttk.Label(outer,textvariable=self.summary,font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,12))
        controls=ttk.Frame(outer)
        controls.pack(fill='x',pady=(0,12))
        ttk.Button(controls,text='Şimdi kontrol et',command=self.check_now).pack(side='left')
        self.pause_button=ttk.Button(controls,text='Devam et' if self.store.setting('paused') else 'Duraklat',command=self.pause)
        self.pause_button.pack(side='left',padx=8)
        ttk.Button(controls,text='CSV dışa aktar',command=self.export).pack(side='left')
        ttk.Button(controls,text='Tamamen çık',command=self.quit).pack(side='right')
        body=ttk.Frame(outer)
        body.pack(fill='both',expand=True)
        sidebar=ttk.Frame(body)
        sidebar.pack(side='right',fill='y',padx=(12,0))
        self.calendar=ScanCalendar(sidebar)
        self.calendar.pack(side='bottom',anchor='e')
        tabs=ttk.Notebook(body)
        tabs.pack(side='left',fill='both',expand=True)
        results=ttk.Frame(tabs,padding=10)
        errors=ttk.Frame(tabs,padding=10)
        settings=ttk.Frame(tabs,padding=18)
        logs=ttk.Frame(tabs,padding=10)
        tabs.add(results,text='  Eşleşen ilanlar  ')
        tabs.add(errors,text='  İşlem durumu  ')
        tabs.add(settings,text='  Ayarlar  ')
        tabs.add(logs,text='  Günlük  ')
        self.tree=self.table(results,('date','title','terms','pages','state'),('Tarih','Kurum / ilan','Bulunan kelimeler','Sayfa','Okuma durumu'),(90,340,250,65,110))
        self.tree.bind('<<TreeviewSelect>>',self.details)
        self.tree.bind('<Double-1>',lambda event:self.open_pdf())
        self.detail=tk.Text(results,height=4,wrap='word',font=('Segoe UI',10),relief='flat',padx=10,pady=8)
        self.detail.pack(fill='x',pady=10)
        self.detail.insert('1.0','İlgili metni görmek için bir ilan seçin. PDF’yi açmak için çift tıklayın.')
        self.detail.configure(state='disabled')
        actions=ttk.Frame(results)
        actions.pack(fill='x')
        ttk.Button(actions,text='İndirilen PDF’yi aç',command=self.open_pdf).pack(side='left')
        ttk.Button(actions,text='Resmî kaynağı aç',command=self.open_source).pack(side='left',padx=8)
        ttk.Label(errors,text='Hatalı indirmeler otomatik yeniden denenir. OCR kontrolü gereken dosyalar burada kalır.',wraplength=900).pack(anchor='w',pady=(0,8))
        self.errors=self.table(errors,('date','title','state','error'),('Tarih','Kurum / adres','Durum','Açıklama'),(90,300,110,440))
        ttk.Button(errors,text='Seçili PDF’yi aç',command=self.open_error).pack(anchor='w',pady=8)
        ttk.Button(errors,text='Başarısız indirmeleri şimdi yeniden dene',command=self.retry).pack(anchor='w')
        ttk.Label(settings,text='Geçmiş taraması başlangıcı (YYYY-AA-GG)').grid(row=0,column=0,sticky='w',pady=9)
        self.start=tk.StringVar(value=self.store.setting('start_date'))
        ttk.Entry(settings,textvariable=self.start,width=22).grid(row=0,column=1,sticky='w',padx=16)
        ttk.Label(settings,text='Arama kelimeleri (virgülle ayırın)').grid(row=1,column=0,sticky='w',pady=9)
        self.terms=tk.StringVar(value=', '.join(self.store.setting('terms')))
        ttk.Entry(settings,textvariable=self.terms,width=35).grid(row=1,column=1,sticky='w',padx=16)
        ttk.Label(settings,text='Kontrol aralığı (dakika, en az 5)').grid(row=2,column=0,sticky='w',pady=9)
        self.interval=tk.StringVar(value=str(self.store.setting('interval_minutes')))
        ttk.Entry(settings,textvariable=self.interval,width=10).grid(row=2,column=1,sticky='w',padx=16)
        self.startup=tk.BooleanVar(value=self.store.setting('autostart'))
        ttk.Checkbutton(settings,text='Windows oturumu açılınca arka planda başlat',variable=self.startup).grid(row=3,column=0,columnspan=2,sticky='w',pady=10)
        ttk.Button(settings,text='Ayarları kaydet',command=self.save).grid(row=4,column=0,sticky='w',pady=12)
        info=('Kelimelerden en az birinin geçmesi yeterlidir. Türkçe harflerin OCR karşılıkları ve kelime ekleri kapsanır.\n\n'
              'Başlangıcı daha eski bir tarihe çekerseniz eksik günler otomatik eklenir. Tamamlanan PDF’ler yeniden okunmaz. '
              'Kelimeler değişirse mevcut metinler tekrar filtrelenir; PDF indirme ve OCR tekrarlanmaz.\n\n'
              'Pencereyi kapatmak uygulamayı sistem tepsisine indirir. Bilgisayar kapalıyken tarama yapılamaz; açıldığında kaçırılan günler tamamlanır. '
              'Kapsam: günlük Çeşitli İlanlar bölümü. OCR yanlış okuyabilir; sonuçlar kesin başvuru uygunluğu değerlendirmesi değildir.')
        ttk.Label(settings,text=info,wraplength=670,style='Muted.TLabel').grid(row=5,column=0,columnspan=2,sticky='w',pady=14)
        ttk.Button(settings,text='Veri klasörünü aç',command=lambda:os.startfile(self.store.directory)).grid(row=6,column=0,sticky='w')
        self.logview=tk.Text(logs,wrap='word',font=('Consolas',10),relief='flat',padx=8,pady=8)
        self.logview.pack(fill='both',expand=True)
        ttk.Label(outer,textvariable=self.status,style='Muted.TLabel',wraplength=1080).pack(anchor='w',pady=(12,0))

    def table(self,parent,columns,headings,widths):
        frame=ttk.Frame(parent)
        frame.pack(fill='both',expand=True)
        tree=ttk.Treeview(frame,columns=columns,show='headings',selectmode='browse',height=6)
        for col,heading,width in zip(columns,headings,widths):
            tree.heading(col,text=heading)
            tree.column(col,width=width,minwidth=50)
        bar=ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y')
        tree.pack(side='left',fill='both',expand=True)
        def resize(event):
            available=max(1,event.width-bar.winfo_reqwidth()-4)
            total=sum(widths)
            for col,width in zip(columns,widths):
                tree.column(col,width=max(50,int(available*width/total)))
        frame.bind('<Configure>',resize)
        return tree

    def refresh(self):
        self.calendar.update_days(self.store.scanned_days())
        rows=self.store.results()
        self.current_rows={str(r['id']):dict(r) for r in rows}
        snapshot=[tuple(r) for r in rows]
        if snapshot!=self.result_snapshot:
            self.result_snapshot=snapshot
            selected=self.tree.selection()
            self.tree.delete(*self.tree.get_children())
            for row in rows:
                self.tree.insert('','end',iid=str(row['id']),values=(row['day'],row['title'],row['terms'],row['hit_pages'],'Kontrol gerekli' if row['status']=='partial' else ('Tamamlandı' if row['status']=='done' else 'İşleniyor')))
            if selected and selected[0] in self.current_rows:
                self.tree.selection_set(selected[0])
        failures=self.store.failures()
        with self.store.connect() as db:
            counts={r[0]:r[1] for r in db.execute('SELECT status,COUNT(*) FROM documents GROUP BY status')}
            days=db.execute("SELECT * FROM days WHERE status='error' ORDER BY day DESC LIMIT 100").fetchall()
            done_days=db.execute("SELECT COUNT(*) FROM days WHERE status='done'").fetchone()[0]
            missing=db.execute("SELECT COUNT(*) FROM days WHERE status='missing'").fetchone()[0]
        errors_snapshot=([tuple(r) for r in failures],[tuple(r) for r in days])
        if errors_snapshot!=self.error_snapshot:
            self.error_snapshot=errors_snapshot
            self.errors.delete(*self.errors.get_children())
            for row in failures:
                self.errors.insert('','end',iid='doc'+str(row['id']),values=(row['day'],row['title'],'OCR kontrolü' if row['status']=='partial' else 'Yeniden denenecek',row['error']))
            for row in days:
                self.errors.insert('','end',values=(row['day'],'İlan dizini','Yeniden denenecek',row['error']))
        self.summary.set(f"{len(rows)} eşleşen PDF     •     {counts.get('done',0)+counts.get('partial',0)} okunan PDF     •     {counts.get('pending',0)+counts.get('processing',0)} bekleyen     •     {done_days} gün tarandı     •     {missing} gün henüz bulunamadı")
        log=self.store.directory/'uygulama.log'
        if log.exists():
            with log.open('rb') as stream:
                stream.seek(max(0,log.stat().st_size-18000))
                content=stream.read().decode('utf-8',errors='replace')
            if content!=self.log_snapshot:
                self.log_snapshot=content
                self.logview.configure(state='normal')
                self.logview.delete('1.0','end')
                self.logview.insert('1.0',content)
                self.logview.see('end')
                self.logview.configure(state='disabled')

    def poll(self):
        while True:
            try:
                item=self.messages.get_nowait()
            except queue.Empty:
                break
            if item=='__show__':
                self.show()
            elif item=='__quit__':
                self.quit()
                return
            else:
                self.status.set(item)
        if getattr(self,'show_event',None) and ctypes.windll.kernel32.WaitForSingleObject(self.show_event,0)==0:
            self.show()
        self.refresh()
        self.root.after(2500,self.poll)

    def details(self,event=None):
        selection=self.tree.selection()
        if not selection:
            return
        with self.store.connect() as db:
            rows=db.execute('SELECT * FROM hits WHERE doc=? ORDER BY page,term',(int(selection[0]),)).fetchall()
        text='\n\n'.join(f"Sayfa {r['page']} • {r['term']}\n…{r['excerpt']}…" for r in rows)
        self.detail.configure(state='normal')
        self.detail.delete('1.0','end')
        self.detail.insert('1.0',text)
        self.detail.configure(state='disabled')

    def selected(self):
        ids=self.tree.selection()
        return self.current_rows.get(ids[0]) if ids else None

    def open_pdf(self):
        row=self.selected()
        if row and row['path'] and Path(row['path']).exists():
            os.startfile(row['path'])

    def open_source(self):
        row=self.selected()
        if row:
            webbrowser.open(row['url'])

    def open_error(self):
        selected=self.errors.selection()
        if selected and selected[0].startswith('doc'):
            with self.store.connect() as db:
                row=db.execute('SELECT path,url FROM documents WHERE id=?',(int(selected[0][3:]),)).fetchone()
            if row and row['path'] and Path(row['path']).exists():
                os.startfile(row['path'])
            elif row:
                webbrowser.open(row['url'])

    def check_now(self):
        self.engine.wake.set()
        self.status.set('Kontrol istendi; mevcut işlem varsa ardından devam edecek')

    def retry(self):
        with self.store.connect() as db:
            db.execute("UPDATE documents SET retry=0 WHERE status='error'")
            db.execute("UPDATE days SET retry=0 WHERE status IN ('error','missing')")
        self.check_now()

    def pause(self):
        paused=not self.store.setting('paused')
        self.store.set_setting('paused',paused)
        self.pause_button.configure(text='Devam et' if paused else 'Duraklat')
        self.engine.wake.set()
        self.status.set('Mevcut PDF tamamlanınca duraklatılacak' if paused else 'Tarama devam ediyor')

    def save(self):
        try:
            start=dt.date.fromisoformat(self.start.get().strip())
            if start>today() or start<dt.date(2000,1,1):
                raise ValueError('Başlangıç tarihi 2000 ile bugün arasında olmalı.')
            interval=int(self.interval.get())
            if not 5<=interval<=1440:
                raise ValueError('Kontrol aralığı 5–1440 dakika arasında olmalı.')
            terms=list(dict.fromkeys(t.strip() for t in self.terms.get().split(',') if t.strip()))
            if not terms or len(terms)>50:
                raise ValueError('1–50 arama kelimesi girin.')
            autostart(self.startup.get())
            for key,value in [('start_date',start.isoformat()),('interval_minutes',interval),('terms',terms),('autostart',self.startup.get())]:
                self.store.set_setting(key,value)
            self.reindex_requested.set()
            self.engine.wake.set()
            self.status.set('Ayarlar kaydedildi; geçmiş metinler de yeni kelimelerle filtrelenecek')
        except Exception as exc:
            messagebox.showerror('Ayarlar kaydedilemedi',str(exc),parent=self.root)

    def export(self):
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.csv',initialfile='eslesen-ilanlar.csv',filetypes=[('CSV','*.csv')])
        if not path:
            return
        with open(path,'w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream,delimiter=';')
            writer.writerow(['Tarih','Kurum','Kelimeler','Sayfalar','PDF bağlantısı'])
            for row in self.store.results():
                values=[row['day'],row['title'],row['terms'],row['hit_pages'],row['url']]
                writer.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in values])
        self.status.set('CSV dosyası kaydedildi')

    def make_tray(self):
        try:
            import pystray
            from PIL import Image,ImageDraw
            image=Image.new('RGB',(64,64),'#183a67')
            draw=ImageDraw.Draw(image)
            draw.rounded_rectangle((15,9,48,55),radius=4,fill='white')
            for y in (20,29,38):
                draw.line((22,y,41,y),fill='#183a67',width=3)
            menu=pystray.Menu(pystray.MenuItem('Sonuçları göster',lambda *args:self.messages.put('__show__'),default=True),
                              pystray.MenuItem('Şimdi kontrol et',lambda *args:self.engine.wake.set()),
                              pystray.MenuItem('Tamamen çık',lambda *args:self.messages.put('__quit__')))
            self.tray=pystray.Icon('KPSSIlanYakalayici',image,'KPSS İlan Yakalayıcı',menu)
            self.tray.run_detached()
        except Exception:
            self.engine.log.exception('Sistem tepsisi başlatılamadı')
            self.tray=None

    def notify(self,count,title):
        if not self.tray:
            return False
        try:
            self.tray.notify(f'{count} yeni eşleşen ilan. {title[:100]}','KPSS İlan Yakalayıcı')
            return True
        except Exception:
            return False

    def hide(self):
        if self.tray:
            self.root.withdraw()
        else:
            self.root.iconify()

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def quit(self):
        self.engine.close()
        if self.tray:
            self.tray.stop()
        self.root.destroy()

    def mainloop(self):
        self.root.mainloop()
