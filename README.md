# KPSS İlan Yakalayıcı

Windows üzerinde çalışan, Resmî Gazete'nin **Çeşitli İlanlar** bölümünü otomatik takip eden masaüstü uygulaması.

## Özellikler

- Normal kullanıcı, bugün dahil son **1–7 günü** seçebilir. Varsayılan 7 gündür; aralık her gün bugüne göre hesaplanır ve zamanla geriye doğru büyümez.
- Proje yöneticisi, özel anahtarı ve parolasıyla 7 gün sınırını kaldırabilir. Seçilen geniş aralık bu kuruluma ve cihaza bağlı bir dijital imzayla yetkilendirilir.
- Bilgisayar Mühendisliği lisans mezunu, KPSS puanı olan ve başlangıçta İngilizce/dil belgesi olmayan aday profiline göre ön filtre uygular. Mühendislik/bilişim ve genel lisans memur/idari kadro yollarını birlikte değerlendirir.
- Kelimeler ek işaret olarak saklanır; genel memur ilanı yalnızca bilişim sözcüğü geçmiyor diye elenmez.
- PDF metnini okur; görüntü içeren sayfalarda bilgisayar üzerinde OCR çalıştırır. Ücretli API anahtarı gerekmez.
- İşlenmiş PDF'leri tekrar indirmez. Aynı içerik farklı bir bağlantıyla yayımlanırsa kayıtlı sayfa metinlerini kullanır.
- Yarım kalan işlemleri kaldığı yerden sürdürür; indirme ve okuma hatalarını otomatik yeniden dener.
- Sonuçlarda kurum, tarih, kelimeler, sayfalar ve ilgili metin parçası gösterilir. CSV dışa aktarımı vardır.
- Sağ alt köşedeki takvimde, PDF taraması biten günler küçük mavi noktalarla işaretlenir.
- Sistem tepsisinde çalışır, yeni eşleşmelerde bildirim gösterir. Windows oturumu açıldığında otomatik başlayabilir.

Bilgisayar kapalıyken çalışmaz; açılınca yalnızca seçili aralıktaki eksik günleri tamamlar. Aralık dışındaki eski bekleyen dosyalar işlenmez; önceden okunmuş ilanlar korunur. Kontrol aralığı varsayılan olarak 30 dakikadır.

## 1.5 revizyonu: profilin sonuçlara etkisi

**Aday profilim** sayfasındaki **Kaydet ve KPSS sonuçlarını göster** düğmesi bilgileri kaydeder, eski arama/kadro yolu kısıtlarını temizler ve KPSS görünümünü açar. Yeniden değerlendirme ilerlemesi ve önceki/sonraki PDF sayısı gösterilir. Bütün ilanlar, akademik duyurular ve başvuru kayıtları korunur.

KPSS puanı/türü yanında, açıkça tespit edilen sınav yılı ve asgari deneyim uyumsuzlukları da KPSS ön listesini daraltır. Deneyim için **0 = deneyim yok**, **boş = bilinmiyor** anlamındadır. Ücret tavanına göre farklı deneyim koşulları ve açık kadro başlıkları ayrı ele alınır. Sayısal puan yalnızca tespit edilen taban puan varsa karşılaştırılır; her profil değişikliği PDF sayısını değiştirmek zorunda değildir. Aynı PDF'de listede kalan kadrolar veya kontrol notları değişebilir. Dil hedef tarihi sadece plandır.

## 1.4 revizyonu: başvuru takibi ve filtre denetimi

İlanı seçip **Başvurdum** düğmesine basınca işaret ve işaretleme tarihi yerel veritabanına kaydedilir. Listede **Başvuruldu** görünür; **Başvurduklarım** düğmesiyle bu ilanlar bulunur. **Başvuruyu geri al** yalnızca işareti kaldırır; PDF korunur. Profil veya tarama aralığı değişikliği başvuru kaydını silmez. CSV aktarımı başvuru durumunu/tarihini de içerir. Bu bir kullanıcı işaretidir; kuruma otomatik başvuru veya kabul onayı değildir.

