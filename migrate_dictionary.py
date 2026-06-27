"""
migrate_dictionary.py
=====================
Converts tr.dic (integer FLAG-based) → tr_v2.dic (FLAG long 2-char-based).

Integer flag → FLAG long mapping:
  Noun stem classes:
    1   → B1  (back, consonant, unrounded)
    101 → B2  (back, consonant, rounded)
    2   → F1  (front, consonant, unrounded)
    102 → F2  (front, consonant, rounded)
    3   → B3  (back, vowel-ending, unrounded)
    103 → B4  (back, vowel-ending, rounded)
    4   → F3  (front, vowel-ending, unrounded)
    104 → F4  (front, vowel-ending, rounded)
    5   → V1  (back, consonant, voicing, unrounded)
    105 → V2  (back, consonant, voicing, rounded)
    6   → V3  (front, consonant, voicing, unrounded)
    106 → V4  (front, consonant, voicing, rounded)
    7   → D1  (back, consonant, vowel-drop, unrounded)
    107 → D2  (back, consonant, vowel-drop, rounded)
    8   → D3  (front, consonant, vowel-drop, unrounded)
    108 → D4  (front, consonant, vowel-drop, rounded)
    13  → C1  (back compound)
    113 → C2  (back compound rounded)
    14  → C3  (front compound)
    114 → C4  (front compound rounded)
    18  → G1  (back, doubling)
    118 → G2  (back, doubling rounded)
    19  → G3  (front, doubling)
    119 → G4  (front, doubling rounded)
    90  → PX  (prefix flag)

  Verb stem classes:
    9   → VB  (back consonant, unrounded)
    109 → VR  (back consonant, rounded)
    10  → VF  (front consonant, unrounded)
    110 → VG  (front consonant, rounded)
    11  → VA  (back vowel stem, unrounded)
    111 → VS  (back vowel stem, rounded)
    12  → VE  (front vowel stem, unrounded)
    112 → VH  (front vowel stem, rounded)
    15  → VK  (back consonant voicing)
    115 → VL  (back consonant voicing, rounded)
    16  → VM  (front consonant voicing)
    116 → VN  (front consonant voicing, rounded)
    17  → VY  (narrowing: demek/yemek)

Additionally, each noun entry gets the appropriate morphological layer flags
(case, plural, possessive, copula, derivation) appended based on its stem class.

For the FIRST version of migration, we:
1. Map the integer stem flag to FLAG long.
2. Append the standard morphological chain for each noun stem class.
3. For verb entries, just rename the verb flag.
4. Leave special/multi-flag entries (like compound nouns) with a warning comment.
"""

import re
import sys
import os
import json
from pathlib import Path
from utf8_flag_mapping import remap_flag_string


# ---------------------------------------------------------------------------
# Flag mapping
# ---------------------------------------------------------------------------

