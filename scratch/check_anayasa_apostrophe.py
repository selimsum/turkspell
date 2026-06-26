with open('anayasa.txt', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if "'" in line or "’" in line or "‘" in line:
            print(idx, line.strip())
