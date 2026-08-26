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

import re

def make_flag_block(flag: str, rules: list[str]) -> str:
    unique_rules = unique(rules)
    
    grouped = {}
    for r in unique_rules:
        parts = r.split(' ', 4)
        if len(parts) == 5:
            prefix = tuple(parts[:4])
            cond = parts[4]
            if prefix not in grouped:
                grouped[prefix] = []
            grouped[prefix].append(cond)
        else:
            if () not in grouped:
                grouped[()] = []
            grouped[()].append(r)
            
    consolidated = []
    for prefix, conds in grouped.items():
        if not prefix:
            consolidated.extend(conds)
            continue
            
        single_brackets = []
        others = []
        for c in conds:
            if re.fullmatch(r'\[([^\]]+)\]', c):
                single_brackets.append(c)
            else:
                others.append(c)
                
        if single_brackets:
            chars = set()
            is_negated = False
            for c in single_brackets:
                m = re.match(r'\[([^\]]+)\]', c)
                inner = m.group(1)
                if inner.startswith('^'):
                    is_negated = True
                    chars.update(list(inner[1:]))
                else:
                    chars.update(list(inner))
            
            sorted_chars = ''.join(sorted(chars))
            if is_negated:
                new_cond = '[^' + sorted_chars + ']'
            else:
                new_cond = '[' + sorted_chars + ']'
            consolidated.append(' '.join(prefix) + ' ' + new_cond)
            
        for c in others:
            consolidated.append(' '.join(prefix) + ' ' + c)
            
    header = f"SFX {flag} Y {len(consolidated)}"
    return header + '\n' + '\n'.join(consolidated)

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
        
    cop_flag = "CL" if lv in 'aıouâû' else "cl"
    
    if add == "0":
        rules.append(sfx(flag, strip, f"0/{cop_flag}", cond))
    elif "/" in add:
        rules.append(sfx(flag, strip, add, cond))
        rules.append(sfx(flag, strip, add + cop_flag, cond))
    else:
        rules.append(sfx(flag, strip, add, cond))
        rules.append(sfx(flag, strip, f"{add}/{cop_flag}", cond))

def sfx_ki(flag: str, strip: str, add: str, cond: str, rules: list, chain_copula: bool = True):
    ki_inflections = [
        '', 'ler', 'lerin', 'lere', 'lerde', 'lerden', 'lerle', 'lerce',
        'leri', 'lerini', 'lerine', 'lerinde', 'lerinden', 'leriyle', 'lerinin',
        'ni', 'ne', 'nde', 'nden', 'nin', 'yle', 'yse', 'dir', 'ydi', 'ymiş', 'yken',
    ]
    
    if chain_copula:
        sfx_copula(flag, strip, add, cond, rules)
    else:
        rules.append(sfx(flag, strip, add, cond))
        
    for infl in ki_inflections:
        # -ki rules don't typically take nominal copulas directly (except -dir etc handled in infl)
        rules.append(sfx(flag, strip, add + "ki" + infl, cond))

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
        derivs = "LILKSZCICKSLDLDTDE"
    else:
        cases = f"{acc_f}{dat_f}{loc_f}{abl_f}{gen_f}{ins_f}{eq_f}"
        possessives = f"{p3}{p1}{p2s}{p1pl}{p2pl}"
        copula_flag = "CL" if is_back else "cl"
        derivs = "LILKSZCICKSLDLDTDE"

    if only_vowel:
        return f"{cases}{possessives}{copula_flag}NE"
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
        # Plural possessive endings: e.g. demiryollarımız, demiryollarımıza, demiryollarınız...
        for p_suf in [
            f"{pl[:-1]}{pl_acc}m",
            f"{pl[:-1]}{pl_acc}n",
            f"{pl[:-1]}{pl_acc}m{pl_acc}z",
            f"{pl[:-1]}{pl_acc}n{pl_acc}z",
        ]:
            plural_suffixes.extend([
                p_suf,
                f"{p_suf}{loc}",
                f"{p_suf}d{loc}",
                f"{p_suf}d{loc}n",
                f"{p_suf}{pl_acc}",
                f"{p_suf}{pl_acc}n",
                f"{p_suf}l{loc}",
            ])
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

