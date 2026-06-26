with open("official_test_v2_fixed.csv", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "î" in line or "â" in line or "û" in line:
            # Print any suspicious replacements
            if "edinî" in line or "idinî" in line or "dinî" in line:
                print(f"Line {i+1}: {line.strip()}")
