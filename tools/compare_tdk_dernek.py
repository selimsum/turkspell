def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def clean_word(line):
    line = line.strip()
    if not line:
        return None
    # Split by comma in case there are grammatical endings/inflections
    word = line.split(',')[0].strip()
    return word

def compare():
    print("Loading TDK word list...")
    tdk_words = set()
    tdk_original_casing = {}
    with open('TDK_turkce_kelime_listesi.txt', 'r', encoding='utf-8') as f:
        for line in f:
            word = clean_word(line)
            if word:
                word_lower = turkish_lowercase(word)
                tdk_words.add(word_lower)
                if word_lower not in tdk_original_casing:
                    tdk_original_casing[word_lower] = word

    print(f"Loaded {len(tdk_words)} unique words/phrases from TDK.")

    print("Loading Dil Derneği spelling dictionary...")
    dernek_words = set()
    dernek_original_casing = {}
    with open('Dil_Dernegi_spelling_dictionary.txt', 'r', encoding='utf-8') as f:
        for line in f:
            word = clean_word(line)
            if word:
                word_lower = turkish_lowercase(word)
                dernek_words.add(word_lower)
                if word_lower not in dernek_original_casing:
                    dernek_original_casing[word_lower] = word

    print(f"Loaded {len(dernek_words)} unique words/phrases from Dil Derneği.")

    # Calculate differences
    only_in_tdk = sorted([tdk_original_casing[w] for w in tdk_words if w not in dernek_words])
    only_in_dernek = sorted([dernek_original_casing[w] for w in dernek_words if w not in tdk_words])

    print(f"Words only in TDK: {len(only_in_tdk)}")
    print(f"Words only in Dil Derneği: {len(only_in_dernek)}")

    output_path = 'tdk_vs_dernek_differences.txt'
    print(f"Writing differences to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"=== WORDS ONLY IN TDK ({len(only_in_tdk)} words) ===\n")
        for w in only_in_tdk:
            f.write(w + '\n')
            
        f.write("\n\n")
        
        f.write(f"=== WORDS ONLY IN DIL DERNEGI ({len(only_in_dernek)} words) ===\n")
        for w in only_in_dernek:
            f.write(w + '\n')

    print("Comparison and writing complete!")

if __name__ == "__main__":
    compare()