def gen_ki_flags() -> list[str]:
    """Relative -ki flags for time nouns: K1 (-ki), K2 (-kü)"""
    blocks = []
    # K1
    rules = []
    sfx_ki("K1", "0", "ki", ".", rules, chain_copula=True)
    blocks.append(make_flag_block("K1", unique(rules)))
    # K2
    rules = []
    sfx_ki("K2", "0", "kü", ".", rules, chain_copula=True)
    blocks.append(make_flag_block("K2", unique(rules)))
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
    """
    pl = 'lar' if harmony == 'back' else 'ler'
    acc_v  = 'ı' if harmony == 'back' else 'i'
    dat_v  = 'a' if harmony == 'back' else 'e'
    gen_v  = 'ın' if harmony == 'back' else 'in'
    eq_v   = 'ca' if harmony == 'back' else 'ce'

    cop = "CP" if harmony == 'back' else "CV"
    ki = "KI"

    suffixes = [
        f"{pl}{acc_v}",
        f"{pl}{dat_v}", f"{pl}{dat_v}/{cop}",
        f"{pl}d{dat_v}", f"{pl}d{dat_v}/{cop}", f"{pl}d{dat_v}/{cop}{ki}",
        f"{pl}d{dat_v}n", f"{pl}d{dat_v}n/{cop}",
        f"{pl}{gen_v}", f"{pl}{gen_v}/{cop}", f"{pl}{gen_v}/{cop}{ki}",
        f"{pl}l{dat_v}", f"{pl}l{dat_v}/{cop}",
        f"{pl}{eq_v}", f"{pl}{eq_v}/{cop}",
    ]
    
    poss_cases = [
        f"{pl}{acc_v}", f"{pl}{acc_v}/{cop}",
        f"{pl}{acc_v}n{dat_v}", f"{pl}{acc_v}n{dat_v}/{cop}",
        f"{pl}{acc_v}nd{dat_v}", f"{pl}{acc_v}nd{dat_v}/{cop}", f"{pl}{acc_v}nd{dat_v}/{cop}{ki}",
        f"{pl}{acc_v}nd{dat_v}n", f"{pl}{acc_v}nd{dat_v}n/{cop}",
        f"{pl}{acc_v}yl{dat_v}", f"{pl}{acc_v}yl{dat_v}/{cop}",
        f"{pl}{acc_v}n{eq_v}", f"{pl}{acc_v}n{eq_v}/{cop}",
        f"{pl}{acc_v}n{acc_v}n", f"{pl}{acc_v}n{acc_v}n/{cop}", f"{pl}{acc_v}n{acc_v}n/{cop}{ki}",
    ]
    suffixes.extend(poss_cases)
    return suffixes


def gen_plural_back(flag: str = "PB") -> str:
    """Back plural: -lar + all plural case forms"""
    rules = []
    rules.append(sfx(flag, "0", "lar", "."))
    rules.append(sfx(flag, "0", "lar/CP", "."))  # base plural (takes plural copula CP, not CL, preventing double plurals)
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
    rules.append(sfx(flag, "0", "ler", "."))
    rules.append(sfx(flag, "0", "ler/CV", "."))  # base plural (takes plural copula CV, not cl, preventing double plurals)
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
    for flag, back, rounded, v_cond in [
        ("PS", True, False, "[aıâ]"),   # back unrounded: -ı/-sı
        ("PT", True, True,  "[ouû]"),   # back rounded:   -u/-su
        ("PU", False, False, "[eiîdD]"),  # front unrounded: -i/-si (includes d for DVD)
        ("PV", False, True,  "[öü]"),   # front rounded:   -ü/-sü
    ]:
        acc_v = "ı" if back and not rounded else ("u" if rounded and back else ("i" if not back and not rounded else "ü"))
        loc_v = "a" if back else "e"
        eq_v = "ca" if back else "ce"

        rules = []
        # After consonant: just -[vowel]
        sfx_copula(flag, "0", acc_v,            CONS_RE, rules)
        # After vowel: -s[vowel] (buffer s)
        sfx_copula(flag, "0", f"s{acc_v}",          v_cond, rules)

        # Cases after poss (n-buffer before all cases)
        # 1. Consonant ending stems (condition: CONS_RE)
        rules.append(sfx(flag, "0", acc_v + "n" + acc_v,         CONS_RE)) # acc
        sfx_copula(flag, "0", acc_v + "n" + loc_v,         CONS_RE, rules) # dat
        sfx_ki(flag, "0", acc_v + "nd" + loc_v,        CONS_RE, rules)      # loc
        sfx_copula(flag, "0", acc_v + "nd" + loc_v + "n",  CONS_RE, rules) # abl
        sfx_ki(flag, "0", acc_v + "n" + acc_v + "n",   CONS_RE, rules)      # gen
        sfx_copula(flag, "0", acc_v + "yl" + loc_v,        CONS_RE, rules) # ins
        sfx_copula(flag, "0", acc_v + "n" + eq_v,          CONS_RE, rules) # eq

        # 2. Vowel ending stems (condition: v_cond)
        poss_s = f"s{acc_v}"
        rules.append(sfx(flag, "0", poss_s + "n" + acc_v,         v_cond)) # acc
        sfx_copula(flag, "0", poss_s + "n" + loc_v,         v_cond, rules) # dat
        sfx_ki(flag, "0", poss_s + "nd" + loc_v,        v_cond, rules)      # loc
        sfx_copula(flag, "0", poss_s + "nd" + loc_v + "n",  v_cond, rules) # abl
        sfx_ki(flag, "0", poss_s + "n" + acc_v + "n",   v_cond, rules)      # gen
        sfx_copula(flag, "0", poss_s + "yl" + loc_v,        v_cond, rules) # ins
        sfx_copula(flag, "0", poss_s + "n" + eq_v,          v_cond, rules) # eq

        # 3. Direct copula inflections on 3sg possessive (bypasses 2-level affix limits for G/D/V alternant stems)
        for cop_base in [
            f"{acc_v}d{acc_v}r", f"{acc_v}yd{acc_v}", f"{acc_v}ym{acc_v}ş", f"{acc_v}ys{loc_v}", f"{acc_v}yken",
            f"{acc_v}yd{acc_v}m", f"{acc_v}yd{acc_v}n", f"{acc_v}yd{acc_v}k", f"{acc_v}yd{acc_v}n{acc_v}z", f"{acc_v}yd{loc_v}l{loc_v}r",
            f"{acc_v}ym{acc_v}ş{acc_v}m", f"{acc_v}ym{acc_v}şs{acc_v}n", f"{acc_v}ym{acc_v}ş{acc_v}z", f"{acc_v}ym{acc_v}şs{acc_v}n{acc_v}z", f"{acc_v}ym{acc_v}şl{loc_v}r",
            f"s{acc_v}d{acc_v}r", f"s{acc_v}yd{acc_v}", f"s{acc_v}ym{acc_v}ş", f"s{acc_v}ys{loc_v}", f"s{acc_v}yken",
            f"s{acc_v}yd{acc_v}m", f"s{acc_v}yd{acc_v}n", f"s{acc_v}yd{acc_v}k", f"s{acc_v}yd{acc_v}n{acc_v}z", f"s{acc_v}yd{loc_v}l{loc_v}r",
            f"s{acc_v}ym{acc_v}ş{acc_v}m", f"s{acc_v}ym{acc_v}şs{acc_v}n", f"s{acc_v}ym{acc_v}ş{acc_v}z", f"s{acc_v}ym{acc_v}şs{acc_v}n{acc_v}z", f"s{acc_v}ym{acc_v}şl{loc_v}r",
        ]:
            cond = v_cond if cop_base.startswith('s') else CONS_RE
            rules.append(sfx(flag, "0", cop_base, cond))

        # Direct copulas on locative/ablative after 3sg possessive (e.g. emrindeymiş, hattındaydı)
        for case_cop in [
            f"{acc_v}nd{loc_v}yd{acc_v}", f"{acc_v}nd{loc_v}ym{acc_v}ş", f"{acc_v}nd{loc_v}ys{loc_v}", f"{acc_v}nd{loc_v}yken",
            f"s{acc_v}nd{loc_v}yd{acc_v}", f"s{acc_v}nd{loc_v}ym{acc_v}ş", f"s{acc_v}nd{loc_v}ys{loc_v}", f"s{acc_v}nd{loc_v}yken",
        ]:
            cond = VOWEL_RE if case_cop.startswith('s') else CONS_RE
            rules.append(sfx(flag, "0", case_cop, cond))

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
        if r_flat:
            rules.append(sfx(flag, "0", r_flat, "[aıâ]"))
        if r_round:
            rules.append(sfx(flag, "0", r_round, "[ouû]"))
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
        if r_flat:
            rules.append(sfx(flag, "0", r_flat, "[eiî]"))
        if r_round:
            rules.append(sfx(flag, "0", r_round, "[öü]"))
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
            rules.append(sfx(flag, "0", r_round, f"[öü]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_round, f"[öü][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
    return make_flag_block(flag, unique(rules))


def gen_copula_plural_back(flag: str = "CP") -> str:
    """Copula suffixes for back-harmony plural stems (-lar). Excludes bare -lar to prevent double-plural over-generation."""
    COPULAS_VOWEL = [
        "ydI", "ydIm", "ydIn", "ydIk", "ydInIz", "ydIlAr",
        "ymIş", "ymIşIm", "ymIşsIn", "ymIşIz", "ymIşsInIz", "ymIşlAr",
        "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr",
        "yIm", "sIn", "yIz", "sInIz",
        "dIr", "dIrlAr", "yken",
        "yImdIr", "sIndIr", "yIzdIr", "sInIzdIr",
    ]
    COPULAS_CONS = [
        "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
        "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
        "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
        "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
        "Im", "sIn", "Iz", "sInIz",
        "dIr", "tIr", "dIrlAr", "tIrlAr", "ken",
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
            cond_suffix = "[^aeıioöuüAEIİOÖUÜÂÎÛçfhkpsşt]"
        elif cop_tmpl.startswith('t'):
            cond_suffix = "[çfhkpsşt]"
        else:
            cond_suffix = "[^aeıioöuüAEIİOÖUÜÂÎÛ]"
        if r_flat:
            rules.append(sfx(flag, "0", r_flat, f"[aıâ]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_flat, f"[aıâ][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
        if r_round:
            rules.append(sfx(flag, "0", r_round, f"[ouû]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_round, f"[ouû][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
    return make_flag_block(flag, unique(rules))


def gen_copula_plural_front(flag: str = "CV") -> str:
    """Copula suffixes for front-harmony plural stems (-ler). Excludes bare -ler to prevent double-plural over-generation."""
    COPULAS_VOWEL = [
        "ydI", "ydIm", "ydIn", "ydIk", "ydInIz", "ydIlAr",
        "ymIş", "ymIşIm", "ymIşsIn", "ymIşIz", "ymIşsInIz", "ymIşlAr",
        "ysA", "ysAm", "ysAn", "ysAk", "ysAnIz", "ysAlAr",
        "yIm", "sIn", "yIz", "sInIz",
        "dIr", "dIrlAr", "yken",
        "yImdIr", "sIndIr", "yIzdIr", "sInIzdIr",
    ]
    COPULAS_CONS = [
        "dI", "dIm", "dIn", "dIk", "dInIz", "dIlAr",
        "tI", "tIm", "tIn", "tIk", "tInIz", "tIlAr",
        "mIş", "mIşIm", "mIşsIn", "mIşIz", "mIşsInIz", "mIşlAr",
        "sA", "sAm", "sAn", "sAk", "sAnIz", "sAlAr",
        "Im", "sIn", "Iz", "sInIz",
        "dIr", "tIr", "dIrlAr", "tIrlAr", "ken",
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
            cond_suffix = "[^aeıioöuüAEIİOÖUÜÂÎÛçfhkpsşt]"
        elif cop_tmpl.startswith('t'):
            cond_suffix = "[çfhkpsşt]"
        else:
            cond_suffix = "[^aeıioöuüAEIİOÖUÜÂÎÛ]"
        if r_flat:
            rules.append(sfx(flag, "0", r_flat, f"[eiaâî]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_flat, f"[eiaâî][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
        if r_round:
            rules.append(sfx(flag, "0", r_round, f"[öü]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_round, f"[öü][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
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


def gen_deriv_li2(flag: str = "LF") -> str:
    """Front-only -lI derivation for inverse-harmony stems.

    Inverse-harmony stems (kontrol, rol, kalp …) keep back vowels but take
    front suffixes, so the regular LI block — whose conditions key on the last
    vowel — emits only the back form ("kontrollu", "rollu"). This block matches
    the same orthographic conditions but produces only the front suffix
    ("li"/"lü", e.g. "kontrollü", "kalpli"). It is attached exclusively to
    inverse-harmony stems (numeric marker 91, expanded to LF by
    migrate_dictionary), so "okullü" / "kitapli" / "yollü" stay invalid.
    """
    stems = [
        # Vowel endings
        ("[aıâ]", "li", "F3"),
        ("[ouû]", "lü", "F4"),
        # Consonant endings (single consonant)
        ("[aıâ][^aeıioöuüâîû]", "li", "F3"),
        ("[ouû][^aeıioöuüâîû]", "lü", "F4"),
        # Double consonant endings
        ("[aıâ][^aeıioöuüâîû][^aeıioöuüâîû]", "li", "F3"),
        ("[ouû][^aeıioöuüâîû][^aeıioöuüâîû]", "lü", "F4"),
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


def gen_deriv_sz2(flag: str = "LSZ") -> str:
    """Front-only -sIz (without) derivation for inverse-harmony stems.

    Inverse-harmony stems (kontrol, ideal …) keep back vowels but take front
    suffixes, so the regular SZ block — keyed on the last vowel — emits only
    the back form ("kontrolsuz", "idealsuz"). This block produces only the
    front suffix ("siz"/"süz": "kontrolsüz", "idealsiz") and is attached
    exclusively to inverse-harmony stems (numeric marker 91, expanded to LSZ
    by migrate_dictionary).
    """
    rules = []
    for cond, suf, sc in [
        ("[aıâ]", "siz", "F1"), ("[ouû]", "süz", "F2"),
        ("[aıâ][^aeıioöuüâîû]", "siz", "F1"), ("[ouû][^aeıioöuüâîû]", "süz", "F2"),
        ("[aıâ][^aeıioöuüâîû][^aeıioöuüâîû]", "siz", "F1"), ("[ouû][^aeıioöuüâîû][^aeıioöuüâîû]", "süz", "F2"),
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


def gen_deriv_lk2(flag: str = "LFK") -> str:
    """Front-only -lIk abstract noun derivation for inverse-harmony stems.

    Same rationale as gen_deriv_li2/gen_deriv_sz2: only the front suffixes
    ("lik"/"lük", plus the vowel allomorphs "liğ"/"lüğ") are emitted, so
    "kontrollük" / "ideallik" are produced while "kontrolluk" is not.
    """
    rules = []
    for cond, suf, suf_v, sc in [
        ("[aıâ][^aeıioöuüâîû]", "lik", "liğ", "F1"),
        ("[ouû][^aeıioöuüâîû]", "lük", "lüğ", "F2"),
        ("[aıâ]",            "lik", "liğ", "F1"),
        ("[ouû]",            "lük", "lüğ", "F2"),
        ("[aıâ][^aeıioöuüâîû][^aeıioöuüâîû]", "lik", "liğ", "F1"),
        ("[ouû][^aeıioöuüâîû][^aeıioöuüâîû]", "lük", "lüğ", "F2"),
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


def gen_deriv_ci2(flag: str = "LCI") -> str:
    """Front-only -cI agentive/occupational derivation for inverse-harmony stems.

    Same rationale as gen_deriv_li2/gen_deriv_sz2: only the front suffixes
    ("ci"/"cü", with the "çi"/"çü" allomorphs after ç/f/h/k/p/s/şt) are emitted,
    so "kontrolcü" is produced while "kontrolcu" is not.
    """
    rules = []
    for cond, suf, sc in [
        ("[aıâ][^çfhkpsşt]", "ci", "F3"), ("[ouû][^çfhkpsşt]", "cü", "F4"),
        ("[aıâ][çfhkpsşt]",  "çi", "F3"), ("[ouû][çfhkpsşt]",  "çü", "F4"),
        ("[aıâ]", "ci", "F3"), ("[ouû]", "cü", "F4"),
        ("[aıâ][^aeıioöuüâîû][^çfhkpsşt]", "ci", "F3"), ("[ouû][^aeıioöuüâîû][^çfhkpsşt]", "cü", "F4"),
        ("[aıâ][^aeıioöuüâîû][çfhkpsşt]",  "çi", "F3"), ("[ouû][^aeıioöuüâîû][çfhkpsşt]",  "çü", "F4"),
    ]:
        rules.append(sfx(flag, "0", f"{suf}/{get_noun_chain(sc)[2:]}", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_ck(flag: str = "CK") -> str:
    """-cIk diminutive & -cIm affection suffixes"""
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
        sc = "B1" if suf.endswith(('cık', 'cuk', 'çık', 'çuk')) else "F1"
        rules.append(sfx(flag, "0", f"{suf}/{get_noun_chain(sc)[2:]}", cond))
        rules.append(sfx(flag, "0", suf, cond))
        
    # Affection suffixes (-cIm, e.g. doktorcum, ninecim, ziyacığım)
    for cond, suf, cop in [
        ("[aıâ]", "cım", "CL"), ("[ouû]", "cum", "CL"), ("[eiîâ]", "cim", "cl"), ("[öüû]", "cüm", "cl"),
        ("[aıâ][^aeıioöuüâîû]", "cım", "CL"), ("[ouû][^aeıioöuüâîû]", "cum", "CL"),
        ("[eiîâ][^aeıioöuüâîû]", "cim", "cl"), ("[öüû][^aeıioöuüâîû]", "cüm", "cl"),
        ("[aıâ]", "cığım", "CL"), ("[ouû]", "cuğum", "CL"), ("[eiîâ]", "ciğim", "cl"), ("[öüû]", "cüğüm", "cl"),
    ]:
        rules.append(sfx(flag, "0", f"{suf}/{cop}", cond))
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
        verb_flag = "Vi" if "a" in suf else "Vj"
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
        verb_flag = "Vi" if "ı" in suf else "Vj"
        inf_suf = "mak" if verb_flag == "Vi" else "mek"
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
        verb_flag = "Vi" if "a" in suf else "Vj"
        inf_suf = "mak" if verb_flag == "Vi" else "mek"
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
    rep_list = [
        # --- High-frequency whole-word typo corrections (rejected_words.csv) ---
        # REP forces these to rank FIRST in suggestions, ahead of ngram candidates.
        ("yanliz", "yalnız"), ("yanlız", "yalnız"),      # ~1.3k metathesis class
        ("deil", "değil"), ("diil", "değil"),
        ("degil", "değil"),                              # 40k silent-ğ class
        ("tesekkur", "teşekkür"), ("tesekkür", "teşekkür"),
        ("teşekkur", "teşekkür"),                        # ~12k
        ("hersey", "her şey"), ("herşey", "her şey"),    # ~7.7k
        ("birsey", "bir şey"), ("birşey", "bir şey"),    # ~15k
        ("geliyo", "geliyor"), ("gelior", "geliyor"),    # speech elision
        ("olucak", "olacak"), ("olcak", "olacak"),
        ("olicak", "olacak"),                            # ~7.7k vowel reduction
        ("oldugunu", "olduğunu"),                        # 31k
        ("yanlis", "yanlış"), ("yanlıs", "yanlış"),      # ~1.3k
        ("mumkun", "mümkün"), ("mümkun", "mümkün"),
        ("0", "o"), ("0", "O"),
        ("1", "i"), ("1", "I"), ("1", "ı"),
        ("3", "e"), ("3", "E"),
        ("4", "a"), ("4", "A"),
        ("5", "s"), ("5", "r"),
        ("6", "y"), ("6", "g"), ("6", "t"),
        ("7", "y"), ("7", "t"),
        ("8", "u"), ("8", "ü"),
        ("9", "o"), ("9", "u"),]
    
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
        # Circumflex single-char mappings
        ("a", "â"), ("â", "a"), ("u", "û"), ("û", "u"), ("i", "î"), ("î", "i"),
        ("A", "Â"), ("Â", "A"), ("U", "Û"), ("Û", "U"), ("İ", "Î"), ("Î", "İ"),
        # Common de-ASCII & uppercase suffix clusters
        ("lari", "ları"), ("larin", "ların"), ("larimi", "larımı"), ("lariniz", "larınız"),
        ("sutcu", "şütçü"), ("sucu", "şücü"), ("tcu", "tçü"),
        ("IS", "İŞ"), ("IL", "İL"), ("IN", "İN"), ("IY", "İY"), ("IR", "İR"), ("ES", "EŞ"), ("IK", "İK")
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
        # High-frequency TDK & modern Turkish compound/split and orthographic typos
        ("herşey", "her_şey"),
        ("birşey", "bir_şey"),
        ("pekçok", "pek_çok"),
        ("herbiri", "her_biri"),
        ("hiçkimse", "hiç_kimse"),
        ("hergün", "her_gün"),
        ("şuan", "şu_an"),
        ("sağol", "sağ_ol"),
        ("hoşçakal", "hoşça_kal"),
        ("hoşgeldin", "hoş_geldin"),
        ("hoşgeldiniz", "hoş_geldiniz"),
        ("farketmek", "fark_etmek"),
        ("terketmek", "terk_etmek"),
        ("ayırdetmek", "ayırt_etmek"),
        ("arzetmek", "arz_etmek"),
        ("başbaşa", "baş_başa"),
        ("gözgöze", "göz_göze"),
        ("yüzyüze", "yüz_yüze"),
        ("yanyana", "yan_yana"),
        ("artarda", "art_arda"),
        ("ardıardına", "ardı_ardına"),
        ("ard_arda", "art_arda"),
        ("peşpeşe", "peş_peşe"),
        ("elele", "el_ele"),
        ("heran", "her_an"),
        ("tabiki", "tabii_ki"),
        ("tabi", "tabii"),
        ("müsade", "müsaade"),
        ("muaffakiyet", "muvaffakiyet"),
        ("müteahit", "müteahhit"),
        ("laboratuar", "laboratuvar"),
        ("konsensus", "konsensüs"),
        ("antreman", "antrenman"),
        ("ünvan", "unvan"),
        ("döküman", "doküman"),
        ("tesbih", "tespih"),
        ("rasgele", "rastgele"),
        ("şurda", "şurada"),
        ("burda", "burada"),
        ("orda", "orada"),
        ("nerde", "nerede"),
        ("gardolap", "gardırop"),
        ("asvalt", "asfalt"),
        ("karnıbahar", "karnabahar"),
        ("komidin", "komodin"),
        ("kiprik", "kirpik"),
        ("parlemento", "parlamento"),
        ("sandöviç", "sandviç"),
        ("silahşör", "silahşor"),
        ("tahamül", "tahammül"),
        ("üniverste", "üniversite"),
        ("zerafet", "zarafet"),
        ("ahçı", "aşçı"),
        ("matba", "matbaa"),
        ("mütevazi", "mütevazı"),
        ("traş", "tıraş"),
        ("egsos", "egzoz"),
        ("eksoz", "egzoz"),
        ("egzos", "egzoz"),
        ("w", "v"),
        ("v", "w"),
        ("q", "k"),
        ("k", "q"),
        ("x", "ks"),
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
                    
    digit_replacements = [
        ("0", "o"), ("0", "ö"),
        ("1", "ı"), ("1", "i"), ("1", "l"),
        ("3", "e"),
        ("4", "a"), ("4", "r"), ("4", "e"),
        ("5", "s"), ("5", "t"),
        ("6", "y"), ("6", "t"),
        ("7", "u"), ("7", "y"),
        ("8", "b"), ("8", "i"),
        ("9", "o"), ("9", "u")
    ]
    for src, dst in digit_replacements:
        rep_list.append((src, dst))

    phonetic_reps = [
        ("ı", "i"), ("i", "ı"),
        ("ğ", "g"), ("g", "ğ"),
        ("ü", "u"), ("u", "ü"),
        ("ş", "s"), ("s", "ş"),
        ("ö", "o"), ("o", "ö"),
        ("ç", "c"), ("c", "ç"),
        ("â", "a"), ("a", "â"),
        ("î", "i"), ("i", "î"),
        ("û", "u"), ("u", "û"),
        ("y", "ğ"), ("ğ", "y"),
        ("v", "b"), ("b", "v"),
        ("d", "t"), ("t", "d"),
        ("tt", "t"), ("t", "tt"),
        ("ll", "l"), ("l", "ll"),
        ("ss", "s"), ("s", "ss"),
        ("nn", "n"), ("n", "nn"),
        ("mm", "m"), ("m", "mm"),
        ("rr", "r"), ("r", "rr"),
        ("kk", "k"), ("k", "kk"),
        ("pp", "p"), ("p", "pp"),
        ("bb", "b"), ("b", "bb"),
        ("dd", "d"), ("d", "dd"),
        ("cc", "c"), ("c", "cc"),
        ("zz", "z"), ("z", "zz")
    ]
    for src, dst in [
        ("a", "â"), ("â", "a"),
        ("A", "Â"), ("Â", "A"),
        ("i", "î"), ("î", "i"),
        ("İ", "Î"), ("Î", "İ"), ("I", "Î"),
        ("u", "û"), ("û", "u"),
        ("U", "Û"), ("Û", "U"),
    ]:
        rep_list.append((src, dst))
    for src, dst in phonetic_reps:
        rep_list.append((src, dst))

    circumflex_typos = [
        ("hal", "hâl"), ("hala", "hâlâ"), ("adet", "âdet"), ("alem", "âlem"),
        ("dahi", "dâhi"), ("sura", "şûra"), ("kagit", "kâğıt"), ("kağıt", "kâğıt"),
        ("ruzgar", "rüzgâr"), ("rüzgar", "rüzgâr"), ("tezgah", "tezgâh"),
        ("dukkan", "dükkân"), ("mahkum", "mahkûm"), ("alim", "âlim"), ("hakimevi", "hâkimevi"),
        ("aciz", "âciz"), ("acizleşebilme", "âcizleşebilme"), ("acizlik", "âcizlik"),
        ("adem", "âdem"), ("ademci", "Âdemci"), ("alemşümullük", "âlemşümullük"),
        ("alimlik", "âlimlik"), ("aliyyülala", "aliyyülâlâ"), ("amalık", "âmâlık"), ("amin", "âmin"),
        ("araz", "âraz"), ("arzuhalci", "arzuhâlci"), ("arzuhalcilik", "arzuhâlcilik"),
        ("askerileşme", "askerîleşme"), ("askerileşmek", "askerîleşmek"),
        ("askerileştirilme", "askerîleştirilme"), ("askerileştirmek", "askerîleştirmek"),
        ("ayan", "âyan"), ("aşık", "âşık"), ("aşıkane", "âşıkane"), ("aşıklı", "âşıklı"),
        ("aşıklık", "âşıklık"), ("aşıktaş", "âşıktaş"), ("batın", "bâtın"), ("batıni", "Bâtıni"),
        ("bedeni", "bedenî"), ("behemehal", "behemehâl"), ("beniadem", "beniâdem"), ("beşeri", "beşerî"),
        ("celali", "Celâli"), ("celalilik", "Celâlilik"), ("ceylanpınar", "Ceylânpınar"), ("cebri", "cebrî"),
        ("cevizi", "cevizî"), ("cinsi", "cinsî"), ("dahilik", "dâhilik"), ("dahiliye", "dâhiliye"),
        ("dahiliyeci", "dâhiliyeci"), ("dahiyane", "dâhiyane"), ("derhal", "derhâl"), ("dini", "dinî"),
        ("ebedi", "ebedî"), ("ebedileşmek", "ebedîleşmek"), ("ebedileştirme", "ebedîleştirme"),
        ("ebedileştirmek", "ebedîleştirmek"), ("ebedilik", "ebedîlik"), ("edebi", "edebî"),
        ("ehli", "ehlî"), ("ehlileşmek", "ehlîleşmek"), ("ehlileştirilme", "ehlîleştirilme"),
        ("ehlileştirme", "ehlîleştirme"), ("ehlileştirmek", "ehlîleştirmek"), ("elifi", "elifî"),
        ("elazığlılık", "Elâzığlılık"), ("esatiri", "esatirî"), ("ezelilik", "ezelîlik"), ("fani", "fâni"),
        ("fenni", "fennî"), ("ferdi", "ferdî"), ("ferdilik", "ferdîlik"), ("feri", "ferî"),
        ("fiili", "fiilî"), ("fikri", "fikrî"), ("gülgun", "gülgûn"), ("günaşık", "günâşık"),
        ("hakimane", "hâkimane"), ("hakkısükut", "hakkısükût"), ("halbuki", "hâlbuki"), ("halen", "hâlen"),
        ("halet", "hâlet"), ("haletiruhiye", "hâletiruhiye"), ("halihazır", "hâlihazır"),
        ("halihazırda", "hâlihazırda"), ("haliyle", "hâliyle"), ("hallenmek", "hâllenmek"),
        ("hallice", "hâllice"), ("halsiz", "hâlsiz"), ("halsizce", "hâlsizce"),
        ("adem", "âdem"), ("ademci", "âdemci"), ("ademiyet", "âdemiyet"), ("ademoğlu", "âdemoğlu"),
        ("adet", "âdet"), ("aciz", "âciz"), ("acizlik", "âcizlik"), ("ahdi", "ahdî"),
        ("alem", "âlem"), ("alemi", "âlemi"), ("alemşümul", "âlemşümul"), ("ali", "âlî"),
        ("alim", "âlim"), ("alimane", "âlimane"), ("alimlik", "âlimlik"), ("aliyyülala", "aliyyülâlâ"),
        ("amade", "âmâde"), ("amalık", "âmâlık"), ("amil", "âmil"), ("amin", "âmin"),
        ("amiran", "âmiran"), ("amirane", "âmirane"), ("amme", "âmme"), ("araz", "âraz"),
        ("arzu", "ârzû"), ("arzuhal", "arzuhâl"), ("arzuhalci", "arzuhâlci"), ("arzuhalcilik", "arzuhâlcilik"),
        ("asakir", "asâkir"), ("asude", "âsûde"), ("aşık", "âşık"), ("aşıkane", "âşıkane"),
        ("aşıklı", "âşıklı"), ("aşıklık", "âşıklık"), ("aşikar", "âşikâr"), ("aşikare", "âşikâre"),
        ("aşikarlık", "âşikârlık"), ("avam", "avâm"), ("ayan", "âyan"), ("ayende", "âyende"),
        ("azap", "azâp"), ("baki", "bâki"), ("balig", "bâliğ"), ("bari", "bâri"),
        ("barika", "bârika"), ("basiret", "basîret"), ("batın", "bâtın"), ("batıni", "bâtınî"),
        ("bedeni", "bedenî"), ("bekar", "bekâr"), ("bekarlık", "bekârlık"), ("berdevam", "berdevâm"),
        ("berkarar", "berkarâr"), ("berkemal", "berkemâl"), ("berkela", "berkelâ"), ("bermutat", "bermutât"),
        ("berveçhe", "berveçh-i"), ("berzaht", "berzâh"), ("beşeri", "beşerî"), ("biilaç", "bîilâç"),
        ("bikare", "bîkâre"), ("biperva", "bîpervâ"), ("bitaraf", "bîtaraf"), ("bivefa", "bîvefâ"),
        ("canan", "cânan"), ("cavidan", "câvidan"), ("cazip", "câzip"), ("cebri", "cebrî"),
        ("cehennemi", "cehennemî"), ("celali", "celâli"), ("celalilik", "celâlilik"), ("cellat", "cellât"),
        ("ceman", "cemân"), ("cenup", "cenûp"), ("cezri", "cezrî"), ("cihan", "cihân"),
        ("cinsi", "cinsî"), ("civar", "civâr"), ("dahi", "dâhi"), ("dahice", "dâhice"),
        ("dahilen", "dâhilen"), ("dahili", "dâhilî"), ("dahilik", "dâhilik"), ("dahiliye", "dâhiliye"),
        ("dahiliyeci", "dâhiliyeci"), ("dahl", "dâhl"), ("daim", "dâim"), ("daima", "dâima"),
        ("daimi", "daimî"), ("daimilik", "daimîlik"), ("darulaceze", "dârülaceze"), ("darulfunun", "dârülfünun"),
        ("darussafaka", "dârüşşafaka"), ("dava", "dâva"), ("davalı", "dâvalı"), ("davar", "davâr"),
        ("divan", "divân"), ("dini", "dinî"), ("ebedi", "ebedî"), ("ebedilik", "ebedîlik"),
        ("ebedileşme", "ebedîleşme"), ("ebedileşmek", "ebedîleşmek"), ("ebedileştirme", "ebedîleştirme"),
        ("ebedileştirmek", "ebedîleştirmek"), ("edebi", "edebî"), ("edebiyat", "edebiyât"),
        ("ehli", "ehlî"), ("ehlileşme", "ehlîleşme"), ("ehlileşmek", "ehlîleşmek"),
        ("ehlileştirilme", "ehlîleştirilme"), ("ehlileştirilmek", "ehlîleştirilmek"),
        ("ehlileştirme", "ehlîleştirme"), ("ehlileştirmek", "ehlîleştirmek"), ("elhasıl", "elhâsıl"),
        ("elifi", "elifî"), ("elzem", "elzêm"), ("emare", "emâre"), ("enam", "enâm"),
        ("esatir", "esâtir"), ("esatiri", "esatirî"), ("esham", "eshâm"), ("esnaf", "esnâf"),
        ("esrar", "esrâr"), ("esvap", "esvâp"), ("etfal", "etfâl"), ("etraf", "etrâf"),
        ("evkaf", "evkâf"), ("evlat", "evlât"), ("evrak", "evrâk"), ("evsaf", "evsâf"),
        ("evvel", "evvêl"), ("ezeli", "ezelî"), ("ezelilik", "ezelîlik"), ("fani", "fâni"),
        ("fanilik", "fânilik"), ("farazi", "farazî"), ("fasık", "fâsık"), ("fasıla", "fâsıla"),
        ("fasılalı", "fâsılalı"), ("fasih", "fasîh"), ("fatih", "fâtih"), ("fatiha", "fâtiha"),
        ("fecaat", "fecâat"), ("fedakar", "fedakâr"), ("fedakarlık", "fedakârlık"), ("felah", "felâh"),
        ("felaket", "felâket"), ("felsefi", "felsefî"), ("fenn", "fênn"), ("fenni", "fennî"),
        ("feragat", "ferâgat"), ("ferah", "ferâh"), ("feraset", "ferâset"), ("ferdi", "ferdî"),
        ("ferdilik", "ferdîlik"), ("feri", "ferî"), ("ferman", "fermân"), ("fesahat", "fesâhat"),
        ("fesh", "fêsh"), ("fevkalade", "fevkalâde"), ("feylesof", "feylesôf"), ("feyz", "fêyz"),
        ("fiili", "fiilî"), ("fikri", "fikrî"), ("fuzuli", "fuzulî"), ("gafil", "gâfil"),
        ("gaip", "gâip"), ("galip", "gâlip"), ("gasp", "gâsp"), ("gaye", "gâye"),
        ("gayet", "gâyet"), ("gayr", "gâyr"), ("gayri", "gayrî"), ("gavur", "gâvur"),
        ("gazap", "gazâp"), ("gazi", "gâzi"), ("gıyap", "gıyâp"), ("gıyabi", "gıyabî"),
        ("gudde", "gûdde"), ("gulam", "gulâm"), ("gulyabani", "gulyabânî"), ("habeşi", "habeşî"),
        ("hacamat", "hacâmat"), ("hacet", "hâcet"), ("haciz", "hâciz"), ("hadise", "hâdise"),
        ("hafaza", "hafâza"), ("hafız", "hâfız"), ("hafıza", "hâfıza"), ("hafif", "hafîf"),
        ("hain", "hâin"), ("hak", "hâk"), ("hakani", "hakanî"), ("hakaret", "hakâret"),
        ("hakikat", "hakîkat"), ("hakiki", "hakikî"), ("hakim", "hâkim"), ("hakimane", "hâkimane"),
        ("hakimiyet", "hâkimiyet"), ("hakimlik", "hâkimlik"), ("hakir", "hakîr"), ("hala", "hâlâ"),
        ("halas", "halâs"), ("halavet", "halâvet"), ("hale", "hâle"), ("halef", "hâlef"),
        ("halen", "hâlen"), ("halet", "hâlet"), ("haletiruhiye", "hâletiruhiye"), ("halfa", "halfâ"),
        ("halı", "hâlî"), ("halihazır", "hâlihazır"), ("halihazırda", "hâlihazırda"), ("halik", "hâlik"),
        ("halim", "halîm"), ("halis", "hâlis"), ("haliyle", "hâliyle"), ("halk", "hâlk"),
        ("halka", "halkâ"), ("halleşme", "hâlleşme"), ("halleşmek", "hâlleşmek"), ("hallice", "hâllice"),
        ("halsiz", "hâlsiz"), ("halsizce", "hâlsizce"), ("halsizleşme", "halsizleşme"), ("halsizleşmek", "hâlsizleşmek"),
        ("halsizlik", "hâlsizlik"), ("hamakat", "hamâkat"), ("hamal", "hamâl"), ("hamam", "hamâm"),
        ("hamarat", "hamârat"), ("hamaset", "hamâset"), ("hamd", "hâmd"), ("hamil", "hâmil"),
        ("hamile", "hâmile"), ("hamis", "hâmis"), ("hami", "hâmî"), ("hamle", "hâmle"),
        ("harab", "harâp"), ("harabe", "harâbe"), ("hararet", "harâret"), ("harb", "hârp"),
        ("harbi", "harbî"), ("harbiyeli", "harbiyelî"), ("harcan", "harcân"), ("harcırah", "harcırâh"),
        ("hareke", "hâreke"), ("hareket", "harekêt"), ("harem", "harêm"), ("harf", "hârf"),
        ("harici", "haricî"), ("hariciye", "hariciyê"), ("harita", "harîtâ"), ("hasar", "hasâr"),
        ("hasat", "hasât"), ("hasb", "hâsb"), ("hasbi", "hasbî"), ("hasbihal", "hasbihâl"),
        ("hasıl", "hâsıl"), ("hasılat", "hâsılat"), ("hasret", "hasrêt"), ("hassa", "hâssa"),
        ("hasta", "hâsta"), ("hastane", "hastânê"), ("haşa", "hâşâ"), ("haşarat", "haşarât"),
        ("haşari", "haşarî"), ("haşin", "haşîn"), ("haşir", "haşîr"), ("haşiv", "hâşiv"),
        ("haşmet", "haşmêt"), ("hat", "hât"), ("hata", "hatâ"), ("hatip", "hatîp"),
        ("hatıra", "hâtıra"), ("hatır", "hâtır"), ("hava", "havâ"), ("havale", "havâle"),
        ("havali", "havâlî"), ("havas", "havâs"), ("havza", "havzâ"), ("hayal", "hayâl"),
        ("hayalperest", "hayâlperest"), ("hayasız", "hayâsız"), ("hayasızca", "hayâsızca"),
        ("hayasızlık", "hayâsızlık"), ("hayat", "hayât"), ("hayır", "hâyır"), ("haysiyet", "haysiyêt"),
        ("haza", "hâzâ"), ("hazan", "hazân"), ("hazar", "hazâr"), ("hazen", "hazên"),
        ("hazık", "hâzık"), ("hazım", "hâzım"), ("hazin", "hazîn"), ("hazinedar", "hazînedâr"),
        ("haziran", "hazîran"), ("hazne", "hâzne"), ("hazret", "hazrêt"), ("hicap", "hicâp"),
        ("hicaz", "hicâz"), ("hicret", "hicrêt"), ("hicri", "hicrî"), ("hidayet", "hidâyet"),
        ("hikaye", "hikâye"), ("hikem", "hikêm"), ("hikemi", "hikemî"), ("hikmet", "hikmêt"),
        ("hilaf", "hilâf"), ("hilal", "hilâl"), ("hile", "hîle"), ("hilkat", "hilkât"),
        ("himaye", "himâye"), ("himmet", "himmêt"), ("hisar", "hisâr"), ("hitab", "hitâp"),
        ("hitabet", "hitâbet"), ("hitam", "hitâm"), ("hiyerarşi", "hiyerarşî"), ("hizmet", "hizmêt"),
        ("hoca", "hôca"), ("hudut", "hudût"), ("hukuk", "hukûk"), ("hukuki", "hukukî"),
        ("hulle", "hûlle"), ("hulyalı", "hulyâlî"), ("hurafe", "hurâfe"), ("hurda", "hurdâ"),
        ("huri", "hûrî"), ("hurma", "hurmâ"), ("hurra", "hurrâ"), ("huruf", "hurûf"),
        ("husul", "husûl"), ("husus", "husûs"), ("hususi", "hususî"), ("husumet", "husûmet"),
        ("huzur", "huzûr"), ("hüccet", "hüccêt"), ("hücre", "hûcre"), ("hükmi", "hükmî"),
        ("hükmet", "hükmêt"), ("hükm", "hüküm"), ("hükran", "şükrân"), ("hükum", "hükûm"),
        ("hükumet", "hükûmet"), ("hüküm", "hükûm"), ("hükümdar", "hükümdâr"), ("hükümet", "hükûmet"),
        ("hülasa", "hülâsa"), ("hülya", "hülyâ"), ("hüner", "hünêr"), ("hürmet", "hürmêt"),
        ("hürriyet", "hürriyêt"), ("hüsn", "hüsn"), ("hüsnühat", "hüsnühat"), ("hüsnühal", "hüsnühâl"),
        ("hüsnüyusuf", "hüsnüyûsuf"), ("hüsran", "hüsrân"), ("hüviyet", "hüviyêt"), ("hüzün", "hüzûn"),
        ("icabat", "icâbât"), ("icabet", "icâbet"), ("icap", "icâp"), ("icbar", "icbâr"),
        ("icra", "icrâ"), ("icraat", "icraât"), ("ictihat", "ictihât"), ("ictimai", "ictimaî"),
        ("ictima", "ictimâ"), ("içtimai", "içtimaî"), ("idare", "idâre"), ("idari", "idarî"),
        ("iddia", "iddiâ"), ("idman", "idmân"), ("idrak", "idrâk"), ("ifade", "ifâde"),
        ("iflah", "iflâh"), ("iflas", "iflâs"), ("ifrat", "ifrât"), ("ifraz", "ifrâz"),
        ("ifrazat", "ifrazât"), ("ifrit", "ifrît"), ("ifşa", "ifşâ"), ("ifşaat", "ifşaât"),
        ("iftar", "iftâr"), ("iftira", "iftirâ"), ("ihale", "ihâle"), ("iham", "ihâm"),
        ("ihanet", "ihânet"), ("ihata", "ihâta"), ("ihdas", "ihdâs"), ("ihlas", "ihlâs"),
        ("ihmal", "ihmâl"), ("ihracat", "ihracât"), ("ihram", "ihrâm"), ("ihraz", "ihrâz"),
        ("ihsan", "ihsân"), ("ihtar", "ihtâr"), ("ihtida", "ihtidâ"), ("ihtilaf", "ihtilâf"),
        ("ihtilal", "ihtilâl"), ("ihtilam", "ihtilâm"), ("ihtilas", "ihtilâs"), ("ihtilat", "ihtilât"),
        ("ihtiram", "ihtirâm"), ("ihtiras", "ihtirâs"), ("ihtiraz", "ihtirâz"), ("ihtisas", "ihtisâs"),
        ("ihtisar", "ihtisâr"), ("ihtişam", "ihtişâm"), ("ihtiyaç", "ihtiyâç"), ("ihtiyar", "ihtiyâr"),
        ("ihtiyari", "ihtiyarî"), ("ihtiyat", "ihtiyât"), ("ihvan", "ihvân"), ("ihya", "ihyâ"),
        ("ikamet", "ikâmet"), ("ikametgah", "ikametgâh"), ("ikaz", "ikâz"), ("ikbal", "ikbâl"),
        ("ikdam", "ikdâm"), ("iklim", "iklîm"), ("ikmal", "ikmâl"), ("ikrah", "ikrâh"),
        ("ikram", "ikrâm"), ("ikramiye", "ikrâmiye"), ("ikrar", "ikrâr"), ("ikraz", "ikrâz"),
        ("iktibas", "iktibâs"), ("iktidar", "iktidâr"), ("iktisap", "iktisâp"), ("iktisat", "iktisât"),
        ("iktisadi", "iktisadî"), ("ila", "ilâ"), ("ilahe", "ilâhe"), ("ilahiyat", "ilahiyât"),
        ("ilahi", "ilahî"), ("ilam", "ilâm"), ("ilan", "ilân"), ("ilave", "ilâve"),
        ("ilham", "ilhâm"), ("ilhak", "ilhâk"), ("illiyet", "illiyêt"), ("iltifat", "iltifât"),
        ("iltihap", "iltihâp"), ("iltica", "ilticâ"), ("iltimas", "iltimâs"), ("iltisak", "iltisâk"),
        ("ilzam", "ilzâm"), ("imad", "imâd"), ("imale", "imâle"), ("imal", "imâl"),
        ("imalat", "imalât"), ("imame", "imâme"), ("imamet", "imâmet"), ("iman", "imân"),
        ("imar", "imâr"), ("imarat", "imarât"), ("imarethane", "imârethâne"), ("imbat", "imbât"),
        ("imbi", "imbî"), ("imdat", "imdât"), ("imha", "imhâ"), ("imkan", "imkân"),
        ("imla", "imlâ"), ("imparator", "imparâtôr"), ("imtiyaz", "imtiyâz"), ("imza", "imzâ"),
        ("inad", "inâd"), ("inayet", "inâyet"), ("inbisat", "inbisât"), ("incil", "incîl"),
        ("indifa", "indifâ"), ("infilak", "infilâk"), ("infaz", "infâz"), ("inikas", "inikâs"),
        ("inkar", "inkâr"), ("inkılap", "inkılâp"), ("inkisar", "inkisâr"), ("inkiyad", "inkiyâd"),
        ("inorganik", "inorgânik"), ("insaf", "insâf"), ("insan", "insân"), ("insani", "insanî"),
        ("insaniyet", "insaniyêt"), ("inşad", "inşâd"), ("inşa", "inşâ"), ("inşaat", "inşaât"),
        ("intac", "intâc"), ("intiba", "intibâ"), ("intibak", "intibâk"), ("intifa", "intifâ"),
        ("intifada", "intifâda"), ("intihal", "intihâl"), ("intihar", "intihâr"), ("intihap", "intihâp"),
        ("intikal", "intikâl"), ("intikam", "intikâm"), ("intisap", "intisâp"), ("intizam", "intizâm"),
        ("intizar", "intizâr"), ("inzibat", "inzibât"), ("inziva", "inzivâ"), ("irad", "irâd"),
        ("irade", "irâde"), ("iradi", "iradî"), ("irfan", "irfân"), ("irsal", "irsâl"),
        ("irsaliye", "irsâliye"), ("irtibat", "irtibât"), ("irtica", "irticâ"), ("irticai", "irticaî"),
        ("irtifa", "irtifâ"), ("irtihal", "irtihâl"), ("irtikap", "irtikâp"), ("irtisal", "irtisâl"),
        ("isabet", "isâbet"), ("isale", "isâle"), ("isbat", "isbât"), ("isfehan", "isfehân"),
        ("iskan", "iskân"), ("iskat", "iskât"), ("islam", "islâm"), ("islami", "islamî"),
        ("isnat", "isnât"), ("ispat", "ispât"), ("ispirto", "ispîrto"), ("israf", "isrâf"),
        ("istibdat", "istibdât"), ("istidat", "istidât"), ("istifa", "istifâ"), ("istifade", "istifâde"),
        ("istifham", "istifhâm"), ("istihbarat", "istihbarât"), ("istihdam", "istihdâm"),
        ("istihkak", "istihkâk"), ("istihkam", "istihkâm"), ("istihkar", "istihkâr"),
        ("istihlas", "istihlâs"), ("istihrac", "istihrâc"), ("istihza", "istihzâ"),
        ("istikamet", "istikâmet"), ("istikbal", "istikbâl"), ("istiklal", "istiklâl"),
        ("istikra", "istikrâ"), ("istikrar", "istikrâr"), ("iktisat", "iktisât"),
        ("istila", "istilâ"), ("istima", "istimâ"), ("istimlak", "istimlâk"),
        ("istinat", "istinât"), ("istintak", "istintâk"), ("istirat", "istirât"),
        ("istirdat", "istirdât"), ("istirham", "istirhâm"), ("istisna", "istisnâ"),
        ("istisnai", "istisnaî"), ("istitar", "istitâr"), ("istiab", "istiâp"),
        ("istizan", "istizân"), ("isyan", "isyân"), ("isyankar", "isyankâr"),
        ("isyankarlık", "isyankârlık"), ("itaat", "itaât"), ("itfa", "itfâ"),
        ("itfaiye", "itfâiye"), ("ithaf", "ithâf"), ("ithal", "ithâl"),
        ("ithalat", "ithalât"), ("itham", "ithâm"), ("itimat", "itimât"),
        ("itiraf", "itirâf"), ("itiraz", "itirâz"), ("itisaf", "itisâf"),
        ("ittifak", "ittifâk"), ("ittihad", "ittihâd"), ("ittiham", "ittihâm"),
        ("ittihaz", "ittihâz"), ("ivaz", "ivâz"), ("izafe", "izâfe"),
        ("izafet", "izâfet"), ("izafi", "izafî"), ("izafiyet", "izafiyêt"),
        ("izah", "izâh"), ("izahat", "izahât"), ("izale", "izâle"),
        ("izam", "izâm"), ("izan", "izân"), ("izaz", "izâz"),
        ("izdivac", "izdivâc"), ("izhar", "izhâr"), ("izin", "izîn"),
        ("izolasyon", "izolâsyon"), ("izzet", "izzêt"), ("kabil", "kâbil"),
        ("kabile", "kabîle"), ("kabiliyet", "kabiliyêt"), ("kabir", "kabîr"),
        ("kabus", "kâbus"), ("kadeh", "kadêh"), ("kadem", "kadêm"),
        ("kader", "kadêr"), ("kadife", "kadîfe"), ("kadim", "kadîm"),
        ("kadimi", "kadimî"), ("kadir", "kadîr"), ("kadirşinas", "kadirşinâs"),
        ("kafe", "kâfe"), ("kafi", "kâfi"), ("kafile", "kâfile"),
        ("kafiye", "kâfiye"), ("kafur", "kâfur"), ("kagir", "kâgir"),
        ("kahin", "kâhin"), ("kahir", "kâhir"), ("kahkaha", "kahkahâ"),
        ("kahraman", "kahramân"), ("kahve", "kâhve"), ("kahveci", "kâhveci"),
        ("kahvehan", "kâhvehâne"), ("kaide", "kâide"), ("kail", "kâil"),
        ("kaim", "kâim"), ("kaime", "kâime"), ("kainat", "kâinat"),
        ("kakule", "kâkule"), ("kalbur", "kalbûr"), ("kalem", "kalêm"),
        ("kalp", "kâlp"), ("kamet", "kâmet"), ("kamil", "kâmil"),
        ("kamus", "kâmûs"), ("kanat", "kanât"), ("kanepe", "kanepê"),
        ("kanun", "kânun"), ("kanunen", "kânunen"), ("kanuni", "kanunî"),
        ("kaos", "kâos"), ("kapasite", "kapasitê"), ("kapital", "kapitâl"),
        ("kar", "kâr"), ("kara", "karâ"), ("karabet", "karâbet"),
        ("karakter", "karaktêr"), ("karar", "karâr"), ("karargah", "karargâh"),
        ("kardan", "kârdan"), ("kargaşa", "kargaşâ"), ("kari", "kârî"),
        ("karine", "karîne"), ("karlı", "kârlı"), ("karlıca", "kârlıca"),
        ("karlılık", "kârlılık"), ("karsız", "kârsız"), ("karsızca", "kârsızca"),
        ("karsızlık", "kârsızlık"), ("karyola", "kâryola"), ("kasa", "kasâ"),
        ("kasaba", "kasabâ"), ("kasap", "kasâp"), ("kasave", "kasâvet"),
        ("kase", "kâse"), ("kaside", "kasîde"), ("kasık", "kasîk"),
        ("kasır", "kasîr"), ("kasırga", "kasırgâ"), ("kasıt", "kâsıt"),
        ("katakulli", "katakullî"), ("katar", "katâr"), ("kategori", "kategôrî"),
        ("kati", "katî"), ("katip", "kâtip"), ("katliam", "katliâm"),
        ("kavga", "kavgâ"), ("kavim", "kavîm"), ("kavmi", "kavmî"),
        ("kavram", "kavrâm"), ("kayda", "kâide"), ("kayık", "kayîk"),
        ("kayın", "kâyın"), ("kayıp", "kayîp"), ("kayır", "kayîr"),
        ("kayıt", "kayît"), ("kaza", "kazâ"), ("kazaen", "kazâen"),
        ("kazan", "kazân"), ("kazanç", "kazânç"), ("kaziye", "kazîye"),
        ("kefalet", "kefâlet"), ("kefil", "kefîl"), ("kelam", "kelâm"),
        ("kelepir", "kelepîr"), ("kemal", "kemâl"), ("keman", "kemân"),
        ("kemane", "kemâne"), ("kenar", "kenâr"), ("keramet", "kerâmet"),
        ("kerata", "keratâ"), ("kerem", "kerêm"), ("kerhane", "kerhâne"),
        ("kerim", "kerîm"), ("kesafet", "kesâfet"), ("kesat", "kesât"),
        ("kesbi", "kesbî"), ("kesif", "kesîf"), ("kesir", "kesîr"),
        ("keşfet", "keşfêt"), ("keşf", "keşif"), ("keşide", "keşîde"),
        ("keşif", "keşîf"), ("kıble", "kıblê"), ("kıdem", "kıdêm"),
        ("kıraat", "kırâat"), ("kısas", "kısâs"), ("kısmet", "kısmêt"),
        ("kıssa", "kıssâ"), ("kıtal", "kıtâl"), ("kıyafet", "kıyâfet"),
        ("kıyam", "kıyâm"), ("kıyamet", "kıyâmet"), ("kıyas", "kıyâs"),
        ("kıyasi", "kıyasî"), ("kibar", "kibâr"), ("kifayet", "kifâyet"),
        ("kik", "kîk"), ("kilise", "kilîse"), ("kimya", "kimyâ"),
        ("kimyevi", "kimyevî"), ("kinaye", "kinâye"), ("kira", "kirâ"),
        ("kitap", "kitâp"), ("kitabe", "kitâbe"), ("klasik", "klâsik"),
        ("klima", "klîma"), ("klinik", "klînîk"), ("klor", "klôr"),
        ("kolluk", "kollûk"), ("kolon", "kolôn"), ("koloni", "kolonî"),
        ("komedi", "komedî"), ("komik", "komîk"), ("komiser", "komisêr"),
        ("komite", "komitê"), ("komplo", "komplô"), ("kompres", "komprês"),
        ("komut", "komût"), ("komuta", "komutâ"), ("komutan", "komutân"),
        ("konak", "konâk"), ("konferans", "konferâns"), ("kongre", "kôngre"),
        ("konser", "konsêr"), ("kontrat", "kontrât"), ("kontrol", "kontrôl"),
        ("konvoy", "konvôy"), ("kopya", "kopyâ"), ("kordiplomatik", "kordiplomâtik"),
        ("koridor", "koridôr"), ("korku", "korkû"), ("korse", "korsê"),
        ("kostüm", "kostûm"), ("koza", "kozâ"), ("köle", "kölê"),
        ("kömür", "kömûr"), ("köprü", "köprû"), ("körfez", "körfêz"),
        ("kral", "krâl"), ("kraliçe", "kraliçê"), ("kredi", "kredî"),
        ("krem", "krêm"), ("krema", "kremâ"), ("kriz", "krîz"),
        ("kronik", "kronîk"), ("kroki", "krôkî"), ("kudret", "kudrêt"),
        ("kudsi", "kudsî"), ("kul", "kûl"), ("kule", "kulê"),
        ("kullan", "kullân"), ("kulup", "kulûp"), ("kumar", "kumâr"),
        ("kumas", "kumâş"), ("kundak", "kundâk"), ("kupa", "kupâ"),
        ("kupon", "kupôn"), ("kuram", "kurâm"), ("kurban", "kurbân"),
        ("kurşun", "kurşûn"), ("kurtul", "kurtûl"), ("kuru", "kurû"),
        ("kurul", "kurûl"), ("kurum", "kurûm"), ("kusur", "kusûr"),
        ("kutup", "kutûp"), ("kutsal", "kutsâl"), ("kuvvet", "kuvvêt"),
        ("kuyu", "kuyû"), ("kuzen", "kuzên"), ("kuzey", "kuzêy"),
        ("küçük", "küçûk"), ("küf", "kûf"), ("küfür", "küfûr"),
        ("kül", "kûl"), ("külfet", "külfêt"), ("külot", "külôt"),
        ("kültür", "kültûr"), ("küme", "kümê"), ("kümes", "kümês"),
        ("künde", "kündê"), ("küp", "kûp"), ("küpe", "küpê"),
        ("kürsü", "kürsû"), ("küstah", "küstâh"), ("kütle", "kütlê"),
        ("kütüphane", "kütüphâne"),
        ("derhal", "derhâl"), ("halbuki", "hâlbuki"), ("behemehal", "behemehâl"),
        ("ilmihal", "ilmihâl"), ("hüsnühal", "hüsnühâl"), ("narıbeyza", "nârıbeyza"),
        ("ceylanpınar", "ceylânpınar"), ("misakımilli", "Misakımillî"),
        ("ezelilik", "ezelîlik"), ("keyfilik", "keyfîlik"), ("millicilik", "millîcilik"),
        ("neftileşmek", "neftîleşmek"), ("neftileştirme", "neftîleştirme"),
        ("neftileştirmek", "neftîleştirmek"), ("resmileşme", "resmîleşme"),
        ("zati", "zatî"), ("İlahi", "İlahî"), ("şekli", "şeklî"),
        ("şemsi", "şemsî"), ("şimali", "şimalî"),
        ("tatbiki", "tatbikî"), ("tedrici", "tedricî"), ("tekasül", "tekâsül"), ("temsili", "temsilî"),
        ("tenkidi", "tenkidî"), ("topyekun", "topyekûn"), ("vakıa", "vâkıâ"), ("vakıf", "vâkıf"),
        ("varis", "vâris"), ("varislik", "vârislik"), ("varissiz", "vârissiz"), ("yad", "yâd"),
        ("yar", "yâr"), ("yaran", "yâran"), ("yarence", "yârence"), ("yarenlik", "yârenlik"),
        ("yekun", "yekûn"), ("zahiri", "zahirî"), ("zati", "zatî"), ("zecri", "zecrî"),
        ("zifiri", "zifirî"), ("zihni", "zihnî"), ("İlahi", "İlahî"), ("şekli", "şeklî"),
        ("şemsi", "şemsî"), ("şimali", "şimalî")
    ]
    for src, dst in circumflex_typos:
        rep_list.append((src, dst))
        
    # Deduplicate while preserving order and removing self-replacements
    seen = set()
    unique_reps = []
    for src, dst in rep_list:
        if src != dst and (src, dst) not in seen:
            seen.add((src, dst))
            unique_reps.append((src, dst))
            
    return unique_reps


def generate_phone_rules() -> list[tuple[str, str]]:
    """Phonetic (metaphone) table for the suggestion engine.

    Hunspell's PHONE is NOT a typo->correction pair list: it is an Aspell-style
    metaphone table. Every dictionary stem and the mistyped input are converted
    to a phonetic code via these rules, and candidates whose code matches the
    input's code are ranked higher. Rules are matched case-insensitively
    (input is uppercased first) and by first-letter groups; multi-character
    rules MUST precede any rule whose search string is their prefix.

    Design:
      1. Multi-char merges for Turkey's top typo classes (rejected_words.csv
         frequencies): deil/diil->değil (40k), yanliz->yalnız metathesis
         (~1.3k), geliyo->geliyor elision (2.2k).
      2. Diacritic folds: ğ==g, ş==s, ç==c, â==a, î==i, û==u so ASCII-typed
         errors converge with correctly hatted candidates.

    NOTE: Hunspell lowercases the word before applying PHONE rules (verified
    against hunspell 1.7.0 CLI); the writer emits rules in lowercase. Keep the
    table NARROW — broad letter merges were empirically shown to degrade
    suggestion lists by displacing good ngram candidates.
    """
    phone_rules = [
        # --- multi-char merges first (they shadow their single-char prefixes) ---
        ("deil", "tegil"),   # deil  -> değil  (40k occurrences in rejected corpus)
        ("diil", "tegil"),   # diil  -> değil
        ("ln", "nl"),        # YANLIZ -> YALNIZ metathesis class
        ("iyo", "iyor"),     # geliyo/gelio -> geliyor speech elision
        # --- diacritic folds only ---
        ("ğ", "g"),
        ("ş", "s"),
        ("ç", "c"),
        ("ö", "o"),
        ("ü", "u"),
        ("ı", "i"),
        ("â", "a"), ("î", "i"), ("û", "u"),
    ]
    seen = set()
    unique_rules = []
    for src, dst in phone_rules:
        if (src, dst) not in seen:
            seen.add((src, dst))
            unique_rules.append((src, dst))
    return unique_rules


def generate_header() -> str:
    rep_pairs = generate_rep_rules()
    rep_lines = [f"REP {len(rep_pairs)}"]
    for src, dst in rep_pairs:
        rep_lines.append(f"REP {src} {dst}")
    rep_block = "\n".join(rep_lines)

    phone_pairs = generate_phone_rules()
    phone_lines = [f"PHONE {len(phone_pairs)}"]
    for src, dst in phone_pairs:
        dst_aff = dst if dst else "_"
        phone_lines.append(f"PHONE {src} {dst_aff}")
    phone_block = "\n".join(phone_lines)

    map_groups = [
        "aâAÂ",
        "uûüUÛÜ",
        "iîıİÎI",
        "oöOÖ",
        "eêEÊ",
        "cçCÇ",
        "gğGĞ",
        "sşSŞ",
        "vwyVWY",
        "qkQK",
        "'’‘",
    ]
    map_lines = [f"MAP {len(map_groups)}"]
    for g in map_groups:
        map_lines.append(f"MAP {g}")
    map_block = "\n".join(map_lines)

    return f"""# Türkçe Yazım Denetimi Sözlüğü - Chained Flags Architecture
