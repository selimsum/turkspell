# -*- coding: utf-8 -*-
"""
tools/generate_golden_verbs.py — Golden Verb Test Suite Builder
=============================================================
Generates a comprehensive test suite of ~10,000 real-world conjugated Turkish
verb forms across all major verb paradigm classes, tenses, persons, copulas,
and participles.

Evaluates every form against current Turkspell (tr.aff / tr.dic) to record a
concrete baseline.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Ensure hunspell is in PATH
winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break

HUNSPELL_BIN = shutil.which("hunspell")
if not HUNSPELL_BIN:
    raise RuntimeError("hunspell binary not found in PATH!")

def check_words_batch(words: list[str], dict_path: str = str(ROOT_DIR / "tr")) -> tuple[set[str], set[str]]:
    """Runs hunspell -l on words. Returns (accepted_set, rejected_set)."""
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    flagged = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    all_words = set(words)
    accepted = all_words - flagged
    rejected = flagged
    return accepted, rejected


# ---------------------------------------------------------------------------
# Morphological Paradigm Generator for Test Verbs
# ---------------------------------------------------------------------------

REPRESENTATIVE_VERBS = [
    # 1. Back unrounded consonant, aorist -ar (VB / wa)
    {"infinitive": "yapmak", "stem": "yap", "class": "VB_ar", "back": True, "round": False, "vowel_end": False, "aorist": "ar"},
    {"infinitive": "bakmak", "stem": "bak", "class": "VB_ar", "back": True, "round": False, "vowel_end": False, "aorist": "ar"},
    {"infinitive": "çıkmak", "stem": "çık", "class": "VB_ar", "back": True, "round": False, "vowel_end": False, "aorist": "ar"},
    {"infinitive": "yatmak", "stem": "yat", "class": "VB_ar", "back": True, "round": False, "vowel_end": False, "aorist": "ar"},
    
    # 2. Back unrounded consonant, irregular aorist -ır (VB / wi)
    {"infinitive": "almak", "stem": "al", "class": "VB_ir", "back": True, "round": False, "vowel_end": False, "aorist": "ır"},
    {"infinitive": "kalmak", "stem": "kal", "class": "VB_ir", "back": True, "round": False, "vowel_end": False, "aorist": "ır"},
    {"infinitive": "varmak", "stem": "var", "class": "VB_ir", "back": True, "round": False, "vowel_end": False, "aorist": "ır"},
    {"infinitive": "sanmak", "stem": "san", "class": "VB_ir", "back": True, "round": False, "vowel_end": False, "aorist": "ır"},
    
    # 3. Back rounded consonant, aorist -ar (VR / wr)
    {"infinitive": "koşmak", "stem": "koş", "class": "VR_ar", "back": True, "round": True, "vowel_end": False, "aorist": "ar"},
    {"infinitive": "korkmak", "stem": "kork", "class": "VR_ar", "back": True, "round": True, "vowel_end": False, "aorist": "ar"},
    {"infinitive": "bozmak", "stem": "boz", "class": "VR_ar", "back": True, "round": True, "vowel_end": False, "aorist": "ar"},
    
    # 4. Back rounded consonant, irregular aorist -ur (VR / wu)
    {"infinitive": "olmak", "stem": "ol", "class": "VR_ur", "back": True, "round": True, "vowel_end": False, "aorist": "ur"},
    {"infinitive": "bulmak", "stem": "bul", "class": "VR_ur", "back": True, "round": True, "vowel_end": False, "aorist": "ur"},
    {"infinitive": "durmak", "stem": "dur", "class": "VR_ur", "back": True, "round": True, "vowel_end": False, "aorist": "ur"},
    {"infinitive": "vurmak", "stem": "vur", "class": "VR_ur", "back": True, "round": True, "vowel_end": False, "aorist": "ur"},
    
    # 5. Front unrounded consonant, aorist -er (VF / we)
    {"infinitive": "geçmek", "stem": "geç", "class": "VF_er", "back": False, "round": False, "vowel_end": False, "aorist": "er"},
    {"infinitive": "sevmek", "stem": "sev", "class": "VF_er", "back": False, "round": False, "vowel_end": False, "aorist": "er"},
    {"infinitive": "seçmek", "stem": "seç", "class": "VF_er", "back": False, "round": False, "vowel_end": False, "aorist": "er"},
    {"infinitive": "kesmek", "stem": "kes", "class": "VF_er", "back": False, "round": False, "vowel_end": False, "aorist": "er"},
    
    # 6. Front unrounded consonant, irregular aorist -ir (VF / wj)
    {"infinitive": "gelmek", "stem": "gel", "class": "VF_ir", "back": False, "round": False, "vowel_end": False, "aorist": "ir"},
    {"infinitive": "vermek", "stem": "ver", "class": "VF_ir", "back": False, "round": False, "vowel_end": False, "aorist": "ir"},
    {"infinitive": "bilmek", "stem": "bil", "class": "VF_ir", "back": False, "round": False, "vowel_end": False, "aorist": "ir"},
    
    # 7. Voicing consonant stems (VK / VM)
    {"infinitive": "tatmak", "stem": "tat", "voiced_stem": "tad", "class": "VK", "back": True, "round": False, "vowel_end": False, "aorist": "ar"},
    {"infinitive": "gitmek", "stem": "git", "voiced_stem": "gid", "class": "VM", "back": False, "round": False, "vowel_end": False, "aorist": "er"},
    {"infinitive": "etmek", "stem": "et", "voiced_stem": "ed", "class": "VM", "back": False, "round": False, "vowel_end": False, "aorist": "er"},
    
    # 8. Front rounded consonant, aorist -er (VG / wg)
    {"infinitive": "dönmek", "stem": "dön", "class": "VG_er", "back": False, "round": True, "vowel_end": False, "aorist": "er"},
    {"infinitive": "çözmek", "stem": "çöz", "class": "VG_er", "back": False, "round": True, "vowel_end": False, "aorist": "er"},
    {"infinitive": "dökmek", "stem": "dök", "class": "VG_er", "back": False, "round": True, "vowel_end": False, "aorist": "er"},
    
    # 9. Front rounded consonant, irregular aorist -ür (VG / wh)
    {"infinitive": "görmek", "stem": "gör", "class": "VG_ur", "back": False, "round": True, "vowel_end": False, "aorist": "ür"},
    {"infinitive": "ölmek", "stem": "öl", "class": "VG_ur", "back": False, "round": True, "vowel_end": False, "aorist": "ür"},
    
    # 10. Back unrounded vowel stem (VA)
    {"infinitive": "anlamak", "stem": "anla", "class": "VA", "back": True, "round": False, "vowel_end": True, "aorist": "r"},
    {"infinitive": "başlamak", "stem": "başla", "class": "VA", "back": True, "round": False, "vowel_end": True, "aorist": "r"},
    {"infinitive": "yaşamak", "stem": "yaşa", "class": "VA", "back": True, "round": False, "vowel_end": True, "aorist": "r"},
    
    # 11. Back rounded vowel stem (VS)
    {"infinitive": "okumak", "stem": "oku", "class": "VS", "back": True, "round": True, "vowel_end": True, "aorist": "r"},
    {"infinitive": "korumak", "stem": "koru", "class": "VS", "back": True, "round": True, "vowel_end": True, "aorist": "r"},
    
    # 12. Front unrounded vowel stem (VE)
    {"infinitive": "beklemek", "stem": "bekle", "class": "VE", "back": False, "round": False, "vowel_end": True, "aorist": "r"},
    {"infinitive": "dinlemek", "stem": "dinle", "class": "VE", "back": False, "round": False, "vowel_end": True, "aorist": "r"},
    {"infinitive": "istemek", "stem": "iste", "class": "VE", "back": False, "round": False, "vowel_end": True, "aorist": "r"},
    {"infinitive": "söylemek", "stem": "söyle", "class": "VH", "back": False, "round": True, "vowel_end": True, "aorist": "r"},
    
    # 13. Front rounded vowel stem (VH)
    {"infinitive": "yürümek", "stem": "yürü", "class": "VH", "back": False, "round": True, "vowel_end": True, "aorist": "r"},
    {"infinitive": "büyümek", "stem": "büyü", "class": "VH", "back": False, "round": True, "vowel_end": True, "aorist": "r"},
    
    # 14. Narrowing verbs (VY)
    {"infinitive": "demek", "stem": "de", "class": "VY", "back": False, "round": False, "vowel_end": True, "aorist": "r", "narrow": True},
    {"infinitive": "yemek", "stem": "ye", "class": "VY", "back": False, "round": False, "vowel_end": True, "aorist": "r", "narrow": True},
    
    # 15. Polysyllabic regular verbs
    {"infinitive": "çalışmak", "stem": "çalış", "class": "VB_poly", "back": True, "round": False, "vowel_end": False, "aorist": "ır"},
    {"infinitive": "konuşmak", "stem": "konuş", "class": "VR_poly", "back": True, "round": True, "vowel_end": False, "aorist": "ur"},
    {"infinitive": "değiştirmek", "stem": "değiştir", "class": "VF_poly", "back": False, "round": False, "vowel_end": False, "aorist": "ir"},
    {"infinitive": "düşünmek", "stem": "düşün", "class": "VG_poly", "back": False, "round": True, "vowel_end": False, "aorist": "ür"},
    
    # 16. Derived passive / causative / abilitative stems
    {"infinitive": "yapılmak", "stem": "yapıl", "class": "VB_pass", "back": True, "round": False, "vowel_end": False, "aorist": "ır"},
    {"infinitive": "yaptırmak", "stem": "yaptır", "class": "VB_caus", "back": True, "round": False, "vowel_end": False, "aorist": "ır"},
    {"infinitive": "yapabilmek", "stem": "yapabil", "class": "VF_abil", "back": False, "round": False, "vowel_end": False, "aorist": "ir"},
    {"infinitive": "sevilmek", "stem": "sevil", "class": "VF_pass", "back": False, "round": False, "vowel_end": False, "aorist": "ir"},
    {"infinitive": "geliştirmek", "stem": "geliştir", "class": "VF_caus", "back": False, "round": False, "vowel_end": False, "aorist": "ir"},
]

def generate_verb_forms(vinfo: dict) -> list[str]:
    """Generates the full standard Turkish verbal paradigm for a verb."""
    forms = set()
    stem = vinfo["stem"]
    voiced = vinfo.get("voiced_stem", stem)
    back = vinfo["back"]
    round_v = vinfo["round"]
    vowel_end = vinfo["vowel_end"]
    is_narrow = vinfo.get("narrow", False)
    
    # Vowels
    v_low = "a" if back else "e"
    v_pres_high = "u" if (back and round_v) else ("ı" if back else ("ü" if round_v else "i"))
    if vowel_end and stem.endswith(('a', 'e')):
        v_high = "ı" if back else "i"
    else:
        v_high = v_pres_high
    
    # 1. Infinitive
    forms.add(vinfo["infinitive"])
    
    # Stem choices: voiced stem before vowels if applicable
    def st_v(is_vowel_initial: bool = False):
        if is_vowel_initial and voiced != stem:
            return voiced
        return stem
    
    # 2. Present continuous: -iyor
    # If vowel-ending, drop final vowel before -Iyor (anla -> anlıyor, bekle -> bekliyor)
    if is_narrow:
        pres_stem = ("di" if stem == "de" else "yi") + "yor"
    elif vowel_end:
        drop_stem = stem[:-1]
        pres_stem = f"{drop_stem}{v_pres_high}yor"
    else:
        pres_stem = f"{st_v(True)}{v_high}yor"
        
    for p_suf in ["", "um", "sun", "uz", "sunuz", "lar"]:
        forms.add(f"{pres_stem}{p_suf}")
        # Copula
        for cop in ["du", "dum", "dun", "duk", "dunuz", "dular"]:
            forms.add(f"{pres_stem}{cop}")
        for cop in ["muş", "muşum", "muşsun", "muşuz", "muşsunuz", "muşlar"]:
            forms.add(f"{pres_stem}{cop}")
        for cop in ["sa", "sam", "san", "sak", "sanız", "salar"]:
            forms.add(f"{pres_stem}{cop}")
        forms.add(f"{pres_stem}dur")
        forms.add(f"{pres_stem}larmış")
        forms.add(f"{pres_stem}lardı")
        forms.add(f"{pres_stem}larsa")

    # 3. Aorist: -ar / -er or -ır / -ir / -ur / -ür or -r
    aor_suf = vinfo["aorist"]
    if is_narrow:
        aor_base = f"{stem}r"
    elif vowel_end:
        aor_base = f"{stem}r"
    else:
        aor_base = f"{st_v(True)}{aor_suf}"
        
    p_aor_high = aor_suf[-1] if aor_suf in ("ır", "ir", "ur", "ür") else ("ı" if back else "i")
    for p_suf in ["", f"{p_aor_high}m", f"s{p_aor_high}n", f"{p_aor_high}z", f"s{p_aor_high}n{p_aor_high}z", "lar" if back else "ler"]:
        forms.add(f"{aor_base}{p_suf}")
    for cop in ["dı" if back else "di", "dım" if back else "dim", "dın" if back else "din", "dık" if back else "dik", "dınız" if back else "diniz", "dılar" if back else "diler"]:
        forms.add(f"{aor_base}{cop}")
    for cop in ["mış" if back else "miş", "mışım" if back else "mişim", "mışsın" if back else "mişsin", "mışız" if back else "mişiz", "mışlar" if back else "mişler"]:
        forms.add(f"{aor_base}{cop}")
    for cop in ["sa" if back else "se", "sam" if back else "sem", "san" if back else "sen", "sak" if back else "sek", "sanız" if back else "seniz", "salar" if back else "seler"]:
        forms.add(f"{aor_base}{cop}")
    forms.add(f"{aor_base}dır" if back else f"{aor_base}dir")
    forms.add(f"{aor_base}larmış" if back else f"{aor_base}lermiş")
    forms.add(f"{aor_base}lardı" if back else f"{aor_base}lerdi")
    forms.add(f"{aor_base}larsa" if back else f"{aor_base}lerse")

    # 4. Definite past: -dı / -di / -tı / -ti
    last_c = stem[-1]
    is_unvoiced = last_c in "çfhkpsşt"
    d_char = "t" if is_unvoiced else "d"
    past_base = f"{stem}{d_char}{v_high}"
    for p_suf in ["", "m", "n", "k", "nız" if back else "niz", "lar" if back else "ler"]:
        forms.add(f"{past_base}{p_suf}")
    for cop in ["ysa" if back else "yse", "ysam" if back else "ysem", "ysan" if back else "ysen", "ysak" if back else "ysek", "ysanız" if back else "yseniz"]:
        forms.add(f"{past_base}{cop}")
    for cop in ["ydı" if back else "ydi", "ydım" if back else "ydim", "ydın" if back else "ydin", "ydık" if back else "ydik"]:
        forms.add(f"{past_base}{cop}")

    # 5. Evidential past: -mış / -miş / -muş / -müş
    evid_base = f"{stem}m{v_high}ş"
    for p_suf in ["", f"{v_high}m", f"s{v_high}n", f"{v_high}z", f"s{v_high}n{v_high}z", f"l{v_low}r"]:
        forms.add(f"{evid_base}{p_suf}")
    for cop in ["tı" if is_unvoiced or back else "ti", "tım" if back else "tim", "tın" if back else "tin", "tık" if back else "tik", "tılar" if back else "tiler"]:
        forms.add(f"{evid_base}{cop}")
    for cop in ["sa" if back else "se", "sam" if back else "sem", "sak" if back else "sek", "salar" if back else "seler"]:
        forms.add(f"{evid_base}{cop}")
    forms.add(f"{evid_base}tır" if back else f"{evid_base}tir")
    forms.add(f"{evid_base}larmış" if back else f"{evid_base}lermiş")
    forms.add(f"{evid_base}lardı" if back else f"{evid_base}lerdi")

    # 6. Future: -acak / -ecek
    if is_narrow:
        fut_base = ("di" if stem == "de" else "yi") + "yecek"
    elif vowel_end:
        fut_base = f"{stem}y{v_low}c{v_low}k"
    else:
        fut_base = f"{st_v(True)}{v_low}c{v_low}k"
        
    fut_voiced = fut_base[:-1] + "ğ"
    forms.add(f"{fut_base}")
    forms.add(f"{fut_voiced}{v_high}m")
    forms.add(f"{fut_base}s{v_high}n")
    forms.add(f"{fut_voiced}{v_high}z")
    forms.add(f"{fut_base}s{v_high}n{v_high}z")
    forms.add(f"{fut_base}l{v_low}r")
    for cop in ["tı" if back else "ti", "tım" if back else "tim", "tık" if back else "tik", "tılar" if back else "tiler"]:
        forms.add(f"{fut_base}{cop}")
    for cop in ["mış" if back else "miş", "mışım" if back else "mişim", "mışlar" if back else "mişler"]:
        forms.add(f"{fut_base}{cop}")
    for cop in ["sa" if back else "se", "sam" if back else "sem", "sak" if back else "sek", "salar" if back else "seler"]:
        forms.add(f"{fut_base}{cop}")
    forms.add(f"{fut_base}tır" if back else f"{fut_base}tir")

    # 7. Necessitative: -malı / -meli
    nec_base = f"{stem}m{v_low}l{v_high}"
    for p_suf in ["", f"y{v_high}m", f"s{v_high}n", f"y{v_high}z", f"s{v_high}n{v_high}z", f"l{v_low}r"]:
        forms.add(f"{nec_base}{p_suf}")
    for cop in ["ydı" if back else "ydi", "ydım" if back else "ydim", "ydık" if back else "ydik"]:
        forms.add(f"{nec_base}{cop}")
    for cop in ["ymış" if back else "ymiş", "ymışlar" if back else "ymişler"]:
        forms.add(f"{nec_base}{cop}")
    for cop in ["ysa" if back else "yse", "ysak" if back else "ysek"]:
        forms.add(f"{nec_base}{cop}")
    forms.add(f"{nec_base}dır" if back else f"{nec_base}dir")

    # 8. Conditional: -sa / -se
    cond_base = f"{stem}s{v_low}"
    for p_suf in ["", "m", "n", "k", "nız" if back else "niz", "lar" if back else "ler"]:
        forms.add(f"{cond_base}{p_suf}")
    for cop in ["ydı" if back else "ydi", "ydım" if back else "ydim", "ydık" if back else "ydik"]:
        forms.add(f"{cond_base}{cop}")

    # 9. Imperative & Optative
    forms.add(f"{stem}")
    forms.add(f"{stem}s{v_high}n")
    if vowel_end:
        forms.add(f"{stem}y{v_high}n")
        forms.add(f"{stem}y{v_high}n{v_high}z")
        forms.add(f"{stem}y{v_low}y{v_high}m")
        forms.add(f"{stem}y{v_low}l{v_high}m")
    else:
        forms.add(f"{st_v(True)}{v_high}n")
        forms.add(f"{st_v(True)}{v_high}n{v_high}z")
        forms.add(f"{st_v(True)}{v_low}y{v_high}m")
        forms.add(f"{st_v(True)}{v_low}l{v_high}m")
    forms.add(f"{stem}s{v_high}nl{v_low}r")

    # 10. Progressive -makta / -mekte
    prog_base = f"{stem}m{v_low}kt{v_low}"
    for p_suf in ["", f"y{v_high}m", f"s{v_high}n", f"y{v_high}z", f"s{v_high}n{v_high}z", f"l{v_low}r"]:
        forms.add(f"{prog_base}{p_suf}")
    for cop in ["ydı" if back else "ydi", "ymış" if back else "ymiş", "ysa" if back else "yse", "dır" if back else "dir"]:
        forms.add(f"{prog_base}{cop}")

    # 11. Participles & Verbal Nouns: -dık, -acak, -ma + Pronominal Cases
    loc_n = "nda" if back else "nde"
    abl_n = "ndan" if back else "nden"
    acc_n = "nı" if back else "ni"
    dat_n = "na" if back else "ne"
    gen_n = "nın" if back else "nin"
    ins_n = "yla" if back else "yle"
    cop_d = "dır" if back else "dir"
    cop_y = "ydı" if back else "ydi"
    cop_s = "ysa" if back else "yse"
    cases_pronom = ["", loc_n, abl_n, acc_n, dat_n, gen_n, ins_n, cop_d, cop_y, cop_s]

    # a. -dık / -dik / -tık / -tik
    part_d = "t" if is_unvoiced else "d"
    part_3sg = f"{stem}{part_d}{v_high}ğ{v_high}"
    for c in cases_pronom:
        forms.add(f"{part_3sg}{c}")
        
    part_1sg = f"{stem}{part_d}{v_high}ğ{v_high}m"
    for c in ["", "da" if back else "de", "dan" if back else "den", "ı" if back else "i", "a" if back else "e", "ın" if back else "in", "la" if back else "le", cop_d]:
        forms.add(f"{part_1sg}{c}")
        
    part_1pl = f"{stem}{part_d}{v_high}ğ{v_high}m{v_high}z"
    for c in ["", "da" if back else "de", "dan" if back else "den", "ı" if back else "i", "a" if back else "e", "ın" if back else "in", "la" if back else "le", cop_d]:
        forms.add(f"{part_1pl}{c}")
        
    part_pl = f"{stem}{part_d}{v_high}kl{v_low}r{v_high}"
    for c in cases_pronom:
        forms.add(f"{part_pl}{c}")

    # b. Verbal noun: -ma / -me
    vn_3sg = f"{stem}m{v_low}s{v_high}"
    for c in cases_pronom:
        forms.add(f"{vn_3sg}{c}")
        
    vn_1pl = f"{stem}m{v_low}m{v_high}z"
    for c in ["", "da" if back else "de", "dan" if back else "den", "a" if back else "e", "ı" if back else "i", "ın" if back else "in", "la" if back else "le"]:
        forms.add(f"{vn_1pl}{c}")
        
    vn_pl = f"{stem}m{v_low}l{v_low}r{v_high}"
    for c in ["", loc_n, abl_n, acc_n, dat_n, gen_n, ins_n]:
        forms.add(f"{vn_pl}{c}")

    # c. Gerunds
    if vowel_end:
        forms.add(f"{stem}y{v_low}r{v_low}k")
        forms.add(f"{stem}y{v_high}p")
        forms.add(f"{stem}y{v_high}nc{v_low}")
    else:
        forms.add(f"{st_v(True)}{v_low}r{v_low}k")
        forms.add(f"{st_v(True)}{v_high}p")
        forms.add(f"{st_v(True)}{v_high}nc{v_low}")
    forms.add(f"{stem}rk{v_low}n")
    forms.add(f"{stem}{part_d}{v_high}kç{v_low}")
    forms.add(f"{stem}m{v_low}d{v_low}n")

    # 12. Negative Finite Forms
    neg_stem = f"{stem}m{v_low}"
    neg_unrounded_v = "ı" if back else "i"
    # Pres cont: yapmıyor
    forms.add(f"{stem}m{neg_unrounded_v}yor")
    forms.add(f"{stem}m{neg_unrounded_v}yordu")
    forms.add(f"{stem}m{neg_unrounded_v}yormuş")
    forms.add(f"{stem}m{neg_unrounded_v}yorsa")
    forms.add(f"{stem}m{neg_unrounded_v}yordur")
    forms.add(f"{stem}m{neg_unrounded_v}yorum")
    forms.add(f"{stem}m{neg_unrounded_v}yorsun")
    forms.add(f"{stem}m{neg_unrounded_v}yoruz")
    forms.add(f"{stem}m{neg_unrounded_v}yorsunuz")
    forms.add(f"{stem}m{neg_unrounded_v}yorlar")
    # Past: yapmadı
    forms.add(f"{neg_stem}d{neg_unrounded_v}")
    forms.add(f"{neg_stem}d{neg_unrounded_v}m")
    forms.add(f"{neg_stem}d{neg_unrounded_v}n")
    forms.add(f"{neg_stem}d{neg_unrounded_v}k")
    forms.add(f"{neg_stem}d{neg_unrounded_v}n{neg_unrounded_v}z")
    forms.add(f"{neg_stem}d{neg_unrounded_v}l{v_low}r")
    # Evidential: yapmamış
    forms.add(f"{neg_stem}m{neg_unrounded_v}ş")
    forms.add(f"{neg_stem}m{neg_unrounded_v}şt{neg_unrounded_v}")
    forms.add(f"{neg_stem}m{neg_unrounded_v}şm{neg_unrounded_v}ş")
    forms.add(f"{neg_stem}m{neg_unrounded_v}şs{v_low}")
    forms.add(f"{neg_stem}m{neg_unrounded_v}şt{neg_unrounded_v}r")
    forms.add(f"{neg_stem}m{neg_unrounded_v}ş{neg_unrounded_v}m")
    forms.add(f"{neg_stem}m{neg_unrounded_v}şs{neg_unrounded_v}n")
    forms.add(f"{neg_stem}m{neg_unrounded_v}ş{neg_unrounded_v}z")
    forms.add(f"{neg_stem}m{neg_unrounded_v}şs{neg_unrounded_v}n{neg_unrounded_v}z")
    forms.add(f"{neg_stem}m{neg_unrounded_v}şl{v_low}r")
    # Future: yapmayacak
    forms.add(f"{neg_stem}y{v_low}c{v_low}k")
    forms.add(f"{neg_stem}y{v_low}c{v_low}kt{neg_unrounded_v}")
    forms.add(f"{neg_stem}y{v_low}c{v_low}km{neg_unrounded_v}ş")
    forms.add(f"{neg_stem}y{v_low}c{v_low}ks{v_low}")
    forms.add(f"{neg_stem}y{v_low}c{v_low}kt{neg_unrounded_v}r")
    forms.add(f"{neg_stem}y{v_low}c{v_low}ğ{neg_unrounded_v}m")
    forms.add(f"{neg_stem}y{v_low}c{v_low}ks{neg_unrounded_v}n")
    forms.add(f"{neg_stem}y{v_low}c{v_low}ğ{neg_unrounded_v}z")
    forms.add(f"{neg_stem}y{v_low}c{v_low}ks{neg_unrounded_v}n{neg_unrounded_v}z")
    forms.add(f"{neg_stem}y{v_low}c{v_low}kl{v_low}r")
    # Aorist: yapmaz
    forms.add(f"{neg_stem}z")
    forms.add(f"{neg_stem}zd{neg_unrounded_v}")
    forms.add(f"{neg_stem}zm{neg_unrounded_v}ş")
    forms.add(f"{neg_stem}zs{v_low}")
    forms.add(f"{neg_stem}m")
    forms.add(f"{neg_stem}zs{neg_unrounded_v}n")
    forms.add(f"{neg_stem}y{neg_unrounded_v}z")
    forms.add(f"{neg_stem}zs{neg_unrounded_v}n{neg_unrounded_v}z")
    forms.add(f"{neg_stem}zl{v_low}r")
    # Necessitative: yapmamalı
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}yd{neg_unrounded_v}")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}ym{neg_unrounded_v}ş")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}ys{v_low}")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}d{neg_unrounded_v}r")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}y{neg_unrounded_v}m")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}s{neg_unrounded_v}n")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}y{neg_unrounded_v}z")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}s{neg_unrounded_v}n{neg_unrounded_v}z")
    forms.add(f"{neg_stem}m{v_low}l{neg_unrounded_v}l{v_low}r")
    # Conditional: yapmasa
    forms.add(f"{neg_stem}s{v_low}")
    forms.add(f"{neg_stem}s{v_low}yd{neg_unrounded_v}")
    forms.add(f"{neg_stem}s{v_low}ym{neg_unrounded_v}ş")
    forms.add(f"{neg_stem}s{v_low}m")
    forms.add(f"{neg_stem}s{v_low}n")
    forms.add(f"{neg_stem}s{v_low}k")
    forms.add(f"{neg_stem}s{v_low}n{neg_unrounded_v}z")
    forms.add(f"{neg_stem}s{v_low}l{v_low}r")
    # Negative Participles
    forms.add(f"{neg_stem}d{neg_unrounded_v}ğ{neg_unrounded_v}")
    forms.add(f"{neg_stem}d{neg_unrounded_v}ğ{neg_unrounded_v}nd{v_low}")
    forms.add(f"{neg_stem}d{neg_unrounded_v}ğ{neg_unrounded_v}nd{v_low}n")
    forms.add(f"{neg_stem}d{neg_unrounded_v}ğ{neg_unrounded_v}n{neg_unrounded_v}")
    forms.add(f"{neg_stem}d{neg_unrounded_v}ğ{neg_unrounded_v}n{v_low}")
    forms.add(f"{neg_stem}d{neg_unrounded_v}ğ{neg_unrounded_v}n{neg_unrounded_v}n")
    forms.add(f"{neg_stem}d{neg_unrounded_v}kl{v_low}r{neg_unrounded_v}")
    forms.add(f"{neg_stem}d{neg_unrounded_v}kl{v_low}r{neg_unrounded_v}nd{v_low}")
    forms.add(f"{neg_stem}d{neg_unrounded_v}kl{v_low}r{neg_unrounded_v}nd{v_low}n")
    forms.add(f"{neg_stem}d{neg_unrounded_v}kl{v_low}r{neg_unrounded_v}n{neg_unrounded_v}")
    forms.add(f"{neg_stem}d{neg_unrounded_v}kl{v_low}r{neg_unrounded_v}n{v_low}")
    # Negative Verbal Nouns
    forms.add(f"{neg_stem}m{v_low}s{neg_unrounded_v}")
    forms.add(f"{neg_stem}m{v_low}s{neg_unrounded_v}nd{v_low}")
    forms.add(f"{neg_stem}m{v_low}s{neg_unrounded_v}nd{v_low}n")
    forms.add(f"{neg_stem}m{v_low}s{neg_unrounded_v}n{neg_unrounded_v}")
    forms.add(f"{neg_stem}m{v_low}s{neg_unrounded_v}n{v_low}")
    forms.add(f"{neg_stem}m{v_low}l{v_low}r{neg_unrounded_v}")
    forms.add(f"{neg_stem}m{v_low}l{v_low}r{neg_unrounded_v}nd{v_low}")
    forms.add(f"{neg_stem}m{v_low}l{v_low}r{neg_unrounded_v}nd{v_low}n")
    # Negative Progressive
    forms.add(f"{neg_stem}m{v_low}kt{v_low}")
    forms.add(f"{neg_stem}m{v_low}kt{v_low}d{neg_unrounded_v}r")
    forms.add(f"{neg_stem}m{v_low}kt{v_low}yd{neg_unrounded_v}")
    forms.add(f"{neg_stem}m{v_low}kt{v_low}ym{neg_unrounded_v}ş")
    
    return sorted(forms)


OVERGENERATION_CANARIES = [
    # 1. Broken demek/yemek rules
    "debilecek", "debilecekler", "debileceklerine", "debileceklerini",
    "debilecekti", "debilecekmiş", "debilecektir",
    "yebilecek", "yebilecekler", "yebileceklerine", "yebileceklerini",
    "yebilecekti", "yebilecekmiş", "yebilecektir",
    # 2. Vowel harmony overgenerations (illegal rounded negatives / illegal rounded söylemek)
    "bozmaduğunu", "bozmaduğu", "bulmaduğunu", "büyümedüğünü",
    "söyledü", "söylemüş", "söyledüğü",
    # 3. Double buffer consonants
    "yapıssı", "gelmeyni", "bakayna", "çıkıssın", "koşuyya",
    # 4. Double plural markings
    "yaparlarar", "gelirlerler", "bakarlararlar", "koşarlarlar",
    # 5. Double copula impossible chains
    "yaptıymış", "yaptıydıymış", "gelmiştidi", "gittiymişti",
    # 6. Non-pronominal cases on 3rd-person participles (missing pronominal 'n')
    "yaptığıda", "yaptığıdan", "yaptığıa", "yaptığıı",
    "gittiğide", "gittiğiden", "gittiğie", "gittiğii",
    "okuduğuda", "okuduğudan",
    "gördüğüde", "gördüğüden",
    # 7. Impossible suffix orders
    "yapdıklar", "yapmıştıydılar", "yaparlardılar"
]

def main():
    print("=" * 70)
    print("TURKSPELL GOLDEN VERB TEST SUITE GENERATOR")
    print("=" * 70)
    print(f"Total representative verb lemmas: {len(REPRESENTATIVE_VERBS)}")
    
    all_positive_forms = {}
    total_generated = 0
    
    for vinfo in REPRESENTATIVE_VERBS:
        v_forms = generate_verb_forms(vinfo)
        all_positive_forms[vinfo["infinitive"]] = v_forms
        total_generated += len(v_forms)
        
    print(f"Total positive verb inflections generated: {total_generated:,}")
    print(f"Total overgeneration canary forms: {len(OVERGENERATION_CANARIES)}")
    
    # Flatten positive forms
    flat_positive = []
    for forms in all_positive_forms.values():
        flat_positive.extend(forms)
    flat_positive = sorted(set(flat_positive))
    
    print(f"Unique positive verb forms: {len(flat_positive):,}")
    
    # Evaluate against current Turkspell
    print("\nEvaluating against current Turkspell tr.aff / tr.dic...")
    accepted_pos, rejected_pos = check_words_batch(flat_positive)
    leaked_canaries, rejected_canaries = check_words_batch(OVERGENERATION_CANARIES)
    
    print("\n--- BASELINE EVALUATION RESULTS ---")
    print(f"Positive Forms Tested:     {len(flat_positive):,}")
    print(f"  Accepted by current dic: {len(accepted_pos):,} ({len(accepted_pos)/len(flat_positive)*100:.2f}%)")
    print(f"  Flagged (currently missing): {len(rejected_pos):,} ({len(rejected_pos)/len(flat_positive)*100:.2f}%)")
    
    print(f"\nCanary Forms Tested (Must be Rejected): {len(OVERGENERATION_CANARIES)}")
    print(f"  Successfully Rejected:   {len(rejected_canaries)} ({len(rejected_canaries)/len(OVERGENERATION_CANARIES)*100:.2f}%)")
    print(f"  Leaked (Overgeneration): {len(leaked_canaries)}")
    if leaked_canaries:
        print(f"  Leaked samples: {leaked_canaries}")

    # Save baseline to tests/golden_verbs_baseline.json
    output_path = ROOT_DIR / "tests" / "golden_verbs_baseline.json"
    baseline_data = {
        "metadata": {
            "num_lemmas": len(REPRESENTATIVE_VERBS),
            "num_positive_forms": len(flat_positive),
            "num_accepted": len(accepted_pos),
            "num_rejected": len(rejected_pos),
            "num_canaries": len(OVERGENERATION_CANARIES),
            "num_canaries_rejected": len(rejected_canaries)
        },
        "accepted_positive_baseline": sorted(accepted_pos),
        "rejected_positive_baseline": sorted(rejected_pos),
        "canary_forms": OVERGENERATION_CANARIES
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(baseline_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nSaved baseline dataset to: {output_path}")

if __name__ == "__main__":
    main()
