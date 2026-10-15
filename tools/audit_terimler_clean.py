import json
import re
from pathlib import Path

parsed_path = Path("raw_data/triage/colab_parsed_terimler.json")
with open(parsed_path, encoding="utf-8") as f:
    parsed = json.load(f)

valid = [x for x in parsed if x.get("lemma")]
print(f"Total valid items: {len(valid)}")

# Let's see all unique lemmas and their POS/attributes
clean_dict = {}
for item in valid:
    lem = item["lemma"].strip().lower()
    if not lem:
        continue
    # Standard Turkish alphabet filter
    if not all(c in "abcçdefgğhıijklmnoöprsştuüvyzâîû" for c in lem):
        continue
    if len(lem) < 2:
        continue
    # Filter repeated character triples (e.g. aaa, bbb)
    if re.search(r"(.)\1\1", lem):
        continue
    
    pos = item.get("pos") or "Noun"
    attrs = item.get("attributes") or []
    
    if lem not in clean_dict:
        clean_dict[lem] = {"lemma": lem, "pos": pos, "attributes": sorted(set(attrs))}
    else:
        # Merge attributes
        clean_dict[lem]["attributes"] = sorted(set(clean_dict[lem]["attributes"] + attrs))

print(f"Unique clean lemmas: {len(clean_dict)}")

# Attribute counts
from collections import Counter
attr_counts = Counter(a for item in clean_dict.values() for a in item["attributes"])
print("Attribute counts in clean set:", attr_counts)
print("POS counts in clean set:", Counter(item["pos"] for item in clean_dict.values()))

# Check samples
sample = list(clean_dict.values())[:30]
for s in sample:
    print(f"  {s['lemma']} [{s['pos']}] attrs={s['attributes']}")
