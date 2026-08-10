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

print(f"Total rows in V3: {len(rows)}")

def is_tr_upper(s):
    # Check if s is uppercase in Turkish
    s_tr = s.replace('i', 'İ').replace('ı', 'I')
    return s_tr.isupper()

def is_tr_lower(s):
    # Check if s has no uppercase letters in Turkish
    s_tr = s.replace('I', 'ı').replace('İ', 'i')
    return not any(c.isupper() for c in s)

casing_mismatches = []
for row in rows:
    gold = row['gold'].strip()
    inp = row['input'].strip()
    
    # Case 1: inp is lowercase (no uppercase letters), but gold has uppercase letters or is all upper
    if not any(c.isupper() for c in inp) and any(c.isupper() for c in gold):
        casing_mismatches.append((inp, gold, "inp lowercase, gold has uppercase"))
    # Case 2: inp is not all-upper, but gold is all-upper
    elif not inp.isupper() and gold.isupper():
        casing_mismatches.append((inp, gold, "inp not all-upper, gold all-upper"))

print(f"Total casing mismatches found: {len(casing_mismatches)}")
print("\nSample mismatches:")
for inp, gold, reason in casing_mismatches[:30]:
    print(f"  Input: '{inp}' | Gold: '{gold}' | Reason: {reason}")
