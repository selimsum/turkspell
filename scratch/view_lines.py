with open("official_test.csv", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "kağ" in line or "hük" in line or "huk" in line:
            print(f"Line {i+1}: {line.strip()}")