Mevcut dosyaların özgün metin sırası bir kez onarılır; OCR/indirme tekrarlanmaz. Dil sınav belgesi ve İngilizce bilgisi ayrımı, çoklu alım/kadro bölümleri, ön lisans/lisans ayrımı ve akademik düzeltme/iptal tanıması düzeltildi. Akademisyen görünümü ilgili düzeltme/iptalleri ayrı etiketle gösterir. Ayrıntılı yöntem, bulgular ve sınırlar [doğrulama raporundadır](DOGRULAMA.md).

## 1.3 revizyonu: ilan listesindeki filtre çubuğu

**İlanlar / PDF’ler** sekmesinde üç düğmeli filtre çubuğu bulunur:

- **Tüm ilanlar:** her açılışta varsayılandır. Profile uymayanlar ve okunmayı bekleyenler dahil bütün keşfedilen PDF bağlantıları listelenir. İndirilmemiş PDF çift tıklanınca resmî bağlantıdan açılır.
- **KPSS • profilime göre:** KPSS ifadesi ve bilgisayar mühendisliği/genel lisans kabulü bulunan alımlar gösterilir. Bilinen puan/puan türü uyumsuzlukları ve karşılanmayan zorunlu dil koşulu elenir. Bilinmeyen puan, yıl, deneyim ve karışık kadro şartları kontrol notlarıyla gösterilebilir. Kesin atama garantisi vermez. Meslek yolu bu görünümde ayrıca seçilebilir.
- **Akademisyen alımları:** akademik alım ifadeleri aranır; kişisel lisans/dil profili bu listeyi daraltmaz. Üniversitelerin idari personel alımları tek başına akademik ilan sayılmaz. OCR/metin tanıma hataları olabilir; bütün belgeler Tüm ilanlar görünümünde korunur.

Düğmeler kayıt sayılarını gösterir. Başlık, tarih ve ek kelime işaretlerinde arama yapılabilir. **Filtreleri temizle**, aramayı ve kadro yolunu da sıfırlayıp tüm kayıtları gösterir. CSV yalnızca görünen listeyi aktarır. Filtreler tarama aralığını değiştirmez. Kişisel bilgiler **Aday profilim** sekmesinde düzenlenir.

## 1.2 revizyonu: aday profiline göre filtre

**Aday profilim** sekmesinde diploma Bilgisayar Mühendisliği lisans olarak tanımlıdır. KPSS puanı olduğu varsayılır; sayısal puan, puan türü ve sınav yılı başlangıçta bilinmiyor bırakılır. İstenirse doldurulabilir. Deneyim süresi de bilinmiyor kabul edilir; sertifika veya ehliyetin bulunduğu varsayılmaz.

İngilizce bilgisi ve dil belgesi ayrı kutulardır; ikisi de başlangıçta kapalıdır. Üç ay sonrası dil öğrenme hedefi olarak kaydedilir. Bu tarih geldiğinde İngilizce veya belge otomatik kazanılmış sayılmaz; kullanıcı gerçekten edindiğinde günceller. İngilizce öğrenmek tek başına YDS/TOEFL gibi bir belge/puan şartını karşıladığı anlamına gelmez.

Sonuçlarda **Ön eşleşme**, **Kontrol gerekli**, **Dil koşulu var**, **Profil dışında** ve **Alım ilanı değil** ayrımı vardır. KPSS görünümü mezuniyet/KPSS dayanağı olan ön eşleşmeleri ve kontrol gerekenleri gösterir; varsayılan Tüm ilanlar görünümü kayıtları gizlemez. Meslek yolu **Mühendis / bilişim**, **Genel memur / idari** veya **Her iki yol** olarak seçilebilir; kurum türüne göre eleme yapılmaz.

