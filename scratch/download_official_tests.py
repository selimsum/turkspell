import urllib.request
import os

def download_file(url, output_path):
    print(f"Downloading {url} -> {output_path}...")
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"  Successfully downloaded to {output_path} ({os.path.getsize(output_path)} bytes)")
    except Exception as e:
        print(f"  Error downloading {url}: {e}")

def main():
    base_url = "https://raw.githubusercontent.com/tdd-ai/spell-checking-and-correction/main/evaluation/data"
    
    # 1. Download official_test_v2.csv
    url_v2 = f"{base_url}/official_test_v2.csv"
    download_file(url_v2, "official_test_v2.csv")
    
    # 2. Download official_test_v2_fixed.csv
    url_v2_fixed = f"{base_url}/official_test_v2_fixed.csv"
    download_file(url_v2_fixed, "official_test_v2_fixed.csv")

if __name__ == "__main__":
    main()
