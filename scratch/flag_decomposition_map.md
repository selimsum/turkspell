# Flag Decomposition Map: Old Paradigm → New Chained FLAG long

## Key Insight (from POC)
Hunspell `FLAG long` confirmed working:
- Each 2-char flag is independent.
- A dictionary entry `word/PFACDALO` applies flags PF, AC, DA, LO simultaneously.
- Each flag produces its own set of valid forms.
- Possessive+case forms must be fully expanded within their flag (not composed at runtime).
- This is NOT Hunspell's own suffix chaining — it's parallel flag application.

---

## New Flag Namespace (FLAG long)

### Stem Class Flags (vowel harmony + phonological rules)
These replace the old integer paradigm flags. They are now **slim** — they encode only
the phonological alternation rule for a given stem class. All case/possessive/copula
forms come from the morphological layer flags below.

| New Flag | Old Flag(s) | Stem Class | Example |
|---|---|---|---|
| `B1` | 1 | Back, consonant-ending, unrounded | yap, kal, taş |
| `B2` | 101 | Back, consonant-ending, rounded | uç, bul |
| `F1` | 2 | Front, consonant-ending, unrounded | git, gel, ev |
| `F2` | 102 | Front, consonant-ending, rounded | düş, gör, göz |
| `B3` | 3 | Back, vowel-ending, unrounded | oda, araba |
| `B4` | 103 | Back, vowel-ending, rounded | kutu, sabun |
| `F3` | 4 | Front, vowel-ending, unrounded | kedi, dere |
| `F4` | 104 | Front, vowel-ending, rounded | ütü, köprü |
| `V1` | 5 | Back, consonant-end, unrounded, voicing | kitap→kitabı, renk→rengi |
| `V2` | 105 | Back, consonant-end, rounded, voicing | dolap→dolabı |
| `V3` | 6 | Front, consonant-end, unrounded, voicing | ip→ibi? (rare) |
| `V4` | 106 | Front, consonant-end, rounded, voicing | |
| `D1` | 7 | Back, consonant-end, unrounded, vowel drop | ağız→ağzı, oğul→oğlu |
| `D2` | 107 | Back, consonant-end, rounded, vowel drop | |
| `D3` | 8 | Front, consonant-end, unrounded, vowel drop | isim→ismi, cisim |
| `D4` | 108 | Front, consonant-end, rounded, vowel drop | |
| `C1` | 13 | Back compound (unrounded) | ardıkuşu (3sg poss compound) |
| `C2` | 113 | Back compound (rounded) | |
| `C3` | 14 | Front compound (unrounded) | |
| `C4` | 114 | Front compound (rounded) | |
| `G1` | 18 | Back, consonant-end, unrounded, doubling | hak→hakkı |
| `G2` | 118 | Back, consonant-end, rounded, doubling | |
| `G3` | 19 | Front, consonant-end, unrounded, doubling | ret→reddi |
| `G4` | 119 | Front, consonant-end, rounded, doubling | |

### Verb Stem Class Flags
| New Flag | Old Flag(s) | Verb Class | Example |
|---|---|---|---|
| `VB` | 9 | Back consonant stem | yazmak, almak |
| `VR` | 109 | Back consonant stem, rounded | okumak |
| `VF` | 10 | Front consonant stem | gelmek, görmek |
| `VG` | 110 | Front consonant stem, rounded | söylemek |
| `VA` | 11 | Back vowel stem | aramak |
| `VS` | 111 | Back vowel stem, rounded | okumak (vowel-stem) |
| `VE` | 12 | Front vowel stem | beklemek |
| `VH` | 112 | Front vowel stem, rounded | söylemek (vowel-stem) |
| `VK` | 15 | Back consonant stem, voicing | gitmek, etmek, tatmak |
| `VL` | 115 | Back consonant stem, voicing, rounded | gütmek |
| `VM` | 16 | Front consonant stem, voicing | |
| `VN` | 116 | Front consonant stem, voicing, rounded | |
| `VY` | 17 | Narrowing stem | demek, yemek |

### Prefix Flag
| New Flag | Old Flag | Description |
|---|---|---|
| `PX` | 90 | Metric/loan prefixes (mili-, mikro-, kilo-, …) |

---

## Morphological Layer Flags

These are NEW flags. They contain COMPLETE expanded forms for their morphological path.
Each flag must cover both voiced/unvoiced consonant endings AND vowel endings.

### Noun Case Flags (Singular)
These flags are applied per harmony class (back/front/rounded/unrounded).
**Design decision:** Use ONE set of case flags with regex conditions to handle all 4 vowel harmony classes.

| New Flag | Morpheme | Rules strategy |
|---|---|---|
| `AC` | Accusative -yI/-I | -yi (front), -yı (back), -yü (front-round), -yu (back-round); -i/-ı/-ü/-u for cons-ending |
| `DA` | Dative -yA/-A | -ye/-ya/-e/-a with y-buffer for vowel stems |
| `LO` | Locative -DA | -de/-da/-te/-ta with voiced/unvoiced distinction |
| `AB` | Ablative -DAn | -den/-dan/-ten/-tan |
| `GE` | Genitive -nIn/-In | -nin/-nın/-nün/-nun (vowel stems); -in/-ın/-ün/-un (cons stems) |
| `IN` | Instrumental -ylA/-lA | -yle/-yla/-le/-la |
| `EQ` | Equative -CA | -ce/-ca/-çe/-ça |

