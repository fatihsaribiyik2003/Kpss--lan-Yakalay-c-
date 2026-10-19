# KPSS İlan Yakalayıcı

Windows üzerinde çalışan, Resmî Gazete'nin **Çeşitli İlanlar** bölümünü otomatik takip eden masaüstü uygulaması.

## Özellikler

- Normal kullanıcı, bugün dahil son **1–7 günü** seçebilir. Varsayılan 7 gündür; aralık her gün bugüne göre hesaplanır ve zamanla geriye doğru büyümez.
- Proje yöneticisi, özel anahtarı ve parolasıyla 7 gün sınırını kaldırabilir. Seçilen geniş aralık bu kuruluma ve cihaza bağlı bir dijital imzayla yetkilendirilir.
- Varsayılan olarak **KPSS, lisans, bilişim, bilgisayar, yazılım** kelimelerini arar. Kelimelerden birinin geçmesi yeterlidir.
- PDF metnini okur; görüntü içeren sayfalarda bilgisayar üzerinde OCR çalıştırır. Ücretli API anahtarı gerekmez.
- İşlenmiş PDF'leri tekrar indirmez. Aynı içerik farklı bir bağlantıyla yayımlanırsa kayıtlı sayfa metinlerini kullanır.
- Yarım kalan işlemleri kaldığı yerden sürdürür; indirme ve okuma hatalarını otomatik yeniden dener.
- Sonuçlarda kurum, tarih, kelimeler, sayfalar ve ilgili metin parçası gösterilir. CSV dışa aktarımı vardır.
- Sağ alt köşedeki takvimde, PDF taraması biten günler küçük mavi noktalarla işaretlenir.
- Sistem tepsisinde çalışır, yeni eşleşmelerde bildirim gösterir. Windows oturumu açıldığında otomatik başlayabilir.

Bilgisayar kapalıyken çalışmaz; açılınca yalnızca seçili aralıktaki eksik günleri tamamlar. Aralık dışındaki eski bekleyen dosyalar işlenmez; önceden okunmuş ilanlar korunur. Kontrol aralığı varsayılan olarak 30 dakikadır.

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
| `watcher/access.py` | Yönetici anahtar kasası ve imzalı tarama yetkileri |
| `watcher/admin_public_key.py` | Dağıtılabilen açık doğrulama anahtarı |
| `tools/provision_admin.py` | Yalnızca proje sahibinin ilk anahtar hazırlığı; uygulama paketine dahil edilmez |
| `tests/test_engine.py` | Otomatik testler |

Bağımlılıklar kendi lisanslarına tabidir. Özellikle PyMuPDF, AGPL / ticari çift lisanslıdır. Bu projeye ayrıca bir yazılım lisansı eklenmemiştir.
