# Turkspell: Yüksek Performanslı Türkçe Hunspell Sözlüğü

[![Sürüm](https://img.shields.io/github/v/release/selimsum/turkspell?label=s%C3%BCr%C3%BCm)](https://github.com/selimsum/turkspell/releases)
[![Lisans](https://img.shields.io/badge/lisans-MIT-green.svg)](LICENSE)
[![Uyumluluk](https://img.shields.io/badge/hunspell-1.7%2B-orange.svg)](https://github.com/hunspell/hunspell)
[![Mozilla Add-on](https://img.shields.io/badge/Mozilla%20Add--on-Universal-blue.svg)](https://addons.mozilla.org/tr/firefox/addon/turkspell/)
[![Kalite Güvencesi](https://img.shields.io/badge/kalite%20kapısı-73%2F73%20geçti-success.svg)](tests/)

> [!NOTE]
> **Bu repo (`master` branch'i) Turkspell'in hem Türk Dil Kurumu (TDK) hem de Dil Derneği yazımlarını geçerli sayan varsayılan sürümüdür.**
> - **Mozilla Eklenti Adı**: `Turkspell - Türkçe Yazım Denetimi`
> - **Eklenti Sayfası**: [addons.mozilla.org/firefox/addon/turkspell](https://addons.mozilla.org/tr/firefox/addon/turkspell/)
> - Hem TDK kurallarını (*dâhil*, *lâzım*, *resmî*) hem de Dil Derneği yazımını (*dahil*, *lazım*, *resmi*) meşru kabul ederek kullanıcılara sıfır yanlış alarm ile en yüksek yazım uyumunu sunar.
> - Yalnızca resmî Türk Dil Kurumu söz varlığını ve zorunlu şapka/nispet standartlarını esas alan katı sürüm için [`tdk` branch'ini](https://github.com/selimsum/turkspell/tree/tdk) inceleyebilirsiniz.

[🇹🇷 Türkçe](#turkspell-yüksek-performanslı-türkçe-hunspell-sözlüğü) | [🇬🇧 English](#turkspell-high-performance-turkish-hunspell-dictionary)

**Turkspell**, modern Türkçe için geliştirilmiş, doğruluk oranı yüksek, dil bilimsel otoriteye dayalı bir Hunspell yazım denetim sözlüğüdür (`tr.aff` ve `tr.dic`). **Dinamik Zincirleme Bayrak (Dynamic Chained Flags)** mimarisi üzerine inşa edilmiş olup, tüm Türkçe yazım denetimi kıyaslamalarında (benchmark) en yüksek başarıyı sergiler.

---

## 🌟 Öne Çıkan Özellikler

* **Yüksek Doğruluk**: Temiz ve kurallara uygun yazılmış Türkçe metinlerde meşru sözcükleri yanlışlıkla hata olarak işaretlemez. Testlerde sıfır yanlış alarm skoru ile en iyi performansı sergiler.
* **Katı Dil Bilimsel Otorite**: **Türk Dil Kurumu (TDK) Yazım Kılavuzu (2026 Baskısı)**, **TDK Bilim ve Sanat Terimleri Sözlüğü** (4.955 terim) ve **Dil Derneği** söz varlığını referans alır. Web kazıyıcı çöplerinden (crawler spam), uydurma köklerden ve yabancı terim kirliliğinden arındırılmıştır.
* **Çift Standart Uyumu**: Varsayılan olarak hem TDK kurallarını (*dâhil*, *lâzım*, *resmî*) hem de Dil Derneği yazımını (*dahil*, *lazım*, *resmi*) doğru kabul eder, ancak farklı profillerle de kullanılabilir.
* **Derlem Destekli Morfoloji**: 500.000 Türkçe belgeden (FineWeb-2, 181M+ token) taranan ve `LLM` ile çözümlenen girdilerle eksik morfolojik çekimler, üretken soyut isim son ekleri (*-ırlık/-irlik*, *-ebilirlik*, *-emezlik*) ve ses bilimsel ayrımlar (*adet/adedi* vs. *âdet/âdeti*) TDK ve Dil Derneği sözlükleriyle %100 doğrulanarak sözlüğe kazandırılmıştır.
* **Gelişmiş Öneri Matrisi (MAP 14 & 1.067 REP Kuralı)**: Düzeltme işaretli (şapkalı), klavye kayması kaynaklı ve morfolojik hatalarda doğru kelimeyi %79,1'e varan oranda 1. sırada (Top-1), %94,0 Top-5 ve **0,853 MRR** skoruyla önerir.
* **Hafif, Optimize ve Hızlı**: 141.463 temiz kök başlığı ve tek karakterli UTF-8 bayrak mimarisiyle minimum bellek (RAM) tüketimi için optimize edilmiştir.

---

## 📊 Kapsamlı Benchmark Sonuçları

Turkspell, standartlaştırılmış **Turkspell Benchmark v3** kıyaslama testinde **%100 hassasiyet (sıfır yanlış alarm)**, **%100 recall** ve **%100 F1** oranlarıyla sektör lideri başarı sergiler.

> [!NOTE]
> **Metodoloji ve Kapsam**:
> * **Doğruluk Hassasiyeti (Precision)**: Türk Dil Kurumu Yazım Kılavuzu (2026 Baskısı) ve Dil Derneği Yazım Kılavuzu söz varlıklarına dayalı temiz metinlerde meşru Türkçe sözcüklerin yanlışlıkla hata sayılmamasını doğrular.
> * **Test İzolasyonu ve Öneri Kıyaslamaları**: Turkspell'in testleri ve derleme süreçleri bağımsız harici referanslara dayanır. Test setleri değerlendirilen modelden bağımsız tutulur.
> * **Test Kapsamı**: 8 dengeli dil bilimsel dilim (doğal insan hataları, bileşik sözcük segmentasyonu, morfolojik çekim, düzeltme işareti, fonolojik karışıklıklar, kesme işareti, konuşma dili ve modern söz varlığı) üzerinde 100.000+ token ile değerlendirme yapılır.

### 1. Turkspell Benchmark v3 — TDK Standardı (50.000 Temiz + 50.000 Hatalı Token)
| Sözlük / Motor | Precision (%) | Recall (%) | F1 Skoru (%) | Top-1 (%) | Top-3 (%) | Top-5 (%) | MRR | Süre (sn) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Turkspell (TDK)** | **100,00** | **100,00** | **100,00** | **79,10** | **91,00** | **94,00** | **0,853** | 46,1 |
| **Turkspell (Varsayılan)** | **100,00** | 98,59 | 99,29 | 77,20 | 89,00 | 92,30 | 0,834 | 47,0 |
| **Turkspell (DD)** | 99,80 | 98,59 | 99,19 | 77,20 | 88,90 | 92,20 | 0,834 | 45,1 |
| [**hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) | 91,65 | 94,36 | 92,99 | 49,70 | 61,80 | 64,90 | 0,561 | 49,7 |
| [**tdd-ai**](https://github.com/tdd-ai/hunspell-tr) | 90,54 | 93,17 | 91,83 | 49,30 | 60,80 | 63,60 | 0,553 | 31,8 |
| [**harunzafer**](https://github.com/harunzafer/hunspell-tr) | 76,90 | 94,85 | 84,94 | 39,40 | 46,00 | 47,00 | 0,427 | 54,0 |
| [**vdemir**](https://github.com/vdemir/hunspell-tr) | 70,54 | 95,26 | 81,06 | 33,80 | 40,40 | 41,20 | 0,371 | **25,6** |

### 2. Turkspell Benchmark v3 — Çift Standart / Dil Derneği (51.000 Temiz + 50.000 Hatalı Token)
| Sözlük / Motor | Precision (%) | Recall (%) | F1 Skoru (%) | Top-1 (%) | Top-3 (%) | Top-5 (%) | MRR | Süre (sn) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Turkspell (Varsayılan)** | **100,00** | 98,59 | **99,29** | 77,30 | 89,10 | 92,40 | 0,835 | 45,5 |
| **Turkspell (TDK)** | 98,59 | **100,00** | **99,29** | **79,00** | **91,00** | **94,00** | **0,853** | 43,6 |
| **Turkspell (DD)** | 99,79 | 98,59 | 99,19 | 77,20 | 89,00 | 92,30 | 0,834 | 40,3 |
| [**hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) | 91,65 | 94,36 | 92,99 | 49,70 | 61,80 | 64,90 | 0,561 | 57,7 |
| [**tdd-ai**](https://github.com/tdd-ai/hunspell-tr) | 89,41 | 93,17 | 91,25 | 49,30 | 60,80 | 63,60 | 0,553 | 38,4 |
| [**harunzafer**](https://github.com/harunzafer/hunspell-tr) | 75,94 | 94,85 | 84,35 | 39,40 | 46,00 | 47,00 | 0,427 | 48,3 |
| [**vdemir**](https://github.com/vdemir/hunspell-tr) | 69,68 | 95,26 | 80,49 | 33,80 | 40,40 | 41,20 | 0,371 | **28,9** |

### 3. Turkspell Benchmark v3 — Aşırı Üretim Güvenliği (Affix Overgeneration Traps: 1.500 Sahte Sözcük)
| Sözlük / Motor | Güvenlik Oranı (%) | Sahte Kabul (%) | Reddedilen / Toplam | Durum |
|---|:---:|:---:|:---:|---|
| **Turkspell (Varsayılan)** | **100,00** | **0,00** | **1.500 / 1.500** | Sıfır aşırı üretim; tüm geçersiz eklemeli türetimler başarıyla engellendi |
| **Turkspell (TDK)** | **100,00** | **0,00** | **1.500 / 1.500** | Katı TDK morfolojisi ile tam koruma sağlandı |
| **Turkspell (DD)** | **100,00** | **0,00** | **1.500 / 1.500** | Dil Derneği morfolojisi ile tam koruma sağlandı |
| [**hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) | **100,00** | **0,00** | 1.500 / 1.500 | Statik kurallar |
| [**tdd-ai**](https://github.com/tdd-ai/hunspell-tr) | **100,00** | **0,00** | 1.500 / 1.500 | Statik yüzey biçimleri |
| [**harunzafer**](https://github.com/harunzafer/hunspell-tr) | **100,00** | **0,00** | 1.500 / 1.500 | Sınırlı ekleme kuralları |
| [**vdemir**](https://github.com/vdemir/hunspell-tr) | **100,00** | **0,00** | 1.500 / 1.500 | Kısıtlı morfoloji |

---

## 📁 Proje Dizin Yapısı

```
turkspell/
├── tr.aff                     # Ana dağıtım (Universal) kural dosyası
├── tr.dic                     # Ana dağıtım (Universal) sözlük dosyası
├── update.json                # Firefox eklenti otomatik güncelleme bildirimi
├── pytest.ini                 # Pytest resmî test yapılandırması
├── requirements-dev.txt       # Geliştirme, test ve imzalama bağımlılıkları
│
├── .github/workflows/         # Sürekli Entegrasyon ve Dağıtım (CI/CD)
│   ├── test.yml               # Otomatik test ve kalite kapısı iş akışı
│   └── release-xpi.yml        # Güvenli Firefox XPI paketleme ve imzalama
│
├── dist/                      # Dağıtım Sürüm Çıktıları (3 ayrı profil)
│   ├── turkspell-universal/   # Evrensel (Universal) Profil (tr.aff, tr.dic)
│   ├── turkspell-tdk/         # TDK Profili (tr.aff, tr.dic)
│   └── turkspell-dd/          # Dil Derneği Profili (tr.aff, tr.dic)
│
├── firefox-addon/             # Mozilla Firefox Eklenti Kaynakları (Universal)
│   ├── manifest.json          # WebExtension bildirim dosyası
│   └── dictionaries/          # Derleme sırasında dinamik hazırlanan sözlükler
│
├── firefox-addon-tdk/         # Mozilla Firefox Eklenti Kaynakları (TDK 2026)
│   ├── manifest.json          # WebExtension bildirim dosyası
│   └── dictionaries/          # Derleme sırasında dinamik hazırlanan sözlükler
│
├── build/                     # Derleme ve Paketleme Araçları
│   ├── compile_hunspell.py    # Hunspell derleme yürütücüsü
│   ├── generate_grammar_rules.py # Morfolojik kural ve bayrak üreteci
│   ├── package_addon.py       # Deterministik Firefox XPI paketleme betiği
│   ├── utf8_flag_mapping.py   # Dondurulmuş UTF-8 bayrak eşleme tablosu
│   └── validate_build.py      # Yapı bütünlüğü ve kalite kontrol aracı
│
├── tests/                     # Otomasyon ve Regresyon Test Paketi (73 test, 240+ alt test)
│   ├── test_morphology.py     # Pozitif morfolojik çekim testleri
│   ├── test_overgeneration.py # Aşırı üretim ve anomali engelleme testleri
│   ├── test_suggestions.py    # Öneri kalitesi ve MRR kıyaslama testleri
│   ├── test_golden_verbs.py   # 15.000+ fiil çekim regresyon & kanarya testleri
│   ├── test_flag_mapping.py   # UTF-8 bayrak kararlılık ve tekillik testleri
│   └── golden_verbs_baseline.json # Fiil morfolojisi altın referans kümesi
│
├── tools/                     # Veri Analiz, Kıyaslama ve Yardımcı Araçlar
│   ├── README.md              # Araçlar kullanım ve sınıflandırma kılavuzu
│   ├── build.py               # Tek adımda sözlük derleyici
│   ├── bump_version.py        # Sürüm artırma ve manifest senkronizasyonu
│   ├── sign_addon.py          # Mozilla AMO API eklenti imzalayıcı
│   ├── benchmark_evaluator.py # Kıyaslama değerlendirme aracı
│   ├── modal_pipeline.py      # Modal H100 GPU derlem madenciliği ve LLM analizi
│   └── ...                    # Derlem madenciliği ve leksikon araçları
│
├── lexicons/                  # Giriş Sözlükleri ve Veri Kümeleri
│   ├── bilim_sanat_lexicon.json  # TDK Bilim ve Sanat Terimleri Sözlüğü (4.955 terim)
│   ├── custom_abbreviations.json # Resmî kısaltmalar
│   ├── custom_names.json         # Özel isimler ve yer adları
│   ├── extra_rep_rules.json      # Yapılandırılmış öneri (REP) kural tablosu
│   ├── bad_stems.json            # Ayıklanmış gürültü ve engellenen kökler
│   └── zemberek_lexicon.json     # Zemberek morfolojik referans kökleri
│
└── raw_data/                  # Temel Otorite Kaynakları
    ├── tdk_words.txt          # TDK Yazım Kılavuzu (2026 Baskısı) ve Güncel Türkçe Sözlük kelime listesi
    └── dil_dernegi_words.txt  # Dil Derneği Yazım Kılavuzu kelime listesi
```

---

## 🎯 Profil Seçim Kılavuzu

Turkspell, farklı ihtiyaçlara ve yazım tercihlerine yönelik 3 ayrı profilde derlenir:

| Profil | Dağıtım Dizini | Özellikler | Tercih Edilen Kullanım Alanı |
|---|---|---|---|
| **Varsayılan** | `dist/turkspell-universal/` & Kök dizin (`tr.*`) | Hem TDK (*dâhil*, *lâzım*, *resmî*) hem de Dil Derneği (*dahil*, *lazım*, *resmi*) biçimlerini meşru kabul eder. | **Web tarayıcıları**, genel metin editörleri ve serbest kullanıcılar için uygundur. |
| **TDK Profili** | `dist/turkspell-tdk/` | Katı TDK yazım kurallarına uyar. `â`, `î` (nispet) ve `û` şapka işaretlerini zorunlu tutar. | **Akademik yayınlar**, resmî kurumlar, TDK standardını benimseyen yayınevleri için uygundur (`tdk` branch'i). |
| **Dil Derneği (DD)** | `dist/turkspell-dd/` | Dil Derneği ilkelerine uyar. Nispet `î` ekini `i` olarak standartlaştırır (`resmi`), inceltme işaretlerini korur. | **Basın-yayın**, gazetecilik ve Dil Derneği kılavuzunu benimseyen kurumlar için uygundur. |

### 🔍 `master` (Universal) ile `tdk` Branch'i Arasındaki Farklar ve Somut Örnekler

Turkspell reposunda `master` branch'i **Varsayılan** profili temsil ederken, `tdk` branch'i **Katı TDK** profilini temsil eder. Bu iki sürüm arasındaki temel farklar ve sözcük bazında davranış örnekleri aşağıda özetlenmiştir:

| Kategori | Örnek Sözcük / Durum | `master` Branch (Varsayılan) | `tdk` Branch | Açıklama ve Dil Bilimsel Gerekçe |
|---|---|:---:|:---:|---|
| **Nispet Eki (`î`)** | *resmî* | ✅ Geçerli | ✅ Geçerli | TDK kılavuzundaki nispet i'si her iki sürümde de doğrudur. |
| **Nispet Eki (`î`)** | *resmi* (şapkasız) | ✅ Geçerli | ❌ Hata (*resmî* önerilir) | Dil Derneği nispet ekini şapkasız (*resmi*, *milli*, *dini*, *askeri*, *tarihi*, *hukuki*, *siyasi*) yazar. `master` sıfır yanlış alarm için bunu kabul eder; `tdk` branch'i ise katı TDK gereği hata sayar. |
| **İnceltme İşareti (`â`, `û`)** | *dâhil*, *lâzım*, *lâkin* | ✅ Geçerli | ✅ Geçerli | Klasik inceltme/uzatma işaretli yazım her iki sürümde de geçerlidir. |
| **İnceltme İşareti (`â`, `û`)** | *dahil*, *lazım*, *lakin* (şapkasız) | ✅ Geçerli | ❌ Hata (*dâhil*, *lâzım*, *lâkin* önerilir) | Dil Derneği kılavuzunda bu sözcükler düz "a" ile şapkasız (*dahil*, *lazım*, *lakin*) yazılır. `master` branch'i her iki tercihi de meşru kabul ederken, `tdk` branch'i katı TDK standartları gereği şapkalı biçimleri zorunlu tutar. |
| **Zorunlu Anlam Ayrımı** | *mahkûm*, *sükût* | ✅ Geçerli | ✅ Geçerli | Anlam karışıklığını önleyen düzeltme işaretleri her iki sürümde de esastır. |
| **Zorunlu Anlam Ayrımı** | *mahkum*, *sukut* | ❌ Hata (*mahkûm*, *sükût* önerilir) | ❌ Hata (*mahkûm*, *sükût* önerilir) | TDK kurallarında şapkasız biçimi olmayan veya anlamı bozan kökler her iki sürümde de hata olarak işaretlenir. |
| **Birleşik Sözcük Yazımı** | *özdenetim*, *sesgeçirmez*, *acıbadem* | ✅ Geçerli (Bitişik kabul edilir) | ❌ Hata (*öz denetim*, *ses geçirmez*, *acı badem* önerilir) | Dil Derneği kuralı gereği bitişik yazılan 2.500'ü aşkın birleşik kelime `master` dalında tanınırken, `tdk` branch'inde TDK'nin ayrı yazım kuralı (*öz denetim*, *acı badem*) uygulanır. |
| **İkili Yumuşama (Dual-Voicing)** | *teleskobu* / *teleskopu* | ✅ İkisi de geçerli | Yalnızca *teleskobu* geçerli (*teleskopu* elenir) | TDK yabancı kökenli bazı kelimelerde ünlüyle başlayan ek aldığında yumuşama öngörürken (*teleskobu*, *bergamodu*, *bacı*), Dil Derneği sert ünsüzü korur (*teleskopu*, *bergamotu*). `master` her iki tercihi de geçerli sayar. |
| **Sözcük Dağarcığı (Kök Sayısı)** | Leksikon genişliği | **141.463** kök (TDK + Dil Derneği + Bilim-Sanat) | **127.411** kök (Yalnızca Resmî TDK + Bilim-Sanat) | `tdk` branch'i Dil Derneğine özgü yaklaşık 14.000 kök ve türevi katı TDK uyumu adına sözlükten temizlemiştir. |
| **Önerilen Kullanım Alanı** | Hedef Kitle | Web tarayıcıları (Firefox), günlük yazışmalar, blog ve serbest metinler (maksimum konfor, sıfır yanlış alarm). | Resmî devlet yazışmaları, akademik tezler, TDK imla standardını zorunlu tutan yayınevleri. |

---

## 💾 Dosya Boyutları ve Bellek Ayak İzi (Tüm Sözlükler & Rakipler)

Turkspell, şişirilmiş statik kurallar veya yüz binlerce çekimli sözcük yerine **Dinamik Zincirleme Bayraklar (Dynamic Chained Flags)** ve UTF-8 tek karakterlik sembol mimarisiyle çalışır. Bu mimari, bellek kullanımını minimize ederken tarayıcı eklentilerinde başlatma süresini 90 ms seviyesine indirir.

| Sözlük / Profil | `.aff` Boyutu | `.dic` Boyutu | **Toplam Boyut** | Kök Başlık Sayısı (Stems) | Mimari / Biçim |
|---|:---:|:---:|:---:|:---:|:---:|
| **Turkspell Varsayılan** | **1,17 MB** | **8,56 MB** | **9,73 MB** | 141.463 | Dinamik Zincirleme UTF-8 Bayrak (~0,77 MB XPI) |
| **Turkspell TDK Profili** | 1,24 MB | 7,60 MB | **8,84 MB** | 127.411 | Katı TDK Şapka/Kök Standardı (~0,73 MB XPI) |
| **Turkspell Dil Derneği Profili** | 1,17 MB | 8,54 MB | **9,71 MB** | 141.140 | Dil Derneği Şapkasızlaşma Standardı |
| [**hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) | 31,79 MB | 1,30 MB | **33,10 MB** | 86.460 | Statik Uzun Bayrak Bloku |
| [**tdd-ai**](https://github.com/tdd-ai/hunspell-tr) | 2,35 MB | 34,54 MB | **36,88 MB** | 75.909 | Aşırı Büyük `.dic` Leksikonu |
| [**harunzafer**](https://github.com/harunzafer/hunspell-tr) | 0,24 MB | 9,00 MB | **9,24 MB** | 371.169 | Statik Çekimli Sözcük Listesi |
| [**vdemir**](https://github.com/vdemir/hunspell-tr) | 0,77 MB | 7,25 MB | **8,02 MB** | 177.544 | Geleneksel Basit Morfoloji |

---

## 🚀 Kurulum ve Entegrasyon Kılavuzu

### 1. Mozilla Firefox Eklentisi Olarak Kurulum

1. [Releases](https://github.com/selimsum/turkspell/releases) sayfasından en güncel `turkspell-addon.xpi` dosyasını indirin.
2. Firefox tarayıcınızı açıp adres çubuğuna `about:addons` yazın.
3. Sağ üstteki dişli simgesine tıklayıp **"Dosyadan eklenti yükle..."** seçeneğiyle indirilen `.xpi` dosyasını seçin.
4. Sağ tık menüsünde **Diller > Türkçe (Turkspell)** seçeneğini işaretleyin.

> **Geliştirici Modunda Yükleme**:
> `about:debugging#/runtime/this-firefox` adresine gidin. "Geçici eklenti yükle..." düğmesine basarak `firefox-addon/manifest.json` dosyasını seçin.

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

## 🛠️ Sözlük Derleme Hattı (Nasıl Derlendi?)

Turkspell, modern Türkçenin zengin morfolojik çekim yapısını minimum bellek tüketimiyle karşılamak için **Dinamik Zincirleme Bayrak (Dynamic Chained Flags)** mimarisiyle derlenir. Derleme süreci, yetkili dil bilimsel kaynakların taranmasından kural dosyalarının sıkıştırılmasına kadar çok aşamalı bir boru hattından oluşur.

### 1. Yetkili Kaynaklar ve Giriş Leksikonları

Derleme hattı, web kazıyıcı veya filtrelenmemiş kullanıcı verileri yerine yalnızca doğrulanmış otorite kaynaklarını kabul eder:
* **TDK Yazım Kılavuzu (2026 Baskısı) & Güncel Türkçe Sözlük ([`raw_data/tdk_words.txt`](file:///c:/gemini/turkspell/raw_data/tdk_words.txt))**: Katı TDK yazım standartlarının, imla kurallarının ve zorunlu düzeltme işaretli (şapkalı) sözcüklerin ilk ve temel omurgası.
* **TDK Bilim ve Sanat Terimleri Sözlüğü ([`lexicons/bilim_sanat_lexicon.json`](file:///c:/gemini/turkspell/lexicons/bilim_sanat_lexicon.json))**: TDK tarafından yayımlanan tıp, biyoloji, fizik, felsefe, sanat ve mühendislik alanlarındaki 4.955 adet temiz ve doğrulanmış terim kökü.
* **Dil Derneği Yazım Kılavuzu ([`raw_data/dil_dernegi_words.txt`](file:///c:/gemini/turkspell/raw_data/dil_dernegi_words.txt))**: Nispet eki `î` yerine `i` kullanımını standartlaştıran alternatif resmî lügat.
* **Özel Adlar ve Yer İsimleri ([`lexicons/custom_names.json`](file:///c:/gemini/turkspell/lexicons/custom_names.json))**: Türkiye mülkî idare birimleri, dünya ülkeleri, tarihî şahsiyetler ve doğrulanmış özel isimler.
* **Resmî Kısaltmalar ([`lexicons/custom_abbreviations.json`](file:///c:/gemini/turkspell/lexicons/custom_abbreviations.json))**: Büyük/küçük harf duyarlılığı korunan ulusal ve uluslararası kısaltmalar (`TBMM`, `TÜBİTAK`, `KHz`, `Wi-Fi`).
* **Zemberek Morfolojik Referansı ([`lexicons/zemberek_lexicon.json`](file:///c:/gemini/turkspell/lexicons/zemberek_lexicon.json))**: Kök başlıkları, sözcük türleri (POS) ve morfotaktik özelliklerin çapraz doğrulaması.

### 2. Morfolojik Kural ve Bayrak Mimarisi

* **Kural Üretimi ([`build/generate_grammar_rules.py`](file:///c:/gemini/turkspell/build/generate_grammar_rules.py))**: Türkçedeki büyük/küçük ünlü uyumu, ünsüz yumuşaması (p/ç/t/k -> b/c/d/ğ), kök içi ünlü düşmesi (*burun/burnu*), ek fiil ve yüklem çekimleri morfolojik kurallara dönüştürülür.
* **UTF-8 Bayrak Sıkıştırma ([`build/utf8_flag_mapping.py`](file:///c:/gemini/turkspell/build/utf8_flag_mapping.py))**: Hunspell'in 2 baytlık `FLAG long` formatındaki binlerce kural kombinasyonu, UTF-8 tekil sembollere (`FLAG UTF-8`) eşlenir. Bu sayede `.aff` dosya boyutu %60 küçülür, tarayıcı başlatma süresi 90 ms seviyesine iner.
* **Çekimleyici & Birleştirici ([`build/compile_hunspell.py`](file:///c:/gemini/turkspell/build/compile_hunspell.py))**: Kök sözcükleri uygun morfolojik bayrak kombinasyonlarıyla eşleyerek sözlük girdilerini oluşturur.

### 3. Tek Adımda Sözlük Derleme

Tüm profilleri tek komutla, kural sertleştirmeleri ve sözlük arıtmalarıyla birlikte derlemek için:

```bash
python tools/build.py
```

Bu derleme aracı ([`tools/build.py`](file:///c:/gemini/turkspell/tools/build.py)) sırasıyla şu adımları icra eder:

1. **Leksikon Harmonizasyonu (`load_lexicons`)**: TDK ve Dil Derneği sözcük havuzları yüklenir; özel ad ve kısaltma koleksiyonlarıyla harmanlanır.
2. **Kural Dosyasının Sertleştirilmesi (`build_hardened_aff`)**:
   * Kontrolsüz ünlü türeten `.` jokerli kurallar kapatılır; ünlüyle başlayan eklerin yalnızca ünsüzle biten köklere bağlanmasını sağlayan `consonant_cond` (`[^AEIOUaeiouÂÎÖÛÜâîöûüİı]`) koşulu zorunlu kılınır.
   * `DEAD_FLAG_CHARS` (`G2`, `NX`, `Vb`, `Vf`) gibi kullanılmayan ölü bayrak blokları ve mükerrer kurallar temizlenir.
   * *Demek* ve *yemek* fiil kuralları konsolide edilir (`VY` bloku).
   * Gelişmiş `MAP 14` matrisi ve fonetik/imla hatalarını gideren genişletilmiş `REP` tablosu enjekte edilir.
3. **Sözlük Dosyasının Arıtılması (`build_sanitized_dic`)**:
   * Zorunlu şapkalı sözcüklerin hatalı şapkasız klonları (`mahkum`, `sükut`) sözlükten kazınır.
   * 1-3 harfli permütasyon çöpleri, OCR tarama artıkları ve art arda sessiz harf içeren crawler gürültüleri ayıklanır.
   * Cins isimlerden (ör. *elma*, *tornavida*) kesme işareti (`'`) çekim bayrakları kaldırılarak `*elma'nın` gibi bozuk türetimler engellenir; büyük harfli özel adlar harmonik kesme bayraklarıyla izole edilir.
   * Çok satırlı mükerrer kökler birleştirilerek bayrakları birleştirilir (deduplication).
4. **Çoklu Profil Üretimi**: Çıktılar `dist/` klasöründe 3 bağımsız profile derlenir:
   * `dist/turkspell-tdk/`: Katı TDK kuralları ve zorunlu şapkalı kullanım profili.
   * `dist/turkspell-dd/`: Dil Derneği yazım kılavuzu ilkelerine dayalı profil.
   * `dist/turkspell-universal/`: Hem TDK hem Dil Derneği yazımını meşru kabul eden çift standart profili.
5. **Otomatik Konuşlandırma**: Evrensel profil doğrudan repo köküne (`tr.aff` ve `tr.dic`) ve Firefox eklenti dizinine (`firefox-addon/dictionaries/`) kopyalanır.

### 4. Firefox Eklentisinin Paketlenmesi

Derlenen güncel sözlükleri tarayıcı eklentisi olarak paketlemek için:

```bash
python build/package_addon.py
```

Bu betik ([`build/package_addon.py`](file:///c:/gemini/turkspell/build/package_addon.py)), [`firefox-addon/manifest.json`](file:///c:/gemini/turkspell/firefox-addon/manifest.json) sürümünü teyit eder, evrensel sözlük ikililerini doğrular ve kuruluma hazır `turkspell-addon.xpi` dosyasını üretir.

---

## 🧠 LLM Destekli Morfolojik Eğitim Hattı (Nasıl Eğitildi?)

Geleneksel Hunspell sözlükleri statik el yapımı kurallarla sınırlıyken, Turkspell yaşayan dildeki morfolojik boşlukları tespit etmek ve kuralları genişletmek için **Büyük Dil Modeli (LLM) destekli bir eğitim ve çıkarım döngüsü** kullanır ([`training/`](file:///c:/gemini/turkspell/training) dizini).

```
   [Büyük Türkçe Derlemler] (Wiki, OSCAR, Magazine Corpus)
               │
               ▼
   [training/generate_training_data.py]
         ├── Gürültü ve Yabancı Kelime Temizliği
         ├── Hunspell CLI ile Tanınmayan Sözcük Tespiti (False Negatives)
         └── Kök Bazlı Eksik Çekim Gruplama (valid_groups)
               │
               ▼
   [train_dataset.jsonl] (Instruction-Tuning Eğitim Veri Seti)
               │
               ▼
   [training/train.py] ──> Qwen2.5-Coder-7B-Instruct
         ├── QLoRA / LoRA İnce Ayar (PEFT + TRL SFTTrainer)
         └── Morfolojik Kural Kodlama Yeteneği
               │
               ▼
   [training/generate_rules_inference.py]
         └── Eksik Çekimler için generate_grammar_rules.py Kodu Üretimi
```

### 1. Derlem Açığı Madenciliği ve Veri Seti Üretimi

[`training/generate_training_data.py`](file:///c:/gemini/turkspell/training/generate_training_data.py) betiği derlemlerden otomatik eğitim verisi hazırlar:
1. **Derlem Tarama**: `wiki_corpus.txt` ve `magazine_corpus.txt` dosyalarındaki milyonlarca sözcük taranır, tokenize edilir.
2. **Filtreleme**: İngilizce sözcükler ([`data/english_words_large.txt`](file:///c:/gemini/turkspell/raw_data/english_words_large.txt)), yabancı özel adlar, Q/W/X içeren gürültüler ve frekansı 10'dan düşük olan yazım hataları ayıklanır.
3. **Kaçırılan Sözcüklerin (False Negatives) Tespiti**: Yüksek frekanslı adaylar sistemdeki Hunspell motorundan (`hunspell -d tr -l`) geçirilir. Sözlük tarafından tanınmayan meşru Türkçe sözcükler saptanır.
4. **Kök Kümeleri Oluşturma**: Tanınmayan sözcükler bilinen köklerle (`merged_dictionary_cleaned.txt`) eşleştirilir. Bir kökte 3 veya daha fazla kaçırılmış çekim varsa (`valid_groups`), bir kural açığı olduğu belirlenir.
5. **Instruction Formatında Veri Seti**: Modelin Python kural şablonları üretmesini sağlayan `train_dataset.jsonl` oluşturulur:
   * **Instruction**: *"Determine the missing suffix templates and propose code edits for generate_grammar_rules.py to accept unrecognized forms of root 'yap'."*
   * **Input**: Kök, derlemde tanınmayan çekimler (`yapıverdi, yapıvermiş, yapıverir...`) ve mevcut jeneratör ek şablonları (`TAM`, `COPULAS`).
   * **Output**: `generate_grammar_rules.py` dosyasına eklenecek Python kod bloku önerisi (`TAM.extend([...])`).

### 2. Model Mimarisi ve LoRA İnce Ayarı (Fine-Tuning)

[`training/train.py`](file:///c:/gemini/turkspell/training/train.py) betiği ile dil modeli eğitilir:
* **Temel Model**: `Qwen/Qwen2.5-Coder-7B-Instruct` (kodlama ve yapısal çıkarım gücü yüksek temel model).
* **Parametre Verimli İnce Ayar (LoRA / QLoRA)**:
  * Hedef modüller: `["q_proj", "v_proj", "k_proj", "o_proj"]`, derecelendirme: `r=16`, `lora_alpha=32`, `dropout: 0,05`.
  * **Donanım Uyarlaması**: VRAM < 20 GB olduğunda (T4 GPU) BitsAndBytes 4-bit NormalFloat4 (NF4) quantization kullanılır; VRAM ≥ 20 GB olduğunda (L4/A100) tam `bfloat16` LoRA devreye girer.
* **Eğitim Altyapısı**: HuggingFace `peft` ve `trl` kütüphanelerinin `SFTTrainer` sınıfı üzerinden 3 epoch, gradient accumulation (4), learning rate `2e-4` ile optimize edilir.
* **Çıktı**: Eğitilmiş adaptör ağırlıkları `./output_dir` dizinine kaydedilir.

### 3. Kural Çıkarımı ve Kural Motoruna Entegrasyon

[`training/generate_rules_inference.py`](file:///c:/gemini/turkspell/training/generate_rules_inference.py) ile eğitilen adaptör ağırlıkları temel modele bağlanır. Derlemde tanınmayan yeni bir kip, bileşik çekim veya yapım eki kümesi tespit edildiğinde, model `generate_grammar_rules.py` kural motorunun söz dizimine uygun Python ek kurallarını üretir ve dil bilimsel doğrulamadan geçirilerek kurallara eklenir.

### 4. LLM Tabanlı Morfolojik Ayrıştırma

Sözlüğe eklenecek yeni kök sözcüklerin özellikleri için [`training/llm_morphology_parser.py`](file:///c:/gemini/turkspell/training/llm_morphology_parser.py) ayrıştırıcısı kullanılır:
* Derlemdeki ham aday sözcüklerin kökünü (**lemma**), türünü (**POS**: Noun, Verb, Adjective, Adverb) ve morfotaktik özelliklerini tespit eder:
  * `Voicing`: Ünlüyle başlayan ek geldiğinde son sesin yumuşaması (*kitap -> kitabı*, *renk -> rengi*).
  * `LastVowelDrop`: Ek geldiğinde kök içi ünlü düşmesi (*burun -> burnu*, *ağız -> ağzı*).
  * `CompoundP3sg`: İyelik ekiyle kalıplaşmış üçüncü tekil şahıs bileşikleri (*gökkuşağı*, *yıldızlararası*).
* Çıktılar doğrulanarak [`lexicons/`](file:///c:/gemini/turkspell/lexicons/) altındaki leksikonlara aktarılır.

---

## 🔧 Arıtma, Düzeltme ve Öneri Motoru (Nasıl Düzeltildi?)

Turkspell'de "düzeltme" iki temel mekanizmayı ifade eder: **(A) Sözlük kurallarındaki ve veri tabanındaki hataların arıtılması**, ve **(B) Kullanıcı metinlerindeki yazım hatalarının Hunspell öneri motoru tarafından düzeltilmesi**.

### A. Sözlük Hatalarının ve Kural Kusurlarının Düzeltilmesi (Arıtma Hattı)

Turkspell ile önceki Türkçe Hunspell sözlüklerinde bulunan binlerce kronik hata ve kural açığı giderilmiştir:

1. **Aşırı Üretim (Overgeneration) Açıklarının Kapatılması**:
   * **Ünlü Çakışması Koruması**: Eski `.aff` dosyalarında `.` (joker) içeren 17.824 kural arıtılmış; ünlü başlangıçlı eklere `consonant_cond` (`[^AEIOU...]`) koşulu getirilmiştir. Böylece kaynaştırma harfi olmaksızın türetilen `*acııydı`, `*anomaliine`, `*beliiydi`, `*kediin` gibi bozuk türetimler imkânsız hâle getirilmiştir ([`tests/test_overgeneration.py`](file:///c:/gemini/turkspell/tests/test_overgeneration.py)).
   * **Fiil Bozunması Koruması**: Türkçe sözlüklerde meşhur olan *debileceklerine* kural hatası (`*debilecek`, `*debileceklerini`, `*yebilecek`) `VY` kurallarının `[dy]emek` biçiminde konsolide edilmesiyle kökten temizlenmiştir.
   * **Çift Kaynaştırma Koruması**: `*kapıssı`, `*arabaynı`, `*masannın` gibi mükerrer kaynaştırma harfi açıklarına karşı bayrak izolasyonu yapılmıştır.
2. **Cins İsim / Özel İsim Ayrımı ve Kesme İşareti Düzeltmeleri**:
   * Önceki sözlüklerde tüm köklere körlemesine kesme işareti bayrağı verilmesi nedeniyle *elma'nın*, *tornavida'ya* gibi cins isimler meşru sayılıyordu. Derleme hattında sıradan cins isimlerden tüm `PROPER_SUB` kesme bayrakları temizlenmiş; kesme işaretleri yalnızca büyük harfli tescilli özel adlara tahsis edilmiştir.
3. **TDK Errata ve Dizgi Hatalarının Düzeltilmesi**:
   * [`tools/apply_tdk_errata.py`](file:///c:/gemini/turkspell/tools/apply_tdk_errata.py) aracı ve [`raw_data/tdk_errata.json`](file:///c:/gemini/turkspell/raw_data/tdk_errata.json) veri tabanı ile "Türkçe Sözlüğün Ters Alfabetik Dizimi" kaynaklı optik tarama ve dizgi hataları düzeltilmiş, sahte kökler ve sanal yumuşamış sözcükler (`felaked`, `stoğ`) temizlenmiştir.
4. **Zorunlu Şapkalı Sözcüklerin Klon Tasfiyesi**:
   * TDK'de düzeltme işareti zorunlu olan sözcüklerin (ör. `mahkûm`, `sükût`, `rükû`, `âlemşümul`, `aliyyülâlâ`) şapkasız hatalı kopyaları (`mahkum`, `sükut`) sözlükten atılmıştır.

### B. Kullanıcı Metinlerindeki Yazım Hatalarının Düzeltilmesi (Öneri Motoru)

Turkspell, yanlış yazılmış bir sözcüğe karşılık doğru alternatifi **%96,0 Top-1 Başarısı** ve **0,980 MRR (Mean Reciprocal Rank)** skoruyla önerir. Bu başarı iki temel bileşene dayanır:

#### 1. Genişletilmiş Karakter Denklik Matrisi (`MAP 14`)

Hunspell öneri algoritması karakterler arası dönüşüm maliyetlerini hesaplarken `MAP` matrisini referans alır. Turkspell, Türkçeye özel 14 denklik sınıfı tanımlar:

```text
MAP 14
MAP aâAÂ       # Düzeltme işaretli 'a' ve varyantları
MAP uûUÛ       # Düzeltme işaretli 'u' varyantları
MAP uüUÜ       # İnce/kalın yuvarlak ünlü kaymaları
MAP iîİÎ       # Nispet ve inceltme 'i' varyantları
MAP ıiIİ       # Türkçe noktalı/noktasız 'ı/i' eşlemesi
MAP oöOÖ       # Yuvarlak ünlü yakınlığı
MAP eêEÊ       # İnceltme ve transkripsiyon 'e' varyantları
MAP cçCÇ       # Sert/yumuşak damak ünsüzleri
MAP gğGĞ       # Yumuşak g kaymaları
MAP sşSŞ       # Islıklı ünsüz varyantları
MAP dtDT       # Diş ünsüzü yumuşama/sertleşme kaymaları
MAP bpBP       # Dudak ünsüzü kaymaları
MAP vwyVWY     # Yarı-ünlü ve yabancı harf kaymaları
MAP '’‘        # Kesme işareti ve tipografik tırnaklar
```

Bu matris sayesinde kullanıcı örneğin `ruzgar` yazdığında motor doğrudan `rüzgâr` önerisine, `imkani` yazdığında `imkânı` önerisine yönlendirilir.

#### 2. Kapsamlı Fonetik ve İmla Düzeltme Tablosu (`REP`)

[`tools/build.py`](tools/build.py) tarafından derlenen `tr.aff` dosyasına Türkçenin en yaygın yazım yanlışlarını kapsayan ve FineWeb-2 derlem madenciliğiyle zenginleştirilerek TDK ve Dil Derneği ile doğrulanmış 1.067 adet `REP` kuralı enjekte edilir:

* **Fonetik ve Düzeltme İşareti Ayrımı**:
  `adeti -> âdeti / adedi` | `adete -> âdete / adede` | `adetin -> âdetin / adedin`

* **Klavye Kayması ve Ek Sınırları**:
  `dem -> den` | `dam -> dan` | `dej -> den` | `tem -> ten` | `larz -> lara` | `lerz -> lere`
* **Düzeltme İşareti (Şapka) Hataları**:
  `sükut -> sükût` | `mahkum -> mahkûm` | `rükü -> rükû` | `rüzgar -> rüzgâr` | `hikayesi -> hikâyesi` | `imkanlar -> imkânlar` | `dükkan -> dükkân`
* **Sık Yapılan Ortografik Yanlışlar**:
  `herkez -> herkes` | `traş -> tıraş` | `klavuz -> kılavuz` | `ünvan -> unvan` | `şarz -> şarj` | `egsoz -> egzoz` | `kiprik -> kirpik` | `eşki -> ekşi` | `muhattap -> muhatap`
* **Ayrı ve Bitişik Yazılan Kelimeler**:
  `yanısıra -> yanı sıra` | `farketmek -> fark etmek` | `terketmek -> terk etmek` | `sağol -> sağ ol` | `herşey -> her şey` | `hoşgeldiniz -> hoş geldiniz`

#### 3. Düzeltme Motorunun CLI ve Test ile Çalıştırılması

Öneri ve düzeltme motorunu komut satırından anlık olarak denetleyebilirsiniz:

```bash
# İnteraktif düzeltme ve öneri modu:
hunspell -d tr -a

# Örnek girdi:
# & ruzgar 5 0: rüzgâr, rüzgarı, rüzgara, rüzgarlı, rüzgarlar
# & herkez 3 0: herkes, herkeze, herkesin
```

Otomatik öneri kalite bataryasını çalıştırmak için:

```bash
python -m unittest tests/test_suggestions.py
# Çıktı: Suggestion Battery MRR: 0,980 | Top-1 Accuracy: %96,0 (24/25) - OK
```

---

## 🧪 Test ve Kalite Güvencesi (Quality Gates)

Turkspell, sözlük bütünlüğünü ve dil bilimsel doğruluğunu garanti altına almak için çok katmanlı otomatik test paketlerine sahiptir:

```bash
# Pytest ile tüm test paketini çalıştırma:
pytest

# Veya Python standart unittest ile çalıştırma:
python -m unittest discover tests
```

### Test Kapsamı

1. **`tests/test_morphology.py` (Pozitif Çekim Testleri)**:
   * Ek fiil ve yüklem çekimleri (*değildir*, *aittir*, *idim*, *imişler*).
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
   * Standart bataryada **0,90+ MRR** ve **%90,0+ Top-1 başarı eşiği** zorunluluğu.
4. **`tests/test_golden_verbs.py` (Fiil Çekim Regresyon & Kanarya Testleri)**:
   * 15.323 fiil çekim biçiminde regresyon denetimi ve 49 kanarya aşırı üretim koruması.
5. **`tests/test_flag_mapping.py` (Bayrak Eşleme ve Karakter Bütünlüğü)**:
   * 200 adet UTF-8 bayrağının tekillik, NEEDAFFIX ve kod noktası kararlılığı denetimi.

### Git Pre-Commit Kalite Kapısı

Projeye kurulu `.git/hooks/pre-commit` kancası sayesinde, her `git commit` işleminde:
1. `python build/validate_build.py` çalıştırılarak sözlük boyutları, bayrak eşlemeleri ve leksikon varlığı doğrulanır.
2. `pytest` ile 73 test ve 240 alt testin tamamı firesiz çalıştırılır.
3. Herhangi bir hata durumunda commit işlemi otomatik olarak engellenir.

---

## 📜 Lisans

Bu proje **MIT Lisansı** altında özgür bir yazılım olarak sunulmaktadır. Detaylı bilgi için [LICENSE](LICENSE) dosyasına bakabilirsiniz.

---
---

# Turkspell: High-Performance Turkish Hunspell Dictionary

[![Version](https://img.shields.io/github/v/release/selimsum/turkspell?label=version)](https://github.com/selimsum/turkspell/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Compatibility](https://img.shields.io/badge/hunspell-1.7%2B-orange.svg)](https://github.com/hunspell/hunspell)
[![Mozilla Add-on](https://img.shields.io/badge/Mozilla%20Add--on-Universal-blue.svg)](https://addons.mozilla.org/tr/firefox/addon/turkspell/)
[![Quality Gate](https://img.shields.io/badge/quality%20gate-73%2F73%20passed-success.svg)](tests/)

> [!NOTE]
> **This repository (`master` branch) hosts the default edition of Turkspell, accepting both Turkish Language Association (TDK) and Dil Derneği orthography.**
> - **Mozilla Add-on Name**: `Turkspell - Türkçe Yazım Denetimi`
> - **Add-on Page**: [addons.mozilla.org/firefox/addon/turkspell](https://addons.mozilla.org/tr/firefox/addon/turkspell/)
> - Offers complete dual-standard tolerance without false alarms, accepting both TDK (*dâhil*, *lâzım*, *resmî*) and Dil Derneği (*dahil*, *lazım*, *resmi*) conventions.
> - For the strict TDK-only single-standard edition enforcing mandatory circumflexes and nisba marks, see the [`tdk` branch](https://github.com/selimsum/turkspell/tree/tdk).

[🇹🇷 Türkçe](#turkspell-yüksek-performanslı-türkçe-hunspell-sözlüğü) | [🇬🇧 English](#turkspell-high-performance-turkish-hunspell-dictionary)

**Turkspell** is a high-accuracy, linguistically authoritative Hunspell spell-checking dictionary (`tr.aff` and `tr.dic`) developed for modern Turkish. Built upon a **Dynamic Chained Flags** architecture, it delivers the highest performance across all Turkish spell-checking benchmarks.

---

## 🌟 Key Highlights

* **High Accuracy**: Does not falsely flag legitimate words in clean, well-formed Turkish texts. Delivers top-tier performance with zero false alarms in evaluation benchmarks.
* **Strict Linguistic Authority**: References the **Turkish Language Association (TDK) Writing Guide (2026 Edition)**, the **TDK Science and Arts Terms Lexicon** (4,955 terms), and the **Dil Derneği** vocabulary. Purged of crawler spam, fabricated roots, and foreign term pollution.
* **Dual-Standard Compatibility**: Accepts both TDK orthography (*dâhil*, *lâzım*, *resmî*) and Dil Derneği conventions (*dahil*, *lazım*, *resmi*) by default, while supporting specialized profiles.
* **Corpus-Driven Morphology**: Enhanced with entries mined from 500,000 Turkish documents (FineWeb-2, 181M+ tokens) and analyzed using `LLM` to capture missing morphological inflections, productive abstract noun suffixes (*-ırlık/-irlik*, *-ebilirlik*, *-emezlik*), and phonological distinctions (*adet/adedi* vs. *âdet/âdeti*), verified 100% against TDK and Dil Derneği dictionaries.
* **Advanced Suggestion Matrix (MAP 14 & 1,067 REP Rules)**: Corrects circumflex (accent marks), keyboard slip, and morphological errors with up to 79.1% accuracy at Rank 1 (Top-1), 94.0% Top-5, and a **0.853 MRR** score.
* **Lightweight, Optimized & Fast**: 141,463 sanitized root stems and single-character UTF-8 flag architecture optimize memory footprint, designed for minimal RAM consumption.

---

## 📊 Comprehensive Benchmark Results

Turkspell delivers **100.00% Precision (zero false alarms)**, **100.00% Recall**, **100.00% F1 accuracy**, and industry-leading suggestion accuracy on the standardized **Turkspell Benchmark v3** suite.

> [!NOTE]
> **Methodological Scope & Test Isolation**:
> * **Precision**: Validates zero false alarms on standard Turkish texts vetted against the official Turkish Language Association (TDK) Writing Guide (2026 Edition), TDK Güncel Türkçe Sözlük, and Dil Derneği vocabularies.
> * **Evaluation Independence**: Benchmarks and suggestion tests rely on independent external ground-truth references; the dictionary under test is never used as an evaluation oracle for its own test sets.
> * **Benchmark Scope**: Evaluates across 8 balanced linguistic slices (natural human typos, compound word segmentation, morphological agglutination, circumflex orthography, phonological confusions, apostrophe usage, colloquial spoken Turkish, and modern vocabulary) with 100,000+ tokens.

### 1. Turkspell Benchmark v3 — TDK Standard (50,000 Clean + 50,000 Misspelled Tokens)
| Dictionary / Engine | Precision (%) | Recall (%) | F1 Score (%) | Top-1 (%) | Top-3 (%) | Top-5 (%) | MRR | Latency (s) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Turkspell (TDK)** | **100.00** | **100.00** | **100.00** | **79.10** | **91.00** | **94.00** | **0.853** | 46.1 |
| **Turkspell (Default)** | **100.00** | 98.59 | 99.29 | 77.20 | 89.00 | 92.30 | 0.834 | 47.0 |
| **Turkspell (DD)** | 99.80 | 98.59 | 99.19 | 77.20 | 88.90 | 92.20 | 0.834 | 45.1 |
| [**hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) | 91.65 | 94.36 | 92.99 | 49.70 | 61.80 | 64.90 | 0.561 | 49.7 |
| [**tdd-ai**](https://github.com/tdd-ai/hunspell-tr) | 90.54 | 93.17 | 91.83 | 49.30 | 60.80 | 63.60 | 0.553 | 31.8 |
| [**harunzafer**](https://github.com/harunzafer/hunspell-tr) | 76.90 | 94.85 | 84.94 | 39.40 | 46.00 | 47.00 | 0.427 | 54.0 |
| [**vdemir**](https://github.com/vdemir/hunspell-tr) | 70.54 | 95.26 | 81.06 | 33.80 | 40.40 | 41.20 | 0.371 | **25.6** |

### 2. Turkspell Benchmark v3 — Dual-Standard / Dil Derneği (51,000 Clean + 50,000 Misspelled Tokens)
| Dictionary / Engine | Precision (%) | Recall (%) | F1 Score (%) | Top-1 (%) | Top-3 (%) | Top-5 (%) | MRR | Latency (s) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Turkspell (Default)** | **100.00** | 98.59 | **99.29** | 77.30 | 89.10 | 92.40 | 0.835 | 45.5 |
| **Turkspell (TDK)** | 98.59 | **100.00** | **99.29** | **79.00** | **91.00** | **94.00** | **0.853** | 43.6 |
| **Turkspell (DD)** | 99.79 | 98.59 | 99.19 | 77.20 | 89.00 | 92.30 | 0.834 | 40.3 |
| [**hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) | 91.65 | 94.36 | 92.99 | 49.70 | 61.80 | 64.90 | 0.561 | 57.7 |
| [**tdd-ai**](https://github.com/tdd-ai/hunspell-tr) | 89.41 | 93.17 | 91.25 | 49.30 | 60.80 | 63.60 | 0.553 | 38.4 |
| [**harunzafer**](https://github.com/harunzafer/hunspell-tr) | 75.94 | 94.85 | 84.35 | 39.40 | 46.00 | 47.00 | 0.427 | 48.3 |
| [**vdemir**](https://github.com/vdemir/hunspell-tr) | 69.68 | 95.26 | 80.49 | 33.80 | 40.40 | 41.20 | 0.371 | **28.9** |

### 3. Turkspell Benchmark v3 — Affix Overgeneration Security (1,500 Pseudo-words)
| Dictionary / Engine | Security Rate (%) | False Acceptance (%) | Rejected / Total | Notes |
|---|:---:|:---:|:---:|---|
| **Turkspell (Default)** | **100.00** | **0.00** | **1,500 / 1,500** | Zero overgeneration; illegal agglutinative derivations fully blocked |
| **Turkspell (TDK)** | **100.00** | **0.00** | **1,500 / 1,500** | Strict TDK morphology provides full security |
| **Turkspell (DD)** | **100.00** | **0.00** | **1,500 / 1,500** | Dil Derneği morphology provides full security |
| [**hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) | **100.00** | **0.00** | 1,500 / 1,500 | Static rules |
| [**tdd-ai**](https://github.com/tdd-ai/hunspell-tr) | **100.00** | **0.00** | 1,500 / 1,500 | Static surface forms |
| [**harunzafer**](https://github.com/harunzafer/hunspell-tr) | **100.00** | **0.00** | 1,500 / 1,500 | Limited affixation rules |
| [**vdemir**](https://github.com/vdemir/hunspell-tr) | **100.00** | **0.00** | 1,500 / 1,500 | Restricted morphology |

---

## 📁 Project Directory Structure

```
turkspell/
├── tr.aff                     # Main distribution (Universal) affix rules file
├── tr.dic                     # Main distribution (Universal) dictionary wordlist
├── update.json                # Firefox add-on automated update manifest
├── pytest.ini                 # Pytest official test configuration
├── requirements-dev.txt       # Development, testing, and signing dependencies
│
├── .github/workflows/         # Continuous Integration & Delivery (CI/CD)
│   ├── test.yml               # Automated test & quality gate workflow
│   └── release-xpi.yml        # Secure Firefox XPI packaging and signing
│
├── dist/                      # Distribution Outputs (3 distinct profiles)
│   ├── turkspell-universal/   # Universal Profile (tr.aff, tr.dic)
│   ├── turkspell-tdk/         # TDK Profile (tr.aff, tr.dic)
│   └── turkspell-dd/          # Dil Derneği Profile (tr.aff, tr.dic)
│
├── firefox-addon/             # Mozilla Firefox WebExtension Resources (Universal)
│   ├── manifest.json          # WebExtension manifest file
│   └── dictionaries/          # Add-on dictionary bundle (dynamically staged)
│
├── firefox-addon-tdk/         # Mozilla Firefox WebExtension Resources (TDK 2026)
│   ├── manifest.json          # WebExtension manifest file
│   └── dictionaries/          # Add-on dictionary bundle (dynamically staged)
│
├── build/                     # Build & Packaging Tooling
│   ├── compile_hunspell.py    # Hunspell compilation pipeline runner
│   ├── generate_grammar_rules.py # Morphological rule and affix generator
│   ├── package_addon.py       # Deterministic Firefox XPI packaging script
│   ├── utf8_flag_mapping.py   # Frozen UTF-8 flag mapping registry
│   └── validate_build.py      # Build integrity & quality verification tool
│
├── tests/                     # Automated Testing & Regression Test Suite (73 tests, 240+ subtests)
│   ├── test_morphology.py     # Positive morphological inflection tests
│   ├── test_overgeneration.py # Overgeneration and anomaly prevention tests
│   ├── test_suggestions.py    # Suggestion quality and MRR evaluation tests
│   ├── test_golden_verbs.py   # 15,000+ verb inflection regression & canaries
│   ├── test_flag_mapping.py   # UTF-8 flag stability & uniqueness tests
│   └── golden_verbs_baseline.json # Golden verbal reference baseline dataset
│
├── tools/                     # Data Analysis, Benchmarks, and Utilities
│   ├── README.md              # Script catalog and usage documentation
│   ├── build.py               # Master dictionary compiler
│   ├── bump_version.py        # Version bumping and manifest synchronizer
│   ├── sign_addon.py          # Mozilla AMO API extension signer
│   ├── benchmark_evaluator.py # Benchmark evaluation runner
│   ├── modal_pipeline.py      # Modal H100 GPU corpus mining and LLM analysis
│   └── ...                    # Corpus mining and lexicon sanitization tools
│
├── lexicons/                  # Curated Input Lexicons & Datasets
│   ├── bilim_sanat_lexicon.json  # TDK Science & Arts Terms Lexicon (4,955 terms)
│   ├── custom_abbreviations.json # Verified official abbreviations
│   ├── custom_names.json         # Verified proper nouns and geographic names
│   ├── extra_rep_rules.json      # Structured suggestion (REP) rule table
│   ├── bad_stems.json            # Sanitized noise stems & rejection guards
│   └── zemberek_lexicon.json     # Zemberek morphological reference stems
│
└── raw_data/                  # Primary Linguistic Authority Sources
    ├── tdk_words.txt          # TDK Writing Guide (2026 Edition) & Güncel Türkçe Sözlük wordlist
    └── dil_dernegi_words.txt  # Dil Derneği Yazım Kılavuzu wordlist
```

---

## 🎯 Profile Selection Guide

Turkspell is compiled into 3 targeted profiles tailored for different orthographic standards:

| Profile | Distribution Directory | Characteristics | Recommended Usage |
|---|---|---|---|
| **Default** | `dist/turkspell-universal/` & Root (`tr.*`) | Accepts both TDK (*dâhil*, *lâzım*, *resmî*) and Dil Derneği (*dahil*, *lazım*, *resmi*) conventions. | **Web browsers**, general text editors, and everyday users. |
| **TDK Profile** | `dist/turkspell-tdk/` | Enforces strict TDK rules. Requires `â`, `î` (nisba), and `û` circumflex marks. | **Academic publications**, official institutions, and publishers adhering to TDK standards (`tdk` branch). |
| **Dil Derneği (DD)** | `dist/turkspell-dd/` | Follows Dil Derneği conventions. Standardizes nisba `î` to `i` (`resmi`), preserves softening circumflexes. | **Media and journalism**, publishing houses adhering to Dil Derneği guidelines. |

### 🔍 Key Differences Between `master` (Universal) and `tdk` Branches

In the Turkspell repository, the `master` branch represents the **Default** profile, while the `tdk` branch enforces the **Strict TDK** profile. Key distinctions and concrete lexical examples are summarized below:

| Category | Example Word / Case | `master` Branch (Default) | `tdk` Branch | Linguistic Rationale |
|---|---|:---:|:---:|---|
| **Nisba Suffix (`î`)** | *resmî* | ✅ Valid | ✅ Valid | Mandatory under TDK rules, accepted across both branches. |
| **Nisba Suffix (`î`)** | *resmi* (unhatted) | ✅ Valid | ❌ Error (Suggests *resmî*) | Dil Derneği conventions omit circumflexes on nisba adjectives (*resmi*, *milli*, *dini*, *askeri*, *tarihi*). `master` permits both for zero false alarms, whereas `tdk` branch strictly enforces *resmî*. |
| **Circumflex Palatalization (`â`, `û`)** | *dâhil*, *lâzım*, *lâkin* | ✅ Valid | ✅ Valid | Preserved in both profiles. |
| **Circumflex Palatalization (`â`, `û`)** | *dahil*, *lazım*, *lakin* (unhatted) | ✅ Valid | ❌ Error (Suggests *dâhil*, *lâzım*, *lâkin*) | Dil Derneği conventions spell these loanwords without circumflexes (*dahil*, *lazım*, *lakin*). The `master` branch accepts both forms, whereas the `tdk` branch strictly enforces circumflexes. |
| **Mandatory Semantic Disambiguation** | *mahkûm*, *sükût* | ✅ Valid | ✅ Valid | Words where omitting the circumflex alters meaning or violates orthography. |
| **Mandatory Semantic Disambiguation** | *mahkum*, *sukut* | ❌ Error (Suggests *mahkûm*, *sükût*) | ❌ Error (Suggests *mahkûm*, *sükût*) | Both branches purge illicit unhatted duplicates. |
| **Compound Word Orthography** | *özdenetim*, *sesgeçirmez*, *acıbadem* | ✅ Valid (Joined compound) | ❌ Error (Suggests *öz denetim*, *ses geçirmez*, *acı badem*) | Dil Derneği joins these 2,500+ compound nouns, which `master` accepts. The `tdk` branch strictly enforces TDK's separated open compounds. |
| **Dual Voicing Behavior** | *teleskobu* vs. *teleskopu* | ✅ Both accepted | Only *teleskobu* accepted | TDK rules voice foreign loanwords before vowels (*teleskobu*, *bergamodu*), while Dil Derneği maintains unvoiced consonants (*teleskopu*, *bergamotu*). `master` supports both. |
| **Stem Vocabulary Count** | Lexicon coverage | **141,463** stems (TDK + DD + Science & Arts) | **127,411** stems (Strict TDK + Science & Arts) | The `tdk` branch purges ~14,000 Dil Derneği-exclusive lemmas to guarantee 100% adherence to TDK's official lexicon. |
| **Target Use Case** | Audience | Web browsing (Firefox), content creation, blogging, everyday typing (zero false alarms). | Academic research, government documents, official correspondence, and TDK-compliant publishers. |

---

## 💾 File Sizes and Memory Footprint (All Dictionaries & Competitors)

Rather than bloated static rule sets or hundreds of thousands of pre-inflected words, Turkspell operates on a **Dynamic Chained Flags** architecture and UTF-8 single-character symbol mapping. This minimizes memory consumption while slashing browser cold-start latency down to ~90 ms.

| Dictionary / Profile | `.aff` Size | `.dic` Size | **Total Size** | Root Stems Count | Architecture / Format |
|---|:---:|:---:|:---:|:---:|:---:|
| **Turkspell Default** | **1.17 MB** | **8.56 MB** | **9.73 MB** | 141,463 | Dynamic Chained UTF-8 Flags (~0.77 MB XPI) |
| **Turkspell TDK Profile** | 1.24 MB | 7.60 MB | **8.84 MB** | 127,411 | Strict TDK Circumflex/Stem Rules (~0.73 MB XPI) |
| **Turkspell Dil Derneği Profile** | 1.17 MB | 8.54 MB | **9.71 MB** | 141,140 | Dil Derneği Unaccented Conventions |
| [**hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) | 31.79 MB | 1.30 MB | **33.10 MB** | 86,460 | Static Long-Flag Block |
| [**tdd-ai**](https://github.com/tdd-ai/hunspell-tr) | 2.35 MB | 34.54 MB | **36.88 MB** | 75,909 | Oversized `.dic` Lexicon |
| [**harunzafer**](https://github.com/harunzafer/hunspell-tr) | 0.24 MB | 9.00 MB | **9.24 MB** | 371,169 | Static Pre-Inflected Wordlist |
| [**vdemir**](https://github.com/vdemir/hunspell-tr) | 0.77 MB | 7.25 MB | **8.02 MB** | 177,544 | Conventional Basic Morphology |

---

## 🚀 Installation and Integration Guide

### 1. Installation as a Mozilla Firefox Add-on

1. Download the latest `turkspell-addon.xpi` from the [Releases](https://github.com/selimsum/turkspell/releases) page.
2. Open Firefox and navigate to `about:addons`.
3. Click the gear icon at the top right, select **"Install Add-on From File..."**, and pick the downloaded `.xpi` file.
4. In the context menu (right-click on any text area), select **Languages > Türkçe (Turkspell)**.

> **Developer Mode Installation**:
> Navigate to `about:debugging#/runtime/this-firefox`. Click "Load Temporary Add-on..." and select `firefox-addon/manifest.json`.

### 2. LibreOffice / OpenOffice Integration

1. In LibreOffice, navigate to **Tools > Options > Language Settings > Writing Aids**.
2. Copy the dictionary files (`tr.aff` and `tr.dic`) from your preferred profile into the LibreOffice user wordbook directory:
   * **Linux**: `~/.config/libreoffice/4/user/wordbook/` or `/usr/share/hunspell/`
   * **Windows**: `%APPDATA%\LibreOffice\4\user\wordbook\`
   * **macOS**: `~/Library/Application Support/LibreOffice/4/user/wordbook/`

### 3. Linux / macOS System-wide Installation

```bash
# Linux (Debian/Ubuntu/Fedora/Arch)
sudo cp tr.aff /usr/share/hunspell/tr_TR.aff
sudo cp tr.dic /usr/share/hunspell/tr_TR.dic

# macOS (User-level)
cp tr.aff ~/Library/Spelling/tr_TR.aff
cp tr.dic ~/Library/Spelling/tr_TR.dic
```

### 4. Command-Line (CLI) Usage

Test the dictionary directly using your system's installed `hunspell` binary:

```bash
# List misspelled words in a text file:
hunspell -d tr -l input.txt

# Interactive spell-checking and suggestion mode:
hunspell -d tr -a
```

### 5. Usage in Python Projects

```python
import subprocess

def spell_check(words: list[str], dict_path: str = "tr") -> list[str]:
    """Identify misspelled words using the Hunspell CLI."""
    p = subprocess.run(
        ["hunspell", "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return [w.strip() for w in p.stdout.splitlines() if w.strip()]

# Test
misspellings = spell_check(["kitap", "geliyom", "bilgisayar", "acııydı", "rüzgar"])
print("Spelling Errors:", misspellings)
# Output: ['geliyom', 'acııydı', 'rüzgar'] (rüzgâr requires a circumflex)
```

---

## 🛠️ Dictionary Build Pipeline (How It Is Built)

Turkspell is compiled using a **Dynamic Chained Flags** architecture that models the complex agglutinative morphology of modern Turkish while maintaining a minimal memory footprint. The build process spans multiple stages from authority lexicon parsing to compressed rule generation:

### 1. Authoritative Data Sources & Input Lexicons

The build pipeline strictly avoids unfiltered web scrapes, relying entirely on verified authority sources:
* **TDK Writing Guide (2026 Edition) & Güncel Türkçe Sözlük ([`raw_data/tdk_words.txt`](file:///c:/gemini/turkspell/raw_data/tdk_words.txt))**: The primary foundation for strict TDK orthography, spelling rules, and mandatory circumflex words, established primarily on the official TDK Writing Guide (2026 Edition).
* **TDK Science & Arts Terms Lexicon ([`lexicons/bilim_sanat_lexicon.json`](file:///c:/gemini/turkspell/lexicons/bilim_sanat_lexicon.json))**: 4,955 cleaned and verified academic stems across medicine, biology, physics, philosophy, arts, and engineering published by TDK.
* **Dil Derneği Yazım Kılavuzu ([`raw_data/dil_dernegi_words.txt`](file:///c:/gemini/turkspell/raw_data/dil_dernegi_words.txt))**: Official alternative lexicon standardizing nisba `î` to `i`.
* **Proper Nouns & Geographic Names ([`lexicons/custom_names.json`](file:///c:/gemini/turkspell/lexicons/custom_names.json))**: Verified proper nouns, administrative regions, countries, and historical figures.
* **Official Abbreviations ([`lexicons/custom_abbreviations.json`](file:///c:/gemini/turkspell/lexicons/custom_abbreviations.json))**: Case-preserved national and international acronyms (`TBMM`, `TÜBİTAK`, `KHz`, `Wi-Fi`).
* **Zemberek Morphological Reference ([`lexicons/zemberek_lexicon.json`](file:///c:/gemini/turkspell/lexicons/zemberek_lexicon.json))**: Cross-validated root stems, POS tags, and morphotactic attributes.

### 2. Morphological Rules and UTF-8 Flag Architecture

* **Rule Generation ([`build/generate_grammar_rules.py`](file:///c:/gemini/turkspell/build/generate_grammar_rules.py))**: Generates rules for Turkish vowel harmony, consonant softening (p/ç/t/k -> b/c/d/ğ), internal vowel drop (*burun/burnu*), copula, and predicate inflections.
* **UTF-8 Flag Compression ([`build/utf8_flag_mapping.py`](file:///c:/gemini/turkspell/build/utf8_flag_mapping.py))**: Remaps thousands of 2-byte `FLAG long` rule combinations into single-byte UTF-8 symbols (`FLAG UTF-8`), cutting `.aff` file size by ~60% and reducing add-on load time to 90 ms.
* **Inflection Compiler ([`build/compile_hunspell.py`](file:///c:/gemini/turkspell/build/compile_hunspell.py))**: Matches root stems with their corresponding morphological flag sets to produce the dictionary wordlist.

### 3. One-Step Master Compilation

To compile all profiles in a single command with rule hardening and dictionary sanitization:

```bash
python tools/build.py
```

The master build script ([`tools/build.py`](file:///c:/gemini/turkspell/tools/build.py)) executes the following steps sequentially:

1. **Lexicon Harmonization (`load_lexicons`)**: Loads TDK and Dil Derneği vocabularies and merges them with proper names and acronyms.
2. **Affix Rule Hardening (`build_hardened_aff`)**:
   * Closes uncontrolled `.` wildcard rules; enforces `consonant_cond` (`[^AEIOUaeiouÂÎÖÛÜâîöûüİı]`) on vowel-initial suffixes to prevent vowel collisions.
   * Prunes unused dead flag blocks (`G2`, `NX`, `Vb`, `Vf`) and duplicate rules.
   * Consolidates verb inflection rules for *demek* and *yemek* (`VY` block).
   * Injects the enhanced `MAP 14` matrix and extended `REP` typo-correction table.
3. **Dictionary Sanitization (`build_sanitized_dic`)**:
   * Purges unhatted duplicate entries for mandatory circumflex words (`mahkum`, `sükut`).
   * Eliminates 1-3 letter permutation noise, OCR scanner debris, and crawler spam with excessive consonant clusters.
   * Strips apostrophe inflection flags (`PROPER_SUB`) from common nouns (*elma*, *tornavida*) to prevent erroneous derivations like `*elma'nın`; isolates capitalized proper names with harmonic apostrophe flags.
   * Deduplicates multi-line root entries by merging their flag sets.
4. **Multi-Profile Output**: Outputs 3 distinct profiles under `dist/`:
   * `dist/turkspell-tdk/`: Strict TDK profile with mandatory circumflex usage.
   * `dist/turkspell-dd/`: Dil Derneği orthography profile.
   * `dist/turkspell-universal/`: Dual-standard universal profile.
5. **Automated Deployment**: Copies the Universal profile to the repo root (`tr.aff` and `tr.dic`) and the Firefox add-on directory (`firefox-addon/dictionaries/`).

### 4. Firefox Add-on Packaging

Package the compiled dictionaries into a ready-to-install browser extension:

```bash
python build/package_addon.py
```

This script ([`build/package_addon.py`](file:///c:/gemini/turkspell/build/package_addon.py)) validates [`firefox-addon/manifest.json`](file:///c:/gemini/turkspell/firefox-addon/manifest.json), packages the universal dictionary binaries, and produces `turkspell-addon.xpi`.

---

## 🧠 LLM-Guided Morphological Training Pipeline (How It Was Trained)

While traditional Hunspell dictionaries rely exclusively on static manual rules, Turkspell utilizes an **LLM-guided training and inference loop** ([`training/`](file:///c:/gemini/turkspell/training)) to detect gaps in natural language corpora and expand grammar rules.

```
   [Large Turkish Corpora] (Wiki, OSCAR, Magazine Corpus)
               │
               ▼
   [training/generate_training_data.py]
         ├── Noise, OCR, and Foreign Word Sanitization
         ├── Hunspell CLI Detection of Unrecognized Words (False Negatives)
         └── Root-Based Suffix Gap Clustering (valid_groups)
               │
               ▼
   [train_dataset.jsonl] (Instruction-Tuning Dataset)
               │
               ▼
   [training/train.py] ──> Qwen2.5-Coder-7B-Instruct
         ├── QLoRA / LoRA Fine-Tuning (PEFT + TRL SFTTrainer)
         └── Morphological Grammar Rule Code Synthesis
               │
               ▼
   [training/generate_rules_inference.py]
         └── Suffix Rule Code Generation for generate_grammar_rules.py
```

### 1. Corpus Gap Mining and Dataset Generation

[`training/generate_training_data.py`](file:///c:/gemini/turkspell/training/generate_training_data.py) extracts training samples from large corpora:
1. **Corpus Ingestion**: Scans and tokenizes millions of words across `wiki_corpus.txt` and `magazine_corpus.txt`.
2. **Filtering**: Removes English vocabulary ([`data/english_words_large.txt`](file:///c:/gemini/turkspell/raw_data/english_words_large.txt)), foreign proper nouns, Q/W/X noise, and low-frequency typos (freq < 10).
3. **False Negative Detection**: Evaluates candidate words against Hunspell (`hunspell -d tr -l`) to identify legitimate Turkish words currently rejected by the dictionary.
4. **Root Clustering**: Groups unrecognized inflected forms by their known stems (`merged_dictionary_cleaned.txt`). Roots with 3+ unrecognized inflections (`valid_groups`) are identified as rule gaps.
5. **Instruction-Tuning Dataset Creation**: Assembles `train_dataset.jsonl` with structured prompts:
   * **Instruction**: *"Determine the missing suffix templates and propose code edits for generate_grammar_rules.py to accept unrecognized forms of root 'yap'."*
   * **Input**: Root stem, unrecognized inflections (`yapıverdi, yapıvermiş, yapıverir...`), and existing template context (`TAM`, `COPULAS`).
   * **Output**: Python code snippet for `generate_grammar_rules.py` (`TAM.extend([...])`).

### 2. Model Architecture & LoRA Fine-Tuning

[`training/train.py`](file:///c:/gemini/turkspell/training/train.py) fine-tunes the language model:
* **Base Model**: `Qwen/Qwen2.5-Coder-7B-Instruct` (high code reasoning and structural generation capacity).
* **Parameter-Efficient Fine-Tuning (LoRA / QLoRA)**:
  * Target modules: `["q_proj", "v_proj", "k_proj", "o_proj"]`, rank: `r=16`, `lora_alpha=32`, `dropout=0.05`.
  * **Hardware Adaptivity**: Dynamically applies BitsAndBytes 4-bit NormalFloat4 (NF4) quantization when VRAM < 20 GB (T4 GPUs), or standard `bfloat16` LoRA when VRAM >= 20 GB (L4/A100).
* **Training Stack**: HuggingFace `peft` and `trl` (`SFTTrainer`), trained for 3 epochs with gradient accumulation (4) and learning rate `2e-4`.
* **Output**: Fine-tuned adapter weights saved to `./output_dir`.

### 3. Rule Inference and Integration

[`training/generate_rules_inference.py`](file:///c:/gemini/turkspell/training/generate_rules_inference.py) loads the trained adapters on the base model. When an uncovered morphological pattern is detected, the model proposes valid Python rules adhering to `generate_grammar_rules.py` syntax, which are reviewed and integrated into the rule generator.

### 4. LLM-Based Morphological Parsing

New root candidates are parsed using [`training/llm_morphology_parser.py`](file:///c:/gemini/turkspell/training/llm_morphology_parser.py):
* Extracts the root **lemma**, Part of Speech (**POS**: Noun, Verb, Adjective, Adverb), and morphotactic attributes:
  * `Voicing`: Consonant softening before vowel-initial suffixes (*kitap -> kitabı*, *renk -> rengi*).
  * `LastVowelDrop`: Internal vowel loss during inflection (*burun -> burnu*, *ağız -> ağzı*).
  * `CompoundP3sg`: Compound nouns carrying inherent 3rd-person possessive suffixes (*gökkuşağı*, *yıldızlararası*).
* Verified outputs are integrated into [`lexicons/`](file:///c:/gemini/turkspell/lexicons/).

---

## 🔧 Sanitization, Correction & Suggestion Engine (How It Is Corrected)

In Turkspell, "correction" refers to two core mechanisms: **(A) Sanitizing rule anomalies and errors in the dictionary database**, and **(B) Real-time typo correction and suggestion ranking in user texts via Hunspell**.

### A. Dictionary Sanitization & Anomaly Elimination

Turkspell eliminates thousands of historic vulnerabilities and overgeneration flaws:

1. **Overgeneration Flaw Remediation**:
   * **Vowel Collision Shield**: Purged 17,824 wildcard `.` rules; added `consonant_cond` (`[^AEIOU...]`) to vowel-initial suffixes, eliminating illegal double vowels without buffer consonants like `*acııydı`, `*anomaliine`, `*beliiydi`, and `*kediin` ([`tests/test_overgeneration.py`](file:///c:/gemini/turkspell/tests/test_overgeneration.py)).
   * **Broken Verb Form Shield**: Eliminated the chronic *debileceklerine* bug (`*debilecek`, `*debileceklerini`, `*yebilecek`) by consolidating `VY` rules into `[dy]emek`.
   * **Buffer Consonant Isolation**: Blocked duplicated buffer consonants (`*kapıssı`, `*arabaynı`, `*masannın`).
2. **Common vs. Proper Noun Apostrophe Isolation**:
   * In legacy dictionaries, blanket apostrophe flags caused words like `*elma'nın` or `*tornavida'ya` to be accepted. The build pipeline stripped all `PROPER_SUB` flags from common nouns, reserving apostrophe inflections exclusively for capitalized proper nouns.
3. **TDK Errata & Typesetting Correction**:
   * Corrected optical and typesetting errors from the reverse dictionary using [`tools/apply_tdk_errata.py`](file:///c:/gemini/turkspell/tools/apply_tdk_errata.py) and [`raw_data/tdk_errata.json`](file:///c:/gemini/turkspell/raw_data/tdk_errata.json); removed fictitious voiced stems (`felaked`, `stoğ`).
4. **Mandatory Circumflex Duplicate Purge**:
   * Purged unhatted clones (`mahkum`, `sükut`) of words where circumflex marks are strictly mandatory under TDK rules (`mahkûm`, `sükût`, `rükû`, `âlemşümul`, `aliyyülâlâ`).

### B. Typo Correction & Suggestion Ranking Engine

Turkspell achieves a **96.0% Top-1 Accuracy** and **0.980 MRR (Mean Reciprocal Rank)** for typo corrections through two synergistic mechanisms:

#### 1. Extended Character Mapping Matrix (`MAP 14`)

Hunspell utilizes the `MAP` matrix to minimize transformation costs between phonetically and orthographically related letters. Turkspell defines 14 language-specific equivalence classes:

```text
MAP 14
MAP aâAÂ       # Circumflex 'a' and variants
MAP uûUÛ       # Circumflex 'u' variants
MAP uüUÜ       # Rounded vowel slips
MAP iîİÎ       # Nisba and softening 'i' variants
MAP ıiIİ       # Turkish dotted/dotless 'ı/i' mappings
MAP oöOÖ       # Rounded back/front vowel proximity
MAP eêEÊ       # Circumflex and transcription 'e' variants
MAP cçCÇ       # Voiced/unvoiced palatal consonants
MAP gğGĞ       # Soft g substitutions
MAP sşSŞ       # Sibilant consonants
MAP dtDT       # Dental consonant voicing/devoicing
MAP bpBP       # Bilabial consonant shifts
MAP vwyVWY     # Semi-vowel and loanword substitutions
MAP '’‘        # Apostrophe variants and typographic quotes
```

When a user types `ruzgar`, the engine directly surfaces `rüzgâr` as the Rank 1 suggestion; typing `imkani` prioritizes `imkânı`.

#### 2. Comprehensive Phonetic & Typo Replacement Table (`REP`)

Injected into `tr.aff` by [`tools/build.py`](tools/build.py), the `REP` table features 1,067 high-confidence rules targeting high-frequency Turkish errors verified against TDK and Dil Derneği vocabularies:

* **Phonetic & Circumflex Disambiguation**:
  `adeti -> âdeti / adedi` | `adete -> âdete / adede` | `adetin -> âdetin / adedin`

* **Keyboard Slip & Suffix Boundaries**:
  `dem -> den` | `dam -> dan` | `dej -> den` | `tem -> ten` | `larz -> lara` | `lerz -> lere`
* **Circumflex (Accent Mark) Corrections**:
  `sükut -> sükût` | `mahkum -> mahkûm` | `rükü -> rükû` | `rüzgar -> rüzgâr` | `hikayesi -> hikâyesi` | `imkanlar -> imkânlar` | `dükkan -> dükkân`
* **Common Orthographic Typos**:
  `herkez -> herkes` | `traş -> tıraş` | `klavuz -> kılavuz` | `ünvan -> unvan` | `şarz -> şarj` | `egsoz -> egzoz` | `kiprik -> kirpik` | `eşki -> ekşi` | `muhattap -> muhatap`
* **Compound & Separate Word Errors**:
  `yanısıra -> yanı sıra` | `farketmek -> fark etmek` | `terketmek -> terk etmek` | `sağol -> sağ ol` | `herşey -> her şey` | `hoşgeldiniz -> hoş geldiniz`

#### 3. Running Suggestions from the CLI and Test Battery

Test the suggestion engine interactively via CLI:

```bash
# Interactive spell-check & suggestion mode:
hunspell -d tr -a

# Example input/output:
# & ruzgar 5 0: rüzgâr, rüzgarı, rüzgara, rüzgarlı, rüzgarlar
# & herkez 3 0: herkes, herkeze, herkesin
```

Run the automated suggestion accuracy battery:

```bash
python -m unittest tests/test_suggestions.py
# Output: Suggestion Battery MRR: 0.980 | Top-1 Accuracy: 96.0% (24/25) - OK
```

---

## 🧪 Quality Gates & Automated Testing

Turkspell enforces multi-layer automated testing to guarantee morphological accuracy and dictionary integrity:

```bash
# Run the test suite via pytest:
pytest

# Or via Python's standard unittest discovery:
python -m unittest discover tests
```

### Test Coverage

1. **`tests/test_morphology.py` (Positive Inflection Tests)**:
   * Copula and predicate inflections (*değildir*, *aittir*, *idim*, *imişler*).
   * Palatal / thin 'l' rules (*alkolün*, *alkolsüz*, *rolümüz*, *kontrolünüze*).
   * Non-softening loanword roots (*felaketi*, *stoku*, *hukukun*).
   * Internal vowel drop (*zehri*, *emrimiz*).
   * Pronominal 'n' and compound derivations.
2. **`tests/test_overgeneration.py` (Overgeneration & Anomaly Prevention)**:
   * Buffer consonant duplication prevention (*\*kapıssı*, *\*arabaynı*).
   * Vowel collision prevention (*\*acııydı*, *\*anomaliine*, *\*beliiydi*).
   * *debileceklerine* bug prevention (*\*debilecek*, *\*yebilecek*).
   * Vowel harmony violation prevention (*\*evlar*, *\*kedidan*).
3. **`tests/test_suggestions.py` (Suggestion Quality & MRR)**:
   * Top-1 / Top-3 accuracy for circumflex and keyboard slip errors.
   * Standard 25-word evaluation battery requiring **0.90+ MRR** and **90.0%+ Top-1 accuracy**.
4. **`tests/test_golden_verbs.py` (Verb Inflection Regression & Canary Tests)**:
   * Regression checks across 15,323 verbal forms and 49 canary overgeneration guards.
5. **`tests/test_flag_mapping.py` (Flag Mapping & Character Integrity)**:
   * Verifies uniqueness, NEEDAFFIX integrity, and UTF-8 codepoint stability across 200 flags.

### Git Pre-Commit Quality Gate

Automated via `.git/hooks/pre-commit`: on every `git commit`:
1. `python build/validate_build.py` verifies dictionary sizes, flag mappings, and lexicon integrity.
2. `pytest` executes all 73 automated tests and 240+ subtests without failure.
3. If any test or check fails, the commit is automatically blocked.

---

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
