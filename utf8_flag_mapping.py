# Helper to map 2-character semantic flags to single UTF-8 characters (Cyrillic block).

ALL_FLAGS = sorted([
    # Noun stem classes
    "B1", "B2", "B3", "B4", "F1", "F2", "F3", "F4", 
    "V1", "V2", "V3", "V4", "D1", "D2", "D3", "D4", 
    "C1", "C2", "C3", "C4", "G1", "G2", "G3", "G4", 
    "NX", "PX",
    # Noun morphological classes (cases, plurals, possessives, copula, ki, derivations)
    "A1", "A2", "A3", "A4", "Y1", "Y2", "L1", "L2", "R1", "R2", "N1", "N2", "N3", "N4", "I1", "I2", "Q1", "Q2",
    "a1", "a2", "a3", "a4", "y1", "y2", "n1", "n2", "n3", "n4", "i1", "i2",
    "PB", "PF",
    "PS", "PT", "PU", "PV", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "PM", "PO", "PP", "PQ", "PN", "PR", "PW", "PZ",
    "CL", "cl", "CP", "CV", "CO", "KI", "LI", "SZ", "LK", "CI", "CK", "DL", "DT", "DE",
    # Proper Noun morphological classes (with apostrophe prefix) - OLD (kept for back-compat)
    "uA", "uY", "uL", "uR", "uN", "uI", "uQ", "uP", "u1", "u2", "u3", "u4", "uC",
    # Verb flags
    "VB", "VR", "VF", "VG", "VA", "VS", "VE", "VH", "VK", "VL", "VM", "VN", "VY",
    # Obsolete
    "NS"
])

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

# Map each flag to a unique Cyrillic codepoint starting at \u0400 (1024)
# 2-char flags come first, then 3-char flags.
LONG_TO_UTF8 = {}
for idx, flag in enumerate(ALL_FLAGS):
    LONG_TO_UTF8[flag] = chr(1024 + idx)
for idx, flag in enumerate(PROPER_NOUN_FLAGS_3):
    LONG_TO_UTF8[flag] = chr(1024 + len(ALL_FLAGS) + idx)

UTF8_TO_LONG = {v: k for k, v in LONG_TO_UTF8.items()}

def remap_flag_string(s: str) -> str:
    """Convert a concatenated string of flags into single UTF-8 characters.

    Flags may be 2 or 3 characters long.  We use a longest-match greedy
    scan: try 3-char first (proper-noun flags start with 'p'), then 2-char.
    """
    if not s:
        return ""
    result = []
    i = 0
    while i < len(s):
        # Try 3-char match first (only 'p' prefix flags are 3-char)
        if i + 3 <= len(s):
            three = s[i:i+3]
            if three in LONG_TO_UTF8:
                result.append(LONG_TO_UTF8[three])
                i += 3
                continue
        # Try 2-char match
        if i + 2 <= len(s):
            two = s[i:i+2]
            if two in LONG_TO_UTF8:
                result.append(LONG_TO_UTF8[two])
                i += 2
                continue
        # Keep single character as-is (shouldn't normally happen)
        result.append(s[i])
        i += 1
    return "".join(result)
