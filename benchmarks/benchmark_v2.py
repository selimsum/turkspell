"""
benchmark_v2.py
===============
Compare tr_v2.aff+tr_v2.dic against tr.aff+tr.dic and tdd-ai/hunspell-tr
on the official 10,000-word test set.

Metrics:
  Top-1 Acc: correction is exactly the first suggestion
  Top-5 Acc: correction is in the first 5 suggestions
  Recall:    misspelled word is detected as wrong (not passed through)
  Precision: non-misspelled gold words accepted as-is
"""

import subprocess
import sys
import csv
import io
import time
from pathlib import Path
from collections import defaultdict

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = Path(__file__).parent.parent
TEST_CSV = BASE / 'official_test_v2_fixed.csv'

DICTIONARIES = {
    'v1 (current)':      str(BASE / 'tr_v1'),
    'v2 (new FLAG long)': str(BASE / 'tr'),
    'tdd-ai/hunspell-tr': str(BASE / 'external_dictionaries' / 'tdd-ai' / 'tr_TR'),
    'harunzafer':        str(BASE / 'external_dictionaries' / 'harunzafer' / 'tr_TR'),
    'selimsum':          str(BASE / 'external_dictionaries' / 'selimsum' / 'tr'),
    'vdemir':            str(BASE / 'external_dictionaries' / 'vdemir' / 'tr_TR'),
}

# Filter to only dicts that exist
AVAILABLE = {}
for name, dic_base in DICTIONARIES.items():
    aff = Path(dic_base + '.aff')
    dic = Path(dic_base + '.dic')
    if aff.exists() and dic.exists():
        AVAILABLE[name] = dic_base
    else:
        print(f"  SKIP {name}: {aff} not found")

print(f"\nDictionaries to test: {list(AVAILABLE.keys())}")


def run_hunspell_suggest(words, dic_base, timeout=120):
    """
    Run hunspell -a on a list of words, return {word: [suggestions]} dict.
    Words that are correct get [] as suggestions.
    Words that are wrong get a list of suggestions (may be empty if no suggestions).
    """
    inp = '\n'.join(words) + '\n'
    result = subprocess.run(
        ['hunspell', '-d', dic_base, '-a'],
        input=inp, capture_output=True, text=True,
        encoding='utf-8', timeout=timeout
    )
    output = result.stdout

    suggestions = {}
    word_iter = iter(words)

    for line in output.split('\n'):
        line = line.strip()
        if not line or line.startswith('@'):
            # @ = info line (first line is version)
            continue
        elif line.startswith('*') or line.startswith('+') or line.startswith('-'):
            # * = correct word, + = compound, - = compound flag
            w = next(word_iter, None)
            if w is not None:
                suggestions[w] = []  # correct — no correction needed
        elif line.startswith('&'):
            # & word count offset: suggestions...
            parts = line.split(':', 1)
            sug_part = parts[1].strip() if len(parts) > 1 else ''
            sugs = [s.strip() for s in sug_part.split(',') if s.strip()]
            w = next(word_iter, None)
            if w is not None:
                suggestions[w] = sugs
        elif line.startswith('#'):
            # # = no suggestions
            w = next(word_iter, None)
            if w is not None:
                suggestions[w] = None  # wrong, no suggestions

    return suggestions


def run_hunspell_list(words, dic_base, timeout=120):
    """
    Run hunspell -l (list only unknown words).
    Returns set of unknown/misspelled words.
    """
    inp = '\n'.join(words) + '\n'
    result = subprocess.run(
        ['hunspell', '-d', dic_base, '-l'],
        input=inp, capture_output=True, text=True,
        encoding='utf-8', timeout=timeout
    )
    return {w.strip() for w in result.stdout.strip().split('\n') if w.strip()}


