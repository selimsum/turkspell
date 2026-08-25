import os
import time
import subprocess
from tqdm import tqdm

import sys

def main():
    dict_path = "../../tr.dic"
    aff_path = "../../tr.aff"
    
    if not os.path.exists(dict_path) or not os.path.exists(aff_path):
        print("Dictionary files not found. Please compile the hunspell dictionary first.")
        return
        
    freq_file = sys.argv[1] if len(sys.argv) > 1 else "data/ts_timeline_frequencies.txt"
    if not os.path.exists(freq_file):
        print(f"Frequency file not found at {freq_file}. Please run the corpus extraction first.")
        return
        
    print(f"Loading word frequencies from {freq_file}...")
    words = []
    total_occurrences = 0
    with open(freq_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                word, count = parts[0], int(parts[1])
                words.append((word, count))
                total_occurrences += count
                
    print(f"Loaded {len(words):,} unique words ({total_occurrences:,.0f} total occurrences).")
    
    # Run hunspell check via subprocess
    # Create a temporary file with all words
    with open("data/test_words.txt", "w", encoding="utf-8") as f:
        for word, _ in words:
            f.write(f"{word}\n")

    # Run hunspell in a single streaming process for ultra-fast execution
    start_time = time.time()
    misspelled_file = "data/raw_misspelled.txt"
    try:
        with open(misspelled_file, "w", encoding="utf-8") as out_f:
            subprocess.run(
                ["hunspell", "-d", "../../tr", "-l", "data/test_words.txt"], 
                stdout=out_f,
                check=True
            )
        
        misspelled = set()
        with open(misspelled_file, "r", encoding="utf-8") as in_f:
            for l in in_f:
                l = l.strip()
                if l:
                    misspelled.add(l)
    except FileNotFoundError:
        print("\nERROR: 'hunspell' binary not found. Please install hunspell (e.g. apt-get install hunspell).")
        return
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Hunspell failed with code {e.returncode}: {e.stderr}")
        return
        
    elapsed = time.time() - start_time
    print(f"Check completed in {elapsed:.2f} seconds ({len(words)/elapsed:,.0f} words/sec).")
    
    # Calculate coverage
    correct_unique = len(words) - len(misspelled)
    
    correct_occurrences = 0
    for word, count in words:
        if word not in misspelled:
            correct_occurrences += count
            
    print("\n--- BENCHMARK RESULTS ---")
    print(f"Unique Word Hit Rate: {correct_unique:,} / {len(words):,} ({correct_unique/len(words):.2%})")
    print(f"Total Occurrence Hit Rate: {correct_occurrences:,} / {total_occurrences:,} ({correct_occurrences/total_occurrences:.2%})")
    
    print("\nTop 50 Missing Words (by frequency):")
    missing_freqs = [(w, c) for w, c in words if w in misspelled]
    for w, c in missing_freqs[:50]:
        print(f"{w} ({c:,})")
        
    # Save missing words to file for analysis
    with open("data/missing_words.txt", "w", encoding="utf-8") as f:
        for w, c in missing_freqs:
            f.write(f"{w}\t{c}\n")
            
    print(f"\nSaved {len(missing_freqs):,} missing words to data/missing_words.txt")
    print("These missing words should be evaluated for the ML empirical pruning phase.")

if __name__ == "__main__":
    main()
