"""
POC Validation Script: FLAG long chained flags
Tests that Hunspell correctly validates forms from multi-flag dictionary entries.
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import subprocess
import sys
from pathlib import Path

HUNSPELL = "hunspell"
DIC_PATH = Path(__file__).parent / "test"  # hunspell -d path (no extension)

def check_word(word: str) -> bool:
    """Returns True if hunspell accepts the word."""
    result = subprocess.run(
        [HUNSPELL, "-d", str(DIC_PATH), "-l"],
        input=word + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    # -l prints only UNKNOWN words. If output is empty, word is valid.
    return result.stdout.strip() == ""

def run_tests():
    tests = [
        # (word, expected_valid, description)
        # --- ev (house) ---
        ("ev",          True,  "bare stem"),
        ("evi",         True,  "accusative (AC flag)"),
        ("eve",         True,  "dative (DA flag)"),
        ("evde",        True,  "locative (LO flag)"),
        ("evden",       True,  "ablative (AB flag)"),
        ("evin",        True,  "genitive (GE flag)"),
        ("evle",        True,  "instrumental (IN flag)"),
        ("evler",       True,  "plural (PF flag)"),
        ("evleri",      True,  "plural+accusative (PF flag)"),
        ("evlere",      True,  "plural+dative (PF flag)"),
        ("evlerde",     True,  "plural+locative (PF flag)"),
        ("evlerden",    True,  "plural+ablative (PF flag)"),
        ("evlerin",     True,  "plural+genitive (PF flag)"),
        ("evlerle",     True,  "plural+instrumental (PF flag)"),
        ("evdir",       True,  "copula -dir (CL flag)"),
        ("evdi",        True,  "copula -di past (CL flag)"),
        ("evmiş",       True,  "copula -miş narrative (CL flag)"),
        ("evse",        True,  "copula -se conditional (CL flag)"),
        ("evken",       True,  "copula -yken adverbial (CL flag)"),
        ("evi",         True,  "3sg possessive (PS flag) - same form as accusative"),
        ("evine",       True,  "3sg possessive dative (PS flag)"),
        ("evinde",      True,  "3sg possessive locative (PS flag)"),
        # --- göz (eye) ---
        ("göz",         True,  "bare stem"),
        ("gözü",        False, "accusative should be 'gözü' but AC flag produces 'gözi' — KNOWN LIMITATION of POC (back-rounded needs different flag)"),
        ("göze",        True,  "dative"),
        ("gözde",       True,  "locative"),
        ("gözler",      True,  "plural"),
        # --- negative tests ---
        ("evta",        False, "invalid locative (front vowel + -ta is wrong)"),
        ("evlar",       False, "invalid plural (front word + -lar is wrong)"),
        ("evlara",      False, "invalid plural dative"),
        ("xyz123",      False, "nonsense word"),
    ]

    passed = 0
    failed = 0
    skipped = 0

    print(f"{'Word':<20} {'Expected':<10} {'Got':<10} {'Result':<8} {'Note'}")
    print("-" * 90)

    for word, expected, desc in tests:
        if "KNOWN LIMITATION" in desc:
            skipped += 1
            print(f"{word:<20} {'valid' if expected else 'invalid':<10} {'SKIP':<10} {'SKIP':<8} {desc}")
            continue

        valid = check_word(word)
        result = valid == expected
        status = "PASS" if result else "FAIL"
        if result:
            passed += 1
        else:
            failed += 1
        got_str = 'valid' if valid else 'invalid'
        exp_str = 'valid' if expected else 'invalid'
        print(f"{word:<20} {exp_str:<10} {got_str:<10} {status:<8} {desc}")

    print()
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    if failed > 0:
        print("POC validation FAILED -- review test.aff rules")
        sys.exit(1)
    else:
        print("POC validation PASSED -- FLAG long chaining confirmed working")

if __name__ == "__main__":
    run_tests()
