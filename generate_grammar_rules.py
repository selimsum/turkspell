"""
generate_grammar_rules.py — Dynamic Chained Flags Architecture
==============================================================

Generates a compact tr.aff using FLAG long (2-char alphanumeric flags).
Each morphological layer has its own small flag. Dictionary entries chain
multiple flags to cover all valid forms.

Architecture:
  Stem-class flags (B1, F1, V1, ...) — handle phonological alternations only
  Case flags      (AC, DA, LO, AB, GE, IN, EQ) — singular cases
  Plural flags    (PB, PF) — plural + all plural cases
  Possessive flags (P1-P6, Q1-Q6) — possessives + their cases
  Copula flag     (CL) — all nominal copula forms
  Relative-ki     (KI) — -ki and its inflections
  Derivation      (LI, SZ, LK, CI, CK) — 1st-level derivation
  2nd-level deriv (DL, DT, DE) — verb-forming derivations + re-nominalization
  Verb flags      (VB, VR, VF, VG, VA, VS, VE, VH, VK, VL, VM_v, VN, VY) — full verb paradigms
  Prefix flag     (PX) — metric/loan prefixes

Estimated output: ~8,000 rules (vs 775,000 in v1)
"""

import os

# ---------------------------------------------------------------------------
# Vowel Harmony Simulator (reused from v1 — identical)
# ---------------------------------------------------------------------------

UNVOICED = set('pçtksşhf')
VOWELS   = set('aeıioöuüâîû')

def get_last_vowel(s: str) -> str:
    for ch in reversed(s):
        if ch in VOWELS:
            return ch.lower()
    return 'a'

def get_last_char(s: str) -> str:
    return s[-1] if s else ''

def harmonize(stem: str, template: str) -> str:
    """Apply template to stem, resolving A/I/U/D/C placeholders."""
    res = list(stem)
    for i, char in enumerate(template):
        lv = get_last_vowel(''.join(res))
        lc = res[-1] if res else ''

        if char in 'AIU' and lc in VOWELS:
            is_pres_cont = (char == 'I' and template[i:i+4] == 'Iyor')
            if not is_pres_cont:
                res.append('y')
                lc = 'y'

        if char == 'A':
            res.append('a' if lv in 'aıouâû' else 'e')
        elif char == 'I':
            if lv in 'aıâ':     res.append('ı')
            elif lv in 'eiî':   res.append('i')
            elif lv in 'ouû':   res.append('u')
            else:               res.append('ü')
        elif char == 'U':
            res.append('u' if lv in 'aıouâû' else 'ü')
        elif char == 'D':
            res.append('t' if lc in UNVOICED else 'd')
        elif char == 'C':
            res.append('ç' if lc in UNVOICED else 'c')
        else:
            res.append(char)

    return ''.join(res)[len(stem):]

def unique(seq):
    seen = set()
    result = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

def make_flag_block(flag: str, rules: list[str]) -> str:
    unique_rules = unique(rules)
    header = f"SFX {flag} Y {len(unique_rules)}"
    return header + '\n' + '\n'.join(unique_rules)

UNVOICED_RE = "[çfhkpsşt]"
VOICED_RE   = "[^çfhkpsşt]"
VOWEL_RE    = "[aeıioöuü]"
CONS_RE     = "[^aeıioöuü]"

def sfx(flag: str, strip: str, add: str, condition: str) -> str:
    return f"SFX {flag} {strip} {add} {condition}"

def sfx_copula(flag: str, strip: str, add: str, cond: str, rules: list):
    lv = None
    for c in reversed(add):
        if c in 'aeıioöuüâîû':
            lv = c.lower()
            break
    if not lv:
        rules.append(sfx(flag, strip, add, cond))
        return
        
    is_vowel = add[-1] in 'aeıioöuüâîû'
    if lv in 'aı':
        sim_stem = "oda" if is_vowel else "bak"
    elif lv in 'ei':
        sim_stem = "kedi" if is_vowel else "ev"
    elif lv in 'ou':
        sim_stem = "kutu" if is_vowel else "uç"
    else:
        sim_stem = "ütü" if is_vowel else "gör"

    
    if is_vowel:
        copulas = [
            "ydI", "ydIm", "ydIn", "ydIk", "ydInIz", "ydIlAr",
            "ymIş", "ymIşIm", "ymIşsIn", "ymIşIz", "ymIşsInIz", "ymIşlAr",
            "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr",
            "yIm", "sIn", "yIz", "sInIz", "lAr",
            "dIr", "dIrlAr", "lArdIr", "yken",
            "yImdIr", "sIndIr", "yIzdIr", "sInIzdIr",
        ]
    else:
        copulas = [
            "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
            "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
            "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
            "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
            "Im", "sIn", "Iz", "sInIz", "lAr",
            "dIr", "tIr", "dIrlAr", "tIrlAr", "lArdIr", "ken",
            "ImdIr", "sIndIr", "IzdIr", "sInIzdIr",
        ]
        
    rules.append(sfx(flag, strip, add, cond))
    for cop in copulas:
        resolved = harmonize(sim_stem, cop)
        if resolved:
            rules.append(sfx(flag, strip, add + resolved, cond))

def sfx_ki(flag: str, strip: str, add: str, cond: str, rules: list, chain_copula: bool = True):
    if chain_copula:
        sfx_copula(flag, strip, add, cond, rules)
    else:
        rules.append(sfx(flag, strip, add, cond))
    is_loc = any(add.endswith(x) for x in ['da', 'de', 'ta', 'te', 'nda', 'nde'])
    is_gen = any(add.endswith(x) for x in ['ın', 'in', 'un', 'ün', 'nın', 'nin', 'nun', 'nün'])
    ki_suffixes = [
        'ki', 'kiler', 'kilerin', 'kilere', 'kilerde', 'kilerden', 'kilerle', 'kilerce',
        'kileri', 'kilerini', 'kilerine', 'kilerinde', 'kilerinden', 'kileriyle', 'kilerinin',
        'kini', 'kine', 'kinde', 'kinden', 'kinin', 'kiyle', 'kiyse', 'kidir', 'kiydi', 'kiymiş', 'kiyken'
    ]
    for ks in ki_suffixes:
        rules.append(sfx(flag, strip, add + ks, cond))

def get_noun_chain(stem_flag: str) -> str:
    if stem_flag in ("PX", "NX"):
        return stem_flag
    back_flags = {"B1", "B2", "V1", "V2", "D1", "D2", "C1", "C2", "G1", "G2"}  # back cons
    back_vowel_flags = {"B3", "B4"}                                               # back vowel-end
    front_flags = {"F1", "F2", "V3", "V4", "D3", "D4", "C3", "C4", "G3", "G4"} # front cons
    front_vowel_flags = {"F3", "F4"}                                              # front vowel-end
    rounded_flags = {"B2", "V2", "D2", "C2", "G2", "B4", "F2", "V4", "D4", "C4", "G4", "F4"}
    
    is_back = stem_flag in back_flags | back_vowel_flags
    is_front = stem_flag in front_flags | front_vowel_flags
    is_rounded = stem_flag in rounded_flags
    is_vowel = stem_flag in back_vowel_flags | front_vowel_flags

    def adjust_flag(base: str) -> str:
        return base.lower() if is_vowel else base

    if is_back and not is_rounded:     acc_f = adjust_flag("A1")
    elif is_back and is_rounded:       acc_f = adjust_flag("A2")
    elif is_front and not is_rounded:  acc_f = adjust_flag("A3")
    else:                              acc_f = adjust_flag("A4")

    dat_f = adjust_flag("Y1") if is_back else adjust_flag("Y2")
    loc_f = "L1" if is_back else "L2"
    abl_f = "R1" if is_back else "R2"

    if is_back and not is_rounded:     gen_f = adjust_flag("N1")
    elif is_back and is_rounded:       gen_f = adjust_flag("N2")
    elif is_front and not is_rounded:  gen_f = adjust_flag("N3")
    else:                              gen_f = adjust_flag("N4")

    ins_f = adjust_flag("I1") if is_back else adjust_flag("I2")
    eq_f  = "Q1" if is_back else "Q2"

    plural = "PB" if is_back else "PF"

    if is_back and not is_rounded:     p3 = "PS"
    elif is_back and is_rounded:       p3 = "PT"
    elif is_front and not is_rounded:  p3 = "PU"
    else:                              p3 = "PV"

    if is_back and not is_rounded:     p1 = "P1"
    elif is_back and is_rounded:       p1 = "P2"
    elif is_front and not is_rounded:  p1 = "P3"
    else:                              p1 = "P4"

    if is_back and not is_rounded:     p2s = "P5"
    elif is_back and is_rounded:       p2s = "P6"
    elif is_front and not is_rounded:  p2s = "P7"
    else:                              p2s = "P8"

    if is_back and not is_rounded:     p1pl = "PM"
    elif is_back and is_rounded:       p1pl = "PO"
    elif is_front and not is_rounded:  p1pl = "PP"
    else:                              p1pl = "PQ"

    if is_back and not is_rounded:     p2pl = "PN"
    elif is_back and is_rounded:       p2pl = "PR"
    elif is_front and not is_rounded:  p2pl = "PW"
    else:                              p2pl = "PZ"

    exclude_vowel = stem_flag[0] in ("V", "D", "G")
    if exclude_vowel:
        cases = f"{loc_f}{abl_f}{ins_f}{eq_f}"
        possessives = ""
    else:
        cases = f"{acc_f}{dat_f}{loc_f}{abl_f}{gen_f}{ins_f}{eq_f}"
        possessives = f"{p3}{p1}{p2s}{p1pl}{p2pl}"

    copula_flag = "CL" if is_back else "cl"

    return f"{stem_flag}{cases}{plural}{possessives}{copula_flag}LILKSZCIDLDTDE"


