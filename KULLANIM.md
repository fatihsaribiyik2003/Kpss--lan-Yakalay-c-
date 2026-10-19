# KPSS İlan Yakalayıcı

Windows 10/11 için otomatik Resmî Gazete ilan takibi. Hazır EXE, PDF okuma motorunu ve OCR modellerini içerir; kullanıcıda Python veya bir API anahtarı gerekmez.

## Açılış

Masaüstündeki **KPSS İlan Yakalayıcı** kısayolunu veya bu klasördeki **BASLAT.bat** dosyasını çift tıklayın. Kurulu uygulama `%LOCALAPPDATA%\Programs\KPSSIlanYakalayici` klasöründedir. Hazır taşınabilir paket `dist/KPSS-Ilan-Yakalayici` klasöründedir; taşırken EXE ile birlikte `_internal` klasörü de taşınmalıdır.

İlk açılışta bugün dahil son **7 gün** taranır. **Tarama aralığı** sekmesinden **1–7 gün** seçip **Seçilen aralığı kaydet ve tara** düğmesine basabilirsiniz. Ana liste başlangıçta bütün keşfedilen ilanları gösterir; filtre çubuğundan KPSS veya akademisyen alımları seçilebilir. Aralık her gün bugüne göre hesaplanır; uygulama açık kaldıkça daha eskiye doğru büyümez. Eski sürümden güncellemede de 7 gün sınırı otomatik uygulanır.

## Sana göre ilanlar

**1.6 sürümünde:** KPSS düğmesi artık bütün KPSS ilanlarını açar. Hemen altında **Alt filtre** çubuğu görünür. **Hiçbiri (tüm KPSS)** hepsini gösterir; mühendislik/bilişim, düz memur/idari veya diğer kadroları seçebilirsin. **Profilime göre** seçeneği kişisel puan/dil/deneyim elemesini uygular. Genel KPSS listesinde kendi bölümün dışındaki veya dil şartı bulunan ilanların da görünmesi normaldir.

Akademisyen düğmesine geçince alt seçenekler akademik alanlara dönüşür. **Mühendislik (tümü)** veya Bilgisayar, Yazılım, Makine vb. tanınan alanları seçebilirsin. **Hiçbiri (tüm akademik)** tüm akademik kayıtları, **Alanı net okunamayanlar** ise alanı kesin çıkarılamayanları gösterir. İlan seçerek alan eşleşmesinin dayanak sayfasını/metnini oku; aynı PDF'deki bütün kadroların aynı koşulu taşıdığı varsayılmaz. Ana filtre değiştirilince eski alt seçim taşınmaz.

Profilini değiştirdikten sonra **Kaydet ve KPSS sonuçlarını göster** düğmesine bas. Uygulama KPSS listesine geçer; eski aramayı/meslek yolu seçimini temizler ve yeniden değerlendirme bitince önceki/sonraki PDF sayısını gösterir. Profil, Tüm ilanlar ve Akademisyen alımları görünümlerini daraltmaz. Deneyimin yoksa **0**, süresini belirtmek istemiyorsan alanı **boş** bırak. Bunlar aynı değildir. Açıkça okunan asgari deneyim ve KPSS sınav yılı uyuşmazlıkları da elenir. Her değişiklik sayıyı değiştirmek zorunda değildir; kayıtlı PDF içindeki uygun görülen kadrolar ve açıklamalar değişebilir.

Başlangıç profili: **Bilgisayar Mühendisliği lisans mezunu, KPSS puanı var, İngilizce bilgisi ve dil belgesi yok**. Kurum türüne göre eleme yapılmaz. Mühendislik/bilişim kadroları ile herhangi bir lisans mezununu kabul eden genel memur/idari kadrolar birlikte değerlendirilir.

