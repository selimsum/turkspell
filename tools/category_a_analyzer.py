import os
import json
from collections import Counter

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cat_a_path = os.path.join(root_dir, 'data', 'phase4_analysis', 'category_a.json')
    
    if not os.path.exists(cat_a_path):
        print("Category A data not found.")
        return
        
    with open(cat_a_path, 'r', encoding='utf-8') as f:
        category_a = json.load(f)
        
    print(f"Loaded {len(category_a)} entries in Category A (Missing Rules).")
    
    # Extract missing suffix patterns
    analysis_freqs = Counter()
    for item in category_a:
        analysis = item['analysis']
        # The format is typically: [lemma:Noun] Noun+A3sg+P3sg+Loc
        # Let's extract the part after the closing bracket ]
        if ']' in analysis:
            morphology = analysis.split(']', 1)[1].strip()
            # Often it's structured like Noun+A3sg+P3sg+Loc
            # Let's count these whole morphological patterns
            analysis_freqs[morphology] += item['freq']
            
    sorted_patterns = analysis_freqs.most_common(100)
    
    print("\n--- TOP 100 MISSING MORPHOLOGICAL PATTERNS ---")
    for i, (pattern, freq) in enumerate(sorted_patterns):
        print(f"{i+1:3}. {pattern:<40} {freq:>10,}")
        
if __name__ == '__main__':
    main()
