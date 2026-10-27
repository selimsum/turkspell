# Turkspell Araçları ve Betikleri (Tools & Scripts)

Bu dizin, Turkspell Türkçe Hunspell sözlüğünün derleme, yayınlama, doğrulama, leksikon madenciliği ve veri analitiği araçlarını içerir.

---

## 1. 🚀 Derleme ve Yayınlama (Build & Release)

| Betik | Açıklama |
|---|---|
| [`build.py`](build.py) | **Ana derleme yürütücüsü.** Universal, TDK ve Dil Derneği profillerini tek adımda derler, leksikonları birleştirir ve `dist/` çıktılarını üretir. |
| [`bump_version.py`](bump_version.py) | SemVer sürüm artırma aracı; `firefox-addon/manifest.json`, `firefox-addon-tdk/manifest.json` ve `update.json` sürümlerini senkronize eder. |
| [`sign_addon.py`](sign_addon.py) | Mozilla AMO API üzerinden Firefox WebExtension paketlerini (`.xpi`) imzalar, kriptografik `META-INF/` doğrulaması yapar ve güvenli ortam değişkenleri kullanır. |
| [`compile_hunspell_utf8.py`](compile_hunspell_utf8.py) | Hunspell kural ve bayraklarını UTF-8 bayrak sistemine dönüştürme yardımcısı. |

---

## 2. 🧪 Değerlendirme, Kıyaslama ve Test (Evaluation & Benchmarks)

| Betik | Açıklama |
|---|---|
| [`benchmark_evaluator.py`](benchmark_evaluator.py) | Mukayese, Gold V4 ve Turkspell Benchmark V2 test paketlerini bağımsız sözlük motorlarına karşı koşturur. |
| [`generate_golden_verbs.py`](generate_golden_verbs.py) | Fiil morfolojisi regresyon testleri için 15.000+ formluk altın veri kümesini (`tests/golden_verbs_baseline.json`) üretir. |
| [`clean_benchmark_collisions.py`](clean_benchmark_collisions.py) | Kıyaslama test setlerindeki çarpışmaları bağımsız referans sözlüklerle (`harunzafer`, `vdemir`) filtreler. |
| [`clean_benchmark_v1_homographs.py`](clean_benchmark_v1_homographs.py) | Akademik test setlerindeki eşsesli sözcükleri denetler. |

---

## 3. 🔍 Derlem Analizi ve Morfoloji Denetimi (Audits & Corpus Mining)

| Betik | Açıklama |
|---|---|
| [`audit_missing_morphology.py`](audit_missing_morphology.py) | Sözlükte eksik olan morfolojik çekim kombinasyonlarını raporlar. |
| [`audit_overgeneration_and_suggestions.py`](audit_overgeneration_and_suggestions.py) | Aşırı üretim açığı olabilecek ek zincirlerini tarar ve MRR öneri başarısını puanlar. |
| [`audit_pure_verb_matrix.py`](audit_pure_verb_matrix.py) | Tüm Türkçe fiil paradigmalarını kapsam haritasına göre doğrular. |
| [`corpus_affix_discovery.py`](corpus_affix_discovery.py) | Geniş Türkçe metin derlemlerinden yeni türetim ve çekim eklerini madencilikle tespit eder. |
| [`clean_and_audit_oscar.py`](clean_and_audit_oscar.py) | OSCAR derlemindeki ham söz varlığını temizler, frekans analizi yapar. |
| [`extract_bilim_sanat_terms.py`](extract_bilim_sanat_terms.py) | TDK Bilim ve Sanat Terimleri Sözlüğü'nden terimleri ayıklar ve JSON leksikona dönüştürür. |

---

## 4. 📦 Bakım ve Veri Düzeltme Araçları (Maintenance & Data Cleaners)

* `apply_tdk_errata.py` & `add_tdk_updates.py`: TDK yazım güncellemelerini ve errata düzeltmelerini uygular.
* `clean_custom_names.py`: Özel adlar listesindeki biçimlendirme hatalarını ve mükerrer kayıtları temizler.
* `clean_zemberek_lexicon.py`: Zemberek kök leksikonunu arındırır.
* `compare_dictionaries.py` & `compare_tdk_dernek.py`: Farklı Hunspell Türkçe sözlüklerini karşılaştırır.
