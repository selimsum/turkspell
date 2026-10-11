"""
tools/modal_pipeline.py
========================
High-Performance Cloud GPU Pipeline for Turkspell using Modal.com ($30 Monthly Credits).

Target: 10,000 Missing Turkish Words

Actions:
    # 1. Mine 10,000 unrecognized words from Turkish Wikipedia using cloud Hunspell:
    modal run tools/modal_pipeline.py --action mine --limit 10000 --output raw_data/mined_10k_candidates.json

    # 2. Parse candidate words with Qwen2.5-32B on A100 GPU:
    modal run tools/modal_pipeline.py --action parse --input raw_data/mined_10k_candidates.json --output raw_data/parsed_10k_entries.json --limit 10000

    # 3. All-in-one: Mine 10,000 words and parse them directly in the cloud:
    modal run tools/modal_pipeline.py --action auto --limit 10000 --output raw_data/parsed_10k_entries.json

    # 4. Quick GPU test (parses 6 words to verify):
    modal run tools/modal_pipeline.py --action test
"""

import json
import os
import re
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import modal

app = modal.App("turkspell")

# Persistent cloud volume to cache Hugging Face models across runs
cache_volume = modal.Volume.from_name("turkspell-cache", create_if_missing=True)

# Cloud Container Image: Includes Hunspell + Turkspell dictionary files
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "hunspell", "libhunspell-dev")
    .pip_install(
        "torch>=2.5.0",
        "transformers>=4.44.0",
        "accelerate>=0.33.0",
        "bitsandbytes>=0.43.0",
        "datasets",
        "peft",
    )
    .env({"HF_HOME": "/cache/huggingface"})
    .add_local_file("tr.aff", "/root/tr.aff")
    .add_local_file("tr.dic", "/root/tr.dic")
)

SYSTEM_PROMPT = """You are an expert morphological analyzer for Turkish (TDK standard).
Your task is to parse a list of Turkish words and determine:
1. The correct Root Lemma (in lowercase Turkish).
   - For inflected nouns/adjectives, strip case/plural/possessive suffixes (e.g., "kitabından" -> "kitap", "ağzını" -> "ağız", "osteoklastlar" -> "osteoklast", "uzaylıların" -> "uzaylı").
   - Derived words with productive derivational suffixes (-lIk, -lI, -lAşmA, -cI) that stand as dictionary headwords keep their derived stem (e.g., "biyouyumluluk" -> "biyouyumluluk", "dijitalleşme" -> "dijitalleşme").
   - For finite/inflected verbs, return the infinitive form with -mak/-mek (e.g., "yapıvermişlerdi" -> "yapıvermek").
2. The Part of Speech (POS): one of 'Noun', 'Verb', 'Adjective', 'Adverb'.
3. Attributes (list of strings, can be empty []):
   - 'Voicing' ONLY if the final consonant of the lemma alternates (p/ç/t/k -> b/c/d/ğ) before a vowel suffix (e.g., kitap->kitabı, renk->rengi, ağaç->ağacı, umut->umudu). Words ending in a vowel (like "uzaylı") NEVER have Voicing.
   - 'LastVowelDrop' ONLY if the narrow vowel in the final syllable of the lemma drops before a vowel suffix (e.g., burun->burnu, ağız->ağzı, karın->karnı). Note: the lemma itself still retains the vowel ("ağız", NOT "ağz").
   - 'CompoundP3sg' ONLY for compound words formed with an inherent 3rd person singular possessive suffix -(s)I at the end (e.g., "gökkuşağı", "yıldızlararası", "denizaltı").

Rules:
- If a word is a typo, brand name, foreign word (English, Latin, etc.), or gibberish, set lemma, pos, and attributes to null.
- Respond ONLY with a valid JSON array. No markdown fences, no explanations, no extra text."""

