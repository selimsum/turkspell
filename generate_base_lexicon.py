import json
from zemberek import TurkishMorphology

def generate_base_lexicon():
    print("Initializing Zemberek Morphological Analyzer...")
    morphology = TurkishMorphology.create_with_defaults()
    lexicon = morphology.lexicon
    
    combined_lexicon = {}
    
    print("Extracting lemmas and attributes from Zemberek's built-in lexicon...")
    for item in lexicon.item_set:
        lemma = item.lemma
        pos = item.primary_pos.name if item.primary_pos else "Noun"
        attrs = [attr.name for attr in item.attributes] if item.attributes else []
        
        # Key by lemma + POS to prevent collision of homonyms with different POS
        key = f"{lemma}/{pos}"
        combined_lexicon[key] = {
            "lemma": lemma,
            "pos": pos,
            "attributes": attrs
        }
        
    print(f"Extracted {len(combined_lexicon)} entries from Zemberek.")
    
    output_path = "zemberek_lexicon.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(list(combined_lexicon.values()), f, ensure_ascii=False, indent=2)
        
    print(f"Saved lexicon database to {output_path}")

if __name__ == "__main__":
    generate_base_lexicon()