**Aday profilim** sekmesinde KPSS puanı, puan türü, sınav yılı ve deneyim süresini istersen doldurabilirsin. Boş alanlar bilinmiyor sayılır; koşulların karşılandığı varsayılmaz. Başlangıçta üç ay sonrası dil öğrenme hedefidir. Hedef tarih geldiğinde profil otomatik değişmez. İngilizce öğrendiğinde **İngilizce bilgim var**, ayrıca geçerli bir sınav sonucu/belge edindiğinde **Dil belgem / sınav sonucum var** kutusunu işaretle. Bunlar ayrı koşullardır.

PDF listesinin üzerindeki çubuktan **Tüm ilanlar**, **KPSS • profilime göre** ve **Akademisyen alımları** seçilir. Her açılışta Tüm ilanlar seçilidir; okunmamış ve profile uymayan kayıtlar da görünür. KPSS görünümü, KPSS ve mezuniyet dayanağı bulunan ilanları seçer; bilinen puan/tür uyumsuzlukları elenir, bilinmeyen şartlar kontrol notuyla korunabilir. Meslek yolu listesi yalnızca KPSS görünümünde çalışır. Akademisyen alımları kişisel lisans/dil profiline göre elenmez; üniversitenin idari alımı ayrı değerlendirilir. Düğmelerde ilan sayıları görünür. İlan ara alanı başlık/tarih/ek kelimelerde arar. **Filtreleri temizle** bütün kayıtları geri getirir. Bu filtreler tarama aralığını değiştirmez.

Bir ilanı seçtiğinde neden listelendiği, kontrol edilmesi gereken şartlar ve dayanak sayfalar görünür. Dil puanı olmayana sıfır verilmesi gibi ifadeler otomatik ret sayılmaz. Aynı PDF'deki farklı kadroların koşulları karışabiliyorsa bütün PDF elenmez; kontrol gerektiği belirtilir. Akademik kadrolar yalnızca lisans profiliyle uygun kabul edilmez. **Ön eşleşme kesin başvuru uygunluğu değildir**; ilgili kadro satırını, başvuru tarihlerini, puan türünü/yılını ve özel şartları doğrula.

Profil değişikliğinde eski metinler yeniden değerlendirilir; indirme/OCR tekrarlanmaz. Varsayılan görünüm dışındaki kayıtlar silinmez. CSV, ekranda görünen kayıtları ve kontrol notlarını aktarır. Profil bilgileriniz ve puanınız GitHub'a gönderilmez.

## Başvurduğun ilanları saklama

1. Başvurunu kurumun resmî sisteminde tamamla.
2. Uygulamada ilgili ilanı seçip **Başvurdum** düğmesine bas.
3. İlanın Başvuru sütununda **Başvuruldu** görünür. Açıklamada işaretleme tarihi yer alır.
4. Sonradan bulmak için listenin üzerindeki **Başvurduklarım** düğmesini kullan. Burada da başlık/tarihle arama yapabilirsin.
5. Yanlış işaretlediysen ilanı seçip **Başvuruyu geri al** düğmesine bas; ilan silinmez.

Profil ve tarama aralığı değişse de bu işaretler korunur. CSV'ye başvuru durumu ve tarih de eklenir. Uygulama hangi kadroya başvurduğunu kurumdan doğrulamaz; aynı PDF'de birden fazla kadro varsa PDF'nin tamamını işaretler. Başvuru işareti kabul/kazanma sonucu değildir. Kullanıcı işaretlemeden otomatik başvuru yapılmış sayılmaz.

Filtrelerin 1.4 sürümündeki denetim sonuçları ve bilinen sınırlar [doğrulama raporundadır](DOGRULAMA.md).

## Proje yöneticisi kilidi

7 günden eski tarama yalnızca proje sahibinin özel anahtarıyla yetkilendirilir. Sizin Windows hesabınıza bu anahtarın ilk kurulum kaydı hazırlanmıştır. Parola henüz belirlenmemişse **Tarama aralığı → Yönetici girişi** düğmesine ilk basışta en az 8 karakterlik parolanızı belirleyin. Parola önceden tanımlanmışsa doğrudan parolanızla giriş yapın. Parolanın kendisi kaydedilmez; rastgele tuzlu PBKDF2-SHA256 özeti (600.000 tur) yerel kayıtta tutulur. Özel anahtar ayrıca parola ile şifrelenir. Yönetici modunda daha büyük bir gün sayısı girip kaydedebilirsiniz; tarih sınırı 2000 yılının başıdır.

