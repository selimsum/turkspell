"""
tools/mine_fineweb_large.py
===========================
High-Performance Distributed Corpus Miner for FineWeb-2 (tur_Latn).
Uses parallel CPU workers on Modal to extract 2,000,000 - 5,000,000 unique words
across distinct parquet shards (~300,000 documents, >100M tokens),
and verifies them against Turkspell Hunspell dictionary to produce a massive candidate pool.
"""

import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

import modal

app = modal.App("turkspell-fineweb-large")

miner_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("hunspell", "libhunspell-dev")
    .pip_install("pyarrow", "huggingface-hub")
    .add_local_file("tr.aff", "/root/tr.aff")
    .add_local_file("tr.dic", "/root/tr.dic")
)


@app.function(image=miner_image, timeout=900, cpu=4.0, memory=16384)
def mine_shard(shard_path: str, max_docs_per_shard: int = 40000) -> dict:
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    print(f"[*] Downloading {shard_path}...")
    t0 = time.time()
    local_file = hf_hub_download(
        repo_id="HuggingFaceFW/fineweb-2",
        filename=shard_path,
        repo_type="dataset",
    )
    print(f"[*] Downloaded {shard_path} in {time.time() - t0:.1f}s. Parsing parquet...")

    pf = pq.ParquetFile(local_file)
    token_re = re.compile(r"[a-zA-ZçÇğĞıİöÖşŞüÜâîûÂÎÛ]+")
    valid_tr_re = re.compile(r"^[abcçdefgğhıijklmnoöprsştuüvyzâîû]+$")

    counts = Counter()
    cap_counts = Counter()
    total_tokens = 0
    scanned = 0

    for batch in pf.iter_batches(batch_size=10000, columns=["text", "language_score"]):
        texts = batch.column("text").to_pylist()
        scores = batch.column("language_score").to_pylist()
        for text, score in zip(texts, scores):
            scanned += 1
            if score is not None and score < 0.99:
                continue
            if not text:
                continue
            text = unicodedata.normalize("NFC", text).replace("\u0307", "")
            for t in token_re.findall(text):
                if len(t) < 3 or len(t) > 32:
                    continue
                lower_t = (
                    t.replace("I", "ı")
                    .replace("İ", "i")
                    .replace("Î", "î")
                    .replace("Â", "â")
                    .replace("Û", "û")
                    .lower()
                )
                if not valid_tr_re.match(lower_t):
                    continue
                if any(lower_t[i] == lower_t[i + 1] == lower_t[i + 2] for i in range(len(lower_t) - 2)):
                    continue
                counts[lower_t] += 1
                total_tokens += 1
                if t[0].isupper():
                    cap_counts[lower_t] += 1

            if scanned >= max_docs_per_shard:
                break
        if scanned >= max_docs_per_shard:
            break

    elapsed = time.time() - t0
    print(
        f"[OK] Scanned {scanned:,} docs in {elapsed:.1f}s | "
        f"{total_tokens:,} tokens | {len(counts):,} unique words from {shard_path}."
    )

    # Return top 400,000 words from this shard to optimize serialization
    top_items = counts.most_common(400000)
    top_counts = {w: c for w, c in top_items}
    top_caps = {w: cap_counts[w] for w, _ in top_items if w in cap_counts}

    return {
        "shard_path": shard_path,
        "scanned": scanned,
        "tokens": total_tokens,
        "unique": len(counts),
        "counts": top_counts,
        "cap_counts": top_caps,
    }