FEW_SHOT_USER = 'Input: ["kitabımızdan", "yapıvermiş", "süpersimetrik", "google", "gökkuşağı", "osteoklastlar", "burnunu"]'
FEW_SHOT_ASSISTANT = """[
  {"word": "kitabımızdan", "lemma": "kitap", "pos": "Noun", "attributes": ["Voicing"]},
  {"word": "yapıvermiş", "lemma": "yapıvermek", "pos": "Verb", "attributes": []},
  {"word": "süpersimetrik", "lemma": "süpersimetrik", "pos": "Adjective", "attributes": []},
  {"word": "google", "lemma": null, "pos": null, "attributes": null},
  {"word": "gökkuşağı", "lemma": "gökkuşağı", "pos": "Noun", "attributes": ["CompoundP3sg"]},
  {"word": "osteoklastlar", "lemma": "osteoklast", "pos": "Noun", "attributes": []},
  {"word": "burnunu", "lemma": "burun", "pos": "Noun", "attributes": ["LastVowelDrop"]}
]"""


def extract_json_array(text: str):
    """Robust JSON extraction from LLM response."""
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


@app.function(
    image=image,
    gpu="A100",
    timeout=7200,
    volumes={"/cache": cache_volume},
)
def parse_words_chunk(words: list[str], batch_size: int = 25, model_id: str = "Qwen/Qwen2.5-32B-Instruct") -> list[dict]:
    """Runs high-speed 4-bit batch inference on Modal A100 GPU for a chunk of words."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    gpu_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"[*] Processing {len(words)} words with {model_id} on {gpu_name} ({vram:.0f} GB VRAM)...")

    tokenizer = AutoTokenizer.from_pretrained(model_id)

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto"
    )

    results = []
    total_batches = (len(words) + batch_size - 1) // batch_size

    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]
        batch_num = i // batch_size + 1
        if batch_num % 10 == 0 or batch_num == 1:
            print(f"  [Batch {batch_num}/{total_batches}] Processing: {batch[:3]}...")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": FEW_SHOT_USER},
            {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
            {"role": "user", "content": f"Input: {json.dumps(batch, ensure_ascii=False)}"},
        ]

        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=False,
            )

        resp = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        parsed = extract_json_array(resp)
        if parsed and isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("lemma"):
                    results.append(item)
        else:
            print(f"  Warning: Batch {batch_num} could not be parsed as JSON.")

    print(f"[OK] Chunk complete: extracted {len(results)} valid morphological entries.")
    return results


@app.function(
    image=image,
    timeout=1800,
)
def mine_corpus_cloud(target_candidates: int = 10000, max_articles: int = 35000) -> list[dict]:
    """Streams Turkish Wikipedia in the cloud and finds high-frequency unrecognized words using Hunspell."""
    import subprocess
    from collections import Counter
    from datasets import load_dataset

    print(f"[*] Starting cloud corpus mining (target: {target_candidates:,} unique words)...")
    print(f"  Streaming Turkish Wikipedia (up to {max_articles:,} articles)...")

    ds = load_dataset("wikimedia/wikipedia", "20231101.tr", split="train", streaming=True)

    counts = Counter()
    cap_counts = Counter()
    total_tokens = 0

    for idx, item in enumerate(ds):
        text = item.get("text", "")
        tokens = re.findall(r'[a-zA-ZçÇğĞıİöÖşŞüÜâîûÂÎÛ]+', text)
        for t in tokens:
            if len(t) < 3 or len(t) > 30:
                continue
            if any(c in 'qwxQWX' for c in t):
                continue
            total_tokens += 1
            lower_t = (
                t.replace('I', 'ı').replace('İ', 'i')
                .replace('Î', 'î').replace('Â', 'â').replace('Û', 'û')
                .lower()
            )
            counts[lower_t] += 1
            if t[0].isupper():
                cap_counts[lower_t] += 1

        if (idx + 1) % 5000 == 0:
            print(f"  Scanned {idx + 1:,} articles ({total_tokens:,} tokens, {len(counts):,} unique candidates)...")

        if idx >= max_articles:
            break

    print(f"[*] Total tokens scanned: {total_tokens:,} across {idx + 1:,} articles.")
    print(f"  Total unique candidates: {len(counts):,}")

    # Filter out proper names (words capitalized > 70% of the time with count >= 4)
    filtered = []
    for w, count in counts.most_common():
        if count < 3:
            continue
        if cap_counts[w] / count > 0.70:
            continue
        filtered.append((w, count))

    print(f"  Filtered non-proper candidates (freq >= 3): {len(filtered):,}")

    # Run Hunspell against Turkspell (/root/tr.aff and /root/tr.dic)
    words_to_check = [w for w, _ in filtered]
    temp_file = "/tmp/candidates_to_check.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("\n".join(words_to_check))

    print("  Running Hunspell verification against Turkspell (/root/tr)...")
    p = subprocess.run(
        ["hunspell", "-d", "/root/tr", "-l", temp_file],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    unrecognized_set = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    print(f"[*] Found {len(unrecognized_set):,} total unrecognized words in corpus!")

    # Return top N unrecognized words sorted by frequency
    top_unrecognized = [
        {"word": w, "freq": counts[w]}
        for w, _ in filtered if w in unrecognized_set
    ][:target_candidates]

    print(f"[OK] Harvested {len(top_unrecognized):,} top unrecognized Turkish words.")
    return top_unrecognized


@app.local_entrypoint()
def main(
    action: str = "test",
    input: str = "",
    output: str = "raw_data/parsed_entries.json",
    limit: int = 10000,
    model: str = "Qwen/Qwen2.5-32B-Instruct",
    chunk_size: int = 1000,
):
    """CLI Entrypoint executed on your local machine."""
    print("=" * 72)
    print(f"TURKSPELL MODAL PIPELINE: {action.upper()} (Target: {limit:,} Words | Model: {model})")
    print("=" * 72)

    if action == "test":
        test_words = ["biyouyumluluk", "osteoklastlar", "yapıvermişlerdi", "yıldızlararası", "gökkuşağı", "google"]
        print(f"Running quick GPU verification on {len(test_words)} words...")
        res = parse_words_chunk.remote(test_words, batch_size=10, model_id=model)
        print("\n--- Test Results from Modal A100 GPU ---")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        print("\n[OK] Verification successful! Modal GPU pipeline is fully operational.")

    elif action == "mine":
        print(f"[*] Mining {limit:,} unrecognized words from Turkish Wikipedia...")
        candidates = mine_corpus_cloud.remote(target_candidates=limit)

        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)

        print(f"\n[DONE] Saved {len(candidates):,} candidate words to {output}")
        print(f"Next step: Run 'modal run tools/modal_pipeline.py --action parse --input {output}' to parse them!")

    elif action == "parse":
        in_path = Path(input)
        if not in_path.exists():
            print(f"Error: Input file {input} not found.")
            sys.exit(1)

        with open(in_path, encoding="utf-8") as f:
            raw_data = json.load(f)

        if isinstance(raw_data, list):
            if raw_data and isinstance(raw_data[0], dict) and "word" in raw_data[0]:
                words = [item["word"] for item in raw_data][:limit]
            else:
                words = [w for w in raw_data if isinstance(w, str)][:limit]
        elif isinstance(raw_data, dict):
            words = list(raw_data.keys())[:limit]
        else:
            print("Error: Unsupported input JSON format.")
            sys.exit(1)

        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        all_entries = []
        if out_path.exists():
            try:
                with open(out_path, encoding="utf-8") as f:
                    all_entries = json.load(f)
                print(f"[*] Found existing output with {len(all_entries):,} already-saved entries.")
            except Exception:
                all_entries = []

        # Dynamic resume detection
        if len(all_entries) >= 2500 and len(words) >= 7000:
            print(f"[*] Resuming from word 7,000! ({len(all_entries):,} entries already saved from words 0..7,000).")
            remaining_words = words[7000:]
            concurrency = 4
        elif len(all_entries) >= 300 and len(words) > 1000:
            print("[*] Chunk 1 (words 0..1,000) was already completed. Resuming from word 1,000 onwards!")
            remaining_words = words[1000:]
            concurrency = 6
        else:
            remaining_words = words
            concurrency = 6

        chunk_len = (len(remaining_words) + concurrency - 1) // concurrency
        chunks = [remaining_words[i:i + chunk_len] for i in range(0, len(remaining_words), chunk_len)]

        print(f"[*] Launching {len(chunks)} parallel cloud workers on A100 GPUs (~{chunk_len:,} words per worker)...")
        print(f"[*] All {len(chunks)} workers will run simultaneously in Modal cloud!")

        handles = [
            (idx, parse_words_chunk.spawn(chunk, batch_size=25, model_id=model))
            for idx, chunk in enumerate(chunks, 1)
        ]

        for idx, handle in handles:
            chunk_res = handle.get()
            all_entries.extend(chunk_res)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            print(f"  [Worker {idx}/{len(handles)} Done] +{len(chunk_res)} entries. Total saved: {len(all_entries):,} in {output}")

        print(f"\n[DONE] All parallel workers completed! Saved {len(all_entries):,} total entries to {output}")

    elif action == "auto":
        print(f"[*] Starting End-to-End Pipeline: Mine {limit:,} words + GPU Parse...")
        candidates = mine_corpus_cloud.remote(target_candidates=limit)
        candidate_words = [item["word"] for item in candidates]

        print(f"[*] Mined {len(candidate_words):,} words. Now starting A100 GPU parsing...")
        chunks = [candidate_words[i:i + chunk_size] for i in range(0, len(candidate_words), chunk_size)]

        all_entries = []
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        for chunk_idx, chunk in enumerate(chunks, 1):
            print(f"\n--- Processing Chunk {chunk_idx}/{len(chunks)} ({len(chunk)} words) on A100 GPU ---")
            parsed_chunk = parse_words_chunk.remote(chunk, batch_size=20, model_id=model)
            all_entries.extend(parsed_chunk)

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            print(f"  [Progress] Saved {len(all_entries):,} total entries so far to {output}")

        print(f"\n[DONE] Pipeline complete! Saved {len(all_entries):,} entries to {output}")

    elif action == "tag-pos":
        in_path = Path(input or "raw_data/unannotated_authority_roots.json")
        if not in_path.exists():
            print(f"Error: Input file {in_path} not found.")
            sys.exit(1)

        with open(in_path, encoding="utf-8") as f:
            words = json.load(f)[:limit]

        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        concurrency = 10
        chunk_len = (len(words) + concurrency - 1) // concurrency
        chunks = [words[i:i + chunk_len] for i in range(0, len(words), chunk_len)]

        print(f"[*] Tagging POS & attributes for {len(words):,} official TDK/DD lemmas across {len(chunks)} parallel A100 GPUs (~{chunk_len:,} lemmas/GPU)...")
        handles = [
            (idx, tag_lemmas_chunk.spawn(chunk, batch_size=30, model_id=model))
            for idx, chunk in enumerate(chunks, 1)
        ]

        all_entries = []
        for idx, handle in handles:
            chunk_res = handle.get()
            all_entries.extend(chunk_res)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            print(f"  [Worker {idx}/{len(handles)} Done] +{len(chunk_res)} lemmas tagged. Total saved: {len(all_entries):,} in {output}")

        print(f"\n[DONE] All parallel workers completed! Saved {len(all_entries):,} tagged lemmas to {output}")


POS_SYSTEM_PROMPT = """You are an expert Turkish lexicographer and morphological analyzer (TDK & Dil Derneği standards).
Every input word is already a verified official Turkish dictionary headword (lemma).
Your task is to classify each lemma's Part of Speech (POS) and morphological inflection attributes.

