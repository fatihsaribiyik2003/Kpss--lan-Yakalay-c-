"""Profil bağımsız ilan türleri ve kaynak metne dayalı akademik alan etiketleri."""
import re

KPSS_OPTIONS=('Hiçbiri (tüm KPSS)','Mühendislik / bilişim','Düz memur / idari','Diğer kadrolar','Profilime göre')
ACADEMIC_ALL='Hiçbiri (tüm akademik)'
ACADEMIC_ENGINEERING='Mühendislik (tümü)'
ACADEMIC_UNKNOWN='Alanı net okunamayanlar'

FIELDS={
    'Bilgisayar Mühendisliği':r'bilgisayar\s*m[ui]hendis\w*',
    'Yazılım Mühendisliği':r'yazilim\s*m[ui]hendis\w*',
    'Elektrik / Elektronik Mühendisliği':r'(?:elektrik(?:\s*[-/]?\s*(?:ve\s*)?elektronik)?|elektronik(?:\s*ve\s*haberlesme)?)\s*m[ui]hendis\w*',
    'Endüstri Mühendisliği':r'endustri\s*m[ui]hendis\w*',
    'Makine Mühendisliği':r'makine\s*m[ui]hendis\w*',
    'İnşaat Mühendisliği':r'insaat\s*m[ui]hendis\w*',
    'Çevre Mühendisliği':r'cevre\s*m[ui]hendis\w*',
    'Gıda Mühendisliği':r'gida\s*m[ui]hendis\w*',
    'Kimya Mühendisliği':r'kimya\s*m[ui]hendis\w*',
    'Malzeme / Metalurji Mühendisliği':r'(?:metalurji(?:\s*ve\s*malzeme)?|malzeme)\s*m[ui]hendis\w*',
    'Harita / Geomatik Mühendisliği':r'(?:harita|geomatik)\s*m[ui]hendis\w*',
    'Biyomedikal Mühendisliği':r'biyomedikal\s*m[ui]hendis\w*',
    'Mekatronik Mühendisliği':r'mekatronik\s*m[ui]hendis\w*',
    'Yapay Zekâ / Veri Mühendisliği':r'yapay\s*zeka(?:\s*ve\s*veri)?\s*m[ui]hendis\w*',
    'Bilişim Sistemleri Mühendisliği':r'bilisim\s*sistem\w*\s*m[ui]hendis\w*',
    'Enerji Mühendisliği':r'enerji(?:\s*sistem\w*)?\s*m[ui]hendis\w*',
    'Havacılık / Uzay Mühendisliği':r'(?:havacilik|uzay|ucak)\s*m[ui]hendis\w*',
    'Ziraat Mühendisliği':r'zir[ai]at\s*m[ui]hendis\w*',
    'Jeoloji / Jeofizik Mühendisliği':r'(?:jeoloji|jeofizik)\s*m[ui]hendis\w*',
    'Maden / Petrol Mühendisliği':r'(?:maden|petrol(?:\s*ve\s*dogalgaz)?)\s*m[ui]hendis\w*',
    'Tekstil Mühendisliği':r'tekstil\s*m[ui]hendis\w*',
    'Tıp':r'\btip\s*(?:fakulte\w*|alan\w*)|\b(?:dahiliye|kardiyoloji|radyoloji|anesteziyoloji|noroloji|cerrahi|pediatri)\b',
    'Diş Hekimliği':r'dis\s*hekim\w*',
    'Hemşirelik':r'hemsirelik\w*',
    'Eczacılık':r'eczacilik\w*',
    'Matematik':r'\bmatematik\w*',
    'Fizik':r'\bfizik\b',
    'Kimya':r'\bkimya\b(?!\s*m[ui]hendis)',
    'Biyoloji':r'\bbiyoloji\w*',
    'Hukuk':r'\bhukuk\w*',
    'İktisat / Ekonomi':r'\b(?:iktisat|ekonomi)\w*',
    'İşletme':r'\bisletme\w*',
    'Eğitim Bilimleri':r'egitim\s*bilim\w*|(?:sinif|okul\s*oncesi|ozel\s*egitim)\s*ogretmen\w*',
    'Tarih':r'\btarih\s*(?:alan\w*|bolum\w*|lisans|doktora)',
    'Türk Dili / Edebiyat':r'turk\s*dili\w*|edebiyat\w*',
    'İlahiyat':r'ilahiyat\w*',
    'Mimarlık':r'\bmimarlik\w*',
    'Psikoloji':r'\bpsikoloji\w*',
    'Sosyoloji':r'\bsosyoloji\w*',
    'İletişim':r'\biletisim\s*(?:fakulte\w*|bilim\w*|alan\w*|bolum\w*)|gazetecilik\w*',
}
ENGINEERING_FIELDS={name for name in FIELDS if 'Mühendisliği' in name}