def get_vowel_chain(stem_flag: str) -> str:
    back_flags = {"B1", "B2", "V1", "V2", "D1", "D2", "C1", "C2", "G1", "G2"}
    back_vowel_flags = {"B3", "B4"}
    is_back = stem_flag in back_flags | back_vowel_flags
    rounded_flags = {"B2", "V2", "D2", "C2", "G2", "B4", "F2", "V4", "D4", "C4", "G4", "F4"}
    is_rounded = stem_flag in rounded_flags

    # Alternant stems end in a consonant (e.g. kitab-), so they take consonant case flags (uppercase)
    if is_back and not is_rounded:     acc_f = "A1"
    elif is_back and is_rounded:       acc_f = "A2"
    elif not is_back and not is_rounded: acc_f = "A3"
    else:                              acc_f = "A4"

    dat_f = "Y1" if is_back else "Y2"

    if is_back and not is_rounded:     gen_f = "N1"
    elif is_back and is_rounded:       gen_f = "N2"
    elif not is_back and not is_rounded: gen_f = "N3"
    else:                              gen_f = "N4"

    if is_back and not is_rounded:     p3, p1, p2s, p1pl, p2pl = "PS", "P1", "P5", "PM", "PN"
    elif is_back and is_rounded:       p3, p1, p2s, p1pl, p2pl = "PT", "P2", "P6", "PO", "PR"
    elif not is_back and not is_rounded: p3, p1, p2s, p1pl, p2pl = "PU", "P3", "P7", "PP", "PW"
    else:                              p3, p1, p2s, p1pl, p2pl = "PV", "P4", "P8", "PQ", "PZ"

    return f"{acc_f}{dat_f}{gen_f}{p3}{p1}{p2s}{p1pl}{p2pl}"

def gen_stem_flag(flag: str) -> str:
    """Slim stem-class flag. Handles bare stem validation and voicing/dropping/doubling."""
    rules = []
    rules.append(sfx(flag, "0", "0", "."))
    if flag in ("V1", "V2", "V3", "V4"):
        vowel_chain = get_vowel_chain(flag)
        voicing_pairs = [('p', 'b'), ('ç', 'c'), ('t', 'd'), ('k', 'ğ'), ('g', 'ğ')]
        for unv, vc in voicing_pairs:
            rules.append(sfx(flag, unv, f"{vc}/{vowel_chain}", f"{unv}"))
    elif flag in ("D1", "D2", "D3", "D4"):
        vowel_chain = get_vowel_chain(flag)
        is_back = flag in ("D1", "D2")
        if is_back:
            endings = ['ıl', 'ım', 'ın', 'ır', 'ıs', 'ız', 'ul', 'um', 'un', 'ur', 'us', 'uz', 'ıf', 'ıh', 'ık', 'ıp', 'ıt', 'uf', 'uh', 'uk', 'up', 'ut', 'uv']
        else:
            endings = ['il', 'im', 'in', 'iş', 'ir', 'is', 'iz', 'ül', 'üm', 'ün', 'ür', 'üs', 'üz', 'if', 'ih', 'ik', 'ip', 'it', 'üf', 'üh', 'ük', 'üp', 'üt', 'üv']
        voicing_map = {'p': 'b', 'ç': 'c', 't': 'd', 'k': 'ğ'}
        for end in endings:
            strip_suffix = end
            add_char = end[1]
            if add_char in voicing_map:
                voiced_char = voicing_map[add_char]
                rules.append(sfx(flag, strip_suffix, f"{voiced_char}/{vowel_chain}", f"{strip_suffix}"))
            else:
                rules.append(sfx(flag, strip_suffix, f"{add_char}/{vowel_chain}", f"{strip_suffix}"))
    elif flag in ("G1", "G2", "G3", "G4"):
        vowel_chain = get_vowel_chain(flag)
        doubling_pairs = [
            ('p', 'bb'), ('t', 'dd'), ('k', 'kk'), ('s', 'ss'), ('z', 'zz'),
            ('l', 'll'), ('n', 'nn'), ('r', 'rr'), ('m', 'mm'), ('c', 'cc'),
            ('f', 'ff'), ('b', 'bb')
        ]
        for unv, double_char in doubling_pairs:
            rules.append(sfx(flag, unv, f"{double_char}/{vowel_chain}", f"{unv}"))
    elif flag in ("C1", "C2", "C3", "C4"):
        # Compound nouns ending in possessive suffix.
        is_back = flag in ("C1", "C2")
        is_rounded = flag in ("C2", "C4")
        
        # Determine the vowel of the stem to strip for plural (ı, u, i, ü)
        if flag == "C1":   strip_v = "ı"
        elif flag == "C2": strip_v = "u"
        elif flag == "C3": strip_v = "i"
        else:              strip_v = "ü"
        
        # Harmony variables
        pl = "ları" if is_back else "leri"
        acc = "ı" if is_back and not is_rounded else ("u" if is_back and is_rounded else ("i" if not is_back and not is_rounded else "ü"))
        loc = "a" if is_back else "e"
        
        # 1. Suffixes that strip the final vowel (Plural and its cases/possessives)
        plural_suffixes = [
            pl,
            f"{pl}n{acc}",
            f"{pl}n{loc}",
            f"{pl}nd{loc}",
            f"{pl}nd{loc}n",
            f"{pl}n{acc}n",
            f"{pl}yl{loc}",
            f"{pl}nc{loc}",
        ]
        for s in plural_suffixes:
            rules.append(sfx(flag, strip_v, s, strip_v))
            # Support relative-ki on plural locative and genitive
            if s.endswith(f"nd{loc}") or s.endswith(f"n{acc}n"):
                sfx_ki(flag, strip_v, s + "ki", strip_v, rules, chain_copula=True)
                
        # 2. Suffixes that keep the final vowel (Singular cases/possessives with pronominal n/y buffer)
        singular_suffixes = [
            f"n{acc}",
            f"n{loc}",
            f"nd{loc}",
            f"nd{loc}n",
            f"n{acc}n",
            f"yla" if is_back else "yle",  # y-buffer for instrumental
            f"nca" if is_back else "nce",  # n-buffer for equative
        ]
        for s in singular_suffixes:
            rules.append(sfx(flag, "0", s, "."))
            # Support relative-ki on singular locative and genitive
            if s.endswith(f"nd{loc}") or s.endswith(f"n{acc}n"):
                sfx_ki(flag, "0", s + "ki", ".", rules, chain_copula=True)
    return make_flag_block(flag, unique(rules))


# ---------------------------------------------------------------------------
# SECTION 2: Case flags (singular, all stem classes)
# ---------------------------------------------------------------------------

def gen_ac_flags() -> list[str]:
    """Accusative flags: A1-A4 (consonant) and a1-a4 (vowel)"""
    blocks = []
    # Consonant-ending
    blocks.append(make_flag_block("A1", [sfx("A1", "0", "ı", ".")]))
    blocks.append(make_flag_block("A2", [sfx("A2", "0", "u", ".")]))
    blocks.append(make_flag_block("A3", [sfx("A3", "0", "i", ".")]))
    blocks.append(make_flag_block("A4", [sfx("A4", "0", "ü", ".")]))
    # Vowel-ending
    blocks.append(make_flag_block("a1", [sfx("a1", "0", "yı", ".")]))
    blocks.append(make_flag_block("a2", [sfx("a2", "0", "yu", ".")]))
    blocks.append(make_flag_block("a3", [sfx("a3", "0", "yi", ".")]))
    blocks.append(make_flag_block("a4", [sfx("a4", "0", "yü", ".")]))
    return blocks

def gen_da_flags() -> list[str]:
    """Dative flags: Y1/Y2 (consonant) and y1/y2 (vowel)"""
    blocks = []
    blocks.append(make_flag_block("Y1", [sfx("Y1", "0", "a", ".")]))
    blocks.append(make_flag_block("Y2", [sfx("Y2", "0", "e", ".")]))
    blocks.append(make_flag_block("y1", [sfx("y1", "0", "ya", ".")]))
    blocks.append(make_flag_block("y2", [sfx("y2", "0", "ye", ".")]))
    return blocks

def gen_lo_flags() -> list[str]:
    """Locative flags: L1 (back), L2 (front)"""
    blocks = []
    # L1
    rules = []
    sfx_ki("L1", "0", "da", "[^çfhkpsşt]", rules)
    sfx_ki("L1", "0", "ta", "[çfhkpsşt]", rules)
    blocks.append(make_flag_block("L1", unique(rules)))
    # L2
    rules = []
    sfx_ki("L2", "0", "de", "[^çfhkpsşt]", rules)
    sfx_ki("L2", "0", "te", "[çfhkpsşt]", rules)
    blocks.append(make_flag_block("L2", unique(rules)))
    return blocks

