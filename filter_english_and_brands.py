from zemberek import TurkishMorphology
import os

# Predefined list of popular global and Turkish brand names/brand tokens to exclude
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

def filter_list():
    print("Initializing Zemberek Morphological Analyzer...")
    morphology = TurkishMorphology.create_with_defaults()

    english_path = 'english_words_large.txt'
    if not os.path.exists(english_path):
        print(f"Error: {english_path} not found.")
        return

    print("Loading English word list...")
    with open(english_path, 'r', encoding='utf-8') as f:
        english = {line.strip().lower() for line in f if line.strip()}

    missing_path = 'missing_from_zemberek.txt'
    if not os.path.exists(missing_path):
        print(f"Error: {missing_path} not found.")
        return

    print(f"Reading {missing_path}...")
    with open(missing_path, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]

    filtered_words = []
    removed_english = []
    removed_brands = []

    print("Filtering words...")
    for word in words:
        word_lower = turkish_lowercase(word)
        
        # 1. Check if it's a known brand name (partially or fully matching brand list)
        is_brand = False
        for brand in COMMON_BRANDS:
            if brand in word_lower:
                is_brand = True
                break
        
        if is_brand:
            removed_brands.append(word)
            continue

        # 2. Check if it's in the English dictionary AND Zemberek cannot parse it
        if word_lower in english:
            # Check Zemberek morphological analysis
            parses = list(morphology.analyze(word_lower))
            if not parses:
                removed_english.append(word)
                continue

        filtered_words.append(word)

    print(f"\nFiltering complete:")
    print(f"  Total words initially:     {len(words)}")
    print(f"  Removed English words:     {len(removed_english)}")
    print(f"  Removed brand names:       {len(removed_brands)}")
    print(f"  Remaining Turkish words:   {len(filtered_words)}")

    print(f"Overwriting {missing_path}...")
    with open(missing_path, 'w', encoding='utf-8') as f:
        for w in filtered_words:
            f.write(w + '\n')
            
    print("Done!")

if __name__ == "__main__":
    filter_list()
