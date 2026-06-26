import os
import urllib.request
import urllib.error

# Dictionary specifications with direct raw URLs or lists of candidate URLs
DICTIONARIES = {
    "tdd-ai": {
        "files": {
            "tr_TR.aff": ["https://raw.githubusercontent.com/tdd-ai/hunspell-tr/master/tr_TR.aff", "https://raw.githubusercontent.com/tdd-ai/hunspell-tr/main/tr_TR.aff"],
            "tr_TR.dic": ["https://raw.githubusercontent.com/tdd-ai/hunspell-tr/master/tr_TR.dic", "https://raw.githubusercontent.com/tdd-ai/hunspell-tr/main/tr_TR.dic"]
        }
    },
    "vdemir": {
        "files": {
            "tr_TR.aff": ["https://raw.githubusercontent.com/vdemir/hunspell-tr/master/tr_TR.aff", "https://raw.githubusercontent.com/vdemir/hunspell-tr/main/tr_TR.aff"],
            "tr_TR.dic": ["https://raw.githubusercontent.com/vdemir/hunspell-tr/master/tr_TR.dic", "https://raw.githubusercontent.com/vdemir/hunspell-tr/main/tr_TR.dic"]
        }
    },
    "harunzafer": {
        "files": {
            "tr_TR.aff": ["https://raw.githubusercontent.com/LibreOffice/dictionaries/ef5ed1ca0e43519a2013d50d9ac67529b78f612c/tr_TR/tr_TR.aff"],
            "tr_TR.dic": ["https://raw.githubusercontent.com/LibreOffice/dictionaries/ef5ed1ca0e43519a2013d50d9ac67529b78f612c/tr_TR/tr_TR.dic"]
        }
    },
    "selimsum": {
        "files": {
            "tr.aff": ["https://raw.githubusercontent.com/selimsum/hunspell-tr-moz/master/tr.aff", "https://raw.githubusercontent.com/selimsum/hunspell-tr-moz/main/tr.aff"],
            "tr.dic": ["https://raw.githubusercontent.com/selimsum/hunspell-tr-moz/master/tr.dic", "https://raw.githubusercontent.com/selimsum/hunspell-tr-moz/main/tr.dic"]
        }
    }
}

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "external_dictionaries")

def download_file(name, file_name, urls, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, file_name)
    
    for url in urls:
        print(f"Trying to download {file_name} for {name} from {url}...")
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response:
                content = response.read()
                with open(target_path, "wb") as f:
                    f.write(content)
            print(f"  Successfully downloaded to {target_path} ({len(content)} bytes)")
            return True
        except urllib.error.HTTPError as e:
            print(f"  Failed: HTTP {e.code} {e.reason}")
        except Exception as e:
            print(f"  Error: {e}")
            
    print(f"ERROR: Could not download {file_name} for {name} from any of the URLs: {urls}")
    return False

def main():
    print("Starting download of spelling dictionaries...")
    success_count = 0
    total_files = sum(len(info["files"]) for info in DICTIONARIES.values())
    
    for name, info in DICTIONARIES.items():
        target_subdir = os.path.join(BASE_DIR, name)
        print(f"\nProcessing: {name}")
        
        for file_name, urls in info["files"].items():
            if download_file(name, file_name, urls, target_subdir):
                success_count += 1
                
    print(f"\nDownload process complete: {success_count}/{total_files} files downloaded successfully.")
    if success_count < total_files:
        print("WARNING: Some dictionary files failed to download!")
        exit(1)
    else:
        print("All external dictionaries downloaded successfully.")

if __name__ == "__main__":
    main()
