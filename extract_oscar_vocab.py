"""
Extract Turkish vocabulary from the OSCAR corpus (latest version) and identify
candidate words missing from the current Hunspell dictionary.

Usage:
    python extract_oscar_vocab.py [--limit N] [--min-freq N] [--hf-token TOKEN]

# Requirements:
#     pip install datasets zstandard
"""
import argparse
import html
import os
import re
import subprocess
import sys
from collections import Counter

# Pre-compiled regex for Turkish-only alphabetic tokens (no digits, no q/w/x)
# Matches lowercase and uppercase equivalent Turkish characters using Unicode escapes
_TURKISH_WORD_RE = re.compile(
    r'^[abc\u00e7defg\u011fh\u0131ijklmno\u00f6prs\u015ftu\u00fcvyz\u00e2\u00ee\u00fb]+$', re.IGNORECASE
)

# Pre-compiled regex for tokenization (extract alphabetic runs including circumflexes)
_TOKEN_RE = re.compile(
    r'[a-zA-Z\u00e7\u00c7\u011f\u011e\u0131\u0130\u00f6\u00d6\u015f\u015e\u00fc\u00dc\u00e2\u00c2\u00ee\u00ce\u00fb\u00db]+'
)


def turkish_lowercase(text):
    return (
        text.replace('I', '\u0131').replace('\u0130', 'i')
        .replace('\u00ce', '\u00ee').replace('\u00c2', '\u00e2').replace('\u00db', '\u00fb')
        .lower()
    )


def load_english_words():
    """Load a set of known English words for filtering."""
    path = 'english_words_large.txt'
    if not os.path.exists(path):
        print("Warning: english_words_large.txt not found. English filtering will be skipped.")
        return set()
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return {line.strip().lower() for line in f if line.strip()}


def load_root_words():
    """Load the merged root dictionary (lemmas only)."""
    dictionaries = set()
    path = 'merged_dictionary_cleaned.txt'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                w = line.strip()
                if w:
                    dictionaries.add(turkish_lowercase(w))
    return dictionaries


