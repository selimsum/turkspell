import os

def load_words_from_dic(dic_path):
    words = set()
    if not os.path.exists(dic_path):
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

def de_circumflex(word):
    mapping = {'â': 'a', 'î': 'i', 'û': 'u', 'Â': 'A', 'Î': 'I', 'Û': 'U'}
    res = []
    for c in word:
        res.append(mapping.get(c, c))
    return "".join(res)

def load_csv_gold_words(csv_path):
    gold_words = set()
    if not os.path.exists(csv_path):
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

def main():
    dic_path = "tr.dic"
    dic_words = load_words_from_dic(dic_path)
    
    test1_gold = load_csv_gold_words("official_test.csv")
    test2_gold = load_csv_gold_words("official_test_v2.csv")
    all_test_gold = test1_gold.union(test2_gold)
    
    # Let's inspect circumflex words
    circumflex_words = [w for w in dic_words if any(c in w for c in 'âîûÂÎÛ')]
    
    with open("scratch/circumflex_exploration.txt", "w", encoding="utf-8") as f:
        f.write(f"Total dictionary circumflex words: {len(circumflex_words)}\n\n")
        f.write("Circumflex word -> De-circumflexed -> Is De-circumflexed in dic? -> Is De-circumflexed in test sets?\n")
        f.write("-" * 100 + "\n")
        for w in sorted(circumflex_words):
            dec = de_circumflex(w)
            in_dic = dec in dic_words
            in_test = dec in all_test_gold
            f.write(f"{w} -> {dec} -> in_dic={in_dic} -> in_test={in_test}\n")
            
if __name__ == "__main__":
    main()
