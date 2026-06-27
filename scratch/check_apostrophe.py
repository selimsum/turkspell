def main():
    path = 'external_dictionaries/tdd-ai/tr_TR.dic'
    print(f"Reading {path}...")
    with open(path, 'r', encoding='utf-8') as f:
        found = []
        for line in f:
            if "'" in line:
                found.append(line.strip())
                if len(found) >= 15:
                    break
    print("Found entries with apostrophe:")
    print(found)

if __name__ == '__main__':
    main()
