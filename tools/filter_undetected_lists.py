import re
import os
import sys
from zemberek import TurkishMorphology

COMMON_BRANDS = {
    'microsoft', 'apple', 'google', 'amazon', 'nvidia', 'netflix', 'facebook', 'twitter',
    'instagram', 'youtube', 'tiktok', 'spotify', 'tesla', 'samsung', 'sony', 'panasonic',
    'intel', 'amd', 'dell', 'hp', 'ibm', 'oracle', 'cisco', 'adidas', 'nike', 'puma',
    'reebok', 'underarmour', 'loreal', 'dove', 'colgate', 'pepsi', 'coca-cola', 'cocacola',
    'starbucks', 'mcdonalds', 'burgerking', 'subway', 'nestle', 'unilever', 'pampers',
    'gillette', 'oralb', 'pantene', 'bayer', 'pfizer', 'roche', 'novartis', 'toyota',
    'honda', 'ford', 'bmw', 'audi', 'mercedes', 'nissan', 'chevrolet', 'hyundai', 'kia',
    'arçelik', 'beko', 'vestel', 'mavi', 'lcwaikiki', 'waikiki', 'migros', 'carrefour',
    'trendyol', 'hepsiburada', 'getir', 'sahibinden'
}

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def is_english_or_proper(word, morphology, english_set):
    word_lower = turkish_lowercase(word)
    
    # 1. Check brand names
    for brand in COMMON_BRANDS:
        if brand in word_lower:
            return True
            
    # 2. Check English dictionary
    if word_lower in english_set:
        return True
        
    # 3. Check if all uppercase or abbreviation/symbols
    if word.isupper():
        return True
        
    # 4. Check if contains foreign characters or non-alphabetic/Greek symbols
    if any(ord(c) > 1000 for c in word):
        # Greek letters (alpha, lambda, pi, etc.)
        return True

    # 5. Check proper noun and foreign name heuristics
    # If the word starts with an uppercase letter:
    if word[0].isupper():
        parses = list(morphology.analyze(word_lower))
        if not parses:
            # Capitalized word that Zemberek cannot parse is almost certainly a foreign name/proper noun
            return True
        # If it parses, check if it's parsed as ProperNoun
        if any(p.item.secondary_pos.name == 'ProperNoun' for p in parses):
            return True

    # Also check Zemberek parses on the original casing
    parses_orig = list(morphology.analyze(word))
    if parses_orig and any(p.item.secondary_pos.name == 'ProperNoun' for p in parses_orig):
        return True

    return False

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("Initializing Zemberek Morphological Analyzer...")
    morphology = TurkishMorphology.create_with_defaults()

    english_path = 'english_words_large.txt'
    if not os.path.exists(english_path):
        print(f"Error: {english_path} not found.")
        return

    print("Loading English word list...")
    with open(english_path, 'r', encoding='utf-8') as f:
        english_set = {line.strip().lower() for line in f if line.strip()}

    files_to_filter = [
        'undetected_words_turkspell.txt',
        'undetected_words_tdd_hunspell-tr.txt',
        'undetected_words_hunspell-tr-moz.txt'
    ]

    for filename in files_to_filter:
        if not os.path.exists(filename):
            print(f"Warning: {filename} not found, skipping.")
            continue
            
        print(f"\nFiltering {filename}...")
        words_with_freq = []
        with open(filename, 'r', encoding='utf-8') as f:
            header = f.readline() # skip header
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    words_with_freq.append((parts[0], int(parts[1])))

        filtered_list = []
        removed_count = 0
        
        for word, freq in words_with_freq:
            if is_english_or_proper(word, morphology, english_set):
                removed_count += 1
            else:
                filtered_list.append((word, freq))
                
        print(f"  Initial count: {len(words_with_freq)}")
        print(f"  Removed:       {removed_count}")
        print(f"  Remaining:     {len(filtered_list)}")
        
        # Save filtered list back to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Word\tFrequency\n")
            for word, freq in filtered_list:
                f.write(f"{word}\t{freq}\n")
        print(f"Overwrote {filename} with filtered list.")

if __name__ == '__main__':
    main()
