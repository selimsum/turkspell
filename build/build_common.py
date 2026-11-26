# -*- coding: utf-8 -*-
"""Shared utilities, Turkish casing helpers, and wordlist/numeral builders for Turkspell."""

import json
import os
import shutil
from pathlib import Path

from utf8_flag_mapping import LONG_TO_UTF8

ROOT_DIR = Path(__file__).resolve().parent.parent

SUPERSCRIPT_DIGITS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUPERSCRIPT_FLAG_MAP = {
    "⁰": "NC",  # sıfır (back unrounded, voiced consonant)
    "¹": "N5",  # bir (front unrounded, voiced consonant)
    "²": "N6",  # iki / kare (front unrounded, vowel-final)
    "³": "N7",  # üç / küp (front rounded, unvoiced consonant)
    "⁴": "N7",  # dört (front rounded, unvoiced consonant)
    "⁵": "N8",  # beş (front unrounded, unvoiced consonant)
    "⁶": "N9",  # altı (back unrounded, vowel-final)
    "⁷": "N6",  # yedi (front unrounded, vowel-final)
    "⁸": "N5",  # sekiz (front unrounded, voiced consonant)
    "⁹": "NA",  # dokuz (back rounded, voiced consonant)
}


def tr_lower(s: str) -> str:
    """Turkish-aware lowercase (I->ı, İ->i)."""
    if not s:
        return ""
    return s.replace("I", "ı").replace("İ", "i").lower()


def tr_upper(s: str) -> str:
    """Turkish-aware uppercase (i->İ, ı->I)."""
    if not s:
        return ""
    return s.replace("i", "İ").replace("ı", "I").upper()


def tr_title(s: str) -> str:
    """Turkish-aware initial capitalization (i->İ, ı->I)."""
    if not s:
        return s
    if s[0] == "i":
        return "İ" + s[1:]
    if s[0] == "ı":
        return "I" + s[1:]
    return s[0].upper() + s[1:]


def find_hunspell() -> str | None:
    """Locate the hunspell binary on PATH, falling back to WinGet Packages on Windows."""
    found = shutil.which("hunspell")
    if found:
        return found
    if os.name == "nt":
        winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
        if os.path.isdir(winget_pkg_dir):
            for root, _dirs, files in os.walk(winget_pkg_dir):
                if "hunspell.exe" in files:
                    if root not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
                    return shutil.which("hunspell") or os.path.join(root, "hunspell.exe")
    return None


def get_numeral_flag_code(n: int) -> str:
    """Return the 2-char numeral affix flag code (N5..ND) for integer n based on its Turkish reading."""
    if n == 0:
        return "NC"
    u = n % 10
    if u != 0:
        return {
            1: "N5", 2: "N6", 3: "N7", 4: "N7", 5: "N8",
            6: "N9", 7: "N6", 8: "N5", 9: "NA",
        }[u]
    t = n % 100
    if t != 0:
        return {
            10: "NA", 20: "N6", 30: "NA", 40: "NB", 50: "N6",
            60: "NB", 70: "N8", 80: "N5", 90: "NC",
        }[t]
    if n % 1000 != 0:
        return "ND"  # yüz
    if n % 1000000 != 0:
        return "N5"  # bin
    if n % 1000000000 != 0:
        return "NA"  # milyon
    return "NC"      # milyar


def generate_numeral_virtual_stems() -> list[str]:
    """Generate NEEDAFFIX-guarded numeric and clock-time stems for apostrophe inflections."""
    stems = {}

    def _add(token: str, flag_code: str):
        u_char = LONG_TO_UTF8.get(flag_code, "")
        if u_char:
            stems[token] = f"{token}/X{u_char}"

    # 1. Integers 0..2100 and leading-zero 01..09
    for n in range(0, 2101):
        _add(str(n), get_numeral_flag_code(n))
    for n in range(1, 10):
        _add(f"0{n}", get_numeral_flag_code(n))

    # 2. Round numbers & dotted thousand-separator forms
    round_nums = [
        1000, 1500, 2000, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900,
        3000, 3500, 4000, 4500, 5000, 6000, 7000, 7500, 8000, 9000,
        10000, 15000, 20000, 25000, 30000, 40000, 50000, 60000, 70000, 75000, 80000, 90000,
        100000, 150000, 200000, 250000, 300000, 400000, 500000, 600000, 700000, 750000, 800000, 900000,
        1000000, 2000000, 5000000, 10000000, 100000000, 1000000000,
    ]
    for n in round_nums:
        fc = get_numeral_flag_code(n)
        _add(str(n), fc)
        dotted = f"{n:,}".replace(",", ".")
        _add(dotted, fc)

    # 3. 24-hour clock times HH.MM (24.00 is valid; 24.01..24.59 are invalid)
    for hh in range(0, 25):
        hh_strs = [f"{hh:02d}"] + ([str(hh)] if 1 <= hh <= 9 else [])
        mm_range = (0,) if hh == 24 else range(0, 60)
        for mm in mm_range:
            fc = get_numeral_flag_code(hh) if mm == 0 else get_numeral_flag_code(mm)
            mm_str = f"{mm:02d}"
            for hs in hh_strs:
                _add(f"{hs}.{mm_str}", fc)

    return list(stems.values())


