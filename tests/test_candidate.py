import datetime as dt
import tempfile
import unittest
from unittest.mock import patch

from watcher.candidate import analyze, default_profile
from watcher.core import Store, Engine, today


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.profile=default_profile(dt.date(2026,10,19))

    def review(self,text,quality='ok'):
        return analyze([{'page':1,'text':text,'quality':quality}],self.profile)

    def test_default_profile_matches_user_and_future_plan_is_not_certificate(self):
        self.assertTrue(self.profile['has_kpss'])
        self.assertFalse(self.profile['language_certificate'])
        self.assertIsNone(self.profile['kpss_score'])
        self.assertEqual(self.profile['language_target_date'],'2027-01-19')
        self.profile['language_target_date']='2020-01-01'
        result=self.review('Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. YDS en az 70 puan almış olmak.')
        self.assertEqual(result['category'],'language')

    def test_engineering_degree_without_english_is_a_pre_match(self):
        result=self.review('Mühendis alım ilanı. Bilgisayar Mühendisliği lisans mezunu olmak. KPSS P3 puan türünden en az 70 puan almak.')
        self.assertEqual(result['category'],'pre_match')
        self.assertEqual(result['route'],'technical')
        self.assertTrue(any('eksik' in note for note in result['reasons']))
        self.assertEqual(result['kpss_minimums'],[70.0])

    def test_general_civil_servant_is_not_excluded_for_missing_it_keywords(self):
        result=self.review('Memur alım ilanı. Herhangi bir lisans programından mezun olmak. KPSS P3 puanına sahip olmak.')
        self.assertEqual(result['category'],'pre_match')
        self.assertEqual(result['route'],'general')
        self.assertTrue(result['general_bachelor'])

    def test_4001_is_undergraduate_route_and_4531_is_engineering_route(self):
        general=self.review('Memur alım ilanı. Aranan nitelik kodu 4001. KPSS P3 puanı.')
        technical=self.review('Mühendis alım ilanı. Aranan nitelik kodu 4531. KPSS P3 puanı.')
        self.assertTrue(general['general_bachelor'])
        self.assertTrue(technical['computer_degree'])
        self.assertEqual(general['category'],'pre_match')
        self.assertEqual(technical['category'],'pre_match')

    def test_language_mandatory_is_separate(self):
        result=self.review('Bilgisayar mühendisi alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. YDS sınavından en az 70 puan almış olmak.')
        self.assertEqual(result['category'],'language')
        self.assertTrue(result['language_required'])

    def test_language_waiver_is_not_treated_as_mandatory(self):
        result=self.review('Sözleşmeli bilişim personeli giriş sınavı ilanı. Bilgisayar mühendisliği lisans mezunu olmak. Yabancı dil puanı olmayan veya belge ibraz etmeyen adayların yabancı dil puanı 0 olarak hesaplanacaktır.')
        self.assertTrue(result['language_optional'])
        self.assertNotEqual(result['category'],'language')

    def test_language_not_required_negation(self):
        result=self.review('Memur alım ilanı. Herhangi bir lisans programından mezun olmak. İngilizce belgesi zorunlu değil.')
        self.assertNotEqual(result['category'],'language')

    def test_kpss_threshold_does_not_become_language_threshold(self):
        result=self.review('Personel alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. YDS belgesi hakkında bilgi, KPSS P3 en az 80 puan şartı.')
        self.assertFalse(result['language_required'])
        self.assertEqual(result['category'],'review')

    def test_language_score_does_not_become_kpss_score(self):
        result=self.review('Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. KPSS P3 en az 60 puan ve YDS en az 80 puan almış olmak.')
        self.assertEqual(result['kpss_minimums'],[60.0])
        self.assertEqual(result['category'],'language')

    def test_mixed_pdf_is_not_all_blocked_by_one_positions_language(self):
        result=analyze([
          {'page':1,'quality':'ok','text':'Personel alım ilanı. Memur: herhangi bir lisans programından mezun olmak.'},
          {'page':2,'quality':'ok','text':'Bilgisayar mühendisi: Bilgisayar mühendisliği lisans mezunu olmak. YDS en az 70 puan almış olmak.'}],self.profile)
        self.assertEqual(result['route'],'mixed')
        self.assertEqual(result['category'],'review')
        self.assertTrue(any('PDF bütünü elenmedi' in note for note in result['reasons']))

    def test_bachelor_does_not_match_pure_academic_hiring(self):
        result=self.review('Öğretim üyesi alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. Doktorasını tamamlamış olmak. Doktor öğretim üyesi alınacaktır.')
        self.assertEqual(result['category'],'outside')

    def test_computer_usage_certificate_does_not_override_wrong_degree(self):
        result=self.review('Memur alım ilanı. Hukuk lisans programından mezun olmak. Bilgisayar kullanabilmek ve bilgisayar sertifikasına sahip olmak.')
        self.assertEqual(result['category'],'outside')
        self.assertFalse(result['computer_degree'])

    def test_unrelated_decision_does_not_match_keyword_only(self):
        result=self.review('Kültür varlıklarını koruma kurulu kararı. Bilgisayar çıktısı ve lisans belgesi arşivde tutulacaktır. Parselin sit alanı olarak tesciline karar verildi.')
        self.assertEqual(result['category'],'other')

    def test_unknown_degree_stays_review(self):
        result=self.review('Programcı alım ilanı. KPSS puanı ile adaylar sıralanacaktır. Mezuniyet tablosu ayrıca yayımlanacaktır.')
        self.assertEqual(result['category'],'review')

    def test_experience_and_certificate_are_not_assumed(self):
        result=self.review('Personel alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. En az 3 yıl mesleki tecrübe sahibi olmak. Sertifika sunmak.')
        self.assertEqual(result['category'],'review')
        self.assertTrue(any('Deneyim' in note for note in result['reasons']))
        self.assertTrue(any('ek belge' in note for note in result['reasons']))

    def test_low_quality_relevant_pdf_remains_review(self):
        result=self.review('Memur alım ilanı. Herhangi bir lisans programından mezun olmak.','review')
        self.assertEqual(result['category'],'review')

    def test_certificate_checkbox_does_not_assert_required_score(self):
        self.profile['language_certificate']=True
        result=self.review('Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. YDS en az 90 puan almış olmak.')
        self.assertEqual(result['category'],'review')
        self.assertTrue(any('belgenin türü' in note for note in result['reasons']))

    def test_known_kpss_score_below_threshold_needs_review(self):
        self.profile.update(kpss_score=65,kpss_type='P3',kpss_year=2024)
        result=self.review('Memur alım ilanı. Herhangi bir lisans programından mezun olmak. 2024 KPSS P3 en az 80 puan almak.')
        self.assertEqual(result['category'],'review')

    def test_long_engineering_list_and_compact_ocr_are_not_lost(self):
        result=self.review('Sözleşmeli bilişim personeli giriş sınavı ilanı. Fakültelerin dört yıllık BilgisayarMühendisliği, Yazılım Mühendisliği, Elektrik Mühendisliği, Elektronik Mühendisliği, Elektrik ve Elektronik Mühendisliği ve Endüstri Mühendisliği bölümlerinden veya denk yurt dışı yükseköğretim kurumlarından mezun olmak. Yabancıdilpuanınailişkinbelgeibrazetmeyenlerinsınavpuanısıfırolarakdeğerlendirilir.')
        self.assertTrue(result['computer_degree'])
        self.assertTrue(result['language_optional'])
        self.assertNotEqual(result['category'],'language')

    def test_degree_in_qualification_table_is_kept_for_review(self):
        result=analyze([{'page':1,'quality':'ok','text':'Personel alım ilanı. KPSS şartı. Mezuniyet şartları Tablo 1 içindedir.'},
                        {'page':2,'quality':'ok','text':'Tablo 1. Bölümler: Bilgisayar Mühendisliği, Elektrik Mühendisliği. KPSS P3.'}],self.profile)
        self.assertTrue(result['computer_degree'])
        self.assertNotEqual(result['category'],'outside')

    def test_university_administrative_hiring_is_included(self):
        result=self.review('Üniversite Rektörlüğünden. Büro personeli alım ilanı. Herhangi bir lisans programından mezun olmak. KPSS P3 puanı.')
        self.assertEqual(result['category'],'pre_match')
        self.assertEqual(result['route'],'general')

    def test_english_knowledge_and_exam_certificate_are_separate(self):
        self.profile['english_available']=True
        self.profile['language_certificate']=False
        text='Programcı alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. İngilizce bilmek.'
        self.assertNotEqual(self.review(text)['category'],'language')
        certificate_text='Programcı alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. YDS en az 70 puan almış olmak.'
        self.assertEqual(self.review(certificate_text)['category'],'language')


