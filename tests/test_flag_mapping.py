# -*- coding: utf-8 -*-
"""
Turkspell Flag Mapping & Codepoint Stability Test Suite
Verifies that:
1. UTF-8 flag mapping assigns unique, stable codepoints.
2. 3-character proper noun flags and 2-character stem/affix flags are parsed without ambiguity.
3. Reversing flag mappings produces identical original flags.
"""

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "build"))

from utf8_flag_mapping import (
    LONG_TO_UTF8,
    UTF8_TO_LONG,
    ALL_FLAGS,
    PROPER_NOUN_FLAGS_3,
    STAGE2_VERB_FLAGS,
    remap_flag_string,
)


class TestFlagMappingStability(unittest.TestCase):
    """Verifies that flag definitions and UTF-8 mappings remain stable."""

    def test_flag_count_and_uniqueness(self):
        """All long flags must map to unique UTF-8 characters."""
        self.assertEqual(len(LONG_TO_UTF8), 200, f"Expected 200 flags, got {len(LONG_TO_UTF8)}")
        # All flags except NE->X should have unique codepoints
        non_ne_values = [v for k, v in LONG_TO_UTF8.items() if k != "NE"]
        self.assertEqual(
            len(non_ne_values),
            len(set(non_ne_values)),
            "Duplicate UTF-8 codepoints detected in flag mapping!"
        )

    def test_needaffix_mapping(self):
        """NE flag must always map to ASCII 'X' for Hunspell NEEDAFFIX compatibility."""
        self.assertEqual(LONG_TO_UTF8["NE"], "X")

    def test_proper_noun_3char_remapping(self):
        """3-char proper noun flags like pBA, pON, pFR must remap cleanly."""
        for flag in ["pBA", "pBL", "pON", "pOR", "pFN", "pUL"]:
            utf8_char = remap_flag_string(flag)
            self.assertEqual(len(utf8_char), 1)
            self.assertEqual(utf8_char, LONG_TO_UTF8[flag])
            self.assertEqual(UTF8_TO_LONG[utf8_char], flag)

    def test_stage2_verb_flag_disambiguation(self):
        """2-char stage 2 flags (e.g. pO, pU) followed by another flag must NOT collide with 3-char flags."""
        # 'pON1' should parse as 'pO' + 'N1', NOT as proper noun 'pON' + '1'
        remapped = remap_flag_string("pON1")
        self.assertEqual(len(remapped), 2)
        self.assertEqual(remapped[0], LONG_TO_UTF8["pO"])
        self.assertEqual(remapped[1], LONG_TO_UTF8["N1"])

        # Genuine 3-char proper noun flag pON followed by B1:
        remapped_proper = remap_flag_string("pONB1")
        self.assertEqual(len(remapped_proper), 2)
        self.assertEqual(remapped_proper[0], LONG_TO_UTF8["pON"])
        self.assertEqual(remapped_proper[1], LONG_TO_UTF8["B1"])

    def test_concatenated_flag_strings(self):
        """Multi-flag combinations must remap without character loss."""
        flags = ["B1", "A1", "Y1", "L1"]
        concatenated = "".join(flags)
        remapped = remap_flag_string(concatenated)
        self.assertEqual(len(remapped), len(flags))
        for i, f in enumerate(flags):
            self.assertEqual(remapped[i], LONG_TO_UTF8[f])


if __name__ == "__main__":
    unittest.main()
