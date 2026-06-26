import json
import os
import subprocess
from zemberek import TurkishMorphology

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def merge_spelling_into_lexicon():
    print("Initializing Zemberek Morphological Analyzer...")
    morphology = TurkishMorphology.create_with_defaults()

    lexicon_path = 'zemberek_lexicon.json'
    if not os.path.exists(lexicon_path):
        print(f"Error: {lexicon_path} not found.")
        return

    print("Loading Zemberek lexicon...")
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)

    # Track existing lemmas for fast lookup
    existing_lemmas = {turkish_lowercase(entry['lemma']): entry for entry in lexicon}
    print(f"Lexicon currently has {len(existing_lemmas)} unique lemmas.")

    spelling_path = 'merged_dictionary_cleaned.txt'
    if not os.path.exists(spelling_path):
        print(f"Error: {spelling_path} not found.")
        return

    print(f"Reading {spelling_path}...")
    added_count = 0
    with open(spelling_path, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if not word:
                continue

            word_lower = turkish_lowercase(word)
            if word_lower not in existing_lemmas:
                # Let Zemberek analyze the word to guess attributes/POS
                analysis = list(morphology.analyze(word))
                if analysis:
                    parse = analysis[0]
                    guess_pos = parse.item.primary_pos.name if parse.item.primary_pos else "Noun"
                    guess_attrs = [attr.name for attr in parse.item.attributes] if parse.item.attributes else []
                else:
                    guess_pos = "Noun"
                    guess_attrs = []

                new_entry = {
                    "lemma": word,
                    "pos": guess_pos,
                    "attributes": guess_attrs
                }
                lexicon.append(new_entry)
                existing_lemmas[word_lower] = new_entry
                added_count += 1

    print(f"\nMerge completed:")
    print(f"  Added from spelling list: {added_count}")
    print(f"  Total lexicon database:   {len(lexicon)}")

    print(f"Saving updated lexicon to {lexicon_path}...")
    with open(lexicon_path, 'w', encoding='utf-8') as f:
        json.dump(lexicon, f, ensure_ascii=False, indent=2)

    print("\nRe-compiling Hunspell dictionary files...")
    try:
        result = subprocess.run(['python', 'compile_hunspell.py'], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error recompiling Hunspell: {e}")

if __name__ == '__main__':
    merge_spelling_into_lexicon()
