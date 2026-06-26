import os
import sys
from collections import Counter

# Reconfigure stdout for UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def get_last_vowel(s):
    vowels = 'aeıioöuüâîûAEIİOÖUÜÂÎÛ'
    for ch in reversed(s):
        if ch in vowels:
            return ch.lower()
    return None

def make_voiced(stem):
    if not stem:
        return stem
    last = stem[-1]
    if last == 'p':
        return stem[:-1] + 'b'
    elif last == 'ç':
        return stem[:-1] + 'c'
    elif last == 't':
        return stem[:-1] + 'd'
    elif last == 'k':
        return stem[:-1] + 'ğ'
    elif last == 'g':
        return stem[:-1] + 'ğ'
    return stem

def make_vowel_drop(stem):
    # Strip last vowel from stem
    # e.g., ağız -> ağz, zehir -> zehr, uzuv -> uzv
    if len(stem) < 3:
        return stem
    vowels = 'aeıioöuüâîû'
    # Find last vowel position
    last_vowel_idx = -1
    for i in range(len(stem) - 1, -1, -1):
        if stem[i] in vowels:
            last_vowel_idx = i
            break
    if last_vowel_idx > 0:
        return stem[:last_vowel_idx] + stem[last_vowel_idx+1:]
    return stem

def make_doubling(stem):
    if not stem:
        return stem
    return stem + stem[-1]

def load_stems_and_variants():
    stems_dict = {} # prefix -> (original_stem, flag, mutation_type)
    
    if not os.path.exists('tr.dic'):
        print("Error: tr.dic not found. Please compile the dictionary first.")
        sys.exit(1)
        
    with open('tr.dic', 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        
    # First line is count
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        if '/' in line:
            stem, flag = line.split('/', 1)
        else:
            stem, flag = line, ""
            
        # Add original stem
        if stem not in stems_dict or len(stems_dict[stem][1]) == 0:
            stems_dict[stem] = (stem, flag, "None")
            
        # Parse flag for mutation categories
        # Noun/Verb voicing flags
        is_voicing = flag in ["5", "6", "15", "16", "105", "106", "115", "116"]
        is_vowel_drop = flag in ["7", "8", "107", "108"]
        is_doubling = flag in ["18", "19", "118", "119"]
        
        # Verb stems end in mak/mek in dictionary, but suffixes attach to root
        root = stem
        is_verb = False
        if flag in ["9", "10", "11", "12", "15", "16", "17", "109", "110", "111", "112", "115", "116"]:
            is_verb = True
            if stem.endswith(('mak', 'mek')):
                root = stem[:-3]
                if root not in stems_dict:
                    stems_dict[root] = (stem, flag, "VerbRoot")
        
        if is_voicing:
            voiced = make_voiced(root)
            if voiced != root:
                stems_dict[voiced] = (stem, flag, "Voicing")
        elif is_vowel_drop:
            dropped = make_vowel_drop(root)
            if dropped != root:
                stems_dict[dropped] = (stem, flag, "VowelDrop")
        elif is_doubling:
            doubled = make_doubling(root)
            stems_dict[doubled] = (stem, flag, "Doubling")
            
    return stems_dict

def analyze_undetected():
    print("Loading dictionary stems...")
    stems_dict = load_stems_and_variants()
    print(f"Loaded {len(stems_dict)} stem variants.")
    
    undetected_file = 'undetected_words_turkspell.txt'
    if not os.path.exists(undetected_file):
        print(f"Error: {undetected_file} not found.")
        sys.exit(1)
        
    with open(undetected_file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        
    undetected_words = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if parts:
            word = parts[0]
            count = 1
            if len(parts) > 1:
                if parts[1].isdigit():
                    count = int(parts[1])
                else:
                    continue # Skip header or invalid line
            undetected_words.append((word, count))
            
    print(f"Analyzing {len(undetected_words)} undetected words...")
    
    missing_stems = [] # list of (word, count)
    suffix_gaps = []   # list of (word, stem, suffix, mutation, count)
    
    # Common short stems that are allowed
    short_stems = {'su', 'ek', 'et', 'al', 'ol', 'ye', 'de', 'ne', 've', 'en', 'bu', 'o', 'ki', 'mi'}
    
    stems_dict_lower = {k.lower(): v for k, v in stems_dict.items()}
    
    for word, count in undetected_words:
        word_lower = word.lower()
        
        # Find all prefix matches via O(1) hash map lookups of prefixes
        best_prefix = None
        best_info = None
        
        for i in range(len(word_lower), 0, -1):
            prefix_candidate = word_lower[:i]
            if prefix_candidate in stems_dict_lower:
                if len(prefix_candidate) >= 3 or word_lower == prefix_candidate or prefix_candidate in short_stems:
                    best_prefix = prefix_candidate
                    best_info = stems_dict_lower[prefix_candidate]
                    break
                    
        if best_prefix is None:
            missing_stems.append((word, count))
        else:
            orig_stem, flag, mutation = best_info
            suffix = word[len(best_prefix):]
            if not suffix:
                # Exact match but probably rejected due to some other constraint (like capitalization or flag conflict)
                suffix_gaps.append((word, orig_stem, "", mutation, count))
            else:
                suffix_gaps.append((word, orig_stem, suffix, mutation, count))
                
    # Sort missing stems by frequency
    missing_stems.sort(key=lambda x: x[1], reverse=True)
    
    # Aggregate suffix gaps
    suffix_counter = Counter()
    suffix_examples = {}
    for word, stem, suffix, mutation, count in suffix_gaps:
        if suffix:
            suffix_counter[suffix] += count
            if suffix not in suffix_examples:
                suffix_examples[suffix] = []
            suffix_examples[suffix].append(f"{word} (stem: {stem})")
            
    print("\n======================================== REPORT ========================================")
    print(f"Total Undetected Words analyzed: {len(undetected_words)}")
    print(f"Words with Missing Stems (Vocabulary Gaps): {len(missing_stems)}")
    print(f"Words with Known Stems (Suffix/Grammar Gaps): {len(suffix_gaps)}")
    print("========================================================================================")
    
    print("\nTOP 20 MISSING STEMS (VOCABULARY GAPS):")
    for word, count in missing_stems[:20]:
        print(f"  {word:<25} (Count: {count})")
        
    print("\nTOP 20 MISSING SUFFIX COMBINATIONS (GRAMMAR GAPS):")
    for suffix, count in suffix_counter.most_common(20):
        examples = ", ".join(suffix_examples[suffix][:3])
        print(f"  -{suffix:<24} (Count: {count}) | Examples: {examples}")

if __name__ == "__main__":
    analyze_undetected()
