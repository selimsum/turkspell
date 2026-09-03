# Turkspell OSCAR 10M Corpus Cleanup & Missing Vocabulary Report

- **Execution Timestamp**: 2026-09-03 23:29:20
- **Corpus Source**: `raw_data/oscar_10m_corpus_frequencies.json`
- **Active Dictionary Tested**: Turkspell v0.6 Gold (`tr.aff` / `tr.dic`)

---

## 1. Corpus Sanitization Summary

| Category | Count | Percentage |
| :--- | :--- | :--- |
| **Raw Initial Entries** | **1,969,242** | 100.00% |
| Combining Dot Artifacts Normalized (`\u0307`) | 80,319 | 4.08% |
| Unique Entries After Normalization | 1,910,006 | 96.99% |
| **Removed English / Foreign Words** | **84,968** | **4.45%** |
| **Removed Proper Names & Inflections** | **26,446** | **1.38%** |
| **Removed Redundant Noise / Tokens** | **36,615** | **1.92%** |
| **Clean Turkish Vocabulary Retained** | **1,761,977** | **92.25%** |

### Sample Removed Tokens

#### Removed English Words (Top 20 by Frequency)
| Word | Frequency | Reason |
| :--- | :--- | :--- |
| `web` | 84,663 | contains_qwx |
| `escort` | 47,039 | english_word |
| `online` | 36,051 | english_word |
| `www` | 33,721 | contains_qwx |
| `the` | 24,896 | english_word |
| `dir` | 18,583 | english_word |
| `windows` | 13,830 | contains_qwx |
| `ii` | 12,535 | english_word |
| `android` | 12,010 | english_word |
| `twitter` | 10,345 | contains_qwx |
| `and` | 10,084 | english_word |
| `new` | 9,646 | contains_qwx |
| `ler` | 8,931 | english_word |
| `hotel` | 8,383 | english_word |
| `lar` | 7,336 | english_word |
| `linux` | 7,245 | contains_qwx |
| `play` | 7,043 | english_word |
| `pro` | 6,928 | english_word |
| `hosting` | 6,829 | english_word |
| `tic` | 5,862 | english_word |

#### Removed Proper Names & Inflections (Top 20 by Frequency)
| Word | Frequency | Reason |
| :--- | :--- | :--- |
| `mehmet` | 32,316 | exclusive_proper_name |
| `mustafa` | 27,651 | exclusive_proper_name |
| `erdoğan` | 25,560 | exclusive_proper_name |
| `ahmet` | 23,845 | exclusive_proper_name |
| `rusya` | 21,686 | exclusive_proper_name |
| `atatürk` | 20,821 | exclusive_proper_name |
| `vakfı` | 15,003 | inflected_proper_vakf |
| `covid` | 14,849 | exclusive_proper_name |
| `instagram` | 13,974 | exclusive_proper_name |
| `casino` | 13,946 | exclusive_proper_name |
| `hasan` | 12,758 | exclusive_proper_name |
| `ibrahim` | 11,710 | exclusive_proper_name |
| `ömer` | 11,687 | exclusive_proper_name |
| `facebook` | 11,403 | exclusive_proper_name |
| `irak` | 10,496 | exclusive_proper_name |
| `muhammed` | 9,937 | exclusive_proper_name |
| `hüseyin` | 9,932 | exclusive_proper_name |
| `dır` | 9,827 | exclusive_proper_name |
| `tayyip` | 9,117 | exclusive_proper_name |
| `galatasaray` | 8,978 | exclusive_proper_name |

#### Removed Redundant Noise & Fragments (Top 20 by Frequency)
| Word | Frequency | Reason |
| :--- | :--- | :--- |
| `nin` | 232,718 | suffix_fragment |
| `a` | 188,765 | single_letter |
| `nın` | 170,615 | suffix_fragment |
| `e` | 165,944 | single_letter |
| `i` | 110,402 | single_letter |
| `com` | 73,899 | web_artifact |
| `nde` | 67,167 | suffix_fragment |
| `nun` | 63,089 | suffix_fragment |
| `dr` | 62,507 | no_vowels |
| `ı` | 57,888 | single_letter |
| `nda` | 49,131 | suffix_fragment |
| `s` | 47,028 | single_letter |
| `tl` | 46,070 | no_vowels |
| `c` | 45,207 | single_letter |
| `b` | 39,658 | single_letter |
| `amp` | 36,189 | web_artifact |
| `m` | 36,021 | single_letter |
| `daki` | 35,732 | suffix_fragment |
| `alt` | 32,242 | web_artifact |
| `deki` | 30,388 | suffix_fragment |

