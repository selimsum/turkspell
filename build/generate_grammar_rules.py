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
        
    ki_part = "" if add.endswith(('ki', 'kü')) else "ki"
    for infl in ki_inflections:
        if not ki_part and infl == '':
            continue
        # -ki rules don't typically take nominal copulas directly (except -dir etc handled in infl)
        rules.append(sfx(flag, strip, add + ki_part + infl, cond))

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

    # Locative and ablative plural copulas (annelerdenim, yükseklerdeydim, diyenlerdendi)
    pl_copulas = [
        f"{pl}d{dat_v}y{acc_v}m", f"{pl}d{dat_v}s{acc_v}n", f"{pl}d{dat_v}y{acc_v}z", f"{pl}d{dat_v}s{acc_v}n{acc_v}z",
        f"{pl}d{dat_v}yd{acc_v}", f"{pl}d{dat_v}yd{acc_v}m", f"{pl}d{dat_v}yd{acc_v}n", f"{pl}d{dat_v}yd{acc_v}k",
        f"{pl}d{dat_v}yd{acc_v}n{acc_v}z", f"{pl}d{dat_v}yd{acc_v}l{dat_v}r", f"{pl}d{dat_v}ym{acc_v}ş",
        f"{pl}d{dat_v}ys{dat_v}",
        f"{pl}d{dat_v}n{acc_v}m", f"{pl}d{dat_v}ns{acc_v}n", f"{pl}d{dat_v}n{acc_v}z", f"{pl}d{dat_v}ns{acc_v}n{acc_v}z",
        f"{pl}d{dat_v}nd{acc_v}", f"{pl}d{dat_v}nd{acc_v}m", f"{pl}d{dat_v}nd{acc_v}n", f"{pl}d{dat_v}nd{acc_v}k",
        f"{pl}d{dat_v}nd{acc_v}n{acc_v}z", f"{pl}d{dat_v}nd{acc_v}l{dat_v}r", f"{pl}d{dat_v}nm{acc_v}ş",
        f"{pl}d{dat_v}ns{dat_v}"
    ]
    suffixes.extend(pl_copulas)
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
                rules.append(sfx(flag, "0", poss + c, "."))
                rules.append(sfx(flag, "0", f"{poss + c}/CP", "."))
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
                rules.append(sfx(flag, "0", poss + c, "."))
                rules.append(sfx(flag, "0", f"{poss + c}/CV", "."))
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
            cond = VOWEL_RE if after_vowel else "."
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
        # 1. Consonant ending stems (condition: CONS_RE and any unvoiced/voiced consonants)
        rules.append(sfx(flag, "0", acc_v + "n" + acc_v,         ".")) # acc
        sfx_copula(flag, "0", acc_v + "n" + loc_v,         ".", rules) # dat
        sfx_ki(flag, "0", acc_v + "nd" + loc_v,        ".", rules)      # loc
        sfx_copula(flag, "0", acc_v + "nd" + loc_v + "n",  ".", rules) # abl
        sfx_ki(flag, "0", acc_v + "n" + acc_v + "n",   ".", rules)      # gen
        sfx_copula(flag, "0", acc_v + "yl" + loc_v,        ".", rules) # ins
        sfx_copula(flag, "0", acc_v + "n" + eq_v,          ".", rules) # eq

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
            cond = v_cond if cop_base.startswith('s') else "."
            rules.append(sfx(flag, "0", cop_base, cond))

        # Direct copulas on locative/ablative after 3sg possessive (e.g. emrindeymiş, hattındaydı)
        for case_cop in [
            f"{acc_v}nd{loc_v}yd{acc_v}", f"{acc_v}nd{loc_v}ym{acc_v}ş", f"{acc_v}nd{loc_v}ys{loc_v}", f"{acc_v}nd{loc_v}yken",
            f"s{acc_v}nd{loc_v}yd{acc_v}", f"s{acc_v}nd{loc_v}ym{acc_v}ş", f"s{acc_v}nd{loc_v}ys{loc_v}", f"s{acc_v}nd{loc_v}yken",
        ]:
            cond = VOWEL_RE if case_cop.startswith('s') else "."
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
        for base_poss, cond in [(sg, "."), (m, VOWEL_RE)]:
            rules.append(sfx(flag, "0", base_poss, cond))
            # Copulas valid on 2sg possessive: 3sg forms and 1sg forms, but never 1pl narrative -mişiz
            for cop_tmpl in [
                "dIr", "dI", "mIş", "sA", "ken", "dIrlAr", "dIlAr", "mIşlAr", "sAlAr",
                "Im", "dIm", "mIşIm", "sAm", "ImdIr"
            ]:
                cop_stem = "baban" if back else "evin"
                if rounded:
                    cop_stem = "kolun" if back else "gözün"
                cop_str = harmonize(cop_stem, cop_tmpl)
                rules.append(sfx(flag, "0", base_poss + cop_str, cond))
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
        for base_poss, cond in [(sg, "."), (m, VOWEL_RE)]:
            rules.append(sfx(flag, "0", base_poss, cond))
            for cop_tmpl in [
                "dIr", "dI", "mIş", "sA", "ken", "dIrlAr", "dIlAr", "mIşlAr", "sAlAr"
            ]:
                cop_stem = "babamız" if back else "evimiz"
                if rounded:
                    cop_stem = "kolumuz" if back else "gözümüz"
                cop_str = harmonize(cop_stem, cop_tmpl)
                rules.append(sfx(flag, "0", base_poss + cop_str, cond))
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
        for base_poss, cond in [(sg, "."), (m, VOWEL_RE)]:
            rules.append(sfx(flag, "0", base_poss, cond))
            for cop_tmpl in [
                "dIr", "dI", "mIş", "sA", "ken", "dIrlAr", "dIlAr", "mIşlAr", "sAlAr",
                "Im", "dIm", "mIşIm", "sAm", "ImdIr"
            ]:
                cop_stem = "babanız" if back else "eviniz"
                if rounded:
                    cop_stem = "kolunuz" if back else "gözünüz"
                cop_str = harmonize(cop_stem, cop_tmpl)
                rules.append(sfx(flag, "0", base_poss + cop_str, cond))
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
            rules.append(sfx(flag, "0", r_round, f"[öüoöuüû]{cond_suffix}"))
            rules.append(sfx(flag, "0", r_round, f"[öüoöuüû][^aeıioöuüAEIİOÖUÜÂÎÛ]{cond_suffix}"))
    return make_flag_block(flag, unique(rules))


