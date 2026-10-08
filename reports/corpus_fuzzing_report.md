# Turkspell Doğal Metin Külliyatı (Corpus Fuzzing) Raporu

- **Tarih**: 2026-10-08 18:44:41
- **Taranan Özgün Türkçe Sözcük**: 65,057
- **Hunspell Başarı Oranı**: 61,038 / 65,057 (93.82%)
- **Toplam Tanınmayan Sözcük**: 4,019 (6.18%)

## 1. Tespit Özeti

| Kategori | Benzersiz Sözcük Sayısı | Toplam Külliyat Frekansı |
| :--- | :--- | :--- |
| **Morfolojik / Ek Zinciri Boşluğu (Grup A)** | 23 | 281 |
| **Eksik Kök / Madde Başı (Grup B)** | 26 | 4,616 |
| **Diğer / Tipik Hata / Yabancı (Grup C)** | 3,970 | 81,245 |

## 2. En Sık Görülen Eksik Ek Şablonları (Grup A)

| Ek / Ek Zinciri | Etkilenen Kelime Sayısı | Külliyat Ağırlığı |
| :--- | :--- | :--- |
| `-ti` | 1 | 100 |
| `-ur` | 3 | 40 |
| `-ar` | 2 | 31 |
| `-er` | 4 | 29 |
| `-ndaki` | 2 | 17 |
| `-ir` | 2 | 15 |
| `-ür` | 1 | 12 |
| `-an` | 2 | 11 |
| `-en` | 2 | 8 |
| `-eli` | 1 | 6 |
| `-tı` | 1 | 6 |
| `-du` | 1 | 3 |
| `-me` | 1 | 3 |

## 3. En Yüksek Frekanslı Morfolojik Boşluklar (İlk 40 Sözcük)

| Sıra | Hata Veren Kelime | Kök | Tespit Edilen Ek | Frekans |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `anti` | `anmak` | `-ti` | 100 |
| 2 | `pour` | `pomak` | `-ur` | 30 |
| 3 | `year` | `ye` | `-ar` | 27 |
| 4 | `idir` | `it` | `-ir` | 12 |
| 5 | `dönüştürür` | `dönüştürmek` | `-ür` | 12 |
| 6 | `over` | `ovmak` | `-er` | 11 |
| 7 | `oder` | `ot` | `-er` | 11 |
| 8 | `sındaki` | `sımak` | `-ndaki` | 10 |
| 9 | `yuan` | `yumak` | `-an` | 8 |
| 10 | `solundaki` | `solumak` | `-ndaki` | 7 |
| 11 | `aleli` | `almak` | `-eli` | 6 |
| 12 | `rieur` | `rie` | `-ur` | 6 |
| 13 | `bantı` | `banmak` | `-tı` | 6 |
| 14 | `token` | `tokmak` | `-en` | 5 |
| 15 | `udur` | `ut` | `-ur` | 4 |
| 16 | `idar` | `it` | `-ar` | 4 |
| 17 | `aider` | `ait` | `-er` | 4 |
| 18 | `alıkoydu` | `alıkoymak` | `-du` | 3 |
| 19 | `some` | `somak` | `-me` | 3 |
| 20 | `artir` | `artmak` | `-ir` | 3 |
| 21 | `etan` | `etmek` | `-an` | 3 |
| 22 | `bien` | `bi` | `-en` | 3 |
| 23 | `ater` | `atmak` | `-er` | 3 |

## 4. En Yüksek Frekanslı Eksik Kökler (İlk 40 Sözcük)

| Sıra | Eksik Kök | Kaynak | Tür | Frekans |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `dan` | Zemberek | Duplicator | 3,947 |
| 2 | `tir` | Zemberek | Duplicator | 187 |
| 3 | `kütleçekim` | Zemberek | Noun | 94 |
| 4 | `hakimiyet` | Zemberek | Noun | 79 |
| 5 | `asteroit` | Zemberek | Noun | 56 |
| 6 | `psikiyatrist` | Zemberek | Noun | 44 |
| 7 | `id` | DilDernegi | Noun | 39 |
| 8 | `pi` | Zemberek | Noun | 20 |
| 9 | `nötrino` | Zemberek | Noun | 19 |
| 10 | `mahkum` | Zemberek | Noun | 19 |
| 11 | `kick` | Zemberek | Noun | 13 |
| 12 | `serotonin` | Zemberek | Noun | 11 |
| 13 | `plasebo` | Zemberek | Noun | 10 |
| 14 | `mer` | Zemberek | Noun | 9 |
| 15 | `dokunmatik` | Zemberek | Adjective | 9 |
| 16 | `dışılık` | Zemberek | Noun | 8 |
| 17 | `mek` | Zemberek | Noun | 8 |
| 18 | `mak` | Zemberek | Noun | 7 |
| 19 | `bipolar` | Zemberek | Adjective | 6 |
| 20 | `makina` | Zemberek | Noun | 6 |
| 21 | `tük` | Zemberek | Noun | 6 |
| 22 | `meskun` | Zemberek | Noun | 5 |
| 23 | `şar` | TDK | Noun | 5 |
| 24 | `fiks` | Zemberek | Adjective | 3 |
| 25 | `poli` | Zemberek | Noun | 3 |
| 26 | `nev` | Zemberek | Noun | 3 |

