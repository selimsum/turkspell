# -*- coding: utf-8 -*-
"""
Turkspell Audit: Numbers, Ordinals, Distributives, Dates/Years & Clock Times
============================================================================
Verifies:
  1. 100% acceptance of valid Turkish apostrophe inflections on numbers, ordinals,
     distributives, decades, years, dotted thousands, and 24-hour clock times
     (both straight ' and curly ’ apostrophes).
  2. 100% rejection (0 leaks) of phonologically invalid number/ordinal/clock-time
     suffixes (*1923'de, *2'inci, *6'ıncı, *7'inci, *3'ncü, *15.00'da, etc.).
  3. Top-1 suggestion accuracy in `hunspell -a` for invalid number/ordinal/date/time suffixes.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = os.environ.get("TURKSPELL_DICT", str(ROOT_DIR / "tr"))

winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
HUNSPELL_BIN = shutil.which("hunspell") or "hunspell"


def check_words(words: list[str], dict_path: str = DICT_PATH) -> tuple[list[str], list[str]]:
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    flagged = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    accepted = [w for w in words if w not in flagged]
    rejected = [w for w in words if w in flagged]
    return accepted, rejected


def get_suggestions(words: list[str], dict_path: str = DICT_PATH) -> dict[str, list[str]]:
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-a"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    lines = [line.strip() for line in p.stdout.splitlines() if line.strip()]
    if lines and lines[0].startswith("@(#)"):
        lines = lines[1:]
    result = {}
    for w, line in zip(words, lines):
        if line.startswith("&"):
            parts = line.split(":", 1)
            sugs = [s.strip() for s in parts[1].split(",")] if len(parts) > 1 else []
            result[w] = sugs
        elif line.startswith(("*", "+", "-")):
            result[w] = ["<ACCEPTED>"]
        else:
            result[w] = []
    return result


# 1. Valid number, ordinal, year, decade, and clock-time inflections
VALID_NUMBER_INFLECTIONS = [
    # Single digits (0..9) cases, possessives, copulas
    "0'da", "0'dan", "0'a", "0'ı", "0'ın", "0'ıncı",
    "1'de", "1'den", "1'e", "1'i", "1'in", "1'le", "1'deki", "1'inci", "1'incisi", "1'er", "1'imiz", "1'dir",
    "2'de", "2'den", "2'ye", "2'yi", "2'nin", "2'yle", "2'deki", "2'si", "2'nci", "2'ncisi", "2'şer", "2'miz", "2'ydi",
    "3'te", "3'ten", "3'e", "3'ü", "3'ün", "3'le", "3'teki", "3'üncü", "3'üncüsü", "3'er", "3'lü", "3'ümüz", "3'tür",
    "4'te", "4'ten", "4'e", "4'ü", "4'ün", "4'le", "4'teki", "4'üncü", "4'üncüsü", "4'er", "4'lü", "4'ümüz", "4'tür",
    "5'te", "5'ten", "5'e", "5'i", "5'in", "5'le", "5'teki", "5'inci", "5'incisi", "5'er", "5'lik", "5'imiz", "5'tir",
    "6'da", "6'dan", "6'ya", "6'yı", "6'nın", "6'yla", "6'daki", "6'sı", "6'ncı", "6'ncısı", "6'şar", "6'lı", "6'dır",
    "7'de", "7'den", "7'ye", "7'yi", "7'nin", "7'yle", "7'deki", "7'si", "7'nci", "7'ncisi", "7'şer", "7'li", "7'dir",
    "8'de", "8'den", "8'e", "8'i", "8'in", "8'le", "8'deki", "8'inci", "8'incisi", "8'er", "8'li", "8'dir",
    "9'da", "9'dan", "9'a", "9'u", "9'un", "9'la", "9'daki", "9'uncu", "9'uncusu", "9'ar", "9'lu", "9'dur",
    # Tens (10..90) cases, ordinals, plurals, derivations
    "10'da", "10'dan", "10'a", "10'u", "10'un", "10'uncu", "10'uncusu", "10'ar", "10'luk", "10'lu", "10'dur",
    "20'de", "20'den", "20'ye", "20'yi", "20'nin", "20'si", "20'nci", "20'ncisi", "20'şer", "20'lik", "20'li", "20'lerde",
    "30'da", "30'dan", "30'a", "30'u", "30'un", "30'uncu", "30'uncusu", "30'ar", "30'luk", "30'lu", "30'larda",
    "40'ta", "40'tan", "40'a", "40'ı", "40'ın", "40'ıncı", "40'ıncısı", "40'ar", "40'lık", "40'lı", "40'larda",
    "50'de", "50'den", "50'ye", "50'yi", "50'nin", "50'si", "50'sinde", "50'sinden", "50'nci", "50'şer", "50'lik", "50'li", "50'lerde",
    "60'ta", "60'tan", "60'a", "60'ı", "60'ın", "60'ıncı", "60'ıncısı", "60'ar", "60'lık", "60'lı", "60'larda",
    "70'te", "70'ten", "70'e", "70'i", "70'in", "70'inci", "70'incisi", "70'er", "70'lik", "70'li", "70'lerde", "70'lerden",
    "80'de", "80'den", "80'e", "80'i", "80'in", "80'inci", "80'incisi", "80'er", "80'lik", "80'li", "80'ler", "80'lerde", "80'lerden", "80'lerin",
    "90'da", "90'dan", "90'a", "90'ı", "90'ın", "90'ıncı", "90'ıncısı", "90'ar", "90'lık", "90'lı", "90'lar", "90'larda", "90'lardan", "90'ların",
    # Hundreds, thousands, millions & dotted forms
    "100'de", "100'den", "100'e", "100'ü", "100'ün", "100'üncü", "100'üncüsü", "100'er", "100'lük", "100'lerce", "100'dür",
    "200'de", "200'den", "200'e", "200'ü", "200'üncü", "200'lük",
    "500'de", "500'den", "500'e", "500'ü", "500'üncü", "500'lük",
    "1000'de", "1000'den", "1000'e", "1000'i", "1000'in", "1000'inci", "1000'er", "1000'lik", "1000'lerce",
    "1.000'de", "1.000'den", "1.000'e", "1.000'i", "1.000'in", "1.000'inci",
    "10.000'de", "10.000'den", "10.000'e", "10.000'i", "10.000'in",
    "100.000'de", "100.000'den", "100.000'e", "100.000'i",
    "1000000'da", "1000000'dan", "1000000'a", "1000000'u", "1000000'un", "1000000'uncu",
    "1.000.000'da", "1.000.000'dan", "1.000.000'a", "1.000.000'u", "1.000.000'un", "1.000.000'uncu",
    # Compound two-digit numbers (11..99)
    "11'de", "11'den", "11'e", "11'i", "11'in", "11'inci",
    "12'de", "12'den", "12'ye", "12'yi", "12'nin", "12'nci", "12'si",
    "13'te", "13'ten", "13'e", "13'ü", "13'ün", "13'üncü",
    "14'te", "14'ten", "14'e", "14'ü", "14'ün", "14'üncü",
    "15'te", "15'ten", "15'e", "15'i", "15'in", "15'inci",
    "16'da", "16'dan", "16'ya", "16'yı", "16'nın", "16'ncı", "16'sı",
    "17'de", "17'den", "17'ye", "17'yi", "17'nin", "17'nci", "17'si",
    "18'de", "18'den", "18'e", "18'i", "18'in", "18'inci",
    "19'da", "19'dan", "19'a", "19'u", "19'un", "19'uncu",
    "21'de", "21'inci", "22'de", "22'nci", "23'te", "23'üncü", "24'te", "24'üncü",
    "25'te", "25'inci", "26'da", "26'ncı", "27'de", "27'nci", "28'de", "28'inci", "29'da", "29'uncu",
    "31'de", "35'te", "42'de", "45'te", "53'te", "64'te", "75'te", "86'da", "99'da", "99'uncu",
    # Historical & contemporary years
    "1071'de", "1071'den", "1453'te", "1453'ten", "1881'de", "1881'den",
    "1915'te", "1915'ten", "1919'da", "1919'dan", "1920'de", "1920'den", "1920'ye",
    "1923'te", "1923'ten", "1923'e", "1923'ü", "1923'ün", "1923'teki", "1923'tü", "1923'tedir",
    "1938'de", "1938'den", "1938'e", "1938'in",
    "1960'larda", "1970'lerde", "1980'lerde", "1980'lerin", "1990'larda", "1990'lardan",
    "1999'da", "1999'dan", "2000'de", "2000'den", "2000'e", "2000'in", "2000'ler", "2000'lerde", "2000'lerin",
    "2020'de", "2020'den", "2020'ye", "2020'nin",
    "2023'te", "2023'ten", "2023'e", "2023'ü", "2023'ün",
    "2024'te", "2024'ten", "2024'e", "2024'ü", "2024'ün",
    "2025'te", "2025'ten", "2025'e", "2025'i", "2025'in",
    "2026'da", "2026'dan", "2026'ya", "2026'yı", "2026'nın", "2026'daki",
    # 24-hour clock times (TDK rule: .00 follows hour phonology; non-zero .MM follows minute phonology)
    "00.00'da", "00.00'dan", "01.00'de", "02.00'de", "03.00'te", "04.00'te", "05.00'te",
    "06.00'da", "07.00'de", "08.00'de", "09.00'da", "09.00'dan", "09.00'a",
    "10.00'da", "10.00'dan", "11.00'de", "12.00'de", "12.00'den", "12.00'ye",
    "13.00'te", "13.00'ten", "14.00'te", "14.00'ten", "15.00'te", "15.00'ten", "15.00'e",
    "16.00'da", "16.00'dan", "17.00'de", "17.00'den", "18.00'de", "18.00'den",
    "19.00'da", "19.00'dan", "20.00'de", "20.00'den", "20.00'ye",
    "21.00'de", "22.00'de", "23.00'te", "23.00'ten", "24.00'te", "24.00'ten",
    "08.30'da", "09.15'te", "09.30'da", "09.45'te", "10.20'de", "11.40'ta",
    "12.30'da", "13.15'te", "14.45'te", "15.30'da", "16.20'de", "17.45'te",
    "18.10'da", "19.05'te", "20.30'da", "21.50'de", "22.15'te", "23.59'da",
]

# Also include curly apostrophe variants for a representative subset
CURLY_APOSTROPHE_SAMPLES = [
    w.replace("'", "’") for w in [
        "1923'te", "2026'da", "2'nci", "3'üncü", "6'ncı", "7'nci",
        "100'üncü", "50'si", "80'lerde", "09.00'da", "15.00'te", "14.45'te"
    ]
]


# 2. Invalid number, ordinal, year, and clock-time inflections -> Expected Top-1 suggestion
INVALID_NUMBER_PAIRS = [
    # Ordinals (TDK rule: 2, 6, 7, 20, 50 end in vowel -> 'nci/'ncı, NOT *'inci/*'ıncı; consonant-end -> 'inci/'üncü/'ıncı/'uncu, NOT *'nci/*'ncü)
    ("1'nci", "1'inci"),
    ("2'inci", "2'nci"),
    ("3'ncü", "3'üncü"),
    ("4'ncü", "4'üncü"),
    ("5'nci", "5'inci"),
    ("6'ıncı", "6'ncı"),
    ("6'nci", "6'ncı"),
    ("7'inci", "7'nci"),
    ("8'nci", "8'inci"),
    ("9'ncu", "9'uncu"),
    ("10'ncu", "10'uncu"),
    ("12'inci", "12'nci"),
    ("16'ıncı", "16'ncı"),
    ("17'inci", "17'nci"),
    ("20'inci", "20'nci"),
    ("30'ncu", "30'uncu"),
    ("40'ncı", "40'ıncı"),
    ("50'inci", "50'nci"),
    ("60'ncı", "60'ıncı"),
    ("70'nci", "70'inci"),
    ("80'nci", "80'inci"),
    ("90'ncı", "90'ıncı"),
    ("100'ncü", "100'üncü"),
    ("1000'nci", "1000'inci"),
    ("2'incisi", "2'ncisi"),
    ("6'ıncısı", "6'ncısı"),
    ("7'incisi", "7'ncisi"),
    ("20'incisi", "20'ncisi"),
    ("50'incisi", "50'ncisi"),
    ("3'ncüsü", "3'üncüsü"),
    ("4'ncüsü", "4'üncüsü"),
    ("100'ncüsü", "100'üncüsü"),
    # Consonant assimilation & vowel harmony errors on single digits & tens
    ("1'te", "1'de"),
    ("1'ten", "1'den"),
    ("2'te", "2'de"),
    ("2'ten", "2'den"),
    ("2'e", "2'ye"),
    ("3'de", "3'te"),
    ("3'den", "3'ten"),
    ("3'da", "3'te"),
    ("4'de", "4'te"),
    ("4'den", "4'ten"),
    ("4'da", "4'te"),
    ("5'de", "5'te"),
    ("5'den", "5'ten"),
    ("5'da", "5'te"),
    ("6'ta", "6'da"),
    ("6'tan", "6'dan"),
    ("6'de", "6'da"),
    ("6'a", "6'ya"),
    ("7'te", "7'de"),
    ("7'ten", "7'den"),
    ("7'da", "7'de"),
    ("7'e", "7'ye"),
    ("8'te", "8'de"),
    ("8'ten", "8'den"),
    ("9'ta", "9'da"),
    ("9'tan", "9'dan"),
    ("10'ta", "10'da"),
    ("10'tan", "10'dan"),
    ("20'te", "20'de"),
    ("20'da", "20'de"),
    ("30'ta", "30'da"),
    ("40'da", "40'ta"),
    ("40'dan", "40'tan"),
    ("50'te", "50'de"),
    ("50'da", "50'de"),
    ("60'da", "60'ta"),
    ("60'dan", "60'tan"),
    ("70'de", "70'te"),
    ("70'den", "70'ten"),
    ("70'da", "70'te"),
    ("80'te", "80'de"),
    ("80'ten", "80'den"),
    ("90'ta", "90'da"),
    ("90'tan", "90'dan"),
    ("100'te", "100'de"),
    ("100'ten", "100'den"),
    ("1000'te", "1000'de"),
    # Historical & contemporary years
    ("1071'te", "1071'de"),
    ("1453'de", "1453'te"),
    ("1453'den", "1453'ten"),
    ("1881'te", "1881'de"),
    ("1915'de", "1915'te"),
    ("1915'den", "1915'ten"),
    ("1919'ta", "1919'da"),
    ("1920'te", "1920'de"),
    ("1923'de", "1923'te"),
    ("1923'den", "1923'ten"),
    ("1923'da", "1923'te"),
    ("1923'deki", "1923'teki"),
    ("1923'dür", "1923'tür"),
    ("1923'dü", "1923'tü"),
    ("1938'te", "1938'de"),
    ("1938'ten", "1938'den"),
    ("2000'te", "2000'de"),
    ("2023'de", "2023'te"),
    ("2023'den", "2023'ten"),
    ("2024'de", "2024'te"),
    ("2024'den", "2024'ten"),
    ("2025'de", "2025'te"),
    ("2025'den", "2025'ten"),
    ("2026'ta", "2026'da"),
    ("2026'tan", "2026'dan"),
    ("2026'de", "2026'da"),
    ("2026'a", "2026'ya"),
    # Clock times (.00 and .MM errors)
    ("09.00'de", "09.00'da"),
    ("09.00'ta", "09.00'da"),
    ("10.00'de", "10.00'da"),
    ("10.00'ta", "10.00'da"),
    ("12.00'da", "12.00'de"),
    ("12.00'te", "12.00'de"),
    ("13.00'da", "13.00'te"),
    ("13.00'de", "13.00'te"),
    ("13.00'dan", "13.00'ten"),
    ("14.00'da", "14.00'te"),
    ("14.00'de", "14.00'te"),
    ("15.00'da", "15.00'te"),
    ("15.00'de", "15.00'te"),
    ("15.00'dan", "15.00'ten"),
    ("15.00'den", "15.00'ten"),
    ("16.00'de", "16.00'da"),
    ("16.00'ta", "16.00'da"),
    ("17.00'da", "17.00'de"),
    ("17.00'te", "17.00'de"),
    ("18.00'da", "18.00'de"),
    ("18.00'te", "18.00'de"),
    ("19.00'de", "19.00'da"),
    ("20.00'da", "20.00'de"),
    ("20.00'te", "20.00'de"),
    ("23.00'da", "23.00'te"),
    ("23.00'de", "23.00'te"),
    ("24.00'da", "24.00'te"),
    ("24.00'de", "24.00'te"),
    ("09.15'de", "09.15'te"),
    ("10.30'ta", "10.30'da"),
    ("14.45'de", "14.45'te"),
    ("16.20'te", "16.20'de"),
    ("18.40'da", "18.40'ta"),
    # Distributives
    ("2'er", "2'şer"),
    ("6'ar", "6'şar"),
    ("7'er", "7'şer"),
    ("20'er", "20'şer"),
    ("50'er", "50'şer"),
    ("3'şer", "3'er"),
    ("5'şer", "5'er"),
]


def main():
    all_valid = VALID_NUMBER_INFLECTIONS + CURLY_APOSTROPHE_SAMPLES
    acc_valid, rej_valid = check_words(all_valid)

    invalid_inputs = [w for w, _ in INVALID_NUMBER_PAIRS]
    acc_invalid, rej_invalid = check_words(invalid_inputs)

    sugs = get_suggestions(invalid_inputs)
    top1_hits = 0
    top3_hits = 0
    misses = []
    for wrong, expected in INVALID_NUMBER_PAIRS:
        cand_list = sugs.get(wrong, [])
        if cand_list and cand_list[0] == expected:
            top1_hits += 1
            top3_hits += 1
        elif expected in cand_list[:3]:
            top3_hits += 1
            misses.append((wrong, expected, cand_list[:5]))
        else:
            misses.append((wrong, expected, cand_list[:5]))

    print("=" * 72)
    print("TURKSPELL NUMBERS, ORDINALS, DATES & CLOCK TIMES AUDIT")
    print("=" * 72)
    print(f"1. Valid Number/Date/Time Acceptance : {len(acc_valid)}/{len(all_valid)} ({100.0 * len(acc_valid) / len(all_valid):.1f}%)")
    if rej_valid:
        print(f"   REJECTED VALID FORMS ({len(rej_valid)}): {rej_valid}")
    print(f"2. Invalid Number Suffix Rejection   : {len(rej_invalid)}/{len(invalid_inputs)} ({100.0 * len(rej_invalid) / len(invalid_inputs):.1f}%)")
    if acc_invalid:
        print(f"   LEAKED INVALID FORMS ({len(acc_invalid)}): {acc_invalid}")
    print(f"3. Suggestion Accuracy (Top-1)       : {top1_hits}/{len(INVALID_NUMBER_PAIRS)} ({100.0 * top1_hits / len(INVALID_NUMBER_PAIRS):.1f}%)")
    print(f"   Suggestion Accuracy (Top-3)       : {top3_hits}/{len(INVALID_NUMBER_PAIRS)} ({100.0 * top3_hits / len(INVALID_NUMBER_PAIRS):.1f}%)")
    if misses:
        print("\n   NON-TOP-1 SUGGESTIONS:")
        for wrong, exp, cands in misses:
            print(f"     {wrong:15s} -> expected: {exp:15s} | got: {cands}")
    print("=" * 72)

    if rej_valid or acc_invalid or misses:
        sys.exit(1)


if __name__ == "__main__":
    main()
