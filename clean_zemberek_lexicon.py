import json
import os
import re
import subprocess

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def clean_lexicon():
    lexicon_path = 'zemberek_lexicon.json'
    if not os.path.exists(lexicon_path):
        print(f"Error: {lexicon_path} not found.")
        return

    print("Loading Zemberek lexicon...")
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)

    # Load TDK + Dernek union
    merged_path = 'merged_dictionary.txt'
    if not os.path.exists(merged_path):
        print(f"Error: {merged_path} not found. Running merge first...")
        # Fall back to checking individually if needed, but merged_dictionary.txt should exist
        dictionaries = set()
    else:
        print("Loading Turkish dictionaries...")
        dictionaries = set()
        with open(merged_path, 'r', encoding='utf-8') as f:
            for line in f:
                dictionaries.add(turkish_lowercase(line.strip()))

    # Load English words list
    english_path = 'english_words_large.txt'
    if not os.path.exists(english_path):
        print(f"Error: {english_path} not found.")
        return

    print("Loading English word list...")
    with open(english_path, 'r', encoding='utf-8') as f:
        english = {line.strip().lower() for line in f if line.strip()}

    cleaned_lexicon = []
    removed_foreign_letters = 0
    removed_english = 0

    print("Filtering Zemberek lexicon...")
    for entry in lexicon:
        lemma = entry['lemma']
        lemma_lower = turkish_lowercase(lemma)
        
        # If the word is in Turkish dictionaries, protect it!
        if lemma_lower in dictionaries:
            cleaned_lexicon.append(entry)
            continue

        # Check for foreign letters q, w, x
        if re.search(r'[qwxQWX]', lemma):
            removed_foreign_letters += 1
            continue

        # Check if it is an English word not present in Turkish dictionaries
        if lemma_lower in english:
            removed_english.append(lemma) if isinstance(removed_english, list) else None
            # We will count it below
            continue

        cleaned_lexicon.append(entry)

    print(f"\nFiltering summary:")
    print(f"  Initial lexicon size:   {len(lexicon)}")
    print(f"  Removed due to q/w/x:   {removed_foreign_letters}")
    # Calculate english removed
    removed_english_count = len(lexicon) - len(cleaned_lexicon) - removed_foreign_letters
    print(f"  Removed English words:  {removed_english_count}")
    print(f"  Cleaned lexicon size:   {len(cleaned_lexicon)}")

    print(f"Saving cleaned lexicon to {lexicon_path}...")
    with open(lexicon_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_lexicon, f, ensure_ascii=False, indent=2)

    print("\nRe-compiling Hunspell dictionary files...")
    # Call compile_hunspell.py using python
    try:
        result = subprocess.run(['python', 'compile_hunspell.py'], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error recompiling Hunspell: {e}")

if __name__ == '__main__':
    clean_lexicon()