NOUN_FLAG_MAP = {
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

VERB_FLAG_MAP = {
    9:   "VB",  109: "VR",
    10:  "VF",  110: "VG",
    11:  "VA",  111: "VS",
    12:  "VE",  112: "VH",
    15:  "VK",  115: "VL",
    16:  "VM",  116: "VN",
    17:  "VY",
}

ALL_FLAG_MAP = {**NOUN_FLAG_MAP, **VERB_FLAG_MAP}

# ---------------------------------------------------------------------------
# Noun morphological chains per harmony class
# ---------------------------------------------------------------------------
# Each noun stem class maps to a set of morphological flags.
# The chain includes: cases, plural, all possessives, copula, relative-ki, derivations.

def noun_chain(stem_flag: str) -> str:
    """Return the morphological flag chain for a given stem class flag."""
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

    # Case flags split by harmony
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

    return (
        f"{stem_flag}"
        f"{cases}"
        f"{plural}"
        f"{possessives}"
        f"CL"
        f"LILKSZCI"
        f"DLDTDE"
    )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_flags(flag_str: str) -> list[int]:
    """Parse comma-separated integer flags from a dic entry flag field."""
    parts = flag_str.split(',')
    result = []
    for p in parts:
        p = p.strip()
        if p.isdigit():
            result.append(int(p))
    return result


def migrate_line(line: str, line_num: int, obsolete_set: set[str] = None) -> tuple[str, str]:
    """
    Migrate a single dictionary line.
    Returns (migrated_line, warning_message).
    """
    line = line.rstrip('\n')
    if not line or line.startswith('#'):
        return line, ''

    # Format: word/flags  OR  word (no flags)
    if '/' in line:
        slash_pos = line.index('/')
        word = line[:slash_pos]
        flag_part = line[slash_pos+1:].split()[0]  # flags only (ignore trailing whitespace/comments)
        flags = parse_flags(flag_part)
    else:
        # No flags — check if word is obsolete
        word = line
        w_lower = word.replace('I', 'ı').replace('İ', 'i').lower()
        if obsolete_set and w_lower in obsolete_set:
            return f"{word}/NS", ''
        return line, ''

    if not flags:
        return line, f'Line {line_num}: Could not parse flags from "{flag_part}"'

    # Check if word is obsolete
    is_obsolete = False
    w_lower = word.replace('I', 'ı').replace('İ', 'i').lower()
    if obsolete_set and w_lower in obsolete_set:
        is_obsolete = True

    # Check if it's a verb flag only
    verb_flags = set(flags) & set(VERB_FLAG_MAP.keys())
    noun_flags_set = set(flags) & set(NOUN_FLAG_MAP.keys())
    # Flag 90 = PX prefix — can legitimately appear alongside a noun stem flag
    has_prefix = 90 in noun_flags_set
    pure_noun_flags = noun_flags_set - {90}  # noun stem flags (not prefix)
    other_flags = set(flags) - set(ALL_FLAG_MAP.keys())

    warnings = []
    if other_flags:
        warnings.append(f'Line {line_num}: Unknown flags {other_flags} in "{line[:60]}"')

    if len(pure_noun_flags) > 1:
        warnings.append(f'Line {line_num}: Multiple noun flags {pure_noun_flags} in "{line[:60]}" — manual review needed')

    if verb_flags and pure_noun_flags:
        # Mixed entry (e.g., compound with both noun + verb paradigm)
        warnings.append(f'Line {line_num}: Mixed noun+verb flags in "{line[:60]}" — manual review')

    # Build new flag string
    new_flags_parts = []

    if verb_flags and not pure_noun_flags:
        # Pure verb entry: just remap verb flag
        for vf in sorted(verb_flags):
            new_flags_parts.append(VERB_FLAG_MAP[vf])
        if is_obsolete:
            new_flags_parts.append("NS")
        new_line = f"{word}/{''.join(new_flags_parts)}"

    elif pure_noun_flags:
        # Noun entry: remap stem class + append morphological chain
        nf = min(pure_noun_flags)  # use primary noun flag
        stem_flag = NOUN_FLAG_MAP[nf]

        chain = noun_chain(stem_flag)
        new_parts = [chain]
        if has_prefix:
            new_parts.append("PX")  # also takes metric prefixes
        for vf in sorted(verb_flags):
            new_parts.append(VERB_FLAG_MAP[vf])
        if is_obsolete:
            new_parts.append("NS")
        new_line = f"{word}/{''.join(new_parts)}"

    elif has_prefix and not pure_noun_flags:
        # Only prefix flag (rare — standalone prefix entry)
        if is_obsolete:
            new_line = f"{word}/PXNS"
        else:
            new_line = f"{word}/PX"

    else:
        # No recognized flags — keep as-is (add NS if obsolete)
        if is_obsolete:
            new_line = f"{word}/NS"
        else:
            new_line = line
        warnings.append(f'Line {line_num}: No recognized flags in "{line[:60]}"')

    return new_line, '\n'.join(warnings)


def migrate_dictionary(input_path: str = 'tr.dic',
                       output_path: str = 'tr_v2.dic',
                       max_warnings: int = 50):
    """Main migration function."""
    # Load obsolete lemmas
    obsolete_set = set()
    obsolete_path = r"C:\Users\selim\.gemini\antigravity-ide\brain\367fb0b0-eb2a-4a2c-9259-f2c7a24d09eb\scratch\obsolete_lemmas.json"
    if os.path.exists(obsolete_path):
        try:
            with open(obsolete_path, 'r', encoding='utf-8') as f:
                obsolete_list = json.load(f)
                obsolete_set = set(obsolete_list)
            print(f"Loaded {len(obsolete_set)} obsolete lemmas to flag as NOSUGGEST.")
        except Exception as e:
            print(f"Error loading obsolete lemmas: {e}")
    else:
        print("Warning: obsolete_lemmas.json not found. No words will be flagged as NOSUGGEST.")

    print(f"Reading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total = len(lines)
    count_line = lines[0].strip()  # First line is word count
    data_lines = lines[1:]

    print(f"Total entries: {count_line}")
    print(f"Migrating...")

    out_lines = []
    all_warnings = []
    migrated = 0
    skipped = 0

    for i, line in enumerate(data_lines, start=2):
        new_line, warning = migrate_line(line, i, obsolete_set)
        if warning:
            all_warnings.append(warning)
        if new_line is not None:
            new_line = new_line.rstrip('\n')
            if '/' in new_line:
                word, flags_str = new_line.split('/', 1)
                utf8_flags = remap_flag_string(flags_str)
                new_line = f"{word}/{utf8_flags}"
            out_lines.append(new_line + '\n')
            migrated += 1

    # Write output
    print(f"Writing {output_path}...")
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"{migrated}\n")
        f.writelines(out_lines)

    print(f"Done. {migrated} entries written.")

    if all_warnings:
        print(f"\n{len(all_warnings)} warnings:")
        for w in all_warnings[:max_warnings]:
            print(f"  {w}")
        if len(all_warnings) > max_warnings:
            print(f"  ... and {len(all_warnings) - max_warnings} more")

    return len(all_warnings)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Migrate tr.dic to FLAG long format')
    parser.add_argument('--input',  default='tr.dic',    help='Input dictionary file')
    parser.add_argument('--output', default='tr_v2.dic', help='Output dictionary file')
    parser.add_argument('--max-warnings', type=int, default=50,
                        help='Max warnings to display (default: 50)')
    args = parser.parse_args()

    n_warnings = migrate_dictionary(args.input, args.output, args.max_warnings)
    if n_warnings > 0:
        print(f"\nWarning: {n_warnings} entries may need manual review.")
    else:
        print("\nMigration clean — no warnings.")
    sys.exit(0 if n_warnings == 0 else 1)


if __name__ == '__main__':
    main()
