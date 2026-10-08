# -*- coding: utf-8 -*-
"""
tools/audit_morphological_coverage.py
======================================
Automated Morphological Quality & Completeness Audit Suite for Turkspell

Implements 3 comprehensive audit engines:
1. Method 2: Combinatorial Matrix Fuzzing (Tests theoretical Turkish suffix chains across phonetic classes)
2. Method 3: Affix Symmetry Linter (Static comparison across parallel harmonic flag families)
3. Method 4: Cross-POS Collision & Attribute Leak Audit (Audits homonyms and POS attribute leaks)
"""

import os
import sys
import re
import json
import shutil
import subprocess
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = os.environ.get("TURKSPELL_DICT", str(ROOT_DIR / "tr"))

# Find hunspell binary
winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
HUNSPELL_BIN = shutil.which("hunspell") or "hunspell"


def run_hunspell_check(words: list[str], dict_path: str = DICT_PATH) -> tuple[set[str], set[str]]:
    """Runs hunspell -l on a batch of words and returns (accepted_set, rejected_set)."""
    if not words:
        return set(), set()
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    rejected = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    accepted = set(words) - rejected
    return accepted, rejected


# ============================================================================
# METHOD 3: AFFIX SYMMETRY LINTER
# ============================================================================

def audit_affix_symmetry() -> dict:
    """
    Statically analyzes flag families in generate_grammar_rules.py or tr.aff
    to detect harmonic asymmetries (suffixes present in one vowel harmonic flag
    but missing in its sister flags).
    """
    print("\n" + "="*70)
    print("METHOD 3: Affix Symmetry Linter (Harmonic Flag Family Completeness)")
    print("="*70)

    sys.path.insert(0, str(ROOT_DIR / "build"))
    from generate_grammar_rules import generate_stage2_flags

    blocks = generate_stage2_flags()
    family_rules = defaultdict(dict)
    
    # Group into families
    # p-family: 3sg participles (pA, pE, pO, pU)
    # q-family: 1/2 person participles (qA, qE, qO, qU)
    # c-family: soft copula (cA, cE, cU, cI)
    # u-family: hard copula (uA, uE, uO, uU)
    # v-family: vowel copula (vA, vE)
    # s-family: past copula (sA, sE)
    families = {
        "Participle 3sg Cases": ["pA", "pE", "pO", "pU"],
        "Participle 1/2 Person Cases": ["qA", "qE", "qO", "qU"],
        "Soft Copulas": ["cA", "cE", "cU", "cI"],
        "Hard Copulas": ["uA", "uE", "uO", "uU"],
        "Vowel Copulas": ["vA", "vE"],
        "Past Copulas": ["sA", "sE"],
    }

    flag_raw_rules = {}
    for blk in blocks:
        lines = blk.strip().split("\n")
        header = lines[0].split()
        if len(header) >= 2:
            fl = header[1]
            rules = []
            for l in lines[1:]:
                parts = l.split()
                if len(parts) >= 4:
                    rules.append(parts[3])
            flag_raw_rules[fl] = rules

    asymmetry_report = {}

    for fam_name, fl_list in families.items():
        # Check rule counts and coverage
        counts = {fl: len(flag_raw_rules.get(fl, [])) for fl in fl_list}
        print(f"\n[Family: {fam_name}] Flags: {fl_list}")
        for fl in fl_list:
            print(f"  {fl:4}: {counts[fl]:2} rules -> {flag_raw_rules.get(fl, [])}")

        # Check for specific structural gaps between unrounded and rounded sisters
        # e.g., pA vs pO, pE vs pU
        # If unrounded has an ending (like 'nca' or 'nda') that is missing in rounded or vice versa:
        gaps = []
        # Normalized checks: check semantic suffixes
        # Map letters to harmony patterns:
        def normalize_suffix(sfx: str) -> str:
            # normalize vowels to V (low: a/e) and H (high: ı/i/u/ü)
            res = []
            for ch in sfx:
                if ch in "ae":
                    res.append("A")
                elif ch in "ıiuü":
                    res.append("I")
                else:
                    res.append(ch)
            return "".join(res)

        normalized_sets = {fl: {normalize_suffix(r) for r in flag_raw_rules.get(fl, [])} for fl in fl_list}
        all_norm_suffixes = set().union(*normalized_sets.values())

        for sfx_norm in sorted(all_norm_suffixes):
            missing_in = [fl for fl in fl_list if sfx_norm not in normalized_sets[fl]]
            present_in = [fl for fl in fl_list if sfx_norm in normalized_sets[fl]]
            # If present in some but missing in others in the same family:
            if missing_in and present_in:
                # Rounded families often have extra rounded variants, but core cases should match
                # Check if it's missing from an unrounded flag while present in rounded or vice-versa
                gaps.append({
                    "suffix_pattern": sfx_norm,
                    "present_in": present_in,
                    "missing_in": missing_in
                })

        if gaps:
            print(f"  Found {len(gaps)} harmonic pattern differences:")
            for g in gaps:
                print(f"    * Pattern '{g['suffix_pattern']}': Present in {g['present_in']}, Missing in {g['missing_in']}")
        else:
            print("  Symmetry: PERFECTLY BALANCED")

        asymmetry_report[fam_name] = {"counts": counts, "gaps": gaps}

    return asymmetry_report


