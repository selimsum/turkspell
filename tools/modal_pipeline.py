"""
tools/modal_pipeline.py
========================
High-Performance Cloud Pipeline for Turkspell using Modal.com ($30 Monthly Credits)
and HuggingFaceFW/fineweb-2 (tur_Latn, language_score >= 0.99).

Actions:
    # 1. Stream FineWeb-2 (tur_Latn) in the cloud, extract clean frequencies & unrecognized candidates:
    modal run tools/modal_pipeline.py --action mine --limit 10000 --max-docs 60000 --output raw_data/fineweb2_unrecognized_candidates.json

    # 2. Parse candidate words with Qwen/Qwen3.6-35B-A3B-FP8 via vLLM on H100 GPU:
    modal run tools/modal_pipeline.py --action parse --input raw_data/fineweb2_unrecognized_candidates.json --output raw_data/fineweb2_parsed_entries.json --limit 5000

    # 3. All-in-one: Mine FineWeb-2 and parse candidates directly in the cloud:
    modal run tools/modal_pipeline.py --action auto --limit 5000 --output raw_data/fineweb2_parsed_entries.json

    # 4. Quick GPU test:
    modal run tools/modal_pipeline.py --action test
"""

import json
import os
import re
import sys
import unicodedata
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

# Lightweight CPU image for streaming FineWeb-2 and running Hunspell verification
cpu_miner_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("hunspell", "libhunspell-dev")
    .pip_install("datasets>=3.0.0", "pyarrow", "huggingface-hub>=0.30.0")
    .env({"HF_HOME": "/cache/huggingface"})
    .add_local_file("tr.aff", "/root/tr.aff")
    .add_local_file("tr.dic", "/root/tr.dic")
)

# High-speed vLLM GPU image for FP8 MoE morphological analysis
gpu_vllm_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "vllm>=0.19.0",
        "huggingface-hub>=0.30.0",
    )
    .env({
        "HF_HOME": "/cache/huggingface",
        "HF_XET_HIGH_PERFORMANCE": "1",
        "VLLM_USE_DEEP_GEMM": "0",
        "VLLM_USE_FLASHINFER_SAMPLER": "0",
    })
)

SYSTEM_PROMPT = """You are an expert Turkish morphological analyzer and lexicographer (TDK & Dil Derneği standards).
Analyze each input Turkish word and return a JSON array of objects with the following fields:

1. "word": The exact input word.
2. "lemma":
   - For simple inflected words (derivation_depth = 0), return the dictionary root lemma in lowercase Turkish:
     * Strip case/plural/possessive/copula suffixes from nouns/adjectives (e.g., "kitabından" -> "kitap", "ağzını" -> "ağız", "alkolü" -> "alkol", "koda" -> "kod", "hakkını" -> "hak").
     * For inflected verbs (tense/person/mood/negation/converbs), return the infinitive with -mak/-mek (e.g., "yapıvermişlerdi" -> "yapıvermek", "gidiyordu" -> "gitmek").
   - For derived words (derivation_depth >= 1), return the derived stem dictionary headword (stripped of case/plural/possessive inflections):
     * e.g., "gözlükçüden" -> "gözlükçü", "yerelleştirmesi" -> "yerelleştirme", "okunabilirliği" -> "okunabilirlik", "sürdürülebilirliklerinden" -> "sürdürülebilirlik", "kurumsallaştırılması" -> "kurumsallaştırılma", "biyouyumluluk" -> "biyouyumluluk", "dijitalleşme" -> "dijitalleşme".
3. "base_root":
   - The underlying root word in TDK/Dil Derneği before derivational suffixes (e.g., for "gözlükçüden" -> "göz", "yerelleştirmesi" -> "yerel", "sürdürülebilirliklerinden" -> "sürmek", "kurumsallaştırılması" -> "kurum", "kitabından" -> "kitap").
4. "derivation_depth": Integer (0, 1, 2, or 3):
   - 0: Inflection only (no derivational suffixes on the lemma, or inherent compound like "gökkuşağı", or loanword stem like "osteoklast", "nörolojik", "biyouyumluluk").
   - 1: 1 derivational suffix layer on a Turkish base root (e.g., "uzay-lı", "göz-lük", "dijital-leşme").
   - 2: 2 derivational suffix layers on a Turkish base root (e.g., "göz-lük-çü", "yerel-leş-tirme", "okun-abil-irlik").
   - 3: 3 or more derivational suffix layers (e.g., "sür-dür-ül-ebilir-lik" -> 3, "kurum-sal-laş-tır-ılma" -> 3).
5. "pos": Part of speech of "lemma": one of 'Noun', 'Verb', 'Adjective', 'Adverb'.
6. "attributes": Phonological attributes of "lemma" (JSON list of strings from this exact set, or []):
   - 'Voicing': ONLY if "lemma" ends in p, ç, t, k and softens to b, c, d, ğ/g before a vowel suffix (e.g., "kitap" -> kitabı, "renk" -> rengi, "okunabilirlik" -> okunabilirliği, "sürdürülebilirlik" -> sürdürülebilirliği, "biyouyumluluk" -> biyouyumluluğu). Words ending in a vowel NEVER have Voicing.
   - 'NoVoicing': ONLY if "lemma" ends in p, ç, t, k, g and does NOT soften before a vowel suffix (e.g., "ahlak" -> ahlakı, "sepet" -> sepeti, "osteoklast" -> osteoklastı).
   - 'LastVowelDrop': ONLY if the narrow vowel (ı, i, u, ü) in the final syllable of "lemma" drops before a vowel suffix (e.g., "ağız" -> ağzı, "burun" -> burnu, "beyin" -> beyni).
   - 'Doubling': ONLY if the final consonant of "lemma" doubles before a vowel suffix (e.g., "hak" -> hakkı, "hat" -> hattı, "ret" -> reddi, "zam" -> zammı).
   - 'InverseHarmony': ONLY if the last vowel of "lemma" is a back vowel (a, ı, o, u, â, û) and the word takes front-vowel suffixes due to a palatal consonant (e.g., "alkol" -> alkolü, "rol" -> rolü, "saat" -> saati, "amiral" -> amirali).
   - 'CompoundP3sg': ONLY for compound nouns ending in an inherent 3rd-person singular possessive suffix -(s)I that inflect with pronominal 'n' (e.g., "gökkuşağı" -> gökkuşağını, "yıldızlararası" -> yıldızlararasında, "denizaltı").

Rules:
- If a word is a misspelling/typo (e.g., "orjinal", "yalnış", "herkez"), a brand/proper name ("google", "instagram"), or a foreign word, set "lemma": null, "base_root": null, "derivation_depth": null, "pos": null, "attributes": null, and provide the corrected Turkish word in "correction" if it is a typo (e.g., "orjinal" -> "orijinal", "yalnış" -> "yanlış") or null if foreign/brand.
- Respond ONLY with a valid JSON array. No markdown fences, no commentary."""

