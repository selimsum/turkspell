"""
benchmark_utf8.py
=================
Verify the new tr_utf8.aff + tr_utf8.dic against tr.aff + tr.dic
to ensure identical correctness and measure actual performance/footprint.
"""
import subprocess, sys, csv, io, time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE     = Path(__file__).parent.parent
TEST_CSV = BASE / 'data' / 'official_test_v2_fixed.csv'
SAMPLE_N = 50    # words for Top-1/Top-5
SEED     = 42

DICTIONARIES = {
    'v2 (FLAG long baseline)': str(BASE / 'tr'),
    'v2 (FLAG UTF-8 new)':      str(BASE / 'tr_utf8'),
}

AVAILABLE = {}
for name, dic_base in DICTIONARIES.items():
    if Path(dic_base + '.aff').exists() and Path(dic_base + '.dic').exists():
        AVAILABLE[name] = dic_base
    else:
        print(f"  SKIP {name}: {dic_base}.aff not found")
print(f"\nDictionaries to test: {list(AVAILABLE.keys())}\n")

def hspell_l(words: list, dic: str, timeout=120) -> set:
    result = subprocess.run(
        ['hunspell', '-d', dic, '-l'],
        input='\n'.join(words) + '\n',
        capture_output=True, text=True, encoding='utf-8', timeout=timeout
    )
    return {w.strip() for w in result.stdout.split('\n') if w.strip()}

def hspell_a(words: list, dic: str, timeout=900) -> dict:
    if not words:
        return {}
    result = subprocess.run(
        ['hunspell', '-d', dic, '-a'],
        input='\n'.join(words) + '\n',
        capture_output=True, text=True, encoding='utf-8', timeout=timeout
    )
    sugs, word_iter = {}, iter(words)
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

def benchmark(dic_base: str, rows: list, name: str) -> dict:
    inputs = [r['input'] for r in rows]
    golds  = [r['gold']  for r in rows]

    # Detection on all words
    print(f"  [{name}]  Step 1/2: detection...", end=' ', flush=True)
    t0 = time.time()
    unknown = hspell_l(inputs, dic_base)
    t1 = time.time()
    print(f"{t1-t0:.1f}s  ({len(unknown)} flagged)")

    total_mis = total_cor = detected = correct_pass = 0
    mis_pairs = []
    for inp, gold in zip(inputs, golds):
        if inp != gold:
            total_mis += 1
            if inp in unknown:
                detected += 1
                mis_pairs.append((inp, gold))
        else:
            total_cor += 1
            if inp not in unknown:
                correct_pass += 1

    recall = (detected / total_mis * 100) if total_mis else 0
    precision = (correct_pass / total_cor * 100) if total_cor else 0

    # Suggestions on sample
    import random
    random.seed(SEED)
    sample_pairs = [p for p in mis_pairs if p[0] in unknown]
    if len(sample_pairs) > SAMPLE_N:
        sample_pairs = random.sample(sample_pairs, SAMPLE_N)

    sample_inputs = [p[0] for p in sample_pairs]
    sample_golds  = [p[1] for p in sample_pairs]

    print(f"  [{name}]  Step 2/2: suggestions...", end=' ', flush=True)
    t0 = time.time()
    try:
        sugs_map = hspell_a(sample_inputs, dic_base, timeout=120)
        t1 = time.time()
        print(f"{t1-t0:.1f}s")
    except subprocess.TimeoutExpired:
        print("Timeout!")
        sugs_map = None

    top1_correct = top5_correct = evaluated = 0
    if sugs_map:
        for inp, gold in zip(sample_inputs, sample_golds):
            sugs = sugs_map.get(inp)
            if sugs is None:
                continue
            evaluated += 1
            if sugs and sugs[0] == gold:
                top1_correct += 1
            if sugs and gold in sugs[:5]:
                top5_correct += 1

    top1 = (top1_correct / evaluated * 100) if evaluated else float('nan')
    top5 = (top5_correct / evaluated * 100) if evaluated else float('nan')

    return {
        'top1': top1,
        'top5': top5,
        'recall': recall,
        'precision': precision,
        'flagged': len(unknown)
    }

def main():
    if not TEST_CSV.exists():
        print(f"Error: {TEST_CSV} not found.")
        return

    print(f"Loading {TEST_CSV}...")
    rows = []
    with open(TEST_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    print(f"Loaded {len(rows)} test pairs.")

    results = {}
    for name, dic_base in AVAILABLE.items():
        res = benchmark(dic_base, rows, name)
        results[name] = res

    print("\n" + "="*80)
    print("VERIFICATION RESULTS")
    print("="*80)
    print(f"{'Metric':<25} {'Baseline (long)':<25} {'New (UTF-8)':<25}")
    print("-"*80)
    
    baseline = results.get('v2 (FLAG long baseline)')
    new_utf8 = results.get('v2 (FLAG UTF-8 new)')
    
    if baseline and new_utf8:
        print(f"{'Recall %':<25} {baseline['recall']:<25.2f} {new_utf8['recall']:<25.2f}")
        print(f"{'Precision %':<25} {baseline['precision']:<25.2f} {new_utf8['precision']:<25.2f}")
        print(f"{'Top-1 Acc %':<25} {baseline['top1']:<25.2f} {new_utf8['top1']:<25.2f}")
        print(f"{'Top-5 Acc %':<25} {baseline['top5']:<25.2f} {new_utf8['top5']:<25.2f}")
        print(f"{'Flagged words':<25} {baseline['flagged']:<25} {new_utf8['flagged']:<25}")
        
        diff_recall = new_utf8['recall'] - baseline['recall']
        diff_prec = new_utf8['precision'] - baseline['precision']
        print("-"*80)
        print(f"Recall Delta: {diff_recall:+.2f}%")
        print(f"Precision Delta: {diff_prec:+.2f}%")
        if abs(diff_recall) < 1e-5 and abs(diff_prec) < 1e-5:
            print("\nSUCCESS: Both dictionaries exhibit identical spelling checker behavior!")
        else:
            print("\nWARNING: Behavior discrepancy detected between baseline and UTF-8 flags!")

if __name__ == '__main__':
    main()