def gen_ab_flags() -> list[str]:
    """Ablative flags: R1 (back), R2 (front)"""
    blocks = []
    # R1
    rules = []
    sfx_copula("R1", "0", "dan", "[^çfhkpsşt]", rules)
    sfx_copula("R1", "0", "tan", "[çfhkpsşt]", rules)
    blocks.append(make_flag_block("R1", unique(rules)))
    # R2
    rules = []
    sfx_copula("R2", "0", "den", "[^çfhkpsşt]", rules)
    sfx_copula("R2", "0", "ten", "[çfhkpsşt]", rules)
    blocks.append(make_flag_block("R2", unique(rules)))
    return blocks

def gen_ge_flags() -> list[str]:
    """Genitive flags: N1-N4 (consonant) and n1-n4 (vowel)"""
    blocks = []
    # Consonant-ending
    rules = []; sfx_ki("N1", "0", "ın", ".", rules); blocks.append(make_flag_block("N1", unique(rules)))
    rules = []; sfx_ki("N2", "0", "un", ".", rules); blocks.append(make_flag_block("N2", unique(rules)))
    rules = []; sfx_ki("N3", "0", "in", ".", rules); blocks.append(make_flag_block("N3", unique(rules)))
    rules = []; sfx_ki("N4", "0", "ün", ".", rules); blocks.append(make_flag_block("N4", unique(rules)))
    # Vowel-ending
    rules = []; sfx_ki("n1", "0", "nın", ".", rules); blocks.append(make_flag_block("n1", unique(rules)))
    rules = []; sfx_ki("n2", "0", "nun", ".", rules); blocks.append(make_flag_block("n2", unique(rules)))
    rules = []; sfx_ki("n3", "0", "nin", ".", rules); blocks.append(make_flag_block("n3", unique(rules)))
    rules = []; sfx_ki("n4", "0", "nün", ".", rules); blocks.append(make_flag_block("n4", unique(rules)))
    return blocks

def gen_in_flags() -> list[str]:
    """Instrumental flags: I1/I2 (consonant) and i1/i2 (vowel)"""
    blocks = []
    rules_i1 = []; sfx_copula("I1", "0", "la", ".", rules_i1); blocks.append(make_flag_block("I1", unique(rules_i1)))
    rules_i2 = []; sfx_copula("I2", "0", "le", ".", rules_i2); blocks.append(make_flag_block("I2", unique(rules_i2)))
    rules_i1_v = []; sfx_copula("i1", "0", "yla", ".", rules_i1_v); blocks.append(make_flag_block("i1", unique(rules_i1_v)))
    rules_i2_v = []; sfx_copula("i2", "0", "yle", ".", rules_i2_v); blocks.append(make_flag_block("i2", unique(rules_i2_v)))
    return blocks

def gen_eq_flags() -> list[str]:
    """Equative flags: Q1 (back), Q2 (front)"""
    blocks = []
    # Q1
    rules = []
    sfx_copula("Q1", "0", "ca", "[^çfhkpsşt]", rules)
    sfx_copula("Q1", "0", "ça", "[çfhkpsşt]", rules)
    blocks.append(make_flag_block("Q1", unique(rules)))
    # Q2
    rules = []
    sfx_copula("Q2", "0", "ce", "[^çfhkpsşt]", rules)
    sfx_copula("Q2", "0", "çe", "[çfhkpsşt]", rules)
    blocks.append(make_flag_block("Q2", unique(rules)))
    return blocks


# ---------------------------------------------------------------------------
# SECTION 3: Plural flags
# ---------------------------------------------------------------------------

def _plural_cases(pl_vowel: str, harmony: str) -> list[str]:
    """
    Return ALL suffixes that can follow a plural -lar/-ler stem.
    harmony: 'back' or 'front'
    pl_vowel: 'a' (back) or 'e' (front)
    """
    # Plural base: 'lar' for back, 'ler' for front
    pl = 'lar' if harmony == 'back' else 'ler'
    acc_v  = 'ı' if harmony == 'back' else 'i'
    dat_v  = 'a' if harmony == 'back' else 'e'
    gen_v  = 'ın' if harmony == 'back' else 'in'
    ins_v  = 'a' if harmony == 'back' else 'e'
    eq_v   = 'ca' if harmony == 'back' else 'ce'
    cop_d  = 'dır' if harmony == 'back' else 'dir'
    cop_di = 'dı' if harmony == 'back' else 'di'
    cop_m  = 'mış' if harmony == 'back' else 'miş'
    cop_sa = 'sa' if harmony == 'back' else 'se'
    cop_flag = "CL" if harmony == 'back' else "CP"
    
    suffixes = [
        # accusative
        f"{pl}{acc_v}",
        # dative
        f"{pl}{dat_v}",
        # locative
        f"{pl}d{dat_v}",
        # ablative
        f"{pl}d{dat_v}n",
        # genitive
        f"{pl}{gen_v}",
        # instrumental
        f"{pl}l{dat_v}",
        # equative
        f"{pl}{eq_v}",
        # copula present
        f"{pl}{cop_d}",
        # copula past
        f"{pl}{cop_di}",
        # copula narrative
        f"{pl}{cop_m}",
        # copula conditional
        f"{pl}{cop_sa}",
        # -ken
        f"{pl}ken",
    ]
    
    # 3sg/3pl possessive of plural cases (with pre-combined copulas)
    poss_cases = [
        f"{pl}{acc_v}",           # ları/leri (bare possessive)
        f"{pl}{acc_v}yl{dat_v}",  # larıyla/leriyle
        f"{pl}n{eq_v}",           # larınca/lerince
        f"{pl}n{acc_v}n",         # larının/lerinin
    ]
    for pc in poss_cases:
        suffixes.append(pc)
        is_vow = pc[-1] in 'aeıioöuü'
        sim_s = "oda" if harmony == 'back' else "ev"
        copulas = [
            "ydI", "ydIm", "ydIn", "ydIk", "ydInIz", "ydIlAr",
            "ymIş", "ymIşIm", "ymIşsIn", "ymIşIz", "ymIşsInIz", "ymIşlAr",
            "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr",
            "yIm", "sIn", "yIz", "sInIz", "lAr",
            "dIr", "dIrlAr", "lArdIr", "yken",
            "yImdIr", "sIndIr", "yIzdIr", "sInIzdIr",
        ] if is_vow else [
            "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
            "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
            "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
            "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
            "Im", "sIn", "Iz", "sInIz", "lAr",
            "dIr", "tIr", "dIrlAr", "tIrlAr", "lArdIr", "ken",
            "ImdIr", "sIndIr", "IzdIr", "sInIzdIr",
        ]
        for cop in copulas:
            resolved = harmonize(sim_s, cop)
            if resolved:
                suffixes.append(pc + resolved)
    # Also relative-ki on genitive and locative
    gen_form = f"{pl}{gen_v}"
    loc_form = f"{pl}d{dat_v}"
    suffixes.append(gen_form + 'ki')
    suffixes.append(loc_form + 'ki')
    for ks in ['ler', 'leri', 'lere', 'lerde', 'lerden', 'ni', 'ne', 'nde', 'nden', 'nin', 'dir', 'ydi']:
        suffixes.append(gen_form + 'ki' + ks)
        suffixes.append(loc_form + 'ki' + ks)
    return suffixes


def gen_plural_back(flag: str = "PB") -> str:
    """Back plural: -lar + all plural case forms"""
    rules = []
    rules.append(sfx(flag, "0", "lar", "."))  # base plural
    for sfx_str in _plural_cases('a', 'back'):
        rules.append(sfx(flag, "0", sfx_str, "."))
    # 1sg/2sg/1pl/2pl possessive of plural (back harmony)
    for poss, acc_v, cases in [
        ("larım",   "ı", ["", "ı", "a", "da", "dan", "ın", "la", "ca"]),
        ("ların",   "ı", ["", "ı", "a", "da", "dan", "ın", "la", "ca"]),
        ("larımız", "ı", ["", "ı", "a", "da", "dan", "ın", "la", "ca"]),
        ("larınız", "ı", ["", "ı", "a", "da", "dan", "ın", "la", "ca"]),
    ]:
        for c in cases:
            if c in ("da", "ın"):
                sfx_ki(flag, "0", poss + c, ".", rules)
            elif c in ("", "dan", "la"):
                sfx_copula(flag, "0", poss + c, ".", rules)
            else:
                rules.append(sfx(flag, "0", poss + c, "."))
    return make_flag_block(flag, unique(rules))


def gen_plural_front(flag: str = "PF") -> str:
    """Front plural: -ler + all plural case forms"""
    rules = []
    rules.append(sfx(flag, "0", "ler", "."))  # base plural
    for sfx_str in _plural_cases('e', 'front'):
        rules.append(sfx(flag, "0", sfx_str, "."))
    # 1sg/2sg/1pl/2pl possessive of plural (front harmony)
    for poss, cases in [
        ("lerim",   ["", "i", "e", "de", "den", "in", "le", "ce"]),
        ("lerin",   ["", "i", "e", "de", "den", "in", "le", "ce"]),
        ("lerimiz", ["", "i", "e", "de", "den", "in", "le", "ce"]),
        ("leriniz", ["", "i", "e", "de", "den", "in", "le", "ce"]),
    ]:
        for c in cases:
            if c in ("de", "in"):
                sfx_ki(flag, "0", poss + c, ".", rules)
            elif c in ("", "den", "le"):
                sfx_copula(flag, "0", poss + c, ".", rules)
            else:
                rules.append(sfx(flag, "0", poss + c, "."))
    return make_flag_block(flag, unique(rules))