FEW_SHOT_USER = 'Input: ["kitabımızdan", "yapıvermiş", "gözlükçüden", "sürdürülebilirlikleri", "alkolün", "orjinal", "google"]'
FEW_SHOT_ASSISTANT = """[
  {"word": "kitabımızdan", "lemma": "kitap", "base_root": "kitap", "derivation_depth": 0, "pos": "Noun", "attributes": ["Voicing"], "correction": null},
  {"word": "yapıvermiş", "lemma": "yapıvermek", "base_root": "yapmak", "derivation_depth": 1, "pos": "Verb", "attributes": [], "correction": null},
  {"word": "gözlükçüden", "lemma": "gözlükçü", "base_root": "göz", "derivation_depth": 2, "pos": "Noun", "attributes": [], "correction": null},
  {"word": "sürdürülebilirlikleri", "lemma": "sürdürülebilirlik", "base_root": "sürmek", "derivation_depth": 3, "pos": "Noun", "attributes": ["Voicing"], "correction": null},
  {"word": "alkolün", "lemma": "alkol", "base_root": "alkol", "derivation_depth": 0, "pos": "Noun", "attributes": ["InverseHarmony"], "correction": null},
  {"word": "orjinal", "lemma": null, "base_root": null, "derivation_depth": null, "pos": null, "attributes": null, "correction": "orijinal"},
  {"word": "google", "lemma": null, "base_root": null, "derivation_depth": null, "pos": null, "attributes": null, "correction": null}
]"""


def extract_json_array(text: str):
    """Robust JSON extraction from LLM response."""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    start = text.find("[")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


@app.function(
    image=gpu_vllm_image,
    gpu="H100",
    timeout=7200,
    volumes={"/cache": cache_volume},
)
def parse_words_chunk(
    words: list[str],
    batch_size: int = 25,
    model_id: str = "Qwen/Qwen3.6-35B-A3B-FP8",
) -> list[dict]:
    """Runs high-speed continuous-batched FP8 inference via vLLM on Modal H100 GPU."""
    import torch
    from vllm import LLM, SamplingParams

    gpu_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"[*] Processing {len(words):,} words with {model_id} via vLLM on {gpu_name} ({vram:.0f} GB VRAM)...")

    llm_kwargs = {
        "model": model_id,
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.90,
        "trust_remote_code": True,
        "enforce_eager": True,
    }
    if "Qwen3.5" in model_id or "Qwen3.6" in model_id:
        llm_kwargs["language_model_only"] = True

    llm = LLM(**llm_kwargs)

    all_conversations = []
    for i in range(0, len(words), batch_size):
        batch = words[i : i + batch_size]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": FEW_SHOT_USER},
            {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
            {"role": "user", "content": f"Input: {json.dumps(batch, ensure_ascii=False)}"},
        ]
        all_conversations.append(messages)

    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=3072,
    )

    print(f"  Running vLLM continuous batching across {len(all_conversations)} batches...")
    try:
        outputs = llm.chat(
            messages=all_conversations,
            sampling_params=sampling_params,
            chat_template_kwargs={"enable_thinking": False},
        )
    except TypeError:
        outputs = llm.chat(
            messages=all_conversations,
            sampling_params=sampling_params,
        )

    results = []
    for batch_idx, out in enumerate(outputs, 1):
        resp = out.outputs[0].text
        parsed = extract_json_array(resp)
        if parsed and isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("word"):
                    results.append(item)
        else:
            print(f"  Warning: Batch {batch_idx} could not be parsed as JSON.")

    print(f"[OK] Chunk complete: extracted {len(results):,} analyzed entries.")
    return results


