import csv
import hashlib
import json
import os
import re
from pathlib import Path

BENCH_REPO = Path(r"c:\gemini\turkspell-benchmarks")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

# 1. Update collision_filter.py in benchmarks
cf_path = BENCH_REPO / "benchmark" / "collision_filter.py"
if cf_path.exists():
    content = cf_path.read_text(encoding="utf-8")
    old_class = """class CollisionFilter:
    def __init__(self, extra_valid: set = None):
        self.universe = load_reference_universe()
        if extra_valid:
            self.universe |= {tlc(w) for w in extra_valid}

    def is_valid_anywhere(self, word: str) -> bool:
        return tlc(word.strip()) in self.universe"""

    new_class = """class CollisionFilter:
    def __init__(self, extra_valid: set = None):
        self.universe = load_reference_universe()
        if extra_valid:
            self.universe |= {tlc(w) for w in extra_valid}
        self._speller_cache = {}
        self._ref_dicts = [
            os.path.join(config.EXTERNAL_DICTS_DIR, "harunzafer", "tr_TR").replace("\\\\", "/"),
            os.path.join(config.TURKSPELL_DICT_DIR, "tr").replace("\\\\", "/"),
            os.path.join(config.EXTERNAL_DICTS_DIR, "vdemir", "tr_TR").replace("\\\\", "/")
        ]

    def is_valid_anywhere(self, word: str) -> bool:
        w = tlc(word.strip())
        if w in self.universe:
            return True
        if w in self._speller_cache:
            return self._speller_cache[w]
            
        is_valid = False
        for d in self._ref_dicts:
            if os.path.exists(d + ".dic"):
                try:
                    import subprocess
                    p = subprocess.run(
                        ["hunspell", "-d", d, "-l"],
                        input=w + "\\n",
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=5
                    )
                    if w not in {line.strip() for line in p.stdout.splitlines()}:
                        is_valid = True
                        break
                except Exception:
                    pass
                    
        self._speller_cache[w] = is_valid
        return is_valid"""

    if old_class in content:
        content = content.replace(old_class, new_class)
        cf_path.write_text(content, encoding="utf-8")
        print("Successfully updated collision_filter.py with morphological speller checks!")
    else:
        print("Note: collision_filter.py already modified or different pattern.")

# 2. Colliding inputs to purge from test datasets
COLLIDING_INPUTS = {
    # Valid Turkish inflected words erroneously generated as synthetic typos
    'aşıkta',       # aşık + ta (locative)
    'darıda',       # darı + da (locative)
    'tende',        # ten + de (locative)
    'kakışılmak',   # kakışmak + ıl (passive verb, TDK)
    'sekilsizlik',  # sekil + siz + lik (TDK)
    'suresizlik',   # sure + siz + lik (TDK)
    'cilli',        # cil + li / cilli (misket, TDK)
    'cinsçik',      # cins + çik (diminutive)
    'evvelcen',     # evvelce + n
    # Defective test pair
    'yahudide',     # gold was yahudice; both uncapitalized, improper pair
    # Valid inflected words erroneously included in corpus_real slice
    'bloğu', 'bloğunun', 'bloğunda',
    'usulünde', 'usulünün', 'usulünü',
    'emrindeki', 'kaydıyla',
    'imalatını', 'imalatına',
    'teşkilatı', 'teşkilatın', 'teşkilatımıza',
    'mescid', 'nisbi', 'rolündeki'
}

# 3. Clean bench_v3_misspelled.csv in data/active/v3 and dataset/turkspell_bench_v3
target_dirs = [
    BENCH_REPO / "data" / "active" / "v3",
    BENCH_REPO / "dataset" / "turkspell_bench_v3"
]

for d in target_dirs:
    csv_file = d / "bench_v3_misspelled.csv"
    manifest_file = d / "manifest.json"
    if not csv_file.exists():
        continue
        
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
        
    original_count = len(rows)
    kept_rows = []
    removed_count = 0
    
    for r in rows:
        inp = r.get("input", "").strip()
        if inp in COLLIDING_INPUTS:
            removed_count += 1
            continue
        kept_rows.append(r)
        
    # Re-index id
    for idx, r in enumerate(kept_rows, 1):
        r["id"] = str(idx)
        
    # Write back cleaned CSV
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)
        
    print(f"[{d.name}] Cleaned {csv_file.name}: {original_count} -> {len(kept_rows)} (removed {removed_count} collisions)")
    
    # Update manifest.json
    if manifest_file.exists():
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        manifest["misspelled_sha256"] = sha256_file(csv_file)
        manifest["misspelled_count"] = len(kept_rows)
        
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"[{d.name}] Updated manifest.json with fresh sha256 and count={len(kept_rows)}")

print("All dataset collision cleaning complete!")
