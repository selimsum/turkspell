import json
import os
import subprocess

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def remove_zemberek_only():
    lexicon_path = 'zemberek_lexicon.json'
    if not os.path.exists(lexicon_path):
        print(f"Error: {lexicon_path} not found.")
        return

    print("Loading Zemberek lexicon...")
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)

    merged_path = 'merged_dictionary.txt'
    if not os.path.exists(merged_path):
        print(f"Error: {merged_path} not found.")
        return

    print("Loading merged TDK + Dil Derneği dictionary...")
    merged_words = set()
    with open(merged_path, 'r', encoding='utf-8') as f:
        for line in f:
            merged_words.add(turkish_lowercase(line.strip()))

    cleaned_lexicon = []
    removed_count = 0

    print("Filtering Zemberek lexicon...")
    for entry in lexicon:
        lemma_lower = turkish_lowercase(entry['lemma'])
        if lemma_lower in merged_words:
            cleaned_lexicon.append(entry)
        else:
            removed_count += 1

    print(f"\nFiltering summary:")
    print(f"  Initial lexicon size:   {len(lexicon)}")
    print(f"  Removed Zemberek-only:  {removed_count}")
    print(f"  Cleaned lexicon size:   {len(cleaned_lexicon)}")

    print(f"Saving cleaned lexicon to {lexicon_path}...")
    with open(lexicon_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_lexicon, f, ensure_ascii=False, indent=2)

    print("\nRe-compiling Hunspell dictionary files...")
    try:
        result = subprocess.run(['python', 'compile_hunspell.py'], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error recompiling Hunspell: {e}")

if __name__ == '__main__':
    remove_zemberek_only()
