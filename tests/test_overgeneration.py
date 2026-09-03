# -*- coding: utf-8 -*-
"""
Turkspell Overgeneration & Fuzzing Test Suite
Verifies that affix rules and flags do NOT overgenerate impossible Turkish words:
1. Illegal double buffer consonants (*kapıssı, *arabaynı)
2. Illegal vowel collisions (*acııydı, *kediin, *gülmeini)
3. Illegal verb formations (*debilecek, *debileceklerine)
4. Illegal vowel harmony violations (*evlar, *odalarımiz)
"""

import sys
import subprocess
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = str(ROOT_DIR / "tr")


def check_illegal_words(words: list[str], dict_path: str = DICT_PATH) -> list[str]:
    """Runs hunspell -l on words that MUST be rejected. Returns any that leaked (were accepted)."""
    p = subprocess.run(
        ["hunspell", "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    flagged = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    # A leaked word is one that hunspell accepted (NOT in flagged)
    leaked = [w for w in words if w not in flagged]
    return leaked


class TestOvergenerationProtection(unittest.TestCase):
    """Tests that illegal morphological combinations are strictly rejected."""

    def test_double_buffer_consonants(self):
        """Buffer consonants (y, s, n) must never be doubled or misplaced."""
        illegal = [
            "kapıssı", "kapıssa", "arabannda", "arabaynı", "evnne",
            "masannın", "kediyni", "odassa", "elmaylaa", "kuzuyya"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Illegal double buffer consonants leaked: {leaked}")

    def test_vowel_collision_anomalies(self):
        """Vowel-initial suffixes must not attach to vowel-final stems without buffer consonant."""
        illegal = [
            "acııydı", "eliiydi", "anomaliine", "gülmeini", "enseindeki",
            "kediin", "kuzuun", "arabaa", "masaa", "tarlain", "tarlai"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Illegal vowel collisions leaked: {leaked}")

    def test_demek_yemek_broken_rules(self):
        """The notorious 'debileceklerine' bug must remain 100% purged."""
        illegal = [
            "debilecek", "debilecekler", "debileceklerine", "debileceklerini",
            "debilecekti", "debilecekmiş", "debilecektir",
            "yebilecek", "yebilecekler", "yebileceklerine", "yebileceklerini"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Broken demek/yemek forms leaked: {leaked}")

    def test_gross_vowel_harmony_violations(self):
        """Front-vowel stems taking back-vowel suffixes and vice versa."""
        illegal = [
            "evlar", "evdan", "evda", "evın",
            "kedilar", "kedidan", "kedida",
            "kapiler", "kapiden", "kapide",
            "odalere", "odalerde", "odalerden"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Gross vowel harmony violations leaked: {leaked}")

    def test_impossible_suffix_chains(self):
        """Double case markers and broken ablative/locative chains."""
        illegal = [
            "evdene", "okuldana", "masadada", "okuldanler",
            "arabadaın", "çocukdaden", "masadanler"
        ]
        leaked = check_illegal_words(illegal)
    def test_bare_virtual_stems(self):
        """Virtual stems guarded by NEEDAFFIX X must never be recognized as bare words."""
        illegal = [
            "bloğ", "tedariğ", "imalad", "cenned", "cehd", "kulb"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Bare virtual stems leaked into dictionary: {leaked}")


if __name__ == "__main__":
    unittest.main()
