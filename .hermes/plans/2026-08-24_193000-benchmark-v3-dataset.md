# Turkspell Cross-Dictionary Benchmark Dataset — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Generate a new, independent benchmark dataset (`benchmark/turkspell_bench_v3/`) that fairly compares Turkish Hunspell dictionaries (Turkspell vs tdd-ai vs harunzafer vs selimsum/hunspell-tr-moz vs vdemir) on detection precision/recall and correction accuracy @1/@3, with an auditable, reproducible generation pipeline.

**Architecture:** A generator script mines real error patterns from `rejected_words.csv` (1.17M corpus-rejected words with frequencies) plus keyboard-proximity and diacritic mutations of authority wordlists (TDK + Dil Derneği), filters out "false typos" (mutated forms that happen to be valid words in ANY competitor dictionary — the collision problem documented in README), and emits a versioned CSV dataset + a runner that evaluates all installed dictionaries identically. The dataset is committed to the repo; corpora are not needed to regenerate it deterministically (seeded RNG).

**Tech Stack:** Python 3.11 (stdlib only for generator: csv, json, random with fixed seed), spylls (already used by `tools/benchmark_evaluator.py`) or hunspell CLI for evaluation, existing repo assets: `raw_data/rejected_words.csv`, `raw_data/tdk_words.txt`, `raw_data/dil_dernegi_words.txt`.

---

## Current context / assumptions

- Repo: `C:\gemini\turkspell`. Existing benchmarks are self-built and README acknowledges collision-filtering via Zemberek; this new set must avoid self-favoring construction.
- Prior session work: PHONE table + REP rules added to `tr.aff`/`tr.dic` (v0.1.2). New benchmark will quantify whether these improved real-world suggestion quality.
- Official Mukayese V2 CSVs were downloaded during the previous session to `%LOCALAPPDATA%/Temp/official_test_v2.csv` (gold,input pairs, 10k rows). They are NOT in the repo. The new generator may optionally ingest them as a seed source but must not depend on Temp files.
- Competitor dictionaries can be fetched via `tools/download_dictionaries.py` (exists in repo) into `external_dictionaries/`.
- Known pitfall from prior session: spylls suggest() is ~1 word/sec on this dictionary — full 10k×5-dictionary runs need chunked/background execution or hunspell CLI. Plan uses a sample-size default of 2,500 words with `--full` flag for 10k.
- Windows host; shell is git-bash. Use `$LOCALAPPDATA/Temp` for scratch, forward-slash paths for native tools.

## Dataset design

Four stratified slices (total default 2,500 misspelled words + 2,500 clean control words):

1. **Corpus-real slice (40%)** — high-frequency rejected words from `rejected_words.csv` that are NOT valid in any of: TDK list, Dil Derneği list, any competitor .dic. These are genuine observed errors. Each entry keeps its frequency tier.
2. **Keyboard-proximity slice (20%)** — valid authority words mutated using the QWERTY-tr KEY adjacency rows already defined in `tr.aff` line 1526 (parse them programmatically so the mutation model is shared, not hand-copied).
3. **Diacritic-collapse slice (20%)** — valid authority words with ş→s, ğ→g, ç→c, ı→i, ö→o, ü→u, â/a î/i û/u folds applied at random positions (the ASCII-typing class).
4. **Phonetic-metathesis slice (20%)** — targeted patterns: nl↔ln swaps, silent-ğ deletions, -ecek/-acak → -ıcak/-ucak reductions, -iyor → -iyo elisions (applied only where result is not a valid word anywhere).

Clean control set: 2,500 random authority words (frequency-balanced) that ARE valid — measures false-positive rate per dictionary.

Every entry gets: `id, slice, input, gold, frequency_tier, notes`. Deterministic: `random.Random(20260824)`.

Collision filter: a candidate is discarded if it appears in ANY reference lexicon (tdk_words, dil_dernegi, zemberek_lexicon.json stems, all downloaded competitor .dic files stripped of flags). This prevents penalizing dictionaries for correctly accepting real words.

## Proposed approach / fairness rules

- Evaluation runner loads each dictionary through the SAME engine path. Default: hunspell CLI (`hunspell -d <dir> -a`) because it's C++-fast and matches Firefox's engine family; spylls fallback if CLI absent.
- Correction@1/@3 computed case-insensitively (Turkish lowercase fold: I↔ı, İ↔i) since dictionaries legitimately differ on KEAPECASE handling.
- Report per-slice AND aggregate metrics; write results to `benchmark/results/<date>_<dict>.json` and a combined markdown table.
- No dictionary under test is used during dataset generation except as a *negative filter* (collision removal), which is fair to all.

---

## Step-by-step plan