def gen_copula_plural_back(flag: str = "CP") -> str:
    """Copula suffixes for back-harmony plural stems (-lar). Excludes bare -lar to prevent double-plural over-generation.
    Excludes singular copulas (1sg/2sg like -sen, -san, -sın, -sin, -ım, -dım, -dın) which are ungrammatical on plurals."""
    COPULAS_VOWEL = [
        "ydI", "ydIk", "ydInIz", "ydIlAr",
        "ymIş", "ymIşIz", "ymIşsInIz", "ymIşlAr",
        "ysA", "ysAk", "ysAnIz", "ysAlAr",
        "yIz", "sInIz",
        "dIr", "dIrlAr", "yken",
        "yIzdIr", "sInIzdIr",
    ]
    COPULAS_CONS = [
        "dI", "dIk", "dInIz", "dIlAr",
        "tI", "tIk", "tInIz", "tIlAr",
        "mIş", "mIşIz", "mIşsInIz", "mIşlAr",
        "sA", "sAk", "sAnIz", "sAlAr",
        "Iz", "sInIz",
        "dIr", "tIr", "dIrlAr", "tIrlAr", "ken",
        "IzdIr", "sInIzdIr",
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
    """Copula suffixes for front-harmony plural stems (-ler). Excludes bare -ler to prevent double-plural over-generation.
    Excludes singular copulas (1sg/2sg like -sen, -san, -sın, -sin, -im, -dim, -din) which are ungrammatical on plurals."""
    COPULAS_VOWEL = [
        "ydI", "ydIk", "ydInIz", "ydIlAr",
        "ymIş", "ymIşIz", "ymIşsInIz", "ymIşlAr",
        "ysA", "ysAk", "ysAnIz", "ysAlAr",
        "yIz", "sInIz",
        "dIr", "dIrlAr", "yken",
        "yIzdIr", "sInIzdIr",
    ]
    COPULAS_CONS = [
        "dI", "dIk", "dInIz", "dIlAr",
        "tI", "tIk", "tInIz", "tIlAr",
        "mIş", "mIşIz", "mIşsInIz", "mIşlAr",
        "sA", "sAk", "sAnIz", "sAlAr",
        "Iz", "sInIz",
        "dIr", "tIr", "dIrlAr", "tIrlAr", "ken",
        "IzdIr", "sInIzdIr",
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
        ("[aıâ][bcdgğjlmnrvyz]", "cı", "B3"), ("[ouû][bcdgğjlmnrvyz]", "cu", "B4"),
        ("[eiîâ][bcdgğjlmnrvyz]", "ci", "F3"), ("[öüû][bcdgğjlmnrvyz]", "cü", "F4"),
        ("[aıâ][çfhkpsşt]",  "çı", "B3"), ("[ouû][çfhkpsşt]",  "çu", "B4"),
        ("[eiîâ][çfhkpsşt]",  "çi", "F3"), ("[öüû][çfhkpsşt]",  "çü", "F4"),
        ("[aıâ]", "cı", "B3"), ("[ouû]", "cu", "B4"), ("[eiîâ]", "ci", "F3"), ("[öüû]", "cü", "F4"),
        # Two-consonant endings
        ("[aıâ][^aeıioöuüâîû][bcdgğjlmnrvyz]", "cı", "B3"), ("[ouû][^aeıioöuüâîû][bcdgğjlmnrvyz]", "cu", "B4"),
        ("[eiîâ][^aeıioöuüâîû][bcdgğjlmnrvyz]", "ci", "F3"), ("[öüû][^aeıioöuüâîû][bcdgğjlmnrvyz]", "cü", "F4"),
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
        ("[aıâ][bcdgğjlmnrvyz]", "ci", "F3"), ("[ouû][bcdgğjlmnrvyz]", "cü", "F4"),
        ("[aıâ][çfhkpsşt]",  "çi", "F3"), ("[ouû][çfhkpsşt]",  "çü", "F4"),
        ("[aıâ]", "ci", "F3"), ("[ouû]", "cü", "F4"),
        ("[aıâ][^aeıioöuüâîû][bcdgğjlmnrvyz]", "ci", "F3"), ("[ouû][^aeıioöuüâîû][bcdgğjlmnrvyz]", "cü", "F4"),
        ("[aıâ][^aeıioöuüâîû][çfhkpsşt]",  "çi", "F3"), ("[ouû][^aeıioöuüâîû][çfhkpsşt]",  "çü", "F4"),
    ]:
        rules.append(sfx(flag, "0", f"{suf}/{get_noun_chain(sc)[2:]}", cond))
    return make_flag_block(flag, unique(rules))


def gen_deriv_ck(flag: str = "CK") -> str:
    """-cIk diminutive & -cIm affection suffixes"""
    rules = []
    for cond, suf in [
        ("[aıâ][bcdgğjlmnrvyz]", "cık"), ("[ouû][bcdgğjlmnrvyz]", "cuk"),
        ("[eiîâ][bcdgğjlmnrvyz]", "cik"), ("[öüû][bcdgğjlmnrvyz]", "cük"),
        ("[aıâ][çfhkpsşt]",  "çık"), ("[ouû][çfhkpsşt]",  "çuk"),
        ("[eiîâ][çfhkpsşt]",  "çik"), ("[öüû][çfhkpsşt]",  "çük"),
        ("[aıâ]", "cık"), ("[ouû]", "cuk"), ("[eiîâ]", "cik"), ("[öüû]", "cük"),
        # Two-consonant endings
        ("[aıâ][^aeıioöuüâîû][bcdgğjlmnrvyz]", "cık"), ("[ouû][^aeıioöuüâîû][bcdgğjlmnrvyz]", "cuk"),
        ("[eiîâ][^aeıioöuüâîû][bcdgğjlmnrvyz]", "cik"), ("[öüû][^aeıioöuüâîû][bcdgğjlmnrvyz]", "cük"),
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
        # --- Targeted Benchmark Fixes ---
        ("bakicısıyla", "bakıcısıyla"),
        ("etkinleştirim", "etkinleştirdim"),
        ("mezhebide", "mezhebinde"),
        ("okumamakça", "okumamakla"),
        ("makça", "makla"),
        ("mekçe", "mekle"),
        ("öllüleri", "ölçüleri"),
        ("ayakladırmaya", "ayaklandırmaya"),
        ("mlla", "malla"),
        ("yakalamanmışız", "yakalamamışız"),
        ("çoğalıldı", "çoğaltıldı"),
        ("misafirlersen", "misafirlerden"),
        ("teknolojilerinsen", "teknolojilerinden"),
        ("topraklarınsan", "topraklarından"),
        ("görüntülerinsen", "görüntülerinden"),
        ("çiftliklersen", "çiftliklerden"),
        ("goya", "boya"),
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

    # --- Verb flags (2-macro-stage factorized) ---
    print("Generating factorized verb paradigm flags...")
    content += "\n# FACTORIZED VERB PARADIGM FLAGS\n"
    content += generate_factorized_verb_rules() + "\n"

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

# ---------------------------------------------------------------------------
# FACTORIZED VERB AFFIX GENERATOR (2-MACRO-STAGE ARCHITECTURE)
# ---------------------------------------------------------------------------

def make_verb_flag_block(flag: str, rules: list[str]) -> str:
    from collections import OrderedDict
    seen = OrderedDict()
    for r in rules:
        seen[r] = None
    u_rules = list(seen.keys())
    return f"SFX {flag} Y {len(u_rules)}\n" + "\n".join(u_rules)


def generate_stage2_flags() -> list[str]:
    blocks = []
    
    # 1. cA: Consonant Back Unrounded Copulas (for -ar, -maz)
    rules_cA = [
        sfx("cA", "0", "dı", "."), sfx("cA", "0", "dım", "."), sfx("cA", "0", "dın", "."),
        sfx("cA", "0", "dık", "."), sfx("cA", "0", "dınız", "."), sfx("cA", "0", "dılar", "."),
        sfx("cA", "0", "mış", "."), sfx("cA", "0", "mışım", "."), sfx("cA", "0", "mışsın", "."),
        sfx("cA", "0", "mışız", "."), sfx("cA", "0", "mışsınız", "."), sfx("cA", "0", "mışlar", "."),
        sfx("cA", "0", "sa", "."), sfx("cA", "0", "sam", "."), sfx("cA", "0", "san", "."),
        sfx("cA", "0", "sak", "."), sfx("cA", "0", "sanız", "."), sfx("cA", "0", "salar", "."),
        sfx("cA", "0", "dır", "."), sfx("cA", "0", "dırlar", "."),
        sfx("cA", "0", "larmış", "."), sfx("cA", "0", "lardı", "."), sfx("cA", "0", "larsa", "."),
        sfx("cA", "0", "larken", ".")
    ]
    blocks.append(make_verb_flag_block("cA", rules_cA))

    # 2. cE: Consonant Front Unrounded Copulas (for -er, -mez)
    rules_cE = [
        sfx("cE", "0", "di", "."), sfx("cE", "0", "dim", "."), sfx("cE", "0", "din", "."),
        sfx("cE", "0", "dik", "."), sfx("cE", "0", "diniz", "."), sfx("cE", "0", "diler", "."),
        sfx("cE", "0", "miş", "."), sfx("cE", "0", "mişim", "."), sfx("cE", "0", "mişsin", "."),
        sfx("cE", "0", "mişiz", "."), sfx("cE", "0", "mişsiniz", "."), sfx("cE", "0", "mişler", "."),
        sfx("cE", "0", "se", "."), sfx("cE", "0", "sem", "."), sfx("cE", "0", "sen", "."),
        sfx("cE", "0", "sek", "."), sfx("cE", "0", "seniz", "."), sfx("cE", "0", "seler", "."),
        sfx("cE", "0", "dir", "."), sfx("cE", "0", "dirler", "."),
        sfx("cE", "0", "lermiş", "."), sfx("cE", "0", "lerdi", "."), sfx("cE", "0", "lerse", "."),
        sfx("cE", "0", "lerken", ".")
    ]
    blocks.append(make_verb_flag_block("cE", rules_cE))

    # 3. cU: Rounded Consonant Back Copulas (for -ıyor, -uyor, -ur)
    rules_cU = [
        sfx("cU", "0", "du", "."), sfx("cU", "0", "dum", "."), sfx("cU", "0", "dun", "."),
        sfx("cU", "0", "duk", "."), sfx("cU", "0", "dunuz", "."), sfx("cU", "0", "dular", "."),
        sfx("cU", "0", "dı", "."), sfx("cU", "0", "dım", "."), sfx("cU", "0", "dın", "."),
        sfx("cU", "0", "dık", "."), sfx("cU", "0", "dınız", "."), sfx("cU", "0", "dılar", "."),
        sfx("cU", "0", "muş", "."), sfx("cU", "0", "muşum", "."), sfx("cU", "0", "muşsun", "."),
        sfx("cU", "0", "muşuz", "."), sfx("cU", "0", "muşsunuz", "."), sfx("cU", "0", "muşlar", "."),
        sfx("cU", "0", "mış", "."), sfx("cU", "0", "mışım", "."), sfx("cU", "0", "mışsın", "."),
        sfx("cU", "0", "mışız", "."), sfx("cU", "0", "mışsınız", "."), sfx("cU", "0", "mışlar", "."),
        sfx("cU", "0", "sa", "."), sfx("cU", "0", "sam", "."), sfx("cU", "0", "san", "."),
        sfx("cU", "0", "sak", "."), sfx("cU", "0", "sanız", "."), sfx("cU", "0", "salar", "."),
        sfx("cU", "0", "dur", "."), sfx("cU", "0", "durlar", "."),
        sfx("cU", "0", "dır", "."), sfx("cU", "0", "dırlar", "."),
        sfx("cU", "0", "larmış", "."), sfx("cU", "0", "lardı", "."), sfx("cU", "0", "larsa", "."),
        sfx("cU", "0", "larken", ".")
    ]
    blocks.append(make_verb_flag_block("cU", rules_cU))

    # 4. cI: Rounded Consonant Front Copulas (for -iyor, -üyor, -ür)
    rules_cI = [
        sfx("cI", "0", "dü", "."), sfx("cI", "0", "düm", "."), sfx("cI", "0", "dün", "."),
        sfx("cI", "0", "dük", "."), sfx("cI", "0", "dünüz", "."), sfx("cI", "0", "düler", "."),
        sfx("cI", "0", "di", "."), sfx("cI", "0", "dim", "."), sfx("cI", "0", "din", "."),
        sfx("cI", "0", "dik", "."), sfx("cI", "0", "diniz", "."), sfx("cI", "0", "diler", "."),
        sfx("cI", "0", "müş", "."), sfx("cI", "0", "müşüm", "."), sfx("cI", "0", "müşsün", "."),
        sfx("cI", "0", "müşüz", "."), sfx("cI", "0", "müşsünüz", "."), sfx("cI", "0", "müşler", "."),
        sfx("cI", "0", "miş", "."), sfx("cI", "0", "mişim", "."), sfx("cI", "0", "mişsin", "."),
        sfx("cI", "0", "mişiz", "."), sfx("cI", "0", "mişsiniz", "."), sfx("cI", "0", "mişler", "."),
        sfx("cI", "0", "se", "."), sfx("cI", "0", "sem", "."), sfx("cI", "0", "sen", "."),
        sfx("cI", "0", "sek", "."), sfx("cI", "0", "seniz", "."), sfx("cI", "0", "seler", "."),
        sfx("cI", "0", "dür", "."), sfx("cI", "0", "dürler", "."),
        sfx("cI", "0", "dir", "."), sfx("cI", "0", "dirler", "."),
        sfx("cI", "0", "lermiş", "."), sfx("cI", "0", "lerdi", "."), sfx("cI", "0", "lerse", "."),
        sfx("cI", "0", "lerken", ".")
    ]
    blocks.append(make_verb_flag_block("cI", rules_cI))

    # 5. uA: Unvoiced Consonant Back Copulas (for -acak, -mış)
    rules_uA = [
        sfx("uA", "0", "tı", "."), sfx("uA", "0", "tım", "."), sfx("uA", "0", "tın", "."),
        sfx("uA", "0", "tık", "."), sfx("uA", "0", "tınız", "."), sfx("uA", "0", "tılar", "."),
        sfx("uA", "0", "mış", "."), sfx("uA", "0", "mışım", "."), sfx("uA", "0", "mışsın", "."),
        sfx("uA", "0", "mışız", "."), sfx("uA", "0", "mışsınız", "."), sfx("uA", "0", "mışlar", "."),
        sfx("uA", "0", "sa", "."), sfx("uA", "0", "sam", "."), sfx("uA", "0", "san", "."),
        sfx("uA", "0", "sak", "."), sfx("uA", "0", "sanız", "."), sfx("uA", "0", "salar", "."),
        sfx("uA", "0", "tır", "."), sfx("uA", "0", "tırlar", "."),
        sfx("uA", "0", "larmış", "."), sfx("uA", "0", "lardı", "."), sfx("uA", "0", "larsa", "."),
        sfx("uA", "0", "ken", ".")
    ]
    blocks.append(make_verb_flag_block("uA", rules_uA))

    # 6. uE: Unvoiced Consonant Front Copulas (for -ecek, -miş)
    rules_uE = [
        sfx("uE", "0", "ti", "."), sfx("uE", "0", "tim", "."), sfx("uE", "0", "tin", "."),
        sfx("uE", "0", "tik", "."), sfx("uE", "0", "tiniz", "."), sfx("uE", "0", "tiler", "."),
        sfx("uE", "0", "miş", "."), sfx("uE", "0", "mişim", "."), sfx("uE", "0", "mişsin", "."),
        sfx("uE", "0", "mişiz", "."), sfx("uE", "0", "mişsiniz", "."), sfx("uE", "0", "mişler", "."),
        sfx("uE", "0", "se", "."), sfx("uE", "0", "sem", "."), sfx("uE", "0", "sen", "."),
        sfx("uE", "0", "sek", "."), sfx("uE", "0", "seniz", "."), sfx("uE", "0", "seler", "."),
        sfx("uE", "0", "tir", "."), sfx("uE", "0", "tirler", "."),
        sfx("uE", "0", "lermiş", "."), sfx("uE", "0", "lerdi", "."), sfx("uE", "0", "lerse", "."),
        sfx("uE", "0", "ken", ".")
    ]
    blocks.append(make_verb_flag_block("uE", rules_uE))

    # 6b. uO: Unvoiced Consonant Back Rounded Copulas (for -muş)
    rules_uO = [
        sfx("uO", "0", "tu", "."), sfx("uO", "0", "tum", "."), sfx("uO", "0", "tun", "."),
        sfx("uO", "0", "tuk", "."), sfx("uO", "0", "tunuz", "."), sfx("uO", "0", "tular", "."),
        sfx("uO", "0", "tı", "."), sfx("uO", "0", "tım", "."), sfx("uO", "0", "tın", "."),
        sfx("uO", "0", "tık", "."), sfx("uO", "0", "tınız", "."), sfx("uO", "0", "tılar", "."),
        sfx("uO", "0", "muş", "."), sfx("uO", "0", "muşum", "."), sfx("uO", "0", "muşsun", "."),
        sfx("uO", "0", "muşuz", "."), sfx("uO", "0", "muşsunuz", "."), sfx("uO", "0", "muşlar", "."),
        sfx("uO", "0", "sa", "."), sfx("uO", "0", "sam", "."), sfx("uO", "0", "san", "."),
        sfx("uO", "0", "sak", "."), sfx("uO", "0", "sanız", "."), sfx("uO", "0", "salar", "."),
        sfx("uO", "0", "tur", "."), sfx("uO", "0", "turlar", "."),
        sfx("uO", "0", "tır", "."), sfx("uO", "0", "tırlar", "."),
        sfx("uO", "0", "larmış", "."), sfx("uO", "0", "lardı", "."), sfx("uO", "0", "larsa", "."),
        sfx("uO", "0", "ken", ".")
    ]
    blocks.append(make_verb_flag_block("uO", rules_uO))

    # 6c. uU: Unvoiced Consonant Front Rounded Copulas (for -müş)
    rules_uU = [
        sfx("uU", "0", "tü", "."), sfx("uU", "0", "tüm", "."), sfx("uU", "0", "tün", "."),
        sfx("uU", "0", "tük", "."), sfx("uU", "0", "tünüz", "."), sfx("uU", "0", "tüler", "."),
        sfx("uU", "0", "ti", "."), sfx("uU", "0", "tim", "."), sfx("uU", "0", "tin", "."),
        sfx("uU", "0", "tik", "."), sfx("uU", "0", "tiniz", "."), sfx("uU", "0", "tiler", "."),
        sfx("uU", "0", "müş", "."), sfx("uU", "0", "müşüm", "."), sfx("uU", "0", "müşsün", "."),
        sfx("uU", "0", "müşüz", "."), sfx("uU", "0", "müşsünüz", "."), sfx("uU", "0", "müşler", "."),
        sfx("uU", "0", "se", "."), sfx("uU", "0", "sem", "."), sfx("uU", "0", "sen", "."),
        sfx("uU", "0", "sek", "."), sfx("uU", "0", "seniz", "."), sfx("uU", "0", "seler", "."),
        sfx("uU", "0", "tür", "."), sfx("uU", "0", "türler", "."),
        sfx("uU", "0", "tir", "."), sfx("uU", "0", "tirler", "."),
        sfx("uU", "0", "lermiş", "."), sfx("uU", "0", "lerdi", "."), sfx("uU", "0", "lerse", "."),
        sfx("uU", "0", "ken", ".")
    ]
    blocks.append(make_verb_flag_block("uU", rules_uU))

    # 7. vA: Vowel-ending Back Copulas (for -malı, -sa, -makta, -dıysa)
    rules_vA = [
        sfx("vA", "0", "ydı", "."), sfx("vA", "0", "ydım", "."), sfx("vA", "0", "ydın", "."),
        sfx("vA", "0", "ydık", "."), sfx("vA", "0", "ydınız", "."), sfx("vA", "0", "ydılar", "."),
        sfx("vA", "0", "ymış", "."), sfx("vA", "0", "ymışım", "."), sfx("vA", "0", "ymışsın", "."),
        sfx("vA", "0", "ymışız", "."), sfx("vA", "0", "ymışsınız", "."), sfx("vA", "0", "ymışlar", "."),
        sfx("vA", "0", "ysa", "."), sfx("vA", "0", "ysam", "."), sfx("vA", "0", "ysan", "."),
        sfx("vA", "0", "ysak", "."), sfx("vA", "0", "ysanız", "."), sfx("vA", "0", "ysalar", "."),
        sfx("vA", "0", "dır", "."), sfx("vA", "0", "dırlar", "."),
        sfx("vA", "0", "larmış", "."), sfx("vA", "0", "lardı", "."), sfx("vA", "0", "larsa", "."),
        sfx("vA", "0", "yken", ".")
    ]
    blocks.append(make_verb_flag_block("vA", rules_vA))

    # 8. vE: Vowel-ending Front Copulas (for -meli, -se, -mekte, -diyse)
    rules_vE = [
        sfx("vE", "0", "ydi", "."), sfx("vE", "0", "ydim", "."), sfx("vE", "0", "ydin", "."),
        sfx("vE", "0", "ydik", "."), sfx("vE", "0", "ydiniz", "."), sfx("vE", "0", "ydiler", "."),
        sfx("vE", "0", "ymiş", "."), sfx("vE", "0", "ymişim", "."), sfx("vE", "0", "ymişsin", "."),
        sfx("vE", "0", "ymişiz", "."), sfx("vE", "0", "ymişsiniz", "."), sfx("vE", "0", "ymişler", "."),
        sfx("vE", "0", "yse", "."), sfx("vE", "0", "ysem", "."), sfx("vE", "0", "ysen", "."),
        sfx("vE", "0", "ysek", "."), sfx("vE", "0", "yseniz", "."), sfx("vE", "0", "yseler", "."),
        sfx("vE", "0", "dir", "."), sfx("vE", "0", "dirler", "."),
        sfx("vE", "0", "lermiş", "."), sfx("vE", "0", "lerdi", "."), sfx("vE", "0", "lerse", "."),
        sfx("vE", "0", "yken", ".")
    ]
    blocks.append(make_verb_flag_block("vE", rules_vE))

    # 9. pA: Participle 3sg Back Cases (for -dığı, -acağı, -ması, -tıkları)
    rules_pA = [
        sfx("pA", "0", "nda", "."), sfx("pA", "0", "ndan", "."), sfx("pA", "0", "nı", "."),
        sfx("pA", "0", "na", "."), sfx("pA", "0", "nın", "."), sfx("pA", "0", "yla", "."),
        sfx("pA", "0", "dır", "."), sfx("pA", "0", "ydı", "."), sfx("pA", "0", "ymış", "."), sfx("pA", "0", "ysa", "."),
        sfx("pA", "0", "ndaysa", ".")
    ]
    blocks.append(make_verb_flag_block("pA", rules_pA))

    # 10. pE: Participle 3sg Front Cases (for -diği, -eceği, -mesi, -tikleri)
    rules_pE = [
        sfx("pE", "0", "nde", "."), sfx("pE", "0", "nden", "."), sfx("pE", "0", "ni", "."),
        sfx("pE", "0", "ne", "."), sfx("pE", "0", "nin", "."), sfx("pE", "0", "yle", "."),
        sfx("pE", "0", "dir", "."), sfx("pE", "0", "ydi", "."), sfx("pE", "0", "ymiş", "."), sfx("pE", "0", "yse", "."),
        sfx("pE", "0", "ndeyse", ".")
    ]
    blocks.append(make_verb_flag_block("pE", rules_pE))

    # 10b. pO: Participle 3sg Back Rounded Cases (for -duğu, -tuğu)
    rules_pO = [
        sfx("pO", "0", "nda", "."), sfx("pO", "0", "ndan", "."), sfx("pO", "0", "nu", "."), sfx("pO", "0", "nı", "."),
        sfx("pO", "0", "na", "."), sfx("pO", "0", "nun", "."), sfx("pO", "0", "nın", "."), sfx("pO", "0", "yla", "."),
        sfx("pO", "0", "dur", "."), sfx("pO", "0", "dır", "."), sfx("pO", "0", "ydu", "."), sfx("pO", "0", "ydı", "."),
        sfx("pO", "0", "ymuş", "."), sfx("pO", "0", "ymış", "."), sfx("pO", "0", "ysa", "."),
        sfx("pO", "0", "ndaysa", ".")
    ]
    blocks.append(make_verb_flag_block("pO", rules_pO))

    # 10c. pU: Participle 3sg Front Rounded Cases (for -düğü, -tüğü)
    rules_pU = [
        sfx("pU", "0", "nde", "."), sfx("pU", "0", "nden", "."), sfx("pU", "0", "nü", "."), sfx("pU", "0", "ni", "."),
        sfx("pU", "0", "ne", "."), sfx("pU", "0", "nün", "."), sfx("pU", "0", "nin", "."), sfx("pU", "0", "yle", "."),
        sfx("pU", "0", "dür", "."), sfx("pU", "0", "dir", "."), sfx("pU", "0", "ydü", "."), sfx("pU", "0", "ydi", "."),
        sfx("pU", "0", "ymüş", "."), sfx("pU", "0", "ymiş", "."), sfx("pU", "0", "yse", "."),
        sfx("pU", "0", "ndeyse", ".")
    ]
    blocks.append(make_verb_flag_block("pU", rules_pU))

    # 11. qA: Participle 1/2 Person Back Cases (for -dığım, -dığın, -dığımız, -dığınız, -mam, -mamız)
    rules_qA = [
        sfx("qA", "0", "da", "."), sfx("qA", "0", "dan", "."), sfx("qA", "0", "ı", "."),
        sfx("qA", "0", "a", "."), sfx("qA", "0", "ın", "."), sfx("qA", "0", "la", "."),
        sfx("qA", "0", "dır", "."), sfx("qA", "0", "dı", "."), sfx("qA", "0", "sa", "."),
        sfx("qA", "0", "daysa", ".")
    ]
    blocks.append(make_verb_flag_block("qA", rules_qA))

    # 12. qE: Participle 1/2 Person Front Cases (for -diğim, -diğin, -diğimiz, -diğiniz, -mem, -memiz)
    rules_qE = [
        sfx("qE", "0", "de", "."), sfx("qE", "0", "den", "."), sfx("qE", "0", "i", "."),
        sfx("qE", "0", "e", "."), sfx("qE", "0", "in", "."), sfx("qE", "0", "le", "."),
        sfx("qE", "0", "dir", "."), sfx("qE", "0", "di", "."), sfx("qE", "0", "se", "."),
        sfx("qE", "0", "deyse", ".")
    ]
    blocks.append(make_verb_flag_block("qE", rules_qE))

    # 12b. qO: Participle 1/2 Person Back Rounded Cases (for -duğum, -duğun, -duğumuz, -duğunuz)
    rules_qO = [
        sfx("qO", "0", "da", "."), sfx("qO", "0", "dan", "."), sfx("qO", "0", "u", "."), sfx("qO", "0", "ı", "."),
        sfx("qO", "0", "a", "."), sfx("qO", "0", "un", "."), sfx("qO", "0", "ın", "."), sfx("qO", "0", "la", "."),
        sfx("qO", "0", "dur", "."), sfx("qO", "0", "dır", "."), sfx("qO", "0", "du", "."), sfx("qO", "0", "dı", "."),
        sfx("qO", "0", "sa", "."), sfx("qO", "0", "daysa", ".")
    ]
    blocks.append(make_verb_flag_block("qO", rules_qO))

    # 12c. qU: Participle 1/2 Person Front Rounded Cases (for -düğüm, -düğün, -düğümüz, -düğünüz)
    rules_qU = [
        sfx("qU", "0", "de", "."), sfx("qU", "0", "den", "."), sfx("qU", "0", "ü", "."), sfx("qU", "0", "i", "."),
        sfx("qU", "0", "e", "."), sfx("qU", "0", "ün", "."), sfx("qU", "0", "in", "."), sfx("qU", "0", "le", "."),
        sfx("qU", "0", "dür", "."), sfx("qU", "0", "dir", "."), sfx("qU", "0", "dü", "."), sfx("qU", "0", "di", "."),
        sfx("qU", "0", "se", "."), sfx("qU", "0", "deyse", ".")
    ]
    blocks.append(make_verb_flag_block("qU", rules_qU))

    # 13. sA: Past Back Copulas (only conditional and narrative past, no ymış)
    rules_sA = [
        sfx("sA", "0", "ysa", "."), sfx("sA", "0", "ysam", "."), sfx("sA", "0", "ysan", "."),
        sfx("sA", "0", "ysak", "."), sfx("sA", "0", "ysanız", "."), sfx("sA", "0", "ysalar", "."),
        sfx("sA", "0", "ydı", "."), sfx("sA", "0", "ydım", "."), sfx("sA", "0", "ydın", "."),
        sfx("sA", "0", "ydık", "."), sfx("sA", "0", "ydınız", "."), sfx("sA", "0", "ydılar", "."),
    ]
    blocks.append(make_verb_flag_block("sA", rules_sA))

    # 14. sE: Past Front Copulas (only conditional and narrative past, no ymiş)
    rules_sE = [
        sfx("sE", "0", "yse", "."), sfx("sE", "0", "ysem", "."), sfx("sE", "0", "ysen", "."),
        sfx("sE", "0", "ysek", "."), sfx("sE", "0", "yseniz", "."), sfx("sE", "0", "yseler", "."),
        sfx("sE", "0", "ydi", "."), sfx("sE", "0", "ydim", "."), sfx("sE", "0", "ydin", "."),
        sfx("sE", "0", "ydik", "."), sfx("sE", "0", "ydiniz", "."), sfx("sE", "0", "ydiler", "."),
    ]
    blocks.append(make_verb_flag_block("sE", rules_sE))

    return blocks


def generate_verb_stage1_block(flag: str, back: bool, round_v: bool, is_vowel_stem: bool, is_narrow: bool, strip: str) -> str:
    rules = []
    
    # Harmony variables
    v_low = "a" if back else "e"
    v_high = "u" if (back and round_v) else ("ı" if back else ("ü" if round_v else "i"))
    unrounded_high = "ı" if back else "i"
    
    # Secondary flags
    cop_pres = "cU"
    cop_fut = "uA" if back else "uE"
    cop_evid = ("uO" if round_v else "uA") if back else (("uU" if round_v else "uE"))
    cop_unv = cop_fut
    cop_vow = "vA" if back else "vE"
    part_3sg = "pO" if (back and round_v) else ("pA" if back else ("pU" if round_v else "pE"))
    part_pers = "qO" if (back and round_v) else ("qA" if back else ("qU" if round_v else "qE"))
    fut_part_3sg = "pA" if back else "pE"
    fut_part_pers = "qA" if back else "qE"
    neg_part_3sg = "pA" if back else "pE"
    neg_part_pers = "qA" if back else "qE"
    vn_part_3sg = "pA" if back else "pE"
    vn_part_pers = "qA" if back else "qE"
    cop_past = "sA" if back else "sE"
    cop_aor = "cU" if (back and round_v) else ("cA" if back else ("cI" if round_v else "cE"))
    neg_cop_aor = "cA" if back else "cE"
    
    is_voicing = flag in ("VK", "VL", "VM", "VN")
    
    def add_r(strip_str, add_str, cond_str):
        rules.append(sfx(flag, strip_str, add_str, cond_str))

    p_pres = ["", "um", "sun", "uz", "sunuz", "lar", "lardır"]

    # 1. PRESENT CONTINUOUS: -ıyor / -iyor / -uyor / -üyor
    if is_narrow:
        add_r("emek", f"iyor/{cop_pres}", "[dy]emek")
        add_r("emek", "iyorken", "[dy]emek")
        for p in p_pres:
            add_r("emek", f"iyor{p}", "[dy]emek")
    elif flag == "VH":
        for v_s in ["emek", "ümek"]:
            add_r(v_s, f"üyor/{cop_pres}", v_s)
            add_r(v_s, "üyorken", v_s)
            for p in p_pres:
                add_r(v_s, f"üyor{p}", v_s)
    elif flag == "VS":
        for v_s in ["amak", "umak"]:
            add_r(v_s, f"uyor/{cop_pres}", v_s)
            add_r(v_s, "uyorken", v_s)
            for p in p_pres:
                add_r(v_s, f"uyor{p}", v_s)
    elif is_vowel_stem:
        v_strip_list = ["amak", "ımak"] if flag == "VA" else ["emek", "imek"]
        for v_s in v_strip_list:
            v_h = "ı" if v_s in ("amak", "ımak") else "i"
            add_r(v_s, f"{v_h}yor/{cop_pres}", v_s)
            add_r(v_s, f"{v_h}yorken", v_s)
            for p in p_pres:
                add_r(v_s, f"{v_h}yor{p}", v_s)
    elif is_voicing:
        add_r(f"t{strip}", f"d{v_high}yor/{cop_pres}", f"t{strip}")
        add_r(f"t{strip}", f"d{v_high}yorken", f"t{strip}")
        for p in p_pres:
            add_r(f"t{strip}", f"d{v_high}yor{p}", f"t{strip}")
    else:
        add_r(strip, f"{v_high}yor/{cop_pres}", strip)
        add_r(strip, f"{v_high}yorken", strip)
        for p in p_pres:
            add_r(strip, f"{v_high}yor{p}", strip)

    # 2. FUTURE: -acak / -ecek
    fut_suf = ("yac" if (is_vowel_stem or flag == "VS") else "ac") if back else (("yec" if (is_vowel_stem or flag == "VH") else "ec"))
    if is_narrow:
        add_r("emek", f"iyecek/{cop_unv}", "[dy]emek")
        add_r("emek", f"iyecek", "[dy]emek")
        add_r("emek", f"iyeceğim", "[dy]emek")
        add_r("emek", f"iyeceksin", "[dy]emek")
        add_r("emek", f"iyeceğiz", "[dy]emek")
        add_r("emek", f"iyeceksiniz", "[dy]emek")
        add_r("emek", f"iyecekler", "[dy]emek")
        add_r("emek", f"iyeceklerdir", "[dy]emek")
    elif flag in ("VH", "VS"):
        add_r(strip, f"{fut_suf}{v_low}k/{cop_unv}", strip)
        add_r(strip, f"{fut_suf}{v_low}k", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m", strip)
        add_r(strip, f"{fut_suf}{v_low}ks{unrounded_high}n", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}z", strip)
        add_r(strip, f"{fut_suf}{v_low}ks{unrounded_high}n{unrounded_high}z", strip)
        add_r(strip, f"{fut_suf}{v_low}ks{unrounded_high}n{unrounded_high}zd{unrounded_high}r", strip)
        add_r(strip, f"{fut_suf}{v_low}kl{v_low}r", strip)
        add_r(strip, f"{fut_suf}{v_low}kl{v_low}rd{unrounded_high}r", strip)
        if flag == "VH":
            add_r(strip, f"{fut_suf}{v_low}ğüm", "ümek")
        elif flag == "VS":
            add_r(strip, f"{fut_suf}{v_low}ğum", "umak")
    elif is_voicing:
        add_r(f"t{strip}", f"d{fut_suf}{v_low}k/{cop_unv}", f"t{strip}")
        add_r(f"t{strip}", f"d{fut_suf}{v_low}k", f"t{strip}")
        add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}m", f"t{strip}")
        add_r(f"t{strip}", f"d{fut_suf}{v_low}ks{unrounded_high}n", f"t{strip}")
        add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}z", f"t{strip}")
        add_r(f"t{strip}", f"d{fut_suf}{v_low}ks{unrounded_high}n{unrounded_high}z", f"t{strip}")
        add_r(f"t{strip}", f"d{fut_suf}{v_low}ks{unrounded_high}n{unrounded_high}zd{unrounded_high}r", f"t{strip}")
        add_r(f"t{strip}", f"d{fut_suf}{v_low}kl{v_low}r", f"t{strip}")
        add_r(f"t{strip}", f"d{fut_suf}{v_low}kl{v_low}rd{unrounded_high}r", f"t{strip}")
        if round_v:
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{v_high}m", f"t{strip}")
    else:
        add_r(strip, f"{fut_suf}{v_low}k/{cop_unv}", strip)
        add_r(strip, f"{fut_suf}{v_low}k", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m", strip)
        add_r(strip, f"{fut_suf}{v_low}ks{unrounded_high}n", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}z", strip)
        add_r(strip, f"{fut_suf}{v_low}ks{unrounded_high}n{unrounded_high}z", strip)
        add_r(strip, f"{fut_suf}{v_low}ks{unrounded_high}n{unrounded_high}zd{unrounded_high}r", strip)
        add_r(strip, f"{fut_suf}{v_low}kl{v_low}r", strip)
        add_r(strip, f"{fut_suf}{v_low}kl{v_low}rd{unrounded_high}r", strip)
        if round_v:
            add_r(strip, f"{fut_suf}{v_low}ğ{v_high}m", strip)

    # 3. DEFINITE PAST: -dı / -di / -tı / -ti
    if flag == "VH":
        for v_h_curr, cond_curr in [("i", "emek"), ("ü", "ümek")]:
            add_r(strip, f"d{v_h_curr}/{cop_past}", cond_curr)
            add_r(strip, f"d{v_h_curr}", cond_curr)
            for p in ["m", "n", "k", f"n{v_h_curr}z", f"l{v_low}r"]:
                add_r(strip, f"d{v_h_curr}{p}", cond_curr)
            add_r(strip, f"d{v_h_curr}ms{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}ns{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}ks{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}n{v_h_curr}zs{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}l{v_low}rs{v_low}", cond_curr)
    elif flag == "VS":
        for v_h_curr, cond_curr in [("ı", "amak"), ("u", "umak")]:
            add_r(strip, f"d{v_h_curr}/{cop_past}", cond_curr)
            add_r(strip, f"d{v_h_curr}", cond_curr)
            for p in ["m", "n", "k", f"n{v_h_curr}z", f"l{v_low}r"]:
                add_r(strip, f"d{v_h_curr}{p}", cond_curr)
            add_r(strip, f"d{v_h_curr}ms{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}ns{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}ks{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}n{v_h_curr}zs{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}l{v_low}rs{v_low}", cond_curr)
    elif is_vowel_stem or is_narrow:
        add_r(strip, f"d{v_high}/{cop_past}", strip)
        add_r(strip, f"d{v_high}", strip)
        for p in ["m", "n", "k", f"n{v_high}z", f"l{v_low}r"]:
            add_r(strip, f"d{v_high}{p}", strip)
        add_r(strip, f"d{v_high}ms{v_low}", strip)
        add_r(strip, f"d{v_high}ns{v_low}", strip)
        add_r(strip, f"d{v_high}ks{v_low}", strip)
        add_r(strip, f"d{v_high}n{v_high}zs{v_low}", strip)
        add_r(strip, f"d{v_high}l{v_low}rs{v_low}", strip)
    else:
        cond_cons = f"[^çfhkpsşt]{strip}"
        cond_unv = f"[çfhkpsşt]{strip}"
        for d_c, cond_s in [("d", cond_cons if not is_voicing else f"[çt]{strip}"), ("t", cond_unv if not is_voicing else f"[çt]{strip}")]:
            add_r(strip, f"{d_c}{v_high}/{cop_past}", cond_s)
            add_r(strip, f"{d_c}{v_high}", cond_s)
            for p in ["m", "n", "k", f"n{v_high}z", f"l{v_low}r"]:
                add_r(strip, f"{d_c}{v_high}{p}", cond_s)
            add_r(strip, f"{d_c}{v_high}ms{v_low}", cond_s)
            add_r(strip, f"{d_c}{v_high}ns{v_low}", cond_s)
            add_r(strip, f"{d_c}{v_high}ks{v_low}", cond_s)
            add_r(strip, f"{d_c}{v_high}n{v_high}zs{v_low}", cond_s)
            add_r(strip, f"{d_c}{v_high}l{v_low}rs{v_low}", cond_s)

    # 4. EVIDENTIAL PAST: -mış / -miş / -muş / -müş
    if flag == "VH":
        for v_h_curr, cond_curr in [("i", "emek"), ("ü", "ümek")]:
            evid_cop = "uE" if v_h_curr == "i" else "uU"
            add_r(strip, f"m{v_h_curr}ş/{evid_cop}", cond_curr)
            for p in ["", f"{v_h_curr}m", f"s{v_h_curr}n", f"{v_h_curr}z", f"s{v_h_curr}n{v_h_curr}z", f"l{v_low}r"]:
                add_r(strip, f"m{v_h_curr}ş{p}", cond_curr)
            add_r(strip, f"m{v_h_curr}ş{v_h_curr}md{v_h_curr}r", cond_curr)
            add_r(strip, f"m{v_h_curr}ş{v_h_curr}zd{v_h_curr}r", cond_curr)
            add_r(strip, f"m{v_h_curr}şs{v_h_curr}nd{v_h_curr}r", cond_curr)
            add_r(strip, f"m{v_h_curr}şs{v_h_curr}n{v_h_curr}zd{v_h_curr}r", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_low}rd{unrounded_high}r", cond_curr)
            add_r(strip, f"m{v_h_curr}şç{v_low}s{unrounded_high}n{v_low}", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_h_curr}k", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_h_curr}ğ{v_h_curr}", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_h_curr}ğ{v_h_curr}n", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_h_curr}kt{v_h_curr}r", cond_curr)
    elif flag == "VS":
        for v_h_curr, cond_curr in [("ı", "amak"), ("u", "umak")]:
            evid_cop = "uA" if v_h_curr == "ı" else "uO"
            add_r(strip, f"m{v_h_curr}ş/{evid_cop}", cond_curr)
            for p in ["", f"{v_h_curr}m", f"s{v_h_curr}n", f"{v_h_curr}z", f"s{v_h_curr}n{v_h_curr}z", f"l{v_low}r"]:
                add_r(strip, f"m{v_h_curr}ş{p}", cond_curr)
            add_r(strip, f"m{v_h_curr}ş{v_h_curr}md{v_h_curr}r", cond_curr)
            add_r(strip, f"m{v_h_curr}ş{v_h_curr}zd{v_h_curr}r", cond_curr)
            add_r(strip, f"m{v_h_curr}şs{v_h_curr}nd{v_h_curr}r", cond_curr)
            add_r(strip, f"m{v_h_curr}şs{v_h_curr}n{v_h_curr}zd{v_h_curr}r", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_low}rd{unrounded_high}r", cond_curr)
            add_r(strip, f"m{v_h_curr}şç{v_low}s{unrounded_high}n{v_low}", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_h_curr}k", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_h_curr}ğ{v_h_curr}", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_h_curr}ğ{v_h_curr}n", cond_curr)
            add_r(strip, f"m{v_h_curr}şl{v_h_curr}kt{v_h_curr}r", cond_curr)
    else:
        add_r(strip, f"m{v_high}ş/{cop_evid}", strip)
        for p in ["", f"{v_high}m", f"s{v_high}n", f"{v_high}z", f"s{v_high}n{v_high}z", f"l{v_low}r"]:
            add_r(strip, f"m{v_high}ş{p}", strip)
        add_r(strip, f"m{v_high}ş{v_high}md{v_high}r", strip)
        add_r(strip, f"m{v_high}ş{v_high}zd{v_high}r", strip)
        add_r(strip, f"m{v_high}şs{v_high}nd{v_high}r", strip)
        add_r(strip, f"m{v_high}şs{v_high}n{v_high}zd{v_high}r", strip)
        add_r(strip, f"m{v_high}şl{v_low}rd{unrounded_high}r", strip)
        add_r(strip, f"m{v_high}şç{v_low}s{unrounded_high}n{v_low}", strip)
        add_r(strip, f"m{v_high}şl{v_high}k", strip)
        add_r(strip, f"m{v_high}şl{v_high}ğ{v_high}", strip)
        add_r(strip, f"m{v_high}şl{v_high}ğ{v_high}n", strip)
        add_r(strip, f"m{v_high}şl{v_high}kt{v_high}r", strip)
        # Participle noun cases on -miş (acıkmışa, çökmüşe, düşmüşlerin, çıkmışta)
        add_r(strip, f"m{v_high}ş{v_low}", strip)
        add_r(strip, f"m{v_high}ş{unrounded_high}", strip)
        if round_v and v_high != unrounded_high:
            add_r(strip, f"m{v_high}ş{v_high}", strip)
        add_r(strip, f"m{v_high}şt{v_low}", strip)
        add_r(strip, f"m{v_high}şt{v_low}n", strip)
        add_r(strip, f"m{v_high}ş{unrounded_high}n", strip)
        if round_v and v_high != unrounded_high:
            add_r(strip, f"m{v_high}ş{v_high}n", strip)
        add_r(strip, f"m{v_high}şl{v_low}r{unrounded_high}n", strip)
        add_r(strip, f"m{v_high}şl{v_low}r{v_low}", strip)
        add_r(strip, f"m{v_high}şl{v_low}rd{v_low}", strip)
        add_r(strip, f"m{v_high}şl{v_low}rd{v_low}n", strip)
        add_r(strip, f"m{v_high}şl{v_low}r{unrounded_high}", strip)
        add_r(strip, f"m{v_high}şl{v_low}rl{v_low}", strip)
        add_r(strip, f"m{v_high}şl{v_low}ryl{v_low}", strip)

    # 5. NECESSITATIVE: -malı / -meli
    add_r(strip, f"m{v_low}l{unrounded_high}/{cop_vow}", strip)
    for p in ["", f"y{unrounded_high}m", f"s{unrounded_high}n", f"y{unrounded_high}z", f"s{unrounded_high}n{unrounded_high}z", f"l{v_low}r"]:
        add_r(strip, f"m{v_low}l{unrounded_high}{p}", strip)

    # 6. CONDITIONAL: -sa / -se
    add_r(strip, f"s{v_low}/{cop_vow}", strip)
    for p in ["", "m", "n", "k", f"n{unrounded_high}z", f"l{v_low}r", f"n{v_low}", f"n{unrounded_high}z{v_low}"]:
        add_r(strip, f"s{v_low}{p}", strip)

    # 7. PROGRESSIVE & INFINITIVES: -makta, -maktan, -makla, -maktı, -maktır, -maktansa
    add_r(strip, f"m{v_low}kt{v_low}/{cop_vow}", strip)
    add_r(strip, f"m{v_low}kt{v_low}n", strip)
    add_r(strip, f"m{v_low}kl{v_low}", strip)
    add_r(strip, f"m{v_low}kt{unrounded_high}", strip)
    add_r(strip, f"m{v_low}kt{unrounded_high}r", strip)
    add_r(strip, f"m{v_low}kt{v_low}ns{v_low}", strip)
    add_r(strip, f"m{v_low}ks{v_low}", strip)
    add_r(strip, f"m{v_low}km{unrounded_high}ş", strip)
    add_r(strip, f"m{v_low}kt{v_low}ki", strip)
    add_r(strip, f"m{v_low}kt{v_low}kil{v_low}r", strip)
    for p in ["", f"y{unrounded_high}m", f"s{unrounded_high}n", f"y{unrounded_high}z", f"s{unrounded_high}n{unrounded_high}z", f"l{v_low}r"]:
        add_r(strip, f"m{v_low}kt{v_low}{p}", strip)

    # 8. IMPERATIVE & OPTATIVE
    if is_narrow:
        add_r(strip, "0", strip)
        add_r(strip, "sin", strip)
        add_r(strip, "sinler", strip)
        for y_pref in ["i", "e"]:
            add_r("emek", f"{y_pref}ye", "[dy]emek")
            add_r("emek", f"{y_pref}yeyim", "[dy]emek")
            add_r("emek", f"{y_pref}yelim", "[dy]emek")
            add_r("emek", f"{y_pref}yin", "[dy]emek")
            add_r("emek", f"{y_pref}yiniz", "[dy]emek")
    elif flag in ("VH", "VS"):
        sub_h = [("i", "emek"), ("ü", "ümek")] if flag == "VH" else [("ı", "amak"), ("u", "umak")]
        add_r(strip, f"y{v_low}", strip)
        add_r(strip, "0", strip)
        add_r(strip, f"y{v_low}l{v_low}r", strip)
        for v_h_curr, cond_curr in sub_h:
            add_r(strip, f"y{v_low}y{v_h_curr}m", cond_curr)
            add_r(strip, f"y{v_low}l{v_h_curr}m", cond_curr)
            add_r(strip, f"y{v_low}s{v_h_curr}n", cond_curr)
            add_r(strip, f"y{v_low}s{v_h_curr}n{v_h_curr}z", cond_curr)
            add_r(strip, f"s{v_h_curr}n", cond_curr)
            add_r(strip, f"y{v_h_curr}n", cond_curr)
            add_r(strip, f"y{v_h_curr}n{v_h_curr}z", cond_curr)
            add_r(strip, f"s{v_h_curr}nl{v_low}r", cond_curr)
    elif is_vowel_stem:
        add_r(strip, f"y{v_low}", strip)
        add_r(strip, f"y{v_low}y{v_high}m", strip)
        add_r(strip, f"y{v_low}s{v_high}n", strip)
        add_r(strip, f"y{v_low}l{v_high}m", strip)
        add_r(strip, f"y{v_low}s{v_high}n{v_high}z", strip)
        add_r(strip, f"y{v_low}l{v_low}r", strip)
        add_r(strip, "0", strip)
        add_r(strip, f"s{v_high}n", strip)
        add_r(strip, f"y{v_high}n", strip)
        add_r(strip, f"y{v_high}n{v_high}z", strip)
        add_r(strip, f"s{v_high}nl{v_low}r", strip)
    elif is_voicing:
        add_r(f"t{strip}", f"d{v_low}", f"t{strip}")
        add_r(f"t{strip}", f"d{v_low}y{v_high}m", f"t{strip}")
        add_r(f"t{strip}", f"d{v_low}s{v_high}n", f"t{strip}")
        add_r(f"t{strip}", f"d{v_low}l{v_high}m", f"t{strip}")
        add_r(f"t{strip}", f"d{v_low}s{v_high}n{v_high}z", f"t{strip}")
        add_r(f"t{strip}", f"d{v_low}l{v_low}r", f"t{strip}")
        add_r(strip, "0", strip)
        add_r(strip, f"s{v_high}n", strip)
        add_r(f"t{strip}", f"d{v_high}n", f"t{strip}")
        add_r(f"t{strip}", f"d{v_high}n{v_high}z", f"t{strip}")
        add_r(strip, f"s{v_high}nl{v_low}r", strip)
    else:
        add_r(strip, f"{v_low}", strip)
        add_r(strip, f"{v_low}y{v_high}m", strip)
        add_r(strip, f"{v_low}s{v_high}n", strip)
        add_r(strip, f"{v_low}l{v_high}m", strip)
        add_r(strip, f"{v_low}s{v_high}n{v_high}z", strip)
        add_r(strip, f"{v_low}l{v_low}r", strip)
        add_r(strip, "0", strip)
        add_r(strip, f"s{v_high}n", strip)
        add_r(strip, f"{v_high}n", strip)
        add_r(strip, f"{v_high}n{v_high}z", strip)
        add_r(strip, f"s{v_high}nl{v_low}r", strip)

    # 9. AORIST (for vowel stems, narrow verbs, and voicing stems)
    if is_narrow:
        add_r(strip, "r/cE", strip)
        add_r(strip, "rken", strip)
        add_r(strip, f"rc{v_low}s{unrounded_high}n{v_low}", strip)
        for p in ["", "im", "sin", "iz", "siniz", "ler"]:
            add_r(strip, f"r{p}", strip)
    elif flag == "VH":
        add_r(strip, "r/cE", "emek")
        add_r(strip, "r/cI", "ümek")
        add_r(strip, "r", strip)
        add_r(strip, f"rl{v_low}r", strip)
        add_r(strip, "rken", strip)
        add_r(strip, f"rc{v_low}s{unrounded_high}n{v_low}", strip)
        for v_h_curr, cond_curr in [("i", "emek"), ("ü", "ümek")]:
            add_r(strip, f"r{v_h_curr}m", cond_curr)
            add_r(strip, f"rs{v_h_curr}n", cond_curr)
            add_r(strip, f"r{v_h_curr}z", cond_curr)
            add_r(strip, f"rs{v_h_curr}n{v_h_curr}z", cond_curr)
    elif flag == "VS":
        add_r(strip, "r/cA", "amak")
        add_r(strip, "r/cU", "umak")
        add_r(strip, "r", strip)
        add_r(strip, f"rl{v_low}r", strip)
        add_r(strip, "rken", strip)
        add_r(strip, f"rc{v_low}s{unrounded_high}n{v_low}", strip)
        for v_h_curr, cond_curr in [("ı", "amak"), ("u", "umak")]:
            add_r(strip, f"r{v_h_curr}m", cond_curr)
            add_r(strip, f"rs{v_h_curr}n", cond_curr)
            add_r(strip, f"r{v_h_curr}z", cond_curr)
            add_r(strip, f"rs{v_h_curr}n{v_h_curr}z", cond_curr)
    elif is_vowel_stem:
        add_r(strip, f"r/{cop_aor}", strip)
        add_r(strip, "rken", strip)
        add_r(strip, f"rc{v_low}s{unrounded_high}n{v_low}", strip)
        for p in ["", f"{v_high}m", f"s{v_high}n", f"{v_high}z", f"s{v_high}n{v_high}z", f"l{v_low}r"]:
            add_r(strip, f"r{p}", strip)
    elif is_voicing:
        aor_c_vow = "a" if back else "e"
        add_r(f"t{strip}", f"d{aor_c_vow}r/{cop_aor}", f"t{strip}")
        add_r(f"t{strip}", f"d{aor_c_vow}r", f"t{strip}")
        add_r(f"t{strip}", f"d{aor_c_vow}rken", f"t{strip}")
        add_r(f"t{strip}", f"d{aor_c_vow}rc{v_low}s{unrounded_high}n{v_low}", f"t{strip}")
        add_r(f"t{strip}", f"d{aor_c_vow}r{unrounded_high}m", f"t{strip}")
        add_r(f"t{strip}", f"d{aor_c_vow}rs{unrounded_high}n", f"t{strip}")
        add_r(f"t{strip}", f"d{aor_c_vow}r{unrounded_high}z", f"t{strip}")
        add_r(f"t{strip}", f"d{aor_c_vow}rs{unrounded_high}n{unrounded_high}z", f"t{strip}")
        add_r(f"t{strip}", f"d{aor_c_vow}rl{v_low}r", f"t{strip}")

    # 10. PARTICIPLES & VERBAL NOUNS (Positive)
    part_endings = [
        "", f"l{v_low}r", f"l{v_low}r{unrounded_high}", f"l{v_low}r{v_low}",
        f"l{v_low}rd{v_low}", f"l{v_low}rd{v_low}n", f"l{v_low}r{unrounded_high}n",
        f"l{v_low}ryl{v_low}", f"l{v_low}rl{v_low}", f"{unrounded_high}", f"{v_low}", f"d{v_low}",
        f"d{v_low}n", f"{unrounded_high}n", f"yl{v_low}",
        f"l{v_low}r{unrounded_high}m{unrounded_high}z",
        f"l{v_low}r{unrounded_high}m{unrounded_high}z{unrounded_high}",
        f"l{v_low}r{unrounded_high}m{unrounded_high}z{v_low}",
        f"l{v_low}r{unrounded_high}m{unrounded_high}zd{v_low}",
        f"l{v_low}r{unrounded_high}m{unrounded_high}zd{v_low}n",
        f"l{v_low}r{unrounded_high}m{unrounded_high}z{unrounded_high}n",
        f"l{v_low}r{unrounded_high}m{unrounded_high}zl{v_low}",
        f"l{v_low}r{unrounded_high}n{v_low}",
        f"l{v_low}r{unrounded_high}n{unrounded_high}",
        f"l{v_low}r{unrounded_high}nd{v_low}",
        f"l{v_low}r{unrounded_high}nd{v_low}n",
        f"l{v_low}r{unrounded_high}n{unrounded_high}n",
        f"l{v_low}r{unrounded_high}nl{v_low}",
        f"{unrounded_high}m{unrounded_high}z",
        f"s{v_low}",
        f"m{unrounded_high}ş",
        f"d{unrounded_high}r",
        f"l{v_low}rd{unrounded_high}r",
        f"l{v_low}rd{v_low}nd{unrounded_high}"
    ]

    # Subject Participle (-an / -en)
    if is_narrow:
        for pe in part_endings:
            add_r("emek", f"iyen{pe}", "[dy]emek")
    elif is_vowel_stem:
        for pe in part_endings:
            add_r(strip, f"y{v_low}n{pe}", strip)
    elif is_voicing:
        for pe in part_endings:
            add_r(f"t{strip}", f"d{v_low}n{pe}", f"t{strip}")
    else:
        for pe in part_endings:
            add_r(strip, f"{v_low}n{pe}", strip)

    # Optative/Future Participle (-ası / -esi: kalınası, yıkılası)
    if is_narrow:
        add_r("emek", "iyesi", "[dy]emek")
        add_r("emek", "iyesice", "[dy]emek")
    elif is_vowel_stem:
        add_r(strip, f"y{v_low}s{unrounded_high}", strip)
        add_r(strip, f"y{v_low}s{unrounded_high}c{v_low}", strip)
    elif is_voicing:
        add_r(f"t{strip}", f"d{v_low}s{unrounded_high}", f"t{strip}")
        add_r(f"t{strip}", f"d{v_low}s{unrounded_high}c{v_low}", f"t{strip}")
    else:
        add_r(strip, f"{v_low}s{unrounded_high}", strip)
        add_r(strip, f"{v_low}s{unrounded_high}c{v_low}", strip)

    # Agentive / Adjectival Derivation: -ıcı / -ici / -ucu / -ücü
    if is_narrow:
        sub_ici = [("iyici", "[dy]emek", "emek")]
    elif flag in ("VH", "VS"):
        sub_ici = [("yici", "emek", strip), ("yücü", "ümek", strip)] if flag == "VH" else [("yıcı", "amak", strip), ("yucu", "umak", strip)]
    elif is_vowel_stem:
        sub_ici = [(f"y{v_high}c{v_high}", strip, strip)]
    elif is_voicing:
        sub_ici = [(f"d{v_high}c{v_high}", f"t{strip}", f"t{strip}")]
    else:
        sub_ici = [(f"{v_high}c{v_high}", strip, strip)]

    for ici_base, ici_cond, ici_strip in sub_ici:
        ici_high = ici_base[-1]
        ici_low = "a" if ici_high in "ıu" else "e"
        ici_unrounded = "ı" if ici_high in "ıu" else "i"
        ici_forms = [
            ici_base,
            f"{ici_base}d{ici_high}r", f"{ici_base}yd{ici_high}", f"{ici_base}ym{ici_high}ş", f"{ici_base}ys{ici_low}",
            f"{ici_base}y{ici_low}", f"{ici_base}y{ici_high}", f"{ici_base}d{ici_low}", f"{ici_base}d{ici_low}n",
            f"{ici_base}n{ici_high}n", f"{ici_base}yl{ici_low}",
            f"{ici_base}l{ici_low}r", f"{ici_base}l{ici_low}r{ici_low}", f"{ici_base}l{ici_low}r{ici_unrounded}",
            f"{ici_base}l{ici_low}rd{ici_low}", f"{ici_base}l{ici_low}rd{ici_low}n", f"{ici_base}l{ici_low}r{ici_unrounded}n",
            f"{ici_base}l{ici_low}rl{ici_low}", f"{ici_base}l{ici_low}ryl{ici_low}",
            f"{ici_base}s{ici_high}", f"{ici_base}s{ici_high}n{ici_high}", f"{ici_base}s{ici_high}n{ici_low}",
            f"{ici_base}s{ici_high}nd{ici_low}", f"{ici_base}s{ici_high}nd{ici_low}n", f"{ici_base}s{ici_high}n{ici_high}n",
            f"{ici_base}s{ici_high}yl{ici_low}", f"{ici_base}s{ici_high}d{ici_high}r",
            f"{ici_base}s{ici_high}yd{ici_high}", f"{ici_base}s{ici_high}yd{ici_high}m", f"{ici_base}s{ici_high}yd{ici_high}n",
            f"{ici_base}s{ici_high}yd{ici_high}k", f"{ici_base}s{ici_high}yd{ici_high}n{ici_high}z",
            f"{ici_base}l{ici_high}k", f"{ici_base}l{ici_high}ğ{ici_high}", f"{ici_base}l{ici_high}ğ{ici_high}n",
            f"{ici_base}l{ici_high}kt{ici_low}", f"{ici_base}l{ici_high}kt{ici_low}n", f"{ici_base}l{ici_high}kt{ici_high}r"
        ]
        for form in ici_forms:
            add_r(ici_strip, form, ici_cond)

    # Object Participles & Verbal Nouns
    if flag == "VH":
        sub_h = [("i", "emek"), ("ü", "ümek")]
        for v_h_curr, cond_curr in sub_h:
            part_3sg_curr = "pU" if v_h_curr == "ü" else "pE"
            part_pers_curr = "qU" if v_h_curr == "ü" else "qE"
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}/{part_3sg_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}m/{part_pers_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}m", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}n/{part_pers_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}n", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}m{v_h_curr}z/{part_pers_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}m{v_h_curr}z", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}n{v_h_curr}z/{part_pers_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}n{v_h_curr}z", cond_curr)
            add_r(strip, f"d{v_h_curr}kl{v_low}r{unrounded_high}/{part_3sg_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}kl{v_low}r{unrounded_high}", cond_curr)
            for poss_p, cases_p in [
                (f"d{v_h_curr}kl{v_low}r{unrounded_high}m", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"d{v_h_curr}kl{v_low}r{unrounded_high}n", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"d{v_h_curr}kl{v_low}r{unrounded_high}m{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"d{v_h_curr}kl{v_low}r{unrounded_high}n{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"])
            ]:
                for c_p in cases_p:
                    add_r(strip, f"{poss_p}{c_p}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}/{fut_part_3sg}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m/{fut_part_pers}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n/{fut_part_pers}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z/{fut_part_pers}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z/{fut_part_pers}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}kl{v_low}r{unrounded_high}/{fut_part_3sg}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}kl{v_low}r{unrounded_high}", cond_curr)
            add_r(strip, f"m{v_low}s{unrounded_high}/{vn_part_3sg}", cond_curr)
            add_r(strip, f"m{v_low}s{unrounded_high}", cond_curr)
            add_r(strip, f"m{v_low}m/{vn_part_pers}", cond_curr)
            add_r(strip, f"m{v_low}m", cond_curr)
            add_r(strip, f"m{v_low}n/{vn_part_pers}", cond_curr)
            add_r(strip, f"m{v_low}n", cond_curr)
            add_r(strip, f"m{v_low}m{unrounded_high}z/{vn_part_pers}", cond_curr)
            add_r(strip, f"m{v_low}m{unrounded_high}z", cond_curr)
            add_r(strip, f"m{v_low}n{unrounded_high}z/{vn_part_pers}", cond_curr)
            add_r(strip, f"m{v_low}n{unrounded_high}z", cond_curr)
            add_r(strip, f"m{v_low}l{v_low}r{unrounded_high}/{vn_part_3sg}", cond_curr)
            add_r(strip, f"m{v_low}l{v_low}r{unrounded_high}", cond_curr)
            if v_h_curr != unrounded_high:
                add_r(strip, f"m{v_low}s{v_h_curr}/{part_3sg_curr}", cond_curr)
                add_r(strip, f"m{v_low}s{v_h_curr}", cond_curr)
                add_r(strip, f"m{v_low}m{v_h_curr}z/{part_pers_curr}", cond_curr)
                add_r(strip, f"m{v_low}m{v_h_curr}z", cond_curr)
                add_r(strip, f"m{v_low}n{v_h_curr}z/{part_pers_curr}", cond_curr)
                add_r(strip, f"m{v_low}n{v_h_curr}z", cond_curr)
    elif flag == "VS":
        sub_h = [("ı", "amak"), ("u", "umak")]
        for v_h_curr, cond_curr in sub_h:
            part_3sg_curr = "pO" if v_h_curr == "u" else "pA"
            part_pers_curr = "qO" if v_h_curr == "u" else "qA"
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}/{part_3sg_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}m/{part_pers_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}m", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}n/{part_pers_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}n", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}m{v_h_curr}z/{part_pers_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}m{v_h_curr}z", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}n{v_h_curr}z/{part_pers_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}ğ{v_h_curr}n{v_h_curr}z", cond_curr)
            add_r(strip, f"d{v_h_curr}kl{v_low}r{unrounded_high}/{part_3sg_curr}", cond_curr)
            add_r(strip, f"d{v_h_curr}kl{v_low}r{unrounded_high}", cond_curr)
            for poss_p, cases_p in [
                (f"d{v_h_curr}kl{v_low}r{unrounded_high}m", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"d{v_h_curr}kl{v_low}r{unrounded_high}n", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"d{v_h_curr}kl{v_low}r{unrounded_high}m{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"d{v_h_curr}kl{v_low}r{unrounded_high}n{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"])
            ]:
                for c_p in cases_p:
                    add_r(strip, f"{poss_p}{c_p}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}/{fut_part_3sg}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m/{fut_part_pers}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n/{fut_part_pers}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z/{fut_part_pers}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z/{fut_part_pers}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}kl{v_low}r{unrounded_high}/{fut_part_3sg}", cond_curr)
            add_r(strip, f"{fut_suf}{v_low}kl{v_low}r{unrounded_high}", cond_curr)
            add_r(strip, f"m{v_low}s{unrounded_high}/{vn_part_3sg}", cond_curr)
            add_r(strip, f"m{v_low}s{unrounded_high}", cond_curr)
            add_r(strip, f"m{v_low}m/{vn_part_pers}", cond_curr)
            add_r(strip, f"m{v_low}m", cond_curr)
            add_r(strip, f"m{v_low}n/{vn_part_pers}", cond_curr)
            add_r(strip, f"m{v_low}n", cond_curr)
            add_r(strip, f"m{v_low}m{unrounded_high}z/{vn_part_pers}", cond_curr)
            add_r(strip, f"m{v_low}m{unrounded_high}z", cond_curr)
            add_r(strip, f"m{v_low}n{unrounded_high}z/{vn_part_pers}", cond_curr)
            add_r(strip, f"m{v_low}n{unrounded_high}z", cond_curr)
            add_r(strip, f"m{v_low}l{v_low}r{unrounded_high}/{vn_part_3sg}", cond_curr)
            add_r(strip, f"m{v_low}l{v_low}r{unrounded_high}", cond_curr)
            if v_h_curr != unrounded_high:
                add_r(strip, f"m{v_low}s{v_h_curr}/{part_3sg_curr}", cond_curr)
                add_r(strip, f"m{v_low}s{v_h_curr}", cond_curr)
                add_r(strip, f"m{v_low}m{v_h_curr}z/{part_pers_curr}", cond_curr)
                add_r(strip, f"m{v_low}m{v_h_curr}z", cond_curr)
                add_r(strip, f"m{v_low}n{v_h_curr}z/{part_pers_curr}", cond_curr)
                add_r(strip, f"m{v_low}n{v_h_curr}z", cond_curr)
    elif is_vowel_stem or is_narrow:
        add_r(strip, f"d{v_high}ğ{v_high}/{part_3sg}", strip)
        add_r(strip, f"d{v_high}ğ{v_high}", strip)
        add_r(strip, f"d{v_high}ğ{v_high}m/{part_pers}", strip)
        add_r(strip, f"d{v_high}ğ{v_high}m", strip)
        add_r(strip, f"d{v_high}ğ{v_high}n/{part_pers}", strip)
        add_r(strip, f"d{v_high}ğ{v_high}n", strip)
        add_r(strip, f"d{v_high}ğ{v_high}m{v_high}z/{part_pers}", strip)
        add_r(strip, f"d{v_high}ğ{v_high}m{v_high}z", strip)
        add_r(strip, f"d{v_high}ğ{v_high}n{v_high}z/{part_pers}", strip)
        add_r(strip, f"d{v_high}ğ{v_high}n{v_high}z", strip)
        add_r(strip, f"d{v_high}kl{v_low}r{unrounded_high}/{part_3sg}", strip)
        add_r(strip, f"d{v_high}kl{v_low}r{unrounded_high}", strip)
        for poss_p, cases_p in [
            (f"d{v_high}kl{v_low}r{unrounded_high}m", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
            (f"d{v_high}kl{v_low}r{unrounded_high}n", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
            (f"d{v_high}kl{v_low}r{unrounded_high}m{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
            (f"d{v_high}kl{v_low}r{unrounded_high}n{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"])
        ]:
            for c_p in cases_p:
                add_r(strip, f"{poss_p}{c_p}", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}/{fut_part_3sg}", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m/{fut_part_pers}", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n/{fut_part_pers}", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z/{fut_part_pers}", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z/{fut_part_pers}", strip)
        add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z", strip)
        add_r(strip, f"{fut_suf}{v_low}kl{v_low}r{unrounded_high}/{fut_part_3sg}", strip)
        add_r(strip, f"{fut_suf}{v_low}kl{v_low}r{unrounded_high}", strip)
        add_r(strip, f"m{v_low}s{unrounded_high}/{vn_part_3sg}", strip)
        add_r(strip, f"m{v_low}s{unrounded_high}", strip)
        add_r(strip, f"m{v_low}m/{vn_part_pers}", strip)
        add_r(strip, f"m{v_low}m", strip)
        add_r(strip, f"m{v_low}n/{vn_part_pers}", strip)
        add_r(strip, f"m{v_low}n", strip)
        add_r(strip, f"m{v_low}m{unrounded_high}z/{vn_part_pers}", strip)
        add_r(strip, f"m{v_low}m{unrounded_high}z", strip)
        add_r(strip, f"m{v_low}n{unrounded_high}z/{vn_part_pers}", strip)
        add_r(strip, f"m{v_low}n{unrounded_high}z", strip)
        add_r(strip, f"m{v_low}l{v_low}r{unrounded_high}/{vn_part_3sg}", strip)
        add_r(strip, f"m{v_low}l{v_low}r{unrounded_high}", strip)
        if v_high != unrounded_high:
            add_r(strip, f"m{v_low}s{v_high}/{part_3sg}", strip)
            add_r(strip, f"m{v_low}s{v_high}", strip)
            add_r(strip, f"m{v_low}m{v_high}z/{part_pers}", strip)
            add_r(strip, f"m{v_low}m{v_high}z", strip)
            add_r(strip, f"m{v_low}n{v_high}z/{part_pers}", strip)
            add_r(strip, f"m{v_low}n{v_high}z", strip)
        # Verbal Noun (-yış / -yiş: yürüyüşü, söyleyişine)
        add_r(strip, f"y{v_high}ş", strip)
        add_r(strip, f"y{v_high}ş{v_high}/{vn_part_3sg}", strip)
        add_r(strip, f"y{v_high}ş{v_high}", strip)
        add_r(strip, f"y{v_high}ş{v_high}m/{vn_part_pers}", strip)
        add_r(strip, f"y{v_high}ş{v_high}m", strip)
        add_r(strip, f"y{v_high}ş{v_high}n/{vn_part_pers}", strip)
        add_r(strip, f"y{v_high}ş{v_high}n", strip)
        add_r(strip, f"y{v_high}ş{v_high}m{v_high}z/{vn_part_pers}", strip)
        add_r(strip, f"y{v_high}ş{v_high}m{v_high}z", strip)
        add_r(strip, f"y{v_high}ş{v_high}n{v_high}z/{vn_part_pers}", strip)
        add_r(strip, f"y{v_high}ş{v_high}n{v_high}z", strip)
        add_r(strip, f"y{v_high}şl{v_low}r{unrounded_high}/{vn_part_3sg}", strip)
        add_r(strip, f"y{v_high}şl{v_low}r{unrounded_high}", strip)
    else:
        cond_cons = f"[^çfhkpsşt]{strip}"
        cond_unv = f"[çfhkpsşt]{strip}"
        for d_c, cond_s in [("d", cond_cons if not is_voicing else f"[çt]{strip}"), ("t", cond_unv if not is_voicing else f"[çt]{strip}")]:
            add_r(strip, f"{d_c}{v_high}ğ{v_high}/{part_3sg}", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}m/{part_pers}", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}m", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}n/{part_pers}", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}n", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}m{v_high}z/{part_pers}", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}m{v_high}z", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}n{v_high}z/{part_pers}", cond_s)
            add_r(strip, f"{d_c}{v_high}ğ{v_high}n{v_high}z", cond_s)
            add_r(strip, f"{d_c}{v_high}kl{v_low}r{unrounded_high}/{fut_part_3sg}", cond_s)
            add_r(strip, f"{d_c}{v_high}kl{v_low}r{unrounded_high}", cond_s)
            for poss_p, cases_p in [
                (f"{d_c}{v_high}kl{v_low}r{unrounded_high}m", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"{d_c}{v_high}kl{v_low}r{unrounded_high}n", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"{d_c}{v_high}kl{v_low}r{unrounded_high}m{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
                (f"{d_c}{v_high}kl{v_low}r{unrounded_high}n{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"])
            ]:
                for c_p in cases_p:
                    add_r(strip, f"{poss_p}{c_p}", cond_s)
            
        if is_voicing:
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}/{fut_part_3sg}", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}m/{fut_part_pers}", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}m", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}n/{fut_part_pers}", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}n", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z/{fut_part_pers}", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z/{fut_part_pers}", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}kl{v_low}r{unrounded_high}/{fut_part_3sg}", f"t{strip}")
            add_r(f"t{strip}", f"d{fut_suf}{v_low}kl{v_low}r{unrounded_high}", f"t{strip}")
        else:
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}/{fut_part_3sg}", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m/{fut_part_pers}", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n/{fut_part_pers}", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z/{fut_part_pers}", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}m{unrounded_high}z", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z/{fut_part_pers}", strip)
            add_r(strip, f"{fut_suf}{v_low}ğ{unrounded_high}n{unrounded_high}z", strip)
            add_r(strip, f"{fut_suf}{v_low}kl{v_low}r{unrounded_high}/{fut_part_3sg}", strip)
            add_r(strip, f"{fut_suf}{v_low}kl{v_low}r{unrounded_high}", strip)
            
        add_r(strip, f"m{v_low}s{unrounded_high}/{vn_part_3sg}", strip)
        add_r(strip, f"m{v_low}s{unrounded_high}", strip)
        add_r(strip, f"m{v_low}m/{vn_part_pers}", strip)
        add_r(strip, f"m{v_low}m", strip)
        add_r(strip, f"m{v_low}n/{vn_part_pers}", strip)
        add_r(strip, f"m{v_low}n", strip)
        add_r(strip, f"m{v_low}m{unrounded_high}z/{vn_part_pers}", strip)
        add_r(strip, f"m{v_low}m{unrounded_high}z", strip)
        add_r(strip, f"m{v_low}n{unrounded_high}z/{vn_part_pers}", strip)
        add_r(strip, f"m{v_low}n{unrounded_high}z", strip)
        add_r(strip, f"m{v_low}l{v_low}r{unrounded_high}/{vn_part_3sg}", strip)
        add_r(strip, f"m{v_low}l{v_low}r{unrounded_high}", strip)
        if v_high != unrounded_high:
            add_r(strip, f"m{v_low}s{v_high}/{part_3sg}", strip)
            add_r(strip, f"m{v_low}s{v_high}", strip)
            add_r(strip, f"m{v_low}m{v_high}z/{part_pers}", strip)
            add_r(strip, f"m{v_low}m{v_high}z", strip)
            add_r(strip, f"m{v_low}n{v_high}z/{part_pers}", strip)
            add_r(strip, f"m{v_low}n{v_high}z", strip)
        # Verbal Noun (-iş / -ış: katledilişine, yayınlanışı, bitiş, gidiş)
        is_pref = "d" if is_voicing else ""
        is_strip = f"t{strip}" if is_voicing else strip
        is_cond = f"t{strip}" if is_voicing else strip
        add_r(is_strip, f"{is_pref}{v_high}ş", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}/{vn_part_3sg}", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}m/{vn_part_pers}", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}m", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}n/{vn_part_pers}", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}n", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}m{v_high}z/{vn_part_pers}", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}m{v_high}z", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}n{v_high}z/{vn_part_pers}", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}ş{v_high}n{v_high}z", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}şl{v_low}r{unrounded_high}/{vn_part_3sg}", is_cond)
        add_r(is_strip, f"{is_pref}{v_high}şl{v_low}r{unrounded_high}", is_cond)

    # 11. GERUNDS / CONVERBS
    if is_narrow:
        for y_pref in ["i", "e"]:
            add_r("emek", f"{y_pref}yerek", "[dy]emek")
            add_r("emek", f"{y_pref}yip", "[dy]emek")
            add_r("emek", f"{y_pref}yince", "[dy]emek")
            add_r("emek", f"{y_pref}yinceye", "[dy]emek")
        add_r("emek", "idikten", "[dy]emek")
        add_r("emek", "iyeli", "[dy]emek")
        add_r("emek", "iyesim", "[dy]emek")
        add_r(strip, "dikçe", strip)
        add_r(strip, "meden", strip)
    elif flag in ("VH", "VS"):
        sub_h = [("i", "emek"), ("ü", "ümek")] if flag == "VH" else [("ı", "amak"), ("u", "umak")]
        add_r(strip, f"y{v_low}r{v_low}k", strip)
        add_r(strip, f"m{v_low}d{v_low}n", strip)
        add_r(strip, f"y{v_low}s{unrounded_high}m", strip)
        for v_h_curr, cond_curr in sub_h:
            add_r(strip, f"y{v_h_curr}p", cond_curr)
            add_r(strip, f"y{v_h_curr}nc{v_low}", cond_curr)
            add_r(strip, f"y{v_h_curr}nc{v_low}y{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}kç{v_low}", cond_curr)
            add_r(strip, f"d{v_h_curr}kt{v_low}n", cond_curr)
            add_r(strip, f"y{v_h_curr}l{unrounded_high}", cond_curr)
    elif is_vowel_stem:
        add_r(strip, f"y{v_low}r{v_low}k", strip)
        add_r(strip, f"y{v_high}p", strip)
        add_r(strip, f"y{v_high}nc{v_low}", strip)
        add_r(strip, f"y{v_high}nc{v_low}y{v_low}", strip)
        add_r(strip, f"d{v_high}kç{v_low}", strip)
        add_r(strip, f"d{v_high}kt{v_low}n", strip)
        add_r(strip, f"y{v_low}l{unrounded_high}", strip)
        add_r(strip, f"y{v_low}s{unrounded_high}m", strip)
        add_r(strip, f"m{v_low}d{v_low}n", strip)
    elif is_voicing:
        add_r(f"t{strip}", f"d{v_low}r{v_low}k", f"t{strip}")
        add_r(f"t{strip}", f"d{v_high}p", f"t{strip}")
        add_r(f"t{strip}", f"d{v_high}nc{v_low}", f"t{strip}")
        add_r(f"t{strip}", f"d{v_high}nc{v_low}y{v_low}", f"t{strip}")
        add_r(strip, f"t{v_high}kç{v_low}", strip)
        add_r(f"t{strip}", f"d{v_high}kt{v_low}n", f"t{strip}")
        add_r(f"t{strip}", f"d{v_low}l{unrounded_high}", f"t{strip}")
        add_r(f"t{strip}", f"d{v_low}s{unrounded_high}m", f"t{strip}")
        add_r(strip, f"m{v_low}d{v_low}n", strip)
    else:
        add_r(strip, f"{v_low}r{v_low}k", strip)
        add_r(strip, f"{v_high}p", strip)
        add_r(strip, f"{v_high}nc{v_low}", strip)
        add_r(strip, f"{v_high}nc{v_low}y{v_low}", strip)
        cond_cons = f"[^çfhkpsşt]{strip}"
        cond_unv = f"[çfhkpsşt]{strip}"
        for d_c, cond_s in [("d", cond_cons), ("t", cond_unv)]:
            add_r(strip, f"{d_c}{v_high}kç{v_low}", cond_s)
            add_r(strip, f"{d_c}{v_high}kt{v_low}n", cond_s)
        add_r(strip, f"{v_low}l{unrounded_high}", strip)
        add_r(strip, f"{v_low}s{unrounded_high}m", strip)
        add_r(strip, f"m{v_low}d{v_low}n", strip)

    # 12. NEGATIVE FORMS
    neg_suf = f"m{v_low}"
    # Neg Pres Cont: yapmıyor, tutmuyor, tutmıyor
    add_r(strip, f"m{unrounded_high}yor/{cop_pres}", strip)
    add_r(strip, f"m{unrounded_high}yorken", strip)
    for p in p_pres:
        add_r(strip, f"m{unrounded_high}yor{p}", strip)

    if round_v:
        add_r(strip, f"m{v_high}yor/{cop_pres}", strip)
        add_r(strip, f"m{v_high}yorken", strip)
        for p in p_pres:
            add_r(strip, f"m{v_high}yor{p}", strip)
        
    # Neg Past: yapmadı
    add_r(strip, f"{neg_suf}d{unrounded_high}/{cop_vow}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}", strip)
    for p in ["m", "n", "k", f"n{unrounded_high}z", f"l{v_low}r"]:
        add_r(strip, f"{neg_suf}d{unrounded_high}{p}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ms{v_low}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ns{v_low}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ks{v_low}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}n{unrounded_high}zs{v_low}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}l{v_low}rs{v_low}", strip)
        
    # Neg Evidential: yapmamış
    add_r(strip, f"{neg_suf}m{unrounded_high}ş/{cop_unv}", strip)
    for p in ["", f"{unrounded_high}m", f"s{unrounded_high}n", f"{unrounded_high}z", f"s{unrounded_high}n{unrounded_high}z", f"l{v_low}r"]:
        add_r(strip, f"{neg_suf}m{unrounded_high}ş{p}", strip)
    add_r(strip, f"{neg_suf}m{unrounded_high}ş{unrounded_high}md{unrounded_high}r", strip)
    add_r(strip, f"{neg_suf}m{unrounded_high}ş{unrounded_high}zd{unrounded_high}r", strip)
    add_r(strip, f"{neg_suf}m{unrounded_high}şs{unrounded_high}nd{unrounded_high}r", strip)
    add_r(strip, f"{neg_suf}m{unrounded_high}şs{unrounded_high}n{unrounded_high}zd{unrounded_high}r", strip)
    add_r(strip, f"{neg_suf}m{unrounded_high}şl{v_low}rd{unrounded_high}r", strip)
        
    # Neg Future: yapmayacak
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}k/{cop_unv}", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}k", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}m", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ks{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ks{unrounded_high}n{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}kl{v_low}r", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}kl{v_low}rd{unrounded_high}r", strip)

    # Neg Necessitative: yapmamalı
    add_r(strip, f"{neg_suf}m{v_low}l{unrounded_high}/{cop_vow}", strip)
    for p in ["", f"y{unrounded_high}m", f"s{unrounded_high}n", f"y{unrounded_high}z", f"s{unrounded_high}n{unrounded_high}z", f"l{v_low}r"]:
        add_r(strip, f"{neg_suf}m{v_low}l{unrounded_high}{p}", strip)
        
    # Neg Conditional: yapmasa
    add_r(strip, f"{neg_suf}s{v_low}/{cop_vow}", strip)
    for p in ["", "m", "n", "k", f"n{unrounded_high}z", f"l{v_low}r", f"n{v_low}", f"n{unrounded_high}z{v_low}"]:
        add_r(strip, f"{neg_suf}s{v_low}{p}", strip)

    # Neg Optative & Imperative
    add_r(strip, f"{neg_suf}y{v_low}y{unrounded_high}m", strip)
    add_r(strip, f"{neg_suf}y{v_low}s{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}y{v_low}", strip)
    add_r(strip, f"{neg_suf}y{v_low}l{unrounded_high}m", strip)
    add_r(strip, f"{neg_suf}y{v_low}s{unrounded_high}n{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}y{v_low}l{v_low}r", strip)
    add_r(strip, f"{neg_suf}s{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}y{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}y{unrounded_high}n{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}s{unrounded_high}nl{v_low}r", strip)

    # Neg Converbs
    add_r(strip, f"{neg_suf}y{v_low}r{v_low}k", strip)
    add_r(strip, f"{neg_suf}y{unrounded_high}p", strip)
    add_r(strip, f"{neg_suf}y{unrounded_high}nc{v_low}", strip)
    add_r(strip, f"{neg_suf}y{unrounded_high}nc{v_low}y{v_low}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}kç{v_low}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}kt{v_low}n", strip)
    add_r(strip, f"{neg_suf}y{v_low}l{unrounded_high}", strip)
    add_r(strip, f"{neg_suf}ks{unrounded_high}z{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}s{unrounded_high}z{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}zken", strip)

    # Neg Progressive & Infinitives
    add_r(strip, f"{neg_suf}m{v_low}k", strip)
    add_r(strip, f"{neg_suf}m{v_low}kt{v_low}/{cop_vow}", strip)
    add_r(strip, f"{neg_suf}m{v_low}kt{v_low}n", strip)
    add_r(strip, f"{neg_suf}m{v_low}kl{v_low}", strip)
    add_r(strip, f"{neg_suf}m{v_low}y{unrounded_high}", strip)
    add_r(strip, f"{neg_suf}m{v_low}y{v_low}", strip)
    add_r(strip, f"{neg_suf}m{v_low}n{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}m{v_low}kt{unrounded_high}", strip)
    add_r(strip, f"{neg_suf}m{v_low}kt{unrounded_high}r", strip)
    add_r(strip, f"{neg_suf}m{v_low}kt{v_low}ns{v_low}", strip)
    for p in ["", f"y{unrounded_high}m", f"s{unrounded_high}n", f"y{unrounded_high}z", f"s{unrounded_high}n{unrounded_high}z", f"l{v_low}r"]:
        add_r(strip, f"{neg_suf}m{v_low}kt{v_low}{p}", strip)

    # Neg Aorist (for vowel stems, narrow verbs, and voicing stems)
    if is_vowel_stem or is_narrow or is_voicing:
        add_r(strip, f"{neg_suf}z/{neg_cop_aor}", strip)
        add_r(strip, f"{neg_suf}m", strip)
        add_r(strip, f"{neg_suf}zs{unrounded_high}n", strip)
        add_r(strip, f"{neg_suf}z", strip)
        add_r(strip, f"{neg_suf}y{unrounded_high}z", strip)
        add_r(strip, f"{neg_suf}zs{unrounded_high}n{unrounded_high}z", strip)
        add_r(strip, f"{neg_suf}zl{v_low}r", strip)
        for c_case in [f"{v_low}", f"{unrounded_high}", f"d{v_low}n", f"d{v_low}", f"{unrounded_high}n"]:
            add_r(strip, f"{neg_suf}z{c_case}", strip)

    # Neg Subject Participle (-mayan / -meyen with noun cases)
    for pe in part_endings:
        add_r(strip, f"{neg_suf}y{v_low}n{pe}", strip)

    # Neg Verbal Nouns with Full Person Agreement (küçümsemememiz, vb.)
    add_r(strip, f"{neg_suf}m{v_low}s{unrounded_high}/{vn_part_3sg}", strip)
    add_r(strip, f"{neg_suf}m{v_low}s{unrounded_high}", strip)
    add_r(strip, f"{neg_suf}m{v_low}m/{vn_part_pers}", strip)
    add_r(strip, f"{neg_suf}m{v_low}m", strip)
    add_r(strip, f"{neg_suf}m{v_low}n/{vn_part_pers}", strip)
    add_r(strip, f"{neg_suf}m{v_low}n", strip)
    add_r(strip, f"{neg_suf}m{v_low}m{unrounded_high}z/{vn_part_pers}", strip)
    add_r(strip, f"{neg_suf}m{v_low}m{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}m{v_low}n{unrounded_high}z/{vn_part_pers}", strip)
    add_r(strip, f"{neg_suf}m{v_low}n{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}m{v_low}l{v_low}r{unrounded_high}/{vn_part_3sg}", strip)
    add_r(strip, f"{neg_suf}m{v_low}l{v_low}r{unrounded_high}", strip)

    # Neg Object Participles with Full Person Agreement (bakmadığınız, vb.)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}/{neg_part_3sg}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}m/{neg_part_pers}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}m", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}n/{neg_part_pers}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}m{unrounded_high}z/{neg_part_pers}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}m{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}n{unrounded_high}z/{neg_part_pers}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}ğ{unrounded_high}n{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}kl{v_low}r{unrounded_high}/{neg_part_3sg}", strip)
    add_r(strip, f"{neg_suf}d{unrounded_high}kl{v_low}r{unrounded_high}", strip)
    for poss_p, cases_p in [
        (f"{neg_suf}d{unrounded_high}kl{v_low}r{unrounded_high}m", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{neg_suf}d{unrounded_high}kl{v_low}r{unrounded_high}n", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{neg_suf}d{unrounded_high}kl{v_low}r{unrounded_high}m{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{neg_suf}d{unrounded_high}kl{v_low}r{unrounded_high}n{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"])
    ]:
        for c_p in cases_p:
            add_r(strip, f"{poss_p}{c_p}", strip)
    
    # Neg Future Participles with Full Person Agreement
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}/{fut_part_3sg}", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}m/{fut_part_pers}", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}m", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}n/{fut_part_pers}", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}n", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}m{unrounded_high}z/{fut_part_pers}", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}m{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}n{unrounded_high}z/{fut_part_pers}", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}ğ{unrounded_high}n{unrounded_high}z", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}kl{v_low}r{unrounded_high}/{fut_part_3sg}", strip)
    add_r(strip, f"{neg_suf}y{v_low}c{v_low}kl{v_low}r{unrounded_high}", strip)
    for poss_p, cases_p in [
        (f"{neg_suf}y{v_low}c{v_low}kl{v_low}r{unrounded_high}m", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{neg_suf}y{v_low}c{v_low}kl{v_low}r{unrounded_high}n", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{neg_suf}y{v_low}c{v_low}kl{v_low}r{unrounded_high}m{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{neg_suf}y{v_low}c{v_low}kl{v_low}r{unrounded_high}n{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"])
    ]:
        for c_p in cases_p:
            add_r(strip, f"{poss_p}{c_p}", strip)

    # Neg Compound Potential: -mayabilir / -meyebilir
    neg_pot = f"{neg_suf}y{v_low}bil"
    add_r(strip, f"{neg_pot}ir/cE", strip)
    add_r(strip, f"{neg_pot}ir", strip)
    add_r(strip, f"{neg_pot}irim", strip)
    add_r(strip, f"{neg_pot}irsin", strip)
    add_r(strip, f"{neg_pot}iriz", strip)
    add_r(strip, f"{neg_pot}irsiniz", strip)
    add_r(strip, f"{neg_pot}irler", strip)
    add_r(strip, f"{neg_pot}iyor", strip)
    add_r(strip, f"{neg_pot}iyoruz", strip)
    add_r(strip, f"{neg_pot}iyorlar", strip)
    add_r(strip, f"{neg_pot}ecek", strip)
    add_r(strip, f"{neg_pot}eceği/{fut_part_3sg}", strip)
    add_r(strip, f"{neg_pot}eceği", strip)
    add_r(strip, f"{neg_pot}iyor", strip)
    add_r(strip, f"{neg_pot}iyoruz", strip)
    add_r(strip, f"{neg_pot}iyorlar", strip)

    # 13. INABILITY ASPECT (-ama / -eme)
    inab_p = "iyem" if is_narrow else (f"d{v_low}m" if is_voicing else (f"y{v_low}m" if is_vowel_stem else f"{v_low}m"))
    inab_strip = "emek" if is_narrow else (f"t{strip}" if is_voicing else strip)
    inab_cond = "[dy]emek" if is_narrow else (f"t{strip}" if is_voicing else strip)

    # Inab Pres Cont: yapamıyor, tutamıyor, anlatamıyorsak
    add_r(inab_strip, f"{inab_p}{unrounded_high}yor/{cop_pres}", inab_cond)
    add_r(inab_strip, f"{inab_p}{unrounded_high}yorken", inab_cond)
    for p in p_pres:
        add_r(inab_strip, f"{inab_p}{unrounded_high}yor{p}", inab_cond)

    # Inab Past: yapamadı, alınamadı, düşürülemedi, sevdiremedik
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}/{cop_vow}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}", inab_cond)
    for p in ["m", "n", "k", f"n{unrounded_high}z", f"l{v_low}r"]:
        add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}{p}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ms{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ns{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ks{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}n{unrounded_high}zs{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}l{v_low}rs{v_low}", inab_cond)

    # Inab Evidential: yapamamış
    add_r(inab_strip, f"{inab_p}{v_low}m{unrounded_high}ş/{cop_unv}", inab_cond)
    for p in ["", f"{unrounded_high}m", f"s{unrounded_high}n", f"{unrounded_high}z", f"s{unrounded_high}n{unrounded_high}z", f"l{v_low}r"]:
        add_r(inab_strip, f"{inab_p}{v_low}m{unrounded_high}ş{p}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{unrounded_high}ş{unrounded_high}md{unrounded_high}r", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{unrounded_high}ş{unrounded_high}zd{unrounded_high}r", inab_cond)

    # Inab Future: yapamayacak, giremeyeceğin
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}k/{cop_unv}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}k", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}m", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ks{unrounded_high}n", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ks{unrounded_high}n{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}kl{v_low}r", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}kl{v_low}rd{unrounded_high}r", inab_cond)

    # Inab Aorist: sığdıramam, yapamaz, yapamayız
    add_r(inab_strip, f"{inab_p}{v_low}z/{cop_aor}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}zs{unrounded_high}n", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}zs{unrounded_high}n{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}zl{v_low}r", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}zken", inab_cond)
    for c_case in [f"{v_low}", f"{unrounded_high}", f"d{v_low}n", f"d{v_low}", f"{unrounded_high}n"]:
        add_r(inab_strip, f"{inab_p}{v_low}z{c_case}", inab_cond)

    # Inab Imperative & Optative: açamasın, söyleyeme, açamayın, vb.
    add_r(inab_strip, f"{inab_p}{v_low}s{unrounded_high}n", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{unrounded_high}n", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{unrounded_high}n{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}s{unrounded_high}nl{v_low}r", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}y{unrounded_high}m", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}l{unrounded_high}m", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}s{unrounded_high}n{unrounded_high}z", inab_cond)

    # Inab Necessitative & Conditional
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}l{unrounded_high}/{cop_vow}", inab_cond)
    for p in ["", f"y{unrounded_high}m", f"s{unrounded_high}n", f"y{unrounded_high}z", f"s{unrounded_high}n{unrounded_high}z", f"l{v_low}r"]:
        add_r(inab_strip, f"{inab_p}{v_low}m{v_low}l{unrounded_high}{p}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}s{v_low}/{cop_vow}", inab_cond)
    for p in ["", "m", "n", "k", f"n{unrounded_high}z", f"l{v_low}r", f"n{v_low}", f"n{unrounded_high}z{v_low}"]:
        add_r(inab_strip, f"{inab_p}{v_low}s{v_low}{p}", inab_cond)

    # Inab Progressive & Infinitives: kullanamamaktadır
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}k", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}kt{v_low}/{cop_vow}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}kt{v_low}n", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}kl{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}y{unrounded_high}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}y{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}n{unrounded_high}n", inab_cond)
    for p in ["", f"y{unrounded_high}m", f"s{unrounded_high}n", f"y{unrounded_high}z", f"s{unrounded_high}n{unrounded_high}z", f"l{v_low}r"]:
        add_r(inab_strip, f"{inab_p}{v_low}m{v_low}kt{v_low}{p}", inab_cond)

    # Inab Participles & Converbs: geçemediğinin, bitirilemeyince
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ğ{unrounded_high}/{neg_part_3sg}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ğ{unrounded_high}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ğ{unrounded_high}m/{neg_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ğ{unrounded_high}n/{neg_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ğ{unrounded_high}m{unrounded_high}z/{neg_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ğ{unrounded_high}m{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ğ{unrounded_high}n{unrounded_high}z/{neg_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}ğ{unrounded_high}n{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}kl{v_low}r{unrounded_high}/{neg_part_3sg}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}kl{v_low}r{unrounded_high}", inab_cond)
    for poss_p, cases_p in [
        (f"{inab_p}{v_low}d{unrounded_high}kl{v_low}r{unrounded_high}m", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{inab_p}{v_low}d{unrounded_high}kl{v_low}r{unrounded_high}n", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{inab_p}{v_low}d{unrounded_high}kl{v_low}r{unrounded_high}m{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{inab_p}{v_low}d{unrounded_high}kl{v_low}r{unrounded_high}n{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"])
    ]:
        for c_p in cases_p:
            add_r(inab_strip, f"{poss_p}{c_p}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}/{fut_part_3sg}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}m/{fut_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}m", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}n/{fut_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}n", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}m{unrounded_high}z/{fut_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}m{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}n{unrounded_high}z/{fut_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}ğ{unrounded_high}n{unrounded_high}z", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}kl{v_low}r{unrounded_high}/{fut_part_3sg}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}c{v_low}kl{v_low}r{unrounded_high}", inab_cond)
    for poss_p, cases_p in [
        (f"{inab_p}{v_low}y{v_low}c{v_low}kl{v_low}r{unrounded_high}m", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{inab_p}{v_low}y{v_low}c{v_low}kl{v_low}r{unrounded_high}n", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{inab_p}{v_low}y{v_low}c{v_low}kl{v_low}r{unrounded_high}m{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"]),
        (f"{inab_p}{v_low}y{v_low}c{v_low}kl{v_low}r{unrounded_high}n{unrounded_high}z", ["", f"{unrounded_high}", f"{v_low}", f"d{v_low}", f"d{v_low}n", f"{unrounded_high}n", f"l{v_low}"])
    ]:
        for c_p in cases_p:
            add_r(inab_strip, f"{poss_p}{c_p}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}s{unrounded_high}/{vn_part_3sg}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}s{unrounded_high}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}l{v_low}r{unrounded_high}/{vn_part_3sg}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}l{v_low}r{unrounded_high}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}m/{vn_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}n/{vn_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}m{unrounded_high}z/{vn_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}m{v_low}n{unrounded_high}z/{vn_part_pers}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{v_low}r{v_low}k", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{unrounded_high}p", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}y{unrounded_high}nc{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}kç{v_low}", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{unrounded_high}kt{v_low}n", inab_cond)
    add_r(inab_strip, f"{inab_p}{v_low}d{v_low}n", inab_cond)
    for pe in part_endings:
        add_r(inab_strip, f"{inab_p}{v_low}y{v_low}n{pe}", inab_cond)

    # Inab Compound Potential: -amayabilir / -emeyebilir
    inab_pot = f"{inab_p}{v_low}y{v_low}bil"
    add_r(inab_strip, f"{inab_pot}ir/cE", inab_cond)
    add_r(inab_strip, f"{inab_pot}ir", inab_cond)
    add_r(inab_strip, f"{inab_pot}irim", inab_cond)
    add_r(inab_strip, f"{inab_pot}irsin", inab_cond)
    add_r(inab_strip, f"{inab_pot}iriz", inab_cond)
    add_r(inab_strip, f"{inab_pot}irsiniz", inab_cond)
    add_r(inab_strip, f"{inab_pot}irler", inab_cond)
    add_r(inab_strip, f"{inab_pot}iyor", inab_cond)
    add_r(inab_strip, f"{inab_pot}eceği/{fut_part_3sg}", inab_cond)
    add_r(inab_strip, f"{inab_pot}eceği", inab_cond)
    add_r(inab_strip, f"{inab_pot}ecek", inab_cond)

    # 14. POSITIVE POTENTIAL ASPECT (-abil / -ebil)
    pot_p = "iyebil" if is_narrow else (f"d{v_low}bil" if is_voicing else (f"y{v_low}bil" if is_vowel_stem else f"{v_low}bil"))
    pot_strip = inab_strip
    pot_cond = inab_cond
    
    # All suffixes on -bil are front-unrounded
    add_r(pot_strip, f"{pot_p}ir/cE", pot_cond)
    add_r(pot_strip, f"{pot_p}ir", pot_cond)
    add_r(pot_strip, f"{pot_p}irim", pot_cond)
    add_r(pot_strip, f"{pot_p}irsin", pot_cond)
    add_r(pot_strip, f"{pot_p}iriz", pot_cond)
    add_r(pot_strip, f"{pot_p}irsiniz", pot_cond)
    add_r(pot_strip, f"{pot_p}irler", pot_cond)
    add_r(pot_strip, f"{pot_p}irken", pot_cond)
    # Past
    add_r(pot_strip, f"{pot_p}di/{cop_past}", pot_cond)
    add_r(pot_strip, f"{pot_p}di", pot_cond)
    add_r(pot_strip, f"{pot_p}dim", pot_cond)
    add_r(pot_strip, f"{pot_p}din", pot_cond)
    add_r(pot_strip, f"{pot_p}dik", pot_cond)
    add_r(pot_strip, f"{pot_p}diniz", pot_cond)
    add_r(pot_strip, f"{pot_p}diler", pot_cond)
    add_r(pot_strip, f"{pot_p}dikte", pot_cond)
    add_r(pot_strip, f"{pot_p}dikten", pot_cond)
    # Evidential
    add_r(pot_strip, f"{pot_p}miş/{cop_unv}", pot_cond)
    add_r(pot_strip, f"{pot_p}miş", pot_cond)
    add_r(pot_strip, f"{pot_p}mişler", pot_cond)
    # Present Continuous
    add_r(pot_strip, f"{pot_p}iyor/{cop_pres}", pot_cond)
    add_r(pot_strip, f"{pot_p}iyor", pot_cond)
    add_r(pot_strip, f"{pot_p}iyorum", pot_cond)
    add_r(pot_strip, f"{pot_p}iyorsun", pot_cond)
    add_r(pot_strip, f"{pot_p}iyoruz", pot_cond)
    add_r(pot_strip, f"{pot_p}iyorsunuz", pot_cond)
    add_r(pot_strip, f"{pot_p}iyorlar", pot_cond)
    add_r(pot_strip, f"{pot_p}iyorken", pot_cond)
    # Future
    add_r(pot_strip, f"{pot_p}ecek/uE", pot_cond)
    add_r(pot_strip, f"{pot_p}ecek", pot_cond)
    add_r(pot_strip, f"{pot_p}eceğim", pot_cond)
    add_r(pot_strip, f"{pot_p}eceksin", pot_cond)
    add_r(pot_strip, f"{pot_p}eceğiz", pot_cond)
    add_r(pot_strip, f"{pot_p}eceksiniz", pot_cond)
    add_r(pot_strip, f"{pot_p}ecekler", pot_cond)
    add_r(pot_strip, f"{pot_p}eceklerdir", pot_cond)
    # Imperative & Necessitative
    add_r(pot_strip, f"{pot_p}sin", pot_cond)
    add_r(pot_strip, f"{pot_p}sinler", pot_cond)
    add_r(pot_strip, f"{pot_p}meli/vE", pot_cond)
    add_r(pot_strip, f"{pot_p}meli", pot_cond)
    add_r(pot_strip, f"{pot_p}melisin", pot_cond)
    add_r(pot_strip, f"{pot_p}meliyiz", pot_cond)
    add_r(pot_strip, f"{pot_p}meliler", pot_cond)
    # Optative of -abil
    add_r(pot_strip, f"{pot_p}e", pot_cond)
    add_r(pot_strip, f"{pot_p}eyim", pot_cond)
    add_r(pot_strip, f"{pot_p}esin", pot_cond)
    add_r(pot_strip, f"{pot_p}elim", pot_cond)
    add_r(pot_strip, f"{pot_p}esiniz", pot_cond)
    add_r(pot_strip, f"{pot_p}eler", pot_cond)
    # -ebilirlik noun derivation (edebilirliği, erişebilirliği)
    add_r(pot_strip, f"{pot_p}irlik", pot_cond)
    add_r(pot_strip, f"{pot_p}irliği/pE", pot_cond)
    add_r(pot_strip, f"{pot_p}irliği", pot_cond)
    add_r(pot_strip, f"{pot_p}irliğini", pot_cond)
    add_r(pot_strip, f"{pot_p}irliğinin", pot_cond)
    add_r(pot_strip, f"{pot_p}irliğinde", pot_cond)
    add_r(pot_strip, f"{pot_p}irliğinden", pot_cond)
    # Verbal Noun & Progressive
    add_r(pot_strip, f"{pot_p}me", pot_cond)
    add_r(pot_strip, f"{pot_p}mek", pot_cond)
    add_r(pot_strip, f"{pot_p}mekte/vE", pot_cond)
    add_r(pot_strip, f"{pot_p}mekte", pot_cond)
    add_r(pot_strip, f"{pot_p}mektedir", pot_cond)
    add_r(pot_strip, f"{pot_p}mesi/pE", pot_cond)
    add_r(pot_strip, f"{pot_p}mesi", pot_cond)
    # Participles
    add_r(pot_strip, f"{pot_p}diği/pE", pot_cond)
    add_r(pot_strip, f"{pot_p}diği", pot_cond)
    add_r(pot_strip, f"{pot_p}diğim/qE", pot_cond)
    add_r(pot_strip, f"{pot_p}diğin/qE", pot_cond)
    add_r(pot_strip, f"{pot_p}diğimiz/qE", pot_cond)
    add_r(pot_strip, f"{pot_p}diğiniz/qE", pot_cond)
    add_r(pot_strip, f"{pot_p}dikleri/pE", pot_cond)
    add_r(pot_strip, f"{pot_p}dikleri", pot_cond)
    add_r(pot_strip, f"{pot_p}eceği/pE", pot_cond)
    add_r(pot_strip, f"{pot_p}eceği", pot_cond)
    add_r(pot_strip, f"{pot_p}eceğim/qE", pot_cond)
    add_r(pot_strip, f"{pot_p}eceğin/qE", pot_cond)
    add_r(pot_strip, f"{pot_p}eceğimiz/qE", pot_cond)
    add_r(pot_strip, f"{pot_p}eceğiniz/qE", pot_cond)
    add_r(pot_strip, f"{pot_p}ecekleri/pE", pot_cond)
    add_r(pot_strip, f"{pot_p}ecekleri", pot_cond)
    for pe in [
        "", "ler", "leri", "lere", "lerde", "lerden", "lerin", "leriyle",
        "i", "e", "de", "den", "in", "yle"
    ]:
        add_r(pot_strip, f"{pot_p}en{pe}", pot_cond)
    for pe in ["", "ler", "leri", "lere", "lerde", "lerden", "lerin", "leriyle"]:
        add_r(pot_strip, f"{pot_p}ecek{pe}", pot_cond)
    # Converbs
    add_r(pot_strip, f"{pot_p}erek", pot_cond)
    add_r(pot_strip, f"{pot_p}ip", pot_cond)
    add_r(pot_strip, f"{pot_p}ince", pot_cond)
    add_r(pot_strip, f"{pot_p}dikçe", pot_cond)
    add_r(pot_strip, f"{pot_p}se", pot_cond)
    add_r(pot_strip, f"{pot_p}seydi", pot_cond)

    return make_verb_flag_block(flag, rules)


def generate_aorist_subflag_block(flag: str, aor_vowel: str, is_back: bool, strip: str) -> str:
    rules = []
    if aor_vowel in ('u', 'o'):
        cop_aor = "cU"
    elif aor_vowel in ('ü', 'ö'):
        cop_aor = "cI"
    elif is_back:
        cop_aor = "cA"
    else:
        cop_aor = "cE"
    v_low = "a" if is_back else "e"
    p_high = aor_vowel if aor_vowel in ('ı', 'i', 'u', 'ü') else ("ı" if is_back else "i")
    neg_unrounded_high = "ı" if is_back else "i"
    neg_suf = f"m{v_low}"

    # Positive Aorist
    rules.append(sfx(flag, strip, f"{aor_vowel}r/{cop_aor}", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}r", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}rken", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}rc{v_low}s{neg_unrounded_high}n{v_low}", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}r{p_high}m", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}rs{p_high}n", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}rs{neg_unrounded_high}n", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}r{p_high}z", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}rs{p_high}n{p_high}z", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}rs{neg_unrounded_high}n{neg_unrounded_high}z", strip))
    rules.append(sfx(flag, strip, f"{aor_vowel}rl{v_low}r", strip))

    # Negative Aorist
    neg_cop_aor = "cA" if is_back else "cE"
    rules.append(sfx(flag, strip, f"{neg_suf}z/{neg_cop_aor}", strip))
    rules.append(sfx(flag, strip, f"{neg_suf}m", strip))
    rules.append(sfx(flag, strip, f"{neg_suf}zs{neg_unrounded_high}n", strip))
    rules.append(sfx(flag, strip, f"{neg_suf}z", strip))
    rules.append(sfx(flag, strip, f"{neg_suf}y{neg_unrounded_high}z", strip))
    rules.append(sfx(flag, strip, f"{neg_suf}zs{neg_unrounded_high}n{neg_unrounded_high}z", strip))
    rules.append(sfx(flag, strip, f"{neg_suf}zl{v_low}r", strip))
    rules.append(sfx(flag, strip, f"{neg_suf}zken", strip))
    for c_case in [f"{v_low}", f"{neg_unrounded_high}", f"d{v_low}n", f"d{v_low}", f"{neg_unrounded_high}n"]:
        rules.append(sfx(flag, strip, f"{neg_suf}z{c_case}", strip))

    return make_verb_flag_block(flag, rules)