# ---------------------------------------------------------------------------
# SECTION 4: Possessive flags
# ---------------------------------------------------------------------------

def gen_all_possessive_flags() -> list[str]:
    """Generate all 1sg possessive flags (P1-P4)."""
    blocks = []
    for flag, back, rounded in [
        ("P1", True, False),   # back unrounded: -ım
        ("P2", True, True),    # back rounded:   -um
        ("P3", False, False),  # front unrounded: -im
        ("P4", False, True),   # front rounded:   -üm
    ]:
        sg = "um" if rounded and back else ("üm" if rounded else ("ım" if back else "im"))
        m  = "m"
        loc = "a" if back else "e"
        acc = "ı" if back and not rounded else ("u" if rounded and back else ("i" if not back and not rounded else "ü"))
        abl = loc + "n"
        gen_s = acc + "n"
        ins = loc
        cop_flag = "CL" if back else "CP"

        eq_v = "ca" if back else "ce"
        rules = []
        for base_poss, after_vowel in [(sg, False), (m, True)]:
            cond = VOWEL_RE if after_vowel else CONS_RE
            sfx_copula(flag, "0", base_poss, cond, rules)
            rules.append(sfx(flag, "0", base_poss + acc,       cond))
            rules.append(sfx(flag, "0", base_poss + loc,       cond))
            sfx_ki(flag, "0", base_poss + "d" + loc,           cond, rules)
            sfx_copula(flag, "0", base_poss + "d" + loc + "n", cond, rules)
            sfx_ki(flag, "0", base_poss + gen_s,               cond, rules)
            sfx_copula(flag, "0", base_poss + "l" + loc,       cond, rules)
            rules.append(sfx(flag, "0", base_poss + eq_v,      cond))
        blocks.append(make_flag_block(flag, unique(rules)))
    return blocks


def gen_3sg_poss_flags() -> list[str]:
    """3sg possessive -I/-sI for all 4 harmony classes."""
    blocks = []
    for flag, back, rounded in [
        ("PS", True, False),   # back unrounded: -ı/-sı
        ("PT", True, True),    # back rounded:   -u/-su
        ("PU", False, False),  # front unrounded: -i/-si
        ("PV", False, True),   # front rounded:   -ü/-sü
    ]:
        acc_v = "ı" if back and not rounded else ("u" if rounded and back else ("i" if not back and not rounded else "ü"))
        loc_v = "a" if back else "e"

        rules = []
        # After consonant: just -[vowel]
        sfx_copula(flag, "0", acc_v,            f"[^aeıioöuü]", rules)
        # After vowel: -s[vowel] (buffer s)
        sfx_copula(flag, "0", f"s{acc_v}",          f"[aeıioöuü]", rules)

        # Cases after poss (n-buffer before all cases)
        # 1. Consonant ending stems (condition: [^aeıioöuü])
        rules.append(sfx(flag, "0", acc_v + "n" + acc_v,         "[^aeıioöuü]")) # acc
        rules.append(sfx(flag, "0", acc_v + "n" + loc_v,         "[^aeıioöuü]")) # dat
        sfx_ki(flag, "0", acc_v + "nd" + loc_v,        "[^aeıioöuü]", rules)      # loc
        sfx_copula(flag, "0", acc_v + "nd" + loc_v + "n",  "[^aeıioöuü]", rules) # abl
        sfx_ki(flag, "0", acc_v + "n" + acc_v + "n",   "[^aeıioöuü]", rules)      # gen
        sfx_copula(flag, "0", acc_v + "yl" + loc_v,        "[^aeıioöuü]", rules) # ins

        # 2. Vowel ending stems (condition: [aeıioöuü])
        poss_s = f"s{acc_v}"
        rules.append(sfx(flag, "0", poss_s + "n" + acc_v,         "[aeıioöuü]")) # acc
        rules.append(sfx(flag, "0", poss_s + "n" + loc_v,         "[aeıioöuü]")) # dat
        sfx_ki(flag, "0", poss_s + "nd" + loc_v,        "[aeıioöuü]", rules)      # loc
        sfx_copula(flag, "0", poss_s + "nd" + loc_v + "n",  "[aeıioöuü]", rules) # abl
        sfx_ki(flag, "0", poss_s + "n" + acc_v + "n",   "[aeıioöuü]", rules)      # gen
        sfx_copula(flag, "0", poss_s + "yl" + loc_v,        "[aeıioöuü]", rules) # ins

        blocks.append(make_flag_block(flag, unique(rules)))
    return blocks


def gen_2sg_poss_flags() -> list[str]:
    """2sg possessive -In/-n"""
    blocks = []
    for flag, back, rounded in [
        ("P5", True, False),
        ("P6", True, True),
        ("P7", False, False),
        ("P8", False, True),
    ]:
        acc_v = "ı" if back and not rounded else ("u" if rounded and back else ("i" if not back and not rounded else "ü"))
        loc_v = "a" if back else "e"
        sg = f"{acc_v}n"
        m  = "n"

        eq_v = "ca" if back else "ce"
        rules = []
        for base_poss, cond in [(sg, CONS_RE), (m, VOWEL_RE)]:
            sfx_copula(flag, "0", base_poss, cond, rules)
            rules.append(sfx(flag, "0", base_poss + acc_v,        cond))
            rules.append(sfx(flag, "0", base_poss + loc_v,        cond))
            sfx_ki(flag, "0", base_poss + "d" + loc_v,  cond, rules)
            sfx_copula(flag, "0", base_poss + "d" + loc_v + "n", cond, rules)
            sfx_ki(flag, "0", base_poss + acc_v + "n",  cond, rules)
            sfx_copula(flag, "0", base_poss + "l" + loc_v,  cond, rules)
            rules.append(sfx(flag, "0", base_poss + eq_v,       cond))
        blocks.append(make_flag_block(flag, unique(rules)))

    return blocks


def gen_1pl_poss_flags() -> list[str]:
    """1pl possessive -ImIz/-mIz"""
    blocks = []
    for flag, back, rounded in [
        ("PM", True, False),
        ("PO", True, True),
        ("PP", False, False),
        ("PQ", False, True),
    ]:
        acc_v = "ı" if back and not rounded else ("u" if rounded and back else ("i" if not back and not rounded else "ü"))
        loc_v = "a" if back else "e"
        sg = f"{acc_v}mız" if back and not rounded else \
             ("umuz" if rounded and back else ("imiz" if not back and not rounded else "ümüz"))
        m  = "mız" if back and not rounded else ("muz" if rounded and back else ("miz" if not back and not rounded else "müz"))

        eq_v = "ca" if back else "ce"
        rules = []
        for base_poss, cond in [(sg, CONS_RE), (m, VOWEL_RE)]:
            sfx_copula(flag, "0", base_poss, cond, rules)
            rules.append(sfx(flag, "0", base_poss + acc_v,        cond))
            rules.append(sfx(flag, "0", base_poss + loc_v,        cond))
            sfx_ki(flag, "0", base_poss + "d" + loc_v,  cond, rules)
            sfx_copula(flag, "0", base_poss + "d" + loc_v + "n", cond, rules)
            sfx_ki(flag, "0", base_poss + acc_v + "n",  cond, rules)
            sfx_copula(flag, "0", base_poss + "l" + loc_v,  cond, rules)
            rules.append(sfx(flag, "0", base_poss + eq_v,       cond))
        blocks.append(make_flag_block(flag, unique(rules)))

    return blocks


def gen_2pl_poss_flags() -> list[str]:
    """2pl possessive -InIz/-nIz"""
    blocks = []
    for flag, back, rounded in [
        ("PN", True, False),
        ("PR", True, True),
        ("PW", False, False),
        ("PZ", False, True),
    ]:
        acc_v = "ı" if back and not rounded else ("u" if rounded and back else ("i" if not back and not rounded else "ü"))
        loc_v = "a" if back else "e"
        sg = f"{acc_v}nız" if back and not rounded else \
             ("umuz" if rounded and back else ("iniz" if not back and not rounded else "ünüz"))
        m  = "nız" if back and not rounded else ("nuz" if rounded and back else ("niz" if not back and not rounded else "nüz"))

        eq_v = "ca" if back else "ce"
        rules = []
        for base_poss, cond in [(sg, CONS_RE), (m, VOWEL_RE)]:
            sfx_copula(flag, "0", base_poss, cond, rules)
            rules.append(sfx(flag, "0", base_poss + acc_v,        cond))
            rules.append(sfx(flag, "0", base_poss + loc_v,        cond))
            sfx_ki(flag, "0", base_poss + "d" + loc_v,  cond, rules)
            sfx_copula(flag, "0", base_poss + "d" + loc_v + "n", cond, rules)
            sfx_ki(flag, "0", base_poss + acc_v + "n",  cond, rules)
            sfx_copula(flag, "0", base_poss + "l" + loc_v,  cond, rules)
            rules.append(sfx(flag, "0", base_poss + eq_v,       cond))
        blocks.append(make_flag_block(flag, unique(rules)))
    return blocks


