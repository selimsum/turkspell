import os
import re

def load_corpus(paths):
    print("Loading corpus and computing frequencies...")
    corpus = set()
    freq = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    word = parts[0]
                    count = int(parts[1])
                    corpus.add(word)
                    freq[word] = freq.get(word, 0) + count
                elif len(parts) == 1:
                    corpus.add(parts[0])
                    freq[parts[0]] = freq.get(parts[0], 0) + 1
                    
    print(f"Loaded {len(corpus)} unique words into corpus set.")
    return corpus, freq

def build_test_roots(dic_path, freq, max_roots=15):
    print(f"Building test roots from {dic_path} based on frequency...")
    flag_roots = {}
    with open(dic_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        
    for line in lines[1:]: # skip count
        if '/' not in line:
            continue
        word, flags = line.split('/', 1)
        # Only take words without spaces, lowercase, alpha
        if not word.isalpha() or not word.islower():
            continue
            
        # Add the word to the flag group
        for flag_char in flags:
            if flag_char not in flag_roots:
                flag_roots[flag_char] = []
            flag_roots[flag_char].append(word)
            
    # Now sort by frequency and keep top max_roots
    for flag_char in flag_roots:
        flag_roots[flag_char].sort(key=lambda w: freq.get(w, 0), reverse=True)
        flag_roots[flag_char] = flag_roots[flag_char][:max_roots]
        
    print(f"Found test roots for {len(flag_roots)} unique flags.")
    return flag_roots

def prune_aff(aff_path, corpus, test_roots):
    print(f"Pruning {aff_path}...")
    with open(aff_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        
    new_lines = []
    dropped_rules_count = 0
    total_rules = 0
    
    # Group lines into blocks safely
    blocks = []
    current_block = None
    
    for line in lines:
        if line.startswith('SFX ') or line.startswith('PFX '):
            parts = line.split()
            if len(parts) >= 4 and parts[2] in ('Y', 'N') and parts[3].isdigit():
                # Header
                if current_block:
                    blocks.append(current_block)
                current_block = {'header': line, 'flag': parts[1], 'type': parts[0], 'combine': parts[2], 'rules': []}
            elif current_block and len(parts) >= 4 and parts[1] == current_block['flag']:
                # Rule for current block
                current_block['rules'].append(line)
            else:
                # Orphan rule or malformed? Just push as raw line
                if current_block:
                    blocks.append(current_block)
                    current_block = None
                blocks.append(line)
        else:
            if current_block:
                blocks.append(current_block)
                current_block = None
            blocks.append(line)
            
    if current_block:
        blocks.append(current_block)
        
    for item in blocks:
        if isinstance(item, str):
            new_lines.append(item)
        else:
            # Process block
            kept_for_this_block = []
            roots = test_roots.get(item['flag'], [])
            if not roots:
                kept_for_this_block = item['rules']
                total_rules += len(item['rules'])
            else:
                for rule in item['rules']:
                    total_rules += 1
                    r_parts = rule.split()
                    if len(r_parts) < 4:
                        kept_for_this_block.append(rule)
                        continue
                        
                    strip = r_parts[2]
                    add = r_parts[3].split('/')[0] # ignore continuation flags
                    if strip == '0': strip = ''
                    if add == '0': add = ''
                    
                    hit = False
                    if strip == '' and add == '':
                        hit = True
                    else:
                        for root in roots:
                            if strip and root.endswith(strip):
                                test_word = root[:-len(strip)] + add
                            else:
                                test_word = root + add
                                
                            if test_word in corpus:
                                hit = True
                                break
                                
                    if hit:
                        kept_for_this_block.append(rule)
                    else:
                        dropped_rules_count += 1
                        
            # Only write block if it has rules
            if kept_for_this_block:
                new_header = f"{item['type']} {item['flag']} {item['combine']} {len(kept_for_this_block)}"
                new_lines.append(new_header)
                new_lines.extend(kept_for_this_block)
                
    with open(aff_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(new_lines) + '\n')
        
    print(f"Pruning complete! Dropped {dropped_rules_count} unused rules out of {total_rules}.")
    return dropped_rules_count

if __name__ == '__main__':
    # Adjust paths based on location
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ts_path = os.path.join(root_dir, 'scripts', 'phase1', 'data', 'ts_timeline_frequencies.txt')
    macocu_path = os.path.join(root_dir, 'scripts', 'phase1', 'data', 'macocu_frequencies.txt')
    
    corpus, freq = load_corpus([ts_path, macocu_path])
    
    dic_path = os.path.join(root_dir, 'tr.dic')
    aff_path = os.path.join(root_dir, 'tr.aff')
    
    test_roots = build_test_roots(dic_path, freq, max_roots=15)
    prune_aff(aff_path, corpus, test_roots)
