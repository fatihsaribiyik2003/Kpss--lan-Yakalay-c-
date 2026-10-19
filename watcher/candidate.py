"""Açıklanabilir aday ön filtresi; başvuru uygunluğu kararı vermez."""
import calendar
import datetime as dt
import hashlib
import json
import re
import unicodedata
from .catalog import build_catalog,ACADEMIC_ALL,ACADEMIC_ENGINEERING,ACADEMIC_UNKNOWN

ANALYSIS_VERSION = 9
CATEGORY_LABELS = {'notice':'Düzeltme / iptal duyurusu','pre_match':'Ön eşleşme', 'review':'Kontrol gerekli',
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


def _analyze(pages, profile):
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
    knowledge_required=False
    formal_required=False
    kpss_scores=[]
    kpss_types=set()
    kpss_years=set()
    experience=False
    experience_minimums=[]
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
        c=re.search(r'bilgisayar\s*m[ui]hendis\w*[^.;]{0,650}(?:mezun|lisans)',text)
        c=c or re.search(r'(?:mezun|lisans)[^.;]{0,170}bilgisayar\s*m[ui]hendis\w*',text)
        if not c and re.search(r'bolumler|ogrenim|mezuniyet|dort yillik|lisans',text):
            c=re.search(r'bilgisayar\s*m[ui]hendis\w*',text)
        if c or (qualification and re.search(r'\b4531\b',text)):
            computer=True
            m=c or re.search(r'\b4531\b',text)
            record(number,'Mezuniyet',clean[max(0,m.start()-50):m.end()+130])
        b=re.search(r'(?:herhangi\s*bir|tum|butun)\s*(?:lisans|fakulte|yuksekogretim)[^.;]{0,130}mezun',text)
        b=b or re.search(r'herhangi\s+bir\s+(?:(?:universite|fakulte|yuksekogretim)\w*\s+){1,4}lisans\s+program[^.;]{0,65}mezun',text)
        if b and re.search(r'\bon\s*lisans',b.group()):
            b=None
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
                # Dil belgesinin sıfır puan sayılması, İngilizce bilme şartını kaldırmaz.
                knowledge=bool(re.search(r'ingilizce\s*(?:bilmek|bilgisine\s*sahip\s*olmak)',value))
                formal_windows=[re.split('kpss',compact[m.start():m.end()+440],maxsplit=1)[0] for m in re.finditer(r'yds|yokdil|toefl|yabancidil',compact)]
                formal=any(re.search(r'(?:enaz\(?[abc0-9]|asgari\(?[abc0-9]|(?:belgeye|puana)[^.;]{0,90}sahipol|puanalmi[sş]olmak)',w) for w in formal_windows)
                preferred=bool(re.search(r'tercihen[^.;]{0,140}(?:ingilizce|yds|yabanci\s*dil)|(?:dil|ingilizce)[^.;]{0,80}tercih sebebi',value))
                knowledge_required |= knowledge and not preferred
                formal_required |= formal and not optional and not preferred
                required |= knowledge or formal
                optional |= preferred
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
                for listing in re.finditer(r'\bkpss\s*[-/]?\s*(p\s*\d+(?:\s*[,/]|\s+veya|\s+ve)?(?:\s*p\s*\d+\s*[,/]*\s*)*)',value):
                    kpss_types.update('P'+m for m in re.findall(r'p\s*(\d+)',listing.group(1)))
                # Kanun/ilan tarihleri sınav yılı değildir; yalnız açık KPSS bağlamı.
                for year_group in re.finditer(r'(?<!\d)(20\d{2}(?:\s*(?:veya|ve|[-/])\s*20\d{2})?)\s*[-/]?\s*(?:yil\w*|tarih\w*)?\s*(?:ait\s*)?(?:yapilan\s*)?(?:kamu\s*personeli\s*secme\s*sinav\w*|kpss)',value):
                    kpss_years.update(int(y) for y in re.findall(r'20\d{2}',year_group.group(1)))
                kpss_years.update(int(y) for y in re.findall(r'\bkpss\s*[-/]?\s*[\[(]?\s*(20\d{2})(?!\d)',value))
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
                words={'bir':1,'iki':2,'uc':3,'dort':4,'bes':5,'alti':6,'yedi':7,'sekiz':8,'dokuz':9,'on':10}
                clause_minimums=[]
                for requirement in re.finditer(r'(?:en\s*az|asgari)\s*(\d{1,2}(?:[.,]\d+)?|bir|iki|uc|dort|bes|alti|yedi|sekiz|dokuz|on)\s*(?:\([^)]{1,18}\)\s*)?yil',value):
                    context=value[requirement.end():requirement.end()+180]
                    before=value[max(0,requirement.start()-65):requirement.start()]
                    if 'tercihen' in before or not re.search(r'tecrube|deneyim|calis|hizmet',context):
                        continue
                    raw=requirement.group(1)
                    clause_minimums.append(float(words[raw]) if raw in words else float(raw.replace(',','.')))
                # Ücret tavanına göre 3/5 yıl alternatifleri genel bölümde birlikte yazılabilir.
                # Ortak alt sınır alınır; açık kadro bölümündeki daha yüksek şart ayrıca uygulanır.
                if clause_minimums:
                    experience_minimums.extend([min(clause_minimums)] if 'kat' in value and re.search(r'digerleri|gecmeyecek',value) else clause_minimums)
            if re.search(r'sertifika|surucu belgesi|ehliyet',value) and not re.search(r'(?:sertifika|surucu belgesi|ehliyet)[^.;]{0,30}aranma[zm]',value):
                certificate=True
                record(number,'Ek belge',re.sub(r'\s+',' ',clause))
    text=' '.join(normalized)
    head=text[:3000]
    academic=bool(re.search(r'ogretim\s+(?:uyesi|elemani)\s+(?:alim|alinacak)|akademik\s+personel\s+alim|(?:ogretim\s+(?:uyesi|elemani|gorevlisi)|arastirma\s+gorevlisi)[^.;]{0,120}(?:alinacaktir|alim\s+ilani|alinacak)|(?:profesor|docent|doktor ogretim uyesi)\s+alim',head))
    # Tablolu PDF'nin bozuk sıralanmış yerel metni başlığı geriye itebilir.
    # OCR kopyası ve ek sayfalardaki açık alım/düzeltme ifadeleri de taranır.
    compact_text=re.sub(r'\s+','',text)
    academic |= bool(re.search(r'(?:ogretim(?:uyesi|uyeleri|elemani|elemanlari|gorevlisi|gorevlileri)|arastirmagorevlisi|akademikpersonel)[^.;]{0,140}(?:alim|alinac|atanacak|basvuru|duzeltme|iptal)',compact_text))
    if re.search(r'(?:iptal|duzeltme)\s*ilani',head[:800]) and re.search(r'ogretim\s*(?:uyesi|elemani|gorevlisi)|profesor|docent',text):
        academic=True
    hiring=bool(re.search(r'personel\w*\s+(?:alim|alinacak)|memur\w*\s+(?:alim|alinacak)|is[cç]i\w*\s+alim|bilisim personeli giris sinavi|ogretim\s+(?:uyesi|elemani)[^.;]{0,45}alinacaktir|kadro[^.;]{0,65}personel[^.;]{0,45}alinacaktir',head))
    hiring |= bool(re.search(r'(?:muhendis|programci|uzman(?: yardimcisi)?|buro personeli|bilgisayar isletmeni)\w*\s+(?:alim|alinacak)',head))
    hiring |= bool(re.search(r'(?:uzman|mufettis|denetci|avukat)[^.;]{0,90}(?:girissinaviilani|sinavilani|alimilani)',re.sub(r'\s+','',head)))
    hiring |= academic or ('kpss' in text and 'mezun' in text and (technical or general))
    hiring |= bool('kpss' in text and re.search(r'sozlesmeli\s*personel|subay\s*temin',head))
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
        if language_required or knowledge_required or formal_required:
            if knowledge_required and not profile.get('english_available'):
                reasons.append('İngilizce bilme şartı bulundu. Dil belgesine sıfır puan verilmesi bu şartı kaldırmaz.')
                category='language'
            elif formal_required and not profile.get('language_certificate'):
                reasons.append('Zorunlu dil sınavı/belge şartı bulundu; profilinizde dil belgesi yok.')
                if route=='mixed':
                    reasons.append('Kadro şartları ayrıştırılamadı; PDF bütünü elenmedi ancak KPSS ön eşleşmesi kabul edilmedi.')
                    category='review'
                else:
                    category='language'
            elif profile.get('language_certificate') or (not language_document_required and profile.get('english_available')):
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
                    reasons.append(f'İlanda açıkça belirtilen KPSS yılları: {", ".join(str(y) for y in sorted(kpss_years))}; profil yılı {profile["kpss_year"]} ile uyuşmuyor.')
                    if category!='language': category='review'
        if experience:
            reasons.append('Deneyim/tecrübe koşulu var; süresi ve kadro kapsamı kontrol edilmeli.' + (' Deneyim süreniz belirtilmedi.' if profile.get('experience_years') is None else f' Profiliniz: {profile["experience_years"]} yıl.'))
            if category!='language': category='review'
            if experience_minimums:
                minimum=max(experience_minimums)
                reasons.append(f'Bu bölümde tespit edilen en yüksek asgari deneyim koşulu: {minimum:g} yıl.')
                if profile.get('experience_years') is not None and profile['experience_years']<minimum:
                    reasons.append('Profildeki deneyim süresi bu bölümün asgari koşulundan düşük; KPSS ön listesinden çıkarıldı.')
        if certificate:
            reasons.append('Sertifika/ehliyet gibi ek belge ifadesi var; sizde bulunduğu varsayılmadı.')
            if category!='language': category='review'
        if low_quality:
            reasons.append('En az bir sayfada OCR kontrolü gerekiyor; otomatik değerlendirme eksik olabilir.')
            if category!='language': category='review'
    # KPSS görünümü yalnızca olumlu mezuniyet dayanağı ve KPSS içeren alımları kapsar.
    # Bilinen uyumsuzluklar elenir; bilinmeyen puan/yıl/belge için notlar korunur.
    kpss_match=bool(hiring and 'kpss' in text and profile.get('has_kpss')
                    and (computer or broad) and category in ('pre_match','review')
                    and not (academic and not (general or broad)))
    if kpss_scores and profile.get('kpss_score') is not None and profile['kpss_score']<min(kpss_scores):
        kpss_match=False
    if kpss_types and profile.get('kpss_type') and profile['kpss_type'] not in kpss_types:
        kpss_match=False
    if kpss_years and profile.get('kpss_year') and profile['kpss_year'] not in kpss_years:
        kpss_match=False
    if experience_minimums and profile.get('experience_years') is not None and profile['experience_years']<max(experience_minimums):
        kpss_match=False
    if formal_required and not profile.get('language_certificate'):
        kpss_match=False
    if knowledge_required and not profile.get('english_available'):
        kpss_match=False
    notice_kind='cancel' if 'iptal ilani' in head[:800] else ('correction' if 'duzeltme ilani' in head[:800] else 'announcement')
    if notice_kind!='announcement':
        kpss_match=False
        category='notice'
        reasons.insert(0,'Bu kayıt bir iptal/düzeltme duyurusudur; yeni ve açık bir alım olarak yorumlanmadı.')
    return {'category':category,'route':route,'reasons':reasons,'evidence':evidence,
            'academic_hiring':academic,'kpss_match':kpss_match,'notice_kind':notice_kind,
            'pages':sorted({e['page'] for e in evidence}),
            'language_required':bool(language_required),'language_optional':bool(language_optional),
            'language_document_required':language_document_required,
            'knowledge_required':knowledge_required,'formal_required':formal_required,
            'kpss_types':sorted(kpss_types),'kpss_minimums':sorted(set(kpss_scores)),
            'kpss_years':sorted(kpss_years),'experience_minimums':sorted(set(experience_minimums)),
            'computer_degree':computer,'general_bachelor':broad,
            'note':'Otomatik ön filtre; kesin başvuru uygunluğu kararı değildir.'}


def analyze(pages, profile):
    """Ayrı alım metinleri ve açık bilişim kadro başlıklarını ayrı değerlendirir."""
    pages=list(pages)
    groups=[]
    current=[]
    last_kind=None
    for page in pages:
        head=re.sub(r'\s+','',norm(page['text'][:850]))
        kind='it' if re.search(r'sozlesmelibilisimpersoneli(?:alim|girissinavi|sinavilani)',head) else ('assistant' if 'uzmanyardimciligigirissinaviilani' in head else None)
        if current and kind and last_kind and kind!=last_kind:
            groups.append(current); current=[]
        current.append(page)
        if kind: last_kind=kind
    if current: groups.append(current)
    blocks=[]
    titles=[]
    for group in groups:
        joined='\n'.join(p['text'] for p in group)
        normalized=norm(joined)
        roles=list(re.finditer(r'(?m)^\s*\d{1,2}\s*[.)]\s*[^\n(]{0,130}(?:uzmani|mimari)\s*\(',normalized))
        if len(roles)<2 or not re.search(r'bilisim\s*personel',normalized):
            blocks.append(group)
            titles.append(re.sub(r'\s+',' ',' '.join(group[0]['text'].splitlines()[:3]))[:160])
            continue
        offsets=[]; cursor=0
        for page in group:
            offsets.append((cursor,cursor+len(page['text']),page)); cursor+=len(page['text'])+1
        def fragments(start,end):
            return [dict(page=p['page'],quality=p['quality'],text=p['text'][max(0,start-a):min(b,end)-a])
                    for a,b,p in offsets if a<end and b>start]
        common=fragments(0,roles[0].start())
        for i,role in enumerate(roles):
            end=roles[i+1].start() if i+1<len(roles) else len(joined)
            blocks.append(common+fragments(role.start(),end))
            titles.append(re.sub(r'\s+',' ',joined[role.start():role.end()]).strip().rstrip('(').strip())
    outcomes=[_analyze(block,profile) for block in blocks] or [_analyze([],profile)]
    if len(outcomes)==1:
        result=outcomes[0]
        result['catalog']=build_catalog(pages,result,norm)
        return result
    eligible=[r for r in outcomes if r['kpss_match']]
    result=dict(eligible[0] if eligible else outcomes[0])
    result['academic_hiring']=any(r['academic_hiring'] for r in outcomes)
    result['kpss_match']=bool(eligible)
    result['scope_count']=len(outcomes)
    result['scope_results']=[{'title':title,'pages':r['pages'],'category':r['category'],'kpss_match':r['kpss_match'],'reasons':r['reasons']} for title,r in zip(titles,outcomes)]
    result['reasons']=[f'PDF {len(outcomes)} ayrı alım/kadro bölümü olarak değerlendirildi; {len(eligible)} bölüm KPSS ön filtresinde kaldı.']+result['reasons']
    if eligible:
        result['reasons'].insert(1,'KPSS ön filtresinde kalan bölümler: '+'; '.join(title for title,r in zip(titles,outcomes) if r['kpss_match']))
    result['evidence']=[e for r in (eligible or outcomes) for e in r['evidence']][:36]
    result['pages']=sorted({e['page'] for e in result['evidence']})
    result['catalog']=build_catalog(pages,result,norm)
    return result


def listing_matches(item, mode='all', route='Hiçbiri (tüm KPSS)', query=''):
    """Liste görünümü; filtresiz modda okunmamış kayıtlar da görünür."""
    review=item.get('assessment') or {}
    catalog=item.get('catalog') or review.get('catalog') or {}
    if mode=='applied' and not item.get('applied_at'):
        return False
    if mode=='kpss' and route=='Profilime göre':
        mode='personal'
    if mode=='personal':
        if not review.get('kpss_match'):
            return False
        if route=='Mühendis / bilişim' and review.get('route') not in ('technical','mixed'):
            return False
        if route=='Genel memur / idari' and review.get('route') not in ('general','mixed'):
            return False
    elif mode=='kpss':
        if not catalog.get('kpss_related'):
            return False
        needed={'Mühendislik / bilişim':'engineering','Düz memur / idari':'admin','Diğer kadrolar':'other'}.get(route)
        if needed and needed not in catalog.get('jobs',[]): return False
    elif mode=='academic':
        if not catalog.get('academic',review.get('academic_hiring')): return False
        fields=catalog.get('academic_fields',[])
        if route==ACADEMIC_ENGINEERING and not catalog.get('academic_engineering'): return False
        if route==ACADEMIC_UNKNOWN and fields: return False
        if route not in (ACADEMIC_ALL,ACADEMIC_ENGINEERING,ACADEMIC_UNKNOWN,'Her iki yol','Hiçbiri (tüm KPSS)') and route not in fields: return False
    needle=norm(query.strip())
    return not needle or needle in norm(' '.join(str(item.get(key) or '') for key in ('title','day','terms')))
