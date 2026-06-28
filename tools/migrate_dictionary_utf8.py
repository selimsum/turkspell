import os
import sys
import json

# Add parent directory to path so it can import from root when run from tools/
base_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(base_dir) in ('tools', 'scripts'):
    project_root = os.path.dirname(base_dir)
else:
    project_root = base_dir

sys.path.append(project_root)

from utf8_flag_mapping import remap_flag_string
from migrate_dictionary import migrate_line

def migrate_dictionary_utf8(input_path: str = 'tr.dic',
                            output_path: str = 'tr_utf8.dic',
                            max_warnings: int = 50):
    """Migrate tr.dic to FLAG UTF-8 format by first getting the 2-char flags and remapping them."""
    # Try loading obsolete lemmas (relative to project root)
    obsolete_set = set()
    obsolete_path = os.path.join(project_root, 'scratch', 'obsolete_lemmas.json')
    if os.path.exists(obsolete_path):
        try:
            with open(obsolete_path, 'r', encoding='utf-8') as f:
                obsolete_list = json.load(f)
                obsolete_set = set(obsolete_list)
            print(f"Loaded {len(obsolete_set)} obsolete lemmas to flag as NOSUGGEST.")
        except Exception as e:
            print(f"Error loading obsolete lemmas: {e}")
    else:
        print("Warning: obsolete_lemmas.json not found. No words will be flagged as NOSUGGEST.")

    print(f"Reading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    count_line = lines[0].strip()  # First line is word count
    data_lines = lines[1:]

    print(f"Total entries to migrate: {count_line}")
    print(f"Migrating to UTF-8 flags...")

    out_lines = []
    all_warnings = []
    migrated = 0

    for i, line in enumerate(data_lines, start=2):
        # 1. Migrate line to 2-character flag format
        new_line_2char, warning = migrate_line(line, i, obsolete_set)
        if warning:
            all_warnings.append(warning)
        
        if new_line_2char is not None:
            # 2. Convert the 2-character flag suffix to single UTF-8 characters
            new_line_2char = new_line_2char.rstrip('\n')
            if '/' in new_line_2char:
                word, flags_str = new_line_2char.split('/', 1)
                utf8_flags = remap_flag_string(flags_str)
                new_line_utf8 = f"{word}/{utf8_flags}"
            else:
                new_line_utf8 = new_line_2char
                
            out_lines.append(new_line_utf8 + '\n')
            migrated += 1

    # Write output
    print(f"Writing {output_path}...")
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f"{migrated}\n")
        f.writelines(out_lines)

    print(f"Done. {migrated} entries written to {output_path}.")
    return len(all_warnings)

if __name__ == '__main__':
    migrate_dictionary_utf8()