Yetkilendirilen geniş aralık, yeniden başlatma sonrasında otomatik takip için korunur. Geniş aralığı değiştirmek için yeniden yönetici girişi gerekir. **Yönetici modunu kapat ve kilitle** düğmesi geniş yetkiyi kaldırıp aralığı en fazla 7 güne düşürür. Normal kullanıcı daha geniş yetkiyi kendisi oluşturamaz; uygulamada ortak bir varsayılan yönetici parolası yoktur.

Özel anahtar ve parola GitHub'a veya hazır uygulamaya dahil edilmez. Anahtar kasası `%LOCALAPPDATA%\KPSSIlanYakalayiciAdmin` klasöründedir. İlk parolayı belirledikten sonra `owner-private.pem` ve `owner.json` dosyalarını güvenli bir yerde yedekleyin. Şifreli anahtar başka bir Windows hesabına yalnızca proje sahibi tarafından taşınmalı ve parola paylaşılmamalıdır. Parolayı unutursanız herkesin kullanabileceği bir parola sıfırlama düğmesi yoktur. Kaynak kodunu değiştirebilen veya Windows hesabınızı bütünüyle kontrol eden biri kendi sürümünü yapabilir; bu yerel kilit değiştirilmemiş uygulamayı korur.

## Otomasyon

1. Uygulama açılır açılmaz çalışmaya başlar ve varsayılan olarak 30 dakikada bir kontrol yapar.
2. Önce bugünü, ardından yalnızca seçili gün aralığındaki eksik geçmiş günleri tarar. Aralık dışındaki bekleyen dosyalar saklanır ancak işlenmez. Aralığı daraltırsanız mevcut PDF sayfası tamamlandıktan sonra yeni sınır uygulanır.
3. Günlük **Çeşitli İlanlar** (`YYYYMMDD-4.htm`) sayfasından resmî PDF bağlantılarını bulur. Diğer ilan kategorileri kapsamda değildir.
4. Son üç günün dizin sayfası, geç eklenen bağlantılar için yeniden kontrol edilir. Daha eski başarılı dizinler tekrar okunmaz. Aynı PDF bağlantısı tekrar indirilmez.
5. İndirilen dosya PDF değilse veya ağ hatası oluşursa hata kaydedilir ve artan bekleme süreleriyle otomatik yeniden denenir. Eski tarihlerde bulunmayan dizinler haftalık yeniden kontrol edilir.
6. Metin içeren sayfalar doğrudan okunur. Büyük görüntüler içeren veya metni az olan sayfalarda bilgisayardaki OCR çalışır. OCR modeli uygulamayla gelir; belge başka bir servise yüklenmez.
7. PDF içerik özeti ve her sayfanın metni kaydedilir. Aynı içerik başka bir URL altında yayımlansa bile daha önceki sayfa okuması kullanılır.
8. Kapanma veya elektrik kesintisinden sonra kaydedilmiş sayfalar korunur; eksik sayfalardan devam edilir. Tamamlanan PDF tekrar OCR işleminden geçirilmez.
9. Kelimeler değiştirildiğinde kayıtlı metinler tekrar filtrelenir. PDF indirme ve OCR işlemleri tekrarlanmaz.
10. Yeni eşleşme sistem tepsisi bildirimi üretir. Sonuçlar bildirim görüntülenmese de sonuç ekranına kaydedilir.

## Arka planda çalışma

Pencerenin **X** düğmesi uygulamayı sistem tepsisine indirir; tarama devam eder. Tepsi simgesine çift tıklayarak pencereyi açabilirsiniz. **Tamamen çık** uygulamayı sonlandırır. **Duraklat** seçimi kalıcıdır; devam etmek için **Devam et** düğmesine basılır.