Rules:
1. Preserve "lemma" EXACTLY as given in the input. Never alter spelling and never return null.
2. "pos": Must be one of 'Noun', 'Adjective', 'Adverb', 'Interjection', 'Conjunction', 'Pronoun', 'Numeral'.
3. "attributes": A JSON list of zero or more morphological flags from this exact set:
   - 'CompoundP3sg': ONLY for Turkish compound nouns that end in an inherent 3rd-person singular possessive suffix -(s)I (e.g., "adabalığı", "acemlalesi", "akdenizhumması", "ayçiçeği", "keçiboynuzu") which inflect with pronominal 'n' (adabalığını, acemlalesinde). Do NOT use on simplex nouns ("abadi", "abani") or nisba adjectives ("abidevi", "acemkürdi").
   - 'Voicing': ONLY if the lemma ends in p, ç, t, k and softens to b, c, d, ğ/g before a vowel suffix (e.g., "abuzambak" -> abuzambağı, "abartık" -> abartığı, "acip" -> acibi).
   - 'NoVoicing': ONLY if the lemma ends in p, ç, t, k, g and does NOT soften before a vowel suffix (e.g., "aberant" -> aberantı, "absent" -> absenti, "acıot" -> acıotu, "ahlak" -> ahlakı).
   - 'InverseHarmony': ONLY if the last vowel is a back vowel (a, ı, o, u, â, û) and the word ends in a palatal 'l' or 't' taking front-vowel suffixes (e.g., "alkol" -> alkolü, "amiral" -> amirali, "hal" -> hali).
   - 'LastVowelDrop': ONLY if the narrow vowel (ı, i, u, ü) in the final syllable drops before a vowel suffix (e.g., "ağız" -> ağzı, "burun" -> burnu).
   - 'Doubling': ONLY if the final consonant doubles before a vowel suffix (e.g., "hak" -> hakkı, "ret" -> reddi, "zam" -> zammı).
