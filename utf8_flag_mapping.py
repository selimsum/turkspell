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
    # Proper Noun morphological classes (with apostrophe prefix)
    "uA", "uY", "uL", "uR", "uN", "uI", "uQ", "uP", "u1", "u2", "u3", "u4", "uC",
    # Verb flags
    "VB", "VR", "VF", "VG", "VA", "VS", "VE", "VH", "VK", "VL", "VM", "VN", "VY",
    # Obsolete
    "NS"
])

# Map each 2-char flag to a unique Cyrillic codepoint starting at \u0400 (1024)
LONG_TO_UTF8 = {flag: chr(1024 + idx) for idx, flag in enumerate(ALL_FLAGS)}
UTF8_TO_LONG = {v: k for k, v in LONG_TO_UTF8.items()}

def remap_flag_string(s: str) -> str:
    """Convert a concatenated string of 2-character flags into a string of single UTF-8 characters."""
    if not s:
        return ""
    # Split s into 2-character chunks
    chunks = [s[i:i+2] for i in range(0, len(s), 2)]
    remapped = []
    for c in chunks:
        if c in LONG_TO_UTF8:
            remapped.append(LONG_TO_UTF8[c])
        else:
            # If it's already a single character or not in our map, keep it
            remapped.append(c)
    return "".join(remapped)
