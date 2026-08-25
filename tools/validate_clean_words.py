# -*- coding: utf-8 -*-
"""Validate a 'clean word' list against Turkish authorities BEFORE reporting
false positives.

Problem this solves: benchmark/eval reports that seed their "correct words"
list from corpus-mined or LLM-enriched sources (category_a.json,
enrich_custom_entries.py output, etc.) end up counting deliberately-rejected
words — unhatted variants of hatted-only TDK entries (neftileşmek vs
neftîleşmek), inflected forms (laciverdi), or non-words (tilen, kesbi) — as
false positives. They are not: flagging them is correct behavior.

This script partitions any candidate "clean word" list into:
  VALID          - present in TDK and/or Dil Derneği (flag-stripped, hatted
                   AND unhatted forms matched exactly)
  HATTED_ONLY    - only the hatted (â î û) variant exists in the authorities;
                   the unhatted input SHOULD be flagged -> excluded from FP count
  NOT_A_WORD     - in no authority list; cannot be counted as a false positive

Only VALID words that hunspell flags are reported as true false positives.

Usage:
    python tools/validate_clean_words.py words.txt
    echo "kesbi\\nev\\nyanlız" | python tools/validate_clean_words.py -
"""
import os
import subprocess
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTHORITY_FILES = [
    os.path.join(BASE_DIR, "raw_data", "tdk_words.txt"),
    os.path.join(BASE_DIR, "raw_data", "tdk_words_new.txt"),
    os.path.join(BASE_DIR, "raw_data", "dil_dernegi_words.txt"),
]
HATS = str.maketrans("âîûÂÎÛ", "aiuAIU")


def tlc(s: str) -> str:
    """Turkish-aware lowercase."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def load_authorities():
    """Return (exact_forms, dehatted_aliases, hatted_forms).

    exact_forms     - every authority entry exactly as listed, lowercased,
                      flags stripped. Membership here means "this exact
                      spelling is sanctioned".
    dehatted_aliases- ASCII-folded spellings of HATTED entries (e.g.
                      'neftilesmek' from 'neftîleşmek'). Kept SEPARATE so a
                      folded input can be detected as a hatted-only variant
                      rather than silently counted as valid.
    hatted_forms    - only entries containing â/î/û.
    """
    exact_forms = set()
    dehatted_aliases = set()
    hatted_forms = set()
    for path in AUTHORITY_FILES:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if not w:
                    continue
                head = w.split("/")[0].strip()
                if not head:
                    continue
                low = tlc(head)
                exact_forms.add(low)
                if any(c in low for c in "âîû"):
                    hatted_forms.add(low)
                    dehatted_aliases.add(low.translate(HATS))
    return exact_forms, dehatted_aliases, hatted_forms


def classify(word: str, exact_forms: set, dehatted_aliases: set,
             hatted_forms: set) -> str:
    w = tlc(word.strip())
    if w in hatted_forms:
        return "VALID"          # itself a legitimate hatted entry
    if w in exact_forms:
        return "VALID"          # exact unhatted authority listing (derhal...)
    if w in dehatted_aliases:
        return "HATTED_ONLY"    # neftileşmek <- neftîleşmek
    return "NOT_A_WORD"         # tilen, kesbi, laciverdi


def hunspell_flagged(words):
    """Run hunspell -d tr -l over the words; return the set it flags."""
    p = subprocess.run(
        ["hunspell", "-d", "tr", "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    return set(l.strip() for l in p.stdout.splitlines() if l.strip())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    if src == "-":
        words = [l.strip() for l in sys.stdin if l.strip()]
    else:
        with open(src, encoding="utf-8") as f:
            words = [l.strip() for l in f if l.strip()]

    all_forms, dehatted_aliases, hatted_forms = load_authorities()
    flagged = hunspell_flagged(words)

    buckets = {"VALID": [], "HATTED_ONLY": [], "NOT_A_WORD": []}
    for w in words:
        buckets[classify(w, all_forms, dehatted_aliases, hatted_forms)].append(w)

    true_fp = [w for w in buckets["VALID"] if w in flagged]

    print(f"Input words: {len(words)}")
    print(f"  VALID (in TDK/DD):              {len(buckets['VALID'])}")
    print(f"  HATTED_ONLY (must be flagged):  {len(buckets['HATTED_ONLY'])}")
    print(f"  NOT_A_WORD (cannot be an FP):   {len(buckets['NOT_A_WORD'])}")
    print()
    print("=== TRUE FALSE POSITIVES (valid + flagged) ===")
    if true_fp:
        for w in true_fp:
            mark = " <-- FLAGGED" if w in flagged else ""
            print(f"  {w}{mark}")
        print(f"\nTotal: {len(true_fp)}  "
              f"(precision impact: {len(true_fp)}/{len(words)})")
    else:
        print("  none")

    if buckets["HATTED_ONLY"]:
        print("\n--- Hatted-only variants correctly flagged "
              "(NOT false positives) ---")
        for w in buckets["HATTED_ONLY"]:
            state = "flagged (correct)" if w in flagged else "accepted (LEAK!)"
            print(f"  {w} -> {state}")

    if buckets["NOT_A_WORD"]:
        print("\n--- Not in any authority (remove from clean list!) ---")
        for w in buckets["NOT_A_WORD"]:
            print(f"  {w}")


if __name__ == "__main__":
    main()
