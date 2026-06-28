import os
import subprocess

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

def filter_undetected_report():
    report_path = 'undetected_words.txt'
    english_path = 'english_words_large.txt'
    
    if not os.path.exists(report_path):
        print(f"Error: {report_path} not found.")
        return
        
    if not os.path.exists(english_path):
        print(f"Error: {english_path} not found.")
        return

    # 1. Load English words
    print("Loading English word list...")
    with open(english_path, 'r', encoding='utf-8') as f:
        english = {turkish_lowercase(line.strip()) for line in f if line.strip()}
        
    # 2. Read the undetected report
    print("Reading undetected_words.txt...")
    header = ""
    rows = []
    with open(report_path, 'r', encoding='utf-8') as f:
        header = f.readline().strip()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                word = parts[0]
                freq = int(parts[1])
                in_root = parts[2] if len(parts) > 2 else "False"
                rows.append((word, freq, in_root))

    print(f"Initial undetected words: {len(rows)}")

    # 3. Batch check lowercase forms with Hunspell
    words_to_check = []
    for word, _, _ in rows:
        words_to_check.append(turkish_lowercase(word))
        
    print("Running Hunspell batch check on lowercased forms...")
    p = subprocess.Popen(['hunspell', '-d', 'tr', '-l'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8')
    out, _ = p.communicate('\n'.join(words_to_check) + '\n')
    unrecognized_lowercased = set(out.splitlines())

    # 4. Filter
    filtered_rows = []
    removed_english = 0
    removed_brands = 0
    removed_proper = 0

    for word, freq, in_root in rows:
        word_lower = turkish_lowercase(word)
        
        # A. Check brand
        is_brand = False
        for brand in COMMON_BRANDS:
            if brand in word_lower:
                is_brand = True
                break
        if is_brand:
            removed_brands += 1
            continue
            
        # B. Check English list
        if word_lower in english:
            removed_english += 1
            continue
            
        # C. Check Proper Name / Acronym / Abbreviation
        # If it starts with an uppercase letter, and its lowercase form is NOT recognized by Hunspell,
        # then it is a proper name, acronym, or foreign entity.
        first_char = word[0] if word else ''
        starts_upper = first_char.isupper() or first_char in 'ÇĞİÖŞÜ'
        
        if starts_upper:
            if word_lower in unrecognized_lowercased:
                removed_proper += 1
                continue

        filtered_rows.append((word, freq, in_root))

    print(f"\nFiltering complete:")
    print(f"  Removed English words:       {removed_english}")
    print(f"  Removed Brand names:         {removed_brands}")
    print(f"  Removed Proper Names/Acronyms:{removed_proper}")
    print(f"  Remaining Turkish words:     {len(filtered_rows)}")

    # 5. Overwrite the report
    print(f"Saving filtered report to {report_path}...")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Word\tFrequency\tInRootWordList\n")
        for word, freq, in_root in filtered_rows:
            f.write(f"{word}\t{freq}\t{in_root}\n")

    # Print top 50 remaining undetected words
    print("\nTop 50 Remaining Undetected Words by Frequency:")
    print("=" * 65)
    print(f"{'No':<4} | {'Word':<25} | {'Frequency':<10} | {'In Root List':<12}")
    print("-" * 65)
    for idx, (word, freq, in_root) in enumerate(filtered_rows[:50], 1):
        safe_word = word.encode('cp1254', errors='replace').decode('cp1254')
        print(f"{idx:<4} | {safe_word:<25} | {freq:<10} | {str(in_root):<12}")

if __name__ == "__main__":
    filter_undetected_report()
