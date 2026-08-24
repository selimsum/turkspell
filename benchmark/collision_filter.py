# -*- coding: utf-8 -*-
"""Collision filter: is a candidate 'typo' actually valid in ANY compared
dictionary or reference lexicon? If yes, it must be excluded from the
benchmark (a dictionary correctly accepting a real word is not an error).

Reference universe:
  - TDK + tdk_new + Dil Derneği authority lists
  - Zemberek morphological lexicon stems
  - every competitor .dic found in external_dictionaries/
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark import config
from benchmark.lexicons import tlc, load_authority_index


def _load_zemberek_stems() -> set:
    stems = set()
    if not os.path.exists(config.ZEMBEREK_LEXICON):
        return stems
    with open(config.ZEMBEREK_LEXICON, encoding="utf-8") as f:
        data = json.load(f)
    # zemberek_lexicon.json format: list of entries with 'lemma' key
    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and entry.get("lemma"):
                stems.add(tlc(str(entry["lemma"]).strip()))
            elif isinstance(entry, str):
                stems.add(tlc(entry.strip()))
    return stems


def parse_dic(path: str) -> set:
    """Parse a Hunspell .dic: first line count, then word/flags lines."""
    words = set()
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i == 0 and line.strip().isdigit():
                    continue
                head = line.split("/")[0].strip()
                if head:
                    words.add(tlc(head))
    except OSError:
        pass
    return words


def load_reference_universe() -> set:
    """Union of everything that counts as 'a real word' for filtering."""
    idx = load_authority_index(config.AUTHORITY_FILES)
    universe = idx["exact"] | _load_zemberek_stems()
    if os.path.isdir(config.EXTERNAL_DICTS_DIR):
        for root, _dirs, files in os.walk(config.EXTERNAL_DICTS_DIR):
            for fn in files:
                if fn.endswith(".dic"):
                    universe |= parse_dic(os.path.join(root, fn))
    return universe


class CollisionFilter:
    def __init__(self, extra_valid: set = None):
        self.universe = load_reference_universe()
        if extra_valid:
            self.universe |= {tlc(w) for w in extra_valid}

    def is_valid_anywhere(self, word: str) -> bool:
        return tlc(word.strip()) in self.universe


if __name__ == "__main__":
    cf = CollisionFilter()
    print(f"Reference universe size: {len(cf.universe):,}")
    for w in ["ev", "kitap", "yanliz", "degil", "tesekkur", "xyzq"]:
        print(f"  {w:12s} valid_anywhere={cf.is_valid_anywhere(w)}")
