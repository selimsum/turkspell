with open("tr.dic", "r", encoding="utf-8") as f:
    for line in f:
        word = line.strip().split('/')[0]
        if "hük" in word or "hûk" in word:
            print(line.strip())
