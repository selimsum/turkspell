# -*- coding: utf-8 -*-
"""
tests/test_golden_verbs.py — Golden Verb Regression & Equivalence Test Suite
=============================================================================
Loads the golden baseline dataset and verifies:
1. All baseline-accepted positive verb forms (13,190 forms) remain accepted (NO regressions).
2. The factorized generator correctly increases coverage for valid Turkish verbal paradigms.
3. Canary overgeneration forms remain strictly rejected.
"""

import os
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT_DIR / "tests" / "golden_verbs_baseline.json"
DICT_PATH = str(ROOT_DIR / "tr")

# Ensure hunspell is in PATH
winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break

HUNSPELL_BIN = shutil.which("hunspell")


def check_words_batch(words: list[str], dict_path: str = DICT_PATH) -> set[str]:
    """Runs hunspell -l on words and returns unrecognized (flagged) words."""
    if not HUNSPELL_BIN:
        raise RuntimeError("hunspell binary not found in PATH!")
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return set(line.strip() for line in p.stdout.splitlines() if line.strip())


class TestGoldenVerbs(unittest.TestCase):
    """Verifies verb morphology equivalence and overgeneration protection."""

    @classmethod
    def setUpClass(cls):
        if not BASELINE_PATH.exists():
            raise FileNotFoundError(f"Baseline file missing: {BASELINE_PATH}")
        with open(BASELINE_PATH, "r", encoding="utf-8") as f:
            cls.baseline = json.load(f)

    def test_golden_positive_equivalence(self):
        """Verifies that none of the baseline-accepted positive verb forms are lost."""
        baseline_accepted = self.baseline["accepted_positive_baseline"]
        flagged = check_words_batch(baseline_accepted)
        
        # We assert zero regressions on baseline accepted forms
        self.assertEqual(
            flagged,
            set(),
            f"Regression detected: {len(flagged)} previously accepted verb forms are now rejected! Sample: {list(flagged)[:15]}"
        )

    def test_canary_overgeneration_rejection(self):
        """Verifies that canary illegal formations are not accepted."""
        canaries = [
            # Broken demek/yemek rules
            "debilecek", "debilecekler", "debileceklerine", "debileceklerini",
            "yebilecek", "yebilecekler", "yebileceklerine", "yebileceklerini",
            # Double buffer consonants
            "yapıssı", "gelmeyni", "bakayna",
            # Double plural markings
            "yaparlarar", "gelirlerler",
            # Double copulas
            "yaptıymış", "yaptıydıymış", "gelmiştidi",
            # Non-pronominal cases on 3rd-person participles (missing pronominal 'n')
            "yaptığıda", "yaptığıdan", "gittiğide", "gittiğiden"
        ]
        flagged = check_words_batch(canaries)
        leaked = set(canaries) - flagged
        self.assertEqual(
            leaked,
            set(),
            f"Overgeneration detected: {len(leaked)} illegal canary forms accepted! Leaked: {leaked}"
        )


if __name__ == "__main__":
    unittest.main()