# ---------------------------------------------------------------------------
# SECTION 5: Copula flag
# ---------------------------------------------------------------------------

def gen_copula_flag_back(flag: str = "CL") -> str:
    COPULAS_VOWEL = [
        "ydI", "ydIm", "ydIn", "ydIk", "ydInIz", "ydIlAr",
        "ymIş", "ymIşIm", "ymIşsIn", "ymIşIz", "ymIşsInIz", "ymIşlAr",
        "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr",
        "yIm", "sIn", "yIz", "sInIz", "lAr",
        "dIr", "dIrlAr", "lArdIr", "yken",
        "yImdIr", "sIndIr", "yIzdIr", "sInIzdIr",
    ]
    COPULAS_CONS = [
        "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
        "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
        "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
        "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
        "Im", "sIn", "Iz", "sInIz", "lAr",
        "dIr", "tIr", "dIrlAr", "tIrlAr", "lArdIr", "ken",
        "ImdIr", "sIndIr", "IzdIr", "sInIzdIr",
    ]
    rules = []
    for cop_tmpl in COPULAS_VOWEL:
        resolved = harmonize("oda", cop_tmpl)
        if resolved:
            rules.append(sfx(flag, "0", resolved, "."))
    for cop_tmpl in COPULAS_CONS:
        resolved = harmonize("bak", cop_tmpl)
        if resolved:
            rules.append(sfx(flag, "0", resolved, "."))
    return make_flag_block(flag, unique(rules))

def gen_copula_flag_front(flag: str = "cl") -> str:
    COPULAS_VOWEL = [
        "ydI", "ydIm", "ydIn", "ydIk", "ydInIz", "ydIlAr",
        "ymIş", "ymIşIm", "ymIşsIn", "ymIşIz", "ymIşsInIz", "ymIşlAr",
        "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr",
        "yIm", "sIn", "yIz", "sInIz", "lAr",
        "dIr", "dIrlAr", "lArdIr", "yken",
        "yImdIr", "sIndIr", "yIzdIr", "sInIzdIr",
    ]
    COPULAS_CONS = [
        "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
        "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
        "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
        "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
        "Im", "sIn", "Iz", "sInIz", "lAr",
        "dIr", "tIr", "dIrlAr", "tIrlAr", "lArdIr", "ken",
        "ImdIr", "sIndIr", "IzdIr", "sInIzdIr",
    ]
    rules = []
    for cop_tmpl in COPULAS_VOWEL:
        resolved = harmonize("kedi", cop_tmpl)
        if resolved:
            rules.append(sfx(flag, "0", resolved, "."))
    for cop_tmpl in COPULAS_CONS:
        resolved = harmonize("ev", cop_tmpl)
        if resolved:
            rules.append(sfx(flag, "0", resolved, "."))
    return make_flag_block(flag, unique(rules))


# ---------------------------------------------------------------------------
# SECTION 6: Relative -ki flag
# ---------------------------------------------------------------------------

def gen_ki_flag(flag: str = "KI") -> str:
    """Relative -ki clitic + its inflections"""
    ki_inflections = [
        '',   # bare -ki
        'ler', 'lerin', 'lere', 'lerde', 'lerden', 'lerle', 'lerce',
        'leri', 'lerini', 'lerine', 'lerinde', 'lerinden', 'leriyle', 'lerinin',
        'ni', 'ne', 'nde', 'nden', 'nin', 'yle', 'yse', 'dir',
        'ydi', 'ymiş', 'yken',
    ]
    rules = []
    for infl in ki_inflections:
        rules.append(sfx(flag, "0", "ki" + infl, "."))
    return make_flag_block(flag, unique(rules))


# ---------------------------------------------------------------------------
# SECTION 7: Derivation flags (1st-level)
# ---------------------------------------------------------------------------