### Task 1: Scaffold benchmark directory + config

**Objective:** Create the module layout and a single source of truth for benchmark parameters.

**Files:**
- Create: `benchmark/__init__.py` (empty)
- Create: `benchmark/config.py`

```python
# benchmark/config.py
"""Turkspell Benchmark V3 configuration."""
SEED = 20260824
SAMPLE_SIZE = 2500          # total misspelled entries (--full raises to 10000)
SLICES = {
    "corpus_real": 0.40,
    "keyboard":    0.20,
    "diacritic":   0.20,
    "phonetic":    0.20,
}
RAW = os.path.join(os.path.dirname(__file__), "..", "raw_data")
import os
AUTHORITY_FILES = [
    os.path.join(RAW, "tdk_words.txt"),
    os.path.join(RAW, "dil_dernegi_words.txt"),
]
REJECTED_CSV = os.path.join(RAW, "rejected_words.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "turkspell_bench_v3")
```

**Step 1:** Create both files.
**Step 2:** Run `python -c "from benchmark import config; print(config.SAMPLE_SIZE)"` — expected `2500`.
**Step 3:** Commit: `git add benchmark/ && git commit -m "feat(bench): scaffold benchmark v3 config"`

### Task 2: Lexicon loader + Turkish case fold utility

**Objective:** Shared helpers to load authority words and normalize Turkish casing.

**Files:**
- Create: `benchmark/lexicons.py`
- Test: `benchmark/test_lexicons.py`

**Step 1: Write failing test**

```python
# benchmark/test_lexicons.py
from benchmark.lexicons import tlc, load_authority_set

def test_turkish_lower():
    assert tlc("KİTAP") == "kitap"
    assert tlc("IŞIK") == "ışık"

def test_load_authority(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("kitap\nekmek\n", encoding="utf-8")
    assert load_authority_set([str(f)]) == {"kitap", "ekmek"}
```

**Step 2:** Run `python -m pytest benchmark/test_lexicons.py -v` — expected FAIL (module missing).

**Step 3: Implement**

```python
# benchmark/lexicons.py
def tlc(s: str) -> str:
    """Turkish-aware lowercase (I->ı, İ->i)."""
    return s.replace("I", "ı").replace("İ", "i").lower()

def load_authority_set(paths) -> set:
    """Load wordlists; strip Hunspell flags after '/'."""
    out = set()
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    out.add(tlc(w.split("/")[0]))
    return out
```

**Step 4:** Run pytest again — expected 2 passed.
**Step 5:** Commit: `git commit -am "feat(bench): turkish case fold + authority loader"`

### Task 3: Mutation engines (4 slices)

**Objective:** Deterministic typo generators for keyboard, diacritic, phonetic slices.

**Files:**
- Create: `benchmark/mutations.py`
- Test: `benchmark/test_mutations.py`

**Step 1: Write failing tests** covering: KEY-adjacency substitution produces a change; diacritic fold changes ş→s exactly once; ln→nl metathesis only when result differs; every mutator returns `(input, gold, notes)` triples and never returns input unchanged.

```python
def test_fold_changes_word():
    inp, gold, note = mutate_diacritic("kuş", rng)
    assert inp != gold and gold == "kuş" and "ş" not in inp or True  # one fold applied
```

(Full test file ~40 lines: one test per mutator + a no-op guard.)

**Step 2:** Run pytest — expected FAIL.
**Step 3:** Implement `mutate_keyboard(word, rng)` (KEY pairs parsed from tr.aff or embedded TR-Q layout dict), `mutate_diacritic(word, rng)`, `mutate_phonetic(word, rng)` (metathesis/silent-ğ/suffix-reduction pattern list), each returning None if no mutation possible (caller retries with another word).
**Step 4:** Run pytest — expected pass (~6 tests).
**Step 5:** Commit.

### Task 4: Corpus-real slice miner

**Objective:** Extract top-frequency rejected words that fail ALL reference lexicons.

**Files:**
- Create: `benchmark/mine_corpus_slice.py`
- Modify: nothing else.

Logic: stream `rejected_words.csv`, skip len<3, skip non-alpha-Turkish tokens, skip anything in the union lexicon set, take top N by frequency. Output list of `(word, freq_tier)`.

**Verify:** run standalone, expect e.g. `degil`, `tesekkur` present with high tiers; expect `com`, `the` (English) excluded via a small stopword screen (ASCII-only words with no Turkish diacritics AND appearing in `training/english_words_large.txt` get dropped).
**Commit.**

### Task 5: Collision filter across all dictionaries

**Objective:** Guarantee no "typo" is actually a valid word in any compared dictionary.

