import csv
import subprocess
import json
import os
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    v1_csv = root / 'official_test_fixed.csv'
    v2_csv = root / 'official_test_v2_fixed.csv'

    print("Reading CSV files to find correct gold words...")
    gold_words = set()

    # V1 (no header)
    if v1_csv.exists():
        with open(v1_csv, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    gold, inp = row[0].strip(), row[1].strip()
                    if gold == inp:
                        gold_words.add(gold)

    # V2 (header gold,input)
    if v2_csv.exists():
        with open(v2_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                gold, inp = row['gold'].strip(), row['input'].strip()
                if gold == inp:
                    gold_words.add(gold)

    print(f"Extracted {len(gold_words)} unique correct gold words. Running Hunspell...")

    # Write them to a temp file to run Hunspell in batch
    temp_input = root / 'scratch' / 'temp_gold.txt'
    temp_input.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_input, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(gold_words)) + '\n')

    # Run hunspell -d tr -l
    result = subprocess.run(
        ['hunspell', '-d', 'tr', '-l'],
        input='\n'.join(sorted(gold_words)) + '\n',
        capture_output=True, text=True, encoding='utf-8'
    )

    undetected = [w.strip() for w in result.stdout.split('\n') if w.strip()]
    print(f"Hunspell flagged {len(undetected)} correct words as misspelled (false positives).")

    # Filter out noise (numbers, punctuation, very short non-words)
    filtered = []
    for w in undetected:
        # Must contain only alphabetic characters
        if w.isalpha() and len(w) >= 3:
            filtered.append(w)

    print(f"Filtered to {len(filtered)} clean words. Saving to harvested_words.json...")
    
    output_path = root / 'harvested_words.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted(filtered), f, ensure_ascii=False, indent=2)

    # Clean up temp file
    if temp_input.exists():
        os.remove(temp_input)

    print("Harvest complete!")

if __name__ == '__main__':
    main()
