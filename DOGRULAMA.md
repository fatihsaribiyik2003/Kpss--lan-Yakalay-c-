# 1.4 filtre ve başvuru takibi denetimi

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