def generate_superscript_stems() -> list[str]:
    """Generate bare-valid superscript unit and power stems for apostrophe-less inflections."""
    stems = {}

    def _add(token: str, flag_code: str):
        u_char = LONG_TO_UTF8.get(flag_code, "")
        if u_char:
            stems[token] = f"{token}/{u_char}"

    area_bases = ("m", "cm", "mm", "km", "dm", "hm", "dam", "nm", "µm")
    for base in area_bases:
        _add(f"{base}²", "N6")  # kare (front unrounded, vowel-final)
        _add(f"{base}³", "N7")  # küp (front rounded, unvoiced consonant)

    power_bases = [str(i) for i in range(0, 21)] + ["100", "1000", "x", "y", "z", "a", "b", "n", "m"]
    for base in power_bases:
        for sup, fc in SUPERSCRIPT_FLAG_MAP.items():
            _add(f"{base}{sup}", fc)

    return list(stems.values())


def load_build_wordlists(root_dir: Path | None = None) -> dict:
    """Load structured wordlists and overrides from lexicons/build_wordlists.json."""
    base = Path(root_dir) if root_dir is not None else ROOT_DIR
    path = base / "lexicons" / "build_wordlists.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_DEFAULT_BUILD_WORDLISTS = load_build_wordlists(ROOT_DIR)
COMPOUND_SET = set(_DEFAULT_BUILD_WORDLISTS["compound_proper_terms"])
VIRTUAL_STEMS = (
    list(_DEFAULT_BUILD_WORDLISTS["base_virtual_stems"])
    + generate_numeral_virtual_stems()
    + generate_superscript_stems()
)


def noun_chain(
    stem_flag: str,
    only_vowel: bool = False,
    only_consonant: bool = False,
    derivs: str | None = None,
) -> str:
    """Return the morphological flag chain for a given noun stem class flag."""
    if stem_flag in ("PX", "NX"):
        return stem_flag
    back_flags = {"B1", "B2", "V1", "V2", "D1", "D2", "C1", "C2", "G1", "G2"}
    back_vowel_flags = {"B3", "B4"}
    front_flags = {"F1", "F2", "V3", "V4", "D3", "D4", "C3", "C4", "G3", "G4"}
    front_vowel_flags = {"F3", "F4"}
    rounded_flags = {"B2", "V2", "D2", "C2", "G2", "B4", "F2", "V4", "D4", "C4", "G4", "F4"}

    is_back = stem_flag in back_flags | back_vowel_flags
    is_front = stem_flag in front_flags | front_vowel_flags
    is_rounded = stem_flag in rounded_flags
    is_vowel = stem_flag in back_vowel_flags | front_vowel_flags

    def adjust_flag(base: str) -> str:
        return base.lower() if is_vowel else base

    if is_back and not is_rounded:
        acc_f = adjust_flag("A1")
    elif is_back and is_rounded:
        acc_f = adjust_flag("A2")
    elif is_front and not is_rounded:
        acc_f = adjust_flag("A3")
    else:
        acc_f = adjust_flag("A4")

    dat_f = adjust_flag("Y1") if is_back else adjust_flag("Y2")
    loc_f = "L1" if is_back else "L2"
    abl_f = "R1" if is_back else "R2"

    if is_back and not is_rounded:
        gen_f = adjust_flag("N1")
    elif is_back and is_rounded:
        gen_f = adjust_flag("N2")
    elif is_front and not is_rounded:
        gen_f = adjust_flag("N3")
    else:
        gen_f = adjust_flag("N4")

    ins_f = adjust_flag("I1") if is_back else adjust_flag("I2")
    eq_f = "Q1" if is_back else "Q2"
    plural = "PB" if is_back else "PF"

    if is_back and not is_rounded:
        p3 = "PS"
    elif is_back and is_rounded:
        p3 = "PT"
    elif is_front and not is_rounded:
        p3 = "PU"
    else:
        p3 = "PV"

    if is_back and not is_rounded:
        p1 = "P1"
    elif is_back and is_rounded:
        p1 = "P2"
    elif is_front and not is_rounded:
        p1 = "P3"
    else:
        p1 = "P4"

    if is_back and not is_rounded:
        p2s = "P5"
    elif is_back and is_rounded:
        p2s = "P6"
    elif is_front and not is_rounded:
        p2s = "P7"
    else:
        p2s = "P8"

    if is_back and not is_rounded:
        p1pl = "PM"
    elif is_back and is_rounded:
        p1pl = "PO"
    elif is_front and not is_rounded:
        p1pl = "PP"
    else:
        p1pl = "PQ"

    if is_back and not is_rounded:
        p2pl = "PN"
    elif is_back and is_rounded:
        p2pl = "PR"
    elif is_front and not is_rounded:
        p2pl = "PW"
    else:
        p2pl = "PZ"

    default_derivs = "LILKSZCICKSLDLDTDE"
    effective_derivs = default_derivs if derivs is None else derivs

    exclude_vowel = stem_flag[0] in ("V", "D", "G")
    if only_vowel:
        cases = f"{acc_f}{dat_f}{gen_f}"
        possessives = f"{p3}{p1}{p2s}{p1pl}{p2pl}"
        copula_flag = "VC" if is_back else "vc"
        return f"{cases}{possessives}{copula_flag}NE"
    elif only_consonant or exclude_vowel:
        cases = f"{loc_f}{abl_f}{ins_f}{eq_f}"
        possessives = ""
        copula_flag = "CL" if is_back else "cl"
    else:
        cases = f"{acc_f}{dat_f}{loc_f}{abl_f}{gen_f}{ins_f}{eq_f}"
        possessives = f"{p3}{p1}{p2s}{p1pl}{p2pl}"
        copula_flag = "CL" if is_back else "cl"

    return f"{stem_flag}{cases}{plural}{possessives}{copula_flag}{effective_derivs}"
