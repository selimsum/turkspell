import csv
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data_dir = Path(r"c:\gemini\turkspell-benchmarks\data")
v3_path = data_dir / "benchmark_tdk_dd_v3.csv"

with open(v3_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

all_caps_gold_low_input = []
any_caps_gold_low_input = []

for row in rows:
    gold = row['gold'].strip()
    inp = row['input'].strip()
    
    # Check if gold is all uppercase (e.g. RÜYALARINIZI)
    gold_tr_upper = gold.replace('i', 'İ').replace('ı', 'I').isupper()
    inp_tr_upper = inp.replace('i', 'İ').replace('ı', 'I').isupper()
    
    inp_has_no_upper = not any(c.isupper() for c in inp)
    gold_has_upper = any(c.isupper() for c in gold)
    
    if gold_tr_upper and not inp_tr_upper:
        all_caps_gold_low_input.append((inp, gold))
        
    if inp_has_no_upper and gold_has_upper:
        any_caps_gold_low_input.append((inp, gold))

print(f"Total rows in V3: {len(rows)}")
print(f"Category 1: Gold is ALL CAPS, Input is NOT ALL CAPS: {len(all_caps_gold_low_input)}")
print(f"Category 2: Gold has uppercase, Input is ALL lowercase: {len(any_caps_gold_low_input)}")

print("\nSample Category 1 (Gold ALL CAPS, Input NOT ALL CAPS):")
for inp, gold in all_caps_gold_low_input[:15]:
    print(f"  Input: '{inp}' -> Gold: '{gold}'")

print("\nSample Category 2 (Gold TitleCase/Upper, Input lowercase):")
for inp, gold in any_caps_gold_low_input[:15]:
    print(f"  Input: '{inp}' -> Gold: '{gold}'")