# ============================================================================
# METHOD 4: CROSS-POS COLLISION & LEAK AUDIT
# ============================================================================

def audit_cross_pos_collisions() -> dict:
    """
    Scans dictionaries and lexicons for lemmas appearing as multiple parts of speech
    or having multiple definitions in TDK, checking for morphological attribute leaks.
    """
    print("\n" + "="*70)
    print("METHOD 4: Cross-POS Collision & Attribute Leak Audit")
    print("="*70)

    tdk_path = ROOT_DIR / "raw_data" / "tdk_dizin_2026.json"
    zemberek_path = ROOT_DIR / "lexicons" / "zemberek_lexicon.json"

    with open(tdk_path, "r", encoding="utf-8") as f:
        tdk_data = json.load(f)

    with open(zemberek_path, "r", encoding="utf-8") as f:
        zemberek_data = json.load(f)

    # 1. Find all homonyms in TDK
    tdk_by_lemma = defaultdict(list)
    for it in tdk_data:
        m = it.get("m", "").strip()
        if m:
            tdk_by_lemma[m.lower()].append(it)

    homonyms_in_tdk = {k: v for k, v in tdk_by_lemma.items() if len(v) > 1}
    print(f"Total unique headwords in TDK dizin: {len(tdk_by_lemma):,}")
    print(f"Lemmas with multiple TDK entries (homonyms/senses): {len(homonyms_in_tdk):,}")

    # 2. Find words that are both Verb and Noun in Turkish
    zemberek_by_lemma = defaultdict(list)
    for it in zemberek_data:
        lem = it.get("lemma", "").strip().lower()
        if lem:
            zemberek_by_lemma[lem].append(it)

    dual_pos_lemmas = []
    for lem, entries in zemberek_by_lemma.items():
        pos_set = {e.get("pos") for e in entries}
        if "Verb" in pos_set and ("Noun" in pos_set or "Adjective" in pos_set):
            dual_pos_lemmas.append((lem, pos_set, entries))

    print(f"Lemmas with both Verb and Noun/Adjective entries in Zemberek: {len(dual_pos_lemmas):,}")

    # 3. Check for specific attribute leaks in tr.dic
    # Inspect all verbs in tr.dic to verify none have illegal voicing or noun flags
    sys.path.insert(0, str(ROOT_DIR / "build"))
    from utf8_flag_mapping import LONG_TO_UTF8, UTF8_TO_LONG

    vk_char = LONG_TO_UTF8.get("VK")
    vl_char = LONG_TO_UTF8.get("VL")
    vm_char = LONG_TO_UTF8.get("VM")
    vn_char = LONG_TO_UTF8.get("VN")
    voicing_verb_chars = {vk_char, vl_char, vm_char, vn_char} - {None}

    dic_path = ROOT_DIR / "tr.dic"
    voicing_verbs_found = defaultdict(list)
    with open(dic_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "/" not in line:
                continue
            word, flags = line.split("/", 1)
            for ch in flags:
                if ch in voicing_verb_chars:
                    voicing_verbs_found[UTF8_TO_LONG.get(ch)].append(word)

    print("\n[Voicing Verb Stems in Compiled tr.dic]:")
    for fl_name, words in voicing_verbs_found.items():
        print(f"  Flag {fl_name:2} ({len(words):2} verbs): {words[:10]}{'...' if len(words) > 10 else ''}")

    # Verify suspicious stems
    suspicious_voicing_verbs = []
    for fl_name, words in voicing_verbs_found.items():
        for w in words:
            # In Turkish, voicing verbs must end in 't' before mak/mek (tatmak, ditmek, gütmek, gitmek, -etmek)
            stem = w[:-3] if w.endswith(("mak", "mek")) else w
            if not stem.endswith("t"):
                suspicious_voicing_verbs.append((w, fl_name, "Stem does not end in 't'"))
            elif not (w.endswith("etmek") or w in {"tatmak", "ditmek", "gitmek", "gütmek"}):
                suspicious_voicing_verbs.append((w, fl_name, "Stem is not in known voicing verb list"))

    print(f"\nSuspicious Voicing Verbs Found: {len(suspicious_voicing_verbs)}")
    for sv in suspicious_voicing_verbs:
        print(f"  * {sv[0]} (Flag: {sv[1]}): {sv[2]}")

    return {
        "homonyms_count": len(homonyms_in_tdk),
        "dual_pos_count": len(dual_pos_lemmas),
        "suspicious_voicing_verbs": suspicious_voicing_verbs
    }


# ============================================================================
# METHOD 2: COMBINATORIAL MATRIX FUZZING
# ============================================================================

def audit_combinatorial_matrix() -> dict:
    """
    Generates theoretical Turkish suffix chains across a representative matrix
    of phonological classes and tests them against Hunspell.
    """
    print("\n" + "="*70)
    print("METHOD 2: Combinatorial Matrix Fuzzing (Affix Paradigm Stress Test)")
    print("="*70)

    # Representative roots for all phonetic classes:
    verbs = {
        "Back Unrounded Consonant": ["yapmak", "almak", "bakmak"],
        "Back Rounded Consonant": ["olmak", "bulmak", "vurmak"],
        "Front Unrounded Consonant": ["gelmek", "bilmek", "sevmek"],
        "Front Rounded Consonant": ["görmek", "gülmek", "dönmek"],
        "Back Vowel Ending": ["başlamak", "anlamak", "okumak"],
        "Front Vowel Ending": ["beklemek", "istemek", "yürümek"],
        "Voicing Stem (t->d)": ["etmek", "gitmek", "tatmak"],
    }

    # Paradigm chains to test
    # Each generator takes verb stem and root
    # Helper for vowel and consonant harmony
    def inflect_verb(lemma: str, sfx_type: str) -> list[str]:
        root = lemma[:-3] if lemma.endswith(("mak", "mek")) else lemma
        last_ch = root[-1].lower()
        ends_unvoiced = last_ch in "çfhkpsşt"
        ends_vow = last_ch in "aeıioöuü"
        
        # Determine dominant vowel
        dom_v = "a"
        for ch in reversed(root):
            if ch.lower() in "aı":
                dom_v = "a"
                break
            elif ch.lower() in "ou":
                dom_v = "u"
                break
            elif ch.lower() in "ei":
                dom_v = "e"
                break
            elif ch.lower() in "öü":
                dom_v = "ü"
                break

        d_c = "t" if ends_unvoiced else "d"
        v_h = "ı" if dom_v == "a" else ("u" if dom_v == "u" else ("i" if dom_v == "e" else "ü"))
        v_l = "a" if dom_v in "au" else "e"

        # Voicing roots mutate t -> d before vowel initial affixes
        voiced_root = (root[:-1] + "d") if (lemma in ["etmek", "gitmek", "tatmak", "gütmek"] and root.endswith("t")) else root

        # Aorist vowel
        if ends_vow:
            aor_v = "r"
        elif lemma in ["almak", "bilmek", "bulmak", "durmak", "gelmek", "görmek", "kalmak", "olmak", "ölmek", "sanmak", "varmak", "vermek", "vurmak"]:
            aor_v = f"{v_h}r"
        else:
            aor_v = f"{v_l}r"

        if sfx_type == "part_ki":
            return [
                f"{root}{d_c}{v_h}ğ{v_h}ndeki" if v_l == "e" else f"{root}{d_c}{v_h}ğ{v_h}ndaki",
                f"{root}{d_c}{v_h}ğ{v_h}ndekiler" if v_l == "e" else f"{root}{d_c}{v_h}ğ{v_h}ndakiler",
                f"{root}{d_c}{v_h}ğ{v_h}ndekini" if v_l == "e" else f"{root}{d_c}{v_h}ğ{v_h}ndakini",
            ]
        elif sfx_type == "part_eq":
            return [
                f"{root}{d_c}{v_h}ğ{v_h}nce" if v_l == "e" else f"{root}{d_c}{v_h}ğ{v_h}nca",
                f"{root}{d_c}{v_h}klerince" if v_l == "e" else f"{root}{d_c}{v_h}klarınca",
            ]
        elif sfx_type == "similative":
            aor_stem = f"{voiced_root}{aor_v}"
            return [f"{aor_stem}cesine" if v_l == "e" else f"{aor_stem}casına"]
        elif sfx_type == "converbs":
            y_buf = "y" if ends_vow else ""
            return [
                f"{root}{d_c}{v_h}kçe" if v_l == "e" else f"{root}{d_c}{v_h}kça",
                f"{root}{y_buf}eli" if v_l == "e" else f"{root}{y_buf}alı",
                f"{root}meksizin" if v_l == "e" else f"{root}maksızın",
            ]
        elif sfx_type == "prog":
            return [
                f"{root}mekteyken" if v_l == "e" else f"{root}maktayken",
                f"{root}mekteydi" if v_l == "e" else f"{root}maktaydı",
                f"{root}mekteymiş" if v_l == "e" else f"{root}maktaymış",
            ]
        elif sfx_type == "vn_ma":
            return [
                f"{root}mesinde" if v_l == "e" else f"{root}masında",
                f"{root}mesinden" if v_l == "e" else f"{root}masından",
                f"{root}mesini" if v_l == "e" else f"{root}masını",
                f"{root}mesine" if v_l == "e" else f"{root}masına",
            ]
        elif sfx_type == "vn_mak":
            return [
                f"{root}mekte" if v_l == "e" else f"{root}makta",
                f"{root}mekten" if v_l == "e" else f"{root}maktan",
                f"{root}mekle" if v_l == "e" else f"{root}makla",
            ]
        return []

    chains = {
        "Participle + Locative + Relative -ki": "part_ki",
        "Participle + Equative (-nca/-nce)": "part_eq",
        "Aorist + Similative (-casına/-cesine)": "similative",
        "Converbs (-dıkça, -alı, -maksızın)": "converbs",
        "Progressive Compound (-maktayken, -maktaydı)": "prog",
        "Verbal Noun -ma + Pronominal n Cases": "vn_ma",
        "Verbal Noun -mak + Hal Ekleri": "vn_mak"
    }

    matrix_results = {}
    print(f"\nTesting {len(chains)} grammatical paradigm chains across {sum(len(v) for v in verbs.values())} verbs...\n")

    for chain_name, sfx_key in chains.items():
        all_words = []
        for cat_name, verb_list in verbs.items():
            for v_lemma in verb_list:
                forms = inflect_verb(v_lemma, sfx_key)
                all_words.extend(forms)

        accepted, rejected = run_hunspell_check(all_words)
        total = len(all_words)
        pct = (len(accepted) / total) * 100 if total else 0
        status = "PASSED" if not rejected else ("PARTIAL" if accepted else "FAILED")
        
        print(f"[{status:7}] {chain_name:42}: {len(accepted):2}/{total:2} ({pct:5.1f}%) accepted")
        if rejected:
            sample_rej = sorted(list(rejected))[:6]
            print(f"          Missing sample: {sample_rej}")
        
        matrix_results[chain_name] = {
            "total": total,
            "accepted": len(accepted),
            "rejected": len(rejected),
            "samples_missing": sorted(list(rejected))[:10]
        }

    return matrix_results


# ============================================================================
# MAIN AUDIT RUNNER
# ============================================================================

def run_all_audits():
    print("="*70)
    print("TURKSPELL MORPHOLOGICAL DIAGNOSTIC AUDIT SUITE")
    print(f"Dictionary target: {DICT_PATH}")
    print("="*70)

    sym_results = audit_affix_symmetry()
    coll_results = audit_cross_pos_collisions()
    mat_results = audit_combinatorial_matrix()

    print("\n" + "="*70)
    print("AUDIT SUMMARY & KEY FINDINGS")
    print("="*70)
    
    # 1. Symmetry Summary
    sym_gaps = sum(len(v["gaps"]) for v in sym_results.values())
    print(f"1. Affix Symmetry: {sym_gaps} harmonic pattern variations across {len(sym_results)} families.")

    # 2. Collision Summary
    susp_voicing = len(coll_results["suspicious_voicing_verbs"])
    print(f"2. Cross-POS Collisions: {susp_voicing} suspicious voicing verbs detected in dictionary.")

    # 3. Combinatorial Matrix Summary
    gaps_found = [k for k, v in mat_results.items() if v["rejected"] > 0]
    print(f"3. Combinatorial Matrix: {len(gaps_found)} paradigm gaps detected:")
    for g in gaps_found:
        res = mat_results[g]
        print(f"   * {g}: {res['rejected']}/{res['total']} missing. Examples: {res['samples_missing'][:4]}")

    print("="*70)


if __name__ == "__main__":
    run_all_audits()