Windows oturumu açıldığında otomatik başlatma varsayılan olarak açıktır. Ayarlardan kapatılabilir. Başlangıç kaydı yalnızca mevcut Windows kullanıcısının `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\KPSSIlanYakalayici` anahtarına yazılır. Windows yönetici hesabı gerekmez; bu, uygulamanın proje yöneticisi kilidinden ayrı bir konudur. Bilgisayar kapalıyken veya kullanıcı oturumu açılmamışken çalışmaz; açıldığında yalnızca seçili aralıkta kalan eksik günleri tamamlar. İnternet kesintisinde kayıtlar korunur, sonraki kontrolde yeniden denenir.

## Sonuçları okuma

- **İlanlar / PDF’ler:** tarih, kurum, meslek yolu, profil ön filtresi ve sayfa numaraları; seçince gerekçe ve dayanak metin görünür. PDF’yi açmak için çift tıklayın.
- **İşlem durumu:** indirme/okuma hataları, OCR kesinliği düşük dosyalar ve erişilemeyen dizinler. Okunamayan dosya “eşleşme yok” olarak değerlendirilmez.
- **Günlük:** yapılan son işlemler. Uzun tarama sırasında o anki PDF ve sayfa altta görünür.
- **Tarama takvimi:** sağ alt köşedeki takvimde, PDF taraması biten günlerin altında küçük mavi nokta görünür. Bekleyen veya hata durumundaki PDF’leri olan günler henüz işaretlenmez. Okunmuş ancak OCR kontrolü gereken PDF’ler ayrıca İşlem durumu sekmesinde gösterilir. Oklarla ay değiştirebilir, **Bu ay** düğmesiyle güncel aya dönebilirsiniz.
- **CSV dışa aktar:** ekranda görünen ilanları Excel ile açılabilir biçimde kaydeder.

Kelime eşleşmesi, başvuru şartlarını karşıladığınız anlamına gelmez. Türkçe harflerin aksansız OCR karşılıkları ve kelime ekleri aranır. Görüntü kalitesi düşük belgelerde OCR hataları olabilir; kaynağın başvuru şartlarını kontrol edin. Aynı URL’deki dosyanın sonradan değiştirilmesi otomatik tespit edilmez; mevcut tasarım tamamlanmış PDF’leri yeniden indirmez.

## Kayıtlar ve kaldırma

PDF’ler, sayfa metinleri, ayarlar ve işlem günlüğü `%LOCALAPPDATA%\KPSSIlanYakalayici` klasöründe tutulur. Ayarlardaki **Veri klasörünü aç** düğmesi bu klasörü açar. Dosyalar buluta gönderilmez; resmî sunucuya yalnızca sayfa/PDF indirme istekleri yapılır.

Kaldırmak için önce Ayarlar’dan otomatik başlangıcı kapatın, **Tamamen çık** düğmesine basın. Ardından uygulama klasörünü ve kısayolları silebilirsiniz. Verileri saklamak istiyorsanız veri klasörünü silmeyin.

## Geliştirme

Kaynak kod: `main.py`, `watcher/core.py`, `watcher/desktop.py`. Bağımlılıklar `requirements.txt` içinde. Kaynaktan çalıştırma: `.venv/Scripts/python.exe main.py`. Paket üretme: `build.ps1`. Otomatik testler: `.venv/Scripts/python.exe -m unittest discover -s tests -v`. Gerçek 18 Ekim 2026 ilanlarıyla uçtan uca doğrulama: `.venv/Scripts/python.exe verify_real.py`.

OCR ve PDF bağımlılıkları kendi lisanslarına tabidir. PyMuPDF AGPL / ticari çift lisanslıdır; uygulamanın kaynak kodu bu klasörde sunulmuştur. Başkalarına dağıtmadan önce kullanılan bileşenlerin lisans koşullarını değerlendirin.
