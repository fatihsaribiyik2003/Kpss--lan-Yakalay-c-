import datetime as dt
import tempfile
import unittest
from watcher.core import Store,Engine,today
from watcher.candidate import analyze,default_profile,listing_matches
from watcher.catalog import ACADEMIC_ALL,ACADEMIC_ENGINEERING,ACADEMIC_UNKNOWN


class SubfilterTests(unittest.TestCase):
    def row(self,text,**profile):
        p=default_profile(dt.date(2026,10,19));p.update(profile)
        result=analyze([{'page':1,'text':text,'quality':'ok'}],p)
        return {'title':'İlan','assessment':result,'catalog':result['catalog']}

    def test_kpss_none_is_all_kpss_not_personal_eligibility(self):
        row=self.row('Memur alım ilanı. Hukuk lisans mezunu olmak. KPSS P48 en az 90 puan. YDS en az 90 puan almış olmak.',has_kpss=False)
        self.assertTrue(listing_matches(row,'kpss','Hiçbiri (tüm KPSS)'))
        self.assertFalse(listing_matches(row,'kpss','Profilime göre'))
        self.assertTrue(listing_matches(row,'all'))

    def test_engineering_includes_other_engineers_and_admin_is_separate(self):
        engineer=self.row('Mühendis alım ilanı. İnşaat mühendisliği lisans mezunu olmak. KPSS P3.')
        admin=self.row('Büro personeli alım ilanı. Herhangi bir lisans mezunu olmak. KPSS P3.')
        self.assertTrue(listing_matches(engineer,'kpss','Mühendislik / bilişim'))
        self.assertFalse(listing_matches(engineer,'kpss','Düz memur / idari'))
        self.assertTrue(listing_matches(admin,'kpss','Düz memur / idari'))
        self.assertFalse(listing_matches(admin,'kpss','Mühendislik / bilişim'))

    def test_staff_word_without_kpss_or_unrelated_kpss_reference_is_not_hiring(self):
        for text in ('Personel alım ilanı. İşçi kurası yapılacaktır.','İhalelere katılmaktan yasaklama kararı. KPSS evrakının arşivlenmesi.'):
            self.assertFalse(listing_matches(self.row(text),'kpss'))

    def test_ocr_hiring_and_military_notice_are_not_silently_omitted(self):
        for text in ('Sözleşmelipersonelalnacaktır. 2024 KPSS P93. Koruma ve Güvenlik Görevlisi.',
                     '2027 YILI MUVAZZAF SUBAY TEMİN İLANI. 2026 KPSS puanı şartı.'):
            self.assertTrue(listing_matches(self.row(text),'kpss'))
        self.assertTrue(listing_matches(self.row('Memur alım ilanı. Kamu Personeli Seçme Sınavından en az 70 puan almış olmak.'),'kpss'))

    def test_salary_reference_does_not_create_admin_vacancy(self):
        text='Mühendis alım ilanı. İnşaat mühendisliği lisans mezunu olmak. KPSS P3. '+('İnşaat alanında özel şartlar. '*230)+'Ajans uzman personel ve destek personeli ücretlerini yönetim kurulu belirler.'
        row=self.row(text)
        self.assertTrue(listing_matches(row,'kpss','Mühendislik / bilişim'))
        self.assertFalse(listing_matches(row,'kpss','Düz memur / idari'))

    def test_academic_department_title_is_not_the_required_degree(self):
        row=self.row('Öğretim üyesi alım ilanı. Yazılım Mühendisliği Bölümü. Bilgisayar Mühendisliği lisans mezunu olmak.')
        self.assertTrue(listing_matches(row,'academic','Bilgisayar Mühendisliği'))
        self.assertFalse(listing_matches(row,'academic','Yazılım Mühendisliği'))
        self.assertTrue(listing_matches(row,'academic',ACADEMIC_ENGINEERING))
        self.assertTrue(listing_matches(row,'academic',ACADEMIC_ALL))
        self.assertFalse(listing_matches(row,'kpss'))

    def test_alternative_fields_and_docent_degree_keep_all_options(self):
        row=self.row('Öğretim üyesi alım ilanı. Doçentliğini Bilgisayar Mühendisliği ya da Yazılım Mühendisliği alanında almış olmak.')
        for field in ('Bilgisayar Mühendisliği','Yazılım Mühendisliği'):
            self.assertTrue(listing_matches(row,'academic',field))
        evidence=row['catalog']['academic_field_evidence']
        self.assertEqual({e['page'] for e in evidence},{1})

    def test_unknown_academic_field_has_its_own_view(self):
        row=self.row('Öğretim elemanı alım ilanı. İlgili alanda doktora yapmış olmak. Özel koşullar tabloda belirtilmiştir.')
        self.assertTrue(listing_matches(row,'academic',ACADEMIC_UNKNOWN))
        self.assertTrue(listing_matches(row,'academic',ACADEMIC_ALL))
        self.assertFalse(listing_matches(row,'academic','Bilgisayar Mühendisliği'))

    def test_catalog_stays_available_during_personal_profile_update(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            with store.connect() as db:
                doc=db.execute("INSERT INTO documents(url,day,title,status,hash) VALUES(?,?,?,'done','catalog-test')",('https://example.org/x.pdf',today().isoformat(),'Memur')).lastrowid
                db.execute('INSERT INTO pages VALUES(?,?,?,?,?)',('catalog-test',1,'Memur alım ilanı. Herhangi bir lisans mezunu olmak. KPSS P3.','metin','ok'))
            engine=Engine(store)
            try:
                engine.refresh_profile()
                self.assertTrue(listing_matches(store.listing_results()[0],'kpss'))
                p=store.setting('candidate_profile');p['has_kpss']=False;store.set_setting('candidate_profile',p)
                row=store.listing_results()[0]
                self.assertIsNone(row['assessment'])
                self.assertTrue(listing_matches(row,'kpss'))
                self.assertFalse(listing_matches(row,'kpss','Profilime göre'))
                self.assertTrue(listing_matches(row,'all'))
            finally:
                for handler in engine.log.handlers[:]:
                    handler.close();engine.log.removeHandler(handler)
