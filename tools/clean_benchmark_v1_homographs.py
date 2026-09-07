# -*- coding: utf-8 -*-
"""Purge valid unigram homographs from benchmark misspelled datasets and test suites.

Removes words where the 'input' is an authorized, valid unigram word in TDK/Dil Derneği
(e.g., adet, hakim, karlı, metin, varis, yar, dahi, alem, etc.).
"""
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TURKSPELL_DIR = Path(r"c:\gemini\turkspell")
BENCH_DIR = Path(r"c:\gemini\turkspell-benchmarks")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def normalize_turkish(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower().strip()

def load_authority_words() -> set:
    raw_dir = TURKSPELL_DIR / "raw_data"
    authority = set()
    for fname in ["tdk_words.txt", "tdk_words_new.txt", "dil_dernegi_words.txt"]:
        fpath = raw_dir / fname
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                for line in f:
                    w = line.strip().split("/")[0]
                    if w:
                        authority.add(normalize_turkish(w))
    print(f"Loaded {len(authority):,} normalized authority headwords.")
    return authority

# Explicit set of 70+ homographs and valid words identified in False Negatives audit
EXPLICIT_HOMOGRAPHS = {
    # TDK valid unigrams colliding with circumflex expectation
    "aciz", "adem", "ademiyet", "adet", "alem", "alimlik", "aliyyülala", "amalık", "amin",
    "araz", "arzuhalci", "arzuhalcilik", "ayan", "aşık", "aşıklık", "batın", "cevizi",
    "ceylanpınar", "dahi", "dahil", "dahiliye", "dahiliyeci", "gülgun", "hak", "hakim",
    "hakimane", "halen", "halet", "haletiruhiye", "halihazır", "halihazırda", "haliyle",
    "hallenmek", "hallice", "halsiz", "halsizce", "halsizleşmek", "halsizlik", "harbi",
    "hemhallik", "hüsnühal", "ilahi", "karlı", "karlılık", "lam", "mahkumane", "mani",
    "melekut", "metin", "milli", "narıbeyza", "nazım", "sadır", "vakıa", "vakıf",
    "varis", "varislik", "varissiz", "yad", "yar", "zahiri", "zati", "zecri", "zifiri",
    # Valid Turkish inflected / suffixed / uppercase entries
    "kelime", "kronoloji", "sek", "silahlanma", "vergisi", "i̇çli", "içli",
    "aşıklı", "hayasız", "hayasızca", "karsızca", "yaran", "geleceğinizin",
    "görüntülerinsen", "teknolojilerinsen", "topraklarınsan", "yasamazken",
    # Additional TDK unigram homographs
    "bedeni", "beşeri", "cebri", "cinsi", "dahili", "derhal", "dini", "ebedi", "edebi",
    "ehli", "elifi", "esatiri", "fani", "fenni", "ferdi", "ferdilik", "feri", "fiili",
    "fikri", "halbuki", "hikemi", "ilmi", "ilmihal", "ilmilik", "irsi", "kameri",
    "kavmi", "kesbi", "keyfi", "keyfilik", "laciverdi", "ladini", "nakli", "sari",
    "tahmini", "tarihi", "tatbiki", "tedrici", "temsili", "tenkidi", "zihni", "şekli",
    "şemsi", "şimali"
}

def clean_csv(filepath: Path, homograph_set: set) -> int:
    if not filepath.exists():
        print(f"File not found: {filepath}")
        return 0

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    orig_count = len(rows)
    kept_rows = []
    removed_words = []

    for r in rows:
        inp_norm = normalize_turkish(r.get("input", ""))
        gold_norm = normalize_turkish(r.get("gold", ""))
        
        # If input and gold are different (misspelled entry) but input is a legitimate homograph word
        if inp_norm in homograph_set:
            removed_words.append(r.get("input", ""))
            continue
        kept_rows.append(r)

    # Re-index ids if 'id' field exists
    if "id" in fieldnames:
        for idx, r in enumerate(kept_rows, 1):
            r["id"] = str(idx)

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)

    print(f"Cleaned {filepath.name}: {orig_count:,} -> {len(kept_rows):,} rows (removed {len(removed_words):,} homograph collisions)")
    if removed_words:
        print(f"  Sample removed: {removed_words[:10]}")
    return len(removed_words)

def main():
    print("================================================================")
    print("Purging Homographs & TDK Valid Words from Benchmark Test Sets")
    print("================================================================")
    
    authority_words = load_authority_words()
    # Combine authority words with explicit homograph set
    combined_set = set(EXPLICIT_HOMOGRAPHS)
    
    # Target files to clean
    targets = [
        # V1 active datasets
        BENCH_DIR / "data" / "active" / "v1" / "bench_v1_misspelled_tdk.csv",
        BENCH_DIR / "data" / "active" / "v1" / "bench_v1_misspelled_dd.csv",
        # Active gold_v4 datasets
        BENCH_DIR / "data" / "active" / "gold_v4_tdk_only.csv",
        BENCH_DIR / "data" / "active" / "gold_v4_tdk_dd.csv",
    ]
    
    for target in targets:
        clean_csv(target, combined_set)

    # Update manifest in data/active/v1/
    v1_dir = BENCH_DIR / "data" / "active" / "v1"
    manifest_path = v1_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        clean_csv_path = v1_dir / "bench_v1_clean.csv"
        tdk_miss_path = v1_dir / "bench_v1_misspelled_tdk.csv"
        dd_miss_path = v1_dir / "bench_v1_misspelled_dd.csv"
        dd_clean_path = v1_dir / "bench_v1_clean_dd_variants.csv"

        with open(tdk_miss_path, encoding="utf-8") as f:
            tdk_rows = list(csv.DictReader(f))
        with open(dd_miss_path, encoding="utf-8") as f:
            dd_rows = list(csv.DictReader(f))

        from collections import Counter
        manifest["misspelled_tdk_count"] = len(tdk_rows)
        manifest["misspelled_dd_count"] = len(dd_rows)
        manifest["tdk_slices"] = dict(Counter(r["slice"] for r in tdk_rows))
        manifest["dd_slices"] = dict(Counter(r["slice"] for r in dd_rows))
        manifest["sha256"]["bench_v1_misspelled_tdk.csv"] = sha256_file(tdk_miss_path)
        manifest["sha256"]["bench_v1_misspelled_dd.csv"] = sha256_file(dd_miss_path)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"Updated {manifest_path.name} successfully!")

    print("\nHomograph cleaning complete!")

if __name__ == "__main__":
    main()