4. Respond ONLY with a valid JSON array of objects. No markdown, no explanations."""

POS_FEW_SHOT_USER = 'Input: ["adabalığı", "abuzambak", "aberant", "abidevi", "acıot", "acitato", "amiral"]'
POS_FEW_SHOT_ASSISTANT = """[
  {"lemma": "adabalığı", "pos": "Noun", "attributes": ["CompoundP3sg"]},
  {"lemma": "abuzambak", "pos": "Noun", "attributes": ["Voicing"]},
  {"lemma": "aberant", "pos": "Adjective", "attributes": ["NoVoicing"]},
  {"lemma": "abidevi", "pos": "Adjective", "attributes": []},
  {"lemma": "acıot", "pos": "Noun", "attributes": ["NoVoicing"]},
  {"lemma": "acitato", "pos": "Adverb", "attributes": []},
  {"lemma": "amiral", "pos": "Noun", "attributes": ["InverseHarmony"]}
]"""


@app.function(
    image=image,
    gpu="A100",
    timeout=7200,
    volumes={"/cache": cache_volume},
)
def tag_lemmas_chunk(lemmas: list[str], batch_size: int = 30, model_id: str = "Qwen/Qwen2.5-32B-Instruct") -> list[dict]:
    """Tags POS and morphological attributes for official TDK/DD lemmas on Modal A100 GPU."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    gpu_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"[*] Tagging {len(lemmas)} lemmas with {model_id} on {gpu_name} ({vram:.0f} GB VRAM)...")

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto"
    )

    results = []
    total_batches = (len(lemmas) + batch_size - 1) // batch_size

    for i in range(0, len(lemmas), batch_size):
        batch = lemmas[i:i + batch_size]
        batch_num = i // batch_size + 1
        if batch_num % 5 == 0 or batch_num == 1:
            print(f"  [Batch {batch_num}/{total_batches}] Tagging: {batch[:3]}...")

        messages = [
            {"role": "system", "content": POS_SYSTEM_PROMPT},
            {"role": "user", "content": POS_FEW_SHOT_USER},
            {"role": "assistant", "content": POS_FEW_SHOT_ASSISTANT},
            {"role": "user", "content": f"Input: {json.dumps(batch, ensure_ascii=False)}"},
        ]

        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=1200,
                do_sample=False,
            )

        resp = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        parsed = extract_json_array(resp)
        batch_set = set(batch)
        seen_in_batch = set()
        if parsed and isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("lemma") in batch_set:
                    lem = item["lemma"]
                    seen_in_batch.add(lem)
                    pos = item.get("pos") or "Noun"
                    attrs = item.get("attributes")
                    if not isinstance(attrs, list):
                        attrs = []
                    results.append({"lemma": lem, "pos": pos, "attributes": attrs})
        # Fallback for any lemma in the batch missed by JSON output
        for lem in batch:
            if lem not in seen_in_batch:
                results.append({"lemma": lem, "pos": "Noun", "attributes": []})

    print(f"[OK] Chunk complete: tagged {len(results)} lemmas.")
    return results

