# -*- coding: utf-8 -*-
"""Generate the deterministic Turkspell Benchmark V3 dataset.

Outputs (under benchmark/turkspell_bench_v3/):
  bench_v3_misspelled.csv  - id,slice,input,gold,frequency_tier,notes
  bench_v3_clean.csv       - id,input,gold(=input),notes
  manifest.json            - seed, sizes, sha256 of outputs

Usage:
  python benchmark/generate_dataset.py            # SAMPLE_SIZE entries
  python benchmark/generate_dataset.py --full     # 10000 entries
  python benchmark/generate_dataset.py --check    # verify determinism
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark import config
from benchmark.lexicons import tlc, load_authority_index
from benchmark.mutations import mutate_keyboard, mutate_diacritic, mutate_phonetic
from benchmark.mine_corpus_slice import mine_corpus_slice, frequency_tier
from benchmark.collision_filter import CollisionFilter


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _authority_words() -> list:
    """Pool of valid authority words for mutation slices."""
    idx = load_authority_index(config.AUTHORITY_FILES)
    return sorted(idx["exact"])


def _fill_slice(target: int, mutator, pool: list, rng, cf, taken: set,
                slice_name: str, out: list):
    """Append up to `target` entries OF THIS SLICE to out."""
    attempts = 0
    produced = 0
    while produced < target and attempts < target * 60 + 5000:
        word = pool[rng.randrange(len(pool))]
        attempts += 1
        r = mutator(word, rng)
        if r is None:
            continue
        inp, gold, note = r
        key = tlc(inp)
        if key in taken or cf.is_valid_anywhere(inp):
            continue
        if len(key) < 2:
            continue
        taken.add(key)
        out.append({
            "slice": slice_name,
            "input": inp,
            "gold": gold,
            "frequency_tier": "",
            "notes": note,
        })
        produced += 1



def generate(full: bool = False) -> None:
    size = config.SAMPLE_SIZE * (4 if full else 1)
    rng = random.Random(config.SEED)

    print("Building reference universe (collision filter)...")
    cf = CollisionFilter()
    print(f"  universe: {len(cf.universe):,} forms")

    quotas = {name: round(size * frac) for name, frac in config.SLICES.items()}
    print(f"Slices: {quotas}")

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    misspelled = []
    taken = set()

    # --- corpus_real ---
    print("Mining corpus-real slice...")
    for w, freq in mine_corpus_slice(quotas["corpus_real"] * 3, set()):
        if len(misspelled) >= quotas["corpus_real"]:
            break
        key = tlc(w)
        if key in taken or cf.is_valid_anywhere(w):
            continue
        taken.add(key)
        misspelled.append({
            "slice": "corpus_real",
            "input": w,
            "gold": "",          # gold unknown for real errors; filled by evaluator
            "frequency_tier": frequency_tier(freq),
            "notes": f"corpus_freq={freq}",
        })
    print(f"  corpus_real: {sum(1 for m in misspelled if m['slice']=='corpus_real')}")

    pool = _authority_words()
    print(f"Authority mutation pool: {len(pool):,} words")

    for name, mutator in (("keyboard", mutate_keyboard),
                          ("diacritic", mutate_diacritic),
                          ("phonetic", mutate_phonetic)):
        n0 = len(misspelled)
        _fill_slice(quotas[name], mutator, pool, rng,
                    cf, taken, name, misspelled)
        print(f"  {name}: {len(misspelled)-n0}")

    rng.shuffle(misspelled)

    # --- clean control set ---
    clean_pool = [w for w in pool if not any(c in w for c in "âîû")]
    clean = []
    seen_clean = set()
    while len(clean) < size and clean_pool:
        i = rng.randrange(len(clean_pool))
        w = clean_pool.pop(i)
        if tlc(w) in seen_clean:
            continue
        seen_clean.add(tlc(w))
        clean.append({"input": w, "gold": w, "notes": "authority"})
    rng.shuffle(clean)

    # --- write outputs ---
    miss_path = os.path.join(config.OUTPUT_DIR, "bench_v3_misspelled.csv")
    with open(miss_path, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=[
            "id", "slice", "input", "gold", "frequency_tier", "notes"])
        wr.writeheader()
        for i, row in enumerate(misspelled, 1):
            row["id"] = i
            wr.writerow(row)

    clean_path = os.path.join(config.OUTPUT_DIR, "bench_v3_clean.csv")
    with open(clean_path, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["id", "input", "gold", "notes"])
        wr.writeheader()
        for i, row in enumerate(clean, 1):
            wr.writerow({"id": i, **row})

    manifest = {
        "seed": config.SEED,
        "size": size,
        "slices": quotas,
        "misspelled_sha256": _sha256(miss_path),
        "clean_sha256": _sha256(clean_path),
        "misspelled_count": len(misspelled),
        "clean_count": len(clean),
    }
    with open(os.path.join(config.OUTPUT_DIR, "manifest.json"),
              "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(misspelled)} misspelled / {len(clean)} clean to "
          f"{config.OUTPUT_DIR}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="generate 10k entries")
    ap.add_argument("--check", action="store_true",
                    help="regenerate and verify byte-identical output")
    args = ap.parse_args()

    if args.check:
        out = config.OUTPUT_DIR
        before = {
            p: _sha256(os.path.join(out, p))
            for p in ("bench_v3_misspelled.csv", "bench_v3_clean.csv")
            if os.path.exists(os.path.join(out, p))
        }
        generate(full=args.full)
        after = {
            p: _sha256(os.path.join(out, p))
            for p in ("bench_v3_misspelled.csv", "bench_v3_clean.csv")
        }
        ok = all(before.get(p) == h for p, h in after.items()) and \
             set(before) == set(after)
        print("DETERMINISM:", "OK" if ok else "MISMATCH")
        sys.exit(0 if ok else 1)
    else:
        generate(full=args.full)
