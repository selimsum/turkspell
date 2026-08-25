import os

def load_stems(dic_path="../../tr.dic"):
    print(f"Loading dictionary lemmas from {dic_path}...")
    valid_stems = set()
    
    with open(dic_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.isdigit(): continue
            
            lemma = line.split('/')[0]
            
            # Extract verb stems
            if lemma.endswith('mak') or lemma.endswith('mek'):
                stem = lemma[:-3]
            else:
                stem = lemma
                
            valid_stems.add(stem)
            
            # Add consonant mutations (voicing) for robust matching
            if stem.endswith('p'): valid_stems.add(stem[:-1] + 'b')
            elif stem.endswith('ç'): valid_stems.add(stem[:-1] + 'c')
            elif stem.endswith('t'): valid_stems.add(stem[:-1] + 'd')
            elif stem.endswith('k'): 
                valid_stems.add(stem[:-1] + 'ğ')
                valid_stems.add(stem[:-1] + 'g')
                
    # Sort stems by length descending so we match the longest stem first
    print(f"Loaded {len(valid_stems):,} robust stems.")
    return valid_stems

def split_missing_words(stems, missing_path="data/missing_words.txt"):
    print(f"Splitting {missing_path} based on stem presence...")
    
    with_stem = []
    no_stem = []
    
    with open(missing_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            parts = line.strip().split('\t')
            if len(parts) != 2: continue
            word, count = parts[0], int(parts[1])
            
            # Normalize for case-insensitive matching (proper nouns are lowercase in tr.dic)
            word_lower = word.replace('İ', 'i').replace('I', 'ı').replace('Î', 'î').replace('Â', 'â').replace('Û', 'û').lower()
            
            # O(L) check: for each prefix of the word, check if it's in the valid_stems SET
            # We enforce that the stem must be at least 2 characters.
            found_stem = False
            for i in range(2, len(word_lower) + 1):
                if word_lower[:i] in stems:
                    found_stem = True
                    break
                    
            if found_stem:
                if count > 5:
                    with_stem.append((word, count))
            else:
                if count > 50:
                    no_stem.append((word, count))
                    
            if i > 0 and i % 50000 == 0:
                print(f"Processed {i} missing words...")

    print("\n--- RESULTS ---")
    print(f"Found {len(with_stem):,} words (freq > 5) WITH recognized stems (Missing Rules).")
    print(f"Found {len(no_stem):,} words (freq > 50) with NO recognized stem (Missing Roots).")
    
    with open("data/missing_rules_candidates.txt", "w", encoding="utf-8") as f:
        for w, c in with_stem: f.write(f"{w}\t{c}\n")
        
    with open("data/missing_roots_candidates.txt", "w", encoding="utf-8") as f:
        for w, c in no_stem: f.write(f"{w}\t{c}\n")
        
    print("\nSaved to data/missing_rules_candidates.txt and data/missing_roots_candidates.txt")

if __name__ == "__main__":
    stems = load_stems()
    split_missing_words(stems)
