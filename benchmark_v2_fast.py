"""
benchmark_v2_fast.py  (v4 — sampled suggestions)
=================================================
Strategy:
  - Detection  : hunspell -l  on ALL 10,000 words  (~6s per dict)
  - Suggestions: hunspell -a  on SAMPLE of 50 words (timeout=900s per dict)
  - Top-1/Top-5 on sample; Recall/Precision on full set.
  - TimeoutExpired → marks suggestions as N/A for that dict.
"""
import subprocess, sys, csv, io, time, random
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE     = Path(__file__).parent
TEST_CSV = BASE / 'official_test_v2_fixed.csv'
SAMPLE_N = 50    # words for Top-1/Top-5 (small to keep under timeout)
SEED     = 42

DICTIONARIES = {
    'v1 (current)':       str(BASE / 'tr_v1'),
    'v2 (FLAG UTF-8)':    str(BASE / 'tr'),
    'tdd-ai/hunspell-tr': str(BASE / 'external_dictionaries' / 'tdd-ai'     / 'tr_TR'),
    'harunzafer':         str(BASE / 'external_dictionaries' / 'harunzafer' / 'tr_TR'),
    'selimsum':           str(BASE / 'external_dictionaries' / 'selimsum'   / 'tr'),
    'vdemir':             str(BASE / 'external_dictionaries' / 'vdemir'     / 'tr_TR'),
}

AVAILABLE = {}
for name, dic_base in DICTIONARIES.items():
    if Path(dic_base + '.aff').exists() and Path(dic_base + '.dic').exists():
        AVAILABLE[name] = dic_base
    else:
        print(f"  SKIP {name}: {dic_base}.aff not found")
print(f"\nDictionaries: {list(AVAILABLE.keys())}\n")


def hspell_l(words: list, dic: str, timeout=120) -> set:
    """hunspell -l via stdin → set of unknown words."""
    result = subprocess.run(
        ['hunspell', '-d', dic, '-l'],
        input='\n'.join(words) + '\n',
        capture_output=True, text=True, encoding='utf-8', timeout=timeout
    )
    return {w.strip() for w in result.stdout.split('\n') if w.strip()}


def hspell_a(words: list, dic: str, timeout=900) -> dict:
    """hunspell -a via stdin → {word: [sugs] or None}."""
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

    # --- Step 1: detection on all words ---
    print(f"  [{name}]  Step 1/2: detection...", end=' ', flush=True)
    t0 = time.time()
    unknown = hspell_l(inputs, dic_base)
    t1 = time.time()
    print(f"{t1-t0:.1f}s  ({len(unknown)} flagged)")

    # Recall / Precision on full set
    total_mis = total_cor = detected = correct_pass = 0
    mis_pairs = []  # (input, gold) where input!=gold and detected
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

    recall    = 100 * detected    / total_mis if total_mis else 0
    precision = 100 * correct_pass / total_cor if total_cor else 0

    # --- Step 2: suggestions on a sample ---
    # De-duplicate by input word
    seen, unique_pairs = set(), []
    for inp, gold in mis_pairs:
        if inp not in seen:
            seen.add(inp)
            unique_pairs.append((inp, gold))

    rng = random.Random(SEED)
    sample = unique_pairs if SAMPLE_N is None else rng.sample(unique_pairs, min(SAMPLE_N, len(unique_pairs)))
    sample_words = [p[0] for p in sample]
    sample_golds = {p[0]: p[1] for p in sample}

    print(f"  [{name}]  Step 2/2: suggestions for {len(sample_words)} sampled words...",
          end=' ', flush=True)
    t2 = time.time()
    timed_out = False
    try:
        sugs = hspell_a(sample_words, dic_base)
    except subprocess.TimeoutExpired:
        sugs = {}
        timed_out = True
    t3 = time.time()
    if timed_out:
        print(f"TIMED OUT after {t3-t2:.0f}s (suggestions unavailable)")
    else:
        print(f"{t3-t2:.1f}s")

    top1 = top5 = 0
    for w, gold in sample_golds.items():
        s = sugs.get(w)
        if isinstance(s, list) and s:
            if s[0] == gold:      top1 += 1
            if gold in s[:5]:     top5 += 1

    n_s = len(sample)
    top1_pct = 100 * top1 / n_s if n_s else 0
    top5_pct = 100 * top5 / n_s if n_s else 0

    elapsed = t3 - t0
    print(f"  → Top-1: {top1_pct:.2f}%  Top-5: {top5_pct:.2f}%  "
          f"Recall: {recall:.2f}%  Precision: {precision:.2f}%  "
          f"({elapsed:.0f}s)\n")

    return {
        'Top-1 Acc %': top1_pct,
        'Top-5 Acc %': top5_pct,
        'Recall %':    recall,
        'Precision %': precision,
        'sample_n':    n_s,
        'elapsed_s':   t3 - t0,
        'timed_out':   timed_out,
    }


def main():
    test_csv = TEST_CSV
    if len(sys.argv) > 1:
        test_csv = Path(sys.argv[1])
    print(f"Loading {test_csv}...")
    rows = []
    with open(test_csv, encoding='utf-8') as f:
        # Read the first line to check for headers
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
    print(f"Loaded {len(rows)} test pairs.  "
          f"Suggestion sample: {SAMPLE_N or 'all'} words  seed={SEED}\n")

    results = {}
    grand_t0 = time.time()
    for name, dic_base in AVAILABLE.items():
        results[name] = benchmark(dic_base, rows, name)

    print(f"Total: {time.time()-grand_t0:.0f}s\n")

    # --- Print table ---
    metrics = ['Top-1 Acc %', 'Top-5 Acc %', 'Recall %', 'Precision %']
    names   = list(results.keys())
    col_w   = max(len(n) for n in names) + 2
    sep     = '=' * (20 + col_w * len(names))

    note = f"(Top-1/Top-5 on {results[names[0]]['sample_n']}-word sample; Recall/Precision on all {len(rows)})"
    print(sep)
    print(f"BENCHMARK RESULTS  {note}")
    print(sep)
    hdr = f"{'Metric':<20}" + ''.join(f"{n:>{col_w}}" for n in names)
    print(hdr)
    print('-' * len(hdr))
    for m in metrics:
        def cell(n, m):
            if results[n].get('timed_out') and m in ('Top-1 Acc %', 'Top-5 Acc %'):
                return f"{'N/A':>{col_w}}"
            return f"{results[n][m]:>{col_w}.2f}"
        print(f"{m:<20}" + ''.join(cell(n, m) for n in names))
    print(sep)

    if 'v1 (current)' in results and 'v2 (FLAG UTF-8)' in results:
        print("\nv2 vs v1 delta:")
        for m in metrics:
            d = results['v2 (FLAG UTF-8)'][m] - results['v1 (current)'][m]
            print(f"  {m:<20} {'+' if d>=0 else ''}{d:.2f}%")


if __name__ == '__main__':
    main()
