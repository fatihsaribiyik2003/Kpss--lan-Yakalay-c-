# Filtre, başvuru takibi ve arayüz denetimi

## 1.7 sade kullanım denetimi

- 84 otomatik test geçti. Yeni işlem testi, duraklatılmış takipte elle kontrol isteğinin taramayı gerçekten devam ettirdiğini; profil ve başvuru kayıtlarını değiştirmediğini doğrular. Tarih araması hem ekrandaki 19.10.2026 hem 2026-10-19 biçiminde test edildi; grup seçimini aşmaz.
- Ayrı test verisiyle gerçek Tk arayüzü çalıştırıldı. 1000×700 ve 1200×800 pencere boyutlarında ana işlem düğmelerinin erişilebilirliği kontrol edildi. Kaydırılabilir yardım ekranı Windows üzerinde ayrıca gözle incelendi.
- İlanlar → KPSS → Mühendislik → Profilime göre → Akademik → Bilgisayar geçişlerinde sayılar ve sütun görünürlüğü kontrol edildi. Arama/temizleme, boş sonuçta düğmelerin kapanması, başvuru işaretleme/geri alma ve büyük ayrıntı penceresi test edildi.
- Filtre motoru değiştirilmedi; 112 kayıt üzerindeki 1.6 alt filtre sayıları korundu. Kullanım kolaylığı değerlendirmesi geliştirici kontrolüdür; bağımsız kullanıcı çalışması yapılmadı.

## 1.6 alt filtre ve unutulan belge denetimi

Genel KPSS kataloğu ile kişisel uygunluk ön filtresi ayrıldı. Önceki sürümlerin KPSS düğmesi kişisel ön adayları gösteriyordu; 1.6'da bunlar KPSS → Profilime göre altındadır. Genel KPSS sayısının artması kişisel koşulların onaylandığı anlamına gelmez.

112 kayıtlık test kopyasında bütün metinlerde KPSS, açık sınav adı ve OCR kısaltma varyantları, filtre sonuçlarından bağımsız tarandı. Sadece sonuç listesi incelenmedi; dışarıda kalan her adayla karşılaştırıldı. İlk sürümde kaçan İstanbul Teknik Üniversitesi sözleşmeli personel ilanı ve muvazzaf subay temin ilanı yakalanıp tanıma düzeltildi. Nihai katalog, metin taramasındaki 20 KPSS bağlantılı alım/duyurunun tamamını içeriyor. Salt KPSS kelimesi geçen ihale/mevzuat örneklerinin yanlış dahil edilmemesi ayrıca test edildi.

| Alt filtre | Doğrulanan PDF sayısı |
|---|---|
| KPSS / Hiçbiri | 20 |
| KPSS / Mühendislik-bilişim | 13 |
| KPSS / Düz memur-idari | 7 |
| KPSS / Diğer kadrolar | 10 |
| Akademik / Hiçbiri | 31 |
| Akademik / Mühendislik (tümü) | 19 |
| Akademik / Bilgisayar Mühendisliği | 11 |
| Akademik / Yazılım Mühendisliği | 4 |
| Akademik / Alanı net okunamayanlar | 3 |

PDF'ler birden fazla kadro içerdiği için alt gruplar örtüşür. KPSS alan alt gruplarının birleşimi 20 belgenin tamamını kapsıyor. Akademik alan grupları ve “alanı net okunamayanlar” birleşimi 31 kaydın tamamını kapsıyor. Mühendislik sözcüğü geçen akademik belgelerin tamamı genel mühendislik alt filtresiyle karşılaştırıldı; kontrol edilen veri kümesinde dışarıda kalmış belge yok.

Bilgisayar/Yazılım için alternatif mezuniyet listeleri ve doçentlik alanları ayrıca incelendi. Adana Alparslan Türkeş Bilim ve Teknoloji Üniversitesi belgesinde Yazılım Mühendisliği kadro/bölüm adı bulunurken koşul Bilgisayar Mühendisliği mezuniyetidir; bu belge yalnız bölüm başlığı nedeniyle Yazılım koşulu diye etiketlenmez. KPSS/idari grupta genel ücret paragrafındaki “destek personeli” ifadesinin açılmış kadro sanılması da engellendi.

Akademik etiketler bütün öğrenim dallarını kusursuz çözen bir tablo ayrıştırıcısı değildir. Kesin çıkarılamayan alanlar ayrı görünümde kalır; tüm belgeler filtresiz listede korunur. Bu denetim mevcut veri kümesinde eksik dosya bulmaya yöneliktir; yeni PDF düzenleri/OCR hataları için sıfır hata garantisi değildir. Kaynak metni ve kadro satırını kontrol etmek gerekir.

