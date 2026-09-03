# -*- coding: utf-8 -*-
"""
Applies verified errata from 'raw_data/tdk_errata.json' to 'raw_data/tdk_words.txt'
Corrects typesetting and optical errors from "Türkçe Sözlüğün Ters Alfabetik Dizimi".
"""

import sys
import json
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
TDK_PATH = ROOT_DIR / "raw_data" / "tdk_words.txt"
ERRATA_PATH = ROOT_DIR / "raw_data" / "tdk_errata.json"

def apply_errata():
    print(f"Loading errata from {ERRATA_PATH}...")
    with open(ERRATA_PATH, "r", encoding="utf-8") as f:
        errata = json.load(f)
        
    corrections = errata.get("corrections", {})
    purges = set(errata.get("purged_typesetting_artifacts", []))
    
    print(f"Loaded {len(corrections)} corrections and {len(purges)} purges.")
    
    with open(TDK_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        
    updated_entries = []
    replaced_count = 0
    purged_count = 0
    
    for line in lines:
        parts = line.split("/")
        word = parts[0]
        flags = "/" + parts[1] if len(parts) > 1 else ""
        
        if word in purges or word.lower() in purges:
            purged_count += 1
            continue
            
        if word in corrections:
            corrected_word = corrections[word]
            updated_entries.append(f"{corrected_word}{flags}")
            replaced_count += 1
        else:
            updated_entries.append(line)
            
    # Deduplicate while preserving case and order
    seen = set()
    final_entries = []
    for entry in updated_entries:
        if entry not in seen:
            seen.add(entry)
            final_entries.append(entry)
            
    print(f"Replaced {replaced_count} typesetting errors with verified corrections.")
    print(f"Purged {purged_count} typesetting artifacts.")
    print(f"Writing {len(final_entries):,} entries to {TDK_PATH}...")
    
    with open(TDK_PATH, "w", encoding="utf-8") as f:
        for entry in final_entries:
            f.write(entry + "\n")
            
    print("Successfully updated raw_data/tdk_words.txt!")

if __name__ == "__main__":
    apply_errata()
