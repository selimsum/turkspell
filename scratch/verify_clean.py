import os

def check_file(path):
    if not os.path.exists(path):
        print(f"{path} does not exist.")
        return
        
    print(f"Verifying {path}...")
    errors = []
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if "gezmedinîz" in line or "edinîlmez" in line or "millîyet" in line:
                errors.append((i+1, line.strip()))
            # Also check any general dinî in suffixes or millîyet
            if "dinîz" in line or "edinîl" in line or "millîy" in line:
                errors.append((i+1, line.strip()))
                
    if errors:
        print(f"  Found {len(errors)} occurrences of incorrect replacements:")
        for idx, err in errors:
            print(f"    Line {idx}: {err}")
    else:
        print("  Clean! No incorrect replacements found.")

def main():
    check_file("official_test_fixed.csv")
    check_file("official_test_v2_fixed.csv")

if __name__ == "__main__":
    main()
