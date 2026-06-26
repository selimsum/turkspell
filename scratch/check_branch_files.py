import urllib.request
import json

def check_branch(branch_name):
    url = f"https://api.github.com/repos/tdd-ai/spell-checking-and-correction/contents/evaluation/data?ref={branch_name}"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            names = [item['name'] for item in data]
            if "official_test_v2_fixed.csv" in names:
                print(f"  Branch '{branch_name}': FOUND official_test_v2_fixed.csv!")
            else:
                print(f"  Branch '{branch_name}': not found.")
    except Exception as e:
        print(f"  Branch '{branch_name}': error - {e}")

def main():
    branches = ["data-augmentation-dev", "dev", "main", "ts_word_list", "turkish-spellcheckers-dev"]
    print("Searching for official_test_v2_fixed.csv on branches:")
    for b in branches:
        check_branch(b)

if __name__ == "__main__":
    main()
