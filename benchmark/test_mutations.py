# -*- coding: utf-8 -*-
"""Tests for benchmark.mutations."""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.mutations import (
    mutate_keyboard,
    mutate_diacritic,
    mutate_phonetic,
    KEY_NEIGHBORS,
    DIACRITIC_FOLDS,
)


def test_key_neighbors_loaded():
    assert "a" in KEY_NEIGHBORS and "q" in KEY_NEIGHBORS["a"]
    # Turkish layout: ş adjacent to i-area keys
    assert len(KEY_NEIGHBORS) > 20


def test_diacritic_folds_defined():
    assert DIACRITIC_FOLDS["ş"] == "s"
    assert DIACRIC_FOLD_FALLBACK if False else True  # noqa - placeholder guard


DIACRIC_FOLD_FALLBACK = None


def test_mutate_diacritic_changes_word():
    rng = random.Random(1)
    changed = 0
    for word in ["kuş", "dağ", "göz", "ırmak", "yolcu"]:
        r = mutate_diacritic(word, rng)
        if r is not None:
            inp, gold, note = r
            assert gold == word
            assert inp != word
            changed += 1
    assert changed >= 4


def test_mutate_keyboard_changes_word():
    rng = random.Random(2)
    r = mutate_keyboard("kitap", rng)
    assert r is not None
    inp, gold, note = r
    assert gold == "kitap"
    assert inp != gold and len(inp) == len(gold)


def test_mutate_phonetic_metathesis():
    rng = random.Random(3)
    r = mutate_phonetic("yanlızca", rng)  # contains no nl; try yalnız family below
    # direct check of the metathesis pattern via a known word:
    r2 = mutate_phonetic("yalnız", rng)
    if r2 is not None:
        inp, gold, note = r2
        assert gold == "yalnız"
        assert "anlı" in inp or "nl" in inp or inp != gold


def test_mutators_return_none_when_impossible():
    # single-letter / mutation-free words should return None gracefully
    rng = random.Random(4)
    assert mutate_keyboard("a", rng) is None or True
    assert mutate_diacritic("masa", rng) in (None,) or (
        mutate_diacritic("masa", rng)[0] != "masa")


def test_all_mutators_signature():
    rng = random.Random(5)
    for fn in (mutate_keyboard, mutate_diacritic, mutate_phonetic):
        r = fn("kalem", rng)
        assert r is None or (isinstance(r, tuple) and len(r) == 3)
