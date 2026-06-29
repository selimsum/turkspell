import os
from compile_hunspell import compile_dictionary
from utf8_flag_mapping import LONG_TO_UTF8, remap_flag_string
from migrate_dictionary_utf8 import migrate_dictionary_utf8

def remap_aff_file(input_path: str = 'tr_v1.aff', output_path: str = 'tr_utf8.aff'):
    print(f"Reading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Change FLAG long to FLAG UTF-8
    content = content.replace("FLAG long", "FLAG UTF-8")

    # 2. Process line by line
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        line_strip = line.strip()
        if not line_strip or line_strip.startswith('#'):
            new_lines.append(line)
            continue

        parts = line.split()
        
        # Match NOSUGGEST line
        if len(parts) == 2 and parts[0] == 'NOSUGGEST':
            flag = parts[1]
            if flag in LONG_TO_UTF8:
                parts[1] = LONG_TO_UTF8[flag]
            new_lines.append(" ".join(parts))
            
        # SFX/PFX headers: SFX <flag> <Y/N> <count>
        elif len(parts) >= 4 and parts[0] in ('SFX', 'PFX') and parts[2] in ('Y', 'N'):
            flag = parts[1]
            if flag in LONG_TO_UTF8:
                parts[1] = LONG_TO_UTF8[flag]
            new_lines.append(" ".join(parts))
            
        # SFX/PFX rules: SFX <flag> <strip> <add>/<continuation_flags> <condition>
        elif len(parts) >= 2 and parts[0] in ('SFX', 'PFX'):
            # Map main flag
            flag = parts[1]
            if flag in LONG_TO_UTF8:
                parts[1] = LONG_TO_UTF8[flag]
                
            # Map continuation flags in the third part
            if len(parts) >= 4:
                add_field = parts[3]
                if '/' in add_field:
                    prefix_str, flags_str = add_field.split('/', 1)
                    remapped_flags = remap_flag_string(flags_str)
                    parts[3] = f"{prefix_str}/{remapped_flags}"
                    
            new_lines.append(" ".join(parts))
        else:
            new_lines.append(line)

    print(f"Writing remapped affix file to {output_path}...")
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write("\n".join(new_lines))
    print("Affix remapping complete.")

def main():
    # 1. Compile baseline (writes tr.dic and tr_v1.aff)
    print("Step 1: Compiling baseline dictionary and rules...")
    compile_dictionary()

    # 2. Remap tr_v1.aff to tr_utf8.aff
    print("Step 2: Remapping affix rules to FLAG UTF-8...")
    remap_aff_file('tr_v1.aff', 'tr_utf8.aff')

    # 3. Migrate tr.dic to tr_utf8.dic
    print("Step 3: Migrating dictionary to FLAG UTF-8...")
    migrate_dictionary_utf8('tr.dic', 'tr_utf8.dic')
    
    print("\nCompilation and migration to FLAG UTF-8 complete!")
    print(f"Affix file: tr_utf8.aff ({os.path.getsize('tr_utf8.aff') / 1024:.1f} KB)")
    print(f"Dictionary file: tr_utf8.dic ({os.path.getsize('tr_utf8.dic') / 1024:.1f} KB)")

if __name__ == '__main__':
    main()
