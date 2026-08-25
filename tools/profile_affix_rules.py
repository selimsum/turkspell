import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    aff_path = os.path.join(base_dir, 'tr.aff')
    dic_path = os.path.join(base_dir, 'tr.dic')
    
    if not os.path.exists(aff_path) or not os.path.exists(dic_path):
        print("tr.aff or tr.dic not found in project root.")
        return
        
    print(f"Reading {aff_path}...")
    sfx_rules = {}
    current_flag = None
    
    with open(aff_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) == 4 and parts[0] == 'SFX' and parts[3].isdigit():
                current_flag = parts[1]
                sfx_rules[current_flag] = []
            elif len(parts) >= 4 and parts[0] == 'SFX' and current_flag and parts[1] == current_flag:
                sfx_rules[current_flag].append(parts)
                
    print(f"Parsed {len(sfx_rules)} SFX flag blocks, total {sum(len(v) for v in sfx_rules.values()):,} rules.")
    
    print(f"Reading {dic_path}...")
    flag_usage = {}
    with open(dic_path, encoding='utf-8') as f:
        first_line = f.readline()
        for line in f:
            line = line.strip()
            if '/' in line:
                word, flags = line.split('/', 1)
                # In FLAG UTF-8, each char is an individual flag
                for ch in flags:
                    if ch not in (',', ' '):
                        flag_usage[ch] = flag_usage.get(ch, 0) + 1
                    
    print("\nAffix Flag Distribution (Top 25 most assigned individual flags):")
    sorted_usage = sorted(flag_usage.items(), key=lambda x: x[1], reverse=True)
    for flag, cnt in sorted_usage[:25]:
        rule_cnt = len(sfx_rules.get(flag, []))
        print(f"  Flag [{flag}]: assigned to {cnt:,} dictionary entries ({rule_cnt} affix rules)")
        
    print("\nUnassigned SFX Flags:")
    unassigned = [f for f in sfx_rules if f not in flag_usage]
    print(f"  {len(unassigned)} flags have 0 dictionary entries referencing them: {unassigned[:15]}")

if __name__ == '__main__':
    main()
