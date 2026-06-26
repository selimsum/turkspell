import os
import subprocess

def run_hunspell_batch(dict_path, typos):
    temp_in = "temp_compare_in.txt"
    temp_out = "temp_compare_out.txt"
    
    with open(temp_in, 'w', encoding='utf-8') as f:
        f.write('\n'.join(typos) + '\n')
        
    with open(temp_in, 'r', encoding='utf-8') as fin, \
         open(temp_out, 'w', encoding='utf-8') as fout:
        subprocess.run(['hunspell', '-a', '-d', dict_path], stdin=fin, stdout=fout)
        
    with open(temp_out, 'r', encoding='utf-8') as f:
        stdout = f.read()
        
    for p in [temp_in, temp_out]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass
            
    raw_blocks = stdout.split('\n\n')
    if raw_blocks and raw_blocks[0].startswith('@(#)'):
        lines = raw_blocks[0].splitlines()
        if len(lines) > 1:
            raw_blocks[0] = '\n'.join(lines[1:])
        else:
            raw_blocks.pop(0)
            
    blocks = [b.strip() for b in raw_blocks if b.strip()]
    results = []
    
    for block in blocks:
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
        results.append((is_incorrect, sugs))
        
    return results

def main():
    test_file = "official_test_v2_fixed.csv"
    dict_turkspell = os.path.abspath("tr")
    dict_tdd = os.path.abspath("external_dictionaries/tdd-ai/tr_TR")
    
    pairs = []
    with open(test_file, 'r', encoding='utf-8') as f:
        next(f) # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))
                if len(pairs) >= 1000:
                    break
                
    print(f"Comparing {len(pairs)} pairs from {test_file}...")
    
    typos = [p[1] for p in pairs]
    
    results_turk = run_hunspell_batch(dict_turkspell, typos)
    results_tdd = run_hunspell_batch(dict_tdd, typos)
    
    mismatches = []
    for i in range(min(len(pairs), len(results_turk), len(results_tdd))):
        gold, typo = pairs[i]
        _, sugs_turk = results_turk[i]
        _, sugs_tdd = results_tdd[i]
        
        gold_norm = gold.replace("’", "'").replace("‘", "'")
        
        sugs_turk_norm = [s.replace("’", "'").replace("‘", "'") for s in sugs_turk]
        turk_top1 = sugs_turk_norm[0] if sugs_turk_norm else None
        turk_has_top1 = (turk_top1 == gold_norm)
        
        sugs_tdd_norm = [s.replace("’", "'").replace("‘", "'") for s in sugs_tdd]
        tdd_top1 = sugs_tdd_norm[0] if sugs_tdd_norm else None
        tdd_has_top1 = (tdd_top1 == gold_norm)
        
        if tdd_has_top1 and not turk_has_top1:
            mismatches.append({
                "typo": typo,
                "gold": gold,
                "turk_sugs": sugs_turk[:5],
                "tdd_sugs": sugs_tdd[:5]
            })
            
    print(f"\nFound {len(mismatches)} mismatches where TDD got Top-1 but Turkspell did not:")
    print(f"{'Typo':<20} | {'Gold':<20} | {'Turkspell top 5':<50} | {'TDD-AI top 5':<50}")
    print("-" * 150)
    for m in mismatches:
        print(f"{m['typo']:<20} | {m['gold']:<20} | {str(m['turk_sugs']):<50} | {str(m['tdd_sugs']):<50}")

if __name__ == "__main__":
    main()
