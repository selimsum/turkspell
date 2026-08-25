import os
import sys
import subprocess
import time
from collections import Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def _tlc(s):
    return s.replace('I', 'ı').replace('İ', 'i').lower()

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, 'raw_data')
    
    # 1. Load Authority Set (TDK + Dil Dernegi)
    authority_set = set()
    for fname in ['tdk_words.txt', 'dil_dernegi_words.txt']:
        fpath = os.path.join(raw_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, encoding='utf-8') as f:
                for line in f:
                    w = line.strip()
                    if w:
                        authority_set.add(_tlc(w))
                        
    print(f"Loaded {len(authority_set):,} authority roots (TDK + Dil Dernegi).", flush=True)
    
    # 2. Parse arguments
    limit = 100000
    freq_file = os.path.join(base_dir, 'scripts', 'phase1', 'data', 'ts_timeline_frequencies.txt')
    for arg in sys.argv[1:]:
        if arg.isdigit():
            limit = int(arg)
        elif os.path.exists(arg):
            freq_file = arg
            
    print(f"Loading top {limit:,} words from {freq_file}...", flush=True)
    word_freqs = {}
    with open(freq_file, encoding='utf-8') as f:
        for line in f:
            if len(word_freqs) >= limit:
                break
            parts = line.strip().split('\t')
            if parts:
                w = parts[0]
                cnt = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                word_freqs[w] = word_freqs.get(w, 0) + cnt
                
    word_list = list(word_freqs.keys())
    print(f"Loaded {len(word_list):,} unique words.", flush=True)
    
    # 3. Check words with Hunspell in chunks
    print("Checking words with Hunspell binary in chunks...", flush=True)
    start_t = time.time()
    misspelled_set = set()
    chunk_size = 25000
    dict_arg = os.path.join(base_dir, 'tr')
    
    for i in range(0, len(word_list), chunk_size):
        chunk = word_list[i:i+chunk_size]
        proc = subprocess.run(
            ['hunspell', '-d', dict_arg, '-l'],
            input="\n".join(chunk) + "\n",
            text=True,
            capture_output=True,
            encoding='utf-8'
        )
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line:
                misspelled_set.add(line)
        print(f"  Processed {min(i+chunk_size, len(word_list)):,}/{len(word_list):,} words... ({len(misspelled_set):,} unrecognized)", flush=True)
        
    print(f"Hunspell check completed in {time.time() - start_t:.2f}s.", flush=True)
    print(f"Total unrecognized words: {len(misspelled_set):,} / {len(word_list):,}", flush=True)
    
    # 4. Dissect unrecognized words against TDK + Dil Dernegi
    missing_affix_chains = Counter()
    missing_examples = {}
    with_auth_root = 0
    voicing_rev = {'b': 'p', 'c': 'ç', 'd': 't', 'ğ': 'k'}
    
    for word in misspelled_set:
        count = word_freqs.get(word, 1)
        w_lower = _tlc(word)
        
        matched_root = None
        matched_suffix = None
        
        for idx in range(len(w_lower) - 1, 1, -1):
            prefix = w_lower[:idx]
            suffix = w_lower[idx:]
            if prefix in authority_set:
                matched_root = prefix
                matched_suffix = suffix
                break
            if prefix and prefix[-1] in voicing_rev:
                unv = prefix[:-1] + voicing_rev[prefix[-1]]
                if unv in authority_set:
                    matched_root = unv
                    matched_suffix = suffix
                    break
                    
        if matched_root and matched_suffix:
            with_auth_root += 1
            missing_affix_chains[matched_suffix] += count
            if matched_suffix not in missing_examples:
                missing_examples[matched_suffix] = []
            if len(missing_examples[matched_suffix]) < 3:
                missing_examples[matched_suffix].append(f"{matched_root}+{matched_suffix} ({word})")
                
    print(f"\nUnrecognized words with valid TDK/DD Root: {with_auth_root:,} ({with_auth_root/max(1, len(misspelled_set)):.1%})", flush=True)
    print("\nTop 30 Missing Suffix Chains (by corpus frequency):", flush=True)
    for suffix, freq in missing_affix_chains.most_common(30):
        examples = ", ".join(missing_examples.get(suffix, []))
        print(f"  -{suffix} (frequency: {freq:,}) -> Examples: {examples}", flush=True)

if __name__ == '__main__':
    main()
