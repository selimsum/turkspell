# Turkspell Değişiklik Günlüğü (Changelog)

Tüm önemli değişiklikler bu dosyada belgelenmektedir. Proje [Semantic Versioning](https://semver.org/) prensiplerini takip eder.

## [0.7.25] - 2026-10-23

### 🧹 Sözlük Hijyeni, Morfolojik Kural Sertleştirmesi & Kalite Kapıları
- **Bilim ve Sanat Terimleri Sözlüğü Arıtması (`lexicons/bilim_sanat_lexicon.json`)**:
  - `tools/extract_bilim_sanat_terms.py` çıkarım hattındaki Python `re.IGNORECASE` Türkçe `i`/`ı` eşleşme hatası ve tekilleştirme öncesi erken süzgeç hatası giderildi.
  - Kaynak veritabanına karışmış Anadolu ağızları (*Derleme Sözlüğü*: `ağrısık`, `babcük`, `cibillik`, `gıllik` vb.) ve Türk lehçeleri/Rusça alıntılar (*Lehçeler Sözlüğü*: `abajurcu`, `astronotluk` vb.) ile standart kelimelerin bozuk yazımları (`antreman`, `gardrop`, `ataç`, `mütevazi`) tamamen temizlendi; doğrulanmış **4.955** saf bilim, tıp, kimya, biyoloji, felsefe ve sanat terimi korundu.
- **`.aff` Ünlü Uyumu ve Morfoloji Düzeltmeleri (`tr.aff`, `tools/build.py`)**:
  - Olumsuz isim-fiil eklerinden (`-ma`/`-me`) sonra yuvarlak ünlü türeten 144 bozuk kural (`*görmesü`, `*ölmesü`, `*okumasu`, `*bulmamuz`, `*düşünmemüz` vb.) kaldırıldı.
  - Ek yazım ve ünlü uyumu hataları düzeltildi (`laryla` ➔ `larıyla`, `leryle` ➔ `leriyle`, `kilar` ➔ `kiler`) ve geçersiz `X` koşullu kurallar budandı.
  - Kendi kendini değiştiren etkisiz `REP lardan lardan` kuralı ve kullanılmayan ölü `VL` (`≛`) bayrak bloğu temizlendi.
- **`.dic` Yetim Bayrak ve Yanlış Türetim Temizliği (`tr.dic`, `lexicons/custom_names.json`)**:
  - `tr.dic` içinde karşılığı olmayan 15 yetim bayrak (`K`, `L`, `∞` ve 12 adet `≰..≼` `u1..uY` bayrağı) temizlendi.
  - `co`/`Co` kısaltma köklerinden küçültme eki bayrağı (`∍` / `CK`) kaldırılarak `*cocuklara`, `*Cocukken` gibi şapkasız/çengelsiz yazım yanlışlarının kabul edilmesi engellendi.
  - `lexicons/custom_names.json` içindeki mükerrer kayıtlar ve şapkasız `Elazığlı`/`Elazığlılık` varyantları temizlendi; `Misakımilli`/`Misakımillî` özel adına `KEEPCASE` (`∥`) bayrağı eklendi.
- **Doğrulama ve Test Altyapısı (`build/validate_build.py`, `tests/test_golden_verbs.py`)**:
  - `build/validate_build.py` aracına `.dic`/`.aff` çapraz bayrak denetimi (yetim bayraklar, kullanılmayan `SFX`/`PFX` blokları ve etkisiz `REP` kuralları) eklendi; tüm profiller **0 hata ve 0 uyarı** ile doğrulandı.
  - `tools/generate_golden_verbs.py` ve `tests/golden_verbs_baseline.json` güncellenerek 66/66 pytest birim testi ve 240 alt test %100 başarıyla geçti.

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
