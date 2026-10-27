# Helper to map semantic flags to single UTF-8 characters (Mathematical Operators block starting at \u2200).
# NOTE: Codepoints must remain frozen and immutable across versions to ensure stable dictionary diffs.
# New flags must ALWAYS be appended to the end of the registry, never inserted in the middle.

FROZEN_FLAGS = [
    'A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4', 'CI', 'CK', 'CL', 'CO', 'CP', 'CV',
    'D1', 'D2', 'D3', 'D4', 'DE', 'DL', 'DT', 'F1', 'F2', 'F3', 'F4', 'G1', 'G2', 'G3', 'G4', 'I1', 'I2',
    'K1', 'K2', 'KC', 'KI', 'L1', 'L2', 'LI', 'LK', 'N1', 'N2', 'N3', 'N4', 'NE', 'NS', 'NX',
    'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'PB', 'PF', 'PM', 'PN', 'PO', 'PP', 'PQ', 'PR', 'PS', 'PT', 'PU', 'PV', 'PW', 'PX', 'PZ',
    'Q1', 'Q2', 'R1', 'R2', 'SL', 'SZ', 'V1', 'V2', 'V3', 'V4', 'VA', 'VB', 'VC', 'VE', 'VF', 'VG', 'VH', 'VK', 'VL', 'VM', 'VN', 'VR', 'VS', 'VY', 'Vb', 'Vf',
    'Y1', 'Y2', 'a1', 'a2', 'a3', 'a4', 'cl', 'i1', 'i2', 'n1', 'n2', 'n3', 'n4',
    'u1', 'u2', 'u3', 'u4', 'uA', 'uC', 'uI', 'uL', 'uN', 'uP', 'uQ', 'uR', 'uY', 'vc',
    'wa', 'we', 'wg', 'wh', 'wi', 'wj', 'wr', 'wu', 'y1', 'y2'
]

ALL_FLAGS = FROZEN_FLAGS

# 3-character proper-noun harmony flags.
# Each family covers 8 sub-flags: N L R Y A I P C
# pB = back-unrounded (a/ı)  e.g. İstanbul, Ankara
# pO = back-rounded   (o/u)  e.g. Ordu, Trabzon
# pF = front-unrounded(e/i)  e.g. Türkiye, İzmir
# pU = front-rounded  (ö/ü)  e.g. Gümüşhane
PROPER_NOUN_FLAGS_3 = [
    f"p{fam}{sub}"
    for fam in "BOFU"
    for sub in "NLRYAIPC"
]

# Front-only derivations for inverse-harmony stems.
#   LF  = front-only -lI   (kontrollü, not kontrollu)
#   LSZ = front-only -sIz  (kontrolsüz, not kontrolsuz)
#   LFK = front-only -lIk  (kontrollük, not kontrolluk)
#   LCI = front-only -cI   (kontrolcü, not kontrolcu)
INVERSE_DERIV_FLAGS = ["LF", "LSZ", "LFK", "LCI"]

# Stage 2 secondary verb flags (copulas and participle case affixes)
STAGE2_VERB_FLAGS = [
    "cA", "cE", "cU", "cI",
    "uE", "uO", "uU",
    "vA", "vE",
    "pA", "pE", "pO", "pU",
    "qA", "qE", "qO", "qU",
    "sA", "sE",
]

# Numeral apostrophe-inflection flags (9 phonological classes for numbers & clock times)
NUMERAL_FLAGS = [
    "N5", "N6", "N7", "N8", "N9", "NA", "NB", "NC", "ND"
]

# Map each flag to a unique Mathematical Operator codepoint starting at \u2200 (8704)
LONG_TO_UTF8 = {}
for idx, flag in enumerate(ALL_FLAGS):
    LONG_TO_UTF8[flag] = chr(8704 + idx)
for idx, flag in enumerate(PROPER_NOUN_FLAGS_3):
    LONG_TO_UTF8[flag] = chr(8704 + len(ALL_FLAGS) + idx)
for idx, flag in enumerate(INVERSE_DERIV_FLAGS):
    LONG_TO_UTF8[flag] = chr(8704 + len(ALL_FLAGS) + len(PROPER_NOUN_FLAGS_3) + idx)
_offset_s2 = len(ALL_FLAGS) + len(PROPER_NOUN_FLAGS_3) + len(INVERSE_DERIV_FLAGS)
for idx, flag in enumerate(STAGE2_VERB_FLAGS):
    LONG_TO_UTF8[flag] = chr(8704 + _offset_s2 + idx)
_offset_num = _offset_s2 + len(STAGE2_VERB_FLAGS)
for idx, flag in enumerate(NUMERAL_FLAGS):
    LONG_TO_UTF8[flag] = chr(8704 + _offset_num + idx)

# Override NE to ASCII 'X' to guarantee correct NEEDAFFIX parsing by Hunspell
LONG_TO_UTF8["NE"] = "X"

UTF8_TO_LONG = {v: k for k, v in LONG_TO_UTF8.items()}

def remap_flag_string(s: str) -> str:
    """Convert a concatenated string of flags into single UTF-8 characters.

    Disambiguates 3-character proper noun flags from 2-character stem/affix flags.
    """
    if not s:
        return ""
    result = []
    i = 0
    n = len(s)
    while i < n:
        # Check if 3-char match is valid (only proper-noun flags start with p[BOFU][NLRYAIPC])
        matched_3 = False
        if i + 3 <= n:
            three = s[i:i+3]
            if three in LONG_TO_UTF8 and three.startswith("p") and len(three) == 3 and three[1] in "BOFU" and three[2] in "NLRYAIPC":
                # If remaining length is odd, a 3-char match would leave an orphan 1-char.
                # Check if a 2-char match + next 2-char match can parse cleanly instead:
                if i + 3 < n and (n - (i + 3)) % 2 != 0:
                    two = s[i:i+2]
                    two_next = s[i+2:i+4] if i + 4 <= n else ""
                    if two in LONG_TO_UTF8 and two_next in LONG_TO_UTF8:
                        pass
                    else:
                        result.append(LONG_TO_UTF8[three])
                        i += 3
                        matched_3 = True
                else:
                    result.append(LONG_TO_UTF8[three])
                    i += 3
                    matched_3 = True

        if matched_3:
            continue

        # Try 2-char match
        if i + 2 <= n:
            two = s[i:i+2]
            if two in LONG_TO_UTF8:
                result.append(LONG_TO_UTF8[two])
                i += 2
                continue

        # Single char fallback (e.g. X for NEEDAFFIX or already remapped UTF-8 chars)
        result.append(s[i])
        i += 1

    return "".join(result)
