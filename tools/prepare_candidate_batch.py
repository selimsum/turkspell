# -*- coding: utf-8 -*-
"""
Helper to prepare next batch of unparsed candidates from fineweb2_unrecognized_candidates.json.
Filters out:
- Already parsed candidates in fineweb2_parsed_entries.json
- Detached suffix fragments from split apostrophes (e.g., 'nın', 'nin', 'daki', 'den', 'lerden')
- Common web/English stopwords (e.g., 'the', 'and', 'for', 'online', 'http')
- Pure noise
"""

import json
import re
from pathlib import Path

COMMON_JUNK_WORDS = {
    "the", "and", "for", "with", "from", "this", "that", "you", "your",
    "http", "https", "www", "com", "net", "org", "html", "php",
    "online", "chat", "escort", "free", "live", "video", "download",
    "app", "pro", "max", "iphone", "samsung", "facebook", "instagram", "twitter"
}

# Suffixes often split by apostrophes in messy web text
DETACHED_SUFFIXES = {
    "nin", "nın", "nün", "nun",
    "in", "ın", "ün", "un",
    "e", "a", "ye", "ya",
    "i", "ı", "ü", "u", "yi", "yı", "yü", "yu",
    "de", "da", "te", "ta",
    "den", "dan", "ten", "tan",
    "le", "la", "yle", "yla",
    "li", "lı", "lü", "lu",
    "siz", "sız", "süz", "suz",
    "ci", "cı", "cü", "cu", "çi", "çı", "çü", "çu",
    "ler", "lar", "leri", "ları", "lerden", "lardan", "lerine", "larına",
    "deki", "daki", "teki", "taki",
    "dir", "dır", "dür", "dur", "tir", "tır", "tür", "tur",
    "si", "sı", "sü", "su",
    "nde", "nda", "nden", "ndan",
    "ce", "ca", "çe", "ça",
}

def clean_candidates(cand_path, parsed_path, output_batch_path, max_batch=5000):
    with open(cand_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    parsed_words = set()
    if Path(parsed_path).exists():
        with open(parsed_path, "r", encoding="utf-8") as f:
            parsed = json.load(f)
            parsed_words = {p["word"] for p in parsed if isinstance(p, dict) and "word" in p}

    clean_batch = []
    skipped_parsed = 0
    skipped_junk = 0
    skipped_detached = 0

    for item in candidates:
        word = item["word"] if isinstance(item, dict) else item
        freq = item["freq"] if isinstance(item, dict) else 1

        if word in parsed_words:
            skipped_parsed += 1
            continue

        if word in COMMON_JUNK_WORDS:
            skipped_junk += 1
            continue

        if word in DETACHED_SUFFIXES:
            skipped_detached += 1
            continue

        clean_batch.append({"word": word, "freq": freq})
        if len(clean_batch) >= max_batch:
            break

    print(f"Total candidates scanned: {len(candidates)}")
    print(f"  Already parsed: {skipped_parsed}")
    print(f"  Skipped detached suffixes: {skipped_detached}")
    print(f"  Skipped foreign/web junk: {skipped_junk}")
    print(f"  Selected clean unparsed candidates for next batch: {len(clean_batch)}")

    with open(output_batch_path, "w", encoding="utf-8") as f:
        json.dump([item["word"] for item in clean_batch], f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved next batch to {output_batch_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Prepare clean candidate batches for LLM morphology parsing")
    parser.add_argument("--candidates", default="raw_data/fineweb2_unrecognized_candidates.json", help="Input unparsed candidates JSON")
    parser.add_argument("--parsed", default="raw_data/fineweb2_parsed_entries.json", help="Already parsed entries JSON")
    parser.add_argument("--output", default="raw_data/fineweb2_llm_input_batch4.json", help="Output batch JSON")
    parser.add_argument("--max-batch", type=int, default=5000, help="Maximum batch size (default: 5000)")
    args = parser.parse_args()
    clean_candidates(
        args.candidates,
        args.parsed,
        args.output,
        max_batch=args.max_batch,
    )
