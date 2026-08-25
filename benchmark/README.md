# Turkspell Benchmark V3

An independent, reproducible benchmark dataset for comparing Turkish Hunspell
dictionaries on spelling-error detection and correction.

## Methodology

### Dataset composition

`turkspell_bench_v3/` contains 2,444 misspelled words in four stratified
slices plus 2,500 valid control words:

| Slice | Share | Source | Example |
|---|---|---|---|
| `corpus_real` | ~40% | High-frequency words rejected by the OSCAR corpus that the reference dictionary also flags (`rejected_words.csv`) | `gida` (gıda), `eticaret` (e-ticaret) |
| `keyboard` | 20% | Adjacent-key substitutions on valid authority words using the Turkish QWERTY layout | `fahriye` → `fshriye` |
| `diacritic` | 20% | ASCII-typing collapses: ş→s, ğ→g, ç→c, ö→o, ü→u, ı→i, â→a | `şairlik` → `sairlik` |
| `phonetic` | 20% | Metathesis (nl↔ln), silent-ğ deletion, future/‑iyor suffix reductions | `düğünsüz` → `düünsüz` |

Control set: random single-token TDK/Dil Derneği words (hatted forms excluded).

### Fairness rules

1. **Collision filter** — a candidate "typo" is discarded if it is a valid
   word in ANY reference source: TDK, TDK-new, Dil Derneği, the Zemberek
   morphological lexicon, or any competitor dictionary's `.dic`. A dictionary
   correctly accepting a real word is never counted as an error.
2. **Corpus-rejection ≠ error** — the corpus rejects many *valid* inflected
   forms. Corpus-real candidates are additionally filtered through the
   reference hunspell dictionary; only words it flags are kept.
   **Disclosure:** this is the one place Turkspell touches dataset
   construction. It can only REMOVE entries, not add them, so it cannot
   inflate Turkspell's own score — but a competitor with wider acceptance of
   inflected forms could theoretically be penalized by rows Turkspell happens
   to flag. Per-slice results are reported separately so this effect is
   auditable.
3. **Determinism** — seeded RNG (`SEED=20260824`); regeneration is
   byte-identical (`python benchmark/generate_dataset.py --check`).
4. **Space-normalized matching** — corrections containing spaces
   (`her şey`, `yanlış yönde`) compare equal after whitespace collapsing and
   Turkish case-folding (I↔ı, İ↔i).

### Metrics

- **Precision** — % of clean control words NOT flagged.
- **Recall** — % of misspelled words flagged.
- **F1** — harmonic mean of the above.
- **Correction@1 / @3** — among flagged misspellings, % where the correct
  form is the first (or within the first three) suggestions.

## Usage

```bash
# Regenerate dataset (deterministic)
python benchmark/generate_dataset.py            # ~2,500 entries
python benchmark/generate_dataset.py --full     # ~10,000 entries
python benchmark/generate_dataset.py --check    # verify byte-identical rerun

# Download competitor dictionaries into external_dictionaries/
python tools/download_dictionaries.py

# Run evaluation (requires hunspell CLI on PATH)
python benchmark/run_benchmark.py                       # all dictionaries
python benchmark/run_benchmark.py --only turkspell      # one dictionary
python benchmark/run_benchmark.py --limit 100           # smoke test
```

Results land in `benchmark/results/<date>_<dict>.json` plus a combined
`summary.md`.

## Adding a dictionary

Create `external_dictionaries/<name>/` containing `<name>.aff` and
`<name>.dic` (or any basename), then re-run the benchmark. The runner
auto-discovers every `.dic` under `external_dictionaries/`.

## Known limitations

- `corpus_real` entries carry no gold correction; Correction@1 for that slice
  counts "any suggestion differing from the input" (weak signal). The JSON
  per-slice breakdown makes this visible.
- Competitor `.dic` parsing strips flags but does not expand `AF` aliases;
  stems are matched as-is. This only affects collision filtering (removing
  candidates), never scoring.
- Datasets derived from TDK/Dil Derneği lists inherit their license terms —
  keep out of distributed add-ons.
