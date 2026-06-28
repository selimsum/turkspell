import json
import re

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def clean_spelling_word(line):
    line = line.strip()
    if not line:
        return None
    # Split by comma in case there are grammatical endings/inflections listed
    word = line.split(',')[0].strip()
    # Strip brackets/punctuation if any exist
    word = re.sub(r'[^\w\s\-\â\î\û\Â\Î\Û]', '', word)
    return word

def compare():
    print("Loading Zemberek lexicon...")
    with open('zemberek_lexicon.json', 'r', encoding='utf-8') as f:
        zemberek_entries = json.load(f)
        
    zemberek_lemmas = set()
    for entry in zemberek_entries:
        zemberek_lemmas.add(turkish_lowercase(entry['lemma']))
        
    print(f"Loaded {len(zemberek_lemmas)} unique lemmas from Zemberek.")
    
    print("Loading Dil Derneği spelling dictionary...")
    spelling_words = set()
    original_casing = {}
    
    with open('Dil_Dernegi_spelling_dictionary.txt', 'r', encoding='utf-8') as f:
        for line in f:
            word = clean_spelling_word(line)
            if word:
                word_lower = turkish_lowercase(word)
                spelling_words.add(word_lower)
                # Save the first casing we find for each lowercase version
                if word_lower not in original_casing:
                    original_casing[word_lower] = word
                    
    print(f"Loaded {len(spelling_words)} unique words from Dil Derneği dictionary.")
    
    # Compare
    missing_from_zemberek = sorted([original_casing[w] for w in spelling_words if w not in zemberek_lemmas])
    
    # For words missing from spelling, let's keep the Zemberek lemmas
    # Map lowercase to original Zemberek lemma
    zemberek_original_casing = {}
    for entry in zemberek_entries:
        lemma = entry['lemma']
        zemberek_original_casing[turkish_lowercase(lemma)] = lemma
        
    missing_from_spelling = sorted([zemberek_original_casing[w] for w in zemberek_lemmas if w not in spelling_words])
    
    print(f"Words in Dil Derneği but missing from Zemberek: {len(missing_from_zemberek)}")
    print(f"Words in Zemberek but missing from Dil Derneği: {len(missing_from_spelling)}")
    
    print("Writing missing_from_zemberek.txt...")
    with open('missing_from_zemberek.txt', 'w', encoding='utf-8') as f:
        for w in missing_from_zemberek:
            f.write(w + '\n')
            
    print("Writing missing_from_spelling.txt...")
    with open('missing_from_spelling.txt', 'w', encoding='utf-8') as f:
        for w in missing_from_spelling:
            f.write(w + '\n')
            
    print("Comparison complete!")

if __name__ == "__main__":
    compare()
