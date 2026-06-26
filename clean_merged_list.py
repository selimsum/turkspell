from zemberek import TurkishMorphology
import os

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def clean_merged():
    print("Initializing Zemberek Morphological Analyzer...")
    morphology = TurkishMorphology.create_with_defaults()
    
    # Load Zemberek's built-in lexicon lemmas (lowercase)
    zemberek_lemmas = {item.lemma.lower() for item in morphology.lexicon.item_set}
    print(f"Loaded {len(zemberek_lemmas)} unique lemmas from Zemberek built-in lexicon.")
    
    merged_path = 'merged_dictionary.txt'
    if not os.path.exists(merged_path):
        print(f"Error: {merged_path} not found.")
        return
        
    print(f"Reading {merged_path}...")
    with open(merged_path, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]
        
    print(f"Loaded {len(words)} entries to filter.")
    
    cleaned_words = []
    removed_spaces = 0
    removed_derived = 0
    
    for word in words:
        # 1. Remove multi-word expressions (containing spaces)
        if ' ' in word:
            removed_spaces += 1
            continue
            
        cleaned_words.append(word)
        
    print(f"\nFiltering summary:")
    print(f"  Total initial words: {len(words)}")
    print(f"  Removed multi-word expressions (with spaces): {removed_spaces}")
    print(f"  Removed derived/inflected words: {removed_derived}")
    print(f"  Remaining cleaned words: {len(cleaned_words)}")
    
    cleaned_output = 'merged_dictionary_cleaned.txt'
    print(f"Saving cleaned merged dictionary to {cleaned_output}...")
    with open(cleaned_output, 'w', encoding='utf-8') as f:
        for w in cleaned_words:
            f.write(w + '\n')
            
    # Also recalculate the comparison with Zemberek based on the cleaned list
    cleaned_set_lower = {turkish_lowercase(w) for w in cleaned_words}
    missing_from_zemberek = sorted([w for w in cleaned_words if turkish_lowercase(w) not in zemberek_lemmas])
    
    # Map Zemberek lowercase to original
    zemberek_original_casing = {}
    for item in morphology.lexicon.item_set:
        lemma = item.lemma
        zemberek_original_casing[lemma.lower()] = lemma
        
    missing_from_merged = sorted([zemberek_original_casing[w] for w in zemberek_lemmas if w not in cleaned_set_lower])
    
    diff_output_path = 'merged_vs_zemberek_differences_cleaned.txt'
    print(f"Saving new differences report to {diff_output_path}...")
    with open(diff_output_path, 'w', encoding='utf-8') as f:
        f.write(f"=== WORDS IN CLEANED MERGED BUT MISSING FROM ZEMBEREK ({len(missing_from_zemberek)} words) ===\n")
        for w in missing_from_zemberek:
            f.write(w + '\n')
            
        f.write("\n\n")
        
        f.write(f"=== WORDS IN ZEMBEREK BUT MISSING FROM CLEANED MERGED ({len(missing_from_merged)} words) ===\n")
        for w in missing_from_merged:
            f.write(w + '\n')
            
    print("Done!")

if __name__ == "__main__":
    clean_merged()
