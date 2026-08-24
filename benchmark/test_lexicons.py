# -*- coding: utf-8 -*-
"""Tests for benchmark.lexicons."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.lexicons import tlc, load_authority_set, load_authority_index


def test_turkish_lower_basic():
    assert tlc("KITAP") == "kıtap"


def test_turkish_lower_dotted_i():
    assert tlc("İSTANBUL") == "istanbul"


def test_turkish_lower_mixed():
    assert tlc("IŞIK") == "ışık"
    assert tlc("IRMAK") == "ırmak"


def test_load_authority_set_strips_flags():
    import tempfile
    f = tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8")
    f.write("kitap\nekmek/N1\ngüzel/A1\n")
    f.close()
    try:
        assert load_authority_set([f.name]) == {"kitap", "ekmek", "güzel"}
    finally:
        os.unlink(f.name)


def test_load_authority_index_tracks_hats():
    import tempfile
    f = tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8")
    # kar: unhatted entry; kâr: hatted-only entry; neftîleşmek: hatted verb
    f.write("kar\nekmek\nkâr\nneftîleşmek\n")
    f.close()
    try:
        idx = load_authority_index([f.name])
        assert idx["exact"] >= {"kar", "ekmek", "kâr", "neftîleşmek"}
        assert idx["hatted"] == {"kâr", "neftîleşmek"}
        assert idx["dehatted_aliases"] == {"neftileşmek"}

    finally:
        os.unlink(f.name)
