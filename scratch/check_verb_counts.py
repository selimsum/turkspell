def main():
    print("Parsing tr_v2.aff for verb rule count validation...")
    with open('tr_v2.aff', 'r', encoding='utf-8') as f:
        content = f.read()
        
    parts = content.split('# VERB PARADIGM FLAGS\n')
    if len(parts) < 2:
        print("Could not find verb paradigm flags section!")
        return
        
    verb_lines = parts[1].split('\n')
    current_flag = None
    declared_count = 0
    actual_count = 0
    
    for line in verb_lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith('#'):
            continue
            
        parts = line_clean.split()
        if len(parts) == 4 and parts[0] == 'SFX' and parts[2] == 'Y':
            # Header line
            if current_flag:
                print(f"Flag {current_flag}: Declared = {declared_count}, Actual = {actual_count}, Diff = {actual_count - declared_count}")
            current_flag = parts[1]
            declared_count = int(parts[3])
            actual_count = 0
        elif parts[0] == 'SFX' and parts[1] == current_flag:
            actual_count += 1
            
    if current_flag:
        print(f"Flag {current_flag}: Declared = {declared_count}, Actual = {actual_count}, Diff = {actual_count - declared_count}")

if __name__ == '__main__':
    main()