def benchmark_dict(dic_base, test_rows, name, batch_size=500):
    """
    Run the full benchmark for one dictionary.
    Returns dict of metric_name -> value.
    """
    print(f"\n  Running benchmark for '{name}'...")
    
    inputs = [r['input'] for r in test_rows]
    golds  = [r['gold']  for r in test_rows]

    top1 = 0
    top5 = 0
    detected = 0  # misspelled words correctly detected as wrong
    correct_pass = 0  # correctly-spelled words accepted as-is
    total_wrong = 0  # how many inputs != gold (i.e., misspelled)
    total_correct = 0  # how many inputs == gold (i.e., already correct)
    
    n = len(test_rows)
    t0 = time.time()

    for i in range(0, n, batch_size):
        batch_rows = test_rows[i:i+batch_size]
        batch_inp = [r['input'] for r in batch_rows]
        batch_gold = [r['gold'] for r in batch_rows]

        # Get suggestions for this batch
        sugs = run_hunspell_suggest(batch_inp, dic_base)

        for inp, gold in zip(batch_inp, batch_gold):
            inp_sugs = sugs.get(inp)
            is_misspelled = (inp != gold)

            if is_misspelled:
                total_wrong += 1
                # Detected: word was not passed as correct
                if inp_sugs != []:  # None or a list of sugs = was flagged
                    detected += 1
                # Top-1: first suggestion matches gold
                if isinstance(inp_sugs, list) and inp_sugs and inp_sugs[0] == gold:
                    top1 += 1
                # Top-5: gold in first 5 suggestions
                if isinstance(inp_sugs, list) and gold in inp_sugs[:5]:
                    top5 += 1
            else:
                total_correct += 1
                # Precision: correct word accepted as-is
                if inp_sugs == []:  # [] means "correct"
                    correct_pass += 1

        elapsed = time.time() - t0
        done = min(i + batch_size, n)
        rate = done / elapsed if elapsed > 0 else 0
        eta = (n - done) / rate if rate > 0 else 0
        print(f"    {done}/{n} ({done/n*100:.0f}%)  {rate:.0f} words/s  ETA {eta:.0f}s", end='\r')

    elapsed = time.time() - t0
    print(f"\n    Done in {elapsed:.1f}s")

    return {
        'Top-1 Acc %':   100 * top1 / total_wrong if total_wrong else 0,
        'Top-5 Acc %':   100 * top5 / total_wrong if total_wrong else 0,
        'Recall %':      100 * detected / total_wrong if total_wrong else 0,
        'Precision %':   100 * correct_pass / total_correct if total_correct else 0,
        'total_wrong':   total_wrong,
        'total_correct': total_correct,
    }


def main():
    print(f"\nLoading test set from {TEST_CSV}...")
    with open(TEST_CSV, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} test pairs.")

    results = {}
    for name, dic_base in AVAILABLE.items():
        results[name] = benchmark_dict(dic_base, rows, name)

    # Print comparison table
    metrics = ['Top-1 Acc %', 'Top-5 Acc %', 'Recall %', 'Precision %']
    col_w = max(len(n) for n in AVAILABLE) + 2

    print(f"\n{'=' * 70}")
    print(f"BENCHMARK RESULTS (n={len(rows)})")
    print(f"{'=' * 70}")
    header = f"{'Metric':<20}" + ''.join(f"{n:>{col_w}}" for n in results)
    print(header)
    print('-' * len(header))
    for m in metrics:
        row_str = f"{m:<20}" + ''.join(f"{results[n][m]:>{col_w}.2f}" for n in results)
        print(row_str)
    print('=' * 70)

    # v1 vs v2 delta
    if 'v1 (current)' in results and 'v2 (new FLAG long)' in results:
        print("\nv2 vs v1 delta:")
        for m in metrics:
            delta = results['v2 (new FLAG long)'][m] - results['v1 (current)'][m]
            sign = '+' if delta >= 0 else ''
            print(f"  {m:<20} {sign}{delta:.2f}%")


if __name__ == '__main__':
    main()