## 1.5 profil etki kontrolü

Profil kaydetme akışı KPSS sonuçlarını açacak ve önceki/sonraki sayıyı gösterecek şekilde güncellendi. Önceden yalnız not olarak kalan deneyim ve sınav yılı, açık koşul tespit edilebildiğinde eleme ölçütü oldu. Kanun/ilan tarihi KPSS sınav yılı kabul edilmiyor. Ücret tavanına göre 3/5 yıl gibi alternatiflerde ortak alt sınır ve ayrı kadro koşulları ayırt ediliyor.

Aynı gerçek veri kümesinde, yalnız belirtilen alan değiştirilerek test edildi:

| Test profili değişikliği | KPSS ön adayı PDF |
|---|---|
| Deneyim boş; puan/tür/yıl bilinmiyor; dil yok | 3 |
| Deneyim 0 yıl | 0 |
| Deneyim 3 yıl | 1 |
| Deneyim 5 yıl | 3 |
| Deneyim boş, KPSS yılı 2024 | 0 |
| Deneyim boş, KPSS yılı 2026 | 3 |

Bu sayılar test senaryolarıdır; kullanıcının gerçek deneyimi veya sınav yılı olarak kaydedilmemiştir. İngilizce bilgisi, dil belgesi, puan ve puan türü için ayrıca bağımsız eşik testleri vardır. İlanında açık taban puan tespit edilmeyen bir PDF, yalnız puan alanı değişti diye elenmeyebilir. Sayı aynı kalıp PDF içindeki kadrolar değişebilir. Profil değişince Tüm ilanlar/akademik/başvuru kayıtları korunur.

Denetim tarihi: 19 Ekim 2026. Sonuçlar bu tarihteki yerel veri kümesi içindir; yeni ilanlarla sayılar değişir.

## Yöntem ve kapsam

- Üretim veritabanının ayrı test kopyası kullanıldı; gerçek başvurular işaretlenmedi.
- 112 kayıtlı PDF'nin dosya envanteri ve özgün PDF metinleri kontrol edildi. Tamamlanmış/kontrol durumundaki 111 belgenin sayfa metinleri yeniden sınıflandırıldı. Bir belgenin okuma işlemi tamamlanmamıştı; filtresiz listede korunuyor.
- Önceki KPSS listesindeki beş PDF'nin mezuniyet/dil koşulları ve kadro ayrımları incelendi; ilgili sayfalar görüntüye çevrilip tablolarla karşılaştırıldı.
- Diğer personel alımlarının mezuniyet şartları, üniversite duyurularının akademik/idari/ihale ayrımı ve iptal/düzeltme başlıkları kontrol edildi. Bütün yüzlerce sayfanın tüm özel şartlarının elle onaylandığı iddia edilmez.
- Beklenen belge kimliklerinden bağımsız bir kontrol listesi oluşturuldu; liste sayıları, meslek yolu, Türkçe/aksansız arama, tarih araması, boş sonuç, başvuru işareti ve geri alma bu listeyle karşılaştırıldı.
- Birim/regresyon testleri, paketlenmiş EXE testi ve ayrı test penceresinde başvuru işaretleme/listeden bulma/geri alma kontrolü uygulandı.

## Bulunan ve düzeltilen hatalar

1. PDF'deki koordinata göre sıralanmış metin tablo başlıklarını dağıtabiliyordu. Özgün içerik sırası kullanılmaya başlandı; mevcut dosyaların yerel metni bir kez onarıldı. İndirme/OCR tekrarı yapılmadı; kayıtlı OCR çıktısı korundu.
2. Dil belgesine sıfır puan verilmesi, İngilizce bilme şartını kaldırıyormuş gibi yorumlanabiliyordu. Dil bilgisi ve sınav belgesi koşulları artık ayrı ele alınıyor.
3. Bir PDF'deki başka kadronun tercih koşulu, zorunlu dil şartını gölgeleyebiliyordu. Açık zorunlu şart artık tek başına başka bir kadronun tercihiyle kaldırılmıyor.
4. Aynı PDF'deki ayrı alım metinleri ve tanınabilen bilişim kadro başlıkları ayrı değerlendiriliyor. Listede kalan bölümlerin adları açıklamada gösteriliyor.
5. Bazı akademik başlıklar ve düzeltme/iptal duyuruları kaçıyordu. Bunlar yakalandı; iptal/düzeltme yeni bir açık alım olarak etiketlenmiyor.
6. “Herhangi bir ön lisans” ifadesi genel lisans kabulüyle karışabiliyordu. Ön lisans/lisans ayrımı ve bitişik OCR yazımları için regresyon kontrolleri eklendi.
7. Birden fazla alternatif KPSS puan türü içeren listeler ve uzman yardımcılığı giriş sınavı başlıkları için tanıma düzeltildi.

