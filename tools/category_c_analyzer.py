import os
import json

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cat_c_path = os.path.join(root_dir, 'data', 'phase4_analysis', 'category_c.json')
    
    if not os.path.exists(cat_c_path):
        print("Category C data not found.")
        return
        
    with open(cat_c_path, 'r', encoding='utf-8') as f:
        category_c = json.load(f)
        
    print(f"Loaded {len(category_c)} entries in Category C (Garbage/Typos).")
    
    # Sort by frequency
    sorted_words = sorted(category_c, key=lambda x: x[1], reverse=True)
    
    print("\n--- TOP 100 INVALID WORDS ---")
    for i, (word, freq) in enumerate(sorted_words[:100]):
        print(f"{i+1:3}. {word:<20} {freq:>10,}")
        
if __name__ == '__main__':
    main()
