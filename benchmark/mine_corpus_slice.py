# -*- coding: utf-8 -*-
"""Mine the corpus-real slice: high-frequency words rejected by the OSCAR
corpus that appear in NO reference lexicon (authorities, Zemberek, English).

These are genuine observed Turkish spelling errors with real frequency weight.
"""
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark import config
from benchmark.lexicons import tlc, load_authority_index, load_authority_set

_TURKISH_ALPHA = re.compile(r"^[a-zçğıöşüâîû]+$")


def _load_english() -> set:
    eng = set()
    if os.path.exists(config.ENGLISH_WORDS):
        with open(config.ENGLISH_WORDS, encoding="utf-8", errors="ignore") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    eng.add(w)
    return eng


def mine_corpus_slice(limit: int, exclude: set) -> list:
    """Return up to `limit` (word, freq) pairs of genuine observed errors.

    exclude - set of lowercase forms to skip (authority words, valid words).
    """
    idx = load_authority_index(config.AUTHORITY_FILES)
    blocked = idx["exact"] | idx["dehatted_aliases"] | set(exclude)
    english = _load_english()

    rows = []
    with open(config.REJECTED_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                freq = int(row["frequency"])
            except (KeyError, ValueError):
                continue
            w = tlc(row["word"].strip())
            if len(w) < 3 or not _TURKISH_ALPHA.match(w):
                continue
            if w in blocked or w in english:
                continue
            rows.append((w, freq))
    rows.sort(key=lambda x: -x[1])
    return rows[:limit]


def frequency_tier(freq: int) -> str:
    if freq >= 10000:
        return "very_high"
    if freq >= 1000:
        return "high"
    if freq >= 100:
        return "medium"
    return "low"


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    for w, c in mine_corpus_slice(n, set()):
        print(f"{w}\t{c}\t{frequency_tier(c)}")
