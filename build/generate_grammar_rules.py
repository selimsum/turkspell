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
VOWEL_RE    = "[aeıioöuüâîûAEIİOÖUÜÂÎÛ]"
CONS_RE     = "[^aeıioöuüâîûAEIİOÖUÜÂÎÛ]"

def sfx(flag: str, strip: str, add: str, condition: str) -> str:
    return f"SFX {flag} {strip} {add} {condition}"

def sfx_copula(flag: str, strip: str, add: str, cond: str, rules: list):
    lv = None
    for c in reversed(add):
        if c in 'aeıioöuüâîû':
            lv = c.lower()
            break
    if not lv:
        # Determine fallback last vowel from the flag name
        back_flags = {
            "P1", "P2", "P5", "P6", "PM", "PO", "PN", "PR", "CL", "PS", "PT",
            "R1", "I1", "i1", "Q1", "PB", "VC", "C1", "C2", "B1", "B2", "B3", "B4",
            "V1", "V2", "D1", "D2", "G1", "G2"
        }
        if flag.startswith('p') and len(flag) >= 3:
            is_back_flag = flag[1] in ('B', 'O')
        else:
            is_back_flag = flag in back_flags
        lv = 'a' if is_back_flag else 'e'
        
    is_vowel = add[-1] in 'aeıioöuüâîû' if add else False
    is_unvoiced = add[-1] in 'pçtksşhf' if add else False
    
    if lv in 'aı':
        if is_vowel:
            sim_stem = "oda"
        elif is_unvoiced:
            sim_stem = "bak"
        else:
            sim_stem = "bal"
    elif lv in 'ei':
        if is_vowel:
            sim_stem = "kedi"
        elif is_unvoiced:
            sim_stem = "tek"
        else:
            sim_stem = "ev"
    elif lv in 'ou':
        if is_vowel:
            sim_stem = "kutu"
        elif is_unvoiced:
            sim_stem = "uç"
        else:
            sim_stem = "yol"
    else:
        if is_vowel:
            sim_stem = "ütü"
        elif is_unvoiced:
            sim_stem = "düş"
        else:
            sim_stem = "gör"

    
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
        # Filter COPULAS_CONS by the voicing of the suffix's last consonant
        last_char = add[-1] if add else ''
        is_unvoiced_suffix = last_char in UNVOICED
        if is_unvoiced_suffix:
            # Exclude templates starting with 'd'
            copulas = [
                "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
                "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
                "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
                "Im", "sIn", "Iz", "sInIz", "lAr",
                "tIr", "tIrlAr", "lArdIr", "ken",
                "ImdIr", "sIndIr", "IzdIr", "sInIzdIr",
            ]
        else:
            # Exclude templates starting with 't'
            copulas = [
                "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
                "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
                "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
                "Im", "sIn", "Iz", "sInIz", "lAr",
                "dIr", "dIrlAr", "lArdIr", "ken",
                "ImdIr", "sIndIr", "IzdIr", "sInIzdIr",
            ]
        
    is_suffix_flag = flag in {
        "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "PM", "PO", "PP", "PQ", "PN", "PR", "PW", "PZ", "PS", "PT", "PU", "PV"
    } or (len(flag) >= 1 and flag[0] in "YyRIiNnAaQ")
    if is_suffix_flag:
        copulas = [c for c in copulas if c not in ("lAr", "lArdIr")]

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

def get_noun_chain(stem_flag: str, only_vowel: bool = False, only_consonant: bool = False) -> str:
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
    if only_vowel:
        cases = f"{acc_f}{dat_f}{gen_f}"
        possessives = f"{p3}{p1}{p2s}{p1pl}{p2pl}"
        copula_flag = "VC" if is_back else "vc"
        derivs = ""
        plural = ""
    elif only_consonant or exclude_vowel:
        cases = f"{loc_f}{abl_f}{ins_f}{eq_f}"
        possessives = ""
        copula_flag = "CL" if is_back else "cl"
        derivs = "LILKSZCISLDLDTDE"
    else:
        cases = f"{acc_f}{dat_f}{loc_f}{abl_f}{gen_f}{ins_f}{eq_f}"
        possessives = f"{p3}{p1}{p2s}{p1pl}{p2pl}"
        copula_flag = "CL" if is_back else "cl"
        derivs = "LILKSZCISLDLDTDE"

    if only_vowel:
        return f"{cases}{possessives}{copula_flag}"
    else:
        return f"{stem_flag}{cases}{plural}{possessives}{copula_flag}{derivs}"


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

    cop_f = "VC" if is_back else "vc"
    return f"{acc_f}{dat_f}{gen_f}{p3}{p1}{p2s}{p1pl}{p2pl}{cop_f}NE"

