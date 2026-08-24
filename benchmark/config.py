"""Turkspell Benchmark V3 configuration.

Single source of truth for dataset generation parameters.
The dataset is deterministic: same seed -> byte-identical output.
"""
import os

SEED = 20260824
SAMPLE_SIZE = 2500          # total misspelled entries (--full raises to 10000)

SLICES = {
    "corpus_real": 0.40,    # high-frequency words rejected by the OSCAR corpus
    "keyboard":    0.20,    # KEY-adjacency typos on valid authority words
    "diacritic":   0.20,    # ş->s, ğ->g ... ASCII-typing collapses
    "phonetic":    0.20,    # metathesis / silent-ğ / suffix reduction
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE_DIR, "raw_data")

AUTHORITY_FILES = [
    os.path.join(RAW, "tdk_words.txt"),
    os.path.join(RAW, "tdk_words_new.txt"),
    os.path.join(RAW, "dil_dernegi_words.txt"),
]
REJECTED_CSV = os.path.join(RAW, "rejected_words.csv")
ZEMBEREK_LEXICON = os.path.join(BASE_DIR, "lexicons", "zemberek_lexicon.json")
ENGLISH_WORDS = os.path.join(BASE_DIR, "training", "english_words_large.txt")
EXTERNAL_DICTS_DIR = os.path.join(BASE_DIR, "external_dictionaries")

OUTPUT_DIR = os.path.join(BASE_DIR, "benchmark", "turkspell_bench_v3")
RESULTS_DIR = os.path.join(BASE_DIR, "benchmark", "results")