### Noun Plural Flags
These flags produce ALL valid forms starting with the plural morpheme.

| New Flag | Description |
|---|---|
| `PF` | Front plural: -ler + all cases (leri, lere, lerde, lerden, lerin, lerle, lerce) |
| `PB` | Back plural: -lar + all cases (ları, lara, larda, lardan, ların, larla, larca) |

### Possessive Flags (Singular base)
Each flag produces the possessive marker + all valid case forms that follow it.

| New Flag | Morpheme | Description |
|---|---|---|
| `P1` | -Im/-m | 1sg possessive: evim, evimde, evime, evimi, evimden, evimin, evimle |
| `P2` | -In/-n | 2sg possessive: evin, evinde, evine, evini, evinden, evinin, evinle |
| `P3` | -I/-sI | 3sg possessive: evi/evsi→evi, evinde, evine, evini, evinden, evinin (n-buffer) |
| `PM` | -ImIz/-mIz | 1pl possessive: evimiz, evimizde, ... |
| `PN` | -InIz/-nIz | 2pl possessive: eviniz, evinizde, ... |
| `PP` | -lArI | 3pl possessive: evleri, evlerinde, evlerine, evlerini, ... |

### Plural Possessive Flags
| New Flag | Description |
|---|---|
| `Q1` | -lArIm: 1sg possessive of plural |
| `Q2` | -lArIn: 2sg possessive of plural |
| `Q3` | -lArI (same as 3pl poss, listed under PP) |
| `QM` | -lArImIz: 1pl possessive of plural |
| `QN` | -lArInIz: 2pl possessive of plural |

### Copula Flag
| New Flag | Description |
|---|---|
| `CL` | All nominal copulas: -dIr, -dI, -dIm, -dIn, ..., -mIş, -mIşIm, ..., -sA, ..., -yken, -ydI, ... |

### Relative-ki Flag
| New Flag | Description |
|---|---|
| `KI` | Relative -ki: applied to locative/genitive forms. Produces -ki, -kiler, -kileri, -kilerde, ... |

### Derivation Flags (1-level: noun → derived adj/noun)
| New Flag | Morpheme | Produces |
|---|---|---|
| `LI` | -lI | adj from noun: evli, evliydi, evliyse; then case flags chain |
| `SZ` | -sIz | without: evsiz, evsizde, evsizler |
| `LK` | -lIk | abstract noun: evlik, evliğin, evliğe (with voicing k→ğ) |
| `CI` | -CI | agentive noun: evci (rare for ev but general pattern) |
| `CK` | -cIk | diminutive: evcik |

### 2-Level Derivation Flags (noun → verb-forming → re-nominalizing)
These implement the requested 2-level derivation.

| New Flag | Morpheme chain | Example |
|---|---|---|
| `DL` | -lAş (verb-forming) | güzel → güzelleş → güzelleşme |
| `DT` | -lAştIr (causative verb) | güzel → güzelleştir → güzelleştirme |
| `DE` | -lEn (reflexive verb) | güzel → güzellenme |
| `DM` | Verb nominals from derivations | güzelleştirme → güzelleştirmenin |

---

## Full Dictionary Entry Structure (Target)

### Noun entry example: `kitap` (back, consonant, voicing: k→ğ, p→b)
```
kitap/V1ACDALOBGEINPBP1P2P3PMQMPNQNPPCLKILILISZCZLKCI
```
Broken down:
- `V1` = back consonant, unrounded, voicing stem class
- `AC` = accusative (produces: kitabı)
- `DA` = dative (produces: kitaba)
- `LO` = locative (produces: kitapta)
- `AB` = ablative (produces: kitaptan)
- `GE` = genitive (produces: kitabın)
- `IN` = instrumental (produces: kitapla)
- `PB` = back plural + all plural cases
- `P1`–`PP` = all possessives
- `QM`, `QN` = plural possessives
- `CL` = copulas
- `KI` = relative -ki
- `LI`,`SZ`,`LK`,`CI` = derivations

### Verb entry example: `yazmak` (back consonant verb)
```
yazmak/VB
```
VB already contains: ALL tense/person forms, negatives, verb nominals, gerunds.

---

## Size Estimation

| Flag Group | Flags | Rules/flag | Total rules |
|---|---|---|---|
| Stem class (nouns) | 20 | ~20 | 400 |
| Case flags (singular) | 7 | ~8 | 56 |
| Plural flags | 2 | ~15 | 30 |
| Possessive flags | 8 | ~50 | 400 |
| Copula flag | 1 | ~70 | 70 |
| Relative-ki | 1 | ~20 | 20 |
| Derivation flags | 7 | ~30 | 210 |
| Verb stem flags | 13 | ~500 | 6,500 |
| Verb nominal flags | 4 | ~50 | 200 |
| Prefix flag | 1 | 22 | 22 |
| **Total** | ~64 | — | **~7,900** |

Compare to current: **~775,000 rules** (37 flags × avg 21,000 rules)
**Estimated reduction: ~99%**
