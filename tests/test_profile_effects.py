import datetime as dt
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch
from watcher.candidate import analyze,default_profile
from watcher.core import Store
from watcher.desktop import Desktop


class ProfileEffects(unittest.TestCase):
    def check(self,text,**changes):
        profile=default_profile(dt.date(2026,10,19));profile.update(changes)
        return analyze([{'page':1,'text':text,'quality':'ok'}],profile)

    def test_known_experience_below_threshold_is_excluded_unknown_is_reviewed(self):
        text='Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. KPSS P3. En az 3 (üç) yıl mesleki tecrübe sahibi olmak.'
        self.assertTrue(self.check(text)['kpss_match'])
        for years in (0,2,2.9):
            self.assertFalse(self.check(text,experience_years=years)['kpss_match'])
        self.assertTrue(self.check(text,experience_years=3)['kpss_match'])
        self.assertEqual(self.check(text)['experience_minimums'],[3.0])

    def test_word_number_experience_and_preferred_experience(self):
        text='Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. KPSS P3. En az beş yıl mesleki deneyim sahibi olmak.'
        self.assertFalse(self.check(text,experience_years=4)['kpss_match'])
        self.assertTrue(self.check(text,experience_years=5)['kpss_match'])
        optional=text.replace('En az beş','Tercihen en az beş')
        self.assertTrue(self.check(optional,experience_years=0)['kpss_match'])

    def test_pay_multiplier_alternatives_do_not_exclude_three_year_role(self):
        text='Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. KPSS P3. Ücret tavanı iki katını geçmeyecekler için en az 3 yıl, diğerleri için en az 5 yıl mesleki tecrübe sahibi olmak.'
        self.assertTrue(self.check(text,experience_years=3)['kpss_match'])
        self.assertFalse(self.check(text,experience_years=2)['kpss_match'])

    def test_kpss_year_is_effective_law_year_is_not_exam_year(self):
        text='Mühendis alım ilanı. 2008 tarihli yönetmelik uyarınca Bilgisayar mühendisliği lisans mezunu olmak. 2025 veya 2026 yıllarında yapılan KPSS P3 sınavından en az 70 puan almak.'
        r=self.check(text,kpss_year=2024)
        self.assertEqual(r['kpss_years'],[2025,2026])
        self.assertFalse(r['kpss_match'])
        self.assertTrue(self.check(text,kpss_year=2026)['kpss_match'])
        self.assertTrue(self.check('Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. 2008 tarihli yönetmelik. KPSS P3.',kpss_year=2024)['kpss_match'])
        for exam in ('2026-KPSS P3','KPSS (2026) P3'):
            r=self.check('Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. '+exam,kpss_year=2024)
            self.assertEqual(r['kpss_years'],[2026])
            self.assertFalse(r['kpss_match'])

    def test_score_type_and_language_fields_each_change_known_mismatch(self):
        text='Mühendis alım ilanı. Bilgisayar mühendisliği lisans mezunu olmak. 2026 KPSS P3 en az 70 puan almak.'
        self.assertFalse(self.check(text,kpss_score=69)['kpss_match'])
        self.assertTrue(self.check(text,kpss_score=70)['kpss_match'])
        self.assertFalse(self.check(text,kpss_type='P1')['kpss_match'])
        self.assertTrue(self.check(text,kpss_type='P3')['kpss_match'])
        english=text+' İngilizce bilmek.'
        self.assertFalse(self.check(english)['kpss_match'])
        self.assertTrue(self.check(english,english_available=True)['kpss_match'])
        exam=text+' YDS en az 70 puan almış olmak.'
        self.assertFalse(self.check(exam,english_available=True)['kpss_match'])
        self.assertTrue(self.check(exam,language_certificate=True)['kpss_match'])

    def test_save_persists_profile_and_opens_unrestricted_kpss_view(self):
        class Var:
            def __init__(self,value):self.value=value
            def get(self):return self.value
            def set(self,value):self.value=value
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            app=SimpleNamespace(store=store,root=None,kpss_score=Var('75,5'),kpss_year=Var('2026'),kpss_type=Var('P3'),experience=Var('0'),language_target=Var('2027-01-19'),has_kpss=Var(True),english_available=Var(False),has_language=Var(False),profile_feedback=Var(''),reindex_requested=threading.Event(),engine=SimpleNamespace(wake=threading.Event()),list_mode=Var('all'),profile_route=Var('Genel memur / idari'),list_query=Var('old search'),tabs=Mock(),results_tab=object(),filter_changed=Mock(),status=Var(''))
            with patch('watcher.desktop.messagebox.showerror') as error:
                Desktop.save_profile(app)
            error.assert_not_called()
            profile=store.setting('candidate_profile')
            self.assertEqual(profile['kpss_score'],75.5)
            self.assertEqual(profile['experience_years'],0)
            self.assertEqual(app.list_mode.get(),'kpss')
            self.assertEqual(app.profile_route.get(),'Her iki yol')
            self.assertEqual(app.list_query.get(),'')
            app.tabs.select.assert_called_once_with(app.results_tab)
            self.assertTrue(app.pending_profile)
            self.assertTrue(app.reindex_requested.is_set())
