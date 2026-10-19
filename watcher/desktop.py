from __future__ import annotations

import csv
import ctypes
import datetime as dt
import json
import math
import re
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import webbrowser

from .core import Store, Engine, today
from .calendar_widget import ScanCalendar
from .access import OwnerVault
from .candidate import CATEGORY_LABELS, ROUTE_LABELS, listing_matches
from .catalog import KPSS_OPTIONS,ACADEMIC_ALL,ACADEMIC_ENGINEERING,ACADEMIC_UNKNOWN


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
        self.root.geometry('1200x800')
        self.root.minsize(1000,700)
        self.root.configure(bg='#f4f6fa')
        self.root.protocol('WM_DELETE_WINDOW',self.hide)
        self.tray = None
        self.current_rows = {}
        self.result_snapshot = None
        self.error_snapshot = None
        self.log_snapshot = None
        self.admin_key = None
        self.vault = OwnerVault()
        self.admin_failures = 0
        self.admin_retry_after = 0
        self.reindex_requested = threading.Event()
        self.reindex_requested.set()
        self.status = tk.StringVar(value='Otomatik takip hazırlanıyor…')
        self.summary = tk.StringVar()
        self.filter_summary = tk.StringVar()
        self.range_summary = tk.StringVar()
        self.profile_feedback=tk.StringVar(value='Bu bilgiler KPSS → Profilime göre alt seçeneğini etkiler. Değişiklikten sonra kaydet.')
        self.pending_profile=False
        self.profile_saved=False
        self.profile_before_count=0
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
        style.configure('Primary.TButton',background='#225acb',foreground='white',padding=(14,9))
        style.map('Primary.TButton',background=[('disabled','#dce2ec'),('active','#1849aa')],foreground=[('disabled','#7b879b')])
        style.configure('TNotebook.Tab',padding=(16,9),background='#e8edf5',foreground='#18243c',expand=(0,0,0,0))
        style.map('TNotebook.Tab',padding=[],expand=[],
                  background=[('selected','#225acb'),('active','#dce6f7')],
                  foreground=[('selected','white')],
                  lightcolor=[('selected','#225acb'),('!selected','#e8edf5')])
        style.configure('Filter.TRadiobutton',padding=(12,9),background='#e8edf5',foreground='#18243c',indicatoron=False)
        style.map('Filter.TRadiobutton',background=[('selected','#225acb')],foreground=[('selected','white')])
        style.configure('Treeview',rowheight=34,font=('Segoe UI',10),background='white',fieldbackground='white')
        style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),padding=8)
        outer = ttk.Frame(self.root,padding=16)
        outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='KPSS İlan Yakalayıcı',style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer,text='İlanları bul, şartları incele, başvurularını takip et.',style='Muted.TLabel').pack(anchor='w',pady=(4,8))
        ttk.Label(outer,textvariable=self.summary,font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,8))
        controls=ttk.Frame(outer)
        controls.pack(fill='x',pady=(0,8))
        ttk.Button(controls,text='Yeni ilanları kontrol et',command=self.check_now,style='Primary.TButton').pack(side='left')
        self.pause_button=ttk.Button(controls,text='Devam et' if self.store.setting('paused') else 'Duraklat',command=self.pause)
        self.pause_button.pack(side='left',padx=8)
        self.tracking_state=tk.StringVar()
        ttk.Label(controls,textvariable=self.tracking_state,style='Muted.TLabel').pack(side='left',padx=10)
        ttk.Label(outer,textvariable=self.status,style='Muted.TLabel',wraplength=1050).pack(side='bottom',anchor='w',pady=(8,0))
        body=ttk.Frame(outer)
        body.pack(fill='both',expand=True)
        sidebar=ttk.Frame(body)
        sidebar.pack(side='right',fill='y',padx=(12,0))
        self.calendar=ScanCalendar(sidebar)
        self.calendar.pack(side='top',anchor='e')
        quick_help=ttk.Frame(sidebar,padding=12)
        quick_help.pack(fill='x')
        ttk.Label(quick_help,text='Nasıl kullanırım?',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,8))
        ttk.Label(quick_help,text='1. Bir ilan grubu seç.\n2. İlanı seçip PDF’yi incele.\n3. Başvurduğunda “Başvurdum” de.',style='Muted.TLabel',wraplength=235).pack(anchor='w')
        sidebar.bind('<Configure>',lambda e:quick_help.pack(fill='x') if e.height>520 else quick_help.pack_forget())
        tabs=ttk.Notebook(body)
        self.tabs=tabs
        tabs.pack(side='left',fill='both',expand=True)
        results=ttk.Frame(tabs,padding=10)
        self.results_tab=results
        scan_page,scan_range=self.scroll_panel(tabs,18)
        settings_tab=ttk.Frame(tabs,padding=10)
        profile_page,profile_tab=self.scroll_panel(tabs,18)
        self.profile_tab=profile_page
        tabs.add(results,text='İlanlar')
        tabs.add(profile_page,text='Profilim')
        tabs.add(scan_page,text='Tarama')
        tabs.add(settings_tab,text='Ayarlar ve yardım')
        advanced=ttk.Notebook(settings_tab)
        advanced.pack(fill='both',expand=True)
        settings_page,settings=self.scroll_panel(advanced,14)
        errors=ttk.Frame(advanced,padding=10)
        logs=ttk.Frame(advanced,padding=10)
        advanced.add(settings_page,text='Genel ve yardım')
        advanced.add(errors,text='Okuma sorunları')
        advanced.add(logs,text='Teknik günlük')
        filters=ttk.Frame(results)
        filters.pack(fill='x',pady=(0,8))
        self.list_mode=tk.StringVar(value='all')
        self.profile_route=tk.StringVar(value=KPSS_OPTIONS[0])
        self.filter_mode='all'
        self.list_query=tk.StringVar()
        self.mode_buttons={}
        for value,label in (('all','Tümü'),('kpss','KPSS'),('academic','Akademik'),('applied','Başvurduklarım')):
            button=ttk.Radiobutton(filters,text=label,value=value,variable=self.list_mode,style='Filter.TRadiobutton',command=self.filter_changed)
            button.pack(side='left',padx=(0,5))
            self.mode_buttons[value]=button
        self.subfilter_bar=ttk.Frame(results)
        ttk.Label(self.subfilter_bar,text='Alt filtre:').pack(side='left',padx=(0,8))
        self.route_input=ttk.Combobox(self.subfilter_bar,textvariable=self.profile_route,values=KPSS_OPTIONS,state='disabled',width=34)
        self.route_input.pack(side='left',fill='x',expand=True)
        self.route_input.bind('<<ComboboxSelected>>',self.filter_changed)
        self.edit_profile_button=ttk.Button(self.subfilter_bar,text='Profilimi düzenle',command=lambda:self.tabs.select(self.profile_tab))
        self.edit_profile_button.pack(side='left',padx=(8,0))
        searchbar=ttk.Frame(results)
        self.searchbar=searchbar
        searchbar.pack(fill='x',pady=(0,8))
        ttk.Label(searchbar,text='Kurum veya tarih ara:').pack(side='left',padx=(0,6))
        self.search_input=ttk.Entry(searchbar,textvariable=self.list_query,width=20)
        self.search_input.pack(side='left',fill='x',expand=True)
        self.list_query.trace_add('write',lambda *_: self.refresh())
        self.clear_search_button=ttk.Button(searchbar,text='Aramayı sil',command=lambda:self.list_query.set(''))
        self.clear_search_button.pack(side='left',padx=(6,0))
        self.reset_button=ttk.Button(searchbar,text='Tüm ilanlara dön',command=self.clear_filters)
        self.reset_button.pack(side='left',padx=(6,0))
        self.filter_label=ttk.Label(results,textvariable=self.filter_summary,style='Muted.TLabel',wraplength=760)
        self.filter_label.pack(anchor='w',pady=(0,6),fill='x')
        self.filter_label.bind('<Configure>',lambda e:self.filter_label.configure(wraplength=e.width))
        self.tree=self.table(results,('date','title','route','assessment','application','pages'),('Tarih','Kurum / ilan','İlan türü','Profil değerlendirmesi','Başvuru','Sayfa'),(85,300,145,150,100,60))
        self.tree.configure(displaycolumns=('date','title','route','application'))
        self.tree.tag_configure('applied',background='#e8f5ee',foreground='#16643b')
        self.tree.tag_configure('notice',foreground='#8b5613')
        self.tree.tag_configure('alternate',background='#f4f7fc')
        self.tree.bind('<<TreeviewSelect>>',self.details)
        self.tree.bind('<Double-1>',lambda event:self.open_pdf())
        self.tree.bind('<Return>',lambda event:self.open_pdf())
        self.root.bind('<Control-f>',self.focus_search)
        detail_frame=ttk.Frame(results)
        detail_frame.pack(fill='x',pady=6)
        self.detail=tk.Text(detail_frame,height=5,wrap='word',font=('Segoe UI',10),relief='flat',padx=10,pady=8)
        detail_scroll=ttk.Scrollbar(detail_frame,orient='vertical',command=self.detail.yview)
        self.detail.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.pack(side='right',fill='y')
        self.detail.pack(side='left',fill='x',expand=True)
        self.detail.insert('1.0','İlgili metni görmek için bir ilan seçin. PDF’yi açmak için çift tıklayın.')
        self.detail.configure(state='disabled')
        actions=ttk.Frame(results)
        actions.pack(fill='x')
        self.pdf_button=ttk.Button(actions,text='PDF’yi aç',command=self.open_pdf,state='disabled',style='Primary.TButton')
        self.pdf_button.pack(side='left')
        self.source_button=ttk.Button(actions,text='Resmî kaynağı aç',command=self.open_source,state='disabled')
        self.source_button.pack(side='left',padx=8)
        self.applied_button=ttk.Button(actions,text='Başvurdum',command=self.toggle_applied,state='disabled')
        self.applied_button.pack(side='left')
        self.detail_button=ttk.Button(actions,text='Ayrıntıları büyüt',command=self.expand_details,state='disabled')
        self.detail_button.pack(side='left',padx=8)
        ttk.Label(errors,text='Hatalı indirmeler otomatik yeniden denenir. OCR kontrolü gereken dosyalar burada kalır.',wraplength=900).pack(anchor='w',pady=(0,8))
        self.errors=self.table(errors,('date','title','state','error'),('Tarih','Kurum / adres','Durum','Açıklama'),(90,300,110,440))
        ttk.Button(errors,text='Seçili PDF’yi aç',command=self.open_error).pack(anchor='w',pady=8)
        ttk.Button(errors,text='Başarısız indirmeleri şimdi yeniden dene',command=self.retry).pack(anchor='w')
        self.build_profile(profile_tab)
        ttk.Label(scan_range,text='Geçmiş taraması',font=('Segoe UI',16,'bold')).pack(anchor='w',pady=(0,12))
        ttk.Label(scan_range,text='Bugün dahil son kaç gün taransın?').pack(anchor='w')
        self.scan_days=tk.StringVar(value=str(self.store.scan_days()))
        self.days_input=ttk.Spinbox(scan_range,from_=1,to=7,textvariable=self.scan_days,width=10,state='readonly')
        self.days_input.pack(anchor='w',pady=10)
        ttk.Label(scan_range,textvariable=self.range_summary,wraplength=620,style='Muted.TLabel').pack(anchor='w',pady=(0,12))
        ttk.Button(scan_range,text='Seçilen aralığı kaydet ve tara',command=self.scan_selected).pack(anchor='w')
        self.admin_button=ttk.Button(scan_range,text='Yönetici girişi',command=self.toggle_admin)
        self.admin_button.pack(anchor='w',pady=(20,8))
        self.admin_state=tk.StringVar(value='Normal kullanıcı: 1–7 gün. Daha eski tarama yalnızca proje yöneticisi tarafından yetkilendirilebilir.')
        ttk.Label(scan_range,textvariable=self.admin_state,wraplength=620,style='Muted.TLabel').pack(anchor='w')
        ttk.Label(scan_range,text='Aralık her gün bugüne göre hesaplanır; uygulama açık kaldıkça geriye doğru büyümez.\n\n'
                  'Aralık dışındaki bekleyen işler işlenmez. Önceden okunmuş ilanlar ve takvim kayıtları korunur. '
                  'Aralık değiştiğinde mevcut PDF sayfası tamamlandıktan sonra yeni sınır uygulanır.',
                  wraplength=620).pack(anchor='w',pady=18)
        self.update_range_summary()
        ttk.Label(settings,text='Etkin tarama aralığı').grid(row=0,column=0,sticky='w',pady=9)
        ttk.Label(settings,textvariable=self.range_summary,wraplength=300).grid(row=0,column=1,sticky='w',padx=16)
        ttk.Label(settings,text='Ek kelime işaretleri (virgülle ayırın)').grid(row=1,column=0,sticky='w',pady=9)
        self.terms=tk.StringVar(value=', '.join(self.store.setting('terms')))
        ttk.Entry(settings,textvariable=self.terms,width=35).grid(row=1,column=1,sticky='w',padx=16)
        ttk.Label(settings,text='Kontrol aralığı (dakika, en az 5)').grid(row=2,column=0,sticky='w',pady=9)
        self.interval=tk.StringVar(value=str(self.store.setting('interval_minutes')))
        ttk.Entry(settings,textvariable=self.interval,width=10).grid(row=2,column=1,sticky='w',padx=16)
        self.startup=tk.BooleanVar(value=self.store.setting('autostart'))
        ttk.Checkbutton(settings,text='Windows oturumu açılınca arka planda başlat',variable=self.startup).grid(row=3,column=0,columnspan=2,sticky='w',pady=10)
        ttk.Button(settings,text='Ayarları kaydet',command=self.save).grid(row=4,column=0,sticky='w',pady=12)
        info=('Tümü: okunmayı bekleyenler dahil bütün ilanlar.\n'
              'KPSS: KPSS bağlantılı ilanlar. “Hiçbiri” bütün KPSS ilanlarını gösterir.\n'
              'KPSS → Profilime göre: yalnız kişisel bilgilerine göre ön adaylar.\n'
              'Akademik: aranan mezuniyet alanlarıyla filtrelenen akademik duyurular.\n'
              'Başvurduklarım: senin başvuru işareti koyduğun ilanlar.\n\n'
              '“Şartları incele” bir hata değildir; puan, dil veya özel şartı PDF’den doğrulaman gerekir. '
              'Tarama, Resmî Gazete günlük Çeşitli İlanlar bölümünü izler.\n\n'
              'Pencereyi kapatınca takip sistem tepsisinde sürer. Bilgisayar kapalıyken tarama yapılamaz. '
              'Ctrl+F ile arama kutusuna geçebilir, seçili ilanı Enter ile açabilirsin.')
        info_label=ttk.Label(settings,text=info,wraplength=670,style='Muted.TLabel')
        info_label.grid(row=5,column=0,columnspan=2,sticky='w',pady=14)
        settings.bind('<Configure>',lambda e:info_label.configure(wraplength=max(240,e.width-40)),add='+')
        ttk.Button(settings,text='Veri klasörünü aç',command=lambda:os.startfile(self.store.directory)).grid(row=6,column=0,sticky='w')
        ttk.Button(settings,text='Görünen ilanları CSV’ye aktar',command=self.export).grid(row=6,column=1,sticky='w',padx=16)
        ttk.Button(settings,text='Uygulamayı tamamen kapat',command=self.quit).grid(row=7,column=0,columnspan=2,sticky='w',pady=(12,0))
        self.logview=tk.Text(logs,wrap='word',font=('Consolas',10),relief='flat',padx=8,pady=8)
        self.logview.pack(fill='both',expand=True)

    def build_profile(self,parent):
        profile=self.store.setting('candidate_profile')
        ttk.Label(parent,text='Aday profilin',font=('Segoe UI',16,'bold')).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,10))
        ttk.Label(parent,text='Bilgisayar Mühendisliği • Lisans mezunu').grid(row=1,column=0,columnspan=2,sticky='w',pady=(0,12))
        self.has_kpss=tk.BooleanVar(value=profile['has_kpss'])
        ttk.Checkbutton(parent,text='KPSS puanım var',variable=self.has_kpss).grid(row=2,column=0,columnspan=2,sticky='w')
        fields=ttk.Frame(parent)
        fields.grid(row=3,column=0,columnspan=2,sticky='w',pady=10)
        self.kpss_score=tk.StringVar(value='' if profile['kpss_score'] is None else str(profile['kpss_score']))
        self.kpss_type=tk.StringVar(value=profile['kpss_type'] or 'Belirtilmedi')
        self.kpss_year=tk.StringVar(value='' if profile['kpss_year'] is None else str(profile['kpss_year']))
        for col,label in [(0,'Puan (isteğe bağlı)'),(2,'Puan türü'),(4,'Sınav yılı')]:
            ttk.Label(fields,text=label).grid(row=0,column=col,sticky='w',padx=(0,8))
        ttk.Entry(fields,textvariable=self.kpss_score,width=9).grid(row=1,column=0,sticky='w',padx=(0,18))
        ttk.Combobox(fields,textvariable=self.kpss_type,values=('Belirtilmedi','P3','P1','P2'),width=15).grid(row=1,column=2,sticky='w',padx=(0,18))
        ttk.Entry(fields,textvariable=self.kpss_year,width=9).grid(row=1,column=4,sticky='w')
        self.has_language=tk.BooleanVar(value=profile['language_certificate'])
        self.english_available=tk.BooleanVar(value=profile.get('english_available',False))
        language=ttk.Frame(parent)
        language.grid(row=4,column=0,columnspan=2,sticky='w',pady=8)
        ttk.Checkbutton(language,text='İngilizce bilgim var',variable=self.english_available).pack(side='left',padx=(0,12))
        ttk.Checkbutton(language,text='Dil belgem / sınav sonucum var',variable=self.has_language).pack(side='left')
        ttk.Label(parent,text='Dil öğrenme hedefi (YYYY-AA-GG)').grid(row=5,column=0,sticky='w',pady=6)
        self.language_target=tk.StringVar(value=profile['language_target_date'] or '')
        ttk.Entry(parent,textvariable=self.language_target,width=18).grid(row=5,column=1,sticky='w',padx=12)
        ttk.Label(parent,text='Mesleki deneyim (yıl; 0 = yok, boş = bilinmiyor)').grid(row=6,column=0,sticky='w',pady=6)
        self.experience=tk.StringVar(value='' if profile['experience_years'] is None else str(profile['experience_years']))
        ttk.Entry(parent,textvariable=self.experience,width=10).grid(row=6,column=1,sticky='w',padx=12)
        ttk.Button(parent,text='Kaydet ve profilime göre adayları göster',command=self.save_profile).grid(row=7,column=0,columnspan=2,sticky='w',pady=12)
        ttk.Label(parent,textvariable=self.profile_feedback,wraplength=650,style='Muted.TLabel').grid(row=8,column=0,columnspan=2,sticky='w',pady=(0,10))
        explanation=('Profil yalnızca KPSS → Profilime göre seçeneğini daraltır. Genel KPSS, akademik duyurular ve başvuru kayıtların korunur.\n\n'
                     'Boş = bilinmiyor. Puan/tür/yıl ve deneyim yalnızca açıkça okunan şartlarla karşılaştırılır. PDF sayısı aynı kalıp içindeki kadrolar değişebilir.\n\n'
                     'Dil hedefi bir plandır; otomatik İngilizce/belge kazandırmaz. Sonuçlar ön filtredir.')
        ttk.Label(parent,text=explanation,wraplength=650,style='Muted.TLabel').grid(row=9,column=0,columnspan=2,sticky='w')

    def save_profile(self):
        try:
            def optional_number(value,label,maximum):
                if not value.strip():
                    return None
                number=float(value.strip().replace(',','.'))
                if not math.isfinite(number) or not 0<=number<=maximum:
                    raise ValueError(f'{label}: 0–{maximum} arasında olmalı.')
                return number
            score=optional_number(self.kpss_score.get(),'KPSS puanı',100)
            experience=optional_number(self.experience.get(),'Deneyim yılı',60)
            year=int(self.kpss_year.get()) if self.kpss_year.get().strip() else None
            if year is not None and not 2000<=year<=today().year+1:
                raise ValueError('KPSS sınav yılını kontrol edin.')
            raw_kind=self.kpss_type.get().strip()
            kind='' if raw_kind in ('','Belirtilmedi') else raw_kind.upper().replace('KPSS','').replace(' ','')
            if kind and not re.fullmatch(r'P\d{1,3}',kind):
                raise ValueError('KPSS türünü P3 gibi yazın veya Belirtilmedi seçin.')
            target=dt.date.fromisoformat(self.language_target.get()).isoformat() if self.language_target.get().strip() else None
            profile={'degree':'computer_engineering_bachelor','has_kpss':self.has_kpss.get(),
                     'kpss_score':score,'kpss_type':kind,'kpss_year':year,
                     'english_available':self.english_available.get(),'language_certificate':self.has_language.get(),'language_target_date':target,
                     'experience_years':experience}
            self.profile_before_count=sum(r['assessment']['kpss_match'] for r in self.store.profile_results())
            self.store.set_setting('candidate_profile',profile)
            self.pending_profile=True
            self.profile_saved=True
            self.profile_feedback.set('Profil kaydedildi. Kayıtlı ilanlar yeni bilgilerinle değerlendiriliyor…')
            self.reindex_requested.set()
            self.engine.wake.set()
            self.list_mode.set('kpss')
            self.profile_route.set('Profilime göre')
            self.filter_mode='kpss'
            self.list_query.set('')
            self.tabs.select(self.results_tab)
            self.filter_changed()
            self.status.set('Profil kaydedildi. Kayıtlı metinler yeniden değerlendiriliyor; PDF indirme ve OCR yapılmaz.')
        except (ValueError,TypeError) as exc:
            messagebox.showerror('Profil kaydedilemedi',str(exc),parent=self.root)

    def filter_changed(self,event=None):
        mode=self.list_mode.get()
        if mode=='academic':
            fields=sorted({f for r in self.store.listing_results() for f in r['catalog'].get('academic_fields',[])})
            options=(ACADEMIC_ALL,ACADEMIC_ENGINEERING,*fields,ACADEMIC_UNKNOWN)
        else:
            options=KPSS_OPTIONS
        if mode!=self.filter_mode or self.profile_route.get() not in options:
            self.profile_route.set(options[0])
        self.filter_mode=mode
        if mode in ('kpss','academic'):
            self.subfilter_bar.pack(fill='x',pady=(0,8),before=self.searchbar)
        else:
            self.subfilter_bar.pack_forget()
        self.route_input.configure(values=options,state='readonly' if mode in ('kpss','academic') else 'disabled')
        self.refresh()

    def focus_search(self,event=None):
        self.tabs.select(self.results_tab)
        self.search_input.focus_set()
        self.search_input.selection_range(0,'end')
        return 'break'

    def scroll_panel(self,parent,padding):
        shell=ttk.Frame(parent)
        canvas=tk.Canvas(shell,bg='#f4f6fa',highlightthickness=0,width=1,height=1)
        scroll=ttk.Scrollbar(shell,orient='vertical',command=canvas.yview)
        scroll.pack(side='right',fill='y')
        canvas.pack(side='left',fill='both',expand=True)
        canvas.configure(yscrollcommand=scroll.set)
        content=ttk.Frame(canvas,padding=padding)
        item=canvas.create_window((0,0),window=content,anchor='nw')
        content.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width))
        def wheel(event):
            widget=event.widget
            if not isinstance(widget,(tk.Text,ttk.Treeview,ttk.Combobox)) and (widget==canvas or str(widget).startswith(str(content)+'.')):
                if content.winfo_reqheight()>canvas.winfo_height():
                    canvas.yview_scroll(-int(event.delta/120),'units')
                    return 'break'
        self.root.bind_all('<MouseWheel>',wheel,add='+')
        return shell,content

    def clear_filters(self):
        self.list_mode.set('all')
        self.profile_route.set(KPSS_OPTIONS[0])
        self.list_query.set('')
        self.filter_changed()

    def table(self,parent,columns,headings,widths):
        frame=ttk.Frame(parent)
        frame.pack(fill='both',expand=True)
        tree=ttk.Treeview(frame,columns=columns,show='headings',selectmode='browse',height=4)
        for col,heading,width in zip(columns,headings,widths):
            tree.heading(col,text=heading)
            tree.column(col,width=width,minwidth=50)
        bar=ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y')
        tree.pack(side='left',fill='both',expand=True)
        def resize(event):
            available=max(1,tree.winfo_width()-4)
            visible=tree['displaycolumns']
            visible=columns if visible==('#all',) else visible
            weights=dict(zip(columns,widths))
            total=sum(weights[col] for col in visible)
            for col in visible:
                tree.column(col,width=max(50,int(available*weights[col]/total)))
        tree.bind('<Configure>',resize)
        return tree

    def refresh(self):
        scanned=self.store.scanned_days()
        self.calendar.update_days(scanned)
        self.update_range_summary()
        lower,upper=self.store.scan_start().isoformat(),today().isoformat()
        all_rows=self.store.listing_results()
        if self.list_mode.get()=='academic':
            fields=sorted({f for r in all_rows for f in r['catalog'].get('academic_fields',[])})
            self.route_input.configure(values=(ACADEMIC_ALL,ACADEMIC_ENGINEERING,*fields,ACADEMIC_UNKNOWN))
        if self.pending_profile and all(r['assessment'] is not None for r in all_rows if r['status'] in ('done','partial')):
            after=sum(bool(r['assessment'] and r['assessment']['kpss_match']) for r in all_rows)
            self.pending_profile=False
            message=f'Profil uygulandı: {self.profile_before_count} → {after} KPSS ön adayı PDF.'
            self.profile_feedback.set(message)
            self.status.set(message)
        rows=[r for r in all_rows if listing_matches(r,self.list_mode.get(),self.profile_route.get(),self.list_query.get())]
        personal=self.list_mode.get()=='kpss' and self.profile_route.get()=='Profilime göre'
        columns=('date','title','route','assessment','application') if personal else ('date','title','route','application')
        if tuple(self.tree['displaycolumns'])!=columns:
            self.tree.configure(displaycolumns=columns)
            self.tree.event_generate('<Configure>')
        if personal:
            self.edit_profile_button.pack(side='left',padx=(8,0))
        else:
            self.edit_profile_button.pack_forget()
        self.clear_search_button.configure(state='normal' if self.list_query.get() else 'disabled')
        self.reset_button.configure(state='normal' if self.list_mode.get()!='all' or self.list_query.get() else 'disabled')
        for mode,label in (('all','Tümü'),('kpss','KPSS'),('academic','Akademik'),('applied','Başvurduklarım')):
            count=sum(listing_matches(r,mode) for r in all_rows)
            counter='…' if self.pending_profile and mode=='kpss' and not any(r['catalog'] for r in all_rows) else str(count)
            self.mode_buttons[mode].configure(text=f'{label} ({counter})')
        self.current_rows={str(r['id']):dict(r) for r in rows}
        snapshot=json.dumps([self.list_mode.get(),self.profile_route.get(),rows],sort_keys=True,ensure_ascii=True)
        if snapshot!=self.result_snapshot:
            self.result_snapshot=snapshot
            selected=self.tree.selection()
            self.tree.delete(*self.tree.get_children())
            for index,row in enumerate(rows):
                review=row['assessment']
                state={'pending':'Okuma bekliyor','processing':'Okunuyor…','error':'Yeniden denenecek','done':'Değerlendiriliyor…','partial':'OCR kontrolü'}.get(row['status'],'Bekliyor')
                info=review or row['catalog']
                area='Akademik alım' if row['catalog'].get('academic') else (ROUTE_LABELS[review['route']] if review else 'Henüz belirlenmedi')
                if row['catalog'].get('kpss_related') and not (self.list_mode.get()=='kpss' and self.profile_route.get()=='Profilime göre'):
                    jobs=row['catalog'].get('jobs',[])
                    area='Birden fazla alan' if len(jobs)>1 else {'engineering':'Mühendislik / bilişim','admin':'İdari / destek','other':'Diğer kadrolar'}.get(jobs[0] if jobs else '',area)
                if info.get('notice_kind') in ('cancel','correction'):
                    area='İptal duyurusu' if info['notice_kind']=='cancel' else 'Düzeltme duyurusu'
                category=({'review':'Şartları incele','pre_match':'Ön aday'}.get(review['category'],CATEGORY_LABELS[review['category']]) if review else state)
                tags=('applied',) if row['applied_at'] else (('notice',) if info.get('notice_kind') in ('cancel','correction') else (('alternate',) if index%2 else ()))
                date=dt.date.fromisoformat(row['day']).strftime('%d.%m.%Y')
                self.tree.insert('','end',iid=str(row['id']),tags=tags,values=(date,row['title'],area,category,'Başvuruldu' if row['applied_at'] else '—',row['hit_pages']))
            if selected and selected[0] in self.current_rows:
                self.tree.selection_set(selected[0])
            elif not self.tree.selection():
                self.applied_button.configure(state='disabled',text='Başvurdum')
                self.pdf_button.configure(state='disabled')
                self.source_button.configure(state='disabled')
                self.detail_button.configure(state='disabled')
                self.detail.configure(state='normal')
                self.detail.delete('1.0','end')
                empty='Bu seçime uyan ilan yok. Aramanı sil veya “Tüm ilanlara dön” düğmesine bas.'
                if self.list_mode.get()=='applied' and not any(r['applied_at'] for r in all_rows):
                    empty='Henüz başvuru işaretlemedin. Tüm ilanlardan bir ilan seçip “Başvurdum” düğmesine basabilirsin.'
                self.detail.insert('1.0','Bir ilan seçerek açıklamayı okuyabilir, çift tıklayarak PDF’yi açabilirsin.' if rows else empty)
                self.detail.configure(state='disabled')
        failures=self.store.failures()
        with self.store.connect() as db:
            counts={r[0]:r[1] for r in db.execute('SELECT status,COUNT(*) FROM documents GROUP BY status')}
            days=db.execute("SELECT * FROM days WHERE status='error' ORDER BY day DESC LIMIT 100").fetchall()
            pending=db.execute("SELECT COUNT(*) FROM documents WHERE status IN ('pending','processing') AND day>=? AND day<=?",(lower,upper)).fetchone()[0]
            missing=db.execute("SELECT COUNT(*) FROM days WHERE status='missing'").fetchone()[0]
        errors_snapshot=([tuple(r) for r in failures],[tuple(r) for r in days],lower,upper)
        if errors_snapshot!=self.error_snapshot:
            self.error_snapshot=errors_snapshot
            self.errors.delete(*self.errors.get_children())
            for row in failures:
                state='OCR kontrolü' if row['status']=='partial' else ('Yeniden denenecek' if lower<=row['day']<=upper else 'Aralık dışında')
                self.errors.insert('','end',iid='doc'+str(row['id']),values=(row['day'],row['title'],state,row['error']))
            for row in days:
                self.errors.insert('','end',values=(row['day'],'İlan dizini','Yeniden denenecek' if lower<=row['day']<=upper else 'Aralık dışında',row['error']))
        hints={'all':'Bütün kayıtlar; okunmayı bekleyenler dahil.',
               'kpss':'KPSS bağlantılı ilanlar. “Hiçbiri” tümünü gösterir; “Profilime göre” kişisel ön adayları gösterir.',
               'academic':'Akademik duyurular; düzeltme ve iptaller dahil. Aranan mezuniyet alanını seçebilirsin.',
               'applied':'Başvuru işareti koyduğun ilanlar. Yeşil satırlar başvurularını gösterir.'}
        if personal:
            hints['kpss']='Profiline göre ön adaylar. “Şartları incele” yazan ilanların eksik bilgilerini PDF’den doğrula.'
        if personal and not self.store.setting('candidate_profile')['has_kpss']:
            hints['kpss']='Profilinde KPSS puanı kapalı. Aday profilim sekmesinden “KPSS puanım var” seçeneğini açıp kaydet.'
        self.filter_summary.set(f"{len(rows)} ilan gösteriliyor • {hints[self.list_mode.get()]}")
        if self.profile_saved and not self.pending_profile and personal:
            self.filter_summary.set(f'{len(rows)} / {len(all_rows)} ilan • '+self.profile_feedback.get())
        if self.pending_profile and personal:
            self.filter_summary.set('Profil uygulanıyor… Bu sırada sonuçlar geçici olarak boş görünebilir. İndirme/OCR tekrarlanmaz.')
        self.summary.set(f"{len(all_rows)} ilan arşivde   •   {sum(bool(r['applied_at']) for r in all_rows)} başvurum   •   {pending} belge okunmayı bekliyor")
        self.tracking_state.set('Otomatik takip duraklatıldı' if self.store.setting('paused') else f'Otomatik takip açık • Son {self.store.scan_days()} gün')
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
            elif item=='__check__':
                self.check_now()
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
        item=self.current_rows.get(selection[0])
        if item:
            self.applied_button.configure(state='normal',text='Başvuru işaretini kaldır' if item['applied_at'] else 'Başvurdum')
            self.pdf_button.configure(state='normal')
            self.source_button.configure(state='normal')
            self.detail_button.configure(state='normal')
        review=item['assessment'] if item else None
        text=''
        if review:
            personal=self.list_mode.get()=='kpss' and self.profile_route.get()=='Profilime göre'
            label={'review':'Şartları incele','pre_match':'Ön aday'}.get(review['category'],CATEGORY_LABELS[review['category']])
            text=f"{item['title']} • {item['day']}\n"
            if personal:
                text+=f'Profil değerlendirmesi: {label} • {ROUTE_LABELS[review["route"]]}\n'
                text+='\n'.join('• '+reason for reason in review['reasons'])
                text+='\n\nDayanaklar:\n'+'\n\n'.join(f"Sayfa {e['page']} • {e['kind']}\n{e['text']}" for e in review['evidence'])
                text+='\n\n'+review['note']
            else:
                text+='Başvuru şartlarını PDF’den incele. Kişisel ön adaylar için KPSS → Profilime göre seç.\n'
            text+='\n\nİlan metninden bölümler:\n'
        catalog=item.get('catalog',{}) if item else {}
        academic_text=''
        if catalog.get('academic'):
            fields=catalog.get('academic_fields',[])
            academic_text='Akademik aranan alan etiketleri: '+(', '.join(fields) if fields else 'Alan net okunamadı; belgeyi kontrol et.')
            evidence=catalog.get('academic_field_evidence',[])
            if self.list_mode.get()=='academic' and self.profile_route.get() in fields:
                evidence=[e for e in evidence if e['field']==self.profile_route.get()]
            academic_text+='\n\n'+'\n\n'.join(f"Sayfa {e['page']} • {e['field']}\n{e['text']}" for e in evidence)+'\n\n'
        if not review and item:
            text=f"{item['title']} • {item['day']}\nBu PDF henüz değerlendirilmedi. İlan tüm kayıtlar görünümünde korunur. Resmî kaynaktan açabilir veya otomatik okumanın tamamlanmasını bekleyebilirsin.\n{item['error'] or ''}"
        text=academic_text+text
        text+='\n\n'.join(f"Sayfa {r['page']} • {r['term']}\n…{r['excerpt']}…" for r in rows)
        if item and item['applied_at']:
            text='BAŞVURULDU • İşaretleme tarihi: '+item['applied_at'][:10]+'\nBu işaret senin kaydındır; kurumun başvuru onayı değildir.\n\n'+text
        self.detail.configure(state='normal')
        self.detail.delete('1.0','end')
        self.detail.insert('1.0',text)
        self.detail.configure(state='disabled')

    def expand_details(self):
        if not self.selected():
            return
        window=tk.Toplevel(self.root)
        window.title('İlan ayrıntıları')
        window.geometry('800x580')
        window.minsize(550,350)
        window.transient(self.root)
        frame=ttk.Frame(window,padding=16)
        frame.pack(fill='both',expand=True)
        ttk.Button(frame,text='Kapat',command=window.destroy).pack(side='bottom',anchor='e',pady=(10,0))
        scroll=ttk.Scrollbar(frame)
        scroll.pack(side='right',fill='y')
        text=tk.Text(frame,wrap='word',font=('Segoe UI',11),relief='flat',padx=12,pady=12,yscrollcommand=scroll.set)
        text.pack(fill='both',expand=True)
        scroll.configure(command=text.yview)
        text.insert('1.0',self.detail.get('1.0','end-1c'))
        text.configure(state='disabled')
        window.bind('<Escape>',lambda e:window.destroy())

    def selected(self):
        ids=self.tree.selection()
        return self.current_rows.get(ids[0]) if ids else None

    def toggle_applied(self):
        row=self.selected()
        if not row:
            return
        applied=not bool(row['applied_at'])
        self.store.set_applied(row['id'],applied)
        self.refresh()
        self.details()
        self.status.set('Başvuru işaretlendi. Başvurduklarım görünümünden bulabilirsin.' if applied else 'Başvuru işareti geri alındı; ilan korunuyor.')

    def open_pdf(self):
        row=self.selected()
        if row and row['path'] and Path(row['path']).exists():
            os.startfile(row['path'])
        elif row:
            webbrowser.open(row['url'])

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
        if self.store.setting('paused'):
            self.store.set_setting('paused',False)
            self.pause_button.configure(text='Duraklat')
        self.engine.wake.set()
        self.status.set('Yeni ilanlar kontrol edilecek; otomatik takip açık.')

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
            days=int(self.scan_days.get())
            maximum=(today()-dt.date(2000,1,1)).days+1
            if not 1<=days<=maximum:
                raise ValueError(f'Gün sayısı 1–{maximum} arasında olmalı.')
            preserve_grant=days==self.store.scan_days() and days>7 and self.admin_key is None
            if days>7 and self.admin_key is None and not preserve_grant:
                raise PermissionError('Normal kullanıcı en fazla 7 gün seçebilir. Önce yönetici girişi yapın.')
            interval=int(self.interval.get())
            if not 5<=interval<=1440:
                raise ValueError('Kontrol aralığı 5–1440 dakika arasında olmalı.')
            terms=list(dict.fromkeys(t.strip() for t in self.terms.get().split(',') if t.strip()))
            if not terms or len(terms)>50:
                raise ValueError('1–50 arama kelimesi girin.')
            autostart(self.startup.get())
            if not preserve_grant:
                self.store.set_scan_days(days,self.admin_key)
            for key,value in [('interval_minutes',interval),('terms',terms),('autostart',self.startup.get())]:
                self.store.set_setting(key,value)
            self.update_range_summary()
            self.reindex_requested.set()
            self.engine.wake.set()
            self.status.set('Ayarlar kaydedildi; geçmiş metinler de yeni kelimelerle filtrelenecek')
            return True
        except Exception as exc:
            messagebox.showerror('Ayarlar kaydedilemedi',str(exc),parent=self.root)
            return False

    def update_range_summary(self):
        days=self.store.scan_days()
        self.range_summary.set(f'Bugün dahil son {days} gün' + (' • yönetici onaylı' if days>7 else ' • 1–7 gün sınırı açık'))

    def scan_selected(self):
        if self.save():
            self.store.set_setting('paused',False)
            self.pause_button.configure(text='Duraklat')
            self.engine.wake.set()
            self.status.set(f'Bugün dahil son {self.store.scan_days()} gün taranacak; tamamlanan PDF’ler atlanacak')

    def toggle_admin(self):
        if self.admin_key is not None:
            self.admin_key=None
            self.store.set_scan_days(min(7,self.store.scan_days()))
            self.scan_days.set(str(self.store.scan_days()))
            self.days_input.configure(to=7,state='readonly')
            self.admin_button.configure(text='Yönetici girişi')
            self.admin_state.set('Yönetici modu kapalı. 1–7 gün sınırı yeniden etkin.')
            self.update_range_summary()
            self.engine.wake.set()
            return
        if time.monotonic()<self.admin_retry_after:
            messagebox.showerror('Yönetici girişi','Çok sayıda hatalı deneme. Bir dakika sonra yeniden deneyin.',parent=self.root)
            return
        if not self.vault.available():
            messagebox.showinfo('Yönetici kilidi','Bu Windows hesabında proje sahibinin yönetici anahtarı yok. '
                                'Dağıtılan uygulama yeni bir yönetici hesabı oluşturamaz.',parent=self.root)
            return
        try:
            if self.vault.needs_password():
                password=simpledialog.askstring('İlk yönetici kurulumu','Size özel yönetici anahtarı bulundu. En az 8 karakterlik bir parola belirleyin:',show='*',parent=self.root)
                if password is None:
                    return
                confirm=simpledialog.askstring('Yönetici parolası','Parolayı tekrar yazın:',show='*',parent=self.root)
                if confirm is None:
                    return
                if password!=confirm:
                    raise ValueError('Parolalar eşleşmiyor.')
                key=self.vault.create_password(password)
            else:
                password=simpledialog.askstring('Yönetici girişi','Yönetici parolanız:',show='*',parent=self.root)
                if password is None:
                    return
                key=self.vault.unlock(password)
            self.admin_key=key
            self.admin_failures=0
            self.days_input.configure(state='normal',to=(today()-dt.date(2000,1,1)).days+1)
            self.admin_button.configure(text='Yönetici modunu kapat ve kilitle')
            self.admin_state.set('Yönetici modu açık. 7 günden fazla bir gün sayısı girip Kaydet ve tara düğmesine basabilirsiniz.')
        except Exception as exc:
            self.admin_failures+=1
            if self.admin_failures>=5:
                self.admin_retry_after=time.monotonic()+60
                self.admin_failures=0
            messagebox.showerror('Yönetici girişi',str(exc),parent=self.root)

    def export(self):
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension='.csv',initialfile='ilanlar.csv',filetypes=[('CSV','*.csv')])
        if not path:
            return
        with open(path,'w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream,delimiter=';')
            writer.writerow(['Tarih','Kurum','Başvuru yolu','Profil ön filtresi','Kontrol notları','Sayfalar','PDF bağlantısı','Başvuru durumu','İşaretleme tarihi'])
            for row in self.current_rows.values():
                review=row['assessment']
                values=[row['day'],row['title'],ROUTE_LABELS[review['route']] if review else '',CATEGORY_LABELS[review['category']] if review else row['status'],' | '.join(review['reasons']) if review else 'Henüz değerlendirilmedi',row['hit_pages'],row['url'],'Başvuruldu' if row['applied_at'] else '',row['applied_at'] or '']
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
                              pystray.MenuItem('Şimdi kontrol et',lambda *args:self.messages.put('__check__')),
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
