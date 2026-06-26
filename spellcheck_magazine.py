import re
import subprocess
import os
import sys
from collections import Counter

# Characters to strip from start/end of tokens
STRIP_CHARS = '"\'’‘“”.?!,:;*()[]{}<>«»/\\#%&+=_-–—~|`'

def turkish_lowercase(text):
    map_chars = {"I": "ı", "İ": "i"}
    for upper, lower in map_chars.items():
        text = text.replace(upper, lower)
    return text.lower()

def clean_corpus_token(token):
    # Strip punctuation from start/end
    token = token.strip(STRIP_CHARS)
    if not token:
        return None
    # If token contains any digit, discard it
    if any(c.isdigit() for c in token):
        return None
    # Check if the token contains at least one letter
    if not any(c.isalpha() for c in token):
        return None
    return token

def run_spellcheck():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    spelling_path = 'merged_dictionary_cleaned.txt'
    corpus_path = 'magazine_corpus.txt'
    dict_name = 'tr'

    # 1. Load root words from spelling dictionary
    if not os.path.exists(spelling_path):
        print(f"Error: {spelling_path} not found.")
        return
        
    print(f"Loading root words from {spelling_path}...")
    root_words = set()
    with open(spelling_path, 'r', encoding='utf-8') as f:
        for line in f:
            w = line.strip()
            if w:
                root_words.add(turkish_lowercase(w))
    print(f"Loaded {len(root_words)} root words.")

    # 2. Tokenize magazine_corpus.txt
    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return

    print(f"Reading and tokenizing {corpus_path}...")
    word_counter = Counter()
    total_tokens = 0
    
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            tokens = line.split()
            for t in tokens:
                cleaned = clean_corpus_token(t)
                if cleaned:
                    word_counter[cleaned] += 1
                    total_tokens += 1

    # Keep only words with frequency > 1
    unique_words = sorted([w for w, c in word_counter.items() if c > 1])
    print(f"Total tokens: {total_tokens}")
    print(f"Unique words with frequency > 1: {len(unique_words)}")

    # 3. Extract unique sub-words by splitting on hyphens
    sub_words_set = set()
    word_to_subwords = {}
    for word in unique_words:
        parts = [p for p in word.split('-') if p]
        word_to_subwords[word] = parts
        for p in parts:
            sub_words_set.add(p)

    sub_words_to_check = []
    sub_word_status = {}
    
    for w in sorted(list(sub_words_set)):
        lowercased_w = turkish_lowercase(w)
        if lowercased_w in root_words:
            sub_word_status[lowercased_w] = True
        else:
            sub_words_to_check.append(lowercased_w)

    print(f"Unique sub-words total: {len(sub_words_set)}")
    print(f"Sub-words skipped (in root list): {len(sub_words_set) - len(sub_words_to_check)}")
    print(f"Sub-words to check with Hunspell: {len(sub_words_to_check)}")

    # 4. Spellcheck using hunspell -l
    temp_input_path = 'temp_subwords_mag.txt'
    temp_output_path = 'temp_results_mag.txt'
    
    print("Writing sub-words to check...")
    with open(temp_input_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sub_words_to_check) + '\n')

    print("Running Hunspell on sub-words...")
    with open(temp_input_path, 'r', encoding='utf-8') as fin, \
         open(temp_output_path, 'w', encoding='utf-8') as fout:
        subprocess.run(['hunspell', '-d', dict_name, '-l'], stdin=fin, stdout=fout)

    # All default to correct
    for word in sub_words_to_check:
        sub_word_status[word] = True

    # Read undetected sub-words
    with open(temp_output_path, 'r', encoding='utf-8') as f:
        for line in f:
            undetected_w = line.strip()
            if undetected_w:
                sub_word_status[turkish_lowercase(undetected_w)] = False

    # Clean up temp files
    for path in [temp_input_path, temp_output_path]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Warning: Could not remove {path}: {e}")

    # 5. Collect undetected words with frequency > 1
    undetected_words = []
    for word in unique_words:
        freq = word_counter[word]
        parts = word_to_subwords[word]
        is_correct = all(sub_word_status.get(turkish_lowercase(p), False) for p in parts)
        
        if not is_correct:
            # Check if this word (lowercased) is in our root list
            lowercased_word = turkish_lowercase(word)
            clean_for_root = re.sub(r'[\'’].*', '', lowercased_word)
            in_root = (lowercased_word in root_words) or (clean_for_root in root_words)
            
            undetected_words.append((word, freq, in_root))

    # Sort by frequency descending, then alphabetically
    undetected_words.sort(key=lambda x: (-x[1], x[0]))

    output_report_path = 'undetected_words.txt'
    print(f"\nFound {len(undetected_words)} undetected words with frequency > 1.")
    print(f"Saving report to {output_report_path}...")
    
    with open(output_report_path, 'w', encoding='utf-8') as f:
        f.write("Word\tFrequency\tInRootWordList\n")
        for word, freq, in_root in undetected_words:
            f.write(f"{word}\t{freq}\t{in_root}\n")

    print("\nTop 50 Undetected Words by Frequency:")
    print("=" * 65)
    print(f"{'No':<4} | {'Word':<25} | {'Frequency':<10} | {'In Root List':<12}")
    print("-" * 65)
    for idx, (word, freq, in_root) in enumerate(undetected_words[:50], 1):
        print(f"{idx:<4} | {word:<25} | {freq:<10} | {str(in_root):<12}")

if __name__ == '__main__':
    run_spellcheck()
