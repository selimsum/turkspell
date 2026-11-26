# Turkspell Araçları ve Betikleri (Tools & Scripts)

Bu dizin, Turkspell Türkçe Hunspell sözlüğünün derleme, yayınlama, doğrulama, leksikon madenciliği ve veri analitiği araçlarını içerir.

---

## 1. 🚀 Derleme ve Yayınlama (Build & Release)

| Betik | Açıklama |
|---|---|
| [`build.py`](build.py) | **Ana derleme yürütücüsü.** Universal, TDK ve Dil Derneği profillerini tek adımda derler, leksikonları birleştirir ve `dist/` çıktılarını üretir. |
| [`migrate_dictionary.py`](migrate_dictionary.py) | Kök sözlük girdilerini 2 aşamalı morfolojik bayrak zincirlerine ve tek baytlık UTF-8 bayraklarına dönüştürür. |
| [`bump_version.py`](bump_version.py) | SemVer sürüm artırma aracı; `firefox-addon/manifest.json`, `firefox-addon-tdk/manifest.json` ve `update.json` sürümlerini senkronize eder. |
| [`sign_addon.py`](sign_addon.py) | Mozilla AMO API üzerinden Firefox WebExtension paketlerini (`.xpi`) imzalar, kriptografik `META-INF/` doğrulaması yapar ve güvenli ortam değişkenleri kullanır. |

---

## 2. 🧪 Değerlendirme, Kıyaslama ve Test (Evaluation & Benchmarks)

| Betik | Açıklama |
|---|---|
| [`benchmark_evaluator.py`](benchmark_evaluator.py) | Mukayese, Gold V4 ve Turkspell Benchmark V2 test paketlerini bağımsız sözlük motorlarına karşı koşturur. |
| [`generate_golden_verbs.py`](generate_golden_verbs.py) | Fiil morfolojisi regresyon testleri için 10.000+ formluk altın veri kümesini (`tests/golden_verbs_baseline.json`) üretir. |
| [`validate_clean_words.py`](validate_clean_words.py) | Aday temiz sözcük listelerini TDK ve Dil Derneği otorite kaynaklarıyla karşılaştırarak gerçek yanlış pozitifleri ayırır. |
| [`profile_affix_rules.py`](profile_affix_rules.py) | `tr.aff` ve `tr.dic` içindeki UTF-8 bayrak dağılımını ve kullanılmayan kuralları profiller. |

---

## 3. 🔍 Derlem Analizi, Bulut GPU (Modal) ve Morfoloji Denetimi (Audits & Corpus Mining)

| Betik | Açıklama |
|---|---|
| [`modal_pipeline.py`](modal_pipeline.py) | Modal.com H100 vLLM üzerinde FineWeb-2 Türkçe derlemini akışlı tarar ve `Qwen/Qwen2.5-32B-Instruct-AWQ` ile morfolojik kök/ek analizi yapar. |
| [`modal_model_comparison.py`](modal_model_comparison.py) | Farklı LLM modellerinin Türkçe morfolojik ayrıştırma doğruluğunu ve hızını Modal GPU üzerinde karşılaştırır. |
| [`corpus_rule_miner.py`](corpus_rule_miner.py) | FineWeb-2 derlem sıklıkları ve LLM analiz çıktılarından yeni `SFX` ek kuralları, şapkalı/ünlü düşmeli gövdeler ve `REP` öneri kuralları çıkarır. |
| [`mine_corpus_rejected_inflections.py`](mine_corpus_rejected_inflections.py) | Kökü `tr.dic` içinde bulunduğu hâlde çekimli biçimi Hunspell tarafından reddedilen gerçek derlem sözcüklerini tespit eder. |
| [`audit_abbrevs_and_names.py`](audit_abbrevs_and_names.py) | Özel adların ve kısaltmaların kesme işaretli çekimlerini denetler. |
| [`audit_clitics_and_particles.py`](audit_clitics_and_particles.py) | Soru eki (`mı/mi/mu/mü`) ve bağlaçların (`da/de`, `ki`) ayrı/bitişik yazımını ve öneri sıralamasını denetler. |
| [`audit_compounds_and_idioms.py`](audit_compounds_and_idioms.py) | Birleşik sözcükler, yardımcı fiiller ve TDK / Dil Derneği profil ayrımlarını denetler. |
| [`audit_numbers_and_dates.py`](audit_numbers_and_dates.py) | Sayı, sıra sayısı, üleştirme, tarih ve saat eklerini denetler. |
| [`audit_overgeneration_and_suggestions.py`](audit_overgeneration_and_suggestions.py) | Aşırı üretim (overgeneration) bataryasını ve TDK sık yapılan yanlışlar öneri başarısını puanlar. |
| [`audit_pure_verb_matrix.py`](audit_pure_verb_matrix.py) | Tüm Türkçe fiil ve isim çekim paradigmalarını yalın kök matrisi üzerinde doğrular. |
| [`audit_tdk_dizin_flags.py`](audit_tdk_dizin_flags.py) | TDK 2026 dizinindeki tüm madde başlarını, ses olaylarını ve eşsesli kökleri `tr.dic` / `tr.aff` üzerinde denetler. |
| [`extract_bilim_sanat_terms.py`](extract_bilim_sanat_terms.py) | TDK Bilim ve Sanat Terimleri Sözlüğü'nden terimleri ayıklar ve `lexicons/bilim_sanat_lexicon.json` üretir. |

---

## 4. 📦 Bakım ve Veri Düzeltme Araçları (Maintenance & Data Cleaners)

* [`apply_tdk_errata.py`](apply_tdk_errata.py) & [`add_tdk_updates.py`](add_tdk_updates.py): TDK yazım güncellemelerini ve errata düzeltmelerini uygular.
* [`clean_custom_names.py`](clean_custom_names.py): Özel adlar listesindeki biçimlendirme hatalarını ve mükerrer kayıtları temizler.
* [`ts_corpus_validator.py`](ts_corpus_validator.py) & [`ingest_free_colab_candidates.py`](ingest_free_colab_candidates.py): TS Corpus (LexiTR) prestij doğrulaması ve aday sözcük içe aktarma araçları.
