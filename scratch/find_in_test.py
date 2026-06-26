with open("scratch/circumflex_exploration.txt", "r", encoding="utf-8") as f:
    for line in f:
        if "in_test=True" in line:
            print(line.strip())
