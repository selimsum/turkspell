import sys

words = [
    "abartılmak", "abartılma", "abdest", "aday", "adımlamak", "akıl", "akropol",
    "almak", "alkışlanmak", "alkışlanma", "almacı", "alt", "alıkoymak", "alışık",
    "amaçlamak", "anahtar", "anayasa", "anlatabilmek", "anlamak", "anlaşmak",
    "anne", "arabesk", "ara", "aroma", "artmak", "arttırmak", "artırmak",
    "arzuhâl", "asfalt", "atmak", "atanmak", "ateşlenmek", "atık", "atılmak",
    "avukat", "ayrılmak", "ayrılık", "ayrıntı", "ayvacı", "ayırmak", "açıklamak"
]

def search_dic(word, filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if '/' in line:
                w, flags = line.strip().split('/', 1)
            else:
                w, flags = line.strip(), ""
            if w == word:
                results.append((w, flags))
    return results

def main():
    print(f"{'Word':<15} | {'tr.dic Flags':<20} | {'tr_v2.dic Flags'}")
    print("-" * 70)
    for w in words:
        v1_entries = search_dic(w, 'tr.dic')
        v2_entries = search_dic(w, 'tr_v2.dic')
        
        v1_str = ", ".join(f"/{f}" for _, f in v1_entries) if v1_entries else "NOT FOUND"
        v2_str = ", ".join(f"/{f}" for _, f in v2_entries) if v2_entries else "NOT FOUND"
        print(f"{w:<15} | {v1_str:<20} | {v2_str}")

if __name__ == '__main__':
    main()
