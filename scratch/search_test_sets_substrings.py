import os

SUBSTRINGS = [
    "kağıt", "kağıd", "hükumet", "aşık", "rüzgar", "hikaye", "dükkan", "tezgah",
    "mekan", "imkan", "inkar", "hizmetkar", "kanaatkar", "dahiyane", "efkarlan",
    "kaşane", "lapseki", "şehriyar", "hallice", "kanunusani", "katibiadil",
    "arzuhal", "cinsi", "fenni", "merkezileş", "millileş", "takribi",
    "resmi", "milli", "dini", "siyasi", "tarihi", "hukuki", "askeri", "fiili",
    "akli", "örfi", "baki", "asgari", "azami", "hala", "dahi", "kamil", "kabil",
    "kabus", "kafi", "kafir", "kahya", "kainat", "katip", "lakin", "melik",
    "rekat", "sukut", "zeka"
]

def search_in_file(path):
    if not os.path.exists(path):
        return
    print(f"\nSearching in {path}:")
    found_counts = {sub: 0 for sub in SUBSTRINGS}
    examples = {sub: [] for sub in SUBSTRINGS}
    
    with open(path, 'r', encoding='utf-8') as f:
        # skip header
        next(f)
        for line in f:
            line_lower = line.lower()
            for sub in SUBSTRINGS:
                if sub in line_lower:
                    found_counts[sub] += 1
                    if len(examples[sub]) < 3:
                        examples[sub].append(line.strip())
                        
    for sub, count in sorted(found_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {sub}: {count} occurrences")
            print(f"    Examples: {examples[sub]}")

def main():
    search_in_file("official_test.csv")
    search_in_file("official_test_v2.csv")

if __name__ == "__main__":
    main()
