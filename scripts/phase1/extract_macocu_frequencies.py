import json
import re
import time
import os
from collections import Counter

def extract_macocu_frequencies(file_path, out_path):
    print(f"Processing 45.5GB JSONL corpus: {file_path}")
    print("This will take a while. Reading line by line to save RAM...")
    
    # Match Turkish letters AND numbers, including proper nouns/numbers with apostrophes and circumflex letters
    word_pattern = re.compile(r"[a-zA-ZçğıöşüâîûÇĞIÖŞÜÂÎÛİ0-9]+(?:'[a-zA-ZçğıöşüâîûÇĞIÖŞÜÂÎÛİ0-9]+)?")
    counter = Counter()
    
    start_time = time.time()
    total_lines = 0
    total_words = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            total_lines += 1
            try:
                data = json.loads(line)
                
                # Skip noisy genres to ensure dictionary quality
                genre = data.get('genre')
                if genre in ('Forum', 'Mix', 'Other', 'Prose/Lyrical'):
                    continue
                    
                # We extract text from both 'title' and 'text' fields
                text = (data.get('title', '') or '') + " " + (data.get('text', '') or '')
                
                # Normalize smart quotes to standard apostrophe before regex matching
                text = text.replace('’', "'").replace('‘', "'").replace('´', "'").replace('`', "'")
                
                words = word_pattern.findall(text)
                # Filter out any token that contains a digit and drop isolated apostrophes
                clean_words = [w for w in words if not any(char.isdigit() for char in w) and w != "'"]
                counter.update(clean_words)
                total_words += len(clean_words)
            except Exception as e:
                pass
                
            if total_lines % 100000 == 0:
                elapsed = time.time() - start_time
                print(f"Processed {total_lines:,} lines ({total_words:,} words)... Elapsed: {elapsed:.1f}s")
                
    elapsed = time.time() - start_time
    print(f"\nFinished parsing! Total lines: {total_lines:,}")
    print(f"Total words processed: {total_words:,}")
    print(f"Unique words found: {len(counter):,}")
    print(f"Parsing time: {elapsed:.1f}s ({total_words/elapsed:,.0f} words/sec)")
    
    print("\nFiltering words with frequency >= 2...")
    filtered_words = {k: v for k, v in counter.items() if v >= 2}
    print(f"Kept {len(filtered_words):,} unique words.")
    
    print(f"Saving frequencies to {out_path}...")
    sorted_words = sorted(filtered_words.items(), key=lambda item: item[1], reverse=True)
    
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        for word, count in sorted_words:
            f.write(f"{word}\t{count}\n")
            
    print("Done!")

if __name__ == "__main__":
    input_file = r"C:\gemini\turkspell\raw_data\MaCoCu-Genre.tr.jsonl"
    output_file = r"C:\gemini\turkspell\scripts\phase1\data\macocu_frequencies.txt"
    extract_macocu_frequencies(input_file, output_file)
