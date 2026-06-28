import json
import re

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def clean_word(line):
    line = line.strip()
    if not line:
        return None
    # Split by comma in case there are grammatical endings/inflections
    word = line.split(',')[0].strip()
    # Strip any trailing/leading symbols but keep letters, spaces, hyphens, and circumflexes
    word = re.sub(r'[^\w\s\-\â\î\û\Â\Î\Û]', '', word)
    return word

def run_merge_and_compare():
    print("Loading TDK word list...")
    tdk_words = set()
    original_casing = {}
    with open('TDK_turkce_kelime_listesi.txt', 'r', encoding='utf-8') as f:
        for line in f:
            word = clean_word(line)
            if word:
                word_lower = turkish_lowercase(word)
                tdk_words.add(word_lower)
                if word_lower not in original_casing:
                    original_casing[word_lower] = word

    print("Loading Dil Derneği spelling dictionary...")
    dernek_words = set()
    with open('Dil_Dernegi_spelling_dictionary.txt', 'r', encoding='utf-8') as f:
        for line in f:
            word = clean_word(line)
            if word:
                word_lower = turkish_lowercase(word)
                dernek_words.add(word_lower)
                if word_lower not in original_casing:
                    original_casing[word_lower] = word

    # 1. Merge
    merged_words = tdk_words.union(dernek_words)
    print(f"\nMerged dictionary statistics:")
    print(f"  TDK unique words:         {len(tdk_words)}")
    print(f"  Dil Derneği unique words: {len(dernek_words)}")
    print(f"  Merged unique words:      {len(merged_words)}")

    # Save merged dictionary word list
    merged_output_path = 'merged_dictionary.txt'
    print(f"Saving merged word list to {merged_output_path}...")
    with open(merged_output_path, 'w', encoding='utf-8') as f:
        for w in sorted(merged_words):
            f.write(original_casing[w] + '\n')

    # 2. Load Zemberek lexicon
    print("\nLoading Zemberek lexicon...")
    with open('zemberek_lexicon.json', 'r', encoding='utf-8') as f:
        zemberek_entries = json.load(f)

    zemberek_lemmas = set()
    zemberek_original_casing = {}
    for entry in zemberek_entries:
        lemma = entry['lemma']
        lemma_lower = turkish_lowercase(lemma)
        zemberek_lemmas.add(lemma_lower)
        zemberek_original_casing[lemma_lower] = lemma

    print(f"Loaded {len(zemberek_lemmas)} unique lemmas from Zemberek.")

    # 3. Compare Merged vs Zemberek
    missing_from_zemberek = sorted([original_casing[w] for w in merged_words if w not in zemberek_lemmas])
    missing_from_merged = sorted([zemberek_original_casing[w] for w in zemberek_lemmas if w not in merged_words])

    print(f"\nComparison results:")
    print(f"  Words in Merged but missing from Zemberek: {len(missing_from_zemberek)}")
    print(f"  Words in Zemberek but missing from Merged: {len(missing_from_merged)}")

    # Write differences file
    diff_output_path = 'merged_vs_zemberek_differences.txt'
    print(f"Writing differences to {diff_output_path}...")
    with open(diff_output_path, 'w', encoding='utf-8') as f:
        f.write(f"=== WORDS IN MERGED BUT MISSING FROM ZEMBEREK ({len(missing_from_zemberek)} words) ===\n")
        for w in missing_from_zemberek:
            f.write(w + '\n')
            
        f.write("\n\n")
        
        f.write(f"=== WORDS IN ZEMBEREK BUT MISSING FROM MERGED ({len(missing_from_merged)} words) ===\n")
        for w in missing_from_merged:
            f.write(w + '\n')

    print("Merge and comparison complete!")

if __name__ == '__main__':
    run_merge_and_compare()