@app.function(image=miner_image, timeout=600, cpu=4.0, memory=16384)
def verify_words_against_hunspell(words: list[str]) -> list[str]:
    import subprocess

    unrecognized = []
    batch_size = 50000
    for i in range(0, len(words), batch_size):
        batch = words[i : i + batch_size]
        p = subprocess.run(
            ["hunspell", "-d", "/root/tr", "-l"],
            input="\n".join(batch) + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        for line in p.stdout.splitlines():
            w = line.strip()
            if w:
                unrecognized.append(w)
    return unrecognized


def get_available_shards() -> list[str]:
    url = "https://huggingface.co/api/datasets/HuggingFaceFW/fineweb-2"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    return [
        s["rfilename"]
        for s in data.get("siblings", [])
        if "tur_Latn/train" in s.get("rfilename", "")
    ]


@app.local_entrypoint()
def main(num_shards: int = 8, docs_per_shard: int = 40000, min_freq: int = 4):
    print("=" * 76)
    print(f"TURKSPELL LARGE CORPUS MINER: {num_shards} parallel workers, {docs_per_shard:,} docs/shard")
    print(f"Targeting: ~{num_shards * docs_per_shard:,} docs (>100M tokens, 2M-5M unique words)")
    print("=" * 76)

    all_shards = get_available_shards()
    shards_to_mine = all_shards[:num_shards]
    print(f"Selected {len(shards_to_mine)} shards:")
    for s in shards_to_mine:
        print(f"  - {s}")

    t_start = time.time()
    handles = [
        mine_shard.spawn(shard_path=s, max_docs_per_shard=docs_per_shard)
        for s in shards_to_mine
    ]

    total_scanned = 0
    total_tokens = 0
    merged_counts = Counter()
    merged_caps = Counter()

    for i, h in enumerate(handles):
        res = h.get()
        total_scanned += res["scanned"]
        total_tokens += res["tokens"]
        merged_counts.update(res["counts"])
        merged_caps.update(res["cap_counts"])
        print(
            f"  [Worker {i+1}/{num_shards} Done ({res['shard_path']})] "
            f"+{res['tokens']:,} tokens. Total unique words so far: {len(merged_counts):,}"
        )

    mining_elapsed = time.time() - t_start
    print(f"\n[*] Mining Complete in {mining_elapsed:.1f}s!")
    print(f"  Total Docs Scanned: {total_scanned:,}")
    print(f"  Total Tokens: {total_tokens:,}")
    print(f"  Total Unique Words: {len(merged_counts):,}")

    # Filter proper nouns (> 70% capitalized) and rare words
    filtered_candidates = []
    clean_freq_table = {}
    for w, count in merged_counts.most_common():
        if count < 2:
            break
        # filter proper nouns
        cap_ratio = merged_caps.get(w, 0) / count
        if cap_ratio > 0.70:
            continue
        clean_freq_table[w] = count
        if count >= min_freq:
            filtered_candidates.append(w)

    print(f"  Clean frequency table size: {len(clean_freq_table):,} words")
    print(f"  Candidate words to test against Hunspell (freq >= {min_freq}): {len(filtered_candidates):,}")

    # Save large frequency table
    Path("raw_data").mkdir(parents=True, exist_ok=True)
    freq_path = Path("raw_data/fineweb2_corpus_frequencies_large.json")
    print(f"[*] Saving frequency table to {freq_path}...")
    with open(freq_path, "w", encoding="utf-8") as f:
        json.dump(clean_freq_table, f, ensure_ascii=False)

    # Parallel Hunspell verification in the cloud
    print(f"[*] Verifying {len(filtered_candidates):,} words against Turkspell (/root/tr)...")
    chunk_sz = 100000
    h_chunks = [
        filtered_candidates[i : i + chunk_sz]
        for i in range(0, len(filtered_candidates), chunk_sz)
    ]
    h_handles = [verify_words_against_hunspell.spawn(chunk) for chunk in h_chunks]

    unrecognized = []
    for h in h_handles:
        unrecognized.extend(h.get())

    # Build final pool sorted by frequency
    unrec_set = set(unrecognized)
    final_pool = [
        {"word": w, "freq": clean_freq_table[w]}
        for w in filtered_candidates
        if w in unrec_set
    ]
    final_pool.sort(key=lambda x: x["freq"], reverse=True)

    pool_path = Path("raw_data/fineweb2_unrecognized_large_pool.json")
    with open(pool_path, "w", encoding="utf-8") as f:
        json.dump(final_pool, f, ensure_ascii=False, indent=2)

    total_time = time.time() - t_start
    print(f"\n[DONE] Pipeline completed in {total_time:.1f}s ({total_time/60:.1f} min)!")
    print(f"  -> Total Unique Words in Frequency Map: {len(clean_freq_table):,}")
    print(f"  -> Total Unrecognized Candidates (freq >= {min_freq}): {len(final_pool):,}")
    print(f"  -> Saved Candidates Pool to {pool_path}")