def build_catalog(pages, assessment, normalize):
    texts=[(p['page'],re.sub(r'\s+',' ',p['text']),normalize(re.sub(r'\s+',' ',p['text']))) for p in pages]
    all_text=' '.join(t for _,_,t in texts)
    compact=re.sub(r'\s+','',all_text)
    head=compact[:5000]
    academic=assessment.get('academic_hiring',False)
    # Alım başlığı, KPSS ve atama bağlamı; salt mevzuat/ihale referansı yetmez.
    hiring=bool(re.search(r'personeli?(?:alim|alin|aln)|sozlesmelipersonel|subaytemin|memur(?:u)?(?:alim|alin)|(?:m[ui]hendis|programci|uzman|mufettis|denetci|avukat)[^.;]{0,100}(?:girissinavi|sinavilani|alim)|sozlesmelibilisimpersoneli|kadro[^.;]{0,100}(?:atan|alim)',head))
    kpss=bool(re.search(r'kps[s5]|kamupersoneli?secmesinav',compact))
    kpss_related=kpss and hiring and not academic
    engineering=bool(re.search(r'm[ui]hendis\w*|bilisimpersoneli|programci|yazilim(?:gelistirme)?uzmani',compact))
    admin=bool(re.search(r'b[ui]ropersonel|b[ui]rogorevli|korumaveg[ui]venlikgorevli|bilgisayarisletmen|verihazirlama|\bvhki\b|zabitamemur',all_text.replace(' ','')))
    # Son sayfadaki genel ücret/mevzuat cümlesi destek kadrosu açıldığı anlamına gelmez.
    admin |= 'destekpersonel' in head
    specialist=bool(re.search(r'uzmanyardimc|uzmanpersonel|mufettis|denetci|avukat|subay',head))
    admin |= bool(not engineering and not specialist and re.search(r'memur(?:u)?(?:alim|alin)|memur(?:unvani|kadrosu)',head))
    jobs=[]
    if engineering: jobs.append('engineering')
    if admin: jobs.append('admin')
    if specialist: jobs.append('other')
    if not jobs: jobs.append('other')
    fields=set();evidence=[]
    if academic:
        for number,original,text in texts:
            found=[]
            for label,pattern in FIELDS.items():
                for match in re.finditer(pattern,text):
                    found.append((match.start(),match.end(),label))
            found.sort()
            for start,end,label in found:
                after=text[end:end+300]
                before=text[max(0,start-90):start]
                # Aranan alanın kendisine bağlanan mezuniyet/uzmanlık/çalışma koşulu aranır.
                requirement=re.search(r'mezun|(?:yuksek\s*lisans|doktora|uzmanlik|docentli[kg])[^.;]{0,100}(?:yapmis|tamamla|almis|sahip)|alan(?:inda|indan)[^.;]{0,100}(?:calisma|almis|yapmis|tamamla|sahip)',after)
                reverse=re.search(r'(?:lisans|doktora|uzmanlik|docentli[kg])[^.;]{0,55}$',before)
                if reverse and re.search(r'mezun|olmak|yapmis|almis|tamamla',reverse.group()):
                    reverse=None
                if not requirement and not reverse:
                    continue
                alternatives=bool(re.match(r'\s*(?:[,/]|veya\b|ya\s*da\b|ve\b)',after))
                if requirement and not alternatives and any(a>=end and a<end+requirement.start() and other!=label for a,b,other in found):
                    continue
                # Bir başlığın ardından başka alanın koşulunu etiketleme.
                if 'bolumu' in after[:25] and re.search(r'(?:lisans|doktora)[^.;]{0,70}mezun',after) and any(a>=end and a<end+220 and other!=label for a,b,other in found):
                    continue
                fields.add(label)
                if sum(e['field']==label for e in evidence)<2:
                    evidence.append({'field':label,'page':number,'text':original[max(0,start-70):end+300]})
    return {'kpss_related':kpss_related,'jobs':jobs,'academic':academic,
            'notice_kind':assessment.get('notice_kind','announcement'),
            'academic_fields':sorted(fields),'academic_field_evidence':evidence,
            'academic_engineering':bool(fields & ENGINEERING_FIELDS)}
