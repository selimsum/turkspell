import re
import os
import sys
import time
import subprocess
from collections import Counter
import math
import concurrent.futures
import multiprocessing

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
        
    # Replace curly apostrophe with straight apostrophe
    token = token.replace("’", "'").replace("‘", "'")
    
    # If token contains any digit, discard it
    if any(c.isdigit() for c in token):
        return None
        
    # Check if the token contains at least one letter
    if not any(c.isalpha() for c in token):
        return None
        
    # Discard Roman numerals
    roman_numerals = {
        "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", 
        "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx"
    }
    if token.lower() in roman_numerals:
        return None
        
    return token

def get_file_size_mb(path):
    if os.path.exists(path):
        return os.path.getsize(path) / (1024 * 1024)
    return 0.0

def run_hunspell_for_dict(dict_path, sub_words_to_check, unique_words, word_counter, word_to_subwords, mode_label):
    safe_basename = os.path.basename(dict_path)
    temp_input_path = f'temp_subwords_{safe_basename}_{mode_label}.txt'
    temp_output_path = f'temp_results_{safe_basename}_{mode_label}.txt'

    # Write sub-words to check
    with open(temp_input_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sub_words_to_check) + '\n')

    # Run Hunspell
    start_time = time.time()
    with open(temp_input_path, 'r', encoding='utf-8') as fin, \
         open(temp_output_path, 'w', encoding='utf-8') as fout:
        subprocess.run(['hunspell', '-d', dict_path, '-l'], stdin=fin, stdout=fout)
    duration = time.time() - start_time

    # Read undetected sub-words
    undetected_subwords = set()
    with open(temp_output_path, 'r', encoding='utf-8') as f:
        for line in f:
            undetected_w = line.strip()
            if undetected_w:
                undetected_w = undetected_w.replace("’", "'").replace("‘", "'")
                undetected_subwords.add(undetected_w)

    # Clean up temp files
    for path in [temp_input_path, temp_output_path]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            pass

    # Evaluate all unique words
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

