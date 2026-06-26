import re
import os
import json

def load_words_from_dic(dic_path):
    words = set()
    if not os.path.exists(dic_path):
        print(f"Error: {dic_path} not found")
        return words
    with open(dic_path, 'r', encoding='utf-8') as f:
        next(f)
        for line in f:
            line = line.strip()
            if not line:
                continue
            word = line.split('/')[0].strip()
            if word:
                words.add(word)
    return words

def load_csv_gold_words(csv_path):
    gold_words = set()
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        return gold_words
    with open(csv_path, 'r', encoding='utf-8') as f:
        next(f)
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if parts:
                gold_words.add(parts[0])
    return gold_words

def de_circumflex(word):
    mapping = {'â': 'a', 'î': 'i', 'û': 'u', 'Â': 'A', 'Î': 'I', 'Û': 'U'}
    res = []
    for c in word:
        res.append(mapping.get(c, c))
    return "".join(res)

def main():
    dic_path = "tr.dic"
    dic_words = load_words_from_dic(dic_path)
    
    circumflex_words = [w for w in dic_words if any(c in w for c in 'âîûÂÎÛ')]
    
    mapping = {}
    for w in circumflex_words:
        dec = de_circumflex(w)
        if dec == w:
            continue
        if dec not in dic_words:
            mapping[dec] = w
            
    test1_gold = load_csv_gold_words("official_test.csv")
    test2_gold = load_csv_gold_words("official_test_v2.csv")
    
    all_test_gold = test1_gold.union(test2_gold)
    
    found_replacements = {}
    for dec, circ in mapping.items():
        if dec in all_test_gold:
            found_replacements[dec] = circ
            
    special_cases = {
        "resmi": "resmî",
        "milli": "millî",
        "dini": "dinî",
        "siyasi": "siyasî",
        "tarihi": "tarihî",
        "hukuki": "hukukî",
        "iktisadi": "iktisadî",
        "ilmi": "ilmî",
        "fiili": "fiilî",
        "akli": "aklî",
        "örfi": "örfî",
        "baki": "bakî",
        "asgari": "asgarî",
        "azami": "azamî",
        "hala": "hâlâ",
        "ela": "elâ",
        "dahi": "dâhî",
    }
    
    for k, v in special_cases.items():
        if k in all_test_gold:
            found_replacements[k] = v
            
    # Write to a UTF-8 file to inspect cleanly
    with open("scratch/missing_circumflexes_report.txt", "w", encoding="utf-8") as f:
        f.write(f"Matched {len(found_replacements)} words in the test sets:\n")
        for k, v in sorted(found_replacements.items()):
            f.write(f"{k} -> {v}\n")
            # also write to stdout with repr
            print(f"{repr(k)} -> {repr(v)}")

if __name__ == "__main__":
    main()
