import os
import json
from collections import Counter

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cat_b_path = os.path.join(root_dir, 'data', 'phase4_analysis', 'category_b.json')
    
    if not os.path.exists(cat_b_path):
        print("Category B data not found.")
        return
        
    with open(cat_b_path, 'r', encoding='utf-8') as f:
        category_b = json.load(f)
        
    print(f"Loaded {len(category_b)} entries in Category B.")
    
    # Count root frequencies
    root_freqs = {}
    for item in category_b:
        lemma = item['lemma']
        root_freqs[lemma] = root_freqs.get(lemma, 0) + item['freq']
        
    # Sort by frequency
    sorted_roots = sorted(root_freqs.items(), key=lambda x: x[1], reverse=True)
    
    print("\n--- TOP 100 NEW ROOTS ---")
    for i, (root, freq) in enumerate(sorted_roots[:100]):
        print(f"{i+1:3}. {root:<20} {freq:>10,}")
        
if __name__ == '__main__':
    main()