def gen_stem_flag(flag: str) -> str:
    """Slim stem-class flag. Handles bare stem validation and voicing/dropping/doubling."""
    rules = []
    rules.append(sfx(flag, "0", "0", "."))
    if flag in ("V1", "V2", "V3", "V4"):
        # Voicing stems are now generated directly in the dictionary as voiced/NE
        pass
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
                rules.append(sfx(flag, strip_suffix, f"{add_char}/{vowel_chain}", f"{strip_suffix}"))
            else:
                rules.append(sfx(flag, strip_suffix, f"{add_char}/{vowel_chain}", f"{strip_suffix}"))
    elif flag in ("G1", "G2", "G3", "G4"):
        vowel_chain = get_vowel_chain(flag)
        doubling_pairs = [
            ('p', 'bb'), ('t', 'dd'), ('t', 'tt'), ('d', 'dd'), ('k', 'kk'), ('s', 'ss'), ('z', 'zz'),
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
        
        # Plural endings always take unrounded vowels (ı/i) for accusative/genitive
        pl_acc = "ı" if is_back else "i"
        
        # 1. Suffixes that strip the final vowel (Plural and its cases/possessives)
        plural_suffixes = [
            pl,
            f"{pl}n{pl_acc}",
            f"{pl}n{loc}",
            f"{pl}nd{loc}",
            f"{pl}nd{loc}n",
            f"{pl}n{pl_acc}n",
            f"{pl}yl{loc}",
            f"{pl}nc{loc}",
        ]
        # Voicing transitions and buffer-s stripping for compound plurals:
        # e.g. buzdolabı + ları -> buzdolapları (b -> p)
        # ipucu + ları -> ipuçları (c -> ç)
        # denizanası + ları -> denizanaları (s -> strip s as well)
        voicing_devoicing = [
            ('b', 'p'),
            ('c', 'ç'),
            ('d', 't'),
            ('ğ', 'k'),
            ('s', '')
        ]

        for s in plural_suffixes:
            is_ki = s.endswith(f"nd{loc}") or s.endswith(f"n{acc}n")
            
            for voiced, unvoiced in voicing_devoicing:
                add_base = unvoiced + s
                cond_str = voiced + strip_v
                strip_str = voiced + strip_v
                if is_ki:
                    sfx_ki(flag, strip_str, add_base, cond_str, rules, chain_copula=True)
                else:
                    sfx_copula(flag, strip_str, add_base, cond_str, rules)
            
            cond_neg = f"[^bcğds]{strip_v}"
            add_base = s
            strip_str = strip_v
            if is_ki:
                sfx_ki(flag, strip_str, add_base, cond_neg, rules, chain_copula=True)
            else:
                sfx_copula(flag, strip_str, add_base, cond_neg, rules)
                
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
    rules_y1 = []
    sfx_copula("Y1", "0", "a", ".", rules_y1)
    blocks.append(make_flag_block("Y1", unique(rules_y1)))
    
    rules_y2 = []
    sfx_copula("Y2", "0", "e", ".", rules_y2)
    blocks.append(make_flag_block("Y2", unique(rules_y2)))
    
    rules_y1_v = []
    sfx_copula("y1", "0", "ya", ".", rules_y1_v)
    blocks.append(make_flag_block("y1", unique(rules_y1_v)))
    
    rules_y2_v = []
    sfx_copula("y2", "0", "ye", ".", rules_y2_v)
    blocks.append(make_flag_block("y2", unique(rules_y2_v)))
    
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
    cop_p1sg  = 'ım' if harmony == 'back' else 'im'
    cop_p2sg  = 'sın' if harmony == 'back' else 'sin'
    cop_p1pl  = 'ız' if harmony == 'back' else 'iz'
    cop_p2pl  = 'sınız' if harmony == 'back' else 'siniz'

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
        # personal copulas
        f"{pl}{cop_p1sg}",
        f"{pl}{cop_p2sg}",
        f"{pl}{cop_p1pl}",
        f"{pl}{cop_p2pl}",
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

    # Plural locative copulas (e.g. lardaysa, lerdeyse, lardayken, lerdeyken)
    # Since loc_form ends in a vowel, we use the vowel-ending copulas.
    sim_s = "oda" if harmony == 'back' else "ev"
    copulas_vow = [
        "ydI", "ydIm", "ydIn", "ydIk", "ydInIz", "ydIlAr",
        "ymIş", "ymIşIm", "ymIşsIn", "ymIşIz", "ymIşsInIz", "ymIşlAr",
        "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr",
        "yIm", "sIn", "yIz", "sInIz", "lAr",
        "dIr", "dIrlAr", "lArdIr", "yken",
    ]
    for cop in copulas_vow:
        resolved = harmonize(sim_s, cop)
        if resolved:
            suffixes.append(loc_form + resolved)

    # Plural ablative and genitive copulas (e.g. lerdense, lerdendir, lerdendirler, lerindendir, lerindense)
    # Since abl_form and gen_form end in a consonant, we use the consonant-ending copulas.
    abl_form = f"{pl}d{dat_v}n"
    copulas_cons = [
        "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
        "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
        "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
        "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
        "Im", "sIn", "Iz", "sInIz", "lAr",
        "dIr", "tIr", "dIrlAr", "tIrlAr", "lArdIr", "ken",
    ]
    for cop in copulas_cons:
        resolved = harmonize(sim_s, cop)
        if resolved:
            suffixes.append(abl_form + resolved)
            suffixes.append(gen_form + resolved)

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
            elif c in ("ı", "a", "ca"):
                rules.append(sfx(flag, "0", poss + c, "."))
            else:
                sfx_copula(flag, "0", poss + c, ".", rules)
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
            elif c in ("i", "e", "ce"):
                rules.append(sfx(flag, "0", poss + c, "."))
            else:
                sfx_copula(flag, "0", poss + c, ".", rules)
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
        sfx_copula(flag, "0", acc_v,            CONS_RE, rules)
        # After vowel: -s[vowel] (buffer s)
        sfx_copula(flag, "0", f"s{acc_v}",          VOWEL_RE, rules)

        # Cases after poss (n-buffer before all cases)
        # 1. Consonant ending stems (condition: CONS_RE)
        rules.append(sfx(flag, "0", acc_v + "n" + acc_v,         CONS_RE)) # acc
        sfx_copula(flag, "0", acc_v + "n" + loc_v,         CONS_RE, rules) # dat
        sfx_ki(flag, "0", acc_v + "nd" + loc_v,        CONS_RE, rules)      # loc
        sfx_copula(flag, "0", acc_v + "nd" + loc_v + "n",  CONS_RE, rules) # abl
        sfx_ki(flag, "0", acc_v + "n" + acc_v + "n",   CONS_RE, rules)      # gen
        sfx_copula(flag, "0", acc_v + "yl" + loc_v,        CONS_RE, rules) # ins

        # 2. Vowel ending stems (condition: VOWEL_RE)
        poss_s = f"s{acc_v}"
        rules.append(sfx(flag, "0", poss_s + "n" + acc_v,         VOWEL_RE)) # acc
        sfx_copula(flag, "0", poss_s + "n" + loc_v,         VOWEL_RE, rules) # dat
        sfx_ki(flag, "0", poss_s + "nd" + loc_v,        VOWEL_RE, rules)      # loc
        sfx_copula(flag, "0", poss_s + "nd" + loc_v + "n",  VOWEL_RE, rules) # abl
        sfx_ki(flag, "0", poss_s + "n" + acc_v + "n",   VOWEL_RE, rules)      # gen
        sfx_copula(flag, "0", poss_s + "yl" + loc_v,        VOWEL_RE, rules) # ins

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
            sfx_copula(flag, "0", base_poss + loc_v,        cond, rules)
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
            sfx_copula(flag, "0", base_poss + loc_v,        cond, rules)
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
             ("unuz" if rounded and back else ("iniz" if not back and not rounded else "ünüz"))
        m  = "nız" if back and not rounded else ("nuz" if rounded and back else ("niz" if not back and not rounded else "nüz"))

        eq_v = "ca" if back else "ce"
        rules = []
        for base_poss, cond in [(sg, CONS_RE), (m, VOWEL_RE)]:
            sfx_copula(flag, "0", base_poss, cond, rules)
            rules.append(sfx(flag, "0", base_poss + acc_v,        cond))
            sfx_copula(flag, "0", base_poss + loc_v,        cond, rules)
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
        r_flat = harmonize("oda", cop_tmpl)
        r_round = harmonize("kutu", cop_tmpl)
        if r_flat: rules.append(sfx(flag, "0", r_flat, "[aıâ]"))
        if r_round: rules.append(sfx(flag, "0", r_round, "[ouû]"))
    for cop_tmpl in COPULAS_CONS:
        r_flat = harmonize("bak", cop_tmpl)
        r_round = harmonize("uç", cop_tmpl)
        
        if cop_tmpl.startswith('d'):
            cond_suffix = "[^aeıioöuüAEIİOÖUÜÂÎÛçfhkpsşt]" # Voiced consonant
        elif cop_tmpl.startswith('t'):
            cond_suffix = "[çfhkpsşt]" # Unvoiced consonant
        else:
            cond_suffix = "[^aeıioöuüAEIİOÖUÜÂÎÛ]" # Any consonant

        if r_flat:
            rules.append(sfx(flag, "0", r_flat, f"[aıâ]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_flat, f"[aıâ][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
        if r_round:
            rules.append(sfx(flag, "0", r_round, f"[ouû]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_round, f"[ouû][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
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
        r_flat = harmonize("kedi", cop_tmpl)
        r_round = harmonize("ütü", cop_tmpl)
        if r_flat: rules.append(sfx(flag, "0", r_flat, "[eiaâî]"))
        if r_round: rules.append(sfx(flag, "0", r_round, "[öüouû]"))
    for cop_tmpl in COPULAS_CONS:
        r_flat = harmonize("ev", cop_tmpl)
        r_round = harmonize("gör", cop_tmpl)
        
        if cop_tmpl.startswith('d'):
            cond_suffix = "[^aeıioöuüAEIİOÖUÜÂÎÛçfhkpsşt]" # Voiced consonant
        elif cop_tmpl.startswith('t'):
            cond_suffix = "[çfhkpsşt]" # Unvoiced consonant
        else:
            cond_suffix = "[^aeıioöuüAEIİOÖUÜÂÎÛ]" # Any consonant

        if r_flat:
            rules.append(sfx(flag, "0", r_flat, f"[eiaâî]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_flat, f"[eiaâî][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
        if r_round:
            rules.append(sfx(flag, "0", r_round, f"[öüouû]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_round, f"[öüouû][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
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
    """-lI adjective derivation"""
    stems = [
        # Vowel endings
        ("[aıâ]", "lı", "B3"),
        ("[ouû]", "lu", "B4"),
        ("[eiîâ]", "li", "F3"),
        ("[öüû]", "lü", "F4"),
        # Consonant endings (single consonant)
        ("[aıâ][^aeıioöuüâîû]", "lı", "B3"),
        ("[ouû][^aeıioöuüâîû]", "lu", "B4"),
        ("[eiîâ][^aeıioöuüâîû]", "li", "F3"),
        ("[öüû][^aeıioöuüâîû]", "lü", "F4"),
        # Double consonant endings
        ("[aıâ][^aeıioöuüâîû][^aeıioöuüâîû]", "lı", "B3"),
        ("[ouû][^aeıioöuüâîû][^aeıioöuüâîû]", "lu", "B4"),
        ("[eiîâ][^aeıioöuüâîû][^aeıioöuüâîû]", "li", "F3"),
        ("[öüû][^aeıioöuüâîû][^aeıioöuüâîû]", "lü", "F4"),
    ]
    rules = []
    for cond, suf, sc in stems:
        rules.append(sfx(flag, "0", f"{suf}/{get_noun_chain(sc)[2:]}", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_sz(flag: str = "SZ") -> str:
    """-sIz (without) derivation"""
    rules = []
    for cond, suf, sc in [
        ("[aıouâû]", "sız", "B1"), ("[eiöüîâû]", "siz", "F1"),
        ("[aıâ][^aeıioöuüâîû]", "sız", "B1"), ("[ouû][^aeıioöuüâîû]", "suz", "B2"),
        ("[eiîâ][^aeıioöuüâîû]", "siz", "F1"), ("[öüû][^aeıioöuüâîû]", "süz", "F2"),
        # Two-consonant endings
        ("[aıâ][^aeıioöuüâîû][^aeıioöuüâîû]", "sız", "B1"), ("[ouû][^aeıioöuüâîû][^aeıioöuüâîû]", "suz", "B2"),
        ("[eiîâ][^aeıioöuüâîû][^aeıioöuüâîû]", "siz", "F1"), ("[öüû][^aeıioöuüâîû][^aeıioöuüâîû]", "süz", "F2"),
    ]:
        rules.append(sfx(flag, "0", f"{suf}/{get_noun_chain(sc)[2:]}", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_sl(flag: str = "SL") -> str:
    """-sAl adjective derivation"""
    rules = []
    for cond, suf, sc in [
        ("[aıouâû]",             "sal", "B1"),
        ("[eiöüîâû]",             "sel", "F1"),
        ("[aıouâû][^aeıioöuüâîû]",  "sal", "B1"),
        ("[eiöüîâû][^aeıioöuüâîû]",  "sel", "F1"),
        # Two-consonant endings
        ("[aıouâû][^aeıioöuüâîû][^aeıioöuüâîû]",  "sal", "B1"),
        ("[eiöüîâû][^aeıioöuüâîû][^aeıioöuüâîû]",  "sel", "F1"),
    ]:
        rules.append(sfx(flag, "0", f"{suf}/{get_noun_chain(sc)[2:]}", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_lk(flag: str = "LK") -> str:
    """-lIk abstract noun derivation + two-stage flag chaining"""
    rules = []
    for cond, suf, suf_v, sc in [
        ("[aıâ][^aeıioöuüâîû]", "lık", "lığ", "B1"),
        ("[ouû][^aeıioöuüâîû]", "luk", "luğ", "B2"),
        ("[eiîâ][^aeıioöuüâîû]", "lik", "liğ", "F1"),
        ("[öüû][^aeıioöuüâîû]", "lük", "lüğ", "F2"),
        ("[aıâ]",            "lık", "lığ", "B1"),
        ("[ouû]",            "luk", "luğ", "B2"),
        ("[eiîâ]",            "lik", "liğ", "F1"),
        ("[öüû]",            "lük", "lüğ", "F2"),
        # Two-consonant stems support
        ("[aıâ][^aeıioöuüâîû][^aeıioöuüâîû]", "lık", "lığ", "B1"),
        ("[ouû][^aeıioöuüâîû][^aeıioöuüâîû]", "luk", "luğ", "B2"),
        ("[eiîâ][^aeıioöuüâîû][^aeıioöuüâîû]", "lik", "liğ", "F1"),
        ("[öüû][^aeıioöuüâîû][^aeıioöuüâîû]", "lük", "lüğ", "F2"),
    ]:
        rules.append(sfx(flag, "0", f"{suf}/{get_noun_chain(sc, only_consonant=True)[2:]}", cond))
        rules.append(sfx(flag, "0", f"{suf_v}/{get_noun_chain(sc, only_vowel=True)}NE", cond))
    return make_flag_block(flag, unique(rules))



def gen_deriv_ci(flag: str = "CI") -> str:
    """-CI agentive/occupational noun derivation"""
    rules = []
    for cond, suf, sc in [
        ("[aıâ][^çfhkpsşt]", "cı", "B3"), ("[ouû][^çfhkpsşt]", "cu", "B4"),
        ("[eiîâ][^çfhkpsşt]", "ci", "F3"), ("[öüû][^çfhkpsşt]", "cü", "F4"),
        ("[aıâ][çfhkpsşt]",  "çı", "B3"), ("[ouû][çfhkpsşt]",  "çu", "B4"),
        ("[eiîâ][çfhkpsşt]",  "çi", "F3"), ("[öüû][çfhkpsşt]",  "çü", "F4"),
        ("[aıâ]", "cı", "B3"), ("[ouû]", "cu", "B4"), ("[eiîâ]", "ci", "F3"), ("[öüû]", "cü", "F4"),
        # Two-consonant endings
        ("[aıâ][^aeıioöuüâîû][^çfhkpsşt]", "cı", "B3"), ("[ouû][^aeıioöuüâîû][^çfhkpsşt]", "cu", "B4"),
        ("[eiîâ][^aeıioöuüâîû][^çfhkpsşt]", "ci", "F3"), ("[öüû][^aeıioöuüâîû][^çfhkpsşt]", "cü", "F4"),
        ("[aıâ][^aeıioöuüâîû][çfhkpsşt]",  "çı", "B3"), ("[ouû][^aeıioöuüâîû][çfhkpsşt]",  "çu", "B4"),
        ("[eiîâ][^aeıioöuüâîû][çfhkpsşt]",  "çi", "F3"), ("[öüû][^aeıioöuüâîû][çfhkpsşt]",  "çü", "F4"),
    ]:
        rules.append(sfx(flag, "0", f"{suf}/{get_noun_chain(sc)[2:]}", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_ck(flag: str = "CK") -> str:
    """-cIk diminutive"""
    rules = []
    for cond, suf in [
        ("[aıâ][^çfhkpsşt]", "cık"), ("[ouû][^çfhkpsşt]", "cuk"),
        ("[eiîâ][^çfhkpsşt]", "cik"), ("[öüû][^çfhkpsşt]", "cük"),
        ("[aıâ][çfhkpsşt]",  "çık"), ("[ouû][çfhkpsşt]",  "çuk"),
        ("[eiîâ][çfhkpsşt]",  "çik"), ("[öüû][çfhkpsşt]",  "çük"),
        ("[aıâ]", "cık"), ("[ouû]", "cuk"), ("[eiîâ]", "cik"), ("[öüû]", "cük"),
        # Two-consonant endings
        ("[aıâ][^aeıioöuüâîû][^çfhkpsşt]", "cık"), ("[ouû][^aeıioöuüâîû][^çfhkpsşt]", "cuk"),
        ("[eiîâ][^aeıioöuüâîû][^çfhkpsşt]", "cik"), ("[öüû][^aeıioöuüâîû][^çfhkpsşt]", "cük"),
        ("[aıâ][^aeıioöuüâîû][çfhkpsşt]",  "çık"), ("[ouû][^aeıioöuüâîû][çfhkpsşt]",  "çuk"),
        ("[eiîâ][^aeıioöuüâîû][çfhkpsşt]",  "çik"), ("[öüû][^aeıioöuüâîû][çfhkpsşt]",  "çük"),
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
        ("[aıâ]",                  "laş", "laşmak"),
        ("[ouû]",                  "laş", "laşmak"),
        ("[eiîâ]",                  "leş", "leşmek"),
        ("[öüû]",                  "leş", "leşmek"),
        ("[aıâ][^aeıioöuüâîû]",       "laş", "laşmak"),
        ("[ouû][^aeıioöuüâîû]",       "laş", "laşmak"),
        ("[eiîâ][^aeıioöuüâîû]",       "leş", "leşmek"),
        ("[öüû][^aeıioöuüâîû]",       "leş", "leşmek"),
        # Two-consonant endings
        ("[aıâ][^aeıioöuüâîû][^aeıioöuüâîû]",       "laş", "laşmak"),
        ("[ouû][^aeıioöuüâîû][^aeıioöuüâîû]",       "laş", "laşmak"),
        ("[eiîâ][^aeıioöuüâîû][^aeıioöuüâîû]",       "leş", "leşmek"),
        ("[öüû][^aeıioöuüâîû][^aeıioöuüâîû]",       "leş", "leşmek"),
    ]:
        verb_flag = "Vb" if "a" in suf else "Vf"
        rules.append(sfx(flag, "0", f"{verb_inf}/{verb_flag}", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_las_tir(flag: str = "DT") -> str:
    """-lAştIr causative verb-forming derivation"""
    rules = []
    for cond, suf in [
        ("[aıouâû]",             "laştır"),
        ("[eiöüîâû]",             "leştir"),
        ("[aıouâû][^aeıioöuüâîû]",  "laştır"),
        ("[eiöüîâû][^aeıioöuüâîû]",  "leştir"),
        # Two-consonant endings
        ("[aıouâû][^aeıioöuüâîû][^aeıioöuüâîû]",  "laştır"),
        ("[eiöüîâû][^aeıioöuüâîû][^aeıioöuüâîû]",  "leştir"),
    ]:
        verb_flag = "Vb" if "ı" in suf else "Vf"
        inf_suf = "mak" if verb_flag == "Vb" else "mek"
        rules.append(sfx(flag, "0", f"{suf}{inf_suf}/{verb_flag}", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_len(flag: str = "DE") -> str:
    """-lAn reflexive/passive verb-forming derivation"""
    rules = []
    for cond, suf in [
        ("[aıouâû]",             "lan"),
        ("[eiöüîâû]",             "len"),
        ("[aıouâû][^aeıioöuüâîû]",  "lan"),
        ("[eiöüîâû][^aeıioöuüâîû]",  "len"),
        # Two-consonant endings
        ("[aıouâû][^aeıioöuüâîû][^aeıioöuüâîû]",  "lan"),
        ("[eiöüîâû][^aeıioöuüâîû][^aeıioöuüâîû]",  "len"),
    ]:
        verb_flag = "Vb" if "a" in suf else "Vf"
        inf_suf = "mak" if verb_flag == "Vb" else "mek"
        rules.append(sfx(flag, "0", f"{suf}{inf_suf}/{verb_flag}", cond))
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

def generate_rep_rules() -> list[tuple[str, str]]:
    rep_list = []
    
    # 1. Base typographic & phonological character substitutions
    char_reps = [
        # Circumflex pairs (priority)
        ("a", "â"), ("â", "a"), ("u", "û"), ("û", "u"), ("i", "î"), ("î", "i"),
        ("A", "Â"), ("Â", "A"), ("U", "Û"), ("Û", "U"), ("İ", "Î"), ("Î", "İ"),
        # De-ASCII lowercase & uppercase character swaps
        ("c", "ç"), ("ç", "c"), ("g", "ğ"), ("ğ", "g"), ("s", "ş"), ("ş", "s"),
        ("o", "ö"), ("ö", "o"), ("u", "ü"), ("ü", "u"), ("ı", "i"), ("i", "ı"),
        ("C", "Ç"), ("Ç", "C"), ("G", "Ğ"), ("Ğ", "G"), ("S", "Ş"), ("Ş", "S"),
        ("O", "Ö"), ("Ö", "O"), ("U", "Ü"), ("Ü", "U"), ("I", "İ"), ("İ", "I"), ("I", "I"),
        # Multi-char typography & phonology
        ("sh", "ş"), ("ch", "ç"), ("gh", "ğ"), ("ss", "ş"),
        ("dd", "t"), ("tt", "d"), ("bb", "p"), ("pp", "b"), ("cc", "c"), ("kk", "g"),
        ("ğ", "y"), ("y", "ğ"), ("h", "ğ"), ("ğ", "h"),
        ("a", "e"), ("e", "a"), ("d", "t"), ("t", "d"), ("p", "b"), ("b", "p"),
        ("z", "s"), ("s", "z"), ("k", "g"), ("g", "k"),
        ("ın", "in"), ("in", "ın"), ("un", "ün"), ("ün", "un"),
        ("da", "de"), ("de", "da"), ("lar", "ler"), ("ler", "lar"),
        ("la", "le"), ("le", "la"), ("’", "'"),
        # Common de-ASCII suffix clusters
        ("lari", "ları"), ("larin", "ların"), ("larimi", "larımı"), ("lariniz", "larınız"),
        ("sutcu", "şütçü"), ("sucu", "şücü"), ("tcu", "tçü"), ("biliyor", "biliyor")
    ]
    for src, dst in char_reps:
        rep_list.append((src, dst))
        
    # 2. Common Lexical Typos
    lexical_typos = [
        ("yanlız", "yalnız"),
        ("yalnış", "yanlış"),
        ("herkez", "herkes"),
        ("şarz", "şarj"),
        ("kirbit", "kibrit"),
        ("pantalon", "pantolon"),
        ("şöför", "şoför"),
        ("egsoz", "egzoz"),
        ("sarmısak", "sarımsak"),
        ("entellektüel", "entelektüel"),
        ("vejeteryan", "vejetaryen"),
        ("insiyatif", "inisiyatif"),
        ("orjinal", "orijinal"),
        ("dinazor", "dinozor"),
        ("klavuz", "kılavuz"),
        ("muhattap", "muhatap"),
        ("idda", "iddaa"),
        ("klüp", "kulüp"),
        ("mualif", "muhalif"),
        ("seftali", "şeftali"),
        ("direk", "direkt"),
        ("makina", "makine"),
        ("meyva", "meyve"),
        ("süpriz", "sürpriz"),
        ("eskişehir", "Eskişehir"),
        ("anadolu", "Anadolu"),
        ("atatürk'ün", "Atatürk'ün"),
        ("Atatürkün", "Atatürk'ün"),
        ("Türkün", "Türk'ün"),
        ("türkten", "Türk'ten"),
        ("istihbarat", "istihbarat"),
        # V2 failure analysis patterns
        ("attır", "arttır"),
        ("attir", "arttir"),
        ("attur", "arttur"),
        ("attür", "arttür"),
        ("wayr", "ayr"),
        ("wair", "air"),
        ("xin", "sin"),
        ("xır", "sır"),
        ("yk", "k"),
        ("yb", "b"),
        ("oligo", "oligar"),
    ]
    for src, dst in lexical_typos:
        rep_list.append((src, dst))
        
    # 3. Morphological Typos (Vowel Drop, Voicing, soft-l loans)
    voicing_stems = [
        ("kitap", "kitab", ["ı", "ın", "a", "ımız", "ınız"]),
        ("ağaç", "ağac", ["ı", "ın", "a", "ımız", "ınız"]),
        ("çocuk", "çocuğ", ["u", "un", "a", "umuz", "unuz"]),
        ("kâğıt", "kâğıd", ["ı", "ın", "a", "ımız", "ınız"]),
        ("borç", "borc", ["u", "un", "a", "umuz", "unuz"]),
        ("renk", "reng", ["i", "in", "e", "imiz", "iniz"]),
        ("kalp", "kalb", ["i", "in", "e", "imiz", "iniz"])
    ]
    for unv, voiced, suffixes in voicing_stems:
        for s in suffixes:
            rep_list.append((f"{unv}{s}", f"{voiced}{s}"))
            
    drop_stems = [
        ("akıl", "akl", ["ı", "ın", "a", "ımız", "ınız"]),
        ("ağız", "ağz", ["ı", "ın", "a", "ımız", "ınız"]),
        ("şehir", "şehr", ["i", "in", "e", "imiz", "iniz"]),
        ("ömür", "ömr", ["ü", "ün", "e", "ümüz", "ünüz"]),
        ("resim", "resm", ["i", "in", "e", "imiz", "iniz"]),
        ("burun", "burn", ["u", "un", "a", "umuz", "unuz"]),
        ("karın", "karn", ["ı", "ın", "a", "ımız", "ınız"]),
        ("zehir", "zehr", ["i", "in", "e", "imiz", "iniz"])
    ]
    for full, dropped, suffixes in drop_stems:
        for s in suffixes:
            rep_list.append((f"{full}{s}", f"{dropped}{s}"))
            
    soft_loans = [
        ("saat", ["ler", "le", "leri", "lerin", "lerinizin", "lerimizin", "e", "i", "in"]),
        ("hâl", ["ler", "le", "leri", "lerin", "e", "i", "in"]),
        ("rol", ["ler", "le", "leri", "lerin", "e", "ü", "ün"]),
        ("alkol", ["ler", "le", "leri", "lerin", "e", "ü", "ün"]),
        ("metal", ["ler", "le", "leri", "lerin", "e", "i", "in"]),
        ("kontrol", ["ler", "le", "leri", "lerin", "e", "ü", "ün"])
    ]
    
    harmony_map = {
        "lar": "ler", "la": "le", "ları": "leri", "ların": "lerin", 
        "larının": "lerinin", "larımızın": "lerimizin", "larınızın": "lerinizin",
        "a": "e", "ı": "i", "ın": "in", "u": "ü", "un": "ün"
    }
    for stem, suffixes in soft_loans:
        for corr_s in suffixes:
            for back_s, front_s in harmony_map.items():
                if corr_s == front_s:
                    rep_list.append((f"{stem}{back_s}", f"{stem}{corr_s}"))
                    
    circumflex_typos = [
        ("hal", "hâl"), ("hala", "hâlâ"), ("adet", "âdet"), ("alem", "âlem"),
        ("dahi", "dâhi"), ("sura", "şûra"), ("kagit", "kâğıt"), ("kağıt", "kâğıt"),
        ("ruzgar", "rüzgâr"), ("rüzgar", "rüzgâr"), ("tezgah", "tezgâh"),
        ("dukkan", "dükkân"), ("mahkum", "mahkûm"), ("alim", "âlim"), ("hakimevi", "hâkimevi")
    ]
    for src, dst in circumflex_typos:
        rep_list.append((src, dst))
        
    return rep_list


def generate_header() -> str:
    rep_pairs = generate_rep_rules()
    rep_lines = [f"REP {len(rep_pairs)}"]
    for src, dst in rep_pairs:
        rep_lines.append(f"REP {src} {dst}")
    rep_block = "\n".join(rep_lines)

    return f"""# Türkçe Yazım Denetimi Sözlüğü - Chained Flags Architecture
SET UTF-8
FLAG long
NOSUGGEST NS
KEEPCASE KC
NEEDAFFIX NE
LANG tr
WORDCHARS '’‘.

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
MAP 18
MAP aâAÂ
MAP uûUÛ
MAP iîİÎ
MAP cçCÇ
MAP gğGĞ
MAP sşSŞ
MAP oöOÖ
MAP uüUÜ
MAP ıiIİ
MAP '’‘
MAP 0o0ö0O0Ö
MAP 3e3E
MAP 4r4e4R4E
MAP 5t5r5T5R
MAP 6y6t6Y6T
MAP 7u7y7U7Y
MAP 8i8u8İ8U
MAP 9o9i9O9İ
MAXDIFF 3
MAXNGRAMSUGS 4

{rep_block}
"""


def generate_grammar():
    """Main entry point — generates the new chained tr.aff."""
    import os
    _build_dir = os.path.dirname(os.path.abspath(__file__))
    _root_dir = os.path.dirname(_build_dir)  # project root (one level up from build/)
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
    print("Generating derivation flags (LI, SZ, LK, CI, CK, SL)...")
    content += "\n# DERIVATION FLAGS (1ST-LEVEL)\n"
    content += gen_deriv_li() + "\n"
    content += gen_deriv_sz() + "\n"
    content += gen_deriv_lk() + "\n"
    content += gen_deriv_ci() + "\n"
    content += gen_deriv_ck() + "\n"
    content += gen_deriv_sl() + "\n"

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

    # --- Voicing Copula flags ---
    print("Generating Voicing Copula flags (VC, vc)...")
    content += "\n# VOICING COPULA FLAGS\n"
    for block in gen_voicing_copula_flags():
        content += block + "\n"

    print("Writing tr.aff...")
    with open(os.path.join(_root_dir, 'tr.aff'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

    # Count rules
    total_sfx = content.count('\nSFX ')
    print(f"Done. Total SFX rules: {total_sfx}")
    import os as _os
    size_kb = _os.path.getsize(os.path.join(_root_dir, 'tr.aff')) / 1024
    print(f"tr.aff size: {size_kb:.1f} KB")


def gen_proper_flags() -> list[str]:
    """Generate apostrophe-suffix flags for proper nouns.

    Turkish proper nouns take case/possessive suffixes separated from the
    base by an apostrophe (e.g. İstanbul'un, Ankara'da, Türkiye'de).
    The suffix vowel harmony depends on the last vowel of the proper noun:

      Family | Last vowel | Consonant-end example | Vowel-end example
      -------|-----------|-----------------------|------------------
      BU     | a / ı     | İstanbul, Atatürk     | Ankara
      BR     | o / u     | Ordu, Bolu            | Kongo
      FU     | e / i     | Edirne → cons: kent   | Türkiye, İzmir
      FR     | ö / ü     | Gümüş, Göl            | Söke

    Each family gets:
      - pN  : genitive   ('nın / 'nun / 'nin / 'nün  after vowel;
                           'ın  / 'un  / 'in  / 'ün   after consonant)
      - pL  : locative   ('da / 'ta  or  'de / 'te)
      - pR  : ablative   ('dan / 'tan  or  'den / 'ten)
      - pY  : dative     ('a / 'e)
      - pA  : accusative ('ı / 'u / 'i / 'ü)
      - pI  : instrumental ('la / 'le)
      - pP  : 3sg poss   ('ı/'sı  or  'u/'su  or  'i/'si  or  'ü/'sü)
      - pC  : copula     ('dır/'tır/'dir/'tir …)
    """
    blocks = []

    # -----------------------------------------------------------------------
    # Helper: build one complete proper-noun flag set for a given harmony
    # -----------------------------------------------------------------------
    def _proper_family(
        flag_prefix: str,      # e.g. "pB" for back-unrounded
        gen_cons: str,         # genitive suffix after consonant: 'ın / 'un / 'in / 'ün
        gen_vowel: str,        # genitive suffix after vowel:     'nın / 'nun / 'nin / 'nün
        loc_soft: str,         # locative soft:  'da / 'de
        loc_hard: str,         # locative hard:  'ta / 'te
        abl_soft: str,         # ablative soft:  'dan / 'den
        abl_hard: str,         # ablative hard:  'tan / 'ten
        dat_cons: str,         # dative after consonant: 'a / 'e
        dat_vowel: str,        # dative after vowel:     'ya / 'ye
        acc_cons: str,         # accusative after consonant: 'ı / 'u / 'i / 'ü
        acc_vowel: str,        # accusative after vowel:     'yı / 'yu / 'yi / 'yü
        poss3_cons: str,       # 3sg poss after consonant:  'ı / 'u / 'i / 'ü
        poss3_vowel: str,      # 3sg poss after vowel:      'sı / 'su / 'si / 'sü
        poss3_gen: str,        # 3sg poss gen:  'ının / 'unun / 'inin / 'ünün
        poss3_dat: str,        # 3sg poss dat:  'ına / 'una / 'ine / 'üne
        poss3_loc: str,        # 3sg poss loc:  'ında / 'unda / 'inde / 'ünde
        poss3_abl: str,        # 3sg poss abl:  'ından / 'undan / 'inden / 'ünden
        ins_suf: str,          # instrumental:  'la / 'le
        cop_suffix: str,       # copula stem vowel for harmonize(): 'a' or 'e'
    ):
        # --- Genitive flag ---
        rules_N = []
        sfx_ki(f"{flag_prefix}N", "0", f"'{gen_cons}",   CONS_RE, rules_N)
        sfx_ki(f"{flag_prefix}N", "0", f"'{gen_vowel}",  VOWEL_RE,  rules_N)
        if flag_prefix == "pB":
            sfx_ki(f"{flag_prefix}N", "0", f"'{gen_cons}",   "[eıiEİ]", rules_N)
        if flag_prefix == "pF":
            sfx_ki(f"{flag_prefix}N", "0", f"'{gen_cons}",   ".", rules_N)
            sfx_ki(f"{flag_prefix}N", "0", f"'ın",          ".", rules_N)
            sfx_ki(f"{flag_prefix}N", "0", f"'un",          ".", rules_N)
            sfx_ki(f"{flag_prefix}N", "0", f"'{gen_vowel}",  "tl",          rules_N)
            sfx_ki(f"{flag_prefix}N", "0", f"'{gen_vowel}",  "TL",          rules_N)
        for cond_pattern in ("[A-Z]", "km", "cm", "mm"):
            sfx_ki(f"{flag_prefix}N", "0", f"'{gen_vowel}", cond_pattern, rules_N)
        blocks.append(make_flag_block(f"{flag_prefix}N", unique(rules_N)))

        # --- Locative flag ---
        rules_L = []
        sfx_ki(f"{flag_prefix}L", "0", f"'{loc_soft}", "[^çfhkpsşt]", rules_L)
        sfx_ki(f"{flag_prefix}L", "0", f"'{loc_hard}", "[çfhkpsşt]", rules_L)
        sfx_ki(f"{flag_prefix}L", "0", f"'n{loc_soft}", VOWEL_RE, rules_L)
        for cond_pattern in ("[A-Z]", "km", "cm", "mm"):
            sfx_ki(f"{flag_prefix}L", "0", f"'n{loc_soft}", cond_pattern, rules_L)
        blocks.append(make_flag_block(f"{flag_prefix}L", unique(rules_L)))

        # --- Ablative flag ---
        rules_R = [
            sfx(f"{flag_prefix}R", "0", f"'{abl_soft}/cl", "[^çfhkpsşt]"),
            sfx(f"{flag_prefix}R", "0", f"'{abl_hard}/cl", "[çfhkpsşt]"),
            sfx(f"{flag_prefix}R", "0", f"'n{abl_soft}/cl", VOWEL_RE),
        ]
        for cond_pattern in ("[A-Z]", "km", "cm", "mm"):
            rules_R.append(sfx(f"{flag_prefix}R", "0", f"'n{abl_soft}/cl", cond_pattern))
        blocks.append(make_flag_block(f"{flag_prefix}R", unique(rules_R)))

        # --- Dative flag ---
        rules_Y = [
            sfx(f"{flag_prefix}Y", "0", f"'{dat_cons}",  CONS_RE),
            sfx(f"{flag_prefix}Y", "0", f"'{dat_vowel}", VOWEL_RE),
            sfx(f"{flag_prefix}Y", "0", f"'n{dat_cons}",  VOWEL_RE),
        ]
        if flag_prefix == "pB":
            rules_Y.append(sfx(f"{flag_prefix}Y", "0", f"'{dat_cons}",  "[eıiEİ]"))
        if flag_prefix == "pF":
            rules_Y.append(sfx(f"{flag_prefix}Y", "0", f"'{dat_cons}",  "."))
            rules_Y.append(sfx(f"{flag_prefix}Y", "0", f"'a",          "."))
            rules_Y.append(sfx(f"{flag_prefix}Y", "0", f"'{dat_vowel}", "tl"))
            rules_Y.append(sfx(f"{flag_prefix}Y", "0", f"'{dat_vowel}", "TL"))
        for cond_pattern in ("[A-Z]", "km", "cm", "mm"):
            rules_Y.append(sfx(f"{flag_prefix}Y", "0", f"'{dat_vowel}", cond_pattern))
        blocks.append(make_flag_block(f"{flag_prefix}Y", unique(rules_Y)))

        # --- Accusative flag ---
        rules_A = [
            sfx(f"{flag_prefix}A", "0", f"'{acc_cons}",  CONS_RE),
            sfx(f"{flag_prefix}A", "0", f"'{acc_vowel}", VOWEL_RE),
            sfx(f"{flag_prefix}A", "0", f"'n{acc_cons}",  VOWEL_RE),
        ]
        if flag_prefix == "pB":
            rules_A.append(sfx(f"{flag_prefix}A", "0", f"'{acc_cons}",  "[eıiEİ]"))
        if flag_prefix == "pF":
            rules_A.append(sfx(f"{flag_prefix}A", "0", f"'{acc_cons}",  "."))
            rules_A.append(sfx(f"{flag_prefix}A", "0", f"'ı",          "."))
            rules_A.append(sfx(f"{flag_prefix}A", "0", f"'{acc_vowel}", "tl"))
            rules_A.append(sfx(f"{flag_prefix}A", "0", f"'{acc_vowel}", "TL"))
        for cond_pattern in ("[A-Z]", "km", "cm", "mm"):
            rules_A.append(sfx(f"{flag_prefix}A", "0", f"'{acc_vowel}", cond_pattern))
        blocks.append(make_flag_block(f"{flag_prefix}A", unique(rules_A)))

        # --- Instrumental flag ---
        rules_I = [
            sfx(f"{flag_prefix}I", "0", f"'{ins_suf}/cl", CONS_RE),
            sfx(f"{flag_prefix}I", "0", f"'y{ins_suf}/cl", VOWEL_RE),
        ]
        for cond_pattern in ("[A-Z]", "km", "cm", "mm"):
            rules_I.append(sfx(f"{flag_prefix}I", "0", f"'y{ins_suf}/cl", cond_pattern))
        blocks.append(make_flag_block(f"{flag_prefix}I", unique(rules_I)))

        # --- 3sg possessive flag ---
        rules_P = [
            sfx(f"{flag_prefix}P", "0", f"'{poss3_cons}/cl",  CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_vowel}/cl", VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_gen}",  CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_dat}",  CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_loc}",  CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_abl}/cl", CONS_RE),
        ]
        sfx_ki(f"{flag_prefix}P", "0", f"'{poss3_loc}",  CONS_RE, rules_P)
        sfx_ki(f"{flag_prefix}P", "0", f"'{poss3_gen}",  CONS_RE, rules_P)
        if flag_prefix == "pF":
            rules_P.append(sfx(f"{flag_prefix}P", "0", f"'{poss3_vowel}/cl", "tl"))
            rules_P.append(sfx(f"{flag_prefix}P", "0", f"'{poss3_vowel}/cl", "TL"))
        for cond_pattern in ("[A-Z]", "km", "cm", "mm"):
            rules_P.append(sfx(f"{flag_prefix}P", "0", f"'{poss3_vowel}/cl", cond_pattern))
        blocks.append(make_flag_block(f"{flag_prefix}P", unique(rules_P)))

        # --- Copula flag ---
        COPULAS_PROP = [
            "'dI", "'dIm", "'dIn", "'dIk", "'dInIz", "'dIlAr",
            "'tI", "'tIm", "'tIn", "'tIk", "'tInIz", "'tIlAr",
            "'mIş", "'mIşIm", "'mIşsIn", "'mIşIz", "'mIşsInIz", "'mIşlAr",
            "'sA", "'sAm", "'sAn", "'sAk", "'sAnIz", "'sAlAr",
            "'Im", "'sIn", "'Iz", "'sInIz", "'lAr",
            "'dIr", "'tIr", "'dIrlAr", "'tIrlAr", "'lArdIr", "'ken",
            "'ImdIr", "'sIndIr", "'IzdIr", "'sInIzdIr",
            # Add proper noun possessive forms and their case inflections (e.g. Güneş'imizin, Dünya'mızın)
            # 1sg possessives (consonant-ending stem)
            "'Im", "'ImIn", "'ImA", "'ImI", "'ImdA", "'ImdAn", "'ImlA",
            # 2sg possessives (consonant-ending stem)
            "'In", "'InIn", "'InA", "'InI", "'IndA", "'IndAn", "'InlA",
            # 1pl possessives (consonant-ending stem)
            "'ImIz", "'ImIzIn", "'ImIzA", "'ImIzI", "'ImIzdA", "'ImIzdAn", "'ImIzlA",
            # 2pl possessives (consonant-ending stem)
            "'InIz", "'InIzIn", "'InIzA", "'InIzI", "'InIzdA", "'InIzdAn", "'InIzlA",
            # 3pl possessives
            "'lArI", "'lArInI", "'lArInA", "'lArIndA", "'lArIndAn", "'lArInIn", "'lArIylA",
            "'lArIn", "'lArA", "'lArdA", "'lArdAn", "'lArlA",
            # Plural locative relative-ki (e.g. server'lardaki, server'larındaki)
            "'lArdAki", "'lArdAkiler", "'lArdAkilerden", "'lArdAkileri",
            "'lArIndAki", "'lArIndAkiler",
            # 1sg possessives (vowel-ending stem)
            "'m", "'mIn", "'mA", "'mI", "'mdA", "'mdAn", "'mlA",
            # 2sg possessives (vowel-ending stem)
            "'n", "'nIn", "'nA", "'nI", "'ndA", "'ndAn", "'nlA",
            # 1pl possessives (vowel-ending stem)
            "'mIz", "'mIzIn", "'mIzA", "'mIzI", "'mIzdA", "'mIzdAn", "'mIzlA",
            # 2pl possessives (vowel-ending stem)
            "'nIz", "'nIzIn", "'nIzA", "'nIzI", "'nIzdA", "'nIzdAn", "'nIzlA"
        ]
        rules_C = []
        for cop_tmpl in COPULAS_PROP:
            resolved = harmonize(cop_suffix, cop_tmpl)
            if resolved:
                rules_C.append(sfx(f"{flag_prefix}C", "0", resolved, "."))
        blocks.append(make_flag_block(f"{flag_prefix}C", unique(rules_C)))

    # -----------------------------------------------------------------------
    # Family BU: back-unrounded (last vowel a/ı) – e.g. İstanbul, Ankara
    # -----------------------------------------------------------------------
    _proper_family(
        flag_prefix="pB",
        gen_cons="ın",    gen_vowel="nın",
        loc_soft="da",    loc_hard="ta",
        abl_soft="dan",   abl_hard="tan",
        dat_cons="a",     dat_vowel="ya",
        acc_cons="ı",     acc_vowel="yı",
        poss3_cons="ı",   poss3_vowel="sı",
        poss3_gen="ının", poss3_dat="ına",
        poss3_loc="ında", poss3_abl="ından",
        ins_suf="la",
        cop_suffix="a",
    )

    # -----------------------------------------------------------------------
    # Family BR: back-rounded (last vowel o/u) – e.g. Ordu, Trabzon, Bolu
    # -----------------------------------------------------------------------
    _proper_family(
        flag_prefix="pO",
        gen_cons="un",    gen_vowel="nun",
        loc_soft="da",    loc_hard="ta",
        abl_soft="dan",   abl_hard="tan",
        dat_cons="a",     dat_vowel="ya",
        acc_cons="u",     acc_vowel="yu",
        poss3_cons="u",   poss3_vowel="su",
        poss3_gen="unun", poss3_dat="una",
        poss3_loc="unda", poss3_abl="undan",
        ins_suf="la",
        cop_suffix="u",
    )

    # -----------------------------------------------------------------------
    # Family FU: front-unrounded (last vowel e/i) – e.g. Türkiye, İzmir
    # -----------------------------------------------------------------------
    _proper_family(
        flag_prefix="pF",
        gen_cons="in",    gen_vowel="nin",
        loc_soft="de",    loc_hard="te",
        abl_soft="den",   abl_hard="ten",
        dat_cons="e",     dat_vowel="ye",
        acc_cons="i",     acc_vowel="yi",
        poss3_cons="i",   poss3_vowel="si",
        poss3_gen="inin", poss3_dat="ine",
        poss3_loc="inde", poss3_abl="inden",
        ins_suf="le",
        cop_suffix="e",
    )

    # -----------------------------------------------------------------------
    # Family FR: front-rounded (last vowel ö/ü) – e.g. Gümüşhane, Söke
    # -----------------------------------------------------------------------
    _proper_family(
        flag_prefix="pU",
        gen_cons="ün",    gen_vowel="nün",
        loc_soft="de",    loc_hard="te",
        abl_soft="den",   abl_hard="ten",
        dat_cons="e",     dat_vowel="ye",
        acc_cons="ü",     acc_vowel="yü",
        poss3_cons="ü",   poss3_vowel="sü",
        poss3_gen="ünün", poss3_dat="üne",
        poss3_loc="ünde", poss3_abl="ünden",
        ins_suf="le",
        cop_suffix="ü",
    )

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
    Extract verb sections from data/tr_reference.aff and remap their flags
    from the old UTF-8 block positions to the current LONG_TO_UTF8 map.
    """
    import os
    _build_dir = os.path.dirname(os.path.abspath(__file__))
    _root_dir = os.path.dirname(_build_dir)

    from utf8_flag_mapping import LONG_TO_UTF8

    # Reconstruct the OLD flag mapping (before KC was added)
    ALL_FLAGS_OLD = sorted([
        "B1", "B2", "B3", "B4", "F1", "F2", "F3", "F4", 
        "V1", "V2", "V3", "V4", "D1", "D2", "D3", "D4", 
        "C1", "C2", "C3", "C4", "G1", "G2", "G3", "G4", 
        "NX", "PX",
        "A1", "A2", "A3", "A4", "Y1", "Y2", "L1", "L2", "R1", "R2", "N1", "N2", "N3", "N4", "I1", "I2", "Q1", "Q2",
        "a1", "a2", "a3", "a4", "y1", "y2", "n1", "n2", "n3", "n4", "i1", "i2",
        "PB", "PF",
        "PS", "PT", "PU", "PV", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "PM", "PO", "PP", "PQ", "PN", "PR", "PW", "PZ",
        "CL", "cl", "CP", "CV", "CO", "KI", "LI", "SZ", "LK", "CI", "CK", "DL", "DT", "DE",
        "uA", "uY", "uL", "uR", "uN", "uI", "uQ", "uP", "u1", "u2", "u3", "u4", "uC",
        "VB", "VR", "VF", "VG", "VA", "VS", "VE", "VH", "VK", "VL", "VM", "VN", "VY",
        "NS"
    ])
    PROPER_NOUN_FLAGS_3 = [
        f"p{fam}{sub}"
        for fam in "BOFU"
        for sub in "NLRYAIPC"
    ]
    OLD_LONG_TO_UTF8 = {}
    for idx, flag in enumerate(ALL_FLAGS_OLD):
        OLD_LONG_TO_UTF8[flag] = chr(1024 + idx)
    for idx, flag in enumerate(PROPER_NOUN_FLAGS_3):
        OLD_LONG_TO_UTF8[flag] = chr(1024 + len(ALL_FLAGS_OLD) + idx)
    OLD_UTF8_TO_LONG = {v: k for k, v in OLD_LONG_TO_UTF8.items()}

    # The long flag names for verbs
    VERB_FLAGS = {"VB", "VR", "VF", "VG", "VA", "VS", "VE", "VH", "VK", "VL", "VM", "VN", "VY"}
    
    # Map them to their OLD Cyrillic characters to locate them in tr_reference.aff
    OLD_VERB_CYRILLIC = {OLD_LONG_TO_UTF8[f] for f in VERB_FLAGS}

    def remap_old_to_new_flag_string(old_flag_str: str, prefix_str: str = "") -> str:
        if not old_flag_str:
            return ""
        old_decoded = []
        for char in old_flag_str:
            if char in OLD_UTF8_TO_LONG:
                old_decoded.append(OLD_UTF8_TO_LONG[char])
            else:
                old_decoded.append(char)
                
        if prefix_str.endswith(('mak', 'mek')):
            bad_flags = {
                'A1', 'A2', 'A3', 'A4', 'Y1', 'Y2', 'N1', 'N2', 'N3', 'N4',
                'PB', 'PF',
                'PS', 'PT', 'PU', 'PV', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8',
                'PM', 'PO', 'PP', 'PQ', 'PN', 'PR', 'PW', 'PZ'
            }
            old_decoded = [f for f in old_decoded if f not in bad_flags]
            
        if 'yor' in prefix_str:
            old_decoded = ['CL' if f == 'cl' else f for f in old_decoded]
            
        if prefix_str.endswith(('mam', 'mem', 'man', 'men', 'masi', 'mesi', 'ması', 'mamız', 'memiz', 'manız', 'meniz', 'maları', 'meleri')):
            poss_flags = {
                'PS', 'PT', 'PU', 'PV', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8',
                'PM', 'PO', 'PP', 'PQ', 'PN', 'PR', 'PW', 'PZ'
            }
            old_decoded = [f for f in old_decoded if f not in poss_flags]
            
        new_chars = []
        for f in old_decoded:
            if f in LONG_TO_UTF8:
                new_chars.append(LONG_TO_UTF8[f])
            else:
                new_chars.append(f)
        return "".join(new_chars)

    print("  Reading data/tr_reference.aff to extract and remap verb sections...")
    _ref_aff = os.path.join(_root_dir, 'data', 'tr_reference.aff')
    with open(_ref_aff, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    verb_flags_rules = {} # new_flag_char -> (combine_char, list of rules)
    verb_flags_order = []

    new_vb_char = LONG_TO_UTF8["Vb"]
    new_vf_char = LONG_TO_UTF8["Vf"]
    verb_flags_rules[new_vb_char] = ('Y', [])
    verb_flags_rules[new_vf_char] = ('Y', [])

    for line in lines:
        line_strip = line.strip()
        if not line_strip or line_strip.startswith('#'):
            continue
        parts = line_strip.split()
        if len(parts) >= 3 and parts[0] == 'SFX':
            flag_char = parts[1]
            if flag_char in OLD_VERB_CYRILLIC:
                long_flag = OLD_UTF8_TO_LONG[flag_char]
                new_flag_char = LONG_TO_UTF8[long_flag]
                
                if parts[2] in ('Y', 'N'):
                    # Header line
                    combine_char = parts[2]
                    if new_flag_char not in verb_flags_rules:
                        verb_flags_rules[new_flag_char] = (combine_char, [])
                        verb_flags_order.append(new_flag_char)
                else:
                    # Rule line
                    if len(parts) >= 4:
                        suf = parts[3].split('/')[0]
                        # Skip grammatically incorrect potential suffixes starting with 'tebil', 'tabil', 'tici', etc.
                        if suf.startswith(('tebil', 'tabil', 'tici', 'tıcı', 'tucu', 'tücü')):
                            continue
                        # Skip suffix rules with ar/er typos instead of lar/ler
                        if suf.endswith(('ırar', 'irer', 'urar', 'ürer', 'arar', 'erer',
                                         'dırar', 'direr', 'durar', 'dürer',
                                         'tırar', 'tirer', 'turar', 'türer',
                                         'ttırar', 'ttirer', 'tturar', 'ttürer',
                                         'yırar', 'yirer', 'yurar', 'yürer')):
                            continue
                        # Skip suffix rules with duplicate/typo 'ir'/'ır'/'ur'/'ür'
                        if suf.startswith(('iriy', 'ırıy', 'uruy', 'ürüy',
                                           'ireb', 'ırab', 'urab', 'üreb',
                                           'iric', 'ırıc', 'uruc', 'ürüc',
                                           'iril', 'ırıl', 'urul', 'ürül',
                                           'irin', 'ırın', 'urun', 'ürün',
                                           'iriş', 'ırış', 'uruş', 'ürüş',
                                           'itir', 'ıtır', 'utur', 'ütür')):
                            continue
                        # Skip suffix rules with missing r typos (e.g. ular, üler instead of urlar, ürler)
                        if suf.startswith(('ular', 'üler', 'ulard', 'ülerd', 'ulark', 'ülerk', 'ularl', 'ülerl', 'ularm', 'ülerm', 'ulars', 'ülers')):
                            continue

                    # Skip reflexive/passive -n rules on consonant-ending verb flags
                    if long_flag in ("VB", "VR", "VF", "VG"):
                        if len(parts) >= 4:
                            suf = parts[3].split('/')[0]
                            if suf.startswith('n'):
                                continue
                    
                    # Remap other flags on the suffix if any (e.g. add/flags)
                    if len(parts) >= 4:
                        add_field = parts[3]
                        prefix_str = add_field.split('/', 1)[0]
                        if prefix_str.endswith(('lar', 'ler')):
                            if 'yor' in prefix_str:
                                cop_flag_char = LONG_TO_UTF8["CL"]
                            else:
                                cop_flag_char = LONG_TO_UTF8["CL"] if long_flag in ("VB", "VR", "VA", "VS", "VK", "VL") else LONG_TO_UTF8["cl"]
                            if '/' in add_field:
                                prefix_str, flags_str = add_field.split('/', 1)
                                remapped_flags = remap_old_to_new_flag_string(flags_str, prefix_str)
                                parts[3] = f"{prefix_str}/{remapped_flags}{cop_flag_char}"
                            else:
                                parts[3] = f"{prefix_str}/{cop_flag_char}"
                        else:
                            if '/' in add_field:
                                prefix_str, flags_str = add_field.split('/', 1)
                                remapped_flags = remap_old_to_new_flag_string(flags_str, prefix_str)
                                parts[3] = f"{prefix_str}/{remapped_flags}"

                    if new_flag_char in verb_flags_rules:
                        suf_field = parts[3] if len(parts) >= 4 else ""
                        suf_base = suf_field.split('/')[0]
                        cond_field = parts[4] if len(parts) >= 5 else "."

                        # Fix: When a suffix starts with 'tt' (double-t) and the
                        # condition includes 't' before 'mak'/'mek', verbs whose stems
                        # end in 't' would get triple-t forms (e.g. tutmak → tutttuğu,
                        # sıkışmak → sıkışttırma, lağvetmek → lağvetttik).
                        # Split each such rule into:
                        #   1) stems ending in tmak/tmek → single-t suffix
                        #   2) all other consonant stems → keep double-t suffix
                        import re as _re
                        is_tt_suffix = suf_base.startswith('tt')
                        # The 't' check: if condition includes 't' in a char class OR
                        # the condition is a bare 'mak'/'mek' (which matches all consonant
                        # endings including 't'-ending stems like lağvetmek, atmak, etc.)
                        cond_has_t = (
                            ('t' in cond_field and ('mak' in cond_field or 'mek' in cond_field))
                            or cond_field in ('mak', 'mek')
                        )
                        is_relevant_flag = long_flag in ("VF", "VG", "VM", "VN", "VB", "VR", "VK", "VL")

                        if is_tt_suffix and cond_has_t and is_relevant_flag:
                            # Rule 1: stems ending in tmak/tmek → drop the first 't'
                            t_part = suf_base[1:]  # 'ttik'→'tik', 'ttır'→'tır', 'ttuğu'→'tuğu'
                            t_parts = list(parts)
                            t_parts[3] = (t_part + '/' + suf_field.split('/')[1]) if '/' in suf_field else t_part
                            t_parts[4] = 'tmak' if 'mak' in cond_field else 'tmek'
                            verb_flags_rules[new_flag_char][1].append(t_parts)

                            # Rule 2: all other consonant-ending stems → keep double-t
                            # Remove 't' from the character class in the condition
                            new_cond = _re.sub(r'\[([^\]]*?)t([^\]]*?)\]',
                                               lambda m: '[' + m.group(1) + m.group(2) + ']',
                                               cond_field)
                            if new_cond and new_cond != cond_field:
                                restricted_parts = list(parts)
                                restricted_parts[4] = new_cond
                                verb_flags_rules[new_flag_char][1].append(restricted_parts)
                            elif cond_field in ('mak', 'mek'):
                                # Bare 'mak'/'mek' condition: restrict to non-t endings
                                non_t = '[çfhkpsşbcdğjlmnrvyz]'
                                non_t_cond = non_t + 'mak' if 'mak' in cond_field else non_t + 'mek'
                                restricted_parts = list(parts)
                                restricted_parts[4] = non_t_cond
                                verb_flags_rules[new_flag_char][1].append(restricted_parts)
                            else:
                                verb_flags_rules[new_flag_char][1].append(parts)
                        else:
                            verb_flags_rules[new_flag_char][1].append(parts)
                        
                        # Clone VB and VF rules to Vb and Vf, filtering out ırmak/irmek/urmak/ürmek
                        suf = parts[3].split('/')[0] if len(parts) >= 4 else ""
                        if new_flag_char == LONG_TO_UTF8["VB"]:
                            if not any(x in suf for x in ('ırmak', 'irmek', 'urmak', 'ürmek')):
                                p_clone = list(parts)
                                verb_flags_rules[new_vb_char][1].append(p_clone)
                        elif new_flag_char == LONG_TO_UTF8["VF"]:
                            if not any(x in suf for x in ('ırmak', 'irmek', 'urmak', 'ürmek')):
                                p_clone = list(parts)
                                verb_flags_rules[new_vf_char][1].append(p_clone)

    # Append Vb and Vf to order
    verb_flags_order.append(new_vb_char)
    verb_flags_order.append(new_vf_char)

    out_lines = []
    for flag_char in verb_flags_order:
        combine_char, rules = verb_flags_rules[flag_char]
        count = len(rules)
        out_lines.append(f"SFX {flag_char} {combine_char} {count}")
        for p in rules:
            p[1] = flag_char
            out_lines.append(" ".join(p))

    return '\n'.join(out_lines)


def gen_voicing_copula_flags() -> list[str]:
    # VC (back voicing copulas)
    rules_VC = [
        sfx("VC", "0", "ım", "."),
        sfx("VC", "0", "ız", "."),
        sfx("VC", "0", "ımdır", "."),
        sfx("VC", "0", "ızdır", ".")
    ]
    block_VC = make_flag_block("VC", unique(rules_VC))

    # vc (front voicing copulas)
    rules_vc = [
        sfx("vc", "0", "im", "."),
        sfx("vc", "0", "iz", "."),
        sfx("vc", "0", "imdir", "."),
        sfx("vc", "0", "izdir", ".")
    ]
    block_vc = make_flag_block("vc", unique(rules_vc))

    return [block_VC, block_vc]


if __name__ == '__main__':
    generate_grammar()
