with open("official_test_v2.csv", "r", encoding="utf-8") as f1, \
     open("official_test_v2_fixed.csv", "r", encoding="utf-8") as f2:
     
    header1 = next(f1)
    header2 = next(f2)
    
    for i in range(1000):
        line1 = next(f1).strip()
        line2 = next(f2).strip()
        if line1 != line2:
            print(f"Line {i+2}:")
            print(f"  Orig: {line1}")
            print(f"  Fixed: {line2}")
