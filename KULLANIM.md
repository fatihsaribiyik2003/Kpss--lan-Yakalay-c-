# KPSS İlan Yakalayıcı — kullanım

Windows 10/11 üzerinde otomatik Resmî Gazete ilan takibi. Hazır uygulama PDF/OCR motorlarını içerir; Python veya ücretli API anahtarı gerekmez.

## Üç adımda kullanım

1. Masaüstündeki **KPSS İlan Yakalayıcı** kısayolunu aç. Yeni ilanları kontrol etmek için üstteki düğmeye basabilirsin; otomatik takip açıkken uygulama kendisi de kontrol eder.
2. **İlanlar** sekmesinde bir grup seç, ilanı seçip **PDF’yi aç** düğmesine bas. Çift tıklama veya Enter da PDF'yi açar. Uzun açıklamaları **Ayrıntıları büyüt** ile okuyabilirsin.
3. Kurumun sisteminde başvurunu tamamladıktan sonra **Başvurdum** düğmesine bas. Yeşil işaretlenen ilanı sonra **Başvurduklarım** altında bulabilirsin.

## Hangi düğme ne gösterir?

| Görünüm | Gösterilen belgeler |
|---|---|
| **Tümü** | Okunmayı bekleyenler dahil bütün kayıtlar |
| **KPSS → Hiçbiri (tüm KPSS)** | Kişisel profile bakmadan bütün KPSS bağlantılı ilanlar |
| **KPSS → Mühendislik / bilişim** | Mühendislik veya bilişim kadroları içeren KPSS belgeleri |
| **KPSS → Düz memur / idari** | İdari/destek kadroları içeren KPSS belgeleri |
| **KPSS → Diğer kadrolar** | Diğer KPSS kadroları |
| **KPSS → Profilime göre** | Kaydettiğin puan, yıl, dil ve deneyim bilgilerine göre kişisel ön adaylar |
| **Akademik** | Akademik alımlar ve ilgili düzeltme/iptal duyuruları |
| **Başvurduklarım** | Senin başvuru işareti koyduğun ilanlar |

“Hiçbiri” alt filtreyi kaldırır; sonuçları boşaltmaz. Genel mühendislik seçimi yalnız Bilgisayar Mühendisliğiyle sınırlı değildir. Akademik görünümde aranan mezuniyet alanını seçebilirsin. **Alanı net okunamayanlar** seçeneği de vardır. Etiketlerin dayanak sayfası ve metni ilan ayrıntılarında görünür. Aynı belge birden fazla kadro içerebilir; grupların sayıları örtüşebilir.

**Kurum veya tarih ara** kutusu seçili grubu daraltır. **Aramayı sil** grubu korur; **Tüm ilanlara dön** aramayı ve tüm filtreleri kaldırır. Ctrl+F arama kutusuna geçer. Tarihi ekranda gördüğün `19.10.2026` veya `2026-10-19` biçiminde arayabilirsin.

## Profilim

Bu sayfa yalnız **KPSS → Profilime göre** sonuçlarını etkiler. Genel KPSS ve Akademik listeler profile göre daralmaz. Bilgilerini değiştirdikten sonra **Kaydet ve profilime göre adayları göster** düğmesine bas; uygulama o görünümü açıp yeniden değerlendirme sonucunu gösterir.

Başlangıç profili Bilgisayar Mühendisliği lisans mezunudur. Puan, puan türü, sınav yılı ve deneyimi istersen doldur. Boş alan bilinmiyor demektir; deneyim yoksa **0** gir. “İngilizce bilgim var” ile “Dil belgem / sınav sonucum var” farklı koşullardır. Dil hedef tarihi geldiğinde bu kutular kendiliğinden değişmez. Kaydettiğin mevcut bilgiler güncellemelerde korunur.

## Başvurduklarım

Başvurunu kurumun resmî sisteminde tamamla, ardından uygulamada ilanı seçip **Başvurdum** de. Başvuru sütunu ve yeşil satır işaretiyle bulabilirsin. Yanlış işaretlediysen **Başvuru işaretini kaldır** düğmesine bas; ilan korunur. Profil veya tarama aralığı değişince başvuruların silinmez.

Bu işaret senin kaydındır; kurumun başvuru onayı veya kazanma sonucu değildir. Aynı PDF'de birkaç kadro varsa işaret bütün PDF'ye aittir.

## Tarama

**Tarama** sekmesinden bugün dahil son **1–7 günü** seçip **Seçilen aralığı kaydet ve tara** düğmesine bas. Daha eski günler yönetici yetkisi gerektirir. Aralık uygulama açık kaldıkça geriye doğru büyümez; önceki ilanlar listeden silinmez.

Üstte otomatik takibin açık veya duraklatılmış olduğu yazılıdır. **Yeni ilanları kontrol et** düğmesi duraklatılmış takibi de devam ettirir. Kurulu uygulama `%LOCALAPPDATA%\Programs\KPSSIlanYakalayici` içindedir. Taşınabilir paketi taşırken EXE ile `_internal` klasörü birlikte taşınmalıdır.

