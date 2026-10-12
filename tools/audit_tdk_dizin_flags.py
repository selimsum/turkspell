# -*- coding: utf-8 -*-
"""
TDK Dizin (80,672 Entries) Full Root, Homonym, and Flag Completeness Audit
==========================================================================
Audits all entries in `raw_data/tdk_dizin_2026.json` against the compiled
`tr.dic` and `tr.aff` (via Hunspell CLI) without waiting for words to appear
in a corpus:
  1. Explicit TDK `"e"` inflection verification (palatal-L, vowel-drop, gemination,
     voicing, irregular su, aorist vowel).
  2. Homonym collision audit (words with multiple TDK entries where a special `"e"`
     paradigm overwrote the regular Turkish paradigm or vice versa).
  3. Unflagged (`flags == ""`) single-word roots in `tr.dic` that are inflectable.
  4. Verbs (`-mak/-mek`) in TDK dizin missing verb flags or failing basic inflections.
"""

import os
import sys
import re
import json
import shutil
import subprocess
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent

winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
HUNSPELL_BIN = shutil.which("hunspell") or "hunspell"

VOWELS = "aeıioöuüâîû"
BACK_VOWELS = set("aıouâû")
ROUND_VOWELS = set("oöuüû")


def tr_lower(s: str) -> str:
    return (
        s.replace("İ", "i")
        .replace("I", "ı")
        .replace("Î", "î")
        .replace("Â", "â")
        .replace("Û", "û")
        .lower()
    )


def hunspell_check_batch(words: list[str], dict_prefix: str) -> set[str]:
    """Returns subset of `words` REJECTED by Hunspell."""
    rejected = set()
    batch_size = 25000
    unique_w = list(dict.fromkeys(w for w in words if w))
    for i in range(0, len(unique_w), batch_size):
        batch = unique_w[i : i + batch_size]
        p = subprocess.run(
            [HUNSPELL_BIN, "-d", dict_prefix, "-l"],
            input="\n".join(batch) + "\n",
            text=True,
            capture_output=True,
            encoding="utf-8",
        )
        for line in p.stdout.splitlines():
            w = line.strip()
            if w:
                rejected.add(w)
    return rejected


def get_last_vowel(word: str) -> str:
    for ch in reversed(word):
        if ch in VOWELS:
            return ch
    return "a"


def regular_noun_3sg(word: str) -> str:
    """Computes regular unvoiced Turkish 3sg possessive / accusative for a stem."""
    lv = get_last_vowel(word)
    back = lv in BACK_VOWELS
    rnd = lv in ROUND_VOWELS
    v_high = "u" if (back and rnd) else ("ı" if back else ("ü" if rnd else "i"))
    if word[-1] in VOWELS:
        return word + "s" + v_high
    return word + v_high


def regular_noun_dative(word: str) -> str:
    lv = get_last_vowel(word)
    back = lv in BACK_VOWELS
    v_low = "a" if back else "e"
    if word[-1] in VOWELS:
        return word + "y" + v_low
    return word + v_low


def regular_noun_locative(word: str) -> str:
    lv = get_last_vowel(word)
    back = lv in BACK_VOWELS
    v_low = "a" if back else "e"
    d_c = "t" if word[-1] in "çfhkpsşt" else "d"
    return word + d_c + v_low