Mezuniyet ifadeleri ve bağlam içindeki nitelik kodları değerlendirilir. Genel lisans 4001 ve Bilgisayar Mühendisliğini kapsayan 4531 kodları için [ÖSYM 2026/1 nitelik tablosu](https://dokuman.osym.gov.tr/pdfdokuman/2026/KPSS/TERCIH1/lisans-nitelik_t1d03072026.pdf) referans alınmıştır. Kodun geçtiği belge veya listedeki başka bir kadro, bütün pozisyonların aynı koşula sahip olduğu anlamına gelmez.

Filtre kural tabanlı ve ihtiyatlıdır; özellikle düz metne dönüşmüş tabloların her kadrosunu kesin ayırdığını iddia etmez. Bir PDF'de farklı kadrolar veya çelişkili koşullar varsa belge bütünü elenmek yerine kontrol listesinde tutulabilir. Yabancı dil puanı olmayanların sıfır puanla değerlendirileceği ifadeler zorunlu belge şartıyla aynı sayılmaz. Bilinmeyen KPSS koşulları, deneyim, ek belge ve OCR belirsizliği açıklama olarak gösterilir. Başvuru tarihleri ve bütün özel şartlar ayrıca doğrulanmalıdır.

Seçilen kaydın altında neden listelendiği, dayanak metin ve sayfa numarası bulunur. Görünüm filtreleri anında uygulanır. Profil kaydedildiğinde saklanan sayfa metinleri yeniden değerlendirilir; PDF indirme/OCR tekrarlanmaz. Bildirimler yalnızca seçili tarama aralığındaki ön eşleşme/kontrol kayıtları içindir. CSV dışa aktarımı ekranda gösterilen kayıtları ve kontrol notlarını içerir. Puan ve profil ayarları yalnızca yerel veritabanına kaydedilir.

## 1.1 revizyonu: kullanıcı sınırı ve proje yöneticisi

**Tarama aralığı** sekmesinde gün sayısını seçip **Seçilen aralığı kaydet ve tara** düğmesine basın. Normal kullanıcı 1–7 gün seçebilir. Eski sürümdeki sabit başlangıç tarihi yeni sürümde tarama sınırı olarak kullanılmaz; güncelleme otomatik olarak 7 günlük aralıkla başlar.

**Yönetici girişi**, yalnızca proje sahibinin özel anahtarının bulunduğu Windows hesabında kullanılabilir. İlk girişte en az 8 karakterlik bir parola belirlenir. Parolanın kendisi kaydedilmez; rastgele tuzlu PBKDF2-SHA256 özeti (600.000 tur) yerel yönetici kaydında tutulur. Özel anahtar ayrıca bu parolayla şifrelenmiş PKCS8 biçiminde saklanır; parola, parola özeti ve özel anahtar uygulama paketine ve GitHub'a dahil edilmez. Diğer kurulumlar yeni yönetici oluşturamaz.

Yönetici daha geniş bir gün sayısı seçip kaydedebilir. İmzalanan aralık uygulama yeniden açıldığında otomatik takip için geçerli kalır; geniş aralığı değiştirmek için tekrar yönetici girişi gerekir. **Yönetici modunu kapat ve kilitle** düğmesi geniş yetkiyi kaldırıp 1–7 gün sınırını yeniden etkinleştirir.

Yönetici anahtar kasası `%LOCALAPPDATA%\KPSSIlanYakalayiciAdmin` klasöründedir. İlk kurulum kaydı Windows DPAPI ile mevcut kullanıcıya bağlıdır; ilk parola belirlendikten sonra silinir. Şifreli `owner-private.pem` ve `owner.json` dosyalarını yalnızca proje sahibi güvenli bir yerde yedeklemelidir. Parola kaybolduğunda uygulamada herkesin kullanabileceği bir sıfırlama veya arka kapı bulunmaz.

Bu, değiştirilmemiş uygulamada yerel yetkilendirmedir; kaynak kodunu değiştiren veya bilgisayarı bütünüyle kontrol eden birinin kendi sürümünü yapmasını engellemez. Açık kaynak bir masaüstü uygulamasında merkezi bir servis olmadan mutlak bir dağıtım/lisans kilidi iddiası yoktur. İmza ve şifreli anahtar işlemleri için [cryptography Ed25519](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/) ve [anahtar serileştirme](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/serialization/) kullanılır.

## Hazır Windows uygulaması

Hazır paket yayımlandığında [Releases](https://github.com/fatihsaribiyik2003/Kpss--lan-Yakalay-c-/releases) bölümünden indirilebilir. Paketteki tüm dosyaları birlikte çıkarın; EXE dosyasının yanındaki `_internal` klasörü gereklidir.

Hazır paket bilgisayarınızda varsa `BASLAT.bat` uygulamayı açar. `KUR.ps1`, paketi mevcut kullanıcının uygulama klasörüne kurar ve masaüstü kısayolu oluşturur. Yönetici hesabı gerekmez.

## Kaynak koddan çalıştırma

Windows ve **Python 3.10 veya üzeri** gerekir. PowerShell'de proje klasöründe:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Başka bir Python sürümü kullanıyorsanız ilk komuttaki `-3.10` seçimini kurulu sürümünüzle değiştirin.

### Windows paketi üretme

```powershell
.\build.ps1
```

Paket `dist/KPSS-Ilan-Yakalayici/` klasörüne oluşturulur. Python çalışma ortamı, PDF motoru ve OCR modelleri pakete dahil edilir. Ardından `KUR.ps1` çalıştırılarak kurulabilir.

### Testler

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Testler; Türkçe kelime eşleşmesini, tamamlanan dosyaların tekrar işlenmemesini, yarım kalan işlemlerin sürmesini, hata durumlarını ve takvimdeki tamamlanan gün işaretlerini kapsar.

## Veriler ve kapsam

Veriler `%LOCALAPPDATA%\KPSSIlanYakalayici` klasöründe saklanır. İndirilen PDF'ler, kullanıcı ayarları ve tarama veritabanı bu depoya dahil edilmez. OCR bilgisayarda yapılır; belgeler bir yapay zekâ servisine yüklenmez.

Kapsam günlük `YYYYMMDD-4.htm` ilan dizinidir. Diğer Resmî Gazete bölümleri taranmaz. OCR hataları olabilir; düşük kesinlikli dosyalar ayrıca işaretlenir. Kelime eşleşmesi başvuru şartlarının karşılandığı anlamına gelmez. Aynı URL altında sonradan değişen PDF'ler yeniden indirilmediği için içerik değişiklikleri otomatik tespit edilmez.

Ayrıntılar için [kullanım kılavuzunu](KULLANIM.md) okuyun.

## Kaynak yapısı

| Dosya | İşlev |
|---|---|
| `main.py` | Başlatma, tek uygulama örneği ve komut satırı seçenekleri |
| `watcher/core.py` | İlan keşfi, PDF/OCR, SQLite kayıtları ve otomatik takip |
| `watcher/desktop.py` | Masaüstü arayüzü, sistem tepsisi ve başlangıç ayarı |
| `watcher/calendar_widget.py` | Taranan günleri gösteren takvim |
| `watcher/candidate.py` | Meslek, genel lisans, KPSS ve dil koşulları için açıklanabilir aday ön filtresi |
| `watcher/access.py` | Yönetici anahtar kasası ve imzalı tarama yetkileri |
| `watcher/admin_public_key.py` | Dağıtılabilen açık doğrulama anahtarı |
| `tools/provision_admin.py` | Yalnızca proje sahibinin ilk anahtar hazırlığı; uygulama paketine dahil edilmez |
| `tests/test_engine.py` | Otomatik testler |

Bağımlılıklar kendi lisanslarına tabidir. Özellikle PyMuPDF, AGPL / ticari çift lisanslıdır. Bu projeye ayrıca bir yazılım lisansı eklenmemiştir.
