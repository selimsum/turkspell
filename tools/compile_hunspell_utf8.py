import os
import sys

# compile_hunspell and utf8_flag_mapping live in build/; migrate_dictionary at root;
# migrate_dictionary_utf8 is a sibling in tools/.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, 'build'))
sys.path.insert(0, os.path.join(_root, 'tools'))

from compile_hunspell import compile_dictionary
from utf8_flag_mapping import LONG_TO_UTF8, remap_flag_string
from migrate_dictionary_utf8 import migrate_dictionary_utf8

import shutil

def remap_aff_file(input_path: str = 'tr.aff', output_path: str = 'tr_utf8.aff', active_flags: set[str] = None):
    print(f"Reading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Change FLAG long to FLAG UTF-8
    content = content.replace("FLAG long", "FLAG UTF-8")

    # 2. Process line by line
    lines = content.split('\n')
    new_lines = []
    skip_current_block = False
    pruned_rules = 0

    for line in lines:
        line_strip = line.strip()
        if not line_strip or line_strip.startswith('#'):
            new_lines.append(line)
            continue

        parts = line.split()
        # Match header directives with flags
        if len(parts) == 2 and parts[0] in ('NOSUGGEST', 'NEEDAFFIX', 'KEEPCASE'):
            flag = parts[1]
            if flag in LONG_TO_UTF8:
                parts[1] = LONG_TO_UTF8[flag]
            new_lines.append(" ".join(parts))
        elif len(parts) == 2 and parts[0] == 'FLAG':
            new_lines.append("FLAG UTF-8")
            
        # SFX/PFX headers: SFX <flag> <Y/N> <count>
        elif len(parts) >= 4 and parts[0] in ('SFX', 'PFX') and parts[2] in ('Y', 'N'):
            flag = parts[1]
            utf8_flag = LONG_TO_UTF8.get(flag, flag)
            if active_flags is not None and utf8_flag not in active_flags:
                skip_current_block = True
                continue
            skip_current_block = False
            parts[1] = utf8_flag
            new_lines.append(" ".join(parts))
            
        # SFX/PFX rules: SFX <flag> <strip> <add>/<continuation_flags> <condition>
        elif len(parts) >= 2 and parts[0] in ('SFX', 'PFX'):
            if skip_current_block:
                pruned_rules += 1
                continue
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

    if pruned_rules:
        print(f"Pruned {pruned_rules:,} unreferenced/dead rules from {output_path}.")
    print(f"Writing remapped affix file to {output_path}...")
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write("\n".join(new_lines))
    print("Affix remapping complete.")

def apply_af_compression(aff_path: str, dic_path: str):
    print(f"Applying AF (Alias Flag) compression to {dic_path} and {aff_path}...")
    with open(dic_path, 'r', encoding='utf-8') as f:
        dic_lines = f.readlines()
        
    if not dic_lines:
        return
        
    header = dic_lines[0]
    entries = dic_lines[1:]
    
    unique_flags = {}
    for line in entries:
        if '/' in line:
            w, f_str = line.strip().split('/', 1)
            if f_str:
                unique_flags[f_str] = unique_flags.get(f_str, 0) + 1
                
    # Sort flags by frequency descending
    sorted_flags = sorted(unique_flags.items(), key=lambda x: x[1], reverse=True)
    flag_to_id = {f: str(i) for i, (f, count) in enumerate(sorted_flags, start=1)}
    
    # 1. Update .dic file
    new_dic = [header]
    for line in entries:
        if '/' in line:
            w, f_str = line.strip().split('/', 1)
            if f_str:
                new_dic.append(f"{w}/{flag_to_id[f_str]}\n")
            else:
                new_dic.append(line)
        else:
            new_dic.append(line)
            
    with open(dic_path, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(new_dic)
        
    # 2. Update .aff file
    af_block = [f"AF {len(flag_to_id)}"]
    for f_str, _ in sorted_flags:
        af_block.append(f"AF {f_str}")
        
    with open(aff_path, 'r', encoding='utf-8') as f:
        aff_content = f.read()
        
    # Insert AF block after FLAG UTF-8 or at the top
    am_placeholder = "\n# AM (Alias Morphological Fields) Placeholder\n# AM 1\n# AM po:noun\n\n"
    
    insertion_str = "\n" + "\n".join(af_block) + "\n" + am_placeholder
    
    if "FLAG UTF-8" in aff_content:
        aff_content = aff_content.replace("FLAG UTF-8", "FLAG UTF-8" + insertion_str, 1)
    else:
        aff_content = insertion_str + aff_content
        
    with open(aff_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(aff_content)
        
    print(f"AF Compression complete. Created {len(flag_to_id)} unique aliases.")

def main():
    # 1. Compile baseline (writes tr.dic and tr.aff)
    print("Step 1: Compiling baseline dictionary and rules...")
    compile_dictionary()

    # 2. Migrate tr.dic to tr_utf8.dic
    print("Step 2: Migrating dictionary to FLAG UTF-8...")
    migrate_dictionary_utf8('tr.dic', 'tr_utf8.dic')

    # Collect active flags from tr_utf8.dic + continuation suffixes
    active_flags = set()
    with open('tr_utf8.dic', 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0 and line.strip().isdigit():
                continue
            if '/' in line:
                for c in line.strip().split('/', 1)[1]:
                    active_flags.add(c)
                    
    with open('tr.aff', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4 and parts[0] in ('SFX', 'PFX') and '/' in parts[3]:
                cont = parts[3].split('/', 1)[1]
                for c in remap_flag_string(cont):
                    active_flags.add(c)
                    
    active_flags.update({LONG_TO_UTF8.get('NE', 'X'), LONG_TO_UTF8.get('KC', 'KC'), LONG_TO_UTF8.get('NS', 'NS')})

    # 3. Remap tr.aff to tr_utf8.aff with dead rule pruning
    print("Step 3: Remapping affix rules to FLAG UTF-8 with dead rule pruning...")
    remap_aff_file('tr.aff', 'tr_utf8.aff', active_flags=active_flags)

    # 4. Apply AF compression
    print("Step 4: Applying AF Compression...")
    apply_af_compression('tr_utf8.aff', 'tr_utf8.dic')

    # 5. Sync final UTF-8 files to tr.aff and tr.dic
    shutil.copyfile('tr_utf8.aff', 'tr.aff')
    shutil.copyfile('tr_utf8.dic', 'tr.dic')
    
    print("\nCompilation, pruning, AF compression, and migration to FLAG UTF-8 complete!")
    print(f"Affix file: tr.aff ({os.path.getsize('tr.aff') / 1024:.1f} KB)")
    print(f"Dictionary file: tr.dic ({os.path.getsize('tr.dic') / 1024:.1f} KB)")

if __name__ == '__main__':
    main()
