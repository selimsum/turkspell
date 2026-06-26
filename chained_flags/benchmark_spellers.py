import re
import subprocess
import os
import sys
import time
from collections import Counter

# Characters to strip from start/end of tokens
STRIP_CHARS = '"\'’‘“”.?!,:;*()[]{}<>«»/\\#%&+=_-–—~|`'

def turkish_lowercase(text):
    map_chars = {"I": "ı", "İ": "i"}
    for upper, lower in map_chars.items():
        text = text.replace(upper, lower)
    return text.lower()

def clean_corpus_token(token):
    token = token.strip(STRIP_CHARS)
    if not token:
        return None
    if any(c.isdigit() for c in token):
        return None
    if not any(c.isalpha() for c in token):
        return None
    return token

def get_file_size_mb(path):
    if os.path.exists(path):
        return os.path.getsize(path) / (1024 * 1024)
    return 0.0

def run_hunspell_for_dict(dict_path, sub_words_to_check, unique_words, word_counter, word_to_subwords):
    temp_input_path = f'temp_subwords_{os.path.basename(dict_path)}.txt'
    temp_output_path = f'temp_results_{os.path.basename(dict_path)}.txt'

    with open(temp_input_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sub_words_to_check) + '\n')

    start_time = time.time()
    with open(temp_input_path, 'r', encoding='utf-8') as fin, \
         open(temp_output_path, 'w', encoding='utf-8') as fout:
        subprocess.run(['hunspell', '-d', dict_path, '-l'], stdin=fin, stdout=fout)
    duration = time.time() - start_time

    undetected_subwords = set()
    with open(temp_output_path, 'r', encoding='utf-8') as f:
        for line in f:
            undetected_w = line.strip()
            if undetected_w:
                undetected_subwords.add(undetected_w)

    for path in [temp_input_path, temp_output_path]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Warning: Could not remove {path}: {e}")

    all_undetected = []
    freq_gt1_undetected = []

    for word in unique_words:
        freq = word_counter[word]
        parts = word_to_subwords[word]
        is_correct = all(p not in undetected_subwords for p in parts)

        if not is_correct:
            all_undetected.append((word, freq))
            if freq > 1:
                freq_gt1_undetected.append((word, freq))

    return duration, all_undetected, freq_gt1_undetected

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    corpus_path = 'magazine_corpus.txt'
    if not os.path.exists(corpus_path):
        corpus_path = '../magazine_corpus.txt'
        
    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return

    print(f"Tokenizing {corpus_path}...")
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

    unique_words = sorted(list(word_counter.keys()))
    print(f"Total tokens: {total_tokens}")
    print(f"Total unique words: {len(unique_words)}")
    
    unique_words_gt1 = [w for w, c in word_counter.items() if c > 1]
    print(f"Unique words with freq > 1: {len(unique_words_gt1)}")

    sub_words_set = set()
    word_to_subwords = {}
    for word in unique_words:
        parts = [p for p in word.split('-') if p]
        word_to_subwords[word] = parts
        for p in parts:
            sub_words_set.add(p)

    sub_words_to_check = sorted(list(sub_words_set))
    print(f"Total unique sub-words to check: {len(sub_words_to_check)}")

    spellers = {
        "Turkspell (Baseline)": "c:\\gemini\\turkspell\\tr",
        "Turkspell (Chained)": "c:\\gemini\\turkspell\\chained_flags\\tr"
    }

    # Only include other spellers if they exist to keep the benchmark run clean
    possible_spellers = {
        "TDD (hunspell-tr)": "C:\\gemini\\hunspell-tr\\tr",
        "hunspell-tr-moz": "C:\\gemini\\hunspell-tr-moz\\tr"
    }
    for name, path in possible_spellers.items():
        if os.path.exists(path + ".aff"):
            spellers[name] = path

    results = {}

    for name, path in spellers.items():
        print(f"\nEvaluating {name}...")
        
        aff_size = get_file_size_mb(path + ".aff")
        dic_size = get_file_size_mb(path + ".dic")
        
        duration, all_undetected, freq_gt1_undetected = run_hunspell_for_dict(
            path, sub_words_to_check, unique_words, word_counter, word_to_subwords
        )
        
        results[name] = {
            "aff_size_mb": aff_size,
            "dic_size_mb": dic_size,
            "duration_sec": duration,
            "all_undetected_count": len(all_undetected),
            "all_correct_count": len(unique_words) - len(all_undetected),
            "freq_gt1_undetected_count": len(freq_gt1_undetected),
            "freq_gt1_correct_count": len(unique_words_gt1) - len(freq_gt1_undetected),
            "all_undetected": all_undetected,
            "freq_gt1_undetected": freq_gt1_undetected
        }
        
        print(f"  Affix file size: {aff_size:.2f} MB")
        print(f"  Dictionary file size: {dic_size:.2f} MB")
        print(f"  Total file size: {aff_size + dic_size:.2f} MB")
        print(f"  Time taken: {duration:.2f} seconds")
        print(f"  All Unique Words: Correct: {results[name]['all_correct_count']} ({results[name]['all_correct_count']/len(unique_words)*100:.2f}%), Undetected: {len(all_undetected)} ({len(all_undetected)/len(unique_words)*100:.2f}%)")
        print(f"  Freq > 1 Words:   Correct: {results[name]['freq_gt1_correct_count']} ({results[name]['freq_gt1_correct_count']/len(unique_words_gt1)*100:.2f}%), Undetected: {len(freq_gt1_undetected)} ({len(freq_gt1_undetected)/len(unique_words_gt1)*100:.2f}%)")

    print("\n" + "="*40 + " COMPARISON REPORT " + "="*40)
    print(f"{'Speller Name':<25} | {'Aff Size (MB)':<13} | {'Dic Size (MB)':<13} | {'Total Size (MB)':<15} | {'All Correct %':<15} | {'Freq>1 Correct %':<17} | {'Time (s)':<8}")
    print("-"*120)
    for name, r in results.items():
        total_size = r['aff_size_mb'] + r['dic_size_mb']
        all_correct_pct = r['all_correct_count'] / len(unique_words) * 100
        freq_gt1_correct_pct = r['freq_gt1_correct_count'] / len(unique_words_gt1) * 100
        print(f"{name:<25} | {r['aff_size_mb']:<13.2f} | {r['dic_size_mb']:<13.2f} | {total_size:<15.2f} | {all_correct_pct:<15.2f} | {freq_gt1_correct_pct:<17.2f} | {r['duration_sec']:<8.2f}")

    for name, r in results.items():
        safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        out_file = f"undetected_words_{safe_name}.txt"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write("Word\tFrequency\n")
            sorted_undetected = sorted(r['freq_gt1_undetected'], key=lambda x: (-x[1], x[0]))
            for word, freq in sorted_undetected:
                f.write(f"{word}\t{freq}\n")
        print(f"Saved undetected list with freq > 1 for {name} to {out_file}")

if __name__ == '__main__':
    main()