def reconstruct_tdk_e_forms(lemma: str, e_str: str) -> list[tuple[str, str]]:
    """
    Given a single-word lowercase lemma and its TDK 'e' string (e.g. '-ğı', '-bi',
    '-li', '-lü', '-klı', '-hri', '-ddi', '-ar', '-der', '-çı, -cı'),
    returns a list of (category, expected_surface_form).
    """
    results = []
    # Clean up e_str (sometimes has extra words or multiple comma-separated parts)
    parts = [p.strip() for p in e_str.split(",")]
    for part in parts:
        # Take only first token if space-corrupted (like "-yu acıtabilme")
        tok = part.split()[0].strip() if part.split() else ""
        if not tok.startswith("-"):
            continue
        suf = tok[1:]
        if not suf or "'" in suf:
            continue

        # 1. Verb aorist annotations on -mak/-mek
        if lemma.endswith(("mak", "mek")):
            stem = lemma[:-3]
            if suf in ("ar", "er", "ır", "ir", "ur", "ür", "r"):
                results.append(("verb_aorist", stem + suf))
            elif suf in ("der", "dar") and stem.endswith("t"):
                results.append(("verb_voicing_aorist", stem[:-1] + suf))
            continue

        # 2. Noun/Adjective annotations
        # Case A: Palatal L (-li, -lü on back-vowel l-ending stem)
        if lemma.endswith("l") and suf in ("li", "lü"):
            results.append(("palatal_l", lemma + suf[1:]))
            # Also dative -le
            results.append(("palatal_l_dat", lemma + "e"))
            continue

        # Case B: Gemination (-llü, -lli, -ddi, -ffı, -kkı, -rrı, -bbi, -ccı, -ssı, -ttı, -zzı, etc.)
        if len(suf) >= 3 and suf[0] == suf[1] and lemma.endswith(suf[0]):
            results.append(("gemination", lemma + suf[1:]))
            continue
        # Gemination + voicing (e.g. tıp -> -bbı, hac -> -ccı, hak -> -kkı, şer -> -rri)
        if len(suf) == 3 and suf[0] == suf[1] and suf[0] in "bcdgğ" and lemma[-1] in "pçtk":
            results.append(("gemination_voiced", lemma[:-1] + suf))
            continue

        # Case C: Irregular su (-yu)
        if lemma.endswith("su") and suf == "yu":
            results.append(("irregular_su", lemma + "yu"))
            continue

        # Case D: Standard voicing (-ğı, -ği, -ğu, -ğü, -bı, -bi, -bu, -bü, -cı, -ci, -cu, -cü, -dı, -di, -du, -dü, -gi, -gü)
        if suf in ("ğı", "ği", "ğu", "ğü") and lemma.endswith("k"):
            results.append(("voicing_k", lemma[:-1] + suf))
            continue
        if suf in ("gi", "gü", "gu", "gı") and lemma.endswith("k"):
            results.append(("voicing_nk", lemma[:-1] + suf))
            continue
        if suf in ("bı", "bi", "bu", "bü") and lemma.endswith("p"):
            results.append(("voicing_p", lemma[:-1] + suf))
            continue
        if suf in ("cı", "ci", "cu", "cü") and lemma.endswith("ç"):
            results.append(("voicing_c", lemma[:-1] + suf))
            continue
        if suf in ("dı", "di", "du", "dü") and lemma.endswith("t"):
            results.append(("voicing_t", lemma[:-1] + suf))
            continue

        # Case E: Explicit unvoiced annotation (-pı, -pi, -çı, -çi, -tı, -ti, -kı, -ki, -tu, -tü)
        if suf in ("pı", "pi", "pu", "pü", "çı", "çi", "çu", "çü", "tı", "ti", "tu", "tü", "kı", "ki", "ku", "kü") and lemma.endswith(suf[0]):
            results.append(("explicit_unvoiced", lemma + suf[1:]))
            continue

        # Case F: Vowel drop (hece düşmesi), e.g. akıl -> -klı, şehir -> -hri, ağız -> -ğzı, vakit -> -kti, akit -> -kdi, kayıp -> -ybı
        # In TDK notation, `suf` starts with the consonant BEFORE the dropped vowel!
        if len(lemma) >= 3 and len(suf) >= 3:
            # Find penultimate consonant in lemma
            c_before_drop = lemma[-3]
            c_last = lemma[-1]
            if suf[0] == c_before_drop:
                # Reconstruct dropped stem: lemma[:-2] + suf[1:]
                results.append(("vowel_drop", lemma[:-2] + suf[1:]))
                continue
    return results


