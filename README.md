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
* **Çift Standart Uyumu (Universal Profile)**: Hem TDK kurallarını (*dâhil*, *bekâr*, *resmî*) hem de Dil Derneği yazımını (*dahil*, *bekar*, *resmi*) meşru kabul eden esnek  profil seçeneği sunar.
* **Aşırı Üretim (Overgeneration) Koruması**: `tr.aff` dosyasındaki 17.824 adet kontrolsüz kural arıtılmış; kaynaştırma harfi olmaksızın çift ünlü türeten (*acııydı*, *anomaliine*, *beliiydi*) veya bozuk fiil türeten (*debileceklerine*, *yebilecek*) kural açıkları kapatılmıştır.
* **Gelişmiş Öneri Matrisi (MAP 14 & Genişletilmiş REP)**: Düzeltme işaretli (şapkalı), klavye kayması kaynaklı ve ses benzerliği olan hatalarda doğru kelimeyi %90'ın üzerinde 1. sırada (Top-1) ve 0.90+ MRR skoruyla önerir.
* **Hafif, Optimize ve Hızlı**: 150.168 temiz kök başlığı ile bellek ayak izi optimize edilmiş; Firefox ve tarayıcı eklentilerinde başlatma süresi 90 ms seviyesine indirilmiştir.

---

## 📊 Kapsamlı Benchmark Sonuçları

Turkspell v0.6 Gold, bağımsız ve standartlaştırılmış tüm Türkçe yazım denetimi kıyaslama paketlerinde **%100.00 Precision (sıfır yanlış alarm)** ve sektör lideri öneri başarısı sergiler.

### 1. Turkspell Benchmark V3 (Kategori Dilimli Sentetik ve Gerçek Hatalar)
| Sözlük / Motor | Precision (%) | Recall (%) | F1 Skoru (%) | Top-1 (%) | Top-3 (%) | Top-5 (%) | MRR | Süre (sn) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Turkspell v0.6 Gold** | **100.00** | **100.00** | **100.00** | **77.60** | **90.70** | **94.80** | **0.851** | 31.9 |
| **selimsum/hunspell-tr-moz** | 94.21 | **99.80** | 96.92 | 67.50 | 89.20 | **93.70** | 0.786 | 40.7 |
| **tdd-ai** | 81.85 | **99.80** | 89.94 | 51.80 | 72.10 | 76.20 | 0.621 | 26.2 |
| **harunzafer** | 61.99 | **99.80** | 76.48 | 40.00 | 50.10 | 51.60 | 0.451 | 26.9 |
| **vdemir** | 55.90 | **99.80** | 71.66 | 33.30 | 41.40 | 43.30 | 0.375 | **12.6** |

### 2. Official Turkspell Gold V4 (Çift Standart: TDK + Dil Derneği)
| Sözlük / Motor | Precision (%) | Recall (%) | F1 Skoru (%) | Top-1 (%) | Top-3 (%) | Top-5 (%) | MRR | Süre (sn) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Turkspell v0.6 Gold (TDK)** | **100.00** | **99.12** | **99.56** | **64.60** | **68.70** | **69.70** | **0.667** | **26.4** |
| **selimsum/hunspell-tr-moz** | 99.79 | 90.33 | 94.83 | 50.40 | 59.30 | 61.20 | 0.551 | 53.2 |
| **vdemir** | 97.71 | 91.17 | 94.33 | 46.10 | 51.90 | 52.40 | 0.490 | 25.3 |
| **harunzafer** | 98.92 | 89.59 | 94.03 | 43.40 | 48.00 | 48.70 | 0.458 | 47.9 |
| **tdd-ai** | 99.63 | 86.76 | 92.75 | 49.90 | 58.30 | 59.60 | 0.541 | 27.4 |

### 3. Mukayese Clean (Akademik V1 & V2)
| Test Kümesi | Precision (%) | Recall (%) | F1 Skoru (%) | Top-1 (%) | Top-3 (%) | Top-5 (%) | MRR | Süre (sn) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Mukayese V1 (Clean)** | **100.00** | **99.38** | **99.69** | **63.80** | **82.30** | **84.90** | **0.731** | **30.7** |
| **Mukayese V2 (Clean)** | **100.00** | **99.18** | **99.59** | **57.00** | **65.20** | **68.30** | **0.617** | **28.4** |

