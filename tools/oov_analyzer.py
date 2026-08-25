import os
import sys
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

def init_worker():
    global morphology
    from zemberek import TurkishMorphology
    import logging
    logging.getLogger('zemberek').setLevel(logging.ERROR)
    morphology = TurkishMorphology.create_with_defaults()

def analyze_chunk(words):
    global morphology
    results_a = []
    results_b = []
    results_c = []
    
    for word, freq in words:
        try:
            analyses = morphology.analyze(word)
            if not analyses:
                results_c.append((word, freq))
                continue
                
            # Filter out proper nouns
            is_proper = False
            for a in analyses:
                if a.item.secondary_pos and a.item.secondary_pos.short_form == 'Prop':
                    is_proper = True
                    break
            
            if is_proper:
                continue # Skip proper nouns entirely
                
            # Take the first valid analysis
            first_valid = None
            for a in analyses:
                first_valid = a
                break
                
            lemma = first_valid.item.lemma
            analysis_str = first_valid.format_string()
            
            # We don't have dic_roots in the worker, so we just return the raw valid items
            # The main process will split them into Category A and B
            results_a.append({'word': word, 'freq': freq, 'lemma': lemma, 'analysis': analysis_str})
            
        except Exception as e:
            results_c.append((word, freq))
            
    return results_a, results_c

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    missing_path = os.path.join(root_dir, 'scripts', 'phase1', 'data', 'missing_words.txt')
    dic_path = os.path.join(root_dir, 'tr.dic')
    
    # Load dic roots
    dic_roots = set()
    with open(dic_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '/' in line:
                word = line.split('/')[0]
                dic_roots.add(word)
                
    print(f"Loaded {len(dic_roots)} dictionary roots.")
    
    # Load missing words
    words = []
    with open(missing_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                words.append((parts[0], int(parts[1])))
                
    print(f"Loaded {len(words)} missing words to analyze.")
    
    chunk_size = 5000
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    
    category_a = []
    category_b = []
    category_c = []
    
    print("Starting multiprocessing analysis...")
    start_t = time.time()
    
    with ProcessPoolExecutor(max_workers=8, initializer=init_worker) as executor:
        futures = {executor.submit(analyze_chunk, chunk): i for i, chunk in enumerate(chunks)}
        
        completed = 0
        for future in as_completed(futures):
            res_a, res_c = future.result()
            
            for item in res_a:
                # Need lowercasing because lemmas in tr.dic are lowercase
                # Wait, zemberek lemma might be lowercase anyway for non-prop
                lemma = item['lemma'].replace('I', 'ı').replace('İ', 'i').lower()
                if lemma in dic_roots:
                    category_a.append(item)
                else:
                    category_b.append(item)
                    
            for item in res_c:
                category_c.append(item)
                
            completed += 1
            if completed % 10 == 0:
                print(f"Progress: {completed}/{len(chunks)} chunks... ({(completed/len(chunks)*100):.1f}%)")
                
    elapsed = time.time() - start_t
    print(f"Analysis completed in {elapsed:.2f} seconds.")
    
    print(f"Category A (Missing Rules): {len(category_a)}")
    print(f"Category B (Missing Roots): {len(category_b)}")
    print(f"Category C (Garbage/Typos): {len(category_c)}")
    
    # Save results
    out_dir = os.path.join(root_dir, 'data', 'phase4_analysis')
    os.makedirs(out_dir, exist_ok=True)
    
    with open(os.path.join(out_dir, 'category_a.json'), 'w', encoding='utf-8') as f:
        json.dump(category_a, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(out_dir, 'category_b.json'), 'w', encoding='utf-8') as f:
        json.dump(category_b, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(out_dir, 'category_c.json'), 'w', encoding='utf-8') as f:
        json.dump(category_c, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
