# Turkspell Değişiklik Günlüğü (Changelog)

Tüm önemli değişiklikler bu dosyada belgelenmektedir. Proje [Semantic Versioning](https://semver.org/) prensiplerini takip eder.

## [0.7.0] - 2026-10-07

### 🚀 Öne Çıkan Başarılar & Metrikler (Milestones)
- **Öneri Motorunda Büyük Sıçrama**: Flagship Benchmark V2 testlerinde Top-1 öneri doğruluğu **%79.40'tan %87.20'ye**, MRR (Mean Reciprocal Rank) skoru **0.843'ten 0.904'e** yükseldi (0.90 psikolojik eşiği aşıldı).
- **TDK Doğruluğu**: Turkspell (TDK) profilinde Top-1 doğruluğu **%73.30'dan %80.90'a**, MRR **0.780'den 0.840'a** ulaştı.
- **Sıfır Yanlış Alarm**: %99.99 - %100.00 Precision ile temiz ve doğru yazılmış Türkçe metinlerde meşru kelimeleri hata saymama standardı korundu.
- **Tam Test Başarısı**: 47/47 pytest birim testi ve 25/25 öneri bataryası (%100 Top-1, 1.000 MRR) ile sıfır regresyon sağlandı.

### ✨ Yeni Özellikler & İyileştirmeler (Added & Improved)
1. **TDK 2026 Resmî Morfoloji Entegrasyonu (`tdk_dizin_2026.json`)**:
   - TDK'nin resmî 2026 dizinindeki `e` (çekim eki) alanları otomatik analiz edilerek derleyiciye entegre edildi:
     - **9.765 kelimede** resmî ünsüz yumuşaması (`Voicing`: `p, ç, t, k` ➔ `b, c, d, ğ`).
     - **360 kelimede** ince 'l' ve alıntı sözcük ters ünlü uyumu (`InverseHarmony`: *alkol*, *saat*, *petrol*, *kontrol*, *terminal*, *festival*, *kristal* vb.).
     - **256 kelimede** orta hece ünlü düşmesi (`LastVowelDrop`: *akıl*, *şehir*, *fikir*, *resim*, *cisim*, *metcezir* vb.).
     - **239 fiilde** geniş zaman aorist eki (`Aorist_A`: `-ar`/`-er`).
     - **56 kelimede** ünsüz ikizleşmesi (`Doubling`: *ad ➔ addi*, *af ➔ affı*, *hat ➔ hattı*, *tıp ➔ tıbbı*, *hak ➔ hakkı*).
2. **Kapsamlı Birleşik ve Ayrı Yazım Kural Seti**:
   - Ses olayı olmayan yardımcı fiillerin hem mastar hem çekimli formları (`farketti`, `terketti`, `ayırdetmek`, `arzetmek`, `haketmek`, `yokoldu`, `varoldu` vb.) öneri motoruna eklendi.
   - Sıkça bitişik yazılan ikilemeler (`yanyana`, `başbaşa`, `gözgöze`, `dizdize`, `omuzomuza`, `içiçe`, `üstüste`, `altalta`, `adımadım`, `arkaarkaya` vb.) ayrıştırılarak Top-1 öneriye bağlandı.
   - Zaman, miktar ve nezaket öbekleri (`haftasonu`, `haftaiçi`, `herşey`, `birşey`, `pekçok`, `sağol`, `hoşçakal`, `hoşgeldin`, `tabiki`, `iyiki` vb.) için kural seti genişletildi.
3. **Klavye Komşuluk Matrisi (`KEY`) ve `MAP` Optimizasyonu**:
   - Türkçe Q ve Türkçe F klavyelerinin komşuluk grupları yatay/dikey/çapraz eksiksiz matris haline getirildi.
   - `MAP` tablosundaki 14 eşdeğerlik grubu klavye matrisine senkronize edildi.
4. **TDK Terim ve İkileme Köklerinin Kurtarılması**:
   - TDK tamlamalarında geçen fakat bağımsız madde listelenmediği için hata sayılan **347 temiz TDK kökü** (*adezyon*, *amino*, *kamkat*, *allak*, *bullak*, *abur*, *cubur*, *afra*, *tafra*, *börtü*, *bıngıl*, *cayır*, *cızır*, *derli*, *dulavrat*, *eften*, *süklüm*, *tiril*, *ıvır*, *zıvır*, *paratiroit*, *onikiparmak*, *tatlısu*, *sendeci* vb.) sözlüğe kazandırıldı.
5. **Fiil ve İsim Morfolojisi Genişletmesi**:
   - Fiil çekim ağacı faktörize edilerek kurallı fiil çekimleri tamamlandı.
   - Ek eylem (copula) ve isim morfolojisi uyumlandırıldı.

### 🧹 Temizlik & Düzeltmeler (Fixed & Removed)
- `circumflex_typos` içindeki bozuk/uydurma 669 hatalı kural (`kasâp`, `insân`, `kültûr`, `ê`, `ô`) ayıklandı; doğrulanmış tekil TDK çiftleri korundu.
- Hunspell `REP` motorunda boşluk içeren önerilerin ilk kelimeden sonrasını budamasına neden olan sentaks hatası düzeltildi (`_` alt tire kuralı uygulandı).
- Eski ve atıl yedek dosyası `tdk_words_old.txt` kaldırıldı; tüm kaynaklar en güncel `tdk_dizin_2026.json` standardına bağlandı.
