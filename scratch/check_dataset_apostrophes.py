import csv

def main():
    path = 'official_test_v2_fixed.csv'
    print(f"Reading {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        found = []
        for row in reader:
            gold = row['gold']
            inp = row['input']
            if "'" in gold or "'" in inp:
                found.append((gold, inp))
                if len(found) >= 15:
                    break
    print("Found entries with apostrophe in test set:")
    print(found)

if __name__ == '__main__':
    main()
