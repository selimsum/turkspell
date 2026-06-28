import json
import os
import subprocess

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def update_lexicon():
    lexicon_path = 'zemberek_lexicon.json'
    if not os.path.exists(lexicon_path):
        print(f"Error: {lexicon_path} not found.")
        return

    print("Loading Zemberek lexicon...")
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)

    existing_lemmas = {turkish_lowercase(entry['lemma']): entry for entry in lexicon}

    # New TDK 12. Baskı words to add/update
    new_words = [
        {"lemma": "Doğubayazıt", "pos": "Noun", "attributes": ["NoVoicing"]},
        {"lemma": "Marmaraereğlisi", "pos": "Noun", "attributes": ["CompoundP3sg"]},
        {"lemma": "Yakantop", "pos": "Noun", "attributes": ["Voicing"]},
        {"lemma": "Kayyım", "pos": "Noun", "attributes": []},
        {"lemma": "Akçaarmut", "pos": "Noun", "attributes": ["Voicing"]},
        {"lemma": "Sultanefendi", "pos": "Noun", "attributes": []},
        {"lemma": "Pileli", "pos": "Adjective", "attributes": []},
        {"lemma": "Yörük", "pos": "Noun", "attributes": ["Voicing"]},
        {"lemma": "Ünvan", "pos": "Noun", "attributes": []}
    ]

    added_count = 0
    updated_count = 0

    for item in new_words:
        lemma_lower = turkish_lowercase(item['lemma'])
        if lemma_lower not in existing_lemmas:
            lexicon.append(item)
            existing_lemmas[lemma_lower] = item
            added_count += 1
            print(f"Added new word: {item['lemma']} ({item['pos']}) with attributes {item['attributes']}")
        else:
            # Update attributes if needed
            entry = existing_lemmas[lemma_lower]
            if set(entry.get('attributes', [])) != set(item['attributes']):
                entry['attributes'] = item['attributes']
                updated_count += 1
                print(f"Updated existing word: {entry['lemma']} attributes to {item['attributes']}")

    print(f"\nTDK 12. Baskı updates complete:")
    print(f"  Added words:   {added_count}")
    print(f"  Updated words: {updated_count}")

    print(f"Saving lexicon to {lexicon_path}...")
    with open(lexicon_path, 'w', encoding='utf-8') as f:
        json.dump(lexicon, f, ensure_ascii=False, indent=2)

    print("\nRe-compiling Hunspell dictionary files...")
    try:
        result = subprocess.run(['python', 'compile_hunspell.py'], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error recompiling Hunspell: {e}")

if __name__ == '__main__':
    update_lexicon()
