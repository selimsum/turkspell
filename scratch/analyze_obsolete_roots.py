import json
import os
import re
from collections import Counter
import sys

# Characters to strip from start/end of tokens
STRIP_CHARS = '"\'’‘“”.?!,:;*()[]{}<>«»/\\#%&+=_-–—~|`'

def tr_lower(text):
    return text.replace("I", "ı").replace("İ", "i").lower()

def clean_token(token):
    token = token.strip(STRIP_CHARS)
    if not token:
        return None
    if any(c.isdigit() for c in token):
        return None
    if not any(c.isalpha() for c in token):
        return None
    return token

def get_lemma_variations(lemma, pos):
    lemma = tr_lower(lemma)
    variations = {lemma}
    
    voicing_map = {'p': 'b', 'ç': 'c', 't': 'd', 'k': 'ğ'}
    voiced_lemma = lemma
    if lemma and lemma[-1] in voicing_map:
        voiced_lemma = lemma[:-1] + voicing_map[lemma[-1]]
        variations.add(voiced_lemma)
        
    if pos == 'Verb':
        root = lemma[:-3] if lemma.endswith(('mak', 'mek')) else lemma
        voiced_root = root
        if root and root[-1] in voicing_map:
            voiced_root = root[:-1] + voicing_map[root[-1]]
            
        variations.add(root)
        variations.add(voiced_root)
        
        verb_suffixes = [
            'mak', 'mek', 'ma', 'me', 'yor', 'ıyor', 'iyor', 'uyor', 'üyor',
            'dı', 'di', 'du', 'dü', 'tı', 'ti', 'tu', 'tü',
            'acak', 'ecek', 'ar', 'er', 'ır', 'ir', 'ur', 'ür', 'maz', 'mez',
            'meli', 'malı', 'se', 'sa'
        ]
        for s in verb_suffixes:
            r = voiced_root if s[0] in 'aeıiouü' else root
            variations.add(r + s)
    else:
        noun_suffixes = [
            'lar', 'ler',
            'da', 'de', 'ta', 'te', 'dan', 'den', 'tan', 'ten', 'la', 'le', 'ca', 'ce',
            'ı', 'i', 'u', 'ü', 'a', 'e', 'ın', 'in', 'un', 'ün',
            'yı', 'yi', 'yu', 'yü', 'ya', 'ye', 'nın', 'nin', 'nun', 'nün', 'yla', 'yle'
        ]
        for s in noun_suffixes:
            stem = voiced_lemma if s[0] in 'aeıiouü' else lemma
            variations.add(stem + s)
            
    return variations

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    # Paths are relative to the workspace root
    scratch_dir = os.path.dirname(os.path.abspath(__file__))
    workspace = os.path.dirname(scratch_dir)
    lexicon_path = os.path.join(workspace, 'zemberek_lexicon.json')
    wiki_path = os.path.join(workspace, 'data', 'wiki_corpus.txt')
    mag_path = os.path.join(workspace, 'data', 'magazine_corpus.txt')
    
    if not os.path.exists(lexicon_path):
        print(f"Error: {lexicon_path} not found.")
        return
        
    print("Loading lexicon...")
    with open(lexicon_path, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)
    print(f"Loaded {len(lexicon)} entries from lexicon.")
    
    lemmas_to_check = []
    for item in lexicon:
        lemma = item.get('lemma')
        pos = item.get('pos')
        if lemma:
            lemmas_to_check.append((lemma, pos))
            
    print("Generating variations for all lemmas...")
    variation_to_lemmas = {}
    
    for idx, (lemma, pos) in enumerate(lemmas_to_check):
        vars_set = get_lemma_variations(lemma, pos)
        for v in vars_set:
            if v not in variation_to_lemmas:
                variation_to_lemmas[v] = []
            variation_to_lemmas[v].append(idx)
            
    word_counts = Counter()
    
    def process_corpus(path):
        if not os.path.exists(path):
            print(f"Warning: {path} not found.")
            return
        print(f"Processing corpus {path}...")
        total_tokens = 0
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                for token in line.split():
                    cleaned = clean_token(token)
                    if cleaned:
                        lowered = tr_lower(cleaned)
                        if lowered in variation_to_lemmas:
                            word_counts[lowered] += 1
                        total_tokens += 1
        print(f"Processed {total_tokens} tokens.")
        
    process_corpus(mag_path)
    process_corpus(wiki_path)
    
    print("Calculating frequencies for each lemma...")
    lemma_frequencies = [0] * len(lemmas_to_check)
    for var, count in word_counts.items():
        for idx in variation_to_lemmas[var]:
            lemma_frequencies[idx] += count
            
    freq_0 = []
    freq_1 = []
    freq_2 = []
    obsolete_lemmas = set()
    
    for idx, (lemma, pos) in enumerate(lemmas_to_check):
        freq = lemma_frequencies[idx]
        lemma_lower = tr_lower(lemma)
        if freq == 0:
            freq_0.append((lemma, pos))
            obsolete_lemmas.add(lemma_lower)
        elif freq == 1:
            freq_1.append((lemma, pos))
            # Do not add to obsolete_lemmas so they can be suggested
        elif freq == 2:
            freq_2.append((lemma, pos))
            # Do not add to obsolete_lemmas so they can be suggested
            
    print(f"Found {len(freq_0)} stems with frequency = 0 (freq < 1)")
    print(f"Found {len(freq_1)} stems with frequency = 1")
    print(f"Found {len(freq_2)} stems with frequency = 2")
    
    # Save lists to the local scratch directory
    out_dir = scratch_dir
    os.makedirs(out_dir, exist_ok=True)
    
    with open(os.path.join(out_dir, 'obsolete_freq_0.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(freq_0), f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(out_dir, 'obsolete_freq_1.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(freq_1), f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, 'obsolete_freq_2.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(freq_2), f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, 'obsolete_lemmas.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(list(obsolete_lemmas)), f, ensure_ascii=False, indent=2)
        
    print("Saved lists successfully.")

if __name__ == '__main__':
    main()