SET UTF-8
FLAG long
NOSUGGEST NS
KEEPCASE KC
NEEDAFFIX NE
LANG tr
NOSPLITSUGS
NOPOLYSUGS
WORDCHARS '’‘.0123456789

# Break characters (allow breaking at hyphens, en-dashes, and em-dashes)
BREAK 5
BREAK -
BREAK ^-
BREAK -$
BREAK –
BREAK —


# Suggestion parameters
KEY qwertyuıopğü|asdfghjklşi|zxcvbnmçö|QWERTYUIOPĞÜ|ASDFGHJKLŞİ|ZXCVBNMÇÖ|fgğıodrnhpqw|uıevazyktsx|jövcçzsb|FGĞIODRNHPQW|UIEVAZYKTSX|JÖVCÇZSB|qaz|wsx|edc|rfv|tgb|yhn|ujm|ıkö|olç|pş|QAZ|WSX|EDC|RFV|TGB|YHN|UJM|IKÖ|OLÇ|PŞ
TRY aeinrlıdkmutsboüşzcgçhpvğfjâîûAEİRLNIDKMUTSBOÜŞZCGÇHPVĞFJÂÎÛ'’
{map_block}
MAXDIFF 5
MAXNGRAMSUGS 8

{rep_block}

# Phonetic equivalence rules: lower edit-distance penalty between mistyped and
# correct candidates that sound alike (silent ğ, metathesis, suffix reduction).
{phone_block}
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
    for block in gen_ki_flags():
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
    print("Generating copula flags (CL, cl, CP, CV)...")
    content += "\n# COPULA FLAGS\n"
    content += gen_copula_flag_back() + "\n"
    content += gen_copula_flag_front() + "\n"
    content += gen_copula_plural_back() + "\n"
    content += gen_copula_plural_front() + "\n"

    # --- Relative -ki flag ---
    print("Generating relative -ki flag (KI)...")
    content += "\n# RELATIVE -KI FLAG\n"
    content += gen_ki_flag() + "\n"

    # --- Derivation flags ---
    print("Generating derivation flags (LI, LF, SZ, LSZ, LK, LFK, CI, LCI, CK, SL)...")
    content += "\n# DERIVATION FLAGS (1ST-LEVEL)\n"
    content += gen_deriv_li() + "\n"
    content += gen_deriv_li2() + "\n"
    content += gen_deriv_sz() + "\n"
    content += gen_deriv_sz2() + "\n"
    content += gen_deriv_lk() + "\n"
    content += gen_deriv_lk2() + "\n"
    content += gen_deriv_ci() + "\n"
    content += gen_deriv_ci2() + "\n"
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

        # --- 3sg possessive flag (supports institutional/compound proper nouns e.g. Mahallesi'nde, Meclisi'nin, Bankası'na, Bakanlığı'na) ---
        poss3_v_gen = "s" + poss3_gen  # si'nin / sı'nın / su'nun / sü'nün
        poss3_v_dat = "s" + poss3_dat  # si'ne / sı'na / su'na / sü'ne
        poss3_v_loc = "s" + poss3_loc  # si'nde / sı'nda / su'nda / sü'nde
        poss3_v_abl = "s" + poss3_abl  # si'nden / sı'ndan / su'ndan / sü'nden
        v_acc_suf = "s" + ("ını" if poss3_cons == "ı" else ("ini" if poss3_cons == "i" else ("unu" if poss3_cons == "u" else "ünü")))
        c_acc_suf = ("ını" if poss3_cons == "ı" else ("ini" if poss3_cons == "i" else ("unu" if poss3_cons == "u" else "ünü")))
        poss3_v_ins = "s" + ("ıyla" if ins_suf == "la" else "iyle")
        poss3_c_ins = ("ıyla" if ins_suf == "la" else "iyle")

        # In Turkish orthography, institutional compounds place the apostrophe AFTER the possessive
        # and require the pronominal 'n' (zamir n'si) before case suffixes:
        # e.g., Meclis -> Meclisi'nin, Mahalle -> Mahallesi'nde, Bakanlık -> Bakanlığı'na
        dat_vowel = "e" if loc_soft == "de" else "a"
        c_gen_suf = poss3_cons + "'n" + gen_cons   # i'nin / ı'nın / u'nun / ü'nün
        c_dat_suf = poss3_cons + "'n" + dat_vowel  # i'ne / ı'na / u'na / ü'ne
        c_loc_suf = poss3_cons + "'n" + loc_soft   # i'nde / ı'nda / u'nda / ü'nde
        c_abl_suf = poss3_cons + "'n" + abl_soft   # i'nden / ı'ndan / u'ndan / ü'nden
        c_acc_suf_inst = poss3_cons + "'n" + acc_cons # i'ni / ı'nı / u'nu / ü'nü
        c_ins_suf_inst = poss3_cons + "'" + ("yle" if ins_suf == "le" else "yla") # i'yle / ı'yla

        v_gen_suf_inst = "s" + poss3_cons + "'n" + gen_cons  # si'nin / sı'nın
        v_dat_suf_inst = "s" + poss3_cons + "'n" + dat_vowel  # si'ne / sı'na
        v_loc_suf_inst = "s" + poss3_cons + "'n" + loc_soft  # si'nde / sı'nda
        v_abl_suf_inst = "s" + poss3_cons + "'n" + abl_soft  # si'nden / sı'ndan
        v_acc_suf_inst = "s" + poss3_cons + "'n" + acc_cons  # si'ni / sı'nı
        v_ins_suf_inst = "s" + poss3_cons + "'" + ("yle" if ins_suf == "le" else "yla") # si'yle / sı'yla

        rules_P = [
            # Consonant ending base - apostrophe before possessive (e.g. Meclis'i, Kanun'u)
            sfx(f"{flag_prefix}P", "0", f"'{poss3_cons}/cl",  CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_gen}",      CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_dat}",      CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_loc}",      CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_abl}/cl",   CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{c_acc_suf}",      CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_c_ins}/cl", CONS_RE),

            # Consonant ending base - institutional compounds (apostrophe after possessive: Meclisi'nin, Ligi'nde)
            sfx(f"{flag_prefix}P", "0", c_gen_suf,            CONS_RE),
            sfx(f"{flag_prefix}P", "0", c_dat_suf,            CONS_RE),
            sfx(f"{flag_prefix}P", "0", c_loc_suf,            CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"{c_abl_suf}/cl",    CONS_RE),
            sfx(f"{flag_prefix}P", "0", c_acc_suf_inst,       CONS_RE),
            sfx(f"{flag_prefix}P", "0", f"{c_ins_suf_inst}/cl", CONS_RE),

            # Vowel ending base - apostrophe before possessive (e.g. Mahalle'si)
            sfx(f"{flag_prefix}P", "0", f"'{poss3_vowel}/cl", VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_v_gen}",    VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_v_dat}",    VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_v_loc}",    VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_v_abl}/cl", VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"'{v_acc_suf}",      VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"'{poss3_v_ins}/cl", VOWEL_RE),

            # Vowel ending base - institutional compounds (apostrophe after possessive: Mahallesi'nde, Partisi'nin, Bankası'nda)
            sfx(f"{flag_prefix}P", "0", v_gen_suf_inst,       VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", v_dat_suf_inst,       VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", v_loc_suf_inst,       VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"{v_abl_suf_inst}/cl", VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", v_acc_suf_inst,       VOWEL_RE),
            sfx(f"{flag_prefix}P", "0", f"{v_ins_suf_inst}/cl", VOWEL_RE),

            # Voiced consonant stems (k -> ğ, t -> d, p -> b): Bakanlık -> Bakanlığı'na, Stat -> Stadı'nda, Grup -> Grubu'nda
            sfx(f"{flag_prefix}P", "k", f"ğ{c_gen_suf}",      "k"),
            sfx(f"{flag_prefix}P", "k", f"ğ{c_dat_suf}",      "k"),
            sfx(f"{flag_prefix}P", "k", f"ğ{c_loc_suf}",      "k"),
            sfx(f"{flag_prefix}P", "k", f"ğ{c_abl_suf}/cl",   "k"),
            sfx(f"{flag_prefix}P", "k", f"ğ{c_acc_suf_inst}",  "k"),
            sfx(f"{flag_prefix}P", "k", f"ğ{c_ins_suf_inst}/cl","k"),

            sfx(f"{flag_prefix}P", "t", f"d{c_gen_suf}",      "t"),
            sfx(f"{flag_prefix}P", "t", f"d{c_dat_suf}",      "t"),
            sfx(f"{flag_prefix}P", "t", f"d{c_loc_suf}",      "t"),
            sfx(f"{flag_prefix}P", "t", f"d{c_abl_suf}/cl",   "t"),

            sfx(f"{flag_prefix}P", "p", f"b{c_gen_suf}",      "p"),
            sfx(f"{flag_prefix}P", "p", f"b{c_dat_suf}",      "p"),
            sfx(f"{flag_prefix}P", "p", f"b{c_loc_suf}",      "p"),
            sfx(f"{flag_prefix}P", "p", f"b{c_abl_suf}/cl",   "p"),
        ]
        sfx_ki(f"{flag_prefix}P", "0", f"'{poss3_loc}",    CONS_RE, rules_P)
        sfx_ki(f"{flag_prefix}P", "0", f"'{poss3_gen}",    CONS_RE, rules_P)
        sfx_ki(f"{flag_prefix}P", "0", f"'{poss3_v_loc}",  VOWEL_RE, rules_P)
        sfx_ki(f"{flag_prefix}P", "0", f"'{poss3_v_gen}",  VOWEL_RE, rules_P)
        sfx_ki(f"{flag_prefix}P", "0", c_loc_suf,          CONS_RE, rules_P)
        sfx_ki(f"{flag_prefix}P", "0", v_loc_suf_inst,     VOWEL_RE, rules_P)
        sfx_ki(f"{flag_prefix}P", "k", f"ğ{c_loc_suf}",    "k", rules_P)
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
            "'nIz", "'nIzIn", "'nIzA", "'nIzI", "'nIzdA", "'nIzdAn", "'nIzlA",
            # Productive proper noun compounding forms (-spor and -oğlu)
            "spor", "spor'un", "spor'a", "spor'da", "spor'dan", "spor'u", "spor'la",
            "spor'lu", "spor'lular", "spor'lunun", "spor'luların", "spor'lulara", "spor'lularda", "spor'lulardan",
            "oğlu", "oğlu'nun", "oğlu'na", "oğlu'nda", "oğlu'ndan", "oğlu'nu", "oğlu'yla",
            "oğulları", "oğullarının", "oğullarına", "oğullarında", "oğullarından",
            # Plural institutional proper noun forms (e.g. Tesisleri'nde, Ödülleri'nde, Elemeleri'nde)
            "lArI'nIn", "lArI'nA", "lArI'ndA", "lArI'ndAn", "lArI'nI", "lArI'ylA",
            "lArI'ndAki", "lArI'ndAkiler",
            # Unit / Abbreviation derivation suffixes (e.g. TL'lik, cm'lik, kg'lık)
            "'lIk", "'lIklAr", "'lIğI", "'lIğIn", "'lIğA", "'lIktA", "'lIktAn"
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
    for deriv in ["LI", "LF", "SZ", "LSZ", "LK", "LFK", "CI", "LCI", "CK", "DL", "DT", "DE"]:
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
    new_wa_char = LONG_TO_UTF8["wa"]
    new_wi_char = LONG_TO_UTF8["wi"]
    new_wr_char = LONG_TO_UTF8["wr"]
    new_wu_char = LONG_TO_UTF8["wu"]
    new_we_char = LONG_TO_UTF8["we"]
    new_wj_char = LONG_TO_UTF8["wj"]
    new_wg_char = LONG_TO_UTF8["wg"]
    new_wh_char = LONG_TO_UTF8["wh"]
    
    for c in [new_vb_char, new_vf_char, new_wa_char, new_wi_char, new_wr_char, new_wu_char, new_we_char, new_wj_char, new_wg_char, new_wh_char]:
        verb_flags_rules[c] = ('Y', [])

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
                        cond_has_t = (
                            ('t' in cond_field and ('mak' in cond_field or 'mek' in cond_field))
                            or cond_field in ('mak', 'mek')
                        )
                        is_relevant_flag = long_flag in ("VF", "VG", "VM", "VN", "VB", "VR", "VK", "VL")

                        if is_tt_suffix and is_relevant_flag:
                            # Stems must never produce double-tt suffixes (ttik, ttı, ttuk...)
                            # Single-t form must always be used
                            t_part = suf_base[1:]
                            t_parts = list(parts)
                            t_parts[3] = (t_part + '/' + suf_field.split('/')[1]) if '/' in suf_field else t_part
                            parts_to_process = [t_parts]
                        else:
                            parts_to_process = [parts]

                        def is_aorist_a_suf(s, is_back):
                            return s.startswith('ar' if is_back else 'er') and not s.startswith('arak' if is_back else 'erek')
                            
                        def is_aorist_i_suf(s, is_back):
                            v = ('ır', 'ur') if is_back else ('ir', 'ür')
                            return s.startswith(v) and not s.startswith(tuple(x + 'mak' if is_back else x + 'mek' for x in v))

                        for cur_parts in parts_to_process:
                            cur_suf = cur_parts[3].split('/')[0] if len(cur_parts) >= 4 else ""
                            if new_flag_char == LONG_TO_UTF8["VB"]:
                                is_a_aorist = is_aorist_a_suf(cur_suf, True)
                                is_i_aorist = is_aorist_i_suf(cur_suf, True)
                                if not is_a_aorist and not is_i_aorist:
                                    verb_flags_rules[new_flag_char][1].append(list(cur_parts))
                                if is_a_aorist:
                                    verb_flags_rules[new_wa_char][1].append(list(cur_parts))
                                if is_i_aorist:
                                    verb_flags_rules[new_wi_char][1].append(list(cur_parts))
                            elif new_flag_char == LONG_TO_UTF8["VF"]:
                                is_a_aorist = is_aorist_a_suf(cur_suf, False)
                                is_i_aorist = is_aorist_i_suf(cur_suf, False)
                                if not is_a_aorist and not is_i_aorist:
                                    verb_flags_rules[new_flag_char][1].append(list(cur_parts))
                                if is_a_aorist:
                                    verb_flags_rules[new_we_char][1].append(list(cur_parts))
                                if is_i_aorist:
                                    verb_flags_rules[new_wj_char][1].append(list(cur_parts))
                            elif new_flag_char == LONG_TO_UTF8["VR"]:
                                is_a_aorist = is_aorist_a_suf(cur_suf, True)
                                is_i_aorist = is_aorist_i_suf(cur_suf, True)
                                if not is_a_aorist and not is_i_aorist:
                                    verb_flags_rules[new_flag_char][1].append(list(cur_parts))
                                if is_a_aorist:
                                    verb_flags_rules[new_wu_char][1].append(list(cur_parts))
                                if is_i_aorist:
                                    verb_flags_rules[new_wu_char][1].append(list(cur_parts))
                            elif new_flag_char == LONG_TO_UTF8["VG"]:
                                is_a_aorist = is_aorist_a_suf(cur_suf, False)
                                is_i_aorist = is_aorist_i_suf(cur_suf, False)
                                if not is_a_aorist and not is_i_aorist:
                                    verb_flags_rules[new_flag_char][1].append(list(cur_parts))
                                if is_a_aorist:
                                    verb_flags_rules[new_wh_char][1].append(list(cur_parts))
                                if is_i_aorist:
                                    verb_flags_rules[new_wh_char][1].append(list(cur_parts))
                            else:
                                verb_flags_rules[new_flag_char][1].append(cur_parts)

    # Append new flags to order
    verb_flags_order.extend([new_vb_char, new_vf_char, new_wa_char, new_wi_char, new_wr_char, new_wu_char, new_we_char, new_wj_char, new_wg_char, new_wh_char])

    # ---------------------------------------------------------------------------
    # INJECT COMPOUND PARTICIPLE & VERBAL NOUN SUFFIX RULES (Strategy 1)
    # ---------------------------------------------------------------------------
    verb_configs = {
        # Back unrounded consonant (yapmak, bakmak, çıkmak, almak, vb.)
        "VB": (True, False, False, False, "mak"),
        "Vb": (True, False, False, False, "mak"),
        "wa": (True, False, False, False, "mak"),
        "wi": (True, False, False, False, "mak"),
        "VK": (True, False, False, False, "mak"),
        # Back rounded consonant (olmak, koşmak, uçmak, bulmak, vb.)
        "VR": (True, True, False, False, "mak"),
        "wr": (True, True, False, False, "mak"),
        "wu": (True, True, False, False, "mak"),
        "VL": (True, True, False, False, "mak"),
        # Front unrounded consonant (gelmek, bilmek, gitmek, etmek, vb.)
        "VF": (False, False, False, False, "mek"),
        "Vf": (False, False, False, False, "mek"),
        "we": (False, False, False, False, "mek"),
        "wj": (False, False, False, False, "mek"),
        "VM": (False, False, False, False, "mek"),
        # Front rounded consonant (görmek, dönmek, ölmek, gülmek, sürmek, vb.)
        "VG": (False, True, False, False, "mek"),
        "wg": (False, True, False, False, "mek"),
        "wh": (False, True, False, False, "mek"),
        "VN": (False, True, False, False, "mek"),
        # Back unrounded vowel (anlamak, başlamak, yaşamak, vb.)
        "VA": (True, False, True, False, "mak"),
        # Back rounded vowel (okumak, korumak, vb.)
        "VS": (True, True, True, False, "mak"),
        # Front unrounded vowel (beklemek, dinlemek, istemek, söylemek, vb.)
        "VE": (False, False, True, False, "mek"),
        # Front rounded vowel (yürümek, büyümek, vb.)
        "VH": (False, True, True, False, "mek"),
        # Narrowing (demek, yemek)
        "VY": (False, False, False, True, "emek"),
    }

    for flag_name, (back, round_v, is_vowel_stem, is_narrow, strip) in verb_configs.items():
        if flag_name not in LONG_TO_UTF8:
            continue
        flag_char = LONG_TO_UTF8[flag_name]
        if flag_char not in verb_flags_rules:
            verb_flags_rules[flag_char] = ('Y', [])
            if flag_char not in verb_flags_order:
                verb_flags_order.append(flag_char)

        # Handle sub-harmonies for vowel-ending verb stems (e.g. söylemek vs yürümek, oynamak vs okumak)
        sub_configs = []
        if is_vowel_stem and flag_name in ("VH", "VS"):
            if flag_name == "VH":
                # Front: -e ending verbs (söylemek, özlemek) use 'i', -ü ending verbs (yürümek, büyümek) use 'ü'
                sub_configs.append((False, "i", "e", "emek"))
                sub_configs.append((True, "ü", "e", "ümek"))
            elif flag_name == "VS":
                # Back: -a ending verbs (oynamak, yollamak) use 'ı', -u ending verbs (okumak, korumak) use 'u'
                sub_configs.append((False, "ı", "a", "amak"))
                sub_configs.append((True, "u", "a", "umak"))
        else:
            v_high = "u" if (back and round_v) else ("ı" if back else ("ü" if round_v else "i"))
            v_low = "a" if back else "e"
            cond_default = f"{strip}" if is_vowel_stem else ("[dy]emek" if is_narrow else None)
            sub_configs.append((round_v, v_high, v_low, cond_default))

        for sub_round, v_high, v_low, specific_cond in sub_configs:
            v_pl_poss = "ı" if back else "i"

            variants = []
            if is_vowel_stem:
                variants = [("d", specific_cond if specific_cond else f"{strip}")]
            elif is_narrow:
                variants = [("d", "[dy]emek")]
            else:
                variants = [
                    ("d", f"[^çfhkpsşt]{strip}"),
                    ("t", f"[çfhkpsşt]{strip}")
                ]

            for d_char, cond in variants:
                # 1. 3sg Past Participle: -dığı / -tığı
                base_3sg = f"{d_char}{v_high}ğ{v_high}"
                cop_3sg_pres = "dur" if (back and sub_round) else ("dür" if (not back and sub_round) else ("dır" if back else "dir"))
                cop_3sg_past = "ydu" if (back and sub_round) else ("ydü" if (not back and sub_round) else ("ydı" if back else "ydi"))
                cop_3sg_rep = "ymuş" if (back and sub_round) else ("ymüş" if (not back and sub_round) else ("ymış" if back else "ymiş"))
                cases_3sg = [
                    "", "nda", "ndan", "nı" if back else "ni", "na" if back else "ne", "nın" if back else "nin", "yla" if back else "yle",
                    cop_3sg_pres, cop_3sg_past, cop_3sg_rep, "ysa" if back else "yse"
                ]
                for c in cases_3sg:
                    suf = f"{base_3sg}{c}" if c else base_3sg
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond])

                # 2. 1sg Participle: -dığım / -tığım
                base_1sg = f"{d_char}{v_high}ğ{v_high}m"
                for c in ["", "da" if back else "de", "dan" if back else "den", f"{v_high}", f"{v_low}", f"{v_high}n", f"l{v_low}", "dır" if back else "dir"]:
                    suf = f"{base_1sg}{c}" if c else base_1sg
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond])

                # 3. 2sg Participle: -dığın / -tığın
                base_2sg = f"{d_char}{v_high}ğ{v_high}n"
                for c in ["", "da" if back else "de", "dan" if back else "den", f"{v_high}", f"{v_low}", f"{v_high}n", f"l{v_low}", "dır" if back else "dir"]:
                    suf = f"{base_2sg}{c}" if c else base_2sg
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond])

                # 4. 1pl Participle: -dığımız / -tığımız
                base_1pl = f"{d_char}{v_high}ğ{v_high}m{v_high}z"
                for c in ["", "da" if back else "de", "dan" if back else "den", f"{v_high}", f"{v_low}", f"{v_high}n", f"l{v_low}", "dır" if back else "dir"]:
                    suf = f"{base_1pl}{c}" if c else base_1pl
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond])

                # 5. 2pl Participle: -dığınız / -tığınız
                base_2pl = f"{d_char}{v_high}ğ{v_high}n{v_high}z"
                for c in ["", "da" if back else "de", "dan" if back else "den", f"{v_high}", f"{v_low}", f"{v_high}n", f"l{v_low}", "dır" if back else "dir"]:
                    suf = f"{base_2pl}{c}" if c else base_2pl
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond])

                # 6. Plural Participle: -dıkları / -tıkları (-dIklArI / -tIklArI)
                base_pl = f"{d_char}{v_high}kl{v_low}r{v_pl_poss}"
                for c in [
                    "", "nda", "ndan", "nı" if back else "ni", "na" if back else "ne", "nın" if back else "nin", "yla" if back else "yle",
                    "dır" if back else "dir", "ydı" if back else "ydi", "ymış" if back else "ymiş", "ysa" if back else "yse"
                ]:
                    suf = f"{base_pl}{c}" if c else base_pl
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond])

            # 7. Verbal Noun 3sg: -ması / -mesi
            m_vowel = "ma" if back else "me"
            base_vn = f"{m_vowel}s{v_high}"
            cond_vn = specific_cond if specific_cond else f"{strip}"
            for c in [
                "", "nda", "ndan", "nı" if back else "ni", "na" if back else "ne", "nın" if back else "nin", "yla" if back else "yle",
                "dır" if back else "dir", "ydı" if back else "ydi", "ymış" if back else "ymiş", "ysa" if back else "yse"
            ]:
                suf = f"{base_vn}{c}" if c else base_vn
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            # 8. Verbal Noun Plural: -maları / -meleri
            base_vn_pl = f"{m_vowel}l{v_low}r{v_pl_poss}"
            for c in [
                "", "nda", "ndan", "nı" if back else "ni", "na" if back else "ne", "nın" if back else "nin", "yla" if back else "yle",
                "dır" if back else "dir", "ydı" if back else "ydi"
            ]:
                suf = f"{base_vn_pl}{c}" if c else base_vn_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            # 9. Future Participle 3sg: -acağı / -eceği / -yacağı / -yeceği
            fut_base = ("yac" if is_vowel_stem else "ac") if back else (("yec" if is_vowel_stem else "ec"))
            if is_narrow:
                fut_base = "yic" if back else "yec"
            base_fut = f"{fut_base}{v_low}ğ{v_high}"
            cond_fut = specific_cond if specific_cond else f"{strip}"
            for c in [
                "", "nda", "ndan", "nı" if back else "ni", "na" if back else "ne", "nın" if back else "nin", "yla" if back else "yle",
                "dır" if back else "dir", "ydı" if back else "ydi"
            ]:
                suf = f"{base_fut}{c}" if c else base_fut
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_fut])

            # Harmony variables for cases and copulas
            loc_c = "nda" if back else "nde"
            abl_c = "ndan" if back else "nden"
            acc_c = "nı" if back else "ni"
            dat_c = "na" if back else "ne"
            gen_c = "nın" if back else "nin"
            ins_c = "yla" if back else "yle"
            cop_c = "dır" if back else "dir"
            cop_p = "ydı" if back else "ydi"
            cop_r = "ymış" if back else "ymiş"
            cop_s = "ysa" if back else "yse"
            all_cases_3sg = ["", loc_c, abl_c, acc_c, dat_c, gen_c, ins_c, cop_c, cop_p, cop_r, cop_s]

            # 10. Future Participle Plural: -acakları / -ecekleri
            fut_pl = ("yacak" if is_vowel_stem else "acak") if back else (("yecek" if is_vowel_stem else "ecek"))
            if is_narrow:
                fut_pl = "yicak" if back else "yecek"
            base_fut_pl = f"{fut_pl}l{v_low}r{v_pl_poss}"
            for c in ["", loc_c, abl_c, acc_c, dat_c, gen_c, ins_c, cop_c, cop_p]:
                suf = f"{base_fut_pl}{c}" if c else base_fut_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_fut])

            # 11. Verbal Noun 1pl Possessive: -mamız / -memiz & Negative: -mamamız / -mememiz (vermememizdir, yapmamamızdır)
            for vn_prefix in [m_vowel, f"{m_vowel}{m_vowel}"]:
                base_vn_1pl = f"{vn_prefix}m{v_high}z"
                for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "ın" if back else "in", "la" if back else "le", cop_c, "dı" if back else "di", "mış" if back else "miş", "sa" if back else "se"]:
                    suf = f"{base_vn_1pl}{c}" if c else base_vn_1pl
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            # 12. Verbal Noun 1sg Possessive: -mam / -mem & Negative: -mamam / -memem
            for vn_prefix in [m_vowel, f"{m_vowel}{m_vowel}"]:
                base_vn_1sg = f"{vn_prefix}m"
                for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "ın" if back else "in", "la" if back else "le", cop_c, "dı" if back else "di"]:
                    suf = f"{base_vn_1sg}{c}" if c else base_vn_1sg
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            # 13. Negative Verbal Noun 3sg & Plural: -maması / -memesi, -mamaları / -memeleri (uğramamasıdır, görmemeleridir)
            base_neg_vn_3sg = f"{m_vowel}{m_vowel}s{v_high}"
            for c in all_cases_3sg:
                suf = f"{base_neg_vn_3sg}{c}" if c else base_neg_vn_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            base_neg_vn_pl = f"{m_vowel}{m_vowel}l{v_low}r{v_pl_poss}"
            for c in ["", loc_c, abl_c, acc_c, dat_c, gen_c, ins_c, cop_c, cop_p]:
                suf = f"{base_neg_vn_pl}{c}" if c else base_neg_vn_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            # 14. Progressive -makta / -mekte + Copulas (bildirilememektedir, gelişememektedir, yapılmaktadır)
            base_prog = "makta" if back else "mekte"
            cond_prog = specific_cond if specific_cond else f"{strip}"
            for c in ["", cop_c, cop_p, cop_r, cop_s, "yım" if back else "yim", "sın" if back else "sin", "yız" if back else "yiz", "sınız" if back else "siniz", "lar" if back else "ler"]:
                suf = f"{base_prog}{c}" if c else base_prog
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_prog])

            # 15. Negative Potential Progressive: -ememekte / -amamamakta
            pot_neg_prog = ("yamamakta" if is_vowel_stem else "amamakta") if back else (("yememekte" if is_vowel_stem else "ememekte"))
            cond_pot = specific_cond if specific_cond else f"{strip}"
            for c in ["", cop_c, cop_p, cop_r, cop_s]:
                suf = f"{pot_neg_prog}{c}" if c else pot_neg_prog
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # 16. Negative Potential Verbal Noun 3sg & Plural: -ememesi / -amamasından / -ememeleri / -amamalarıdır (yönetememesinden)
            pot_neg_vn = ("yamama" if is_vowel_stem else "amama") if back else (("yememe" if is_vowel_stem else "ememe"))
            base_pot_vn_3sg = f"{pot_neg_vn}s{v_high}"
            for c in all_cases_3sg:
                suf = f"{base_pot_vn_3sg}{c}" if c else base_pot_vn_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            base_pot_vn_pl = f"{pot_neg_vn}l{v_low}r{v_pl_poss}"
            for c in ["", loc_c, abl_c, acc_c, dat_c, gen_c, ins_c, cop_c, cop_p]:
                suf = f"{base_pot_vn_pl}{c}" if c else base_pot_vn_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # 17. Negative Potential Future Plural: -emeyecekleri / -amayacakları (yönetemeyecekleri)
            pot_neg_fut_pl = ("yamayacak" if is_vowel_stem else "amayacak") if back else (("yemeyecek" if is_vowel_stem else "emeyecek"))
            base_pot_fut_pl = f"{pot_neg_fut_pl}l{v_low}r{v_pl_poss}"
            for c in ["", loc_c, abl_c, acc_c, dat_c, gen_c, ins_c, cop_c, cop_p]:
                suf = f"{base_pot_fut_pl}{c}" if c else base_pot_fut_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # 18. Negative Past Participle All Persons: -madığı / -mediği (3sg), -madığım (1sg), -madığın (2sg), -madığımız (1pl), -madığınız (2pl), -madıkları (3pl)
            neg_past_base_3sg = f"{m_vowel}d{v_high}ğ{v_high}"
            for c in all_cases_3sg:
                suf = f"{neg_past_base_3sg}{c}" if c else neg_past_base_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            for p_tag, p_suf in [
                ("1sg", f"{m_vowel}d{v_high}ğ{v_high}m"),
                ("2sg", f"{m_vowel}d{v_high}ğ{v_high}n"),
                ("1pl", f"{m_vowel}d{v_high}ğ{v_high}m{v_high}z"),
                ("2pl", f"{m_vowel}d{v_high}ğ{v_high}n{v_high}z"),
            ]:
                for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "la" if back else "le", cop_c, "dı" if back else "di", "sa" if back else "se"]:
                    suf = f"{p_suf}{c}" if c else p_suf
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            base_neg_past_pl = f"{m_vowel}d{v_high}kl{v_low}r{v_pl_poss}"
            for c in ["", loc_c, abl_c, acc_c, dat_c, gen_c, ins_c, cop_c, cop_p, cop_r, cop_s]:
                suf = f"{base_neg_past_pl}{c}" if c else base_neg_past_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            # 19. Negative Potential Past Participle All Persons: -amadığı / -emediği (alınamadığı, sevemediğin, bulamadığımız...)
            pot_neg_past = ("yamad" if is_vowel_stem else "amad") if back else (("yemed" if is_vowel_stem else "emed"))
            base_pot_past_3sg = f"{pot_neg_past}{v_high}ğ{v_high}"
            for c in all_cases_3sg:
                suf = f"{base_pot_past_3sg}{c}" if c else base_pot_past_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            for p_tag, p_suf in [
                ("1sg", f"{pot_neg_past}{v_high}ğ{v_high}m"),
                ("2sg", f"{pot_neg_past}{v_high}ğ{v_high}n"),
                ("1pl", f"{pot_neg_past}{v_high}ğ{v_high}m{v_high}z"),
                ("2pl", f"{pot_neg_past}{v_high}ğ{v_high}n{v_high}z"),
            ]:
                for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "la" if back else "le", cop_c, "dı" if back else "di", "sa" if back else "se"]:
                    suf = f"{p_suf}{c}" if c else p_suf
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            base_pot_past_pl = f"{pot_neg_past}{v_high}kl{v_low}r{v_pl_poss}"
            for c in ["", loc_c, abl_c, acc_c, dat_c, gen_c, ins_c, cop_c, cop_p, cop_r, cop_s]:
                suf = f"{base_pot_past_pl}{c}" if c else base_pot_past_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # 20. Negative Potential Future Participle All Persons: -amayacağı / -emeyeceği (anlaşılamayacağını, bulamayacağımı...)
            base_pot_fut_stem = ("yamayac" if is_vowel_stem else "amayac") if back else (("yemeyec" if is_vowel_stem else "emeyec"))
            base_pot_fut_3sg = f"{base_pot_fut_stem}{v_low}ğ{v_high}"
            for c in all_cases_3sg:
                suf = f"{base_pot_fut_3sg}{c}" if c else base_pot_fut_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            for p_tag, p_suf in [
                ("1sg", f"{base_pot_fut_stem}{v_low}ğ{v_high}m"),
                ("2sg", f"{base_pot_fut_stem}{v_low}ğ{v_high}n"),
                ("1pl", f"{base_pot_fut_stem}{v_low}ğ{v_high}m{v_high}z"),
                ("2pl", f"{base_pot_fut_stem}{v_low}ğ{v_high}n{v_high}z"),
            ]:
                for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "la" if back else "le", cop_c, "dı" if back else "di", "sa" if back else "se"]:
                    suf = f"{p_suf}{c}" if c else p_suf
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # 21. Future Participle Persons: -acağım (1sg), -acağın (2sg), -acağımız (1pl), -acağınız (2pl) (göreceğime, atacağın, anlaşacağınızı...)
            for p_tag, p_suf in [
                ("1sg", f"{fut_base}{v_low}ğ{v_high}m"),
                ("2sg", f"{fut_base}{v_low}ğ{v_high}n"),
                ("1pl", f"{fut_base}{v_low}ğ{v_high}m{v_high}z"),
                ("2pl", f"{fut_base}{v_low}ğ{v_high}n{v_high}z"),
            ]:
                for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "la" if back else "le", cop_c, "dı" if back else "di", "sa" if back else "se"]:
                    suf = f"{p_suf}{c}" if c else p_suf
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_fut])

            # 22. Positive Ability Future Participles: -abileceği / -ebileceği (hazırlayabileceğimi, halledilebileceğine...)
            abil_base = ("yabil" if is_vowel_stem else "abil") if back else (("yebil" if is_vowel_stem else "ebil"))
            base_abil_fut_3sg = f"{abil_base}eceği"
            for c in ["", "nde", "nden", "ni", "ne", "nin", "yle", "dir", "ydi", "ymiş", "yse"]:
                suf = f"{base_abil_fut_3sg}{c}" if c else base_abil_fut_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            for p_tag, p_suf in [
                ("1sg", f"{abil_base}eceğim"),
                ("2sg", f"{abil_base}eceğin"),
                ("1pl", f"{abil_base}eceğimiz"),
                ("2pl", f"{abil_base}eceğiniz"),
            ]:
                for c in ["", "e", "i", "de", "den", "le", "dir", "di", "se"]:
                    suf = f"{p_suf}{c}" if c else p_suf
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            base_abil_fut_pl = f"{abil_base}ecekleri"
            for c in ["", "nde", "nden", "ni", "ne", "nin", "yle", "dir", "ydi"]:
                suf = f"{base_abil_fut_pl}{c}" if c else base_abil_fut_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # Positive Ability Progressive: -abilmekte / -ebilmekte (karıştırılabilmektedir, yapılabilmektedir)
            abil_prog = f"{abil_base}mekte"
            for c in ["", "dir", "ydi", "ymiş", "yse", "dirler"]:
                suf = f"{abil_prog}{c}" if c else abil_prog
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # 23. Nominalized Participle Plurals: -anlar / -enler (adlandıranların, faydalananlarla, getirenlerden...)
            an_suf = "iyen" if is_narrow else (("yan" if is_vowel_stem else "an") if back else (("yen" if is_vowel_stem else "en")))
            base_an_pl = f"{an_suf}l{v_low}r"
            for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "ın" if back else "in", "la" if back else "le", "ca" if back else "ce", "dandı" if back else "dendi", "dendir" if back else "dendir", cop_c, cop_p, cop_r, cop_s]:
                suf = f"{base_an_pl}{c}" if c else base_an_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_fut])

            # -anları / -enleri (3sg possessive of plural participle: sevenlerimizi, yapanları)
            for c in ["", "na" if back else "ne", "nı" if back else "ni", "nda" if back else "nde", "ndan" if back else "nden", "nın" if back else "nin", "yla" if back else "yle", cop_c, cop_p]:
                suf = f"{base_an_pl}{v_pl_poss}{c}" if c else f"{base_an_pl}{v_pl_poss}"
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_fut])

            # -anlarımız / -enlerimiz (1pl possessive of plural participle: sevenlerimizi)
            for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "la" if back else "le"]:
                suf = f"{base_an_pl}{v_pl_poss}m{v_pl_poss}z{c}" if c else f"{base_an_pl}{v_pl_poss}m{v_pl_poss}z"
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_fut])

            # Singular -anı / -eni (inananı, bakanı)
            base_an_3sg = f"{an_suf}{v_pl_poss}"
            for c in ["", "na" if back else "ne", "nı" if back else "ni", "nda" if back else "nde", "ndan" if back else "nden", "nın" if back else "nin", "yla" if back else "yle", cop_c, cop_p]:
                suf = f"{base_an_3sg}{c}" if c else base_an_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_fut])

            # 24. Past Person + Conditional Copula: -dımsa / -dimse / -dıksa / -dikse (aldımsa, öğrendimse)
            for d_c, cond_v in (variants if not is_vowel_stem else [("d", cond_fut)]):
                di_prefix = ("ydı" if is_vowel_stem else d_c) + v_high
                for p_cond_suf in [
                    f"{di_prefix}ms{v_low}",      # -dımsa / -dimse
                    f"{di_prefix}ns{v_low}",      # -dınsa / -dinse
                    f"{di_prefix}ks{v_low}",      # -dıksa / -dikse
                    f"{di_prefix}n{v_high}zs{v_low}", # -dınızsa / -dinizse
                ]:
                    verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, p_cond_suf, cond_v])

                # Participle Locative + Conditional Copula: -dığında / -dığımızda / -dıklarında + ysa
                suf_1pl_cond = f"{di_prefix}ğ{v_high}m{v_high}zd{v_low}ys{v_low}"
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf_1pl_cond, cond_v])
                suf_3sg_cond = f"{di_prefix}ğ{v_high}nd{v_low}ys{v_low}"
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf_3sg_cond, cond_v])
                suf_3pl_cond = f"{di_prefix}kl{v_low}r{v_pl_poss}nd{v_low}ys{v_low}"
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf_3pl_cond, cond_v])

            # 25. Negative Ability Necessitative: -amamalı / -ememeli (çıkamamalı, yapamamalı)
            pot_neg_nec = ("yamama" if is_vowel_stem else "amama") if back else (("yememe" if is_vowel_stem else "ememe"))
            base_nec = f"{pot_neg_nec}l{v_high}"
            for c in ["", "yım" if back else "yim", "sın" if back else "sin", "yız" if back else "yiz", "sınız" if back else "siniz", "lar" if back else "ler", "dır" if back else "dir", "ydı" if back else "ydi", "ymış" if back else "ymiş", "ysa" if back else "yse"]:
                suf = f"{base_nec}{c}" if c else base_nec
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # 26. Negative Present Participle: -mayanlar / -meyenler (geçmeyenlerden, bilmeyenlerin)
            mayan_suf = f"{m_vowel}y{v_low}n"
            base_neg_an_pl = f"{mayan_suf}l{v_low}r"
            for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "ın" if back else "in", "la" if back else "le", "ca" if back else "ce", "dandır" if back else "dendir", cop_c, cop_p, cop_r, cop_s]:
                suf = f"{base_neg_an_pl}{c}" if c else base_neg_an_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            for c in ["", "na" if back else "ne", "nı" if back else "ni", "nda" if back else "nde", "ndan" if back else "nden", "nın" if back else "nin", "yla" if back else "yle", cop_c, cop_p]:
                suf = f"{base_neg_an_pl}{v_pl_poss}{c}" if c else f"{base_neg_an_pl}{v_pl_poss}"
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            base_neg_an_3sg = f"{mayan_suf}{v_pl_poss}"
            for c in ["", "na" if back else "ne", "nı" if back else "ni", "nda" if back else "nde", "ndan" if back else "nden", "nın" if back else "nin", "yla" if back else "yle", cop_c, cop_p]:
                suf = f"{base_neg_an_3sg}{c}" if c else base_neg_an_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_vn])

            # 27. Negative Potential Present Participle: -amayanlar / -emeyenler (sindiremeyenlere, gelemeyenlerin)
            pot_neg_an = ("yamay" if is_vowel_stem else "amay") if back else (("yemey" if is_vowel_stem else "emey"))
            base_pot_an_pl = f"{pot_neg_an}{v_low}nl{v_low}r"
            for c in ["", "a" if back else "e", "ı" if back else "i", "da" if back else "de", "dan" if back else "den", "ın" if back else "in", "la" if back else "le", "ca" if back else "ce", "dandır" if back else "dendir", cop_c, cop_p, cop_r, cop_s]:
                suf = f"{base_pot_an_pl}{c}" if c else base_pot_an_pl
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            for c in ["", "na" if back else "ne", "nı" if back else "ni", "nda" if back else "nde", "ndan" if back else "nden", "nın" if back else "nin", "yla" if back else "yle", cop_c, cop_p]:
                suf = f"{base_pot_an_pl}{v_pl_poss}{c}" if c else f"{base_pot_an_pl}{v_pl_poss}"
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            base_pot_an_3sg = f"{pot_neg_an}{v_low}n{v_pl_poss}"
            for c in ["", "na" if back else "ne", "nı" if back else "ni", "nda" if back else "nde", "ndan" if back else "nden", "nın" if back else "nin", "yla" if back else "yle", cop_c, cop_p]:
                suf = f"{base_pot_an_3sg}{c}" if c else base_pot_an_3sg
                verb_flags_rules[flag_char][1].append(["SFX", flag_char, strip, suf, cond_pot])

            # 28. Infinitive Verbal Noun Cases: -makla / -mekle, -maktan / -mekten
            verb_flags_rules[flag_char][1].append(["SFX", flag_char, "0", "la" if back else "le", f"{strip}"])
            verb_flags_rules[flag_char][1].append(["SFX", flag_char, "0", "tan" if back else "ten", f"{strip}"])

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
    # VC (back voicing copulas: unrounded + rounded)
    rules_VC = [
        sfx("VC", "0", "ım", "."),
        sfx("VC", "0", "ız", "."),
        sfx("VC", "0", "ımdır", "."),
        sfx("VC", "0", "ızdır", "."),
        sfx("VC", "0", "um", "."),
        sfx("VC", "0", "uz", "."),
        sfx("VC", "0", "umdur", "."),
        sfx("VC", "0", "uzdur", ".")
    ]
    block_VC = make_flag_block("VC", unique(rules_VC))

    # vc (front voicing copulas: unrounded + rounded)
    rules_vc = [
        sfx("vc", "0", "im", "."),
        sfx("vc", "0", "iz", "."),
        sfx("vc", "0", "imdir", "."),
        sfx("vc", "0", "izdir", "."),
        sfx("vc", "0", "üm", "."),
        sfx("vc", "0", "üz", "."),
        sfx("vc", "0", "ümdür", "."),
        sfx("vc", "0", "üzdür", ".")
    ]
    block_vc = make_flag_block("vc", unique(rules_vc))

    return [block_VC, block_vc]


if __name__ == '__main__':
    generate_grammar()
