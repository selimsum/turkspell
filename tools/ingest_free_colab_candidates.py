#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turkspell Ingestion Pipeline for Free Colab & TS Corpus Mined Candidates
Audits, filters, and partitions mined candidates against official TDK and Dil Derneği lexicons.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = ROOT_DIR / "raw_data"
LEXICONS_DIR = ROOT_DIR / "lexicons"
DIST_DIR = ROOT_DIR / "dist"

TDK_WORDS_PATH = RAW_DATA_DIR / "tdk_words.txt"
DD_WORDS_PATH = RAW_DATA_DIR / "dil_dernegi_words.txt"
AUTHORITY_POS_PATH = LEXICONS_DIR / "authority_pos_completed.json"

WINGET_PKG_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(WINGET_PKG_DIR):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
HUNSPELL_BIN = shutil.which("hunspell") or "hunspell"


def turkish_lower(s: str) -> str:
    return s.replace("İ", "i").replace("I", "ı").lower()


def load_authorities() -> Tuple[Set[str], Set[str], Dict[str, str]]:
    """Loads TDK, Dil Derneği words and circumflex mapping."""
    tdk_words = set()
    dd_words = set()
    circumflex_map = {}

    if TDK_WORDS_PATH.exists():
        with open(TDK_WORDS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and not w.startswith("#"):
                    clean = turkish_lower(w)
                    tdk_words.add(clean)
                    unhatted = (
                        clean.replace("â", "a")
                        .replace("î", "i")
                        .replace("û", "u")
                        .replace("ô", "o")
                    )
                    if unhatted != clean:
                        circumflex_map[unhatted] = clean

    if DD_WORDS_PATH.exists():
        with open(DD_WORDS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and not w.startswith("#"):
                    clean = turkish_lower(w)
                    dd_words.add(clean)
                    unhatted = (
                        clean.replace("â", "a")
                        .replace("î", "i")
                        .replace("û", "u")
                        .replace("ô", "o")
                    )
                    if unhatted != clean and unhatted not in circumflex_map:
                        circumflex_map[unhatted] = clean

    return tdk_words, dd_words, circumflex_map


def check_with_hunspell(words: List[str], dict_prefix: str = "tr") -> Set[str]:
    """Returns set of words recognized by the current Hunspell dictionary."""
    if not words:
        return set()
    try:
        p = subprocess.run(
            [HUNSPELL_BIN, "-d", dict_prefix, "-l"],
            input="\n".join(words) + "\n",
            text=True,
            capture_output=True,
            encoding="utf-8",
            check=False
        )
        flagged = set(line.strip() for line in p.stdout.splitlines() if line.strip())
        recognized = set(words) - flagged
        return recognized
    except Exception as e:
        print(f"Hunspell check error: {e}")
        return set()


def ingest_mined_candidates(
    input_file: Path,
    output_dir: Path,
    min_prestige: float = 0.0,
    check_hunspell: bool = True
):
    """Audits mined entries, segregates authority matches, circumflex mismatches, and noise."""
    tdk_words, dd_words, circumflex_map = load_authorities()
    authority_words = tdk_words | dd_words
    print(f"Loaded authority lexicons: {len(tdk_words):,} TDK words, {len(dd_words):,} Dil Derneği words.")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        entries = list(data.values()) if any(isinstance(v, dict) for v in data.values()) else [{"word": k} for k in data]
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError("Unsupported JSON file format.")

    print(f"Processing {len(entries):,} input candidates from {input_file}...")

    authority_exact = []
    circumflex_mismatches = []
    unattested_entries = []

    words_to_check = []
    for item in entries:
        w = item.get("word", "")
        lemma = item.get("lemma") or w
        if not lemma:
            continue
            
        clean_lemma = turkish_lower(lemma)
        clean_word = turkish_lower(w)
        
        # Check prestige score filter if present
        prestige = item.get("prestige_score", 0.0)
        if min_prestige > 0 and prestige < min_prestige:
            continue
            
        words_to_check.append(clean_word)

        if clean_lemma in authority_words or clean_word in authority_words:
            matched_authority = "TDK+DD" if (clean_lemma in tdk_words and clean_lemma in dd_words) else ("TDK" if clean_lemma in tdk_words else "DD")
            authority_exact.append({
                "word": clean_word,
                "lemma": clean_lemma,
                "pos": item.get("pos"),
                "attributes": item.get("attributes", []),
                "authority": matched_authority,
                "prestige_score": prestige,
                "academic_freq": item.get("academic_freq", 0),
                "informative_freq": item.get("informative_freq", 0),
                "total_freq": item.get("total_freq", 0),
                "source_count": item.get("corpus_count", item.get("count", 1))
            })
        elif clean_lemma in circumflex_map or clean_word in circumflex_map:
            correct_hatted = circumflex_map.get(clean_lemma, circumflex_map.get(clean_word))
            circumflex_mismatches.append({
                "word": clean_word,
                "unhatted_lemma": clean_lemma,
                "official_hatted_lemma": correct_hatted,
                "prestige_score": prestige,
                "source_count": item.get("corpus_count", item.get("count", 1))
            })
        else:
            unattested_entries.append({
                "word": clean_word,
                "lemma": clean_lemma,
                "pos": item.get("pos"),
                "attributes": item.get("attributes", []),
                "prestige_score": prestige,
                "source_count": item.get("corpus_count", item.get("count", 1))
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check Hunspell status of authority candidates
    if check_hunspell and authority_exact:
        test_words = [item["word"] for item in authority_exact]
        recognized = check_with_hunspell(test_words)
        for item in authority_exact:
            item["hunspell_recognized"] = item["word"] in recognized
            
        missing_count = sum(1 for item in authority_exact if not item.get("hunspell_recognized"))
        print(f"\nHunspell Recognition on Authority Matches:")
        print(f"  Already Recognized: {len(authority_exact) - missing_count:,}")
        print(f"  Currently REJECTED (Genuine Grammar/Affix/Stem Gaps): {missing_count:,}")

    # Save segregated JSONs
    with open(output_dir / "authority_exact_entries.json", "w", encoding="utf-8") as f:
        json.dump(authority_exact, f, ensure_ascii=False, indent=2)

    with open(output_dir / "authority_circumflex_entries.json", "w", encoding="utf-8") as f:
        json.dump(circumflex_mismatches, f, ensure_ascii=False, indent=2)

    with open(output_dir / "unattested_corpus_entries.json", "w", encoding="utf-8") as f:
        json.dump(unattested_entries, f, ensure_ascii=False, indent=2)

    print(f"\n================ Ingestion Summary ================")
    print(f"  Total Candidates Processed:     {len(entries):,}")
    print(f"  Exact Authority Matches (TDK/DD): {len(authority_exact):,} -> raw_data/authority_exact_entries.json")
    print(f"  Circumflex Mismatches (Hats):   {len(circumflex_mismatches):,} -> raw_data/authority_circumflex_entries.json")
    print(f"  Unattested Words (Noise/Slang): {len(unattested_entries):,} -> raw_data/unattested_corpus_entries.json")
    print(f"====================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Ingest and audit mined candidates from Colab Free Tier / TS Corpus")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON file from Colab mining")
    parser.add_argument("--output-dir", type=str, default=str(RAW_DATA_DIR), help="Output directory for partitioned datasets")
    parser.add_argument("--min-prestige", type=float, default=0.0, help="Minimum TS Corpus prestige score threshold")
    parser.add_argument("--skip-hunspell", action="store_true", help="Skip checking current Hunspell dictionary")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file '{args.input}' does not exist.")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    ingest_mined_candidates(
        input_path,
        output_dir,
        min_prestige=args.min_prestige,
        check_hunspell=not args.skip_hunspell
    )


if __name__ == "__main__":
    main()
