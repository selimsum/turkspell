import csv
import subprocess
from pathlib import Path

BASE = Path(__file__).parent.parent
CSV_PATH = BASE / 'official_test_v2_fixed.csv'

def check_batch(words, dic_base):
    inp = '\n'.join(words) + '\n'
    result = subprocess.run(
        ['hunspell', '-d', dic_base, '-l'],
        input=inp, capture_output=True, text=True, encoding='utf-8'
    )
    return {w.strip() for w in result.stdout.strip().split('\n') if w.strip()}

def main():
    print("Loading words...")
    golds = set()
    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            golds.add(r['gold'])
            
    golds = sorted(list(golds))
    print(f"Total unique gold words: {len(golds)}")
    
    print("Checking with v1 (tr_v1)...")
    v1_rejected = check_batch(golds, 'tr_v1')
    
    print("Checking with v2 (tr)...")
    v2_rejected = check_batch(golds, 'tr')
    
    false_rejections = []
    for w in golds:
        if w not in v1_rejected and w in v2_rejected:
            false_rejections.append(w)
            
    print(f"\nFound {len(false_rejections)} false rejections (accepted by v1, rejected by v2):")
    for w in false_rejections[:100]:
        print(w)
        
    # Write to a file for deeper inspection
    out_path = BASE / 'scratch' / 'false_rejections.txt'
    with open(out_path, 'w', encoding='utf-8') as f:
        for w in false_rejections:
            f.write(w + '\n')
    print(f"\nWrote {len(false_rejections)} words to {out_path}")

if __name__ == '__main__':
    main()
