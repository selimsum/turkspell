import urllib.request
import json

def main():
    url = "https://api.github.com/repos/tdd-ai/spell-checking-and-correction/branches"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("Branches in repo:")
            for item in data:
                print(f"  - {item['name']}")
    except Exception as e:
        print(f"Error querying GitHub API: {e}")

if __name__ == "__main__":
    main()
