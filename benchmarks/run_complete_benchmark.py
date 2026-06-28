import os
import sys
import csv
import time
import subprocess
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Force UTF-8 output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = Path(__file__).parent.parent
DATA_DIR = BASE / 'data'

TEST_SETS = {
    'V1 Official Test': DATA_DIR / 'official_test_fixed.csv',
    'V2 Official Test': DATA_DIR / 'official_test_v2_fixed.csv'
}

DICTIONARIES = {
    'Turkspell':         str(BASE / 'tr'),
    'tdd-ai/hunspell-tr': str(BASE / 'external_dictionaries' / 'tdd-ai' / 'tr_TR'),
    'harunzafer':        str(BASE / 'external_dictionaries' / 'harunzafer' / 'tr_TR'),
    'selimsum':          str(BASE / 'external_dictionaries' / 'selimsum' / 'tr'),
    'vdemir':            str(BASE / 'external_dictionaries' / 'vdemir' / 'tr_TR'),
}

SEED = 42
SAMPLE_SIZE = 1000  # Number of misspelled words to sample for suggestion/correction accuracy

# Check which dictionaries are actually available
AVAILABLE_DICTS = {}
for name, dic_base in DICTIONARIES.items():
    aff = Path(dic_base + '.aff')
    dic = Path(dic_base + '.dic')
    if aff.exists() and dic.exists():
        AVAILABLE_DICTS[name] = dic_base
    else:
        print(f"Skipping {name} (files not found: {dic_base}.aff/.dic)")

def load_test_set(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        first_line = f.readline()
        f.seek(0)
        if 'gold' in first_line or 'input' in first_line:
            reader = csv.DictReader(f)
            rows = list(reader)
        else:
            reader = csv.reader(f)
            for parts in reader:
                if len(parts) >= 2:
                    rows.append({'gold': parts[0].strip(), 'input': parts[1].strip()})
    return rows

def hspell_l(words, dic, timeout=120):
    """Run hunspell -l on words list and return a set of unrecognized words."""
    if not words:
        return set()
    result = subprocess.run(
        ['hunspell', '-d', dic, '-l'],
        input='\n'.join(words) + '\n',
        capture_output=True, text=True, encoding='utf-8', timeout=timeout
    )
    return {w.strip() for w in result.stdout.split('\n') if w.strip()}

def hspell_chunk_a(words, dic, timeout=180):
    """Run hunspell -a on a chunk of words and return suggestion mapping."""
    if not words:
        return {}
    result = subprocess.run(
        ['hunspell', '-d', dic, '-a'],
        input='\n'.join(words) + '\n',
        capture_output=True, text=True, encoding='utf-8', timeout=timeout
    )
    sugs = {}
    word_iter = iter(words)
    for line in result.stdout.split('\n'):
        ls = line.strip()
        if not ls or ls.startswith('@'):
            continue
        if ls[0] in ('*', '+', '-'):
            w = next(word_iter, None)
            if w: sugs[w] = []
        elif ls.startswith('&'):
            c = ls.find(':')
            sug_list = [s.strip() for s in ls[c+1:].split(',') if s.strip()] if c >= 0 else []
            w = next(word_iter, None)
            if w: sugs[w] = sug_list
        elif ls.startswith('#'):
            w = next(word_iter, None)
            if w: sugs[w] = None
    return sugs

def run_suggestions_parallel(words, dic, chunk_size=50, max_workers=12):
    """Run suggestions in parallel with smaller chunk size and higher thread limit to prevent timeouts."""
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(hspell_chunk_a, chunk, dic): chunk for chunk in chunks}
        for future in futures:
            try:
                chunk_res = future.result()
                results.update(chunk_res)
            except Exception as e:
                print(f"  Warning: Suggestion chunk timed out or failed: {e}")
                
    return results

def calculate_metrics(true_labels, predicted_labels):
    tp = sum(1 for t, p in zip(true_labels, predicted_labels) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(true_labels, predicted_labels) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(true_labels, predicted_labels) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(true_labels, predicted_labels) if t == 0 and p == 0)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return precision, recall, f1