---

## 2. Turkspell Verification & Accuracy Metrics

All cleaned Turkish words were evaluated directly against Turkspell (`hunspell -d tr -l`):

| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total Clean Words Tested** | **1,761,977** | 100.00% |
| **Accepted by Turkspell** | **910,957** | **51.70%** |
| **Missing / Failing in Turkspell** | **851,020** | **48.30%** |

### Missing Words Breakdown by Frequency Tier

| Frequency Tier | Unique Words | Total Corpus Occurrences | Description |
| :--- | :--- | :--- | :--- |
| **Very High (>= 10,000)** | 10 | 186,656 | Key candidates for dictionary updates |
| **High (1,000 - 9,999)** | 349 | 735,306 | Key candidates for dictionary updates |
| **Medium (100 - 999)** | 5,396 | 1,341,040 | Key candidates for dictionary updates |
| **Low (10 - 99)** | 52,216 | 1,334,907 | Key candidates for dictionary updates |
| **Rare (1 - 9)** | 793,049 | 1,393,139 | Key candidates for dictionary updates |

---

## 3. Top 100 Highest-Frequency Missing/Failing Words

The following words are high-frequency tokens in the cleaned Turkish web corpus that Turkspell currently rejects:

| Rank | Word | Corpus Frequency | Observed Linguistic Category |
| :--- | :--- | :--- | :--- |
| 1 | **dan** | 74,838 | Short root / particle |
| 2 | **seo** | 23,693 | Short root / particle |
| 3 | **imkanı** | 14,081 | Vocabulary Gap |
| 4 | **le** | 11,220 | Short root / particle |
| 5 | **adeta** | 10,730 | Vocabulary Gap |
| 6 | **idi** | 10,690 | Verb Inflection |
| 7 | **cok** | 10,591 | Short root / particle |
| 8 | **osman** | 10,401 | Vocabulary Gap |
| 9 | **blog** | 10,351 | Short root / particle |
| 10 | **kovid** | 10,061 | Vocabulary Gap |
| 11 | **isparta** | 8,767 | Vocabulary Gap |
| 12 | **icin** | 8,762 | Short root / particle |
| 13 | **şikayet** | 8,244 | Vocabulary Gap |
| 14 | **birbitki** | 7,673 | Vocabulary Gap |
| 15 | **mekan** | 7,578 | Vocabulary Gap |
| 16 | **büyüksehir** | 7,343 | Vocabulary Gap |
| 17 | **sayili** | 7,092 | Vocabulary Gap |
| 18 | **tadını** | 6,934 | Vocabulary Gap |
| 19 | **fetö** | 6,905 | Short root / particle |
| 20 | **lı** | 6,573 | Short root / particle |
| 21 | **nci** | 6,264 | Short root / particle |
| 22 | **zeka** | 6,246 | Short root / particle |
| 23 | **iphone** | 6,156 | Vocabulary Gap |
| 24 | **be** | 5,998 | Short root / particle |
| 25 | **islâm** | 5,789 | Circumflex spelling |
| 26 | **camii** | 5,625 | Vocabulary Gap |
| 27 | **hikaye** | 5,450 | Vocabulary Gap |
| 28 | **hakkinda** | 5,121 | Noun Inflection / Agglutination |
| 29 | **rüzgar** | 5,002 | Vocabulary Gap |
| 30 | **hikayesi** | 4,935 | Vocabulary Gap |
| 31 | **öztürk** | 4,926 | Vocabulary Gap |
| 32 | **sinan** | 4,796 | Vocabulary Gap |
| 33 | **imalatı** | 4,661 | Vocabulary Gap |
| 34 | **hamdi** | 4,604 | Verb Inflection |
| 35 | **buradasiniz** | 4,582 | Vocabulary Gap |
| 36 | **aydin** | 4,548 | Vocabulary Gap |
| 37 | **plani** | 4,477 | Vocabulary Gap |
| 38 | **kılıçdaroğlu** | 4,412 | Vocabulary Gap |
| 39 | **ayhan** | 4,382 | Vocabulary Gap |
| 40 | **işık** | 4,294 | Short root / particle |
| 41 | **bitcoin** | 4,184 | Vocabulary Gap |
| 42 | **usb** | 4,047 | Short root / particle |
| 43 | **salih** | 3,962 | Vocabulary Gap |
| 44 | **erol** | 3,844 | Short root / particle |
| 45 | **ekrem** | 3,823 | Vocabulary Gap |
| 46 | **özdemir** | 3,800 | Vocabulary Gap |
| 47 | **tadı** | 3,734 | Short root / particle |
| 48 | **faruk** | 3,718 | Vocabulary Gap |
| 49 | **adnan** | 3,716 | Vocabulary Gap |
| 50 | **ceo** | 3,690 | Short root / particle |
| 51 | **bekir** | 3,653 | Vocabulary Gap |
| 52 | **tir** | 3,632 | Short root / particle |
| 53 | **lerde** | 3,593 | Vocabulary Gap |
| 54 | **leri** | 3,504 | Short root / particle |
| 55 | **teşkilatı** | 3,498 | Vocabulary Gap |
| 56 | **iddaa** | 3,476 | Vocabulary Gap |
| 57 | **ibn** | 3,449 | Short root / particle |
| 58 | **numarali** | 3,322 | Vocabulary Gap |
| 59 | **özcan** | 3,271 | Vocabulary Gap |
| 60 | **nuri** | 3,266 | Short root / particle |
| 61 | **tarafindan** | 3,245 | Vocabulary Gap |
| 62 | **imkanları** | 3,181 | Vocabulary Gap |
| 63 | **nasil** | 3,142 | Vocabulary Gap |
| 64 | **ünal** | 3,133 | Short root / particle |
| 65 | **erp** | 3,123 | Short root / particle |
| 66 | **ersoy** | 3,096 | Vocabulary Gap |
| 67 | **morhipo** | 3,061 | Vocabulary Gap |
| 68 | **belediyespor** | 3,039 | Vocabulary Gap |
| 69 | **erkan** | 2,982 | Vocabulary Gap |
| 70 | **özkan** | 2,961 | Vocabulary Gap |
| 71 | **ba** | 2,953 | Short root / particle |
| 72 | **turgut** | 2,951 | Vocabulary Gap |
| 73 | **akif** | 2,910 | Short root / particle |
| 74 | **uludağ** | 2,838 | Vocabulary Gap |
| 75 | **yanısıra** | 2,808 | Vocabulary Gap |
| 76 | **ucu** | 2,805 | Short root / particle |
| 77 | **itso** | 2,762 | Short root / particle |
| 78 | **lık** | 2,749 | Short root / particle |
| 79 | **demirel** | 2,721 | Vocabulary Gap |
| 80 | **degisikligi** | 2,691 | Vocabulary Gap |
| 81 | **imkansız** | 2,677 | Vocabulary Gap |
| 82 | **kapadokya** | 2,664 | Vocabulary Gap |
| 83 | **hakk** | 2,658 | Short root / particle |
| 84 | **oktay** | 2,576 | Vocabulary Gap |
| 85 | **herşeyi** | 2,569 | Vocabulary Gap |
| 86 | **islem** | 2,548 | Vocabulary Gap |
| 87 | **gazze** | 2,538 | Vocabulary Gap |
| 88 | **antalyaspor** | 2,513 | Vocabulary Gap |
| 89 | **ce** | 2,465 | Adverbial / Derivational suffix |
| 90 | **pirha** | 2,424 | Vocabulary Gap |
| 91 | **hikayeleri** | 2,417 | Vocabulary Gap |
| 92 | **larda** | 2,397 | Noun Inflection / Agglutination |
| 93 | **hoşgeldiniz** | 2,391 | Vocabulary Gap |
| 94 | **mahkum** | 2,365 | Vocabulary Gap |
| 95 | **afrin** | 2,338 | Vocabulary Gap |
| 96 | **ercan** | 2,328 | Vocabulary Gap |
| 97 | **karari** | 2,312 | Vocabulary Gap |
| 98 | **fahrettin** | 2,295 | Vocabulary Gap |
| 99 | **id** | 2,294 | Short root / particle |
| 100 | **hes** | 2,281 | Short root / particle |

---

## 4. Key Findings & Recommendations for Turkspell

1. **High-Frequency Agglutination & Suffix Rules**:
   - Several missing words are legitimate multi-affix agglutinations (e.g. copular `-ken`, `-ce`, specialized participle formations) that can be enabled in `tr.aff` without bloating `tr.dic`.
2. **Missing Root Stems**:
   - Top unflagged missing items reveal legitimate contemporary Turkish root words, compounds written as single words, and widely accepted loanwords.
3. **Circumflex Regularization**:
   - Unhatted forms of mandatory hatted words in web text naturally appear with high frequency due to informal keyboard usage.

> [!NOTE]
> The cleaned frequency dataset has been saved to `raw_data/oscar_10m_corpus_frequencies.json`.
> The full missing word list (851,020 entries) can be used for automated rule mining and dictionary enrichment.
