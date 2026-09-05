import json
import os
from pathlib import Path

def tr_lower(text: str) -> str:
    return text.replace('I', 'ı').replace('İ', 'i').lower()

BASE_DIR = Path(r"c:\gemini\turkspell")
NAMES_PATH = BASE_DIR / "lexicons" / "custom_names.json"
TDK_PATH = BASE_DIR / "raw_data" / "tdk_words.txt"

with open(NAMES_PATH, encoding='utf-8') as f:
    names = json.load(f)

print(f"Original entries in custom_names.json: {len(names)}")

with open(TDK_PATH, encoding='utf-8') as f:
    tdk_words = {tr_lower(line.strip().split('/')[0]) for line in f if line.strip()}

INTL_APOS_BRANDS = {
    "McDonald's", "Domino's", "Wendy's", "Levi's", "Macy's", "Hardee's",
    "O'Connor", "O'Neill", "D'Angelo", "L'Oréal", "O'Flaherty"
}
ascii_map = str.maketrans('cgiosu', 'çğıöşü')

cleaned_names = []
seen_lemmas = set()
dropped_counts = {}

for item in names:
    lem = item.get('lemma', '').strip()
    if not lem:
        continue
    
    # 1. Single character noise
    if len(lem) == 1:
        dropped_counts['single_char'] = dropped_counts.get('single_char', 0) + 1
        continue
        
    # 2. Length <= 2 noise (keep valid names / brands like Su, Ay, HP, LG)
    if len(lem) <= 2 and lem not in ('Su', 'Ay', 'HP', 'LG'):
        dropped_counts['len_le_2_noise'] = dropped_counts.get('len_le_2_noise', 0) + 1
        continue
        
    # 3. Known junk stems or numeric junk
    if lem in ('Gur', 'A101', 'N11'):
        dropped_counts['junk_or_numeric'] = dropped_counts.get('junk_or_numeric', 0) + 1
        continue
        
    # 4. Inflected entries with apostrophes
    if "'" in lem:
        if lem in INTL_APOS_BRANDS or lem.startswith("O'") or lem.startswith("D'"):
            pass  # keep genuine international brand/family name
        else:
            dropped_counts['inflected_apostrophe'] = dropped_counts.get('inflected_apostrophe', 0) + 1
            # Extract base lemma (e.g. Schneider from Schneider'e)
            base = lem.split("'")[0].strip()
            if len(base) >= 3 and base[0].isupper() and not base.isupper() and base not in seen_lemmas:
                cleaned_names.append({'lemma': base, 'pos': 'ProperNoun', 'attributes': []})
                seen_lemmas.add(base)
            continue
            
    # 5. ALL CAPS ASCII common words (headline scraper noise)
    if lem.isupper() and len(lem) >= 3:
        lower_lem = lem.lower()
        if lower_lem in tdk_words or tr_lower(lem) in tdk_words or lower_lem.translate(ascii_map) in tdk_words:
            if lem not in ('THY', 'PTT', 'TEB', 'TUSAŞ', 'TOGG', 'BİM', 'AMD', 'BMW', 'KFC', 'FOX', 'NVIDIA', 'FIAT', 'MESA', 'PAOK', 'JAMA'):
                dropped_counts['all_caps_common_word'] = dropped_counts.get('all_caps_common_word', 0) + 1
                continue
                
    if lem in seen_lemmas:
        dropped_counts['duplicate'] = dropped_counts.get('duplicate', 0) + 1
        continue
        
    seen_lemmas.add(lem)
    cleaned_names.append(item)

# Sort alphabetically by lemma
cleaned_names.sort(key=lambda x: x['lemma'])

print(f"Cleaned entries count: {len(cleaned_names)}")
for reason, count in dropped_counts.items():
    print(f"  Dropped {reason}: {count}")

# Backup original
backup_path = BASE_DIR / "lexicons" / "custom_names.json.bak"
if not backup_path.exists():
    NAMES_PATH.rename(backup_path)
    print(f"Backed up original to {backup_path}")

with open(NAMES_PATH, 'w', encoding='utf-8') as f:
    json.dump(cleaned_names, f, indent=2, ensure_ascii=False)

print(f"Successfully wrote cleaned lexicon to {NAMES_PATH}")
