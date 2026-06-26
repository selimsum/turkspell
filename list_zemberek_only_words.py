import json
import os

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def extract_zemberek_only():
    print("Loading Zemberek lexicon (cleaned)...")
    with open('zemberek_lexicon.json', 'r', encoding='utf-8') as f:
        lexicon = json.load(f)
        
    zemberek_lemmas = set()
    original_casing = {}
    for entry in lexicon:
        lemma = entry['lemma']
        lemma_lower = turkish_lowercase(lemma)
        zemberek_lemmas.add(lemma_lower)
        original_casing[lemma_lower] = lemma
        
    print(f"Loaded {len(zemberek_lemmas)} unique lemmas from Zemberek.")

    print("Loading merged TDK + Dil Derneği dictionary...")
    merged_words = set()
    with open('merged_dictionary.txt', 'r', encoding='utf-8') as f:
        for line in f:
            merged_words.add(turkish_lowercase(line.strip()))
            
    print(f"Loaded {len(merged_words)} unique words from TDK + Dil Derneği union.")

    # Find words in Zemberek but NOT in merged dictionary
    zemberek_only = sorted([original_casing[w] for w in zemberek_lemmas if w not in merged_words])
    
    print(f"\nFound {len(zemberek_only)} words present in Zemberek but not in TDK or Dil Derneği.")
    
    output_path = 'zemberek_only_words.txt'
    print(f"Saving list to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for w in zemberek_only:
            f.write(w + '\n')
            
    print("Sample words:")
    for w in zemberek_only[:50]:
        print(f"  - {w}")
        
    print("Done!")

if __name__ == '__main__':
    extract_zemberek_only()
