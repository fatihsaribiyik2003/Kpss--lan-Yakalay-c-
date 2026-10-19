# KPSS İlan Yakalayıcı

Windows üzerinde çalışan, Resmî Gazete'nin **Çeşitli İlanlar** bölümünü otomatik takip eden masaüstü uygulaması.

## Özellikler

- İlk çalıştırmada son 30 günü, sonraki kontrollerde yeni ve eksik günleri tarar. Başlangıç tarihi değiştirilebilir.
- Varsayılan olarak **KPSS, lisans, bilişim, bilgisayar, yazılım** kelimelerini arar. Kelimelerden birinin geçmesi yeterlidir.
- PDF metnini okur; görüntü içeren sayfalarda bilgisayar üzerinde OCR çalıştırır. Ücretli API anahtarı gerekmez.
- İşlenmiş PDF'leri tekrar indirmez. Aynı içerik farklı bir bağlantıyla yayımlanırsa kayıtlı sayfa metinlerini kullanır.
- Yarım kalan işlemleri kaldığı yerden sürdürür; indirme ve okuma hatalarını otomatik yeniden dener.
- Sonuçlarda kurum, tarih, kelimeler, sayfalar ve ilgili metin parçası gösterilir. CSV dışa aktarımı vardır.
- Sağ alt köşedeki takvimde, PDF taraması biten günler küçük mavi noktalarla işaretlenir.
- Sistem tepsisinde çalışır, yeni eşleşmelerde bildirim gösterir. Windows oturumu açıldığında otomatik başlayabilir.

Bilgisayar kapalıyken çalışmaz; açılınca seçili tarih aralığındaki eksik günleri tamamlar. Kontrol aralığı varsayılan olarak 30 dakikadır.

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
| `tests/test_engine.py` | Otomatik testler |

Bağımlılıklar kendi lisanslarına tabidir. Özellikle PyMuPDF, AGPL / ticari çift lisanslıdır. Bu projeye ayrıca bir yazılım lisansı eklenmemiştir.
