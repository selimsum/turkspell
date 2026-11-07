import os
import sys
import re
import shutil
import json
from pathlib import Path

TURKSPELL_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = TURKSPELL_DIR.parent / "turkspell-benchmarks"
DIST_DIR = TURKSPELL_DIR / "dist"
RAW_DIR = TURKSPELL_DIR / "raw_data"

TDK_PATH = TURKSPELL_DIR / "raw_data" / "tdk_words.txt"
DD_PATH = TURKSPELL_DIR / "raw_data" / "dil_dernegi_words.txt"
CUSTOM_ABBREV_PATH = TURKSPELL_DIR / "lexicons" / "custom_abbreviations.json"
CUSTOM_NAMES_PATH = TURKSPELL_DIR / "lexicons" / "custom_names.json"
BILIM_SANAT_PATH = TURKSPELL_DIR / "lexicons" / "bilim_sanat_lexicon.json"

AFF_SRC = TURKSPELL_DIR / "tr.aff"
DIC_SRC = TURKSPELL_DIR / "tr.dic"

def get_base_dic_lines():
    root_dic = TURKSPELL_DIR / "tr.dic"
    universal_dic = TURKSPELL_DIR / "dist" / "turkspell-universal" / "tr.dic"
    # If root tr.dic is strictly newer than dist universal tr.dic (e.g. compile_hunspell.py was run),
    # prioritize root tr.dic. Otherwise, prefer dist universal tr.dic to avoid inheriting
    # a profile-specific deployment (e.g. TDK-only).
    if root_dic.exists() and universal_dic.exists():
        if root_dic.stat().st_mtime > universal_dic.stat().st_mtime:
            print("  Base dictionary source: root tr.dic (newer than dist/turkspell-universal/tr.dic)")
            candidates = [root_dic, universal_dic]
        else:
            print("  Base dictionary source: dist/turkspell-universal/tr.dic")
            candidates = [universal_dic, root_dic]
    else:
        candidates = [universal_dic, root_dic]
    for dic_path in candidates:
        if dic_path.exists():
            with open(dic_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > 50000:
                return lines
    return []

sys.path.insert(0, str(TURKSPELL_DIR / "build"))
from utf8_flag_mapping import UTF8_TO_LONG, LONG_TO_UTF8, remap_flag_string, STAGE2_VERB_FLAGS

vowels = "AEIOUaeiouÂÎÖÛÜâîöûüİı"
consonant_cond = "[^AEIOUaeiouÂÎÖÛÜâîöûüİı]"

DEAD_FLAG_CHARS = {LONG_TO_UTF8[f] for f in ['G2', 'NX', 'Vb', 'Vf', 'VL'] if f in LONG_TO_UTF8}
STAGE2_VERB_CHARS = {LONG_TO_UTF8[f] for f in STAGE2_VERB_FLAGS if f in LONG_TO_UTF8}
PROPER_SUB_UTF8 = {k for k, v in UTF8_TO_LONG.items() if v.startswith("p") and len(v) == 3}
KC_FLAG = LONG_TO_UTF8.get("KC", "")

# Case and possessive flags that MUST NEVER be attached to proper nouns without apostrophe
COMMON_CASE_CHARS = {
    LONG_TO_UTF8[f] for f in [
        'DE', 'DL', 'DT', 'L1', 'L2', 'R1', 'R2',
        'a1', 'a2', 'a3', 'a4', 'i1', 'i2', 'i3', 'i4', 'n1', 'n2', 'n3', 'n4', 'y1', 'y2', 'y3', 'y4',
        'A1', 'A2', 'A3', 'A4', 'I1', 'I2', 'I3', 'I4', 'Y1', 'Y2', 'Y3', 'Y4', 'N1', 'N2', 'N3', 'N4',
        'B1', 'B2', 'B3', 'B4', 'F1', 'F2', 'F3', 'F4', 'V1', 'V2', 'V3', 'V4', 'D1', 'D2', 'D3', 'D4', 'C1', 'C2', 'C3', 'C4', 'G1', 'G2', 'G3', 'G4',
        'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'PB', 'PM', 'PN', 'PS', 'PO', 'PR', 'PT', 'PU', 'PV', 'PW', 'PX', 'PZ', 'PQ', 'PF', 'PP',
        'Q1', 'Q2', 'Q3', 'CL', 'CP', 'CV', 'cl', 'CK', 'vc', 'VC',
        'uA', 'uE', 'uO', 'uU', 'cA', 'cE', 'cI', 'cU', 'vA', 'vE', 'sA', 'sE',
        'pA', 'pE', 'pO', 'pU', 'qA', 'qE', 'qO', 'qU'
    ] if f in LONG_TO_UTF8
}

# Structured build wordlists, morphological overrides, and virtual stems loaded from lexicons/build_wordlists.json
_BUILD_WORDLISTS_PATH = TURKSPELL_DIR / "lexicons" / "build_wordlists.json"
with open(_BUILD_WORDLISTS_PATH, "r", encoding="utf-8") as _bwf:
    _BUILD_WORDLISTS = json.load(_bwf)

PURE_PROPER_NOUNS = set(_BUILD_WORDLISTS["pure_proper_nouns"])

RE_OCR_FRAGMENT = re.compile(r'^[rlmny][b-df-hj-np-tv-z]')
RE_REPEATED_CHARS = re.compile(r'(.)\1\1')
RE_CONSONANT_CLUSTER = re.compile(r'^[b-df-hj-np-tv-z]{4,}')

# Extra REP rules loaded from structured JSON in lexicons/
_extra_rep_path = TURKSPELL_DIR / "lexicons" / "extra_rep_rules.json"
if _extra_rep_path.exists():
    with open(_extra_rep_path, "r", encoding="utf-8") as f:
        EXTRA_REP_RULES = json.load(f)
else:
    EXTRA_REP_RULES = []

MANDATORY_HATTED_WORDS = dict(_BUILD_WORDLISTS["mandatory_hatted_words"])
COMPOUND_PROPER_TERMS = list(_BUILD_WORDLISTS["compound_proper_terms"])
COMPOUND_SET = set(COMPOUND_PROPER_TERMS)
LEGITIMATE_MISSED_WORDS = list(_BUILD_WORDLISTS["legitimate_missed_words"])

# Standard regular non-voicing inflection flags (including VC/vc for 1sg/1pl vowel-initial copulas on [pçtk] stems)
BACK_UNVOICED_FLAGS = remap_flag_string("A1 B1 CI CK CL I1 L1 LI LK N1 P1 P5 PB PM PN PS Q1 R1 SL SZ Y1 VC".replace(" ", ""))
FRONT_UNVOICED_FLAGS = remap_flag_string("A3 CI CK DE F1 I2 L2 LI LK N3 P3 P7 PF PP PU PW Q2 R2 SL SZ Y2 cl vc".replace(" ", ""))
BACK_ROUNDED_UNVOICED_FLAGS = remap_flag_string("A2 B2 CI CK CL I1 L1 LI LK N2 P2 P6 PB PO PR PT Q1 R1 SL SZ Y1 VC".replace(" ", ""))
FRONT_ROUNDED_UNVOICED_FLAGS = remap_flag_string("A4 CI CK DE DL DT F2 I2 L2 LI LK N4 P4 P8 PF PQ PV PZ Q2 R2 SL SZ Y2 cl vc".replace(" ", ""))

B3_VOWEL_FLAGS = remap_flag_string("B3 a1 y1 L1 R1 n1 i1 Q1 PB PS P1 P5 PM PN CL LI LK SZ CI CK SL DL DT DE".replace(" ", ""))
B4_VOWEL_FLAGS = remap_flag_string("B4 a2 y1 L1 R1 n2 i1 Q1 PB PT P2 P6 PO PR CL LI LK SZ CI CK SL DL DT DE".replace(" ", ""))
F3_VOWEL_FLAGS = remap_flag_string("F3 a3 y2 L2 R2 n3 i2 Q2 PF PU P3 P7 PP PW cl LI LK SZ CI CK SL DL DT DE".replace(" ", ""))
F4_VOWEL_FLAGS = remap_flag_string("F4 a4 y2 L2 R2 n4 i2 Q2 PF PV P4 P8 PQ PZ cl LI LK SZ CI CK SL DL DT DE".replace(" ", ""))

HEAD_FLAG_OVERRIDES = dict(_BUILD_WORDLISTS["base_head_flag_overrides"])
BACK_NOVOICING_STEMS = list(_BUILD_WORDLISTS["back_novoicing_stems"])
BACK_ROUNDED_NOVOICING_STEMS = list(_BUILD_WORDLISTS["back_rounded_novoicing_stems"])
FRONT_NOVOICING_STEMS = list(_BUILD_WORDLISTS["front_novoicing_stems"])
DUAL_VOICING_BACK_ROUNDED = list(_BUILD_WORDLISTS["dual_voicing_back_rounded"])
DUAL_VOICING_BACK_UNROUNDED = list(_BUILD_WORDLISTS["dual_voicing_back_unrounded"])
DUAL_VOICING_G_BACK_ROUNDED = list(_BUILD_WORDLISTS["dual_voicing_g_back_rounded"])
NON_VERB_MAK_NOUNS = list(_BUILD_WORDLISTS["non_verb_mak_nouns"])

VOWEL_DROP_D1_HEADS = set(_BUILD_WORDLISTS["vowel_drop_d1_heads"])
VOWEL_DROP_D2_HEADS = set(_BUILD_WORDLISTS["vowel_drop_d2_heads"])
VOWEL_DROP_D3_HEADS = set(_BUILD_WORDLISTS["vowel_drop_d3_heads"])
VOWEL_DROP_D4_HEADS = set(_BUILD_WORDLISTS["vowel_drop_d4_heads"])

_voicing_table = {"p": "b", "ç": "c", "t": "d", "k": "ğ", "g": "ğ"}
PURGE_VIRTUAL_STEMS = {"felaked", "stoğ", "yahudiliğ", "ferahnağ"}
for _w in BACK_NOVOICING_STEMS + BACK_ROUNDED_NOVOICING_STEMS + FRONT_NOVOICING_STEMS:
    if _w and _w[-1] in _voicing_table:
        PURGE_VIRTUAL_STEMS.add(_w[:-1] + _voicing_table[_w[-1]])

PALATAL_L_HEADS = set(_BUILD_WORDLISTS["base_palatal_l_heads"])
PALATAL_L_FLAGS = "".join(LONG_TO_UTF8[f] for f in "A4 N4 P4 PV P8 Y2 L2 R2 I2 PQ PZ CK cl LF LSZ LFK LCI PF".split())

# Load completed POS & morphological attributes for the 45,273 previously unannotated TDK/DD lemmas
_COMPLETED_POS_PATH = TURKSPELL_DIR / "lexicons" / "authority_pos_completed.json"
if _COMPLETED_POS_PATH.exists():
    with open(_COMPLETED_POS_PATH, encoding="utf-8") as _cpf:
        for _item in json.load(_cpf):
            _lem = _item.get("lemma", "")
            _pos = _item.get("pos", "Noun")
            _attrs = _item.get("attributes", [])
            if _lem in HEAD_FLAG_OVERRIDES or _lem in PALATAL_L_HEADS:
                continue
            if "CompoundP3sg" in _attrs:
                if _lem.endswith("ı"):
                    HEAD_FLAG_OVERRIDES[_lem] = "∀∈∌∍∎∖∗∘∡∧∩∪∫∲∶∺∼∽≂≉≋≍≎≣"
                elif _lem.endswith("u"):
                    HEAD_FLAG_OVERRIDES[_lem] = "∁∉∌∍∎∖∗∘∡∧∩∪∬∳∷∺∾≁≃≉≋≍≎≣"
                elif _lem.endswith("i"):
                    HEAD_FLAG_OVERRIDES[_lem] = "∂∊∌∍∖∗∘∢∨∩∪∭∴∸∻∿≄≆≊≌≍≎≤≩"
                elif _lem.endswith("ü"):
                    HEAD_FLAG_OVERRIDES[_lem] = "∃∋∌∍∖∗∘∢∨∩∪∮∵∹∻≀≅≈≊≌≍≎≤≩"
            elif "InverseHarmony" in _attrs:
                if _lem.endswith(("ol", "ul")):
                    PALATAL_L_HEADS.add(_lem)
                elif _lem.endswith(("al", "at")):
                    HEAD_FLAG_OVERRIDES[_lem] = FRONT_UNVOICED_FLAGS
            elif _pos in ("Interjection", "Conjunction"):
                HEAD_FLAG_OVERRIDES[_lem] = ""

VIRTUAL_STEMS = list(_BUILD_WORDLISTS["base_virtual_stems"])


def get_numeral_flag_code(n: int) -> str:
    """Return the 2-char numeral affix flag code (N5..ND) for integer n based on its Turkish reading."""
    if n == 0:
        return "NC"
    u = n % 10
    if u != 0:
        return {
            1: "N5", 2: "N6", 3: "N7", 4: "N7", 5: "N8",
            6: "N9", 7: "N6", 8: "N5", 9: "NA"
        }[u]
    t = n % 100
    if t != 0:
        return {
            10: "NA", 20: "N6", 30: "NA", 40: "NB", 50: "N6",
            60: "NB", 70: "N8", 80: "N5", 90: "NC"
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

    # 3. 24-hour clock times HH.MM (where .00 follows hour phonology per TDK rules)
    for hh in range(0, 25):
        hh_strs = [f"{hh:02d}"] + ([str(hh)] if 1 <= hh <= 9 else [])
        for mm in range(0, 60):
            fc = get_numeral_flag_code(hh) if mm == 0 else get_numeral_flag_code(mm)
            mm_str = f"{mm:02d}"
            for hs in hh_strs:
                _add(f"{hs}.{mm_str}", fc)

    return list(stems.values())


VIRTUAL_STEMS.extend(generate_numeral_virtual_stems())

EXTRA_AUTHORITY_HEADWORDS = list(_BUILD_WORDLISTS["extra_authority_headwords"])

def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()

def tr_title(s: str) -> str:
    if not s: return s
    if s[0] == 'i': return 'İ' + s[1:]
    if s[0] == 'ı': return 'I' + s[1:]
    return s[0].upper() + s[1:]

def load_lexicons():
    print("Loading authority sets & custom lexicons...")
    tdk_words = set()
    with open(TDK_PATH, encoding="utf-8") as f:
        for line in f:
            w = tr_lower(line.strip().split("/")[0].split(" (")[0])
            if w: tdk_words.add(w)
            
    dd_words = set()
    with open(DD_PATH, encoding="utf-8") as f:
        for line in f:
            w = tr_lower(line.strip().split("/")[0].split(" (")[0])
            if w: dd_words.add(w)
            
    custom_abbrevs = set()
    custom_abbrevs_orig = set()
    if CUSTOM_ABBREV_PATH.exists():
        with open(CUSTOM_ABBREV_PATH, encoding="utf-8") as f:
            for item in json.load(f):
                lem = item.get("lemma", "").strip()
                if lem:
                    # Do NOT lowercase abbreviations: preserve exact casing
                    custom_abbrevs_orig.add(lem)
                    if lem.islower():
                        custom_abbrevs.add(lem)
                    
    custom_names = set()
    custom_names_orig = set()
    if CUSTOM_NAMES_PATH.exists():
        with open(CUSTOM_NAMES_PATH, encoding="utf-8") as f:
            for item in json.load(f):
                lem = item.get("lemma", "").strip()
                if lem:
                    custom_names_orig.add(lem)
                    if lem.islower():
                        custom_names.add(lem)
                    
    bilim_sanat_lexicon = []
    bilim_sanat_words = set()
    if BILIM_SANAT_PATH.exists():
        with open(BILIM_SANAT_PATH, encoding="utf-8") as f:
            bilim_sanat_lexicon = json.load(f)
            for item in bilim_sanat_lexicon:
                lem = item.get("lemma", "").strip()
                if lem:
                    bilim_sanat_words.add(tr_lower(lem))
                    
    print(f"  TDK: {len(tdk_words):,}, DD: {len(dd_words):,}, Bilim-Sanat: {len(bilim_sanat_words):,}, Abbrevs: {len(custom_abbrevs_orig):,}, Names: {len(custom_names_orig):,}")
    return tdk_words, dd_words, bilim_sanat_lexicon, bilim_sanat_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig

def build_hardened_aff(profile="tdk"):
    print(f"Building hardened .aff file for profile [{profile}]...")
    with open(AFF_SRC, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    hardened_lines = []
    fixed_wildcards = 0
    
    # 1. Parse into header and SFX/PFX blocks to drop dead flags and duplicates
    header_lines = []
    sfx_blocks = {}
    curr_flag = None
    
    for line in lines:
        line_s = line.strip()
        parts = line_s.split()
        
        # Check if starting an SFX/PFX block
        if len(parts) >= 4 and parts[0] in ('SFX', 'PFX') and parts[2] in ('Y', 'N'):
            curr_flag = parts[1]
            if curr_flag not in sfx_blocks:
                sfx_blocks[curr_flag] = []
            sfx_blocks[curr_flag].append(line)
        elif curr_flag is not None and len(parts) >= 2 and parts[0] in ('SFX', 'PFX') and parts[1] == curr_flag:
            # Suffix rule within curr_flag block
            # Safely disable ungrammatical / vowel-violating rules
            if line_s.startswith("SFX ≠") and "emek ebilecek" in line_s:
                if len(parts) >= 5: parts[4] = "X"; line = " ".join(parts) + "\n"
            elif line_s == "SFX ≖ emek enr emek": line = "SFX ≖ emek enr X\n"
            elif line_s == "SFX ≟ umak unr umak": line = "SFX ≟ umak unr X\n"
            elif line_s == "SFX ≟ amak atrsanız amak": line = "SFX ≟ amak atrsanız X\n"
            elif line_s in ("SFX ⊁ mek mesü mek", "SFX ≘ mek mesü mek"): line = line.replace("mek\n", "X\n")
            elif line_s.startswith("SFX ≟") and "masunı" in line_s:
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s.startswith("SFX ⊂ mak ırm"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s.startswith("SFX ⊁ mek üre"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s in ("SFX ≓ amak adırıp amak", "SFX ≓ ımak ıdırıp ımak"):
                parts = line_s.split(); parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s.startswith("SFX ⊃ mek irme/"):
                parts[-1] = "X"; line = " ".join(parts) + "\n"
            elif line_s == "SFX ≚ tmak dıktan tmak":
                line = "SFX ≚ mak tıktan tmak\n"
            elif line_s == "SFX ≛ tmak duktan tmak":
                line = "SFX ≛ mak tuktan tmak\n"
            elif line_s == "SFX ≜ tmek dikten tmek":
                line = "SFX ≜ mek tikten tmek\n"
            elif line_s == "SFX ≝ tmek dükten tmek":
                line = "SFX ≝ mek tükten tmek\n"
            elif line_s in ("SFX ≠ emek idikten [dy]emek", "SFX ≠ emek idikten demek", "SFX ≠ emek idikten yemek"):
                line = f"SFX ≠ mek dikten {parts[4]}\n"
            elif len(parts) >= 4 and "/" in parts[3]:
                clean_add, flags = parts[3].split("/", 1)
                if clean_add.endswith("ğ") and "X" not in flags:
                    parts[3] = f"{clean_add}/X{flags}"
                    line = " ".join(parts) + "\n"
                # Overgeneration hardening: prevent chained derivations on derived suffixes
                _lk_flags = {LONG_TO_UTF8[f] for f in ("LK", "LFK") if f in LONG_TO_UTF8}
                _bad_on_lik = {LONG_TO_UTF8[f] for f in ("DT", "DL", "DE", "CI", "LCI", "LK", "LFK") if f in LONG_TO_UTF8}
                _all_deriv_flags = {LONG_TO_UTF8[f] for f in ("LI", "LF", "SZ", "LSZ", "CK", "SL", "DT", "DL", "DE", "CI", "LCI", "LK", "LFK") if f in LONG_TO_UTF8}
                if curr_flag in _lk_flags or clean_add.endswith(("lık", "lik", "luk", "lük")):
                    flags = "".join(c for c in flags if c not in _bad_on_lik)
                    parts[3] = f"{clean_add}/{flags}"
                    line = " ".join(parts) + "\n"
                if clean_add.endswith((
                    "cılık", "cilik", "culuk", "cülük",
                    "çılık", "çilik", "çuluk", "çülük",
                    "sızlık", "sizlik", "suzluk", "süzlük",
                    "lılık", "lilik", "luluk", "lülük",
                    "sallık", "sellik"
                )):
                    flags = "".join(c for c in flags if c not in _all_deriv_flags)
                    parts[3] = f"{clean_add}/{flags}"
                    line = " ".join(parts) + "\n"
            if curr_flag not in STAGE2_VERB_CHARS and len(parts) >= 5:
                clean_add = parts[3].split("/")[0]
                if parts[2] in ("mak", "mek"):
                    if clean_add.startswith(("ıl", "il", "ul", "ül")):
                        parts[4] = f"[^lAEIOUaeiouÂÎÖÛÜâîöûüİı]{parts[2]}"
                        line = " ".join(parts) + "\n"
                        fixed_wildcards += 1
                    elif parts[4] in (".", consonant_cond) and clean_add and clean_add[0] in vowels:
                        parts[4] = f"[^AEIOUaeiouÂÎÖÛÜâîöûüİı]{parts[2]}"
                        line = " ".join(parts) + "\n"
                        fixed_wildcards += 1
                elif parts[4] == "." and clean_add and clean_add[0] in vowels:
                    parts[4] = consonant_cond
                    line = " ".join(parts) + "\n"
                    fixed_wildcards += 1
            sfx_blocks[curr_flag].append(line)
        elif curr_flag is not None and (not line_s or line_s.startswith('#')):
            curr_flag = None
            header_lines.append(line)
        elif curr_flag is not None:
            sfx_blocks[curr_flag].append(line)
        else:
            header_lines.append(line)
            
    print(f"  Fixed {fixed_wildcards} wildcard rules in .aff")
    
    # 2. Prune dead flag blocks and deduplicate identical rules per block
    pruned_flags = 0
    dropped_rules = 0
    clean_sfx_blocks = {}
    
    for flag, block in sfx_blocks.items():
        if flag in DEAD_FLAG_CHARS:
            pruned_flags += 1
            dropped_rules += len(block) - 1
            continue
            
        header, rules = block[0], block[1:]
        seen = set()
        kept = []
        flag_long = UTF8_TO_LONG.get(flag, flag)
        for r in rules:
            r_strip = r.strip()
            if r_strip in seen:
                dropped_rules += 1
                continue
            parts_r = r_strip.split()
            if len(parts_r) >= 5:
                cond = parts_r[4]
                clean_add_r = parts_r[3].split("/")[0]
                if cond == 'X' or clean_add_r in ('mesü', 'memüz', 'menüz', 'masu', 'mamuz', 'manuz', 'eceğüm', 'yeceğüm', 'deceğüm', 'acağum', 'yacağum'):
                    dropped_rules += 1
                    continue
                if flag_long == 'VH' and cond == 'imek':
                    dropped_rules += 1
                    continue
                elif flag_long == 'VS' and cond == 'ımak':
                    dropped_rules += 1
                    continue
                if any(bad_s in clean_add_r for bad_s in ('laryla', 'leryle', 'kilar')):
                    parts_r[3] = parts_r[3].replace('laryla', 'larıyla').replace('leryle', 'leriyle').replace('kilar', 'kiler')
                # Fix verb continuation vowel harmony mismatches
                if '/' in parts_r[3]:
                    if clean_add_r in ('emez', 'ülmez', 'ülemez', 'yemez', 'der', 'demez', 'dülmez', 'dülemez'):
                        parts_r[3] = parts_r[3].replace('/' + LONG_TO_UTF8['cI'], '/' + LONG_TO_UTF8['cE'])
                    elif clean_add_r in ('amaz', 'ulmaz', 'ulamaz', 'yamaz'):
                        parts_r[3] = parts_r[3].replace('/' + LONG_TO_UTF8['cU'], '/' + LONG_TO_UTF8['cA'])
                    elif clean_add_r == 'dükleri':
                        parts_r[3] = parts_r[3].replace('/' + LONG_TO_UTF8['pU'], '/' + LONG_TO_UTF8['pE'])
                    elif clean_add_r == 'dukları':
                        parts_r[3] = parts_r[3].replace('/' + LONG_TO_UTF8['pO'], '/' + LONG_TO_UTF8['pA'])
                    elif clean_add_r.endswith('abileceği'):
                        parts_r[3] = parts_r[3].replace('/' + LONG_TO_UTF8['pA'], '/' + LONG_TO_UTF8['pE'])
                    elif flag_long in ('pBR', 'pBI', 'pBP', 'pOR', 'pOI', 'pOP'):
                        parts_r[3] = parts_r[3].replace('/' + LONG_TO_UTF8['cl'], '/' + LONG_TO_UTF8['CL'])
                        if flag_long == 'pOP':
                            parts_r[3] = parts_r[3].replace("'ıyla/", "'uyla/").replace("'sıyla/", "'suyla/")
                    elif flag_long == 'pUP':
                        parts_r[3] = parts_r[3].replace("'iyle/", "'üyle/").replace("'siyle/", "'süyle/")
                if flag_long == 'CK' and '/' in parts_r[3] and clean_add_r in ('cık', 'cuk', 'cik', 'cük', 'çık', 'çuk', 'çik', 'çük'):
                    from utf8_flag_mapping import remap_flag_string
                    ck_chains = {
                        'cık': ('cığ', remap_flag_string('L1R1I1Q1PBCLLILKSZCICKSLDLDTDE'), remap_flag_string('A1Y1N1PSP1P5PMPNVCNE')),
                        'çık': ('çığ', remap_flag_string('L1R1I1Q1PBCLLILKSZCICKSLDLDTDE'), remap_flag_string('A1Y1N1PSP1P5PMPNVCNE')),
                        'cuk': ('cuğ', remap_flag_string('L1R1I1Q1PBCLLILKSZCICKSLDLDTDE'), remap_flag_string('A2Y1N2PTP2P6POPRVCNE')),
                        'çuk': ('çuğ', remap_flag_string('L1R1I1Q1PBCLLILKSZCICKSLDLDTDE'), remap_flag_string('A2Y1N2PTP2P6POPRVCNE')),
                        'cik': ('ciğ', remap_flag_string('L2R2I2Q2PFclLILKSZCICKSLDLDTDE'), remap_flag_string('A3Y2N3PUP3P7PPPWvcNE')),
                        'çik': ('çiğ', remap_flag_string('L2R2I2Q2PFclLILKSZCICKSLDLDTDE'), remap_flag_string('A3Y2N3PUP3P7PPPWvcNE')),
                        'cük': ('cüğ', remap_flag_string('L2R2I2Q2PFclLILKSZCICKSLDLDTDE'), remap_flag_string('A4Y2N4PVP4P8PQPZvcNE')),
                        'çük': ('çüğ', remap_flag_string('L2R2I2Q2PFclLILKSZCICKSLDLDTDE'), remap_flag_string('A4Y2N4PVP4P8PQPZvcNE')),
                    }
                    suf_v, cons_c, vow_c = ck_chains[clean_add_r]
                    r1_s = f"SFX {flag} 0 {clean_add_r}/{cons_c} {cond}"
                    r2_s = f"SFX {flag} 0 {suf_v}/{vow_c} {cond}"
                    for rx_s in (r1_s, r2_s):
                        if rx_s not in seen:
                            seen.add(rx_s)
                            kept.append(rx_s + '\n')
                    continue
                r_strip = ' '.join(parts_r)
                r = r_strip + '\n'
            if r_strip in seen:
                dropped_rules += 1
                continue
            seen.add(r_strip)
            kept.append(r)

        if flag_long == 'VR':
            for opt_suf in ('ayım', 'asın', 'alım'):
                opt_rule = f"SFX {flag} mak {opt_suf} [^AEIOUaeiouÂÎÖÛÜâîöûüİı]mak"
                if opt_rule not in seen:
                    seen.add(opt_rule)
                    kept.append(opt_rule + "\n")
        elif flag_long == 'VG':
            for opt_suf in ('eyim', 'esin', 'elim'):
                opt_rule = f"SFX {flag} mek {opt_suf} [^AEIOUaeiouÂÎÖÛÜâîöûüİı]mek"
                if opt_rule not in seen:
                    seen.add(opt_rule)
                    kept.append(opt_rule + "\n")
        elif flag_long in ('wi', 'wj', 'wu', 'wh'):
            _aor_lk_specs = {
                'wi': ('mak', 'ı', 'a', LONG_TO_UTF8['pA']),
                'wj': ('mek', 'i', 'e', LONG_TO_UTF8['pE']),
                'wu': ('mak', 'u', 'a', LONG_TO_UTF8['pO']),
                'wh': ('mek', 'ü', 'e', LONG_TO_UTF8['pU']),
            }
            _st, _vh, _vl, _p3 = _aor_lk_specs[flag_long]
            for _lk_s in (
                f"{_vh}rl{_vh}k", f"{_vh}rl{_vh}kt{_vh}r",
                f"{_vh}rl{_vh}ğ{_vh}/{_p3}", f"{_vh}rl{_vh}ğ{_vh}",
                f"{_vh}rl{_vh}ğ{_vl}", f"{_vh}rl{_vh}ğ{_vh}n",
                f"{_vh}rl{_vh}ğ{_vh}n{_vl}", f"{_vh}rl{_vh}ğ{_vh}nd{_vl}", f"{_vh}rl{_vh}ğ{_vh}nd{_vl}n",
                f"{_vh}rl{_vh}ğ{_vh}n{_vh}", f"{_vh}rl{_vh}ğ{_vh}n{_vh}n",
            ):
                _r_lk = f"SFX {flag} {_st} {_lk_s} [nl]{_st}"
                if _r_lk not in seen:
                    seen.add(_r_lk)
                    kept.append(_r_lk + "\n")
            _is_b = flag_long in ('wa', 'wi', 'wr', 'wu')
            _st = 'mak' if _is_b else 'mek'
            _vl = 'a' if _is_b else 'e'
            _vuh = 'ı' if _is_b else 'i'
            for _part_s in (
                f"m{_vl}z{_vuh}d{_vuh}r",
                f"m{_vl}zl{_vl}r{_vuh}",
                f"m{_vl}zl{_vl}r{_vuh}n{_vl}",
                f"m{_vl}zl{_vl}r{_vuh}nd{_vl}",
                f"m{_vl}zl{_vl}r{_vuh}nd{_vl}n",
                f"m{_vl}zl{_vl}r{_vuh}nd{_vl}nd{_vuh}r",
                f"m{_vl}zl{_vl}r{_vuh}n",
                f"m{_vl}zl{_vl}r{_vuh}n{_vuh}",
                f"m{_vl}zl{_vl}r{_vuh}n{_vuh}n",
                f"m{_vl}zd{_vl}nd{_vuh}r",
            ):
                _r_part = f"SFX {flag} {_st} {_part_s} {_st}"
                if _r_part not in seen:
                    seen.add(_r_part)
                    kept.append(_r_part + "\n")
        if flag_long in ('VA', 'VB', 'VE', 'VF', 'VG', 'VH', 'VK', 'VM', 'VN', 'VR', 'VS', 'VY'):
            _pot_extra = []
            for _r_existing in kept:
                _pr = _r_existing.strip().split()
                if len(_pr) >= 5 and _pr[3].endswith('bilirlik'):
                    _base_b = _pr[3][:-3]  # '...bilir'
                    for _ex_s in (f"{_base_b}liktir", f"{_base_b}liğine", f"{_base_b}liğin"):
                        _pot_extra.append(f"SFX {flag} {_pr[2]} {_ex_s} {_pr[4]}")
            for _rx in _pot_extra:
                if _rx not in seen:
                    seen.add(_rx)
                    kept.append(_rx + "\n")
            
        parts = header.split()
        if len(parts) >= 4 and parts[2] in ('Y', 'N'):
            parts[3] = str(len(kept))
            header = " ".join(parts) + "\n"
            
        # Consolidate VY (demek + yemek) duplicate rules
        if flag_long == 'VY':
            demek_map = {}
            yemek_map = {}
            other_vy = []
            for r in kept:
                parts_r = r.strip().split()
                if len(parts_r) >= 5:
                    strip, add, cond = parts_r[2], parts_r[3], parts_r[4]
                    if cond == 'demek': demek_map[(strip, add)] = r
                    elif cond == 'yemek': yemek_map[(strip, add)] = r
                    else: other_vy.append(r)
                else: other_vy.append(r)
            common_keys = set(demek_map.keys()) & set(yemek_map.keys())
            consolidated_vy = []
            for k in sorted(common_keys):
                strip, add = k
                consolidated_vy.append(f"SFX {flag} {strip} {add} [dy]emek\n")
            for k, r in demek_map.items():
                if k not in common_keys: consolidated_vy.append(r)
            for k, r in yemek_map.items():
                if k not in common_keys: consolidated_vy.append(r)
            consolidated_vy.extend(other_vy)
            parts = header.split()
            parts[3] = str(len(consolidated_vy))
            header = " ".join(parts) + "\n"
            dropped_rules += len(common_keys)
            kept = consolidated_vy

        clean_sfx_blocks[flag] = [header] + kept
        
    print(f"  Pruned {pruned_flags} dead flag blocks, {dropped_rules:,} total duplicate/dead rules.")
    
    # Reassemble aff content
    aff_text = "".join(header_lines).rstrip() + "\n\n"
    for flag in sorted(clean_sfx_blocks.keys()):
        aff_text += "".join(clean_sfx_blocks[flag]) + "\n"
        
    # Enhanced MAP Matrix
    new_map = """MAP 14
MAP aâAÂ
MAP uûUÛ
MAP uüUÜ
MAP iîİÎ
MAP ıiIİ
MAP oöOÖ
MAP eêEÊ
MAP cçCÇ
MAP gğGĞ
MAP sşSŞ
MAP dtDT
MAP bpBP
MAP vwyVWY
MAP '’‘"""
    aff_text = re.sub(r'MAP \d+\n(?:MAP [^\n]+\n)+', new_map + '\n', aff_text, count=1)
    
    # Extra REP rules: clean any leading "REP " prefixes
    clean_extra = []
    for r in EXTRA_REP_RULES:
        rule_str = " ".join(r) if isinstance(r, list) else str(r).strip()
        while rule_str.startswith("REP "):
            rule_str = rule_str[4:].strip()
        if rule_str:
            clean_extra.append(rule_str)

    if profile == "tdk":
        clean_extra.extend([
            "resmi resmî",
            "milli millî",
            "dini dinî",
            "askeri askerî",
            "tarihi tarihî",
            "ahlaki ahlâkî",
            "dahili dâhilî",
            "ilmi ilmî",
            "edebi edebî",
            "ebedi ebedî",
            "insani insanî",
            "ruhi ruhî",
            "siyasi siyasî",
            "hukuki hukukî",
            "iktisadi iktisadî",
            "felsefi felsefî",
            "zihni zihnî",
            "hayali hayalî",
            "manevi manevî",
            "maddi maddî",
            "harbi harbî",
            "kısmi kısmî",
            "şahsi şahsî",
            "vicdani vicdanî",
            "dahiliye dâhiliye",
            "dahil dâhil",
            "bekar bekâr",
            "ruzgar rüzgâr",
            "hikaye hikâye",
            "kagıt kâğıt",
            "kagit kâğıt",
            "dukkan dükkân",
            "tezgah tezgâh",
            "mekan mekân",
            "imkan imkân",
            "mahkum mahkûm",
            "sukun sükûn",
            "sukut sükût",
            "batini bâtıni",
            "teleskopu teleskobu",
            "bergamotu bergamodu",
            "baçı bacı",
            "bilim$ _bilimi",
            "^hayalilik$ hayalîlik",
            "^haki$ hâkî"
        ])
        # Load all TDK-open compound suggestions (where joined is used in Dil Derneği)
        clean_extra.extend(_BUILD_WORDLISTS.get("tdk_open_compound_rep", []))
    elif profile == "dd":
        clean_extra.extend([
            "dâhilî dahili",
            "hâkî haki",
            "î i",
            "resmî resmi",
            "askerî askeri",
            "dinî dini",
            "millî milli",
            "misakımilli Misakımilli",
            "misakımillî Misakımilli",
            "Misakımillî Misakımilli"
        ])
        # Load all DD-open compound suggestions (where joined is used in TDK)
        clean_extra.extend(_BUILD_WORDLISTS.get("dd_open_compound_rep", []))
        
    # Extract only genuine replacement pairs from base aff, ignoring digit counts like "1265"
    base_rep = []
    for m in re.findall(r'^REP\s+(.+)$', aff_text, re.MULTILINE):
        rule_str = m.strip()
        while rule_str.startswith("REP "):
            rule_str = rule_str[4:].strip()
        parts = rule_str.split()
        if len(parts) >= 2 and not (len(parts) == 1 and parts[0].isdigit()):
            base_rep.append(rule_str)

    all_rep = [r for r in dict.fromkeys(clean_extra + base_rep) if len(r.split()) >= 2 and r.split()[0] != r.split()[1]]
    rep_block = f"REP {len(all_rep)}\n" + "\n".join(f"REP {r}" for r in all_rep) + "\n"

    # Remove all existing REP lines and replace cleanly after MAXNGRAMSUGS
    aff_text = re.sub(r'^REP.*$\n?', '', aff_text, flags=re.MULTILINE)
    aff_text = re.sub(r'(MAXNGRAMSUGS \d+)\n+', r'\1\n\n' + rep_block + '\n', aff_text, count=1)
    
    return aff_text

PROPER_B = remap_flag_string("pBN pBL pBR pBY pBA pBI pBP pBC".replace(" ", ""))
PROPER_O = remap_flag_string("pON pOL pOR pOY pOA pOI pOP pOC".replace(" ", ""))
PROPER_F = remap_flag_string("pFN pFL pFR pFY pFA pFI pFP pFC".replace(" ", ""))
PROPER_U = remap_flag_string("pUN pUL pUR pUY pUA pUI pUP pUC".replace(" ", ""))

UNIT_FLAG_MAP = {
    "cm": PROPER_F, "mm": PROPER_F, "km": PROPER_F, "dm": PROPER_F, "nm": PROPER_F,
    "ml": PROPER_F, "mL": PROPER_F, "cl": PROPER_F, "dl": PROPER_F, "hl": PROPER_F,
    "lt": PROPER_F, "sn": PROPER_F,
    "kg": PROPER_B, "gr": PROPER_B, "mg": PROPER_B, "dg": PROPER_B, "cg": PROPER_B,
    "dk": PROPER_B, "yy": PROPER_B,
    "kr": PROPER_O, "krş": PROPER_O,
}

BRAND_FLAG_MAP = {
    "iPhone": remap_flag_string("KC CK CL cl L1 L2".replace(" ", "")) + PROPER_O + PROPER_F,
    "iPad": remap_flag_string("KC CK cl L2".replace(" ", "")) + PROPER_F + PROPER_B,
    "YouTube": remap_flag_string("CK CL cl L1 L2".replace(" ", "")) + PROPER_O + PROPER_F,
    "Google": remap_flag_string("CK CL cl L1 L2".replace(" ", "")) + PROPER_B + PROPER_F,
    "Apple": remap_flag_string("CK CL cl L1 L2".replace(" ", "")) + PROPER_B + PROPER_F,
    "Twitter": remap_flag_string("CK CL cl L1 L2".replace(" ", "")) + PROPER_B + PROPER_F,
    "VMware": remap_flag_string("CK cl L2".replace(" ", "")) + PROPER_F,
    "A101": PROPER_F,
}


def get_abbrev_flags(w: str) -> str:
    if not w or len(w) <= 1 or any(c in w for c in ". '/"):
        return ""
    if w in UNIT_FLAG_MAP:
        return UNIT_FLAG_MAP[w]
    if w in BRAND_FLAG_MAP:
        return BRAND_FLAG_MAP[w]
    wl = tr_lower(w)
    if wl in ("usb", "hdmi", "hdmı"):
        return HEAD_FLAG_OVERRIDES[wl]
    if w.isupper() and w.isalpha() and len(w) >= 2:
        if w[-1] in "AIÂ":
            fl = PROPER_B
        elif w[-1] in "OUÛ":
            fl = PROPER_O
        elif w[-1] in "EİÎ":
            fl = PROPER_F
        elif w[-1] in "ÖÜ":
            fl = PROPER_U
        else:
            if w[-1] == "Q":
                fl = PROPER_U
            elif w[-1] == "W":
                fl = PROPER_O + PROPER_F
            else:
                fl = PROPER_F
            if w[-1] in "KH" or w in ("TL", "GB", "MB", "TB", "KB", "PB"):
                fl += PROPER_B
            for ch in reversed(w):
                if ch in "AIÂOUÛEİÎÖÜ":
                    if ch in "AIÂ":
                        fl += PROPER_B
                    elif ch in "OUÛ":
                        fl += PROPER_O
                    elif ch in "EİÎ":
                        fl += PROPER_F
                    elif ch in "ÖÜ":
                        fl += PROPER_U
                    break
        return "".join(sorted(set(fl)))
    if w.isalpha() and len(w) >= 2:
        lv = "e"
        for ch in reversed(w):
            if ch in "aıâouûeiîöüAIÂOUÛEİÎÖÜ":
                lv = tr_lower(ch)
                break
        if lv in "aıâ":
            fl = PROPER_B
        elif lv in "ouû":
            fl = PROPER_O
        elif lv in "eiî":
            fl = PROPER_F
        else:
            fl = PROPER_U
        if w[-1].isupper() and w[-1] not in "AIÂOUÛEİÎÖÜ":
            fl += PROPER_F
            if w[-1] in "KH":
                fl += PROPER_B
        return "".join(sorted(set(fl)))
    return ""


def build_sanitized_dic(tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig, bilim_sanat_lexicon=None, bilim_sanat_words=None, profile="tdk", raw_lines=None):
    print(f"Sanitizing .dic file for profile [{profile}]...")
    
    unhatted_to_purge = {tr_lower(v) for v in MANDATORY_HATTED_WORDS.values()}
    unhat_map = str.maketrans('âîûÂÎÛ', 'aiuAIU')
    _hat_scan_words = (
        tdk_words
        | dd_words
        | (bilim_sanat_words if bilim_sanat_words else set())
        | {tr_lower(w.split("/")[0]) for w in LEGITIMATE_MISSED_WORDS + EXTRA_AUTHORITY_HEADWORDS}
    )
    for h in _hat_scan_words:
        if any(c in h for c in 'âîû'):
            u = h.translate(unhat_map)
            if profile == "tdk":
                if u not in tdk_words:
                    unhatted_to_purge.add(tr_lower(u))
            else:
                if u not in dd_words and u not in tdk_words:
                    unhatted_to_purge.add(tr_lower(u))
    print(f"  Unhatted clones targeted for purge: {len(unhatted_to_purge)}")

    authority_all = tdk_words | dd_words
    if profile in ("universal", "bilim-sanat", "tdk") and bilim_sanat_words:
        authority_all = authority_all | bilim_sanat_words
    dd_words_to_purge = set()
    bilim_sanat_only_to_purge = set()
    if profile == "tdk":
        all_ref = tdk_words | (bilim_sanat_words if bilim_sanat_words else set())
        dd_words_to_purge = (dd_words - all_ref) - custom_names - custom_abbrevs - {tr_lower(c) for c in COMPOUND_SET}
        print(f"  Dil Derneği-only words targeted for purge: {len(dd_words_to_purge)}")
    elif profile == "dd":
        all_ref = dd_words
        if bilim_sanat_words:
            _legit_heads = {tr_lower(w.split("/")[0]) for w in LEGITIMATE_MISSED_WORDS + EXTRA_AUTHORITY_HEADWORDS}
            _bs_only = (bilim_sanat_words - dd_words - tdk_words) - custom_names - custom_abbrevs - {tr_lower(c) for c in COMPOUND_SET} - _legit_heads
            bilim_sanat_only_to_purge = _bs_only | {w.replace("î", "i") for w in _bs_only}
    else:
        all_ref = authority_all
    whitelist = (all_ref - unhatted_to_purge) | custom_abbrevs | custom_names | {tr_lower(c) for c in COMPOUND_SET}
    
    _bad_stems_path = TURKSPELL_DIR / "lexicons" / "bad_stems.json"
    if _bad_stems_path.exists():
        with open(_bad_stems_path, "r", encoding="utf-8") as f:
            BAD_STEMS = set(json.load(f))
    else:
        BAD_STEMS = set()
    if profile == "tdk":
        BAD_STEMS.update({"fata", "çe"})

    _B12_CHARS = {LONG_TO_UTF8["B1"], LONG_TO_UTF8["B2"]}
    _F12_CHARS = {LONG_TO_UTF8["F1"], LONG_TO_UTF8["F2"]}
    _VC_CHAR = LONG_TO_UTF8["VC"]
    _vc_CHAR = LONG_TO_UTF8["vc"]
    
    if raw_lines is None:
        raw_lines = get_base_dic_lines()
    if raw_lines and raw_lines[0].strip().isdigit():
        raw_lines = raw_lines[1:]
        
    clean_entries = []
    seen_heads = set()
    
    removed_permutations = 0
    removed_crawler_spam = 0
    removed_unhatted_dups = 0
    removed_bad_stems = 0
    removed_dd_words = 0
    removed_redundant_upper = 0
    cleaned_common_noun_flags = 0
    
    # Single-pass parse and pre-scan lowercase heads
    existing_lower_heads = set()
    parsed_lines = []
    for line in raw_lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        idx = line_clean.find("/")
        if idx != -1:
            head = line_clean[:idx]
            flags = line_clean[idx+1:]
        else:
            head = line_clean
            flags = ""
        parsed_lines.append((head, flags))
        if head.islower():
            existing_lower_heads.add(head)

    virtual_stem_heads = {w.split("/")[0] for w in VIRTUAL_STEMS}
    for head, flags in parsed_lines:
        head_lower = tr_lower(head)
        if head in virtual_stem_heads or " (" in head:
            continue
        
        # 1. Purge known bad stems and bogus voiced virtual stems
        if head_lower in PURGE_VIRTUAL_STEMS or head_lower in ("felaked", "stoğ"):
            removed_bad_stems += 1
            continue
        if head in BAD_STEMS or (
            head_lower in BAD_STEMS
            and (
                head.islower()
                or head_lower in {
                    "ademci", "topyekun", "alemşümul", "alemşümullük",
                    "misakımilli", "misakımillî", "yahudi", "yahudice",
                    "yahudilik", "yahudiliğ", "yahudibaklası", "fata", "çe",
                    "müslüman", "müslümanca", "müslümanlık", "müslümanlığ",
                    "hristiyan", "hristiyanca", "hristiyanlık", "hristiyanlığ",
                    "hıristiyan", "hıristiyanlık", "hıristiyanlığ"
                }
            )
        ):
            removed_bad_stems += 1
            continue

        # 1b. In TDK profile, purge words unique to Dil Derneği
        if profile == "tdk" and head_lower in dd_words_to_purge:
            removed_dd_words += 1
            continue
        if profile == "dd" and head_lower in bilim_sanat_only_to_purge:
            continue
            
        # 2. Purge unhatted duplicates for mandatory hatted words
        if head in unhatted_to_purge or head_lower in unhatted_to_purge:
            removed_unhatted_dups += 1
            continue
            
        # 3. Whitelist check (protects all custom abbreviations, custom names, compound terms, TDK/DD)
        is_whitelisted = head_lower in whitelist or head in custom_abbrevs_orig or head in custom_names_orig or (head_lower in authority_all if profile != "tdk" else head_lower in tdk_words)
        
        if not is_whitelisted:
            # 1-3 letter permutation noise not in whitelist
            if len(head) <= 3 and head.isalpha():
                removed_permutations += 1
                continue
            # Chopped OCR fragments
            if head.isalpha() and RE_OCR_FRAGMENT.match(head_lower):
                removed_crawler_spam += 1
                continue
            # Crawler spam / repeated clusters
            if RE_REPEATED_CHARS.search(head) or RE_CONSONANT_CLUSTER.search(head_lower):
                removed_crawler_spam += 1
                continue
            if head.islower() and len(head) >= 4:
                if head_lower.startswith("aa") or head_lower.startswith("bb"):
                    removed_crawler_spam += 1
                    continue
                    
        # 4. Common noun vs proper noun compound separation
        is_compound_term = head_lower in COMPOUND_SET

        # Fast path: only partition flags if any PROPER_SUB_UTF8 flag character is present
        if any(c in PROPER_SUB_UTF8 for c in flags):
            proper_flags = "".join(c for c in flags if c in PROPER_SUB_UTF8)
            common_flags = "".join(c for c in flags if c not in PROPER_SUB_UTF8)
        else:
            proper_flags = ""
            common_flags = flags
        
        if head[0].isupper():
            # Check if this capitalized entry is legitimate:
            # - A custom name (e.g. Arc, AMD, HP, LG, Ahmet, İstanbul)
            # - A custom abbreviation (e.g. AA, ABD, ABS)
            # - A compound term (e.g. Dağ, Göl, Vadi, Ova, Köprü, Saray)
            # - Has KEEPCASE (KC) or proper noun flags
            is_legit_upper = (
                head in custom_names_orig
                or head_lower in custom_names
                or head in custom_abbrevs_orig
                or head_lower in custom_abbrevs
                or is_compound_term
                or (KC_FLAG and KC_FLAG in flags)
                or len(head) <= 4
                or bool(proper_flags)
            )
            # If it's merely a capitalized clone of a common noun (e.g. Abajur when abajur exists) with no proper flags -> Drop!
            if not is_legit_upper and head_lower in existing_lower_heads:
                removed_redundant_upper += 1
                continue

            # Architecture Enforcement: Proper Noun Inflection Contract
            # Proper nouns (e.g. Adana, Atatürk, Türkiye, Ahmet, Ali) CANNOT take un-apostrophed common case/possessive flags!
            is_proper = (
                bool(proper_flags)
                or head in custom_names_orig
                or head_lower in custom_names
                or head_lower in PURE_PROPER_NOUNS
            )
            if is_proper and not is_compound_term and head not in BRAND_FLAG_MAP:
                # Strip all un-apostrophed common case and possessive flags
                clean_fl = "".join(c for c in flags if c not in COMMON_CASE_CHARS)
                # Enforce KEEPCASE so lowercase typo like 'adana' is never accepted
                if KC_FLAG and KC_FLAG not in clean_fl:
                    clean_fl = KC_FLAG + clean_fl
                # Enforce proper apostrophe flags if missing
                if not any(c in PROPER_SUB_UTF8 for c in clean_fl):
                    last_v = ""
                    for ch in reversed(head):
                        if ch in "aıâouûeiîöüAIÂOUÛEİÎÖÜ":
                            last_v = tr_lower(ch)
                            break
                    if last_v in "aıâ":
                        clean_fl += PROPER_B
                    elif last_v in "ouû":
                        clean_fl += PROPER_O
                    elif last_v in "eiî":
                        clean_fl += PROPER_F
                    elif last_v in "öü":
                        clean_fl += PROPER_U
                flags = clean_fl
        else:
            # Lowercase entry:
            if head_lower in PURE_PROPER_NOUNS:
                # Pure proper nouns must NEVER exist in lowercase!
                removed_bad_stems += 1
                continue
            if is_compound_term:
                # Lowercase compound term (dağ, vadi, ova): gets ONLY common flags (no apostrophes!)
                flags = common_flags
                # Also ensure the Capitalized compound head exists with proper flags!
                cap_head = tr_title(head)
                if proper_flags and (cap_head, proper_flags) not in seen_heads:
                    seen_heads.add((cap_head, proper_flags))
                    clean_entries.append(f"{cap_head}/{proper_flags}")
            elif head in UNIT_FLAG_MAP:
                flags = UNIT_FLAG_MAP[head]
            elif head in custom_abbrevs_orig or head_lower in custom_abbrevs:
                # Keep abbreviation as-is
                pass
            elif head in custom_names_orig or head_lower in custom_names:
                # Keep name as-is
                pass
            else:
                # Ordinary common noun (elma, tornavida): strip all proper noun flags!
                if proper_flags:
                    cleaned_common_noun_flags += 1
                    flags = common_flags
                    
        # Morphological flag overrides for core stems:
        if head in UNIT_FLAG_MAP:
            flags = UNIT_FLAG_MAP[head]
        elif head in BRAND_FLAG_MAP:
            flags = BRAND_FLAG_MAP[head]
        elif len(head) >= 2 and head.isupper() and head.isalpha():
            flags = get_abbrev_flags(head)
        elif head in custom_abbrevs_orig and not head.islower():
            flags = "".join(sorted(set(flags + get_abbrev_flags(head))))
        elif head_lower in HEAD_FLAG_OVERRIDES and (head.islower() or head not in COMPOUND_SET):
            flags = HEAD_FLAG_OVERRIDES[head_lower]
        elif head_lower in PALATAL_L_HEADS:
            flags = PALATAL_L_FLAGS
        elif head_lower.endswith((" etmek", " gitmek")) or head_lower in ("kayetmek", "kayyetmek"):
            flags = LONG_TO_UTF8["VM"]
        elif head_lower.endswith(" tatmak"):
            flags = LONG_TO_UTF8["VK"]
        elif head_lower.endswith(" gütmek"):
            flags = LONG_TO_UTF8["VN"]
        elif not head_lower.endswith(("mak", "mek")) and "X" not in flags and any(c in flags for c in "≔≖≗≘≙≚≛≜≝≞≟≠≡"):
            # Rescue non-mak/mek nouns/adjectives that erroneously received verb flags
            if head_lower in {
                "aktı", "bakarak", "bakındı", "defol", "evlensek", "gebere", "görsün",
                "görürsün", "haçan", "hisset", "kıstı", "niceleyin", "ol", "sencileyin",
                "sevsinler", "seyret", "seç", "siktir", "sizcileyin", "sus", "sıyırdım",
                "yürü", "üçürdüm"
            }:
                flags = ""
            else:
                _lv = "a"
                for _ch in reversed(head_lower):
                    if _ch in "aeıioöuüâîû":
                        _lv = _ch
                        break
                if head_lower[-1] in "aeıioöuüâîû":
                    if _lv in "aıâ":
                        flags = B3_VOWEL_FLAGS
                    elif _lv in "ouû":
                        flags = B4_VOWEL_FLAGS
                    elif _lv in "eiî":
                        flags = F3_VOWEL_FLAGS
                    else:
                        flags = F4_VOWEL_FLAGS
                else:
                    if _lv in "aıâ":
                        flags = BACK_UNVOICED_FLAGS + (LONG_TO_UTF8["V1"] if head_lower.endswith("k") else "")
                    elif _lv in "ouû":
                        flags = BACK_ROUNDED_UNVOICED_FLAGS + (LONG_TO_UTF8["V2"] if head_lower.endswith("k") else "")
                    elif _lv in "eiî":
                        flags = FRONT_UNVOICED_FLAGS + (LONG_TO_UTF8["V3"] if head_lower.endswith("k") else "")
                    else:
                        flags = FRONT_ROUNDED_UNVOICED_FLAGS + (LONG_TO_UTF8["V4"] if head_lower.endswith("k") else "")
        
        # Inject vowel drop flags (D1, D2, D3, D4)
        if head_lower in VOWEL_DROP_D1_HEADS:
            d_flag = LONG_TO_UTF8.get("D1", "")
            if d_flag and d_flag not in flags:
                flags += d_flag
        elif head_lower in VOWEL_DROP_D2_HEADS:
            d_flag = LONG_TO_UTF8.get("D2", "")
            if d_flag and d_flag not in flags:
                flags += d_flag
        elif head_lower in VOWEL_DROP_D3_HEADS:
            d_flag = LONG_TO_UTF8.get("D3", "")
            if d_flag and d_flag not in flags:
                flags += d_flag
        elif head_lower in VOWEL_DROP_D4_HEADS:
            d_flag = LONG_TO_UTF8.get("D4", "")
            if d_flag and d_flag not in flags:
                flags += d_flag

        # Temporal relative -ki for sezon (sezonki, sezonkinin, sezonkiler)
        if head_lower == "sezon":
            k1_flag = LONG_TO_UTF8.get("K1", "")
            if k1_flag and k1_flag not in flags:
                flags += k1_flag

        # Loanwords ending in 'ing' must take front-vowel noun suffixes
        if head.lower().endswith("ing") and ("≑" in flags or not flags):
            flags = flags.replace("≑", "") + "∙∂≤∨≌∭∢≊∻≄∴∸∿≆≩∩∪≎∌∍≍" + (PROPER_F if not head.islower() else "")
            
        # For TDK profile: dual voicing stems (teleskop, bergamot, baç) take only consonant suffixes
        if profile == "tdk" and head_lower in (DUAL_VOICING_BACK_ROUNDED + DUAL_VOICING_BACK_UNROUNDED):
            consonant_flags = remap_flag_string("CI CK CL L1 LI LK PB Q1 R1 SL SZ".replace(" ", ""))
            flags = "".join(sorted(set(c for c in flags if c in consonant_flags)))
        elif profile == "tdk" and head_lower in DUAL_VOICING_G_BACK_ROUNDED:
            consonant_v2_flags = remap_flag_string("V2 CI CK CL L1 LI LK PB Q1 R1 SL SZ".replace(" ", ""))
            flags = "".join(sorted(set(c for c in flags if c in consonant_v2_flags)))
            
        if profile == "dd" and "î" in head:
            head_dd = head.replace("î", "i")
            if head_dd in BAD_STEMS:
                continue
            head = head_dd
            
        if profile == "universal" and "î" in head:
            head_unhatted = head.replace("î", "i")
            if head_unhatted not in BAD_STEMS:
                entry_unhatted = (head_unhatted, flags)
                if entry_unhatted not in seen_heads:
                    seen_heads.add(entry_unhatted)
                    clean_entries.append(f"{head_unhatted}/{flags}" if flags else head_unhatted)

        # Dil Derneği accepts unhatted forms for certain words like batıni, batıniye
        if head.lower() in ("bâtıni", "bâtıniye"):
            head_unhatted = head.replace("â", "a")
            if profile == "dd":
                head = head_unhatted
            elif profile == "universal":
                entry_unhatted = (head_unhatted, flags)
                if entry_unhatted not in seen_heads:
                    seen_heads.add(entry_unhatted)
                    clean_entries.append(f"{head_unhatted}/{flags}" if flags else head_unhatted)
                
        if len(head) == 1:
            flags = ""
        elif head_lower.endswith(("p", "ç", "t", "k")):
            if any(c in _B12_CHARS for c in flags) and _VC_CHAR not in flags:
                flags += _VC_CHAR
            if any(c in _F12_CHARS for c in flags) and _vc_CHAR not in flags:
                flags += _vc_CHAR
            
        if head == "boyn":
            flags = flags.replace("≕", "")
        elif head == "boyun":
            flags = flags.replace("∓", "")

        # Overgeneration hardening: prevent recursive chained pseudo-word derivations
        _strip_lik_flags = {LONG_TO_UTF8[f] for f in ("CI", "LCI", "LK", "LFK", "DL", "DT", "DE") if f in LONG_TO_UTF8}
        _strip_double_flags = {LONG_TO_UTF8[f] for f in ("LI", "LF", "SZ", "LSZ", "CK", "SL") if f in LONG_TO_UTF8}
        if head_lower.endswith(("lık", "lik", "luk", "lük")):
            flags = "".join(c for c in flags if c not in _strip_lik_flags)
            if head_lower.endswith((
                "cılık", "cilik", "culuk", "cülük",
                "çılık", "çilik", "çuluk", "çülük",
                "sızlık", "sizlik", "suzluk", "süzlük",
                "lılık", "lilik", "luluk", "lülük",
                "sallık", "sellik"
            )):
                flags = "".join(c for c in flags if c not in _strip_double_flags)
        elif head_lower.endswith(("lıklı", "likli", "luklu", "lüklü")):
            flags = "".join(c for c in flags if c not in _strip_lik_flags)
            
        entry_key = (head, flags)
        if entry_key in seen_heads:
            continue
        seen_heads.add(entry_key)
        clean_entries.append(f"{head}/{flags}" if flags else head)
        
    print(f"  Removed: {removed_permutations} permutation noises, {removed_crawler_spam} crawler spam, {removed_unhatted_dups} unhatted dups, {removed_bad_stems} bad stems.")
    print(f"  Pruned {removed_redundant_upper:,} redundant capitalized duplicates.")
    print(f"  Cleaned proper-noun apostrophe flags from {cleaned_common_noun_flags:,} ordinary common nouns.")
    
    # 5. Inject legitimate missed words & virtual stems & extra authority headwords
    added_legit = 0
    for w in LEGITIMATE_MISSED_WORDS:
        if profile == "dd" and "î" in w:
            w = w.replace("î", "i")
        head_w = w.split("/")[0]
        head_lower = tr_lower(head_w)
        if (head_w in unhatted_to_purge or head_lower in unhatted_to_purge) and not (head_w == "Misakımilli" and profile in ("universal", "dd")):
            continue
        fl_w = w.split("/")[1] if "/" in w else ""
        if head_w.lower() in HEAD_FLAG_OVERRIDES and not fl_w:
            fl_w = HEAD_FLAG_OVERRIDES[head_w.lower()]
        entry_w = f"{head_w}/{fl_w}" if fl_w else head_w
        if (head_w, "") not in seen_heads and (head_w.lower(), "") not in seen_heads:
            clean_entries.append(entry_w)
            seen_heads.add((head_w, ""))
            added_legit += 1
            
    for w in VIRTUAL_STEMS + EXTRA_AUTHORITY_HEADWORDS:
        head_w = w.split("/")[0]
        head_lower = tr_lower(head_w)
        if (head_w in unhatted_to_purge or head_lower in unhatted_to_purge) and not (head_w == "Misakımilli" and profile in ("universal", "dd")):
            continue
        if profile == "dd" and "î" in head_w:
            continue
        if "/" not in w and head_lower in HEAD_FLAG_OVERRIDES:
            clean_entries.append(f"{w}/{HEAD_FLAG_OVERRIDES[head_lower]}")
        else:
            clean_entries.append(w)
        seen_heads.add((head_w, ""))
        added_legit += 1
            
    # 5b. Inject Bilim ve Sanat Terimleri
    added_terimler = 0
    if profile in ("universal", "bilim-sanat", "tdk") and bilim_sanat_lexicon:
        for t_item in bilim_sanat_lexicon:
            w = t_item["lemma"]
            head_lower = tr_lower(w)
            if w in unhatted_to_purge or head_lower in unhatted_to_purge:
                continue
            if (w, "") in seen_heads or (head_lower, "") in seen_heads:
                continue
            attrs = t_item.get("attributes", [])
            pos = t_item.get("pos", "Noun")
            if head_lower in HEAD_FLAG_OVERRIDES:
                fl = HEAD_FLAG_OVERRIDES[head_lower]
            elif head_lower in PALATAL_L_HEADS or "InverseHarmony" in attrs:
                fl = PALATAL_L_FLAGS
            elif "CompoundP3sg" in attrs:
                if head_lower.endswith("ı"):
                    fl = "∀∈∌∍∎∖∗∘∡∧∩∪∫∲∶∺∼∽≂≉≋≍≎≣"
                elif head_lower.endswith("u"):
                    fl = "∁∉∌∍∎∖∗∘∡∧∩∪∬∳∷∺∾≁≃≉≋≍≎≣"
                elif head_lower.endswith("i"):
                    fl = "∂∊∌∍∖∗∘∢∨∩∪∭∴∸∻∿≄≆≊≌≍≎≤≩"
                elif head_lower.endswith("ü"):
                    fl = "∃∋∌∍∖∗∘∢∨∩∪∮∵∹∻≀≅≈≊≌≍≎≤≩"
                else:
                    fl = ""
            elif pos == "Verb" and head_lower.endswith(("mak", "mek")):
                fl = ""
            else:
                _lv = "a"
                for _ch in reversed(head_lower):
                    if _ch in "aeıioöuüâîû":
                        _lv = _ch
                        break
                if head_lower[-1] in "aeıioöuüâîû":
                    if _lv in "aıâ": fl = B3_VOWEL_FLAGS
                    elif _lv in "ouû": fl = B4_VOWEL_FLAGS
                    elif _lv in "eiî": fl = F3_VOWEL_FLAGS
                    else: fl = F4_VOWEL_FLAGS
                else:
                    has_voicing = "Voicing" in attrs or head_lower.endswith("k")
                    if _lv in "aıâ":
                        fl = BACK_UNVOICED_FLAGS + (LONG_TO_UTF8["V1"] if has_voicing else "")
                    elif _lv in "ouû":
                        fl = BACK_ROUNDED_UNVOICED_FLAGS + (LONG_TO_UTF8["V2"] if has_voicing else "")
                    elif _lv in "eiî":
                        fl = FRONT_UNVOICED_FLAGS + (LONG_TO_UTF8["V3"] if has_voicing else "")
                    else:
                        fl = FRONT_ROUNDED_UNVOICED_FLAGS + (LONG_TO_UTF8["V4"] if has_voicing else "")
            
            clean_entries.append(f"{w}/{fl}" if fl else w)
            seen_heads.add((w, ""))
            added_terimler += 1
        print(f"  Injected: {added_terimler:,} Bilim ve Sanat Terimleri lemmas into profile [{profile}].")

    # 6. Inject all missing custom abbreviations and names from lexicons
    added_abbrevs = 0
    for a in custom_abbrevs_orig:
        if (a, "") not in seen_heads:
            if (a.lower(), "") not in seen_heads or a != a.lower():
                fl_a = get_abbrev_flags(a)
                if not fl_a and a.lower() in HEAD_FLAG_OVERRIDES:
                    fl_a = HEAD_FLAG_OVERRIDES[a.lower()]
                clean_entries.append(f"{a}/{fl_a}" if fl_a else a)
                seen_heads.add((a, ""))
                added_abbrevs += 1
            
    lower_to_flags = {}
    for h, fl in parsed_lines:
        if h.islower() and h not in virtual_stem_heads and "X" not in fl:
            lower_to_flags[h] = fl

    added_names = 0
    for n in custom_names_orig:
        n_lower = tr_lower(n)
        if (n in unhatted_to_purge or n_lower in unhatted_to_purge) and not any(c in n for c in "âîû"):
            continue
        if (n, "") not in seen_heads and ((n.lower(), "") not in seen_heads or (n and (n[0].isupper() or any(c.isupper() for c in n)))):
            base_fl = lower_to_flags.get(n.lower(), "")
            # Assign harmonic proper noun apostrophe inflection flags for capitalized proper names
            if n in BRAND_FLAG_MAP:
                entry_n = f"{n}/{BRAND_FLAG_MAP[n]}"
            elif len(n) >= 2 and n.isupper() and n.isalpha():
                fl_n = get_abbrev_flags(n)
                entry_n = f"{n}/{fl_n}" if fl_n else n
            elif n.lower() in HEAD_FLAG_OVERRIDES:
                entry_n = f"{n}/{HEAD_FLAG_OVERRIDES[n.lower()]}"
            elif n and (n[0].isupper() or any(c.isupper() for c in n)) and not any(c in n for c in "0123456789."):
                last_vowel = ""
                for ch in reversed(n):
                    if ch in "aıâouûeiîöüAIÂOUÛEİÎÖÜ":
                        last_vowel = tr_lower(ch)
                        break
                if last_vowel in "aıâ":
                    proper_flags = remap_flag_string("CK CL pBN pBL pBR pBY pBA pBI pBP pBC".replace(" ", ""))
                elif last_vowel in "ouû":
                    proper_flags = remap_flag_string("CK CL pON pOL pOR pOY pOA pOI pOP pOC".replace(" ", ""))
                elif last_vowel in "eiî":
                    proper_flags = remap_flag_string("CK cl pFN pFL pFR pFY pFA pFI pFP pFC".replace(" ", ""))
                elif last_vowel in "öü":
                    proper_flags = remap_flag_string("CK cl pUN pUL pUR pUY pUA pUI pUP pUC".replace(" ", ""))
                else:
                    proper_flags = ""
                base_fl_clean = "".join(c for c in base_fl if c not in COMMON_CASE_CHARS)
                combined_fl = "".join(sorted(set(base_fl_clean + proper_flags + (KC_FLAG or ""))))
                entry_n = f"{n}/{combined_fl}" if combined_fl else n
            else:
                base_fl_clean = "".join(c for c in base_fl if c not in COMMON_CASE_CHARS)
                combined_fl = "".join(sorted(set(base_fl_clean + (KC_FLAG or ""))))
                entry_n = f"{n}/{combined_fl}" if combined_fl else n
            clean_entries.append(entry_n)
            seen_heads.add((n, ""))
            added_names += 1
            
    print(f"  Injected: {added_legit} legitimate missed words, {added_abbrevs} missing abbrevs, {added_names} missing names.")
    
    # 7. Deduplicate multi-line heads in .dic
    merged_heads = {}
    for entry in clean_entries:
        idx = entry.find("/")
        if idx != -1:
            h = entry[:idx]
            fl = entry[idx+1:]
        else:
            h = entry
            fl = ""
        if h not in merged_heads:
            merged_heads[h] = set(fl)
        else:
            merged_heads[h].update(fl)

    valid_dic_flags = (set(UTF8_TO_LONG.keys()) - DEAD_FLAG_CHARS - {
        LONG_TO_UTF8[f] for f in ('u1', 'u2', 'u3', 'u4', 'uC', 'uI', 'uL', 'uN', 'uP', 'uQ', 'uR', 'uY') if f in LONG_TO_UTF8
    }) | {'X', '∥', '∰'}
    deduped_entries = []
    for h in sorted(merged_heads.keys()):
        fl_set = merged_heads[h] & valid_dic_flags
        if h in ("co", "Co"):
            fl_set.discard("∍")
        fl_combined = "".join(sorted(fl_set))
        deduped_entries.append(f"{h}/{fl_combined}" if fl_combined else h)

    print(f"  Clean entries before dedup: {len(clean_entries):,} -> after dedup: {len(deduped_entries):,}")
    return deduped_entries

def compile_v06(deploy_profile="universal", compile_base=False, skip_tests=False):
    if compile_base:
        print("\n=======================================================")
        print("Compiling base dictionary and grammar rules...")
        print("=======================================================")
        import compile_hunspell
        compile_hunspell.compile_dictionary()
    tdk_words, dd_words, bilim_sanat_lexicon, bilim_sanat_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig = load_lexicons()
    base_lines = get_base_dic_lines()
    if compile_base:
        print("\nNormalizing base dictionary and affix rules through universal pipeline...")
        norm_aff = build_hardened_aff(profile="universal")
        with open(AFF_SRC, "w", encoding="utf-8") as f:
            f.write(norm_aff)
        base_lines = build_sanitized_dic(
            tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig,
            bilim_sanat_lexicon=bilim_sanat_lexicon, bilim_sanat_words=bilim_sanat_words,
            profile="universal", raw_lines=base_lines
        )
    
    profiles = ["tdk", "dd", "universal"]
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    for prof in profiles:
        print(f"\n=======================================================")
        print(f"Compiling Turkspell - Profile: [{prof.upper()}]")
        print(f"=======================================================")
        
        prof_dir = DIST_DIR / f"turkspell-{prof}"
        prof_dir.mkdir(parents=True, exist_ok=True)
        
        # Build aff
        aff_content = build_hardened_aff(profile=prof)
        aff_out = prof_dir / "tr.aff"
        with open(aff_out, "w", encoding="utf-8") as f:
            f.write(aff_content)
            
        # Build dic
        dic_entries = build_sanitized_dic(
            tdk_words, dd_words, custom_abbrevs, custom_abbrevs_orig, custom_names, custom_names_orig,
            bilim_sanat_lexicon=bilim_sanat_lexicon, bilim_sanat_words=bilim_sanat_words,
            profile=prof, raw_lines=base_lines
        )
        dic_out = prof_dir / "tr.dic"
        with open(dic_out, "w", encoding="utf-8") as f:
            f.write(f"{len(dic_entries)}\n")
            for entry in dic_entries:
                f.write(f"{entry}\n")
                
        print(f"Successfully compiled: {prof_dir / 'tr.aff'} and {prof_dir / 'tr.dic'}")
        
    def _copy_file(src, dst):
        try:
            shutil.copy2(src, dst)
        except OSError:
            with open(src, "rb") as f_in, open(dst, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

    # Deploy selected profile to repository root
    print(f"\nDeploying Turkspell ({deploy_profile.upper()}) to repository root ({TURKSPELL_DIR / 'tr.*'})...")
    _copy_file(DIST_DIR / f"turkspell-{deploy_profile}" / "tr.aff", TURKSPELL_DIR / "tr.aff")
    _copy_file(DIST_DIR / f"turkspell-{deploy_profile}" / "tr.dic", TURKSPELL_DIR / "tr.dic")
    
    # Deploy to Firefox addon
    addon_dict_dir = TURKSPELL_DIR / "firefox-addon" / "dictionaries"
    if addon_dict_dir.exists():
        _copy_file(DIST_DIR / f"turkspell-{deploy_profile}" / "tr.aff", addon_dict_dir / "tr.aff")
        _copy_file(DIST_DIR / f"turkspell-{deploy_profile}" / "tr.dic", addon_dict_dir / "tr.dic")
        
    addon_tdk_dict_dir = TURKSPELL_DIR / "firefox-addon-tdk" / "dictionaries"
    if addon_tdk_dict_dir.exists():
        _copy_file(DIST_DIR / "turkspell-tdk" / "tr.aff", addon_tdk_dict_dir / "tr.aff")
        _copy_file(DIST_DIR / "turkspell-tdk" / "tr.dic", addon_tdk_dict_dir / "tr.dic")
        
    print("Deployment complete!")
    print("\nValidating all profile dictionaries and deployed root dictionary...")
    from validate_build import validate
    all_errors, all_warnings = [], []
    for prof in profiles:
        p_dic = str(DIST_DIR / f"turkspell-{prof}" / "tr.dic")
        p_aff = str(DIST_DIR / f"turkspell-{prof}" / "tr.aff")
        p_errs, p_warns = validate(p_dic, p_aff, verbose=False, run_tests=False)
        all_errors.extend(f"[{prof}] {e}" for e in p_errs)
        all_warnings.extend(f"[{prof}] {w}" for w in p_warns)
    errors, warnings = validate(
        str(TURKSPELL_DIR / "tr.dic"),
        str(TURKSPELL_DIR / "tr.aff"),
        run_tests=not skip_tests,
    )
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    for w in all_warnings:
        print(f"  WARNING: {w}")
    for e in all_errors:
        print(f"  ERROR:   {e}")
    if all_errors:
        raise SystemExit(f"\nDictionary validation failed: {len(all_errors)} error(s).")
    print(f"Validation passed ({len(all_warnings)} warning(s)).")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compile Turkspell Hunspell dictionaries")
    parser.add_argument(
        "--compile-base",
        action="store_true",
        help="Regenerate base tr.dic and tr.aff from source lexicons using build/compile_hunspell.py first"
    )
    parser.add_argument(
        "--deploy-profile",
        default=os.environ.get("TURKSPELL_PROFILE", "universal"),
        choices=["tdk", "universal", "dd"],
        help="Profile to deploy to repo root and firefox-addon (default: universal)"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running the full morphological regression test suite during post-build validation"
    )
    args = parser.parse_args()
    compile_v06(deploy_profile=args.deploy_profile, compile_base=args.compile_base, skip_tests=args.skip_tests)
