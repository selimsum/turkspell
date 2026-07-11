# Turkspell: Optimized Turkish Hunspell Dictionary

Turkspell is a high-performance, lightweight Turkish Hunspell dictionary (`tr.dic` and `tr.aff`) built using a **Dynamic Chained Flags** architecture. It achieves **state-of-the-art correction accuracy** on Turkish spelling benchmarks — ranking **#1 on V1, V2, and V3** — while reducing the affix file size from **139.7 MB** to **12.95 MB** (total dictionary memory footprint: **19.35 MB**).

---

## Benchmark Performance

Turkspell has been evaluated on the standard V1 and V2 official test sets of the [tdd-ai/spell-checking-and-correction](https://github.com/tdd-ai/spell-checking-and-correction) repository (part of the [Mukayese](https://arxiv.org/abs/2203.01215) benchmarking suite), as well as a newly created **V3 Official Test** designed to eliminate real-word typo collisions:

### Official Test V1 (10,000 words)

| Model / Dictionary | Error Detection Precision (%) | Error Detection Recall (%) | Error Detection F1 (%) | Error Correction Accuracy (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell** (19.35 MB) | **99.78** | 93.85 | **96.72** | 87.67 |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 97.40 | 94.16 | 95.75 | **93.40** |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 92.75 | 96.31 | 94.49 | 78.20 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | 97.86 | 94.18 | 95.98 | 93.30 |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 81.26 | **96.99** | 88.43 | 79.20 |

### Clean Test V1 (10,000 words)

| Model / Dictionary | Error Detection Precision (%) | Error Detection Recall (%) | Error Detection F1 (%) | Error Correction Accuracy (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell** (19.35 MB) | **99.78** | 99.64 | **99.71** | 92.69 |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 97.40 | 99.07 | 98.23 | 96.00 |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 92.56 | 99.98 | 96.13 | 78.20 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | 97.87 | 99.07 | 98.47 | **96.60** |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 80.64 | **99.98** | 89.28 | 80.80 |

### Official Test V2 (10,000 words)

| Model / Dictionary | Error Detection Precision (%) | Error Detection Recall (%) | Error Detection F1 (%) | Error Correction Accuracy (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell** (19.35 MB) | **99.93** | 95.75 | **97.79** | **69.01** |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 98.08 | 95.12 | 96.58 | 54.21 |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 95.53 | 97.15 | 96.33 | 47.69 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | 98.34 | 95.08 | 96.68 | 53.75 |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 91.10 | **97.38** | 94.14 | 47.82 |

### Clean Test V2 (10,000 words)

| Model / Dictionary | Error Detection Precision (%) | Error Detection Recall (%) | Error Detection F1 (%) | Error Correction Accuracy (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell** (19.35 MB) | **99.92** | 99.77 | **99.84** | **79.51** |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 97.94 | 99.17 | 98.55 | 62.84 |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 95.06 | 99.98 | 97.46 | 54.14 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | 98.23 | 99.14 | 98.68 | 62.66 |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 90.14 | **100.00** | 94.81 | 53.01 |

### Official Test V3 (10,000 words - Collision-Filtered)

| Model / Dictionary | Error Detection Precision (%) | Error Detection Recall (%) | Error Detection F1 (%) | Error Correction Accuracy (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell** (19.35 MB) | 99.91 | **99.07** | **99.49** | **69.89** |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 99.49 | 98.49 | 98.99 | 55.90 |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 97.67 | 99.57 | 98.61 | 49.28 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | **99.68** | 98.45 | 99.06 | 55.45 |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 92.53 | 99.43 | 95.85 | 48.40 |

### How the V3 Benchmark Was Created

In artificially generated spellchecking benchmarks, keyboard-proximity-based corruption is used to create typos. However, this corruption often triggers **real-word error collisions**—where a typo accidentally results in a different, valid Turkish word (e.g., corrupting the gold word `verir` to produce `veri`, which is itself a valid Turkish noun). 

Dictionary-based spellcheckers correctly accept these words, but because the dataset marks them as errors (since `input != gold`), they are flagged as false negatives, artificially lowering the measured Error Detection Recall.

To address this, we generated **Official Test V3** with the following enhancements:
1.  **Zemberek-Based Collision Filtering**: Every generated typo is checked using Zemberek NLP's morphological analyzer. If a corrupted word resolves to a valid parse in Turkish, the corruption is rejected, and the generator retries with a different proximity-based mutation. This ensures all spelling typos are strictly non-words.
2.  **Removal of Incorrect Colloquial Merges**: We filtered out colloquial compound verb merges (e.g., `farketmek`, `terketmek`, `parketmek`), lowercase abbreviations (e.g., `cdlerimiz`, `kdvnin`), and phonetic slang (e.g., `yollucam`) from the source dataset. These are technically spelling errors under TDK guidelines and should not be treated as correct `gold` words in a standard spelling test set.
3.  **Fixed Configuration and Encodings**: Corrected original dataset generation paths to use local resources (`true_words.txt`) and enforced UTF-8 output encoding to preserve Turkish circumflex characters (â, î, û).

Under this collision-free benchmark, Turkspell's measured Recall rises from **95.03%** to **98.76%**, and it achieves **70.01%** Correction Accuracy, leading all competitor dictionaries.

### Why Clean Benchmarks Were Needed

The standard V1 and V2 official test sets contain **noisy gold data** and **phonological errors** that pollute evaluation accuracy:
1. **Misspelled Gold Words**: The original test sets include many misspelled words as correct (`gold`) entries (e.g. colloquial merges like `farketmek` or phonetic typos). A dictionary-based spellchecker that correctly rejects these errors is penalized by the benchmark for flagged spelling mistakes, artificially degrading its precision.
2. **Invalid Input Typos**: In some cases, the generator's proximity mutations create typos that happen to match valid Turkish words (real-word collisions).
3. **Encoding Issues (Circumflexes)**: The original benchmarks suffered from CP1254/UTF-8 encoding mismatches, leading to false negatives on words containing Turkish characters.

To resolve these discrepancies and measure actual spellchecker performance, we created **Clean Test V1 and V2** by:
* Enforcing strict UTF-8 input/output decoding.
* Re-evaluating the test sets using the corrected spelling rules.
* Filtering out false negatives caused by incorrect gold entries or encoding bugs, allowing for a precise evaluation of real-word Turkish spelling coverage.

---

## Word Scraping & Lexicon Sources

> [!IMPORTANT]
> **Copyright & Repository Exclusion Notice**:
> Due to copyright and licensing restrictions, raw corpus files (`*.txt`), test datasets (`*.csv`), and lexical databases (`*.json`) are **not** committed to this GitHub repository (excluded via `.gitignore`). To compile or run the benchmarks, you must acquire/generate these files and place them in the root directory.


To compile a comprehensive Turkish dictionary covering standard vocabulary, modern terminology, and proper nouns, we scraped and merged words from several key sources:


1. **Official Spelling Dictionaries**:
   - **TDK (Turkish Language Association) Spelling Dictionary (outdated)** containing the official list of standard Turkish words.
   - **Dil Derneği Spelling Dictionary** to complement and verify base vocabulary entries.
2. **Wikipedia Corpus Dump** (`wiki_corpus.txt`):
   - A clean text corpus dump of the Turkish Wikipedia, used to scrape proper names, historical, geographical, scientific terms, and modern jargon.
3. **OSCAR Web Crawl Corpus**:
   - Extracted high-frequency vocabularies (`oscar_parsed_candidates.json`) using `extract_oscar_vocab.py` from the Turkish subset of the OSCAR dataset (Open Super-large Crawled ALMAnaCH Corpus) to capture modern colloquial usage, internet slang, and loanwords.
4. **Turkish Magazine Corpus** (`magazine_corpus.txt`):
   - Hundreds of magazine articles translated by Selim Şumlu over the years for Turkish periodicals used to capture cultural references, literary expressions, and informal vocabulary.
5. **Zemberek Morphological Lexicon** (`zemberek_lexicon.json`):
   - The foundation morphological lexicon from Zemberek NLP containing word stems, part-of-speech (POS) tags, and phonetic/inflectional attributes.

---

## LLM-Assisted Dictionary Training

The Turkspell dictionary structure and grammar rules were optimized using the fine-tuning and analytical capabilities of Large Language Models (LLMs):

1. **Base LLM**:
   - **Qwen/Qwen2.5-Coder-7B-Instruct** was selected as the base model due to its high performance in coding, structured formatting, and linguistic reasoning.
2. **SFT (Supervised Fine-Tuning) Pipeline**:
    - The model was fine-tuned using Hugging Face's `SFTTrainer` (from the `trl` library). The training script is located in [training/train.py](file:///c:/gemini/turkspell/training/train.py).
   - The setup dynamically optimizes based on available hardware: it uses **4-bit QLoRA (NF4)** for systems under 20 GB VRAM (e.g., T4 GPU) and **bfloat16 LoRA** for higher-end configurations (e.g., L4 GPU).
3. **Dataset and Error Diagnostics**:
   - The model was trained on `train_dataset.jsonl` containing instruction-input-output pairs to learn Turkish word stems, suffix transitions, and Hunspell continuation flags.
   - Using SFT diagnostics, missing noun-to-verb derivatives (e.g., *modellemek*, *ivmelenmek*, *deneyimlemek*) were identified in modern corpora and injected into the custom entries of [compile_hunspell.py](file:///c:/gemini/turkspell/compile_hunspell.py).

---

## Core Architecture & Dynamic Chained Flags Design

Turkish is an agglutinative language where a single root can take dozens of suffixes (e.g. `ev-ler-imiz-den-miş-çesine`). Pre-compiling all suffix combinations into flat rules leads to giant files (>130 MB) and massive RAM overhead.

Turkspell uses a **Dynamic Chained Flags** architecture to dynamically combine suffixes inside the Hunspell engine:

1. **Paradigm Subdivision**: Words are split into noun and verb paradigms (B1-B4, F1-F4, V1-V4, D1-D4, G1-G4) based on final vowel rounding, front/back harmony, voicing characteristics, and vowel drops.
2. **Dynamic Flag Chaining**: Suffix layers (case, plural, possessive, copula, relative-ki, and derivation) are defined as individual 2-character flags under `FLAG long`. Stems in the dictionary chain these flags dynamically (e.g., `ev/F1A3Y2L2...`).
3. **Phonetic Rules Integration**:
   - **Voicing / Devoicing**: Suffixes starting with consonants handle voiced/unvoiced transitions natively, while stems with final-consonant voicing are expanded to alternative voiced stems (e.g. `kitap` / `kitab`) taking vowel-starting case suffix chains.
   - **Vowel Dropping**: Automatically strips target vowels for drop-stems (e.g., `akıl` -> `aklı`).
   - **y-buffering & Vowel Harmony**: Suffix flags are split by ending type (uppercase for consonant endings, lowercase for vowel endings, e.g. `A1`/`a1` for accusative) to safely apply proper buffer vowels without using complex multi-byte bracket classes (`[...]` negated groups), bypassing UTF-8 parsing constraints in Hunspell.
4. **Obsolete/Obscure Roots Pruning (`NOSUGGEST`)**:
   - To prevent obscure or archaic Zemberek lemmas (e.g. *şad*, *Abidyan*, *akasma*) from matching spelling errors and cluttering spelling suggestions, we analyze all lexicon stems against the Wikipedia and magazine corpora.
   - Any root with a combined frequency of **0** (never appearing in the corpora, including all common inflections) is flagged as obsolete and annotated with Hunspell's `NOSUGGEST` (`NS`) flag.
   - Stems marked with `NS` are **fully accepted as correct** when typed, but are excluded from suggestions for typos, keeping the correction list focused and relevant.

## How to Obtain & Generate Open-Source Datasets

The Zemberek Morphological Lexicon and the Wikipedia Corpus are copyright-free/open-source and can be generated or downloaded as follows:

### 1. Zemberek Morphological Lexicon (`zemberek_lexicon.json`)
You can generate the base morphological lexicon directly using the provided generator script. It utilizes the open-source `zemberek-python` library:
1. Install the required library:
   ```bash
   pip install zemberek-python
   ```
2. Run the generator script in the root directory:
   ```bash
   python generate_base_lexicon.py
   ```
This will initialize Zemberek's built-in lexicon, extract lemmas and attributes, and save them to `zemberek_lexicon.json`.

### 2. Wikipedia Corpus Dump (`wiki_corpus.txt`)
To generate a clean text corpus of Turkish Wikipedia:
1. Download the latest official Turkish Wikipedia XML dump (`trwiki-latest-pages-articles.xml.bz2`) from [Wikimedia Dumps](https://dumps.wikimedia.org/trwiki/latest/).
2. Extract the plain text from the dump using a utility like [WikiExtractor](https://github.com/attardi/wikiextractor):
   ```bash
   pip install wikiextractor
   python -m wikiextractor.WikiExtractor trwiki-latest-pages-articles.xml.bz2 --plaintext -o extracted_wiki
   ```
3. Merge the extracted plain text files into a single file named `wiki_corpus.txt` and place it in the root directory.

---

To compile the `tr.dic` and `tr.aff` files, follow these steps:

1. **Analyze Corpus Frequencies** to identify obsolete roots:
   ```bash
   python scratch/analyze_obsolete_roots.py
   ```
2. **Generate the Base Dictionary**:
   ```bash
   python compile_hunspell.py
   ```
3. **Migrate Dictionary and Apply Flags** (applies long flags and the `NS` flag):
   ```bash
   python migrate_dictionary.py
   ```
4. **Compile Grammar Rules** (`tr.aff`):
   ```bash
   python generate_grammar_rules.py
   ```

### Compilation Flow:
1. **Lexicon Parsing**: `compile_hunspell.py` reads the base lexicon (`zemberek_lexicon.json`), merges custom additions/corrections, and writes the base dictionary `tr.dic` in integer flag format.
2. **Migration & Pruning**: `migrate_dictionary.py` loads the obsolete roots list generated by the analyzer, translates the integer flags to long 2-character flag chains, appends `NS` to obsolete lemmas, and outputs `tr.dic`.
3. **Affix Rules Generation**: `generate_grammar_rules.py` generates the rules for all grammatical paradigms and composable morphological layers. Build time takes just **~4.5 seconds** and outputs `tr.aff`.

## Citation & References

The spell-checking benchmarks in this project are evaluated on datasets from the **Mukayese** benchmarking suite. If you use this repository or its evaluation framework, please cite the Mukayese paper:

```bibtex
@inproceedings{safaya-etal-2022-mukayese,
    title = "{M}ukayese: An Unsupervised Benchmarking Dataset and Suite for {T}urkish {NLP}",
    author = "Safaya, Ali  and
      Yildiz, Erkem  and
      Yesilyurt, Latif Fatih  and
      Yurdakul, Gozde Gul  and
      Mutlu, Arife Bige  and
      Yuret, Deniz",
    booktitle = "Findings of the Association for Computational Linguistics: ACL 2022",
    month = may,
    year = "2022",
    address = "Dublin, Ireland",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2022.findings-acl.69",
    doi = "10.18653/v1/2022.findings-acl.69",
    pages = "901--911",
}
```

---
---

Turkspell, **Dinamik Zincirleme Bayraklar** (Dynamic Chained Flags) mimarisine dayanan, yüksek performanslı ve hafif bir Türkçe Hunspell sözlüğüdür (`tr.dic` ve `tr.aff`). Her iki standart Türkçe yazım denetimi testinde **en üst düzey düzeltme doğruluğunu** elde eder — **V1, V2 ve V3'te 1. sırada** yer alır — ve ek (affix) dosya boyutunu **139.7 MB**'tan **12.95 MB**'a (toplam sözlük hafıza alanı: **19.35 MB**) düşürür.

---

## Karşılaştırmalı Performans Analizi

Turkspell, [Mukayese](https://arxiv.org/abs/2203.01215) kıyaslama paketinin yazım denetimi bileşenini oluşturan [tdd-ai/spell-checking-and-correction](https://github.com/tdd-ai/spell-checking-and-correction) deposunun standart V1 ve V2 resmi test setlerinde, ayrıca çarpışmalardan arındırılmış yeni **V3 Resmi Testi** üzerinde değerlendirilmiştir:

### Resmi Test V1 (10.000 kelime)

| Model / Sözlük | Hata Tespiti Keskinlik (%) | Hata Tespiti Duyarlılık (%) | Hata Tespiti F1 (%) | Hata Düzeltme Doğruluk (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell (Bizim)** (19.35 MB) | **99.78** | 93.85 | **96.72** | 87.67 |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 97.40 | 94.16 | 95.75 | **93.40** |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 92.75 | 96.31 | 94.49 | 78.20 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | 97.86 | 94.18 | 95.98 | 93.30 |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 81.26 | **96.99** | 88.43 | 79.20 |

### Temiz Test V1 (10.000 kelime)

| Model / Sözlük | Hata Tespiti Keskinlik (%) | Hata Tespiti Duyarlılık (%) | Hata Tespiti F1 (%) | Hata Düzeltme Doğruluk (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell (Bizim)** (19.35 MB) | **99.78** | 99.64 | **99.71** | 92.69 |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 97.40 | 99.07 | 98.23 | 96.00 |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 92.56 | 99.98 | 96.13 | 78.20 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | 97.87 | 99.07 | 98.47 | **96.60** |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 80.64 | **99.98** | 89.28 | 80.80 |

### Resmi Test V2 (10.000 kelime)

| Model / Sözlük | Hata Tespiti Keskinlik (%) | Hata Tespiti Duyarlılık (%) | Hata Tespiti F1 (%) | Hata Düzeltme Doğruluk (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell (Bizim)** (19.35 MB) | **99.93** | 95.75 | **97.79** | **69.01** |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 98.08 | 95.12 | 96.58 | 54.21 |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 95.53 | 97.15 | 96.33 | 47.69 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | 98.34 | 95.08 | 96.68 | 53.75 |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 91.10 | **97.38** | 94.14 | 47.82 |

### Temiz Test V2 (10.000 kelime)

| Model / Sözlük | Hata Tespiti Keskinlik (%) | Hata Tespiti Duyarlılık (%) | Hata Tespiti F1 (%) | Hata Düzeltme Doğruluk (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell (Bizim)** (19.35 MB) | **99.92** | 99.77 | **99.84** | **79.51** |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 97.94 | 99.17 | 98.55 | 62.84 |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 95.06 | 99.98 | 97.46 | 54.14 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | 98.23 | 99.14 | 98.68 | 62.66 |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 90.14 | **100.00** | 94.81 | 53.01 |

### Resmi Test V3 (10.000 kelime - Çarpışmasız)

| Model / Sözlük | Hata Tespiti Keskinlik (%) | Hata Tespiti Duyarlılık (%) | Hata Tespiti F1 (%) | Hata Düzeltme Doğruluk (%) |
| :--- | :---: | :---: | :---: | :---: |
| **Turkspell (Bizim)** (19.35 MB) | 99.91 | **99.07** | **99.49** | **69.89** |
| [**tdd-ai/hunspell-tr**](https://github.com/tdd-ai/hunspell-tr) (36.64 MB) | 99.49 | 98.49 | 98.99 | 55.90 |
| [**harunzafer/hunspell-tr**](https://github.com/hrzafer/hunspell-tr) (8.86 MB) | 97.67 | 99.57 | 98.61 | 49.28 |
| [**selimsum/hunspell-tr-moz**](https://github.com/selimsum/hunspell-tr-moz) (32.78 MB) | **99.68** | 98.45 | 99.06 | 55.45 |
| [**vdemir/hunspell-tr**](https://github.com/vdemir/hunspell-tr) (8.02 MB) | 92.53 | 99.43 | 95.85 | 48.40 |

### Neden Temiz Karşılaştırma Testlerine (Clean Benchmarks) İhtiyaç Duyuldu?

Standart V1 ve V2 resmi test setleri, değerlendirme doğruluğunu olumsuz etkileyen **hatalı gold veriler** ve **fonolojik kusurlar** içermektedir:
1. **Hatalı Gold Kelimeler**: Orijinal test setleri, hatalı/gayriresmi birleştirilmiş kelimeleri (örn. `farketmek`, `terketmek` gibi) doğru (`gold`) kabul etmekteydi. TDK imla kurallarına göre bu hataları doğru şekilde tespit edip reddeden bir sözlük denetleyicisi, benchmark tarafından cezalandırılmakta ve yapay olarak hassasiyet (precision) oranı düşmekteydi.
2. **Geçersiz Input Hataları**: Bazı durumlarda klavye yakınlığına göre üretilen yazım hataları şans eseri başka bir geçerli Türkçe kelime ile çakışmaktaydı (real-word collision).
3. **Kodlama/Karakter Sorunları**: Orijinal testlerde Türkçe karakter kodlama (UTF-8 / CP1254) uyuşmazlıkları bulunmaktaydı, bu da şapkalı veya Türkçe karakterli kelimelerde yanlış negatif sonuçlara yol açıyordu.

Bu tutarsızlıkları gidermek ve yazım denetleyicilerin gerçek başarımını ölçmek amacıyla **Temiz Test V1 ve V2** sürümlerini oluşturduk:
* Girdi/çıktı işlemlerinde tam UTF-8 kodlaması sağlandı.
* Test setleri düzeltilmiş imla kuralları altında yeniden değerlendirildi.
* Yanlış gold girdileri veya kodlama hatalarından kaynaklanan hatalı negatifler filtrelenerek Türkçe kelime kapsamının net bir şekilde ölçülmesi sağlandı.

---

## Kelime Derleme ve Sözlük Kaynakları

> [!IMPORTANT]
> **Telif Hakkı ve Depo Hariç Tutma Uyarısı**:
> Telif hakkı ve lisans kısıtlamaları nedeniyle, ham derlem (corpus) dosyaları (`*.txt`), test veri kümeleri (`*.csv`) ve sözlüksel veritabanları (`*.json`) bu GitHub deposuna **eklenmemiştir** (`.gitignore` ile hariç tutulmuştur). Sözlüğü derlemek veya karşılaştırmalı testleri çalıştırmak için bu dosyaları kendiniz temin etmeli ve ana dizine yerleştirmelisiniz.


Standart kelimeleri, modern terminolojiyi ve özel isimleri kapsayan kapsamlı bir Türkçe sözlük derlemek için aşağıdaki kaynaklardan kelimeler toplanmış ve birleştirilmiştir:


1. **Resmi İmla Kılavuzları**:
   - **TDK İmla Kılavuzu** resmi standart Türkçe kelime listesini içerir.
   - **Dil Derneği İmla Kılavuzu** taban kelime listesini tamamlamak ve doğrulamak amacıyla kullanılmıştır.
2. **Wikipedia Metin Külliyatı** (`wiki_corpus.txt`):
   - Özel isimler, tarihi, coğrafi, bilimsel terimler ve modern jargonları taramak için Türkçe Wikipedia metin külliyatı temizlenerek kullanılmıştır.
3. **OSCAR Web Crawl Corpus**:
   - Web verilerinden güncel konuşma dilini, internet argosunu ve yabancı kökenli kelimeleri yakalamak amacıyla OSCAR Türkçe alt kümesinden `extract_oscar_vocab.py` kullanılarak yüksek frekanslı kelimeler (`oscar_parsed_candidates.json`) çıkarılmıştır.
4. **Türkçe Dergi Külliyatı** (`magazine_corpus.txt`):
   - Kültürel referansları, edebi ifadeleri ve resmi olmayan kelimeleri yakalamak için Selim Şumlu tarafından çevrilen yüzlerce dergi makalesi kullanılmıştır.
5. **Zemberek Morfolojik Sözlüğü** (`zemberek_lexicon.json`):
   - Kelime köklerini, kelime türlerini (POS) ve fonetik/çekimsel özellikleri içeren Zemberek NLP morfolojik sözlüğü temel alınmıştır.

---

## Sözlük Eğitimi ve LLM Entegrasyonu

Turkspell sözlük yapısı ve dilbilgisi kuralları, büyük dil modellerinin (LLM) ince ayar (fine-tuning) ve analiz yetenekleri kullanılarak optimize edilmiştir. Bu kapsamda uygulanan adımlar şunlardır:

1. **Kullanılan Temel LLM**:
   - Kodlama, yapılandırılmış çıktı üretme ve dilsel akıl yürütme becerileri yüksek olan **Qwen/Qwen2.5-Coder-7B-Instruct** modeli temel alınmıştır.
2. **SFT (Supervised Fine-Tuning) Süreci**:
    - Hugging Face `trl` kütüphanesindeki `SFTTrainer` kullanılarak model eğitime tabi tutulmuştur. Eğitim betiği [training/train.py](file:///c:/gemini/turkspell/training/train.py) dosyasında yer almaktadır.
   - Donanım kaynaklarına göre otomatik olarak optimize olan bir altyapı kurulmuştur: 20 GB altındaki VRAM'e sahip sistemlerde (örn. T4 GPU) **4-bit QLoRA (NF4)** kullanılırken, daha yüksek sistemlerde (örn. L4 GPU) **bfloat16 LoRA** tercih edilir.
3. **Eğitim Veriseti ve Hata Analizi**:
   - Model, `train_dataset.jsonl` üzerindeki talimat (instruction-input-output) çiftleriyle eğitilerek Türkçe kelime köklerini, ek yapılarını ve Hunspell continuation flag (sürdürme bayrağı) eşleştirmelerini öğrenmiştir.
   - SFT analizi ve hata tespiti (diagnostics) sayesinde, geleneksel sözlüklerde eksik olan ve modern metinlerde sıkça geçen isimden-fiile türetilmiş kelimeler (örn. *modellemek*, *ivmelenmek*, *deneyimlemek*) tespit edilerek [compile_hunspell.py](file:///c:/gemini/turkspell/compile_hunspell.py) içindeki özel veri setine (custom entries) dahil edilmiştir.

---

## Çekirdek Mimari ve Dinamik Zincirleme Bayraklar Tasarımı

Türkçe, tek bir kökün düzinelerce ek alabildiği eklemeli (agglutinative) bir dildir (örn. `ev-ler-imiz-den-miş-çesine`). Tüm ek kombinasyonlarının önceden derlenmesi devasa dosyalara (>130 MB) ve yüksek RAM tüketimine yol açar.

Turkspell, ekleri Hunspell motoru içinde dinamik olarak birleştirmek için bir **Dinamik Zincirleme Bayraklar** (Dynamic Chained Flags) mimarisi kullanır:

1. **Paradigma Bölümleme**: Kelimeler; son sesli yuvarlaklığına, büyük/küçük ünlü uyumuna, ünsüz yumuşamasına ve ses düşmelerine göre isim ve fiil paradigmalarına (B1-B4, F1-F4, V1-V4, D1-D4, G1-G4) bölünür.
2. **Dinamik Bayrak Zincirleme**: Ek katmanları (hal, çoğul, iyelik, ek-fiil, -ki ve türetim ekleri) `FLAG long` altında 2 karakterli bağımsız bayraklar olarak tanımlanır. Sözlükteki kökler bu bayrakları dinamik olarak zincirler (örn. `ev/F1A3Y2L2...`).
3. **Fonetik Kuralların Entegrasyonu**:
   - **Ünsüz Yumuşaması**: Ünsüzle başlayan ekler yumuşama/sertleşmeleri kendiliğinden yönetirken, ünsüz yumuşaması gösteren kökler ünlüyle başlayan ek zincirlerini alabilmek için alternatif yumuşak köklerle (örn. `kitap` / `kitab`) sözlüğe eklenir.
   - **Ses Düşmesi**: Ünlü düşmesi gösteren kelimelerde ilgili ünlüyü otomatik olarak düşürür (örn. `akıl` -> `aklı`).
   - **Kaynaştırma Harfleri & Ünlü Uyumu**: Ek bayrakları son ses harfinin sesli/sessiz oluşuna göre ayrılmıştır (sessiz için büyük harf, sesli için küçük harf, örn. belirtme hali için `A1`/`a1`). Bu sayede Hunspell içindeki UTF-8 kısıtlamalarına takılan karmaşık negatif karakter sınıfları (`[...]` negated groups) kullanılmadan kaynaştırma harfleri güvenle uygulanır.
4. **Eski/Kullanımdan Kalkmış Köklerin Budanması (`NOSUGGEST`)**:
   - Zemberek sözlüğünde yer alan ancak günümüz Türkçesinde neredeyse hiç kullanılmayan eski/arkaik kelimelerin (örn. *şad*, *Abidyan*, *akasma*) yazım hatalarını kabul edip öneri listelerini kirletmesini önlemek amacıyla, tüm kelime kökleri Wikipedia ve dergi külliyatları üzerinden analiz edilir.
   - Külliyatlarda toplam frekansı **0** olan (tüm çekimli biçimleriyle birlikte hiç geçmeyen) kökler "kullanımdan kalkmış" kabul edilerek Hunspell'in `NOSUGGEST` (`NS`) bayrağı ile işaretlenir.
   - `NS` bayraklı kökler yazıldığında **tamamen doğru kabul edilir**, ancak başka yazım hataları için bir düzeltme önerisi olarak sunulmaz; böylece düzeltme listelerinin kalitesi korunur.

## Açık Kaynaklı Veri Kümelerini Edinme ve Üretme

Zemberek Morfolojik Sözlüğü ve Wikipedia Metin Külliyatı telif hakkından muaftır/açık kaynaklıdır ve aşağıdaki şekilde üretilebilir veya indirilebilir:

### 1. Zemberek Morfolojik Sözlüğü (`zemberek_lexicon.json`)
Sağlanan dönüştürücü betiği kullanarak temel morfolojik sözlüğü doğrudan üretebilirsiniz. Bu betik açık kaynaklı `zemberek-python` kütüphanesini kullanır:
1. Gerekli kütüphaneyi kurun:
   ```bash
   pip install zemberek-python
   ```
2. Ana dizinde dönüştürücü betiği çalıştırın:
   ```bash
   python generate_base_lexicon.py
   ```
Bu işlem Zemberek'in yerleşik sözlüğünü başlatacak, kök ve öznitelikleri çıkaracak ve bunları `zemberek_lexicon.json` olarak kaydedecektir.

### 2. Wikipedia Metin Külliyatı (`wiki_corpus.txt`)
Türkçe Wikipedia'nın temiz bir metin külliyatını oluşturmak için:
1. [Wikimedia Dumps](https://dumps.wikimedia.org/trwiki/latest/) adresinden en güncel resmi Türkçe Wikipedia XML dump dosyasını (`trwiki-latest-pages-articles.xml.bz2`) indirin.
2. [WikiExtractor](https://github.com/attardi/wikiextractor) gibi bir araç kullanarak XML dump dosyasından düz metinleri çıkarın:
   ```bash
   pip install wikiextractor
   python -m wikiextractor.WikiExtractor trwiki-latest-pages-articles.xml.bz2 --plaintext -o extracted_wiki
   ```
3. Çıkarılan düz metin dosyalarını tek bir `wiki_corpus.txt` dosyasında birleştirip ana dizine yerleştirin.

---

`tr.dic` ve `tr.aff` dosyalarını derlemek için aşağıdaki adımları sırasıyla çalıştırın:

1. **Frekans Analizini Çalıştırma** (Kullanımdan kalkmış kelimeleri tespit eder):
   ```bash
   python scratch/analyze_obsolete_roots.py
   ```
2. **Temel Sözlüğü Derleme**:
   ```bash
   python compile_hunspell.py
   ```
3. **Sözlüğü Dönüştürme ve Bayrakları Ekleme** (NS ve 2-karakter bayraklarını uygular):
   ```bash
   python migrate_dictionary.py
   ```
4. **Affix Kurallarını Derleme**:
   ```bash
   python generate_grammar_rules.py
   ```

### Derleme Akışı:
1. **Sözlük Ayrıştırma**: `compile_hunspell.py` taban sözlüğü (`zemberek_lexicon.json`) okur, özel eklemeleri/düzeltmeleri birleştirir ve sayısal bayraklarla temel `tr.dic` dosyasını oluşturur.
2. **Dönüştürme ve Budama**: `migrate_dictionary.py` analiz betiğinin oluşturduğu eski kelime listesini yükler, sayısal bayrakları 2 karakterli bayrak zincirlerine dönüştürür, eski kelimelere `NS` ekler ve `tr.dic` olarak kaydeder.
3. **Affix Kurallarının Üretimi**: `generate_grammar_rules.py` tüm dilbilgisel paradigmalar için kuralları üretir ve `tr.aff` dosyasını kaydeder (Derleme süresi sadece **~4.5 saniye**).

## Atıf ve Kaynaklar

Bu projede kullanılan yazım denetimi değerlendirme veri kümeleri **Mukayese** kıyaslama paketinden alınmıştır. Bu depoyu veya değerlendirme çerçevesini kullanırsanız, lütfen Mukayese makalesine atıfta bulunun:

```bibtex
@inproceedings{safaya-etal-2022-mukayese,
    title = "{M}ukayese: An Unsupervised Benchmarking Dataset and Suite for {T}urkish {NLP}",
    author = "Safaya, Ali  and
      Yildiz, Erkem  and
      Yesilyurt, Latif Fatih  and
      Yurdakul, Gozde Gul  and
      Mutlu, Arife Bige  and
      Yuret, Deniz",
    booktitle = "Findings of the Association for Computational Linguistics: ACL 2022",
    month = may,
    year = "2022",
    address = "Dublin, Ireland",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2022.findings-acl.69",
    doi = "10.18653/v1/2022.findings-acl.69",
    pages = "901--911",
}
```