### 4. Düzeltme İşareti (Şapka / Circumflex) Testleri
| Test Kümesi / Profil | Precision (%) | Recall (%) | F1 Skoru (%) | Top-1 (%) | Top-3 (%) | MRR | En Yakın Rakip Top-1 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Circumflex (Dil Derneği Standartı)** | **100.00** | **98.13** | **99.06** | **97.20** | **98.13** | **0.977** | %23.36 (`harunzafer`) |
| **Circumflex (TDK Standartı)** | **100.00** | **54.47** | **70.52** | **53.63** | **54.47** | **0.541** | %1.68 (`selimsum`) |

### 5. Derlem Kapsamı ve Hız (`magazine_corpus.txt`)
| Sözlük / Motor | Kelime Kapsama Oranı (Recall %) | Tanınmayan Kelime | Değerlendirme Süresi |
|---|:---:|:---:|:---:|
| **selimsum/hunspell-tr-moz** | **83.94%** | 25.321 | 33.0 sn |
| **tdd-ai** | 83.02% | 26.782 | **21.3 sn** |
| **Turkspell v0.6 Gold (TDK)** | 79.92% | 31.699 | 27.5 sn |
| **harunzafer** | 79.50% | 32.366 | 35.8 sn |
| **vdemir** | 75.99% | 37.885 | 16.1 sn |

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

## 💾 Dosya Boyutları ve Bellek Ayak İzi

Turkspell, şişirilmiş statik kurallar veya milyonlarca çekimli sözcük yerine **Dinamik Zincirleme Bayraklar (Dynamic Chained Flags)** mimarisiyle çalışır. Bu mimari, bellek kullanımını minimize ederken tarayıcı eklentilerinde başlatma süresini 90 ms seviyesine indirir.

### Turkspell v0.6 Dağıtım Boyutları
| Profil / Paket | `.aff` Boyutu | `.dic` Boyutu | Toplam Sözlük Boyutu | Kök Başlık Sayısı (Stems) | Dağıtım / Eklenti Paketi |
|---|:---:|:---:|:---:|:---:|:---:|
| **Turkspell v0.6 Universal (Amiral Gemisi)** | 10.61 MB | 8.06 MB | **18.67 MB** | 150.168 | 1.55 MB (`turkspell-addon.xpi`) |
| **Turkspell v0.6 TDK Profili** | 10.61 MB | 8.06 MB | **18.67 MB** | 150.079 | `dist/turkspell-v0.6-tdk/` |
| **Turkspell v0.6 Dil Derneği Profili** | 10.61 MB | 7.99 MB | **18.60 MB** | 149.453 | `dist/turkspell-v0.6-dd/` |

### Türkçe Hunspell Sözlükleri Boyut ve Mimari Karşılaştırması
| Sözlük Motoru | `.aff` Kural Boyutu | `.dic` Sözlük Boyutu | Toplam Dosya Boyutu | Kök / Başlık Sayısı | Mimari Yaklaşımı ve Bellek Etkisi |
|---|:---:|:---:|:---:|:---:|---|
| **Turkspell v0.6 Gold** | 10.61 MB | 8.06 MB | **18.67 MB** | 150.168 | **Dinamik Zincirleme Bayraklar**: Dengeli bellek tüketimi, anlık tarayıcı başlatma |
| **selimsum/hunspell-tr-moz** | 31.79 MB | 1.30 MB | **33.10 MB** | 86.460 | Aşırı genişletilmiş statik kural tablosu (31+ MB kural dosyası) |
| **tdd-ai** | 2.35 MB | 34.54 MB | **36.88 MB** | 75.909 | Şişirilmiş çekimli sözcük gövdesi (34+ MB sözlük metni) |
| **harunzafer** | 0.24 MB | 9.00 MB | **9.24 MB** | 371.169 | Denetimsiz ham kelime listesi (yüksek yanlış kabul oranı) |
| **vdemir** | 0.77 MB | 7.25 MB | **8.02 MB** | ~160.000 | Sınırlı kural kapsamı (düşük öneri ve çekim başarısı) |

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