def gen_deriv_li(flag: str = "LI") -> str:
    """-lI adjective derivation (+ basic inflection of derived adj)"""
    # Back: -lı / Front: -li / Back-rounded: -lu / Front-rounded: -lü
    stems = {
        "[aı][^aeıioöuü]": ("lı", "lıydı", "lıydım", "lıyken", "lılar", "lılara", "lılarda", "lılardan",
                              "lılık", "lılığa", "lılıkta", "lılıktan"),
        "[ou][^aeıioöuü]": ("lu", "luydu", "luyken", "lular", "lulara", "lularda", "lulardan",
                              "luluk", "luluğa"),
        "[ei][^aeıioöuü]": ("li", "liydi", "liyken", "liler", "lilere", "lilerde", "lilerden",
                              "lilik", "liliğe"),
        "[öü][^aeıioöuü]": ("lü", "lüydü", "lüyken", "lüler", "lülere", "lülerde", "lülerden",
                              "lülük", "lülüğe"),
        "[aı]": ("lı", "lıydı", "lıyken", "lılar"),
        "[ou]": ("lu", "luydu", "luyken", "lular"),
        "[ei]": ("li", "liydi", "liyken", "liler"),
        "[öü]": ("lü", "lüydü", "lüyken", "lüler"),
    }
    rules = []
    for cond, forms in stems.items():
        for form in forms:
            rules.append(sfx(flag, "0", form, cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_sz(flag: str = "SZ") -> str:
    """-sIz (without) derivation"""
    rules = []
    for cond, suf in [("[aıou]", "sız"), ("[eiöü]", "siz"),
                      ("[aı][^aeıioöuü]","sız"), ("[ou][^aeıioöuü]","suz"),
                      ("[ei][^aeıioöuü]","siz"), ("[öü][^aeıioöuü]","süz")]:
        rules.append(sfx(flag, "0", suf, cond))
        rules.append(sfx(flag, "0", suf + "lık", cond))
        rules.append(sfx(flag, "0", suf + "lar", cond))
        rules.append(sfx(flag, "0", suf + "lara", cond))
        rules.append(sfx(flag, "0", suf + "larda", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_lk(flag: str = "LK") -> str:
    """-lIk abstract noun derivation + full possessive and case forms"""
    rules = []
    for cond, suf, suf_v, acc, gen, dat, loc, abl, ins in [
        ("[aı][^aeıioöuü]", "lık", "lığ", "lığı", "lığın", "lığa",  "lıkta",  "lıktan",  "lıkla"),
        ("[ou][^aeıioöuü]", "luk", "luğ", "luğu", "luğun", "luğa",  "lukta",  "luktan",  "lukla"),
        ("[ei][^aeıioöuü]", "lik", "liğ", "liği", "liğin", "liğe",  "likte",  "likten",  "likle"),
        ("[öü][^aeıioöuü]", "lük", "lüğ", "lüğü", "lüğün", "lüğe",  "lükte",  "lükten",  "lükle"),
        ("[aı]",            "lık", "lığ", "lığı", "lığın", "lığa",  "lıkta",  "lıktan",  "lıkla"),
        ("[ou]",            "luk", "luğ", "luğu", "luğun", "luğa",  "lukta",  "luktan",  "lukla"),
        ("[ei]",            "lik", "liğ", "liği", "liğin", "liğe",  "likte",  "likten",  "likle"),
        ("[öü]",            "lük", "lüğ", "lüğü", "lüğün", "lüğe",  "lükte",  "lükten",  "lükle"),
    ]:
        # Bare derived noun + case
        rules.append(sfx(flag, "0", suf, cond))
        rules.append(sfx(flag, "0", suf + "lar", cond))
        rules.append(sfx(flag, "0", suf_v + "a",  cond))   # dat
        rules.append(sfx(flag, "0", suf_v + "ı" if 'ı' in acc else suf_v + "i" if 'i' in acc else suf_v + "u" if 'u' in acc else suf_v + "ü", cond))  # acc
        rules.append(sfx(flag, "0", suf + "ta",   cond))   # loc
        rules.append(sfx(flag, "0", suf + "tan",  cond))   # abl
        rules.append(sfx(flag, "0", suf_v + "ın" if 'ı' in gen else suf_v + "in" if 'i' in gen else suf_v + "un" if 'u' in gen else suf_v + "ün", cond))  # gen
        rules.append(sfx(flag, "0", suf + "la",   cond))   # ins
        # 3sg possessive + case (n-buffer before case suffix: lığ+ı+n+a=lığına)
        poss_v = "ı" if 'ı' in acc else "i" if 'i' in acc else "u" if 'u' in acc else "ü"
        dat_v  = "a" if poss_v in ("ı", "u") else "e"
        for form in [
            suf_v + poss_v,                               # 3sg poss bare (lığı)
            suf_v + poss_v + "n" + dat_v,                # 3sg poss dative (lığına)
            suf_v + poss_v + "nd" + dat_v,               # 3sg poss locative (lığında)
            suf_v + poss_v + "nd" + dat_v + "n",         # 3sg poss ablative (lığından)
            suf_v + poss_v + "n" + poss_v + "n",         # 3sg poss genitive (lığının)
            suf_v + poss_v + ("yla" if poss_v in ("u", "ı") else "yle"),  # 3sg poss ins
        ]:
            rules.append(sfx(flag, "0", form, cond))
        # 1sg possessive: bare, acc, loc, gen
        p1bare = suf + poss_v + "m"                      # lık+ım = lıkım
        p1acc  = suf + poss_v + "m" + poss_v             # lıkımı
        p1loc  = suf + poss_v + "md" + dat_v             # lıkımda
        p1gen  = suf + poss_v + "m" + poss_v + "n"       # lıkımın
        for form in [p1bare, p1acc, p1loc, p1gen]:
            rules.append(sfx(flag, "0", form, cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_ci(flag: str = "CI") -> str:
    """-CI agentive/occupational noun derivation"""
    rules = []
    for cond, suf in [
        ("[aı][^çfhkpsşt]", "cı"), ("[ou][^çfhkpsşt]", "cu"),
        ("[ei][^çfhkpsşt]", "ci"), ("[öü][^çfhkpsşt]", "cü"),
        ("[aı][çfhkpsşt]",  "çı"), ("[ou][çfhkpsşt]",  "çu"),
        ("[ei][çfhkpsşt]",  "çi"), ("[öü][çfhkpsşt]",  "çü"),
        # vowel ending
        ("[aı]", "cı"), ("[ou]", "cu"), ("[ei]", "ci"), ("[öü]", "cü"),
    ]:
        rules.append(sfx(flag, "0", suf, cond))
        rules.append(sfx(flag, "0", suf + "lar", cond))
        rules.append(sfx(flag, "0", suf + "lık", cond))
        rules.append(sfx(flag, "0", suf + "lara", cond))
        rules.append(sfx(flag, "0", suf + "larda", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_ck(flag: str = "CK") -> str:
    """-cIk diminutive"""
    rules = []
    for cond, suf in [
        ("[aı][^çfhkpsşt]", "cık"), ("[ou][^çfhkpsşt]", "cuk"),
        ("[ei][^çfhkpsşt]", "cik"), ("[öü][^çfhkpsşt]", "cük"),
        ("[aı][çfhkpsşt]",  "çık"), ("[ou][çfhkpsşt]",  "çuk"),
        ("[ei][çfhkpsşt]",  "çik"), ("[öü][çfhkpsşt]",  "çük"),
        ("[aı]", "cık"), ("[ou]", "cuk"), ("[ei]", "cik"), ("[öü]", "cük"),
    ]:
        rules.append(sfx(flag, "0", suf, cond))
    return make_flag_block(flag, unique(rules))


# ---------------------------------------------------------------------------
# SECTION 8: 2nd-level derivation flags (verb-forming + re-nominalization)
# ---------------------------------------------------------------------------

def gen_deriv_las(flag: str = "DL") -> str:
    """-lAş verb-forming derivation"""
    rules = []
    for cond, suf, verb_inf in [
        ("[aı]",                  "laş", "laşmak"),
        ("[ou]",                  "laş", "laşmak"),
        ("[ei]",                  "leş", "leşmek"),
        ("[öü]",                  "leş", "leşmek"),
        ("[aı][^aeıioöuü]",       "laş", "laşmak"),
        ("[ou][^aeıioöuü]",       "laş", "laşmak"),
        ("[ei][^aeıioöuü]",       "leş", "leşmek"),
        ("[öü][^aeıioöuü]",       "leş", "leşmek"),
    ]:
        inf = verb_inf
        rules.append(sfx(flag, "0", inf, cond))
        for case in ['ın', 'a', 'ta', 'tan', 'la', 'lar']:
            rules.append(sfx(flag, "0", inf[:-3] + case, cond))
        for ger in ['ma', 'me', 'ış', 'iş', 'uş', 'üş']:
            rules.append(sfx(flag, "0", suf + ger, cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_las_tir(flag: str = "DT") -> str:
    """-lAştIr causative verb-forming derivation"""
    rules = []
    for cond, suf in [
        ("[aıou]",             "laştır"),
        ("[eiöü]",             "leştir"),
        ("[aıou][^aeıioöuü]",  "laştır"),
        ("[eiöü][^aeıioöuü]",  "leştir"),
    ]:
        rules.append(sfx(flag, "0", suf + "mak", cond))
        rules.append(sfx(flag, "0", suf + "mek", cond))
        rules.append(sfx(flag, "0", suf + "ma",  cond))
        rules.append(sfx(flag, "0", suf + "me",  cond))
        rules.append(sfx(flag, "0", suf + "ış",  cond))
        rules.append(sfx(flag, "0", suf + "iş",  cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_len(flag: str = "DE") -> str:
    """-lAn reflexive/passive verb-forming derivation"""
    rules = []
    for cond, suf in [
        ("[aıou]",             "lan"),
        ("[eiöü]",             "len"),
        ("[aıou][^aeıioöuü]",  "lan"),
        ("[eiöü][^aeıioöuü]",  "len"),
    ]:
        rules.append(sfx(flag, "0", suf + "mak", cond))
        rules.append(sfx(flag, "0", suf + "mek", cond))
        rules.append(sfx(flag, "0", suf + "ma",  cond))
        rules.append(sfx(flag, "0", suf + "me",  cond))
    return make_flag_block(flag, unique(rules))


# ---------------------------------------------------------------------------
# SECTION 9: Verb paradigm flags (reuse TAM/NEG from v1)
# ---------------------------------------------------------------------------
# NOTE: Verb paradigms are the largest flags. We keep negative forms baked in
# (as per user decision). The verb paradigm flags are generated using the SAME
# generate_verb_suffixes() + format_verb_rules() logic from v1, but now the
# flag names are 2-char FLAG long identifiers.

def get_v1_verb_content() -> str:
    """
    Import and re-run the old generator's verb section, but relabeling
    the output flags to FLAG long identifiers.
    
    Old → New flag mapping:
      9   → VB   (back consonant, unrounded)
      109 → VR   (back consonant, rounded)
      10  → VF   (front consonant, unrounded)
      110 → VG   (front consonant, rounded)
      11  → VA   (back vowel stem, unrounded)
      111 → VS   (back vowel stem, rounded)
      12  → VE   (front vowel stem, unrounded)
      112 → VH   (front vowel stem, rounded)
      15  → VK   (back consonant voicing)
      115 → VL   (back consonant voicing, rounded)
      16  → VM   (front consonant voicing)
      116 → VN   (front consonant voicing, rounded)
      17  → VY   (narrowing: demek/yemek)
    
    This function is a stub — the actual verb generation is done by calling
    the v1 generate_verb_suffixes() and format_verb_rules() functions and
    post-processing to replace integer flags with 2-char flags.
    """
    return "# (Verb flags generated by patching v1 logic — see generate_grammar.py)"


# ---------------------------------------------------------------------------
# SECTION 10: Prefix flag
# ---------------------------------------------------------------------------

def gen_prefix_flag(flag: str = "PX") -> str:
    """Metric and loan prefixes"""
    prefixes = [
        "mili", "mikro", "nano", "piko", "femto", "atto",
        "kilo", "mega", "giga", "tera", "peta", "eksa",
        "anti", "hiper", "siber", "biyo", "oto", "kriyo",
        "psiko", "makro", "nöro",
    ]
    lines = [f"PFX {flag} Y {len(prefixes)}"]
    for p in prefixes:
        lines.append(f"PFX {flag} 0 {p} .")
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# MAIN GENERATOR
# ---------------------------------------------------------------------------

def generate_header() -> str:
    return """# Türkçe Yazım Denetimi Sözlüğü - Chained Flags Architecture v1
SET UTF-8
FLAG long
NOSUGGEST NS
LANG tr
WORDCHARS '

# Break characters (allow breaking at hyphens, en-dashes, and em-dashes)
BREAK 5
BREAK -
BREAK ^-
BREAK -$
BREAK –
BREAK —


# Suggestion parameters
KEY qwertyuıopğü|asdfghjklşi|zxcvbnmçö|QWERTYUIOPĞÜ|ASDFGHJKLŞİ|ZXCVBNMÇÖ|fgğıodrnhpqw|uıevazyktsx|jövcçzsb|FGĞIODRNHPQW|UIEVAZYKTSX|JÖVCÇZSB|qaz|wsx|edc|rfv|tgb|yhn|ujm|ıkö|olç|pş|QAZ|WSX|EDC|RFV|TGB|YHN|UJM|IKÖ|OLÇ|PŞ
TRY aeilrıtdknsmyuböuşzcgçhpvğfjAEİLRITDKNSMYUBÖUŞZCGÇHPVĞFJ
MAP 9
MAP aâAÂ
MAP uûUÛ
MAP iîİÎ
MAP cçCÇ
MAP gğGĞ
MAP sşSŞ
MAP oöOÖ
MAP uüUÜ
MAP ıiIİ
MAXDIFF 3

REP 52
REP a â
REP â a
REP u û
REP û u
REP i î
REP î i
REP c ç
REP ç c
REP g ğ
REP ğ g
REP s ş
REP ş s
REP o ö
REP ö o
REP u ü
REP ü u
REP ı i
REP i ı
REP sh ş
REP ch ç
REP gh ğ
REP ss ş
REP dd t
REP tt d
REP bb p
REP pp b
REP cc c
REP kk g
REP ğ y
REP y ğ
REP h ğ
REP ğ h
REP a e
REP e a
REP d t
REP t d
REP p b
REP b p
REP z s
REP s z
REP k g
REP g k
REP ın in
REP in ın
REP un ün
REP ün un
REP da de
REP de da
REP lar ler
REP ler lar
REP la le
REP le la
"""


def generate_grammar_v1():
    """Main entry point — generates the new chained tr.aff."""
    content = generate_header()

    # --- Case flags ---
    print("Generating case flags (AC, DA, LO, AB, GE, IN, EQ)...")
    # --- Stem class flags ---
    print("Generating stem class flags (B1/B2/F1/F2/B3/B4/F3/F4/V1-V4/D1-D4/C1-C4/G1-G4/NX)...")
    content += "\n# STEM CLASS FLAGS\n"
    STEM_CLASS_FLAGS = [
        "B1", "B2",   # back consonant: unrounded, rounded
        "F1", "F2",   # front consonant: unrounded, rounded
        "B3", "B4",   # back vowel-ending: unrounded, rounded
        "F3", "F4",   # front vowel-ending: unrounded, rounded
        "V1", "V2",   # back consonant voicing: unrounded, rounded
        "V3", "V4",   # front consonant voicing: unrounded, rounded
        "D1", "D2",   # back vowel-drop: unrounded, rounded
        "D3", "D4",   # front vowel-drop: unrounded, rounded
        "C1", "C2",   # back compound: unrounded, rounded
        "C3", "C4",   # front compound: unrounded, rounded
        "G1", "G2",   # back doubling: unrounded, rounded
        "G3", "G4",   # front doubling: unrounded, rounded
        "NX",         # test/generic stem (used in validate_v2.py)
    ]
    for sc_flag in STEM_CLASS_FLAGS:
        content += gen_stem_flag(sc_flag) + "\n"

    content += "\n# CASE FLAGS\n"
    for block in gen_ac_flags():
        content += block + "\n"
    for block in gen_da_flags():
        content += block + "\n"
    for block in gen_lo_flags():
        content += block + "\n"
    for block in gen_ab_flags():
        content += block + "\n"
    for block in gen_ge_flags():
        content += block + "\n"
    for block in gen_in_flags():
        content += block + "\n"
    for block in gen_eq_flags():
        content += block + "\n"

    # --- Plural flags ---
    print("Generating plural flags (PB, PF)...")
    content += "\n# PLURAL FLAGS\n"
    content += gen_plural_back() + "\n"
    content += gen_plural_front() + "\n"

    # --- 3sg possessive flags ---
    print("Generating 3sg possessive flags (PS, PT, PU, PV)...")
    content += "\n# 3SG POSSESSIVE FLAGS\n"
    for block in gen_3sg_poss_flags():
        content += block + "\n"

    # --- 1sg possessive flags ---
    print("Generating 1sg possessive flags (P1-P4)...")
    content += "\n# 1SG POSSESSIVE FLAGS\n"
    for block in gen_all_possessive_flags():
        content += block + "\n"

    # --- 2sg possessive flags ---
    print("Generating 2sg possessive flags (P5-P8)...")
    content += "\n# 2SG POSSESSIVE FLAGS\n"
    for block in gen_2sg_poss_flags():
        content += block + "\n"

    # --- 1pl possessive flags ---
    print("Generating 1pl possessive flags (PM, PO, PP, PQ)...")
    content += "\n# 1PL POSSESSIVE FLAGS\n"
    for block in gen_1pl_poss_flags():
        content += block + "\n"

    # --- 2pl possessive flags ---
    print("Generating 2pl possessive flags (PN, PR, PW, PZ)...")
    content += "\n# 2PL POSSESSIVE FLAGS\n"
    for block in gen_2pl_poss_flags():
        content += block + "\n"

    # --- Copula flags ---
    print("Generating copula flags (CL, cl)...")
    content += "\n# COPULA FLAGS\n"
    content += gen_copula_flag_back() + "\n"
    content += gen_copula_flag_front() + "\n"

    # --- Relative -ki flag ---
    print("Generating relative -ki flag (KI)...")
    content += "\n# RELATIVE -KI FLAG\n"
    content += gen_ki_flag() + "\n"

    # --- Derivation flags ---
    print("Generating derivation flags (LI, SZ, LK, CI, CK)...")
    content += "\n# DERIVATION FLAGS (1ST-LEVEL)\n"
    content += gen_deriv_li() + "\n"
    content += gen_deriv_sz() + "\n"
    content += gen_deriv_lk() + "\n"
    content += gen_deriv_ci() + "\n"
    content += gen_deriv_ck() + "\n"

    # --- 2nd-level derivation flags ---
    print("Generating 2nd-level derivation flags (DL, DT, DE)...")
    content += "\n# DERIVATION FLAGS (2ND-LEVEL: VERB-FORMING)\n"
    content += gen_deriv_las() + "\n"
    content += gen_deriv_las_tir() + "\n"
    content += gen_deriv_len() + "\n"

    # --- Verb flags (patched from v1) ---
    print("Generating verb paradigm flags (VB, VR, VF, VG, VA, VS, VE, VH, VK, VL, VM, VN, VY)...")
    content += "\n# VERB PARADIGM FLAGS\n"
    content += _generate_verb_flags_from_v1() + "\n"

    # --- Prefix flag ---
    print("Generating prefix flag (PX)...")
    content += "\n# PREFIX FLAG\n"
    content += gen_prefix_flag() + "\n"

    # --- Proper Noun flags ---
    print("Generating Proper Noun case/possessive flags with apostrophes...")
    content += "\n# PROPER NOUN CASE/POSSESSIVE FLAGS\n"
    for block in gen_proper_flags():
        content += block + "\n"

    print("Writing tr_v1.aff...")
    with open('tr_v1.aff', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

    # Count rules
    total_sfx = content.count('\nSFX ')
    print(f"Done. Total SFX rules: {total_sfx}")
    import os
    size_kb = os.path.getsize('tr_v1.aff') / 1024
    print(f"tr_v1.aff size: {size_kb:.1f} KB")


def gen_proper_flags() -> list[str]:
    blocks = []
    
    # uA (Accusative: 'ü)
    blocks.append(make_flag_block("uA", [sfx("uA", "0", "'ü", ".")]))
    
    # uY (Dative: 'e)
    blocks.append(make_flag_block("uY", [sfx("uY", "0", "'e", ".")]))
    
    # uL (Locative: 'de / 'te)
    blocks.append(make_flag_block("uL", [
        sfx("uL", "0", "'de", "[^çfhkpsşt]"),
        sfx("uL", "0", "'te", "[çfhkpsşt]")
    ]))
    
    # uR (Ablative: 'den / 'ten)
    blocks.append(make_flag_block("uR", [
        sfx("uR", "0", "'den/cl", "[^çfhkpsşt]"),
        sfx("uR", "0", "'ten/cl", "[çfhkpsşt]")
    ]))
    
    # uN (Genitive: 'ün)
    rules_uN = []
    sfx_ki("uN", "0", "'ün", ".", rules_uN)
    blocks.append(make_flag_block("uN", unique(rules_uN)))
    
    # uI (Instrumental: 'le)
    blocks.append(make_flag_block("uI", [sfx("uI", "0", "'le/cl", ".")]))
    
    # uQ (Equative: 'ce / 'çe)
    blocks.append(make_flag_block("uQ", [
        sfx("uQ", "0", "'ce/cl", "[^çfhkpsşt]"),
        sfx("uQ", "0", "'çe/cl", "[çfhkpsşt]")
    ]))
    
    # uP (3sg possessive: 'ü / 'sü)
    rules_uP = [
        sfx("uP", "0", "'ü/cl", "[^aeıioöuü]"),
        sfx("uP", "0", "'sü/cl", "[aeıioöuü]"),
        sfx("uP", "0", "'ünün", "[^aeıioöuü]"), # gen
        sfx("uP", "0", "'ünü", "[^aeıioöuü]"), # acc
        sfx("uP", "0", "'üne", "[^aeıioöuü]"), # dat
        sfx("uP", "0", "'ünde", "[^aeıioöuü]"), # loc
        sfx("uP", "0", "'ünden/cl", "[^aeıioöuü]"), # abl
        sfx("uP", "0", "'üyle/cl", "[^aeıioöuü]"), # ins
    ]
    sfx_ki("uP", "0", "'ünde", "[^aeıioöuü]", rules_uP)
    sfx_ki("uP", "0", "'ünün", "[^aeıioöuü]", rules_uP)
    blocks.append(make_flag_block("uP", unique(rules_uP)))
    
    # u1 (1sg possessive: 'üm)
    rules_u1 = [
        sfx("u1", "0", "'üm/cl", "[^aeıioöuü]"),
        sfx("u1", "0", "'ümü", "[^aeıioöuü]"),
        sfx("u1", "0", "'üme", "[^aeıioöuü]"),
        sfx("u1", "0", "'ümden/cl", "[^aeıioöuü]"),
        sfx("u1", "0", "'ümle/cl", "[^aeıioöuü]"),
    ]
    sfx_ki("u1", "0", "'ümde", "[^aeıioöuü]", rules_u1)
    sfx_ki("u1", "0", "'ümün", "[^aeıioöuü]", rules_u1)
    blocks.append(make_flag_block("u1", unique(rules_u1)))
    
    # u2 (2sg possessive: 'ün)
    rules_u2 = [
        sfx("u2", "0", "'ün/cl", "[^aeıioöuü]"),
        sfx("u2", "0", "'ünü", "[^aeıioöuü]"),
        sfx("u2", "0", "'üne", "[^aeıioöuü]"),
        sfx("u2", "0", "'ünden/cl", "[^aeıioöuü]"),
        sfx("u2", "0", "'ünle/cl", "[^aeıioöuü]"),
    ]
    sfx_ki("u2", "0", "'ünde", "[^aeıioöuü]", rules_u2)
    sfx_ki("u2", "0", "'ünün", "[^aeıioöuü]", rules_u2)
    blocks.append(make_flag_block("u2", unique(rules_u2)))
    
    # u3 (1pl possessive: 'ümüz)
    rules_u3 = [
        sfx("u3", "0", "'ümüz/cl", "[^aeıioöuü]"),
        sfx("u3", "0", "'ümüzü", "[^aeıioöuü]"),
        sfx("u3", "0", "'ümüze", "[^aeıioöuü]"),
        sfx("u3", "0", "'ümüzden/cl", "[^aeıioöuü]"),
        sfx("u3", "0", "'ümüzle/cl", "[^aeıioöuü]"),
    ]
    sfx_ki("u3", "0", "'ümüzde", "[^aeıioöuü]", rules_u3)
    sfx_ki("u3", "0", "'ümüzün", "[^aeıioöuü]", rules_u3)
    blocks.append(make_flag_block("u3", unique(rules_u3)))
    
    # u4 (2pl possessive: 'ünüz)
    rules_u4 = [
        sfx("u4", "0", "'ünüz/cl", "[^aeıioöuü]"),
        sfx("u4", "0", "'ünüzü", "[^aeıioöuü]"),
        sfx("u4", "0", "'ünüze", "[^aeıioöuü]"),
        sfx("u4", "0", "'ünüzden/cl", "[^aeıioöuü]"),
        sfx("u4", "0", "'ünüzle/cl", "[^aeıioöuü]"),
    ]
    sfx_ki("u4", "0", "'ünüzde", "[^aeıioöuü]", rules_u4)
    sfx_ki("u4", "0", "'ünüzün", "[^aeıioöuü]", rules_u4)
    blocks.append(make_flag_block("u4", unique(rules_u4)))
    
    # uC (Proper Nominal Copula: 'dir, 'dirler, etc.)
    rules_uC = []
    COPULAS_PROP = [
        "'di", "'dim", "'din", "'dik", "'diniz", "'diler",
        "'ti", "'tim", "'tin", "'tik", "'tiniz", "'tiler",
        "'miş", "'mişim", "'mişsin", "'mişiz", "'mişsiniz", "'mişler",
        "'se", "'sem", "'sen", "'sek", "'seniz", "'seler",
        "'im", "'sin", "'iz", "'siniz", "'ler",
        "'dir", "'tir", "'dirler", "'tirler", "'lerdir", "'ken",
        "'imdir", "'sindir", "'izdir", "'sinizdir",
    ]
    for cop_tmpl in COPULAS_PROP:
        resolved = harmonize("gör", cop_tmpl)
        if resolved:
            rules_uC.append(sfx("uC", "0", resolved, "[öü][^ıiaeöoüu]"))
            
    blocks.append(make_flag_block("uC", unique(rules_uC)))
    
    return blocks


def get_verbal_noun_chain(stem_flag: str) -> str:
    """Verbal nouns (like -mak, -me, -iş) should only take case, plural, possessive, and copula.
    They must never take noun/adjective derivations (like -lik, -li, -siz, -ci, -leş, -len).
    """
    if stem_flag in ("PX", "NX"):
        return stem_flag
    chain = get_noun_chain(stem_flag)
    for deriv in ["LI", "SZ", "LK", "CI", "CK", "DL", "DT", "DE"]:
        chain = chain.replace(deriv, "")
    return chain

def _generate_verb_flags_from_v1() -> str:
    """
    Re-use verb content from v1 tr.aff directly (already generated on disk).
    Extract verb paradigm sections and remap integer flags to FLAG long 2-char identifiers.
    Also remap noun continuation flags on verb nominalizations to their full FLAG long chains,
    splitting voicing flags into unvoiced and voiced variants to bypass the 2-suffix limit.
    """
    import re

    FLAG_MAP = {
        9:   "VB", 109: "VR",
        10:  "VF", 110: "VG",
        11:  "VA", 111: "VS",
        12:  "VE", 112: "VH",
        15:  "VK", 115: "VL",
        16:  "VM", 116: "VN",
        17:  "VY",
    }
    VERB_FLAG_INTS = set(FLAG_MAP.keys())

    NOUN_MAP = {
        1:   "B1",  101: "B2",
        2:   "F1",  102: "F2",
        3:   "B3",  103: "B4",
        4:   "F3",  104: "F4",
        5:   "V1",  105: "V2",
        6:   "V3",  106: "V4",
        7:   "D1",  107: "D2",
        8:   "D3",  108: "D4",
        13:  "C1",  113: "C2",
        14:  "C3",  114: "C4",
        18:  "G1",  118: "G2",
        19:  "G3",  119: "G4",
        90:  "PX",
    }

    print("  Reading data/tr_v1.aff to extract verb sections...")
    with open('data/tr_v1.aff', 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    out_lines = []
    in_verb_block = False

    for line in lines:
        # Detect start of a new SFX block
        m = re.match(r'^SFX (\d+) Y (\d+)', line)
        if m:
            flag_int = int(m.group(1))
            in_verb_block = (flag_int in VERB_FLAG_INTS)
        # Process lines that belong to verb blocks
        if in_verb_block:
            # Check if this line has a noun nominalization flag (e.g. /6 or /5)
            # Line format: SFX 9 mak abildik/6 .
            m_rule = re.match(r'^(SFX \d+ \S+ \S+)/(\d+) (.*)$', line)
            if m_rule:
                prefix, old_int_str, suffix = m_rule.group(1), m_rule.group(2), m_rule.group(3)
                old_int = int(old_int_str)
                if old_int in NOUN_MAP:
                    stem_flag = NOUN_MAP[old_int]
                    if stem_flag.startswith('V'):
                        # Voicing class: generate unvoiced and voiced rules!
                        # 1. Unvoiced (ends in k) -> cons_chain (exclude the stem flag V1/V2/V3/V4)
                        cons_chain = get_verbal_noun_chain(stem_flag)
                        if cons_chain.startswith(stem_flag):
                            cons_chain = cons_chain[len(stem_flag):]
                        
                        unvoiced_line = f"{prefix}/{cons_chain} {suffix}"
                        out_lines.append(unvoiced_line)
                        
                        # 2. Voiced (ends in ğ) -> vowel_chain (restricted - no derivations)
                        vowel_chain = get_vowel_chain(stem_flag) + "CL"
                        
                        # Replace final 'k' of the suffix in prefix with 'ğ'
                        parts = prefix.split()
                        if len(parts) == 4 and parts[3].endswith('k'):
                            parts[3] = parts[3][:-1] + 'ğ'
                            voiced_prefix = ' '.join(parts)
                            voiced_line = f"{voiced_prefix}/{vowel_chain} {suffix}"
                            out_lines.append(voiced_line)
                        else:
                            # Fallback if it doesn't end in k
                            out_lines.append(line)
                    else:
                        # Non-voicing class: normal chain
                        chain = get_verbal_noun_chain(stem_flag)
                        normal_line = f"{prefix}/{chain} {suffix}"
                        out_lines.append(normal_line)
                else:
                    out_lines.append(line)
            else:
                out_lines.append(line)

    verb_content = '\n'.join(out_lines)

    # Remap integer flags to FLAG long (longest int first to avoid substring issues)
    for old_int, new_flag in sorted(FLAG_MAP.items(), key=lambda x: -x[0]):
        # Replace SFX header lines: "SFX 9 Y 15043" -> "SFX VB Y 15043"
        verb_content = re.sub(
            rf'^SFX {old_int} (Y \d+)$',
            f'SFX {new_flag} \\1',
            verb_content,
            flags=re.MULTILINE
        )
        # Replace SFX rule lines: "SFX 9 mak ..." -> "SFX VB mak ..."
        verb_content = re.sub(
            rf'^SFX {old_int} (\S)',
            f'SFX {new_flag} \\1',
            verb_content,
            flags=re.MULTILINE
        )
        # Remap continuation flags in nominalization suffix lines (e.g. /9 or /109)
        verb_content = re.sub(
            rf'/(\S+?){old_int}\b',
            f'/\\g<1>{new_flag}',
            verb_content
        )

    # Recalculate verb rule counts dynamically to prevent header count mismatches
    lines = verb_content.split('\n')
    header_indices = {}
    counts = {}
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue
        parts = line_clean.split()
        if len(parts) == 4 and parts[0] == 'SFX' and parts[2] == 'Y':
            flag = parts[1]
            header_indices[flag] = idx
            counts[flag] = 0
        elif len(parts) >= 2 and parts[0] == 'SFX':
            flag = parts[1]
            if flag in counts:
                counts[flag] += 1

    for flag, idx in header_indices.items():
        lines[idx] = f"SFX {flag} Y {counts[flag]}"

    return '\n'.join(lines)


if __name__ == '__main__':
    generate_grammar_v1()