def benchmark_spelling_mode(corpus_words, spellers, mode_label):
    print(f"\n--- Running Spelling Benchmark ({mode_label}) ---")
    word_counter = Counter(corpus_words)
    unique_words = sorted(list(word_counter.keys()))
    unique_words_gt1 = [w for w, c in word_counter.items() if c > 1]
    
    print(f"  Total tokens: {len(corpus_words)}")
    print(f"  Total unique words: {len(unique_words)}")
    print(f"  Unique words with freq > 1: {len(unique_words_gt1)}")

    sub_words_set = set()
    word_to_subwords = {}
    for word in unique_words:
        parts = [p for p in word.split('-') if p]
        word_to_subwords[word] = parts
        for p in parts:
            sub_words_set.add(p)

    sub_words_to_check = sorted(list(sub_words_set))
    print(f"  Total unique sub-words to check: {len(sub_words_to_check)}")

    results = {}
    for name, path in spellers.items():
        print(f"  Evaluating {name}...")
        
        aff_size = get_file_size_mb(path + ".aff")
        dic_size = get_file_size_mb(path + ".dic")
        
        duration, all_undetected, freq_gt1_undetected = run_hunspell_for_dict(
            path, sub_words_to_check, unique_words, word_counter, word_to_subwords, mode_label
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
        
        # Save undetected lists
        safe_name = name.lower().replace("/", "_").replace("-", "_")
        out_file = f"undetected_words_{mode_label}_{safe_name}.txt"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write("Word\tFrequency\n")
            sorted_undetected = sorted(freq_gt1_undetected, key=lambda x: (-x[1], x[0]))
            for w, freq in sorted_undetected:
                f.write(f"{w}\t{freq}\n")
                
    return results, len(unique_words), len(unique_words_gt1)

def run_correction_chunk(dict_path, pairs_chunk, worker_id, mode_label, filename_suffix):
    safe_basename = os.path.basename(dict_path)
    temp_input_path = f'temp_corr_input_{safe_basename}_{mode_label}{filename_suffix}_{worker_id}.txt'
    temp_output_path = f'temp_corr_output_{safe_basename}_{mode_label}{filename_suffix}_{worker_id}.txt'
    
    inputs = [p[1] for p in pairs_chunk]
    with open(temp_input_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(inputs) + '\n')
        
    with open(temp_input_path, 'r', encoding='utf-8') as fin, \
         open(temp_output_path, 'w', encoding='utf-8') as fout:
        subprocess.run(['hunspell', '-a', '-d', dict_path], stdin=fin, stdout=fout)
        
    with open(temp_output_path, 'r', encoding='utf-8') as f:
        output_content = f.read()
        
    for path in [temp_input_path, temp_output_path]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
            
    raw_blocks = output_content.split('\n\n')
    if raw_blocks and raw_blocks[0].startswith('@(#)'):
        lines = raw_blocks[0].splitlines()
        if len(lines) > 1:
            raw_blocks[0] = '\n'.join(lines[1:])
        else:
            raw_blocks.pop(0)
            
    blocks = [b.strip() for b in raw_blocks if b.strip()]
    total_eval = min(len(pairs_chunk), len(blocks))
    
    top1_hits = 0
    top5_hits = 0
    top10_hits = 0
    mrr_sum = 0.0
    detection_rate = 0
    suggestions_rate = 0
    
    for i in range(total_eval):
        gold_word = pairs_chunk[i][0]
        block = blocks[i]
        
        is_incorrect = False
        sugs = []
        for line in block.splitlines():
            line = line.strip()
            if line.startswith('&'):
                is_incorrect = True
                parts = line.split(':', 1)
                if len(parts) == 2:
                    sugs = [s.strip() for s in parts[1].split(',')]
            elif line.startswith('#'):
                is_incorrect = True
                
        if is_incorrect:
            detection_rate += 1
            if sugs:
                suggestions_rate += 1
                gold_norm = gold_word.replace("’", "'").replace("‘", "'")
                sugs_norm = [s.replace("’", "'").replace("‘", "'") for s in sugs]
                
                if gold_norm in sugs_norm:
                    rank = sugs_norm.index(gold_norm) + 1
                    if rank == 1:
                        top1_hits += 1
                    if rank <= 5:
                        top5_hits += 1
                    if rank <= 10:
                        top10_hits += 1
                    mrr_sum += 1.0 / rank
                    
    return {
        "top1_hits": top1_hits,
        "top5_hits": top5_hits,
        "top10_hits": top10_hits,
        "mrr_sum": mrr_sum,
        "detection_rate": detection_rate,
        "suggestions_rate": suggestions_rate,
        "total_eval": total_eval
    }

def run_correction_benchmark(dict_path, pairs, mode_label, filename_suffix=""):
    num_cores = multiprocessing.cpu_count()
    num_workers = min(num_cores, 8)
    
    # Split pairs into chunks
    chunk_size = math.ceil(len(pairs) / num_workers)
    chunks = [pairs[i:i + chunk_size] for i in range(0, len(pairs), chunk_size)]
    
    start_time = time.time()
    
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, chunk in enumerate(chunks):
            futures.append(executor.submit(run_correction_chunk, dict_path, chunk, i, mode_label, filename_suffix))
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    duration = time.time() - start_time
    
    total_eval = sum(r["total_eval"] for r in results)
    top1_hits = sum(r["top1_hits"] for r in results)
    top5_hits = sum(r["top5_hits"] for r in results)
    top10_hits = sum(r["top10_hits"] for r in results)
    mrr_sum = sum(r["mrr_sum"] for r in results)
    detection_rate = sum(r["detection_rate"] for r in results)
    suggestions_rate = sum(r["suggestions_rate"] for r in results)
    
    accuracy_top1 = (top1_hits / total_eval) * 100 if total_eval > 0 else 0.0
    accuracy_top5 = (top5_hits / total_eval) * 100 if total_eval > 0 else 0.0
    accuracy_top10 = (top10_hits / total_eval) * 100 if total_eval > 0 else 0.0
    mrr = (mrr_sum / total_eval) * 100 if total_eval > 0 else 0.0
    det_pct = (detection_rate / total_eval) * 100 if total_eval > 0 else 0.0
    sug_pct = (suggestions_rate / total_eval) * 100 if total_eval > 0 else 0.0
    
    return duration, accuracy_top1, accuracy_top5, accuracy_top10, mrr, det_pct, sug_pct

def print_spelling_markdown_table(title, results, total_uniq, total_gt1):
    print(f"\n### {title}")
    print(f"| {'Speller Name':<28} | {'Aff (MB)':<8} | {'Dic (MB)':<8} | {'Total (MB)':<10} | {'All Correct %':<15} | {'Freq>1 Correct %':<17} | {'Time (s)':<8} |")
    print(f"|{'-'*30}|{'-'*10}|{'-'*10}|{'-'*12}|{'-'*17}|{'-'*19}|{'-'*10}|")
    for name, r in results.items():
        total_size = r['aff_size_mb'] + r['dic_size_mb']
        all_correct_pct = r['all_correct_count'] / total_uniq * 100
        freq_gt1_correct_pct = r['freq_gt1_correct_count'] / total_gt1 * 100
        print(f"| {name:<28} | {r['aff_size_mb']:<8.2f} | {r['dic_size_mb']:<8.2f} | {total_size:<10.2f} | {all_correct_pct:<15.2f} | {freq_gt1_correct_pct:<17.2f} | {r['duration_sec']:<8.2f} |")

def print_correction_markdown_table(title, results):
    print(f"\n### {title}")
    print(f"| {'Speller Name':<28} | {'Top-1 Acc %':<12} | {'Top-5 Acc %':<12} | {'Top-10 Acc %':<12} | {'MRR':<8} | {'Detection %':<12} | {'Suggestion %':<13} | {'Time (s)':<8} |")
    print(f"|{'-'*30}|{'-'*14}|{'-'*14}|{'-'*14}|{'-'*10}|{'-'*14}|{'-'*15}|{'-'*10}|")
    for name, r in results.items():
        print(f"| {name:<28} | {r['top1']:<12.2f} | {r['top5']:<12.2f} | {r['top10']:<12.2f} | {r['mrr']:<8.2f} | {r['det']:<12.2f} | {r['sug']:<13.2f} | {r['time']:<8.2f} |")

def load_test_pairs(path, limit=1000):
    pairs = []
    with open(path, 'r', encoding='utf-8') as f:
        next(f) # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))
                if len(pairs) >= limit:
                    break
    return pairs

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_path = os.path.join(base_dir, 'data', 'anayasa.txt')
    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return
        
    test_set_path = os.path.join(base_dir, 'spell-checking-and-correction/evaluation/data/one_million_test_set.csv')
    test_set_fixed_path = os.path.join(base_dir, 'spell-checking-and-correction/evaluation/data/one_million_test_set_fixed.csv')
    
    if not os.path.exists(test_set_path) or not os.path.exists(test_set_fixed_path):
        print("Error: Test set CSV files are missing.")
        return

    # 1. Spelling Tokenization
    print("Tokenizing anayasa.txt...")
    raw_tokens = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            tokens = line.split()
            for t in tokens:
                cleaned = clean_corpus_token(t)
                if cleaned:
                    raw_tokens.append(cleaned)

    # 2. Load test pairs (Standard & Circumflex-Fixed)
    # Skip loading original correction test cases to save memory
    test_pairs = []
    
    print("Loading circumflex-fixed correction test cases...")
    test_pairs_fixed = load_test_pairs(test_set_fixed_path, limit=100000)

    # Dictionary configurations (renamed to GitHub Repository Names)
    spellers = {
        "Turkspell": os.path.join(base_dir, "tr"),
        "tdd-ai/hunspell-tr": os.path.join(base_dir, "external_dictionaries/tdd-ai/tr_TR"),
        "vdemir/hunspell-tr": os.path.join(base_dir, "external_dictionaries/vdemir/tr_TR"),
        "harunzafer/hunspell-tr": os.path.join(base_dir, "external_dictionaries/harunzafer/tr_TR"),
        "selimsum/hunspell-tr-moz": os.path.join(base_dir, "external_dictionaries/selimsum/tr")
    }

    # ==================== RUN SPELLING BENCHMARKS ====================
    # CASE SENSITIVE
    print("\n==================== RUNNING CASE-SENSITIVE BENCHMARKS ====================")
    spelling_sensitive, uniq_sensitive, gt1_sensitive = benchmark_spelling_mode(
        raw_tokens, spellers, "case_sensitive"
    )
    
    print("\nSkipping Original Correction Benchmark as requested...")
    corr_sensitive = {}
        
    print("\nRunning Circumflex-Fixed Correction Benchmark (case_sensitive)...")
    corr_sensitive_fixed = {}
    for name, path in spellers.items():
        print(f"  Evaluating suggestions for {name}...")
        duration, top1, top5, top10, mrr, det, sug = run_correction_benchmark(path, test_pairs_fixed, "case_sensitive", "_fixed")
        corr_sensitive_fixed[name] = {"time": duration, "top1": top1, "top5": top5, "top10": top10, "mrr": mrr, "det": det, "sug": sug}

    # CASE INSENSITIVE
    print("\n==================== RUNNING CASE-INSENSITIVE BENCHMARKS ====================")
    lowercased_tokens = [turkish_lowercase(w) for w in raw_tokens]
    spelling_insensitive, uniq_insensitive, gt1_insensitive = benchmark_spelling_mode(
        lowercased_tokens, spellers, "case_insensitive"
    )
    
    print("\nReusing Case-Sensitive Correction results for Case-Insensitive (since inputs are identical lowercase)...")
    corr_insensitive = corr_sensitive
    corr_insensitive_fixed = corr_sensitive_fixed

    # ==================== COMPARATIVE REPORTS ====================
    print("\n" + "="*50 + " FINAL BENCHMARK COMPARATIVE REPORTS " + "="*50)
    
    print("\n## SPELLING ACCURACY RESULTS (anayasa.txt)")
    print_spelling_markdown_table("Case-Sensitive Spelling Accuracy", spelling_sensitive, uniq_sensitive, gt1_sensitive)
    print_spelling_markdown_table("Case-Insensitive Spelling Accuracy", spelling_insensitive, uniq_insensitive, gt1_insensitive)
    
    print("\n## CORRECTION RESULTS - ORIGINAL TEST SET (official_test_v2.csv)")
    print_correction_markdown_table("Case-Sensitive Correction Performance (Original)", corr_sensitive)
    print_correction_markdown_table("Case-Insensitive Correction Performance (Original)", corr_insensitive)
    
    print("\n## CORRECTION RESULTS - CIRCUMFLEX-FIXED TEST SET (official_test_v2_fixed.csv)")
    print_correction_markdown_table("Case-Sensitive Correction Performance (Fixed)", corr_sensitive_fixed)
    print_correction_markdown_table("Case-Insensitive Correction Performance (Fixed)", corr_insensitive_fixed)
    
    print("\nUndetected words lists have been saved for each engine.")

if __name__ == '__main__':
    main()