## Önceki beş KPSS kaydının sonucu

| PDF | Sonuç | Dayanak / sınır |
|---|---|---|
| [Türkiye İş Kurumu](https://www.resmigazete.gov.tr/ilanlar/eskiilanlar/2026/10/20261018-4-4.pdf) | Kontrol listesinde kaldı | Dokuz açık kadro başlığı ayrıldı. İngilizce bilgisi şartı bulunan altı bölüm elendi; kıdemli yapay zekâ, yapay zekâ ve kıdemli iş zekâsı bölümleri ön filtrede kaldı. Bu, bu kadroların bütün şartlarının karşılandığı anlamına gelmez. Deneyim ve diğer özel şartlar doğrulanmalı. |
| [Türk Akreditasyon Kurumu](https://www.resmigazete.gov.tr/ilanlar/eskiilanlar/2026/10/20261016-4-12.pdf) | Kontrol listesinde kaldı | Aynı PDF'deki uzman yardımcılığı ve sözleşmeli bilişim personeli sınavı ayrıldı. İlk bölümün dil/mezuniyet şartı ikinciye aktarılmadı; bilişim bölümü için deneyim/özel şart kontrolü sürüyor. |
| [Sayıştay](https://www.resmigazete.gov.tr/ilanlar/eskiilanlar/2026/10/20261016-4-1.pdf) | Kontrol listesinde kaldı | Dil puanı olmayanlar için sıfır değerlendirmesi var. İki yazılım kadrosu ayrıldı; özellikle deneyim ve teknik belge koşulları henüz doğrulanmış değildir. |
| [Orta Karadeniz Kalkınma Ajansı](https://www.resmigazete.gov.tr/ilanlar/eskiilanlar/2026/10/20261013-4-13.pdf) | KPSS ön listesinden çıktı | Bilgisayar mühendisliğini kapsayan uzman başvurusu için zorunlu dil belgesi koşulu var. Başka destek kadrosundaki tercih ifadesi bu koşulu kaldırmıyor. |
| [İstanbul Kalkınma Ajansı](https://www.resmigazete.gov.tr/ilanlar/eskiilanlar/2026/10/20261012-4-4.pdf) | KPSS ön listesinden çıktı | KPSS ile uzman başvurusu bölümündeki zorunlu dil belgesi koşulu, KPSS aranmaksızın deneyimle başvuru seçeneğiyle karıştırılmıyor. |

## Veri kümesindeki beklenen sonuçlar

| Görünüm | Doğrulanan sonuç |
|---|---|
| Tüm ilanlar | 112; okunmamış kayıt dahil, profil nedeniyle gizleme yok |
| KPSS / her iki yol | 3 PDF; hepsi kontrol gerektiren ön aday |
| KPSS / mühendis-bilişim | Aynı 3 PDF |
| KPSS / genel memur-idari | 0; bu veri kümesinde doğrulanan genel lisans dayanağıyla kalan ilan yok |
| Akademisyen alımları | 31 ilgili kayıt: 22 alım, 5 düzeltme, 4 iptal duyurusu |
| Başvurduklarım | Yalnızca kullanıcının işaretlediği kayıtlar; profile uymayan veya tarama aralığı dışında kalan ilan da korunur |
| Arama ve temizleme | Arama seçili görünümü daraltır; temizleme tüm kayıtları geri getirir |

## Pratik sınırlar

KPSS puanı, türü, yılı ve deneyim profilde bilinmiyorsa uygunluk onaylanmaz. “Kontrol gerekli” kaydı otomatik atama/başvuru onayı değildir. Açık başlıklarla ayrıştırılamayan karmaşık tablolar, OCR hataları, yaş, vatandaşlık, sertifika, sınav ve başvuru tarihi gibi bütün özel şartlar insan kontrolü gerektirebilir. Yeni belge biçimleri için hata olasılığı tamamen ortadan kaldırılmış değildir.

Başvuru işareti kullanıcı beyanıdır. Uygulama kuruma başvuru göndermez, kurumdan kabul veya kazanma sonucu aldığını varsaymaz.