def benchmark_dict_on_set(dic_base, rows):
    inputs = [r['input'] for r in rows]
    golds = [r['gold'] for r in rows]
    
    # 1. Detection on ALL words (extremely fast using hunspell -l)
    t_det_start = time.time()
    unrecognized = hspell_l(inputs, dic_base)
    t_det = time.time() - t_det_start
    
    true_labels = []
    predicted_labels = []
    misspelled_pairs = []
    
    for inp, gold in zip(inputs, golds):
        is_misspelled = (inp != gold)
        if is_misspelled:
            true_labels.append(1)
            misspelled_pairs.append((inp, gold))
        else:
            true_labels.append(0)
            
        # speller flags as misspelled (1) if it's in the unrecognized set
        is_flagged = 1 if inp in unrecognized else 0
        predicted_labels.append(is_flagged)
        
    precision, recall, f1 = calculate_metrics(true_labels, predicted_labels)
    
    # 2. Correction accuracy on a sample of misspelled words
    # Filter to actual misspelled words
    rng = random.Random(SEED)
    sample_pairs = rng.sample(misspelled_pairs, min(SAMPLE_SIZE, len(misspelled_pairs)))
    sample_inputs = [p[0] for p in sample_pairs]
    
    t_sug_start = time.time()
    sugs_map = run_suggestions_parallel(sample_inputs, dic_base, chunk_size=50, max_workers=12)
    t_sug = time.time() - t_sug_start
    
    accurate = 0
    evaluated = 0
    for inp, gold in sample_pairs:
        sugs = sugs_map.get(inp)
        if sugs is not None:
            evaluated += 1
            if gold in sugs:
                accurate += 1
                
    corr_acc = (accurate / evaluated) if evaluated > 0 else 0.0
    
    return {
        'precision': precision * 100,
        'recall': recall * 100,
        'f1': f1 * 100,
        'corr_acc': corr_acc * 100,
        't_detection': t_det,
        't_suggestion': t_sug
    }

def main():
    print("Available dictionaries:", list(AVAILABLE_DICTS.keys()))
    print("Test sets:", list(TEST_SETS.keys()))
    print(f"Sampling {SAMPLE_SIZE} misspelled words for correction accuracy evaluation (seed={SEED}).")
    
    all_results = {}
    
    for set_name, set_path in TEST_SETS.items():
        if not set_path.exists():
            print(f"Skipping {set_name} (file {set_path} not found)")
            continue
            
        print(f"\nEvaluating on {set_name}...")
        rows = load_test_set(set_path)
        print(f"Loaded {len(rows)} test pairs.")
        
        all_results[set_name] = {}
        
        for dict_name, dic_base in AVAILABLE_DICTS.items():
            t0 = time.time()
            metrics = benchmark_dict_on_set(dic_base, rows)
            elapsed = time.time() - t0
            print(f"  {dict_name:20} done in {elapsed:5.1f}s (det: {metrics['t_detection']:.1f}s, sug: {metrics['t_suggestion']:.1f}s) | Prec: {metrics['precision']:.2f}% | Rec: {metrics['recall']:.2f}% | F1: {metrics['f1']:.2f}% | Corr Acc: {metrics['corr_acc']:.2f}%")
            all_results[set_name][dict_name] = metrics

    # Format and print final comparison tables
    for set_name, results in all_results.items():
        print("\n" + "=" * 90)
        print(f"RESULTS FOR {set_name.upper()}")
        print("=" * 90)
        print(f"{'Dictionary':<25} | {'Detection Prec (%)':<20} | {'Detection Rec (%)':<20} | {'Detection F1 (%)':<18} | {'Correction Acc (%)':<20}")
        print("-" * 111)
        for dict_name, metrics in results.items():
            print(f"{dict_name:<25} | {metrics['precision']:<20.2f} | {metrics['recall']:<20.2f} | {metrics['f1']:<18.2f} | {metrics['corr_acc']:<20.2f}")
        print("=" * 90)

if __name__ == '__main__':
    main()
