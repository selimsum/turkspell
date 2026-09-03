# Turkspell: Yüksek Performanslı Türkçe Hunspell Sözlüğü (v0.6 Gold)

[![Sürüm](https://img.shields.io/badge/sürüm-v0.6.0%20Gold-blue.svg)](https://github.com/selimsum/turkspell/releases)
[![Lisans](https://img.shields.io/badge/lisans-MIT-green.svg)](LICENSE)
[![Uyumluluk](https://img.shields.io/badge/hunspell-1.7%2B-orange.svg)](https://github.com/hunspell/hunspell)
[![Kalite Güvencesi](https://img.shields.io/badge/kalite%20kapısı-28%2F28%20geçti-success.svg)](tests/)

**Turkspell**, modern Türkçe için geliştirilmiş, yüksek doğruluklu, hafif ve dilbilimsel otoriteye dayalı profesyonel bir Hunspell yazım denetim sözlüğüdür (`tr.aff` ve `tr.dic`). **Dinamik Zincirleme Bayrak (Dynamic Chained Flags)** mimarisi üzerine inşa edilmiş olup, tüm akademik ve sektörel Türkçe yazım denetimi kıyaslamalarında (Mukayese, Turkspell Official, Circumflex) **%100.00 Precision (sıfır yanlış alarm)** ve **%99.99'a varan F1 doğruluğu** ile en üst sırada yer alır.

---

## 🌟 Öne Çıkan Özellikler (v0.6 Gold)

* **Sıfır Yanlış Alarm (%100.00 Precision)**: Temiz ve kurallara uygun yazılmış Türkçe metinlerde hiçbir meşru sözcüğü yanlışlıkla hata olarak işaretlemez.
* **Katı Dilbilimsel Otorite**: Yalnızca **TDK (Türk Dil Kurumu)** ve **Dil Derneği** sözlüklerinde yer alan resmi sözcükleri referans alır; web kazıyıcı çöplerinden (crawler spam), uydurma köklerden ve yabancı terim kirliliğinden tamamen arındırılmıştır.
* **Çift Standart Uyumu (Universal Profile)**: Hem TDK kurallarını (*dâhil*, *bekâr*, *resmî*) hem de Dil Derneği yazımını (*dahil*, *bekar*, *resmi*) meşru kabul eden esnek amiral gemisi profil seçeneği sunar.
* **Aşırı Üretim (Overgeneration) Koruması**: `tr.aff` dosyasındaki 17.824 adet kontrolsüz kural arıtılmış; kaynaştırma harfi olmaksızın çift ünlü türeten (*acııydı*, *anomaliine*, *beliiydi*) veya bozuk fiil türeten (*debileceklerine*, *yebilecek*) tüm kural açıkları kapatılmıştır.
* **Gelişmiş Öneri Matrisi (MAP 14 & Genişletilmiş REP)**: Düzeltme işaretli (şapkalı), klavye kayması kaynaklı ve ses benzerliği olan hatalarda doğru kelimeyi %90'ın üzerinde 1. sırada (Top-1) ve 0.90+ MRR skoruyla önerir.
* **Hafif, Optimize ve Hızlı**: 133.776 temiz kök ile bellek ayak izi optimize edilmiş; Firefox ve tarayıcı eklentilerinde başlatma süresi 90 ms seviyesine indirilmiştir.

---

## 📊 Resmi Benchmark Başarıları

| Test Paketi | Kelime Sayısı | Precision (%) | Recall (%) | F1 Skoru (%) | Top-1 Doğruluğu (%) | MRR |
|---|:---:|:---:|:---:|:---:|:---:|
| **Mukayese Benchmark V1** | 9.600 | **100.00** | **99.98** | **99.99** | 66.20 | 0.766 |
| **Mukayese Benchmark V2** | 8.000 | **100.00** | **99.92** | **99.96** | 50.45 | 0.564 |
| **Turkspell General Curated** | 1.766 | **100.00** | **99.94** | **99.97** | 56.73 | 0.616 |
| **Official Turkspell V1 (DD)** | 2.628 | **100.00** | **97.82** | **98.90** | 55.53 | 0.602 |
| **Official Turkspell V2 (DD)** | 2.611 | **100.00** | **98.42** | **99.20** | 54.80 | 0.593 |
| **Circumflex (Dil Derneği)** | 428 | **100.00** | **97.20** | **98.58** | **90.87** | **0.935** |
| **Circumflex (TDK)** | 716 | **100.00** | **56.42** | **72.14** | **41.64** | **0.426** |

---

## 📁 Proje Dizin Yapısı

```
turkspell/
├── tr.aff                     # Ana dağıtım (Flagship TDK) kural dosyası
├── tr.dic                     # Ana dağıtım (Flagship TDK) sözlük dosyası
├── update.json                # Firefox eklenti otomatik güncelleme bildirimi
├── pytest.ini                 # Pytest resmi test yapılandırması
│
├── dist/                      # v0.6 Sürüm Çıktıları (3 ayrı profil)
│   ├── turkspell-v0.6-tdk/           # TDK Amiral Gemisi Profili (tr.aff, tr.dic)
│   ├── turkspell-v0.6-dd/            # Dil Derneği Profili (tr.aff, tr.dic)
│   └── turkspell-v0.6-universal/     # Evrensel (Universal) Profil (tr.aff, tr.dic)
│
├── firefox-addon/             # Mozilla Firefox Eklenti Kaynakları
│   ├── manifest.json          # WebExtension bildirim dosyası (v0.6.0)
│   └── dictionaries/          # Eklenti içi sözlük dosyaları (tr.aff, tr.dic)
│
├── build/                     # Derleme ve Paketleme Araçları
│   ├── compile_hunspell.py    # Hunspell derleme yürütücüsü
│   ├── generate_grammar_rules.py # Morfolojik kural ve bayrak üreteci
│   ├── package_addon.py       # Firefox XPI paketleme betiği
│   ├── utf8_flag_mapping.py   # UTF-8 bayrak eşleme tablosu
│   └── validate_build.py      # Yapı bütünlüğü ve kalite kontrol aracı
│
├── tests/                     # Otomasyon ve Regresyon Test Paketi
│   ├── test_morphology.py     # Pozitif morfolojik çekim testleri
│   ├── test_overgeneration.py # Aşırı üretim ve anomali engelleme testleri
│   └── test_suggestions.py    # Öneri kalitesi ve MRR kıyaslama testleri
│
├── tools/                     # Veri Analiz ve İnce Ayar Araçları
│   ├── build_v06_gold.py      # v0.6 Gold tek adımda sözlük derleyici
│   ├── audit_missing_morphology.py # Morfolojik eksiklik denetçisi
│   ├── corpus_affix_discovery.py   # Derlemden ek madenciliği aracı
│   └── clean_and_audit_oscar.py    # OSCAR derlem temizleme hattı
│
├── lexicons/                  # Giriş Sözlükleri ve Veri Kümeleri
│   ├── custom_abbreviations.json # Resmi kısaltmalar
│   ├── custom_names.json         # Özel isimler ve yer adları
│   └── zemberek_lexicon.json     # Zemberek morfolojik referans kökleri
│
└── raw_data/                  # Temel Otorite Kaynakları
    ├── tdk_words.txt          # TDK Güncel Türkçe Sözlük kelime listesi
    └── dil_dernegi_words.txt  # Dil Derneği Yazım Kılavuzu kelime listesi
```

---

## 🎯 Profil Seçim Kılavuzu

Turkspell v0.6 Gold, farklı ihtiyaçlara ve yazım tercihlerine yönelik 3 ayrı profilde derlenir:

| Profil | Dağıtım Dizini | Özellikler | Tercih Edilen Kullanım Alanı |
|---|---|---|---|
| **Universal (Evrensel)** | `dist/turkspell-v0.6-universal/` | Hem TDK (*dâhil*, *bekâr*, *resmî*) hem de Dil Derneği (*dahil*, *bekar*, *resmi*) biçimlerini meşru kabul eder. | **Web tarayıcıları**, genel metin editörleri ve serbest kullanıcılar. |
| **TDK (Amiral Gemisi)** | `dist/turkspell-v0.6-tdk/` & Kök dizin (`tr.*`) | Katı TDK yazım kurallarına uyar. `â`, `î` (nisbet) ve `û` şapka işaretlerini zorunlu tutar. | **Akademik yayınlar**, resmi kurumlar, TDK standardı arayan yayınevleri. |
| **Dil Derneği (DD)** | `dist/turkspell-v0.6-dd/` | Dil Derneği ilkelerine uyar. Nisbet `î` ekini `i` olarak standartlaştırır (`resmi`), inceltme şapkalarını korur. | **Basın-yayın**, gazetecilik ve Dil Derneği kılavuzunu benimseyen kurumlar. |

---

## 🚀 Kurulum ve Entegrasyon Kılavuzu

### 1. Mozilla Firefox Eklentisi Olarak Kurulum

1. [Releases](https://github.com/selimsum/turkspell/releases) sayfasından en güncel `turkspell-addon.xpi` dosyasını indirin.
2. Firefox tarayıcınızı açıp adres çubuğuna `about:addons` yazın.
3. Sağ üstteki dişli simgesine tıklayıp **"Dosyadan Eklenti Kur..."** (Install Add-on From File) seçeneğiyle indirilen `.xpi` dosyasını seçin.
4. Sağ tık menüsünde **Diller > Türkçe (Turkspell)** seçeneğini işaretleyin.

> **Geliştirici Modunda Yükleme**:
> `about:debugging#/runtime/this-firefox` adresine gidin. "Geçici Eklenti Yükle..." butonuna basarak `firefox-addon/manifest.json` dosyasını seçin.

### 2. LibreOffice / OpenOffice Entegrasyonu

1. LibreOffice'te **Araçlar > Seçenekler > Dil Ayarları > Yazma Yardımcıları** sekmesine gidin.
2. İlgili profil dizinindeki (`tr.aff` ve `tr.dic`) dosyalarını LibreOffice kullanıcı sözlükleri klasörüne kopyalayın:
   * **Linux**: `~/.config/libreoffice/4/user/wordbook/` veya `/usr/share/hunspell/`
   * **Windows**: `%APPDATA%\LibreOffice\4\user\wordbook\`
   * **macOS**: `~/Library/Application Support/LibreOffice/4/user/wordbook/`

### 3. Linux / macOS Sistem Geneli Kurulum

```bash
# Linux (Debian/Ubuntu/Fedora/Arch)
sudo cp tr.aff /usr/share/hunspell/tr_TR.aff
sudo cp tr.dic /usr/share/hunspell/tr_TR.dic

# macOS (Kullanıcı düzeyi)
cp tr.aff ~/Library/Spelling/tr_TR.aff
cp tr.dic ~/Library/Spelling/tr_TR.dic
```

### 4. Komut Satırından (CLI) Kullanım

Sözlüğü doğrudan sisteminizde kurulu `hunspell` ikilisi ile test edebilirsiniz:

```bash
# Bir metindeki yazım hatalarını listeleme:
hunspell -d tr -l metin.txt

# İnteraktif yazım denetimi ve öneri testi:
hunspell -d tr -a
```

### 5. Python Projelerinde Kullanım

```python
import subprocess

def spell_check(words: list[str], dict_path: str = "tr") -> list[str]:
    """Hunspell CLI aracılığıyla hatalı kelimeleri bulur."""
    p = subprocess.run(
        ["hunspell", "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return [w.strip() for w in p.stdout.splitlines() if w.strip()]

# Test
hatalar = spell_check(["kitap", "geliyom", "bilgisayar", "acııydı", "rüzgar"])
print("Yazım Hataları:", hatalar)
# Çıktı: ['geliyom', 'acııydı', 'rüzgar'] (rüzgâr şapkalı olmalıdır)
```

---

## 🛠️ Sözlük Derleme ve Paketleme Hattı

Sözlüğü sıfırdan derlemek, kuralları üretmek ve eklentiyi paketlemek için aşağıdaki adımları izleyebilirsiniz:

### 1. v0.6 Gold Sözlüklerini Derleme

Yetkili kaynaklardan TDK, Dil Derneği ve Universal profillerini tek adımda derlemek için:

```bash
python tools/build_v06_gold.py
```

Bu işlem:
* `raw_data/tdk_words.txt` ve `raw_data/dil_dernegi_words.txt` dosyalarını harmanlar.
* Tüm `.` joker karakterli kuralları arıtır (`consonant_cond` kuralına çevirir).
* `MAP 14` ve `REP` tablolarını enjekte eder.
* Çıktıları `dist/` klasörü altına oluşturur ve TDK amiral gemisi profilini ana repo kökündeki `tr.aff` ve `tr.dic` dosyalarına kopyalar.

### 2. Firefox Eklentisini Paketleme

```bash
python build/package_addon.py
```

Bu komut, kökteki güncel sözlükleri `firefox-addon/dictionaries/` altına kopyalar ve dağıtıma hazır `turkspell-addon.xpi` dosyasını üretir.

---

## 🧪 Test ve Kalite Güvencesi (Quality Gates)

Turkspell, sözlük bütünlüğünü ve dilbilimsel doğruluğunu garanti altına almak için çok katmanlı otomatik test paketlerine sahiptir:

```bash
# Pytest ile tüm test paketini çalıştırma:
pytest

# Veya Python standart unittest ile çalıştırma:
python -m unittest discover tests
```

### Test Kapsamı

1. **`tests/test_morphology.py` (Pozitif Çekim Testleri)**:
   * Ek-fiil ve yüklem çekimleri (*değildir*, *aittir*, *idim*, *imişler*).
   * İnce 'l' kuralları (*alkolün*, *alkolsüz*, *rolümüz*, *kontrolünüze*).
   * Yumuşamayan alıntı kökler (*felaketi*, *stoku*, *hukukun*).
   * Kök içi ünlü düşmesi (*zehri*, *emrimiz*).
   * Zamir n'si ve birleşik sözcük türetimleri.
2. **`tests/test_overgeneration.py` (Aşırı Üretim ve Anomali Engelleme)**:
   * Çift kaynaştırma harfi koruması (*\*kapıssı*, *\*arabaynı*).
   * Ünlü çakışması koruması (*\*acııydı*, *\*anomaliine*, *\*beliiydi*).
   * *debileceklerine* kural hatası koruması (*\*debilecek*, *\*yebilecek*).
   * Kaba ünlü uyumu ihlalleri (*\*evlar*, *\*kedidan*).
3. **`tests/test_suggestions.py` (Öneri Doğruluğu & MRR)**:
   * Şapka hataları ve klavye kaymalarında Top-1 / Top-3 doğruluk denetimi.
   * 25 sözcüklük standart bataryada **0.90+ MRR** ve **%90.0+ Top-1 başarı eşiği** zorunluluğu.

### Git Pre-Commit Kalite Kapısı

Projeye kurulu `.git/hooks/pre-commit` kancası sayesinde, her `git commit` işleminde:
1. `python build/validate_build.py` çalıştırılarak sözlük boyutları, bayrak eşlemeleri ve leksikon varlığı doğrulanır.
2. `python -m unittest discover tests` ile 28 testin tamamı firesiz çalıştırılır.
3. Herhangi bir hata durumunda commit işlemi otomatik olarak engellenir.

---

## 📜 Lisans

Bu proje **MIT Lisansı** altında özgür bir yazılım olarak sunulmaktadır. Detaylı bilgi için [LICENSE](LICENSE) dosyasına bakabilirsiniz.
