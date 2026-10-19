"""Gerçek PDF denetiminde görülen yapıların küçük, bağımsız regresyon örnekleri."""
import datetime as dt
import unittest
from watcher.candidate import analyze,default_profile,listing_matches


class FilterRegressions(unittest.TestCase):
    def setUp(self):
        self.profile=default_profile(dt.date(2026,10,19))

    def check(self,*texts):
        return analyze([{'page':i+1,'text':t,'quality':'ok'} for i,t in enumerate(texts)],self.profile)

    def test_waived_exam_document_does_not_waive_english_knowledge(self):
        r=self.check('Sözleşmeli bilişim personeli alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. KPSS P3. Yabancı dil puanı olmayanların puanı sıfır sayılır. İngilizce bilgisine sahip olmak.')
        self.assertFalse(r['kpss_match'])
        self.assertEqual(r['category'],'language')
        self.profile['english_available']=True
        self.assertTrue(self.check('Bilişim personeli alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. KPSS P3. İngilizce bilgisine sahip olmak.')['kpss_match'])

    def test_required_c_level_not_hidden_by_unrelated_preference(self):
        r=self.check('Personel alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. KPSS P1. İngilizcedilindenYabancıDilBilgisiSınavındanasgari(C)düzeyinekarşılıkgelenbelgeyebaşvurutarihinde sahipolmak.',
                     'Başka destek kadrosunda dil belgesi tercih sebebidir. Dil şartı aranmaz.')
        self.assertFalse(r['kpss_match'])
        self.assertTrue(r['formal_required'])

    def test_separate_announcements_do_not_share_degree_and_language_rules(self):
        r=self.check('UZMAN YARDIMCILIĞI GİRİŞ SINAVI İLANI\nHukuk lisans mezunu olmak. KPSS P2. YDS en az 70 puan almış olmak.',
                     'SÖZLEŞMELİ BİLİŞİM PERSONELİ SINAV İLANI\nBilgisayar mühendisliği lisans mezunu olmak. KPSS P3. Yabancı dil puanı olmayanların puanı sıfır sayılır.')
        self.assertEqual(r['scope_count'],2)
        self.assertTrue(r['kpss_match'])
        self.assertEqual(r['kpss_types'],['P3'])
        self.assertEqual(r['scope_results'][0]['kpss_match'],False)
        self.assertEqual(r['scope_results'][1]['kpss_match'],True)

    def test_only_positions_without_known_language_barrier_remain(self):
        r=self.check('SÖZLEŞMELİ BİLİŞİM PERSONELİ ALIM İLANI\nBilgisayar mühendisliği lisans mezunu olmak. KPSS P3. Yabancı dil puanı olmayanların puanı sıfır sayılır.\n'
                     '1. Kıdemli Sistem Uzmanı (1 Kişi - Tam Zamanlı)\nİngilizce bilmek.\n'
                     '2. Yazılım Uzmanı (1 Kişi - Tam Zamanlı)\nEn az üç yıl deneyim sahibi olmak.')
        self.assertTrue(r['kpss_match'])
        self.assertEqual(r['scope_count'],2)
        self.assertFalse(r['scope_results'][0]['kpss_match'])
        self.assertTrue(r['scope_results'][1]['kpss_match'])

    def test_kpss_alternative_type_list_and_general_bachelor(self):
        self.profile['kpss_type']='P3'
        r=self.check('Memur alım ilanı. Tüm lisans programlarından mezun olmak. KPSS P1, P2, P3 puanlarından herhangi birinden en az 70 puan almak.')
        self.assertTrue(r['kpss_match'])
        self.assertEqual(r['kpss_types'],['P1','P2','P3'])
        self.assertTrue(r['general_bachelor'])

    def test_filters_dont_confuse_university_bans_or_computer_skills_with_degree(self):
        for text in ('Üniversite Rektörlüğü. İhalelere katılmaktan yasaklama kararı. Bilgisayar ve lisans belgeleri.',
                     'Memur alım ilanı. Hukuk lisans mezunu olmak. Bilgisayar kullanabilmek. KPSS P3.'):
            r=self.check(text)
            row={'assessment':r,'title':'Üniversite','applied_at':None}
            self.assertFalse(listing_matches(row,'personal'))
            self.assertFalse(listing_matches(row,'academic'))
            self.assertTrue(listing_matches(row,'all'))

    def test_formal_exam_condition_not_satisfied_by_english_knowledge_alone(self):
        self.profile['english_available']=True
        self.assertFalse(self.check('Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. KPSS P3. YDS en az 70 puan almış olmak.')['kpss_match'])

    def test_academic_corrections_and_cancellations_are_labelled_as_notices(self):
        for text,kind in [('DÜZELTME İLANI. Üniversitemizdeki öğretim elemanı ilanının özel şartları düzeltilmiştir.','correction'),
                          ('İPTAL İLANI. Üniversitemizin Profesör kadrosu iptal edilmiştir.','cancel')]:
            r=self.check(text)
            self.assertTrue(r['academic_hiring'])
            self.assertEqual(r['notice_kind'],kind)
            self.assertEqual(r['category'],'notice')
            self.assertFalse(r['kpss_match'])

    def test_compact_general_bachelor_is_distinct_from_associate_degree(self):
        r=self.check('Memur alım ilanı. Herhangibirlisansprogramındanmezunolmak. KPSS P3.')
        self.assertTrue(r['kpss_match'])
        r=self.check('Memur alım ilanı. Herhangibironlisansprogramındanmezunolmak. KPSS P93.')
        self.assertFalse(r['kpss_match'])
        for degree in ('Herhangi bir ön lisans programından mezun olmak.', 'Herhangi bir onlisans programından mezun olmak.'):
            r=self.check('Memur alım ilanı. '+degree+' KPSS P93.')
            self.assertFalse(r['general_bachelor'])
            self.assertFalse(r['kpss_match'])

    def test_specialist_assistant_exam_is_hiring_even_without_technical_words(self):
        r=self.check('UZMAN YARDIMCILIĞI GİRİŞ SINAVI İLANI. Hukuk fakültesinden mezun olmak. KPSS P48.')
        self.assertNotEqual(r['category'],'other')
        self.assertFalse(r['kpss_match'])