def main():
    dict_prefix = str(ROOT_DIR / "tr")
    tdk_path = ROOT_DIR / "raw_data" / "tdk_dizin_2026.json"
    print(f"Loading {tdk_path} ...")
    with open(tdk_path, encoding="utf-8") as f:
        tdk_entries = json.load(f)
    print(f"Loaded {len(tdk_entries):,} TDK entries.")

    # Load tr.dic
    dic_heads = defaultdict(set)
    with open(ROOT_DIR / "tr.dic", encoding="utf-8") as f:
        lines = f.read().splitlines()[1:]
    for line in lines:
        if not line.strip():
            continue
        if "/" in line:
            h, fl = line.split("/", 1)
        else:
            h, fl = line.strip(), ""
        dic_heads[h].add(fl)

    # Group single-word lowercase TDK entries by lemma
    by_lemma = defaultdict(list)
    for item in tdk_entries:
        m = item.get("m", "").strip()
        if not m or " " in m or "-" in m or not m[0].islower():
            continue
        by_lemma[m].append(item)

    print(f"Unique single-word lowercase TDK lemmas: {len(by_lemma):,}")

    # 1. Collect all explicit 'e' test forms and homonym regular test forms
    e_tests = []  # (lemma, category, e_str, surface_form)
    homonym_regular_tests = []  # (lemma, e_list, reg_3sg, reg_dat, reg_loc)
    verb_tests = []  # (lemma, past_3sg, pres_3sg, vn_ma)
    unflagged_noun_tests = []  # (lemma, loc_form, pl_form)

    for lemma, items in by_lemma.items():
        # Check explicit 'e' annotations
        e_vals = [it.get("e", "") for it in items if it.get("e")]
        has_plain_entry = any(not it.get("e") for it in items)

        for it in items:
            e_str = it.get("e", "")
            if e_str:
                for cat, surf in reconstruct_tdk_e_forms(lemma, e_str):
                    e_tests.append((lemma, cat, e_str, surf))

        # Check homonyms: lemma has BOTH a plain entry (no 'e') AND an entry with special 'e'
        if len(items) >= 2 and has_plain_entry and e_vals and not lemma.endswith(("mak", "mek")):
            # If one of the 'e' entries is gemination, vowel_drop, palatal_l, or voicing
            special_cats = [cat for e_s in e_vals for cat, _ in reconstruct_tdk_e_forms(lemma, e_s)]
            if any(c in ("gemination", "gemination_voiced", "vowel_drop", "palatal_l") for c in special_cats):
                reg_3sg = regular_noun_3sg(lemma)
                reg_dat = regular_noun_dative(lemma)
                reg_loc = regular_noun_locative(lemma)
                homonym_regular_tests.append((lemma, e_vals, reg_3sg, reg_dat, reg_loc))

        # Check verbs (-mak/-mek)
        if lemma.endswith(("mak", "mek")) and len(lemma) >= 5:
            stem = lemma[:-3]
            back = lemma.endswith("mak")
            v_low = "a" if back else "e"
            lv = get_last_vowel(stem) if any(c in VOWELS for c in stem) else v_low
            rnd = lv in ROUND_VOWELS
            v_high = "u" if (back and rnd) else ("ı" if back else ("ü" if rnd else "i"))
            d_c = "t" if (stem and stem[-1] in "çfhkpsşt") else "d"
            past_3sg = stem + d_c + v_high
            vn_ma = stem + "m" + v_low + "s" + ("ı" if back else "i")
            verb_tests.append((lemma, past_3sg, vn_ma))

        # Check unflagged roots in tr.dic
        if lemma in dic_heads and dic_heads[lemma] == {""} and len(lemma) >= 2 and not lemma.endswith(("mak", "mek")):
            loc_f = regular_noun_locative(lemma)
            lv = get_last_vowel(lemma)
            pl_f = lemma + ("lar" if lv in BACK_VOWELS else "ler")
            unflagged_noun_tests.append((lemma, loc_f, pl_f))

    # Batch check all candidate surface forms with Hunspell
    all_words_to_check = []
    for _, _, _, surf in e_tests:
        all_words_to_check.append(surf)
    for _, _, r3, rd, rl in homonym_regular_tests:
        all_words_to_check.extend([r3, rd, rl])
    for lemma, p3, vn in verb_tests:
        all_words_to_check.extend([lemma, p3, vn])
    for lemma, loc_f, pl_f in unflagged_noun_tests:
        all_words_to_check.extend([loc_f, pl_f])

    print(f"Running Hunspell batch check on {len(set(all_words_to_check)):,} generated TDK test forms...")
    rejected_set = hunspell_check_batch(all_words_to_check, dict_prefix)

    # Report 1: Explicit 'e' failures by category
    print("\n" + "=" * 80)
    print("1. EXPLICIT TDK 'e' INFLECTION FAILURES BY CATEGORY")
    print("=" * 80)
    e_fails_by_cat = defaultdict(list)
    for lemma, cat, e_str, surf in e_tests:
        if surf in rejected_set:
            e_fails_by_cat[cat].append((lemma, e_str, surf))

    for cat, fails in sorted(e_fails_by_cat.items(), key=lambda x: -len(x[1])):
        print(f"\n[{cat}] Failed: {len(fails)}")
        for lemma, e_str, surf in fails[:40]:
            in_dic = lemma in dic_heads
            fl_len = max((len(f) for f in dic_heads[lemma]), default=-1)
            print(f"  {lemma:<22} (e={e_str:<10}) -> expected: {surf:<22} [in_dic={in_dic}, flags_len={fl_len}]")

    # Report 2: Homonym Regular Inflection Overwrites (like kül, hal, sır, şık, cebir)
    print("\n" + "=" * 80)
    print("2. HOMONYM COLLISIONS (PLAIN ENTRY OVERWRITTEN BY SPECIAL 'e' ENTRY)")
    print("=" * 80)
    homonym_fails = []
    for lemma, e_vals, r3, rd, rl in homonym_regular_tests:
        failed_forms = [w for w in (r3, rd, rl) if w in rejected_set]
        if failed_forms:
            homonym_fails.append((lemma, e_vals, failed_forms))
    print(f"Total homonyms with rejected regular inflections: {len(homonym_fails)}")
    for lemma, e_vals, failed_forms in homonym_fails[:60]:
        print(f"  {lemma:<18} (special e={e_vals}) -> rejected regular: {failed_forms}")

    # Report 3: Verbs (-mak/-mek) failing basic inflections
    print("\n" + "=" * 80)
    print("3. TDK VERBS (-mak/-mek) FAILING BASIC INFLECTIONS")
    print("=" * 80)
    verb_fails = []
    for lemma, p3, vn in verb_tests:
        if p3 in rejected_set or vn in rejected_set:
            verb_fails.append((lemma, p3 in rejected_set, vn in rejected_set))
    print(f"Total TDK verbs failing past_3sg or verbal_noun_3sg: {len(verb_fails)}")
    for lemma, f_p3, f_vn in verb_fails[:50]:
        in_dic = lemma in dic_heads
        fl_len = max((len(f) for f in dic_heads[lemma]), default=-1)
        print(f"  {lemma:<26} [in_dic={in_dic}, flags_len={fl_len}] fail_past={f_p3}, fail_vn={f_vn}")

    # Report 4: Unflagged single-word lemmas in tr.dic
    print("\n" + "=" * 80)
    print("4. UNFLAGGED SINGLE-WORD TDK LEMMAS IN tr.dic (REJECTING LOCATIVE & PLURAL)")
    print("=" * 80)
    unflagged_fails = []
    for lemma, loc_f, pl_f in unflagged_noun_tests:
        if loc_f in rejected_set and pl_f in rejected_set:
            unflagged_fails.append(lemma)
    print(f"Total unflagged TDK lemmas in tr.dic rejecting both locative & plural: {len(unflagged_fails)}")
    print("  All:", unflagged_fails)

    # Report 5: Bare single-word TDK lemmas rejected by Hunspell
    print("\n" + "=" * 80)
    print("5. BARE SINGLE-WORD TDK LEMMAS REJECTED BY HUNSPELL")
    print("=" * 80)
    bare_rejected = hunspell_check_batch(list(by_lemma.keys()), dict_prefix)
    print(f"Total bare single-word lowercase TDK lemmas rejected: {len(bare_rejected)}")
    for w in sorted(bare_rejected)[:80]:
        print(f"  {w}")


if __name__ == "__main__":
    main()