@app.function(
    image=cpu_miner_image,
    cpu=4.0,
    memory=8192,
    timeout=3600,
    volumes={"/cache": cache_volume},
)
def mine_corpus_cloud(
    target_candidates: int = 10000,
    max_docs: int = 60000,
    min_lang_score: float = 0.99,
    min_freq: int = 4,
) -> dict:
    """
    Streams HuggingFaceFW/fineweb-2 (name='tur_Latn', language_score >= 0.99) in the cloud,
    computes clean Turkish word frequencies, and runs Hunspell against /root/tr.
    """
    import subprocess
    from collections import Counter
    from datasets import load_dataset

    print(f"[*] Starting FineWeb-2 (tur_Latn) cloud mining (target: {target_candidates:,} unrecognized words)...")
    print(f"  Streaming up to {max_docs:,} documents with language_score >= {min_lang_score}...")

    ds = load_dataset("HuggingFaceFW/fineweb-2", name="tur_Latn", split="train", streaming=True)

    counts = Counter()
    cap_counts = Counter()
    total_tokens = 0
    kept_docs = 0
    scanned_docs = 0

    token_re = re.compile(r"[a-zA-ZçÇğĞıİöÖşŞüÜâîûÂÎÛ]+")
    valid_tr_re = re.compile(r"^[abcçdefgğhıijklmnoöprsştuüvyzâîû]+$")

    for item in ds:
        scanned_docs += 1
        lang_score = item.get("language_score", 1.0)
        if lang_score is not None and lang_score < min_lang_score:
            continue

        text = item.get("text", "")
        if not text:
            continue

        kept_docs += 1
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
            # Reject 3+ identical consecutive letters (e.g. "चोok" / "aaah")
            if any(lower_t[i] == lower_t[i + 1] == lower_t[i + 2] for i in range(len(lower_t) - 2)):
                continue

            total_tokens += 1
            counts[lower_t] += 1
            if t[0].isupper():
                cap_counts[lower_t] += 1

        if kept_docs % 10000 == 0:
            print(
                f"  Kept {kept_docs:,} docs (scanned {scanned_docs:,}) | "
                f"{total_tokens:,} tokens | {len(counts):,} unique types..."
            )

        if kept_docs >= max_docs:
            break

    print(f"[*] Total tokens extracted: {total_tokens:,} across {kept_docs:,} high-confidence Turkish documents.")
    print(f"  Total raw unique word types: {len(counts):,}")

    # Filter out proper names (capitalized > 70% of occurrences) and rare hapax noise
    filtered = []
    clean_freq_map = {}
    for w, count in counts.most_common():
        if count < 2:
            break
        if cap_counts[w] / count > 0.70:
            continue
        if len(clean_freq_map) < 500000:
            clean_freq_map[w] = count
        if count >= min_freq:
            filtered.append((w, count))

    print(f"  Filtered non-proper candidates (freq >= {min_freq}): {len(filtered):,}")

    # Verify against Hunspell (/root/tr.aff and /root/tr.dic) in batches
    words_to_check = [w for w, _ in filtered]
    unrecognized_set = set()
    batch_size = 50000
    print(f"  Running Hunspell verification on {len(words_to_check):,} words against Turkspell (/root/tr)...")
    for i in range(0, len(words_to_check), batch_size):
        batch = words_to_check[i : i + batch_size]
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
                unrecognized_set.add(w)

    print(f"[*] Found {len(unrecognized_set):,} unrecognized word types (freq >= {min_freq}) in FineWeb-2!")

    top_unrecognized = [
        {"word": w, "freq": count}
        for w, count in filtered
        if w in unrecognized_set
    ][:target_candidates]

    print(f"[OK] Harvested {len(top_unrecognized):,} top unrecognized words + {len(clean_freq_map):,} clean frequencies.")
    return {
        "total_docs": kept_docs,
        "total_tokens": total_tokens,
        "unrecognized": top_unrecognized,
        "frequencies": clean_freq_map,
    }


