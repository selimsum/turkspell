import subprocess
import os

dict_path = os.path.abspath("tr")

def main():
    test_set_path = 'official_test_v2_fixed.csv'
    if not os.path.exists(test_set_path):
        print(f"Error: {test_set_path} not found.")
        return
        
    pairs = []
    with open(test_set_path, 'r', encoding='utf-8') as f:
        next(f) # skip header
        for line in f:
            parts = line.strip().split(',')
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))
                if len(pairs) >= 1000:
                    break

    # Write inputs to temp file
    temp_in = "temp_detect_in.txt"
    temp_out = "temp_detect_out.txt"
    
    with open(temp_in, 'w', encoding='utf-8') as f:
        f.write('\n'.join([p[1] for p in pairs]) + '\n')
        
    with open(temp_in, 'r', encoding='utf-8') as fin, \
         open(temp_out, 'w', encoding='utf-8') as fout:
        subprocess.run(['hunspell', '-a', '-d', dict_path], stdin=fin, stdout=fout)
    
    # Read output and match with inputs
    results = []
    with open(temp_out, 'r', encoding='utf-8') as f:
        output_content = f.read()
        
    for p in [temp_in, temp_out]:
        if os.path.exists(p):
            os.remove(p)
            
    raw_blocks = output_content.split('\n\n')
    if raw_blocks and raw_blocks[0].startswith('@(#)'):
        lines = raw_blocks[0].splitlines()
        if len(lines) > 1:
            raw_blocks[0] = '\n'.join(lines[1:])
        else:
            raw_blocks.pop(0)
            
    blocks = [b.strip() for b in raw_blocks if b.strip()]
    
    not_flagged = []
    for i in range(min(len(pairs), len(blocks))):
        gold, inp = pairs[i]
        block = blocks[i]
        
        is_incorrect = False
        for line in block.splitlines():
            if line.startswith('&') or line.startswith('#'):
                is_incorrect = True
                break
                
        if not is_incorrect:
            not_flagged.append((gold, inp))
            
    print(f"Total not flagged typos: {len(not_flagged)}")
    for gold, inp in not_flagged:
        print(f"  Typo: {inp:<15} (Intended Gold: {gold})")

if __name__ == "__main__":
    main()
