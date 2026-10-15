import json
import re

with open('raw_data/triage/colab_parsed_terimler.json', encoding='utf-8') as f:
    parsed = json.load(f)

# Load TDK GTS words to identify already known words
with open('raw_data/tdk_words.txt', encoding='utf-8') as f:
    tdk_words = set(line.strip().split('/')[0].lower() for line in f if line.strip())

valid = [x for x in parsed if x.get('lemma')]
new_terms = []
for x in valid:
    lem = x['lemma'].strip().lower()
    if lem in tdk_words:
        continue
    # must be all turkish alpha
    if not all(c in 'abcçdefgğhıijklmnoöprsştuüvyzâîû' for c in lem):
        continue
    new_terms.append(x)

print(f'Total new terms from parsed colab: {len(new_terms)}')

# Sample 50 new terms
for item in new_terms[100:150]:
    print(f"{item['word']} -> {item['lemma']} [{item.get('pos')}] {item.get('attributes')}")
