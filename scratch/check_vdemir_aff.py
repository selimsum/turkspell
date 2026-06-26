with open('external_dictionaries/vdemir/tr_TR.aff', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if "'" in line:
            print(idx, line.strip())
