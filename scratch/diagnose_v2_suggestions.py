import subprocess
import csv
from pathlib import Path

def run_hunspell_a(words, dic_base):
    inp = '\n'.join(words) + '\n'
    result = subprocess.run(
        ['hunspell', '-d', dic_base, '-a'],
        input=inp, capture_output=True, text=True, encoding='utf-8'
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

def main():
    root = Path(__file__).parent.parent
    csv_path = root / 'official_test_v2_fixed.csv'
    our_dic = root / 'tr'
    selim_dic = root / 'external_dictionaries' / 'selimsum' / 'tr'

    print("Loading test cases...")
    test_cases = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gold, inp = row['gold'].strip(), row['input'].strip()
            if gold != inp:
                test_cases.append((inp, gold))

    print(f"Loaded {len(test_cases)} misspelled words. Running diagnosis on first 100 cases...")
    sample = test_cases[:100]
    inputs = [p[0] for p in sample]

    our_sugs = run_hunspell_a(inputs, str(our_dic))
    selim_sugs = run_hunspell_a(inputs, str(selim_dic))

    discrepancies = []
    for inp, gold in sample:
        our_list = our_sugs.get(inp) or []
        selim_list = selim_sugs.get(inp) or []
        
        our_top5 = gold in our_list[:5]
        selim_top5 = gold in selim_list[:5]

        if selim_top5 and not our_top5:
            discrepancies.append({
                'input': inp,
                'gold': gold,
                'our_sugs': our_list[:5],
                'selim_sugs': selim_list[:5]
            })

    print(f"\nFound {len(discrepancies)} cases where Selimsum is in Top-5 but we are not:")
    for idx, d in enumerate(discrepancies[:15], start=1):
        print(f"\n{idx}. Input: {d['input']} -> Gold: {d['gold']}")
        print(f"   Our Top-5: {d['our_sugs']}")
        print(f"   Selimsum Top-5: {d['selim_sugs']}")

if __name__ == '__main__':
    main()
