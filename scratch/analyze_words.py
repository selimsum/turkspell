import json
import sys

# Ensure UTF-8 stdout on windows
sys.stdout.reconfigure(encoding='utf-8')

words = [
    "buzdolabınızdaki",
    "gezingede",
    "geçiremeseydi",
    "genetikçi",
    "ipucudur",
    "istirahatinden",
    "kafataslarımızın",
    "kolonileşerek",
    "milihertz",
    "moderatörlerin",
    "moralsizlik",
    "yaşasalardı"
]

with open('zemberek_lexicon.json', 'r', encoding='utf-8') as f:
    lexicon = json.load(f)

# Let's search for matches where the lemma starts with or is inside the lexicon
lex_dict = {entry['lemma'].lower(): entry for entry in lexicon}

print("Searching lexicon:")
for word in words:
    print(f"\nTarget Word: {word}")
    
    # Check if exact lemma in lexicon
    if word in lex_dict:
        print(f"  EXACT MATCH: {lex_dict[word]}")
    
    # Find any lemmas in the lexicon that match the start of the word
    prefix_matches = []
    for l, entry in lex_dict.items():
        if word.startswith(l):
            prefix_matches.append(entry)
    
    if prefix_matches:
        print("  Prefix matches (stems):")
        for m in sorted(prefix_matches, key=lambda x: len(x['lemma']), reverse=True):
            print(f"    {m['lemma']} ({m.get('pos')}) - attributes: {m.get('attributes')}")
    else:
        print("  No prefix matches.")
