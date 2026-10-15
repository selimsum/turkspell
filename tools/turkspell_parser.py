#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turkspell Terim Parser (High-Performance GPU ChatTemplate V4)
Parses Turkish candidate words using Qwen2.5-7B-Instruct (4-bit NF4).
"""

import os
import sys
import json
import re
import time
import shutil
import subprocess
from pathlib import Path

print("=== Turkspell Morphology Parser (High-Performance ChatTemplate V4) ===")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Setup paths
repo_dir = Path("/tmp/turkspell")
if not repo_dir.exists():
    print("Cloning turkspell repository (branch: universal-bilim-sanat)...")
    subprocess.run(
        ["git", "clone", "--depth", "1", "-b", "universal-bilim-sanat", "https://github.com/selimsum/turkspell.git", str(repo_dir)],
        check=True
    )

input_file = repo_dir / "raw_data" / "triage" / "colab_candidate_words.txt"
if not input_file.exists():
    raise FileNotFoundError(f"Input file not found at {input_file}")

with open(input_file, "r", encoding="utf-8") as f:
    candidates = [line.strip() for line in f if line.strip()]
print(f"Loaded total candidate words: {len(candidates):,}")

# Determine output file location (Colab vs Kaggle vs local)
if Path("/content").exists():
    output_file = Path("/content/colab_parsed_terimler_part3.json")
elif Path("/kaggle/working").exists():
    output_file = Path("/kaggle/working/colab_parsed_terimler_part3.json")
else:
    output_file = repo_dir / "raw_data" / "triage" / "colab_parsed_terimler_part3.json"

# Resume capability
parsed_results = []
already_parsed = set()
if output_file.exists():
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            parsed_results = json.load(f)
            already_parsed = {item.get("word") for item in parsed_results if item.get("word")}
        print(f"Resumed from existing output: {len(already_parsed):,} words already parsed.")
    except Exception as e:
        print(f"Could not load existing output ({e}), starting fresh.")
        parsed_results = []
        already_parsed = set()

remaining = [w for w in candidates if w not in already_parsed]
print(f"Remaining words to process: {len(remaining):,}")

if not remaining:
    print("All candidate words are already processed!")
    sys.exit(0)

# Model setup
model_id = "Qwen/Qwen2.5-7B-Instruct"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device} | Model: {model_id} (4-bit NF4)")

tokenizer = AutoTokenizer.from_pretrained(model_id)

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto"
)
model.eval()

SYSTEM_PROMPT = """You are an expert morphological analyzer for Turkish (TDK standard).
Your task is to parse a list of Turkish words and determine for each word:
1. "word": the input word.
2. "lemma": the correct root lemma in lowercase Turkish. For verbs, use the infinitive (-mak/-mek).
3. "pos": 'Noun', 'Verb', 'Adjective', or 'Adverb'.
4. "attributes": list of strings:
   - 'Voicing' if the last consonant changes when inflected with a vowel suffix (e.g. kitap->kitabı, renk->rengi, ağaç->ağacı, umut->umudu).
   - 'LastVowelDrop' if root vowel drops (e.g. burun->burnu, ağız->ağzı).
   - 'CompoundP3sg' for compound words with inherent 3rd person possessive (e.g. gökkuşağı, suçiçeği).
   - 'InverseHarmony' for palatal-L roots that take front suffixes despite back vowel (e.g. alkol, protokol, santral).

Rules:
- If a word is a typo, brand name, foreign word (English, Latin, etc.), or gibberish, set "lemma", "pos", and "attributes" to null.
- Respond ONLY with a valid JSON array. No explanations, no markdown fences."""

FEW_SHOT_USER = '["kitabımızdan", "yapıvermiş", "süpersimetrik", "google", "nörobiyolojik", "osteoklastlar", "gökkuşağı", "alkol"]'
FEW_SHOT_ASSISTANT = """[
  {"word": "kitabımızdan", "lemma": "kitap", "pos": "Noun", "attributes": ["Voicing"]},
  {"word": "yapıvermiş", "lemma": "yapıvermek", "pos": "Verb", "attributes": []},
  {"word": "süpersimetrik", "lemma": "süpersimetrik", "pos": "Adjective", "attributes": []},
  {"word": "google", "lemma": null, "pos": null, "attributes": null},
  {"word": "nörobiyolojik", "lemma": "nörobiyolojik", "pos": "Adjective", "attributes": []},
  {"word": "osteoklastlar", "lemma": "osteoklast", "pos": "Noun", "attributes": []},
  {"word": "gökkuşağı", "lemma": "gökkuşağı", "pos": "Noun", "attributes": ["CompoundP3sg"]},
  {"word": "alkol", "lemma": "alkol", "pos": "Noun", "attributes": ["InverseHarmony"]}
]"""

def extract_json_array(text: str):
    text = re.sub(r'```(?:json)?\s*', '', text).strip()
    start = text.find('[')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None

# Fast Generation Loop with Chat Template & Stop Token
batch_size = 35
total_batches = (len(remaining) + batch_size - 1) // batch_size
start_total_time = time.time()

print(f"\nStarting generation: {len(remaining):,} words in {total_batches:,} batches of {batch_size}...")

for batch_idx in range(0, len(remaining), batch_size):
    batch = remaining[batch_idx : batch_idx + batch_size]
    batch_num = (batch_idx // batch_size) + 1
    t0 = time.time()

    # Apply official ChatML template
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": FEW_SHOT_USER},
        {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
        {"role": "user", "content": json.dumps(batch, ensure_ascii=False)}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id
        )

    # Decode only newly generated tokens
    gen_tokens = outputs[0][inputs.input_ids.shape[1]:]
    response = tokenizer.decode(gen_tokens, skip_special_tokens=True)
    dt = time.time() - t0

    batch_results = extract_json_array(response)
    valid_batch_count = 0
    if batch_results and isinstance(batch_results, list):
        for res in batch_results:
            if isinstance(res, dict) and res.get("word"):
                parsed_results.append(res)
                valid_batch_count += 1
    else:
        print(f"  [WARN] Batch {batch_num} JSON decode failed. Tokens generated: {len(gen_tokens)}")

    # Timing & ETA calculation
    elapsed = time.time() - start_total_time
    avg_per_batch = elapsed / batch_num
    remaining_batches = total_batches - batch_num
    eta_sec = remaining_batches * avg_per_batch
    eta_min = eta_sec / 60

    print(f"Batch {batch_num}/{total_batches} ({len(batch)} words) -> {valid_batch_count} valid [{dt:.2f}s, tokens: {len(gen_tokens)}] | ETA: {eta_min:.1f} min")

    # Save checkpoint to disk every 5 batches (and on the last batch)
    if batch_num % 5 == 0 or batch_num == total_batches:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(parsed_results, f, ensure_ascii=False, indent=2)

print(f"\n=== FINISHED ALL BATCHES! ===")
print(f"Total parsed results: {len(parsed_results):,}")
print(f"Saved output to {output_file} ({output_file.stat().st_size:,} bytes)")