## Proje yöneticisi kilidi

7 günden eski tarama yalnızca proje sahibinin özel anahtarıyla yetkilendirilir. Sizin Windows hesabınıza bu anahtarın ilk kurulum kaydı hazırlanmıştır. Parola henüz belirlenmemişse **Tarama → Yönetici girişi** düğmesine ilk basışta en az 8 karakterlik parolanızı belirleyin. Parola önceden tanımlanmışsa doğrudan parolanızla giriş yapın. Parolanın kendisi kaydedilmez; rastgele tuzlu PBKDF2-SHA256 özeti (600.000 tur) yerel kayıtta tutulur. Özel anahtar ayrıca parola ile şifrelenir. Yönetici modunda daha büyük bir gün sayısı girip kaydedebilirsiniz; tarih sınırı 2000 yılının başıdır.

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

Pencerenin **X** düğmesi uygulamayı sistem tepsisine indirir; tarama devam eder. Tepsi simgesine çift tıklayarak pencereyi açabilirsiniz. **Ayarlar ve yardım → Genel ve yardım → Uygulamayı tamamen kapat** uygulamayı sonlandırır. **Duraklat** seçimi kalıcıdır; devam etmek için **Devam et** veya **Yeni ilanları kontrol et** düğmesine basılır.

Windows oturumu açıldığında otomatik başlatma varsayılan olarak açıktır. Ayarlardan kapatılabilir. Başlangıç kaydı yalnızca mevcut Windows kullanıcısının `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\KPSSIlanYakalayici` anahtarına yazılır. Windows yönetici hesabı gerekmez; bu, uygulamanın proje yöneticisi kilidinden ayrı bir konudur. Bilgisayar kapalıyken veya kullanıcı oturumu açılmamışken çalışmaz; açıldığında yalnızca seçili aralıkta kalan eksik günleri tamamlar. İnternet kesintisinde kayıtlar korunur, sonraki kontrolde yeniden denenir.

## Sonuçları okuma

- **İlanlar:** tarih, kurum/ilan, ilan türü ve başvuru durumu. Kişisel değerlendirme sütunu yalnız KPSS → Profilime göre seçilince görünür. “Şartları incele” hata değildir; bilinmeyen veya özel koşulları PDF'den doğrula. “Ön aday” kesin uygunluk onayı değildir.
- **Ayarlar ve yardım → Okuma sorunları:** indirme/okuma hataları ve OCR kontrolü gereken dosyalar. Okunamayan belge “eşleşme yok” sayılmaz; Tümü görünümünde korunur.
- **Ayarlar ve yardım → Teknik günlük:** son tarama işlemleri.
- **Tarama takvimi:** sağdaki mavi noktalar taraması biten günleri gösterir. Oklarla ayı değiştir, Bu ay ile geri dön.
- **Ayarlar ve yardım → Genel ve yardım → Görünen ilanları CSV’ye aktar:** yalnız ekrandaki sonuçları ve başvuru işaretlerini kaydeder. Uzun sayfaları fare tekerleği veya sağdaki kaydırma çubuğuyla kaydırabilirsin.

Kelime eşleşmesi veya alan etiketi başvuru şartlarını karşıladığın anlamına gelmez. Aynı PDF'de farklı koşullara sahip kadrolar olabilir. Görüntü kalitesi düşük belgelerde OCR hataları olabilir. Aynı URL'deki dosyanın sonradan değişmesi otomatik tespit edilmez; tamamlanmış PDF'ler yeniden indirilmez.

## Kayıtlar ve kaldırma

PDF’ler, sayfa metinleri, ayarlar ve işlem günlüğü `%LOCALAPPDATA%\KPSSIlanYakalayici` klasöründe tutulur. Ayarlardaki **Veri klasörünü aç** düğmesi bu klasörü açar. Dosyalar buluta gönderilmez; resmî sunucuya yalnızca sayfa/PDF indirme istekleri yapılır.

Kaldırmak için önce Ayarlar’dan otomatik başlangıcı kapatın, **Uygulamayı tamamen kapat** düğmesine basın. Ardından uygulama klasörünü ve kısayolları silebilirsiniz. Verileri saklamak istiyorsanız veri klasörünü silmeyin.

## Geliştirme

Kaynak kod: `main.py`, `watcher/core.py`, `watcher/desktop.py`. Bağımlılıklar `requirements.txt` içinde. Kaynaktan çalıştırma: `.venv/Scripts/python.exe main.py`. Paket üretme: `build.ps1`. Otomatik testler: `.venv/Scripts/python.exe -m unittest discover -s tests -v`. Gerçek 18 Ekim 2026 ilanlarıyla uçtan uca doğrulama: `.venv/Scripts/python.exe verify_real.py`.

OCR ve PDF bağımlılıkları kendi lisanslarına tabidir. PyMuPDF AGPL / ticari çift lisanslıdır; uygulamanın kaynak kodu bu klasörde sunulmuştur. Başkalarına dağıtmadan önce kullanılan bileşenlerin lisans koşullarını değerlendirin.