def hunspell_check(words, dict_path='tr'):
    """
    Run Hunspell to check which words are already accepted by the compiled dictionary.
    Returns the set of words that Hunspell does NOT recognize.
    """
    if not words:
        return set()

    print(f"  Writing {len(words):,} candidate words to temporary file...", flush=True)
    temp_file = '_oscar_hunspell_check.txt'
    try:
        with open(temp_file, 'w', encoding='utf-8', newline='\n') as f:
            for w in words:
                f.write(w + '\n')

        print("  Executing Hunspell CLI checker subprocess (may take a moment)...", flush=True)
        p = subprocess.Popen(
            ['hunspell', '-d', dict_path, '-l'],
            stdin=open(temp_file, 'r', encoding='utf-8'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate(timeout=300)
        unrecognized = set(stdout.decode('utf-8', errors='replace').splitlines())
        return unrecognized
    except FileNotFoundError:
        print("Warning: 'hunspell' binary not found. Skipping Hunspell verification.")
        print("Install with: sudo apt-get install -y hunspell")
        return set(words)  # Treat all as unrecognized if Hunspell isn't available
    except subprocess.TimeoutExpired:
        print("Warning: Hunspell timed out. Treating all candidates as unrecognized.")
        return set(words)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def extract_vocab(limit=100000, min_freq=5, hf_token=None):
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("Error: 'huggingface_hub' package is not installed.")
        print("Please run: pip install huggingface_hub")
        sys.exit(1)

    try:
        import zstandard as zstd
    except ImportError:
        print("Error: 'zstandard' package is not installed.")
        print("Please run: pip install zstandard")
        print("This is required to read community-oscar's compressed .zst files.")
        sys.exit(1)

    try:
        import requests
    except ImportError:
        print("Error: 'requests' package is not installed.")
        print("Please run: pip install requests")
        sys.exit(1)

    import json

    # --- Load filters ---
    english_words = load_english_words()
    root_words = load_root_words()
    print(f"Loaded {len(english_words)} English words and {len(root_words)} Turkish root lemmas for filtering.")

    # --- List files from HF Hub ---
    print("Listing Turkish metadata files from community-oscar repo on Hugging Face Hub...")
    api = HfApi(token=hf_token)
    try:
        files = api.list_repo_files(repo_id="oscar-corpus/community-oscar", repo_type="dataset")
    except Exception as e:
        print(f"Error listing repository files: {e}")
        print("Please ensure your HF token is correct and you have accepted the dataset terms.")
        sys.exit(1)

    tr_files = sorted([f for f in files if "tr_meta/" in f and f.endswith(".jsonl.zst")])
    if not tr_files:
        print("Error: No Turkish metadata files (tr_meta/*.jsonl.zst) found in the dataset repository.")
        sys.exit(1)

    print(f"Found {len(tr_files)} Turkish data shards to process.")

    # --- Process documents ---
    word_counts = Counter()
    capitalized_counts = Counter()
    total_counts = Counter()
    processed_docs = 0

    # --- Process local corpora (Wikipedia and Magazine) ---
    for local_file in ["wiki_corpus.txt", "magazine_corpus.txt"]:
        if os.path.exists(local_file):
            print(f"Processing local corpus: {local_file}...")
            try:
                with open(local_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        text = html.unescape(line)
                        tokens = _TOKEN_RE.findall(text)
                        for token in tokens:
                            if len(token) < 2:
                                continue
                            lower = turkish_lowercase(token)
                            if not _TURKISH_WORD_RE.match(lower):
                                continue
                            total_counts[lower] += 1
                            if token[0].isupper():
                                capitalized_counts[lower] += 1
            except Exception as e:
                print(f"Warning: Error reading local corpus {local_file}: {e}")

    print(f"Streaming and processing up to {limit:,} documents from OSCAR...")
    
    for file_path in tr_files:
        if processed_docs >= limit:
            break
            
        url = f"https://huggingface.co/datasets/oscar-corpus/community-oscar/resolve/main/{file_path}"
        headers = {}
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
            
        print(f"Processing shard: {file_path}")
        try:
            r = requests.get(url, headers=headers, stream=True)
            r.raise_for_status()
            
            dctx = zstd.ZstdDecompressor()
            decompressor = dctx.decompressobj()
            
            buffer = b""
            for chunk in r.iter_content(chunk_size=65536):
                if processed_docs >= limit:
                    break
                decompressed = decompressor.decompress(chunk)
                if decompressed:
                    buffer += decompressed
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        if not line.strip():
                            continue
                            
                        try:
                            doc = json.loads(line.decode('utf-8'))
                        except Exception:
                            continue
                            
                        text = doc.get("content", doc.get("text", ""))
                        text = html.unescape(text)
                        tokens = _TOKEN_RE.findall(text)
                        for token in tokens:
                            if len(token) < 2:
                                                                continue
                            lower = turkish_lowercase(token)
                            if not _TURKISH_WORD_RE.match(lower):
                                continue
                                
                            total_counts[lower] += 1
                            if token[0].isupper():
                                capitalized_counts[lower] += 1
                                
                        processed_docs += 1
                        if processed_docs % 10000 == 0:
                            print(f"  Processed {processed_docs:,} documents, unique tokens: {len(total_counts):,}")
                            
                        if processed_docs >= limit:
                            break
                            
            # Process remaining buffer
            if processed_docs < limit and buffer.strip():
                try:
                    doc = json.loads(buffer.decode('utf-8'))
                    text = doc.get("content", doc.get("text", ""))
                    text = html.unescape(text)
                    tokens = _TOKEN_RE.findall(text)
                    for token in tokens:
                        if len(token) < 2:
                            continue
                        lower = turkish_lowercase(token)
                        if not _TURKISH_WORD_RE.match(lower):
                            continue
                        total_counts[lower] += 1
                        if token[0].isupper():
                            capitalized_counts[lower] += 1
                    processed_docs += 1
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Warning: Error reading shard {file_path}: {e}")
            continue

    print(f"Finished processing {processed_docs:,} documents. Total unique tokens: {len(total_counts):,}", flush=True)

    # --- Identify proper names (capitalized >70% of the time, count >= 3) ---
    proper_names = set()
    for w, count in total_counts.items():
        if count >= 3:
            cap_ratio = capitalized_counts.get(w, 0) / count
            if cap_ratio > 0.70:
                proper_names.add(w)
    print(f"Identified {len(proper_names):,} probable proper names (filtered out).", flush=True)

    # --- Filter candidates ---
    candidates = []
    for word, freq in total_counts.most_common():
        if freq < min_freq:
            break  # most_common is sorted descending, so we can stop early
        if word in english_words:
            continue
        if word in proper_names:
            continue
        if word in root_words:
            continue
        candidates.append((word, freq))

    print(f"Candidates after filtering (freq >= {min_freq}): {len(candidates):,}", flush=True)

    # --- Hunspell verification (filter out words already accepted by dictionary) ---
    candidate_words = [w for w, _ in candidates]
    print(f"Running Hunspell verification on {len(candidate_words):,} candidate words...", flush=True)
    unrecognized = hunspell_check(candidate_words)
    print(f"Hunspell rejects {len(unrecognized):,} of {len(candidate_words):,} candidates.", flush=True)

    # --- Save results ---
    output_file = "oscar_undetected_words.txt"
    missing_count = 0
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Word\tFrequency\n")
        for word, freq in candidates:
            if word in unrecognized:
                f.write(f"{word}\t{freq}\n")
                missing_count += 1

    print(f"Saved {missing_count:,} undetected candidates to {output_file}")

    # Also save the full frequency list for reference
    full_output = "oscar_full_vocab.txt"
    with open(full_output, 'w', encoding='utf-8') as f:
        f.write("Word\tFrequency\n")
        for word, freq in total_counts.most_common():
            if freq >= min_freq:
                f.write(f"{word}\t{freq}\n")
    print(f"Saved full vocabulary (freq >= {min_freq}) to {full_output}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract Turkish vocabulary from OSCAR corpus")
    parser.add_argument('--limit', type=int, default=100000,
                        help='Maximum number of documents to process (default: 100000)')
    parser.add_argument('--min-freq', type=int, default=5,
                        help='Minimum frequency threshold for candidates (default: 5)')
    parser.add_argument('--hf-token', type=str, default=None,
                        help='Hugging Face API token (required for gated datasets like OSCAR-2301)')
    args = parser.parse_args()

    extract_vocab(limit=args.limit, min_freq=args.min_freq, hf_token=args.hf_token)
