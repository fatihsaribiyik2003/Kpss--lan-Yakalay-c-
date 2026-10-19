"""Açıklanabilir aday ön filtresi; başvuru uygunluğu kararı vermez."""
import calendar
import datetime as dt
import hashlib
import json
import re
import unicodedata

ANALYSIS_VERSION = 3
CATEGORY_LABELS = {'pre_match':'Ön eşleşme', 'review':'Kontrol gerekli',
                   'language':'Dil koşulu var', 'outside':'Profil dışında', 'other':'Alım ilanı değil'}
ROUTE_LABELS = {'technical':'Mühendis / bilişim', 'general':'Genel memur / idari',
                'mixed':'Bilişim + genel kadro', 'unknown':'Alanı kontrol et'}


def default_profile(date):
    month=date.month+3
    year=date.year+(month-1)//12
    month=(month-1)%12+1
    target=dt.date(year,month,min(date.day,calendar.monthrange(year,month)[1]))
    return {'degree':'computer_engineering_bachelor','has_kpss':True,
            'kpss_score':None,'kpss_type':'','kpss_year':None,
            'english_available':False,'language_certificate':False,'language_target_date':target.isoformat(),
            'experience_years':None}


def fingerprint(profile):
    return hashlib.sha256(json.dumps(profile,sort_keys=True,ensure_ascii=True).encode()).hexdigest()


def norm(text):
    text=text.replace('ı','i').replace('İ','I').casefold()
    return ''.join(c for c in unicodedata.normalize('NFKD',text) if not unicodedata.combining(c))