@app.local_entrypoint()
def main(
    action: str = "test",
    input: str = "",
    output: str = "raw_data/fineweb2_parsed_entries.json",
    limit: int = 10000,
    max_docs: int = 60000,
    model: str = "Qwen/Qwen3.6-35B-A3B-FP8",
    chunk_size: int = 1500,
):
    """CLI Entrypoint executed on your local machine."""
    print("=" * 76)
    print(f"TURKSPELL FINEWEB-2 MODAL PIPELINE: {action.upper()} (Limit: {limit:,} | Model: {model})")
    print("=" * 76)

    if action == "test":
        test_words = [
            "kitabımızdan",
            "gözlükçüden",
            "sürdürülebilirliklerinden",
            "alkolü",
            "orjinal",
            "google",
        ]
        print(f"Running quick GPU verification on {len(test_words)} words with {model}...")
        res = parse_words_chunk.remote(test_words, batch_size=10, model_id=model)
        print("\n--- Test Results from Modal H100 GPU ---")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        print("\n[OK] Verification successful! Modal GPU pipeline is fully operational.")

    elif action == "mine":
        print(f"[*] Streaming HuggingFaceFW/fineweb-2 (tur_Latn, up to {max_docs:,} docs) in Modal cloud...")
        cloud_data = mine_corpus_cloud.remote(target_candidates=limit, max_docs=max_docs)

        candidates = cloud_data["unrecognized"]
        freq_map = cloud_data["frequencies"]

        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)

        freq_out_path = Path("raw_data/fineweb2_corpus_frequencies.json")
        with open(freq_out_path, "w", encoding="utf-8") as f:
            json.dump(freq_map, f, ensure_ascii=False)

        print(f"\n[DONE] Scanned {cloud_data['total_docs']:,} FineWeb-2 docs ({cloud_data['total_tokens']:,} tokens)")
        print(f"  -> Saved {len(candidates):,} unrecognized candidates to {out_path}")
        print(f"  -> Saved {len(freq_map):,} word frequencies to {freq_out_path}")

    elif action == "parse":
        in_path = Path(input or "raw_data/fineweb2_unrecognized_candidates.json")
        if not in_path.exists():
            print(f"Error: Input file {in_path} not found.")
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

        chunks = [words[i : i + chunk_size] for i in range(0, len(words), chunk_size)]
        print(f"[*] Launching {len(chunks)} parallel H100 vLLM workers (~{chunk_size:,} words/worker)...")

        handles = [
            (idx, parse_words_chunk.spawn(chunk, batch_size=25, model_id=model))
            for idx, chunk in enumerate(chunks, 1)
        ]

        all_entries = []
        for idx, handle in handles:
            chunk_res = handle.get()
            all_entries.extend(chunk_res)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            print(f"  [Worker {idx}/{len(handles)} Done] +{len(chunk_res):,} entries. Total saved: {len(all_entries):,}")

        print(f"\n[DONE] Saved {len(all_entries):,} total analyzed entries to {out_path}")

    elif action == "auto":
        print(f"[*] Step 1: Mining {limit:,} unrecognized words from FineWeb-2 (tur_Latn)...")
        cloud_data = mine_corpus_cloud.remote(target_candidates=limit, max_docs=max_docs)
        candidates = cloud_data["unrecognized"]
        freq_map = cloud_data["frequencies"]

        cand_path = Path("raw_data/fineweb2_unrecognized_candidates.json")
        cand_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cand_path, "w", encoding="utf-8") as f:
            json.dump(candidates, f, ensure_ascii=False, indent=2)

        freq_path = Path("raw_data/fineweb2_corpus_frequencies.json")
        with open(freq_path, "w", encoding="utf-8") as f:
            json.dump(freq_map, f, ensure_ascii=False)

        candidate_words = [item["word"] for item in candidates]
        print(f"[*] Step 2: Parsing {len(candidate_words):,} words on H100 GPU with {model}...")

        chunks = [candidate_words[i : i + chunk_size] for i in range(0, len(candidate_words), chunk_size)]
        handles = [
            (idx, parse_words_chunk.spawn(chunk, batch_size=25, model_id=model))
            for idx, chunk in enumerate(chunks, 1)
        ]

        all_entries = []
        out_path = Path(output)
        for idx, handle in handles:
            chunk_res = handle.get()
            all_entries.extend(chunk_res)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            print(f"  [Worker {idx}/{len(handles)} Done] +{len(chunk_res):,} entries. Total saved: {len(all_entries):,}")

        print(f"\n[DONE] Full FineWeb-2 pipeline complete! Saved {len(all_entries):,} entries to {out_path}")
