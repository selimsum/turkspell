# Turkspell Değişiklik Günlüğü (Changelog)

Tüm önemli değişiklikler bu dosyada belgelenmektedir. Proje [Semantic Versioning](https://semver.org/) prensiplerini takip eder.

## [Unreleased]

### 🛠️ Morfoloji, TDK Kısaltma Kuralları ve Kalite İyileştirmeleri
- **TDK Noktalı ve Üs İşaretli Kısaltma Desteği (`build/generate_grammar_rules.py`, `build/build_common.py`, `tools/build.py`, `lexicons/build_wordlists.json`)**:
  - Sonunda nokta bulunan kısaltmalarla (`vb.leri`, `Alm.dan`, `İng.yi`, `a.g.e.de`, `Dr.a`, `Prof.e`, `yy.da`, `T.C.nde`) üs işaretli kısaltmalara/sayılara (`cm³e`, `m²ye`, `6⁴ten`, `10⁶ya`) gelen eklerin kesme işareti olmadan okunuşa uygun bitişik yazılması sağlandı; kesmeli hatalı biçimler (`vb.'leri`, `Alm.'dan`, `cm³'e`, `m²'ye`, `6⁴'ten`) reddedilip `REP` kurallarıyla Top-1 öneriye bağlandı.
  - `WORDCHARS` başlığına üs rakamları (`⁰¹²³⁴⁵⁶⁷⁸⁹`) eklendi; noktalı kısaltmalara sızan cins isim/yapım eki ve özel ad kesme bayrakları temizlendi.
- **Morfolojik Aşırı Üretim ve Saat Düzeltmeleri (`build/generate_grammar_rules.py`, `build/build_common.py`)**:
  - Yuvarlak geniş zaman fiil köklerindeki uyumsuz 2. tekil/çoğul biçimler (`*olursın`, `*görürsin`, `*bulursınız`, `*ölürsiniz`) kaldırıldı.
  - Yumuşayan adlarda 1. tekil/çoğul ek eylem (`VC`/`vc`) kurallarına yuvarlaklık uyumu koşulları eklendi (`*devletüm`, `*pilotım`, `*stokım`, `*çöpim` engellendi).
  - 24 saatlik saat gösteriminde geçersiz `24.01`–`24.59` kökleri kaldırıldı (`24.00` korundu).
  - `tools/build.py` içindeki `seen_heads` demet uyumsuzluğu giderilerek `mat`, `zıt`, `kal`, `ark`, `tutamak` köklerine sızan fazladan bayraklar temizlendi.
- **Tekrarlanabilir Derleme, CI ve Kod Temizliği**:
  - Ortak Türkçe harf dönüştürme (`tr_lower`/`tr_upper`/`tr_title`), `find_hunspell()`, sayı/üs üretimi ve `noun_chain` yardımcıları `build/build_common.py` modülünde birleştirilerek `build/` ↔ `tools/build.py` döngüsel bağımlılığı kaldırıldı.
  - Temiz klonlarda `--compile-base` derlemesinin eksiksiz çalışması için `raw_data/tdk_dizin_2026.json` ve `raw_data/custom_entries.json` sürüm kontrolüne alındı ve eksik girdi sessizce atlanmak yerine hata fırlatacak şekilde sertleştirildi.
  - CI iş akışı (`.github/workflows/test.yml`) `--compile-base` tekrarlanabilirliğini ve `TDK`/`DD` profilleri için tam morfoloji + fiil regresyon testlerini doğrulayacak şekilde genişletildi (`tests/test_morphology.py` içindeki `görmemezlik` TDK profili koruması eklendi).
  - `README.md` içindeki 44 yerel `file:///` bağlantısı göreli depo yollarıyla değiştirildi, metrikler güncellendi, `tools/profile_affix_rules.py` UTF-8 BOM'u ve araçlardaki sabit yerel makine yolları temizlendi.

## [0.7.26] - [0.7.40] - 2026-10-24 / 2026-11-26

### ✨ Öne Çıkan Değişiklikler (Git Geçmişi Özeti)
- **FineWeb-2 Derlem Madenciliği ve Öneri (`REP`) Genişletmeleri**: Büyük Türkçe derlemlerden doğrulanmış yüzlerce ortografik yazım yanlışı, ayrı/bitişik bileşik ve bağlaç (`de`/`da`, `ki`, `mı`) düzeltme kuralı eklendi.
- **Derleme Boru Hattı ve Bayrak Hijyeni**: Satır içi kelime listeleri ve istisnalar `lexicons/build_wordlists.json` dosyasına taşındı; cins isim bayrak şişkinliği ve ara derleme uyarıları giderildi; `--compile-base` ve artımlı derlemeler %100 bayt-özdeş (idempotent) hâle getirildi.
- **Özel Ad Kesme Sözleşmesi**: Özel adlardan kesmesiz cins isim hal/iyelik bayrakları ayrıştırıldı; sürüm otomasyonu ve çoklu profil CI doğrulamaları eklendi.

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