def analyze(pages, profile):
    evidence=[]
    normalized=[]
    low_quality=False
    def record(page,kind,text):
        item={'page':page,'kind':kind,'text':text[:440]}
        if item not in evidence and sum(e['kind']==kind for e in evidence)<4:
            evidence.append(item)
    computer=False
    broad=False
    technical=False
    general=False
    language_required=[]
    language_optional=[]
    language_mention=False
    language_document_required=False
    kpss_scores=[]
    kpss_types=set()
    kpss_years=set()
    experience=False
    certificate=False
    other_degree=False
    mixed_scope=False
    total_text=''
    for page in pages:
        original=page['text']
        clean=re.sub(r'\s+',' ',original)
        text=norm(clean)
        number=page['page']
        normalized.append(text)
        total_text+=original+'\n'
        low_quality |= page['quality']!='ok'
        # Kodlar sadece mezuniyet/nitelik bağlamında kullanılır.
        qualification=bool(re.search(r'nitelik|ogrenim|mezun|aranan sart',text))
        c=re.search(r'bilgisayar\s*muhendis\w*[^.;]{0,650}(?:mezun|lisans)',text)
        c=c or re.search(r'(?:mezun|lisans)[^.;]{0,170}bilgisayar\s*muhendis\w*',text)
        if not c and re.search(r'bolumler|ogrenim|mezuniyet|dort yillik|lisans',text):
            c=re.search(r'bilgisayar\s*muhendis\w*',text)
        if c or (qualification and re.search(r'\b4531\b',text)):
            computer=True
            m=c or re.search(r'\b4531\b',text)
            record(number,'Mezuniyet',clean[max(0,m.start()-50):m.end()+130])
        b=re.search(r'(?:herhangi|tum|butun)\s+bir?\s*(?:lisans|fakulte|yuksekogretim)[^.;]{0,130}mezun',text)
        b=b or re.search(r'herhangi\s+bir\s+[^.;]{0,45}lisans\s+program[^.;]{0,65}mezun',text)
        if b or (qualification and re.search(r'\b4001\b',text)):
            broad=True
            m=b or re.search(r'\b4001\b',text)
            record(number,'Genel lisans',clean[max(0,m.start()-50):m.end()+130])
        technical |= bool(re.search(r'bilisim personel|programci|yazilim\s+(?:uzman|gelistir|personel)|bilgisayar\s+muhendis|sistem\s+(?:uzman|yonetic)|ag\s+uzman',text))
        general |= bool(re.search(r'\bmemur\b|buro personel|idari personel|veri hazirlama|bilgisayar isletmen|\bvhki\b',text))
        other_degree |= bool(re.search(r'(?:cevre muhendisligi|insaat muhendisligi|hukuk|hemsirelik|eczacilik|makine muhendisligi|psikoloji|iktisat|isletme|maliye|kamu yonetimi|saglik yonetimi|sosyal hizmet)[^.;]{0,100}mezun',text))
        mixed_scope |= bool(re.search(r'bazi\s+(?:kadro|pozisyon)|yalnizca[^.;]{0,55}(?:kadro|pozisyon)|sadece[^.;]{0,55}(?:kadro|pozisyon)',text))
        # Nokta ve satır sınırları korunur; OCR/natif kopyaları tek belgeye körlemesine şart eklemez.
        clauses=re.split(r'(?<=[.;])\s+|\n\s*\n',original)
        for clause in clauses:
            value=re.sub(r'\s+',' ',norm(clause))
            if re.search(r'\byds\b|\byokdil\b|\btoefl\b|yabanci\s*dil|ingilizce',value):
                language_mention=True
                optional=bool(re.search(r'(?:dil|yds|yokdil|ingilizce|toefl)[^.;]{0,180}(?:puan\w* olmayan|belge[^.;]{0,60}(?:ibraz etmeyen|sunmayan)|aranma[zm]|sarti yok|zorunlu degil|tercih sebebi)|(?:ibraz etmeyen|belge sunmayan)[^.;]{0,120}(?:dil|sifir|\b0\b)',value))
                compact=re.sub(r'\s+','',value)
                optional |= bool(re.search(r'(?:yabancidil|yds|yokdil|ingilizce)[^.;]{0,200}(?:belgeibrazetmeyen|puan[i1]?olmayan|zorunludegil|sarti[na]?aranma[zm])',compact))
                language_windows=[]
                for anchor in re.finditer(r'\byds\b|\byokdil\b|\btoefl\b|yabanci\s*dil|ingilizce',value):
                    tail=re.split(r'\bkpss\b',value[anchor.start():anchor.end()+200],maxsplit=1)[0]
                    language_windows.append(tail)
                required=any(re.search(r'en az\s*\d+|asgari\s*\d+|zorunlu|sart(?:i|ini|tir)|almis olmak|bilmek|belgelemek|belgelendirmek|gerekli',window) for window in language_windows)
                if optional:
                    language_optional.append(number)
                    record(number,'Dil: zorunlu olmayabilir',re.sub(r'\s+',' ',clause))
                elif required:
                    language_required.append(number)
                    language_document_required |= any(re.search(r'\byds\b|\byokdil\b|\btoefl\b|belge|puan|sinav',window) for window in language_windows)
                    record(number,'Dil şartı',re.sub(r'\s+',' ',clause))
                else:
                    record(number,'Dil bilgisi kontrolü',re.sub(r'\s+',' ',clause))
            if 'kpss' in value:
                kpss_types.update('P'+m for m in re.findall(r'\bkpss\s*[-/]?\s*p\s*(\d+)\b',value))
                kpss_years.update(int(y) for y in re.findall(r'\b(20\d{2})\b',value))
                for anchor in re.finditer(r'\bkpss\b',value):
                    window=re.split(r'\byds\b|\byokdil\b|\btoefl\b|yabanci\s*dil|ingilizce',value[anchor.start():anchor.end()+230],maxsplit=1)[0]
                    for m in re.finditer(r'(?:en az|asgari|taban)\s*(\d{2,3}(?:[.,]\d+)?)\s*(?:\([^)]*\)\s*)?puan|taban puan\w*\s*[:=]?\s*(\d{2,3}(?:[.,]\d+)?)',window):
                        score=float((m.group(1) or m.group(2)).replace(',','.'))
                        if score<=100:
                            kpss_scores.append(score)
                record(number,'KPSS',re.sub(r'\s+',' ',clause))
            if re.search(r'tecrube|deneyim',value) and not re.search(r'(?:tecrube|deneyim)[^.;]{0,35}(?:aranma[zm]|sarti yok|gerekmem)',value):
                experience=True
                record(number,'Deneyim',re.sub(r'\s+',' ',clause))
            if re.search(r'sertifika|surucu belgesi|ehliyet',value) and not re.search(r'(?:sertifika|surucu belgesi|ehliyet)[^.;]{0,30}aranma[zm]',value):
                certificate=True
                record(number,'Ek belge',re.sub(r'\s+',' ',clause))
    text=' '.join(normalized)
    head=text[:3000]
    academic=bool(re.search(r'ogretim\s+(?:uyesi|elemani)\s+(?:alim|alinacak)|akademik\s+personel\s+alim',head))
    hiring=bool(re.search(r'personel\w*\s+(?:alim|alinacak)|memur\w*\s+(?:alim|alinacak)|is[cç]i\w*\s+alim|bilisim personeli giris sinavi|ogretim\s+(?:uyesi|elemani)[^.;]{0,45}alinacaktir|kadro[^.;]{0,65}personel[^.;]{0,45}alinacaktir',head))
    hiring |= bool(re.search(r'(?:muhendis|programci|uzman(?: yardimcisi)?|buro personeli|bilgisayar isletmeni)\w*\s+(?:alim|alinacak)',head))
    hiring |= academic or ('kpss' in text and 'mezun' in text and (technical or general))
    route='mixed' if (technical or computer) and (general or broad) else ('technical' if technical or computer else ('general' if general or broad else 'unknown'))
    reasons=[]
    category='review'
    if not hiring:
        if low_quality and len(text.strip())<150:
            reasons.append('Metin yetersiz veya OCR belirsiz; alım ilanı olup olmadığı kontrol edilmeli.')
        else:
            category='other'
            reasons.append('Personel alımı olduğunu gösteren yeterli ifade bulunmadı.')
    elif academic and not (general or broad):
        category='outside'
        reasons.append('Akademik kadro ilanı; yalnızca lisans mezuniyetiyle uyum varsayılmadı.')
    elif other_degree and not (computer or broad):
        category='outside'
        reasons.append('Bilgisayar mühendisliği/genel lisans yerine başka bölüm mezuniyeti belirtiliyor.')
    elif computer or broad:
        category='pre_match'
        reasons.append('Bilgisayar mühendisliği mezuniyetiyle ön eşleşme.' if computer else 'Herhangi bir lisans mezuniyetini kabul eden ifade/kod bulundu.')
        if computer and broad:
            reasons.append('Hem bilişim hem genel lisans kadroları olabilir; kadro satırı ayrıca kontrol edilmeli.')
    else:
        reasons.append('Kadro alanı ilgili olabilir ancak bilgisayar mühendisliği/genel lisans kabulü kesin çıkarılamadı.')
    relevant=category in ('pre_match','review')
    if relevant:
        if language_required:
            if profile.get('language_certificate') or (not language_document_required and profile.get('english_available')):
                reasons.append('Dil şartı var; belgenin türü, puanı ve geçerliliği kontrol edilmeli.' if language_document_required else 'İngilizce bilgisi şartı var; kurumun istediği seviye ve değerlendirme yöntemi kontrol edilmeli.')
                category='review'
            elif language_optional or route=='mixed' or mixed_scope:
                reasons.append('Bazı kadrolar dil şartı istiyor olabilir; PDF bütünü elenmedi. Kadro bazında kontrol edin.')
                category='review'
            else:
                reasons.append('Zorunlu dil koşulu bulundu; profilinizde şu an dil belgesi yok.' if language_document_required else 'Yabancı dil bilgisi şartı bulundu; profilinizde şu an İngilizce bilgisi yok.')
                category='language'
        elif language_optional:
            reasons.append('Dil belgesi olmayanlar için değerlendirme ifadesi var; dil geçmesi tek başına eleme nedeni değil.')
        elif language_mention:
            reasons.append('Yabancı dil ifadesi var ancak zorunluluk net değil; kontrol edilmeli.')
            category='review'
        else:
            reasons.append('Metinde zorunlu dil koşulu tespit edilmedi; bu, koşul olmadığı garantisi değildir.')
        if 'kpss' in text:
            if not profile.get('has_kpss'):
                reasons.append('KPSS koşulu bulunuyor; profilinizde KPSS puanı yok.')
                if category!='language': category='review'
            else:
                if profile.get('kpss_score') is None or not profile.get('kpss_type') or profile.get('kpss_year') is None:
                    reasons.append('KPSS puanı/türü/yılı profilinizde eksik; taban puan uygunluğu kesinleştirilmedi.')
                if kpss_scores and profile.get('kpss_score') is not None:
                    minimum=min(kpss_scores)
                    reasons.append(f'İlanda tespit edilen taban puan(lar): {", ".join(str(v) for v in sorted(set(kpss_scores)))}; profil puanı: {profile["kpss_score"]}.')
                    if profile['kpss_score']<minimum:
                        reasons.append('Profil puanı tespit edilen alt sınırın altında; kadro ve puan türünü doğrulayın.')
                        if category!='language': category='review'
                if kpss_types and profile.get('kpss_type') and profile['kpss_type'] not in kpss_types:
                    reasons.append('İlandaki KPSS puan türü ile profiliniz aynı görünmüyor; kontrol gerekli.')
                    if category!='language': category='review'
                if kpss_years and profile.get('kpss_year') and profile['kpss_year'] not in kpss_years:
                    reasons.append('KPSS yılı uyumu kontrol edilmeli; ilandaki diğer tarihleri de içerebilir.')
                    if category!='language': category='review'
        if experience:
            reasons.append('Deneyim/tecrübe koşulu var; süresi ve kadro kapsamı kontrol edilmeli.' + (' Deneyim süreniz belirtilmedi.' if profile.get('experience_years') is None else f' Profiliniz: {profile["experience_years"]} yıl.'))
            if category!='language': category='review'
        if certificate:
            reasons.append('Sertifika/ehliyet gibi ek belge ifadesi var; sizde bulunduğu varsayılmadı.')
            if category!='language': category='review'
        if low_quality:
            reasons.append('En az bir sayfada OCR kontrolü gerekiyor; otomatik değerlendirme eksik olabilir.')
            if category!='language': category='review'
    return {'category':category,'route':route,'reasons':reasons,'evidence':evidence,
            'pages':sorted({e['page'] for e in evidence}),
            'language_required':bool(language_required),'language_optional':bool(language_optional),
            'language_document_required':language_document_required,
            'kpss_types':sorted(kpss_types),'kpss_minimums':sorted(set(kpss_scores)),
            'computer_degree':computer,'general_bachelor':broad,
            'note':'Otomatik ön filtre; kesin başvuru uygunluğu kararı değildir.'}