**Files:**
- Create: `benchmark/collision_filter.py`
- Uses: `tools/download_dictionaries.py` output dir `external_dictionaries/` (gitignored already).

Logic: parse each competitor `.dic` (first line = count; subsequent lines `word/flags`), union into one set alongside authority+Zemberek sets; expose `is_valid_anywhere(word) -> bool`. Generator drops candidates where `is_valid_anywhere(input)`.
**Verify:** `is_valid_anywhere("ev")` True; `is_valid_anywhere("yanliz")` False.
**Commit.**

### Task 6: Dataset generator (assembles all slices)

**Objective:** Produce `benchmark/turkspell_bench_v3/bench_v3_misspelled.csv` and `bench_v3_clean.csv` with columns `id,slice,input,gold,frequency_tier,notes`.

**Files:**
- Create: `benchmark/generate_dataset.py`

Steps: build lexicon union → mine corpus slice → generate mutation slices from frequency-ranked authority words (retry loop until slice quotas filled, max 50 attempts/word) → apply collision filter to everything → shuffle seeded → write CSVs + a `manifest.json` (seed, sizes, sha256 of outputs, generation date, source file hashes).
**Verify:** row counts match SLICES ratios ±2%; rerun produces byte-identical files (determinism check); spot-check 10 entries manually.
**Commit.**

### Task 7: Multi-dictionary evaluation runner

**Objective:** Evaluate every dictionary under `external_dictionaries/*/` plus Turkspell itself; emit JSON + markdown comparison table.

**Files:**
- Create: `benchmark/run_benchmark.py`
- Create: `benchmark/results/.gitkeep`

Engine choice: prefer hunspell CLI in batch mode (`hunspell -d <dir> -a -l` for detection; `-a` stream parsing for suggestions — feed all words in ONE process invocation to amortize startup). Fallback spylls with progress logging every 200 words and resumable partial-results cache in `%LOCALAPPDATA%/Temp/bench_cache_<dict>.json`.
Metrics per dictionary: precision (clean set), recall (misspelled set), F1, correction@1, correction@3 — overall and per slice.
Output: `benchmark/results/<YYYYMMDD>_<dictname>.json` + `benchmark/results/summary.md` table sorted by correction@1.
**Verify:** run on Turkspell alone with a 100-word smoke subset (`--limit 100`): completes <5 min, JSON well-formed, table renders.
**Commit.**

### Task 8: Full run + README documentation

**Objective:** Produce the actual comparison numbers and document methodology.

**Files:**
- Create: `benchmark/README.md` (methodology, fairness rules, how to regenerate, how to add a dictionary)
- Modify: root `README.md` — add a "Benchmark V3 (independent)" section linking results.

Steps: download competitor dictionaries → generate dataset → run full benchmark (background task, chunked) → write summary.md numbers into both READMEs → final commit.

### Task 9: CI hook (optional but recommended)

**Files:**
- Create: `.github/workflows/benchmark-smoke.yml`

Runs generator determinism check + 100-word smoke eval on push to protect pipeline integrity. Does NOT run full benchmark (too slow for CI).

---

## Tests / validation summary

- Unit: `python -m pytest benchmark/ -v` (lexicon loader, mutators, collision filter, determinism).
- Integration: `python benchmark/generate_dataset.py && python benchmark/generate_dataset.py --check` (byte-identical rerun).
- Smoke eval: `python benchmark/run_benchmark.py --only turkspell --limit 100`.
- Manual: open `summary.md`, confirm Turkspell ≥ competitors on corpus_real slice (expected: REP/PHONE work shows up there).

## Risks, tradeoffs, open questions

1. **spylls speed** (~1 word/sec × 2,500 × 5 dicts ≈ hours). Mitigation: hunspell CLI primary; background execution; resumable cache. Open question: does the user have `hunspell` CLI available outside this machine? (It was found via winget here.)
2. **Competitor .dic formats differ** (FLAG long vs UTF-8, AF aliases). Parser must handle both; verify against `tdd-ai/hunspell-tr` which uses aliased AF blocks like Turkspell.
3. **Self-favoring risk**: corpus_real slice mined from OUR rejected_words could embed Turkspell-specific biases. Mitigation: rejected_words comes from generic OSCAR corpus (not our dic), and collision filter removes anything any dict accepts. Still document this provenance honestly in benchmark/README.md.
4. **hersey/birsey class**: space-containing corrections can never win @1 in Hunspell ranking; decide whether benchmark counts "her şey" match case-insensitively-with-space-normalized (recommended: yes, normalize spaces before compare — otherwise REP fixes are invisible).
5. **License**: dataset derived from TDK/Dil Derneği lists inherits their restrictions — mark dataset CC-BY-NC like existing raw_data handling, keep it out of the XPI.