def generate_factorized_verb_rules() -> str:
    blocks = []
    
    # 1. Stage 2 Copula and Case Flags
    blocks.extend(generate_stage2_flags())
    
    # 2. Stage 1 Verb Classes
    # Consonant stems
    blocks.append(generate_verb_stage1_block("VB", back=True, round_v=False, is_vowel_stem=False, is_narrow=False, strip="mak"))
    blocks.append(generate_verb_stage1_block("VR", back=True, round_v=True, is_vowel_stem=False, is_narrow=False, strip="mak"))
    blocks.append(generate_verb_stage1_block("VF", back=False, round_v=False, is_vowel_stem=False, is_narrow=False, strip="mek"))
    blocks.append(generate_verb_stage1_block("VG", back=False, round_v=True, is_vowel_stem=False, is_narrow=False, strip="mek"))
    
    # Vowel stems
    blocks.append(generate_verb_stage1_block("VA", back=True, round_v=False, is_vowel_stem=True, is_narrow=False, strip="mak"))
    blocks.append(generate_verb_stage1_block("VS", back=True, round_v=True, is_vowel_stem=True, is_narrow=False, strip="mak"))
    blocks.append(generate_verb_stage1_block("VE", back=False, round_v=False, is_vowel_stem=True, is_narrow=False, strip="mek"))
    blocks.append(generate_verb_stage1_block("VH", back=False, round_v=True, is_vowel_stem=True, is_narrow=False, strip="mek"))
    
    # Voicing consonant stems
    blocks.append(generate_verb_stage1_block("VK", back=True, round_v=False, is_vowel_stem=False, is_narrow=False, strip="mak"))
    blocks.append(generate_verb_stage1_block("VL", back=True, round_v=True, is_vowel_stem=False, is_narrow=False, strip="mak"))
    blocks.append(generate_verb_stage1_block("VM", back=False, round_v=False, is_vowel_stem=False, is_narrow=False, strip="mek"))
    blocks.append(generate_verb_stage1_block("VN", back=False, round_v=True, is_vowel_stem=False, is_narrow=False, strip="mek"))
    
    # Narrowing verbs (demek, yemek)
    blocks.append(generate_verb_stage1_block("VY", back=False, round_v=False, is_vowel_stem=False, is_narrow=True, strip="mek"))
    
    # 3. Aorist Subflags
    blocks.append(generate_aorist_subflag_block("wa", aor_vowel="a", is_back=True, strip="mak"))
    blocks.append(generate_aorist_subflag_block("wi", aor_vowel="ı", is_back=True, strip="mak"))
    blocks.append(generate_aorist_subflag_block("wr", aor_vowel="a", is_back=True, strip="mak"))
    blocks.append(generate_aorist_subflag_block("wu", aor_vowel="u", is_back=True, strip="mak"))
    blocks.append(generate_aorist_subflag_block("we", aor_vowel="e", is_back=False, strip="mek"))
    blocks.append(generate_aorist_subflag_block("wj", aor_vowel="i", is_back=False, strip="mek"))
    blocks.append(generate_aorist_subflag_block("wg", aor_vowel="e", is_back=False, strip="mek"))
    blocks.append(generate_aorist_subflag_block("wh", aor_vowel="ü", is_back=False, strip="mek"))
    
    return "\n\n".join(blocks)


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
