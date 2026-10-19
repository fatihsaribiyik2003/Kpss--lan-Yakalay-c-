# KPSS İlan Yakalayıcı

Windows 10/11 için otomatik Resmî Gazete ilan takibi. Hazır EXE, PDF okuma motorunu ve OCR modellerini içerir; kullanıcıda Python veya bir API anahtarı gerekmez.

## Açılış

Masaüstündeki **KPSS İlan Yakalayıcı** kısayolunu veya bu klasördeki **BASLAT.bat** dosyasını çift tıklayın. Kurulu uygulama `%LOCALAPPDATA%\Programs\KPSSIlanYakalayici` klasöründedir. Hazır taşınabilir paket `dist/KPSS-Ilan-Yakalayici` klasöründedir; taşırken EXE ile birlikte `_internal` klasörü de taşınmalıdır.

İlk açılışta son **30 gün** taranır. Varsayılan kelimeler **KPSS, lisans, bilişim, bilgisayar, yazılım**. Bunlardan herhangi birinin geçmesi yeterlidir. Daha eski bir tarihten taramak için Ayarlar sekmesindeki başlangıç tarihini değiştirip kaydedin. Tarih `2026-01-01` gibi yazılır. Geçmiş taramasının süresi PDF sayısına ve bilgisayarın hızına bağlıdır; işlem otomatik devam eder.

## Otomasyon

1. Uygulama açılır açılmaz çalışmaya başlar ve varsayılan olarak 30 dakikada bir kontrol yapar.
2. Önce yeni tarihleri, ardından seçili başlangıç tarihine kadar eksik geçmiş günleri tarar.
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

Windows oturumu açıldığında otomatik başlatma varsayılan olarak açıktır. Ayarlardan kapatılabilir. Başlangıç kaydı yalnızca mevcut Windows kullanıcısının `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\KPSSIlanYakalayici` anahtarına yazılır. Yönetici hesabı gerekmez. Bilgisayar kapalıyken veya kullanıcı oturumu açılmamışken çalışmaz; açıldığında kaçırılan günleri tamamlar. İnternet kesintisinde kayıtlar korunur, sonraki kontrolde yeniden denenir.

## Sonuçları okuma

- **Eşleşen ilanlar:** kurum, tarih, bulunan kelimeler, sayfa numaraları; seçince ilgili metin görünür. PDF’yi açmak için çift tıklayın.
- **İşlem durumu:** indirme/okuma hataları, OCR kesinliği düşük dosyalar ve erişilemeyen dizinler. Okunamayan dosya “eşleşme yok” olarak değerlendirilmez.
- **Günlük:** yapılan son işlemler. Uzun tarama sırasında o anki PDF ve sayfa altta görünür.
- **Tarama takvimi:** sağ alt köşedeki takvimde, PDF taraması biten günlerin altında küçük mavi nokta görünür. Bekleyen veya hata durumundaki PDF’leri olan günler henüz işaretlenmez. Okunmuş ancak OCR kontrolü gereken PDF’ler ayrıca İşlem durumu sekmesinde gösterilir. Oklarla ay değiştirebilir, **Bu ay** düğmesiyle güncel aya dönebilirsiniz.
- **CSV dışa aktar:** eşleşen ilanları Excel ile açılabilir biçimde kaydeder.

Kelime eşleşmesi, başvuru şartlarını karşıladığınız anlamına gelmez. Türkçe harflerin aksansız OCR karşılıkları ve kelime ekleri aranır. Görüntü kalitesi düşük belgelerde OCR hataları olabilir; kaynağın başvuru şartlarını kontrol edin. Aynı URL’deki dosyanın sonradan değiştirilmesi otomatik tespit edilmez; mevcut tasarım tamamlanmış PDF’leri yeniden indirmez.

## Kayıtlar ve kaldırma

PDF’ler, sayfa metinleri, ayarlar ve işlem günlüğü `%LOCALAPPDATA%\KPSSIlanYakalayici` klasöründe tutulur. Ayarlardaki **Veri klasörünü aç** düğmesi bu klasörü açar. Dosyalar buluta gönderilmez; resmî sunucuya yalnızca sayfa/PDF indirme istekleri yapılır.

Kaldırmak için önce Ayarlar’dan otomatik başlangıcı kapatın, **Tamamen çık** düğmesine basın. Ardından uygulama klasörünü ve kısayolları silebilirsiniz. Verileri saklamak istiyorsanız veri klasörünü silmeyin.

## Geliştirme

Kaynak kod: `main.py`, `watcher/core.py`, `watcher/desktop.py`. Bağımlılıklar `requirements.txt` içinde. Kaynaktan çalıştırma: `.venv/Scripts/python.exe main.py`. Paket üretme: `build.ps1`. Otomatik testler: `.venv/Scripts/python.exe -m unittest discover -s tests -v`. Gerçek 18 Ekim 2026 ilanlarıyla uçtan uca doğrulama: `.venv/Scripts/python.exe verify_real.py`.

OCR ve PDF bağımlılıkları kendi lisanslarına tabidir. PyMuPDF AGPL / ticari çift lisanslıdır; uygulamanın kaynak kodu bu klasörde sunulmuştur. Başkalarına dağıtmadan önce kullanılan bileşenlerin lisans koşullarını değerlendirin.