class ProfileStorageTests(unittest.TestCase):
    def test_cached_non_keyword_document_is_classified_without_download_or_ocr(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            engine=Engine(store)
            try:
                with store.connect() as db:
                    db.execute("INSERT INTO documents(url,day,title,status,hash,pages) VALUES(?,?,?,'done','cached',1)",('https://www.resmigazete.gov.tr/example.pdf',today().isoformat(),'Memur alımı'))
                    db.execute('INSERT INTO pages VALUES(?,?,?,?,?)',('cached',1,'Memur alım ilanı. Aranan nitelik kodu 4001. KPSS P3 puanı.','metin','ok'))
                with patch.object(engine,'fetch',side_effect=AssertionError('İndirme olmamalı')),patch.object(engine.reader,'page',side_effect=AssertionError('OCR olmamalı')):
                    engine.refresh_profile()
                self.assertEqual(len(store.results()),0)
                self.assertEqual(store.profile_results()[0]['category'],'pre_match')
                profile=store.setting('candidate_profile')
                profile['language_certificate']=True
                store.set_setting('candidate_profile',profile)
                self.assertEqual(store.profile_results(),[])
                engine.refresh_profile()
                self.assertEqual(len(store.profile_results()),1)
            finally:
                for handler in engine.log.handlers[:]:
                    handler.close()
                    engine.log.removeHandler(handler)


if __name__=='__main__':
    unittest.main()
