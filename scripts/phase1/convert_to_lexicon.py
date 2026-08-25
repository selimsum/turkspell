import json
import os

input_file = r'c:\gemini\turkspell\scripts\phase1\data\classified_stems.json'
output_file = r'c:\gemini\turkspell\lexicons\oscar_parsed_candidates.json'

with open(input_file, 'r', encoding='utf-8') as f:
    classified_stems = json.load(f)

lexicon = []
for word, meta_str in classified_stems.items():
    try:
        meta = json.loads(meta_str)
        if meta.get('valid'):
            pos = meta.get('pos', 'Noun')
            
            # Map acronyms to ProperNoun as per custom_abbreviations.json structure
            if pos == 'Acronym':
                pos = 'ProperNoun'
            
            lexicon.append({
                "lemma": word,
                "pos": pos,
                "attributes": []
            })
    except Exception as e:
        pass

# Deduplicate just in case
unique_lexicon = {item['lemma']: item for item in lexicon}.values()
final_lexicon = list(unique_lexicon)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(final_lexicon, f, ensure_ascii=False, indent=2)

print(f"Successfully converted {len(final_lexicon)} valid stems to lexicon format at {output_file}")
