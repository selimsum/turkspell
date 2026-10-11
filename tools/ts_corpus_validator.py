#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turkspell TS Corpus (LexiTR) Validation & Prestige Filter
Connects to TS Corpus / LexiTR API to evaluate candidate words by their
academic, informative, fictional, and social media frequencies.

API Endpoint:
    http://lexitr.tscorpus.com/freq/frequency?word={word}&query_type=as_is
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

LEXITR_API_URL = "http://lexitr.tscorpus.com/freq/frequency"
DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent / "raw_data" / "lexitr_cache.json"


def query_ts_corpus(word: str, timeout: int = 8) -> Dict[str, Any]:
    """Queries LexiTR API for a single Turkish word and returns frequency metrics.
    
    Returns:
        dict with academic_freq, informative_freq, fictional_freq, social_freq,
        total_freq, prestige_score, and is_prestigious flag.
    """
    clean_word = word.strip().lower()
    encoded = urllib.parse.quote(clean_word)
    url = f"{LEXITR_API_URL}?word={encoded}&query_type=as_is"
    
    headers = {
        "User-Agent": "Turkspell-Linguistic-Miner/1.0 (Mozilla-compatible research client)"
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                g_freqs = data.get("genre_frequencies", [])
                if g_freqs and isinstance(g_freqs, list):
                    stats = g_freqs[0]
                    acad = int(stats.get("academic_freq", 0))
                    info = int(stats.get("informative_freq", 0))
                    fict = int(stats.get("fictional_freq", 0))
                    social = int(stats.get("social_media_freq", 0))
                    total = int(stats.get("total_freq", 0))
                    
                    # Prestige score weighs formal written language over casual social media noise
                    score = (acad * 3.0) + (info * 2.0) + (fict * 1.5) + (social * 0.2)
                    is_prestigious = (acad > 0 or info > 0 or fict > 0)
                    
                    return {
                        "word": clean_word,
                        "academic_freq": acad,
                        "informative_freq": info,
                        "fictional_freq": fict,
                        "social_freq": social,
                        "total_freq": total,
                        "prestige_score": round(score, 2),
                        "is_prestigious": is_prestigious,
                        "found": total > 0
                    }
    except Exception as e:
        pass
        
    return {
        "word": clean_word,
        "academic_freq": 0,
        "informative_freq": 0,
        "fictional_freq": 0,
        "social_freq": 0,
        "total_freq": 0,
        "prestige_score": 0.0,
        "is_prestigious": False,
        "found": False
    }


def load_cache(cache_path: Path) -> Dict[str, Dict[str, Any]]:
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, Dict[str, Any]], cache_path: Path):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def batch_validate_candidates(
    words: List[str],
    max_workers: int = 5,
    cache_path: Optional[Path] = None,
    save_interval: int = 100
) -> Dict[str, Dict[str, Any]]:
    """Enriches a batch of candidate words using LexiTR API with caching and concurrency."""
    cache_path = cache_path or DEFAULT_CACHE_PATH
    cache = load_cache(cache_path)
    results = {}
    
    uncached = []
    for w in words:
        clean_w = w.strip().lower()
        if clean_w in cache:
            results[clean_w] = cache[clean_w]
        else:
            uncached.append(clean_w)
            
    print(f"Validating {len(words)} candidates ({len(results)} cached, {len(uncached)} to query from TS Corpus)...")
    
    if not uncached:
        return results
        
    def _worker(target_w: str):
        # Polite query delay to avoid hammering TS Corpus
        time.sleep(0.04)
        return target_w, query_ts_corpus(target_w)

    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_worker, w): w for w in uncached}
        for future in as_completed(futures):
            target_w, metrics = future.result()
            results[target_w] = metrics
            cache[target_w] = metrics
            completed += 1
            
            if completed % save_interval == 0:
                print(f"  Processed {completed}/{len(uncached)} TS Corpus queries...")
                save_cache(cache, cache_path)
                
    save_cache(cache, cache_path)
    print(f"Validation complete! Total words cached in {cache_path}: {len(cache):,}")
    return results


def main():
    parser = argparse.ArgumentParser(description="TS Corpus / LexiTR Candidate Validator")
    parser.add_argument("--word", type=str, help="Single word to query")
    parser.add_argument("--input", type=str, help="Input JSON file containing list of words or candidate dicts")
    parser.add_argument("--output", type=str, help="Output JSON file for enriched candidates")
    parser.add_argument("--cache", type=str, default=str(DEFAULT_CACHE_PATH), help="Path to cache JSON file")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent workers")
    args = parser.parse_args()

    cache_path = Path(args.cache)

    if args.word:
        res = query_ts_corpus(args.word)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    if args.input:
        in_path = Path(args.input)
        if not in_path.exists():
            print(f"Error: input file '{args.input}' not found.")
            sys.exit(1)
            
        with open(in_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                word_list = [item.get("word") for item in data if item.get("word")]
            else:
                word_list = [str(x) for x in data]
        elif isinstance(data, dict):
            word_list = list(data.keys())
        else:
            print("Unsupported JSON input structure.")
            sys.exit(1)
            
        enriched_map = batch_validate_candidates(word_list, max_workers=args.workers, cache_path=cache_path)
        
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(enriched_map, f, ensure_ascii=False, indent=2)
            print(f"Saved results to {out_path}")
        else:
            prestigious_count = sum(1 for m in enriched_map.values() if m.get("is_prestigious"))
            print(f"\nSummary:")
            print(f"  Total queried: {len(enriched_map)}")
            print(f"  Prestigious (Academic/Informative > 0): {prestigious_count} ({prestigious_count/len(enriched_map)*100:.1f}%)")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
