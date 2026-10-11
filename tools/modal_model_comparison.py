"""
tools/modal_model_comparison.py
================================
Head-to-head comparison of LLM models for Turkish morphological analysis on Modal A100-80GB GPU.
Tests multiple models on the same word set and reports accuracy.

Usage:
    modal run tools/modal_model_comparison.py
"""

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import modal

app = modal.App("turkspell-model-comparison")

cache_volume = modal.Volume.from_name("turkspell-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.5.0",
        "transformers>=4.44.0",
        "accelerate>=0.33.0",
        "bitsandbytes>=0.43.0",
    )
    .env({"HF_HOME": "/cache/huggingface"})
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

# Ground truth with proper Turkish characters
GROUND_TRUTH = {
    "biyouyumluluk":    {"lemma": "biyouyumluluk",    "pos": "Noun",      "attrs": []},
    "osteoklastlar":    {"lemma": "osteoklast",        "pos": "Noun",      "attrs": []},
    "gökkuşağı":        {"lemma": "gökkuşağı",         "pos": "Noun",      "attrs": ["CompoundP3sg"]},
    "yapıvermişlerdi":  {"lemma": "yapıvermek",        "pos": "Verb",      "attrs": []},
    "yıldızlararası":   {"lemma": "yıldızlararası",    "pos": ["Noun", "Adjective"], "attrs": ["CompoundP3sg"]},
    "google":           {"lemma": None,                "pos": None,        "attrs": None},
    "kitabından":       {"lemma": "kitap",             "pos": "Noun",      "attrs": ["Voicing"]},
    "ağzını":           {"lemma": "ağız",              "pos": "Noun",      "attrs": ["LastVowelDrop"]},
    "dijitalleşme":     {"lemma": "dijitalleşme",      "pos": "Noun",      "attrs": []},
    "nörolojik":        {"lemma": "nörolojik",         "pos": "Adjective", "attrs": []},
    "instagram":        {"lemma": None,                "pos": None,        "attrs": None},
    "uzaylıların":      {"lemma": "uzaylı",            "pos": "Noun",      "attrs": []},
}

TEST_WORDS = list(GROUND_TRUTH.keys())


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


def turkish_lower(s):
    if s is None:
        return None
    return (
        s.replace('I', 'ı').replace('İ', 'i')
        .replace('Î', 'î').replace('Â', 'â').replace('Û', 'û')
        .lower()
    )


def score_results(results: list[dict], ground_truth: dict) -> dict:
    """Score model results against ground truth across all 12 words."""
    correct_lemma = 0
    correct_pos = 0
    correct_attrs = 0
    total = len(ground_truth)
    details = []

    by_word = {turkish_lower(r.get("word", "")): r for r in results if isinstance(r, dict)}

    for word, gt in ground_truth.items():
        res = by_word.get(turkish_lower(word))
        if res is None:
            details.append(f"  [MISS] {word} (missing from output)")
            continue

        pred_lemma = turkish_lower(res.get("lemma"))
        gt_lemma = turkish_lower(gt["lemma"])
        pred_pos = res.get("pos")
        gt_pos = gt["pos"]
        pred_attrs = sorted(res.get("attributes") or []) if res.get("attributes") is not None else None
        gt_attrs = sorted(gt["attrs"]) if gt["attrs"] is not None else None

        lemma_ok = pred_lemma == gt_lemma
        if isinstance(gt_pos, list):
            pos_ok = pred_pos in gt_pos
        else:
            pos_ok = pred_pos == gt_pos
        attrs_ok = pred_attrs == gt_attrs

        if lemma_ok:
            correct_lemma += 1
        if pos_ok:
            correct_pos += 1
        if attrs_ok:
            correct_attrs += 1

        status = "PASS" if (lemma_ok and pos_ok and attrs_ok) else "FAIL"
        detail = f"  [{status}] {word}"
        if not lemma_ok:
            detail += f" | lemma: '{res.get('lemma')}' (expected '{gt['lemma']}')"
        if not pos_ok:
            detail += f" | pos: '{pred_pos}' (expected '{gt_pos}')"
        if not attrs_ok:
            detail += f" | attrs: {res.get('attributes')} (expected {gt['attrs']})"
        details.append(detail)

    return {
        "total": total,
        "lemma_acc": correct_lemma / total * 100 if total > 0 else 0,
        "pos_acc": correct_pos / total * 100 if total > 0 else 0,
        "attrs_acc": correct_attrs / total * 100 if total > 0 else 0,
        "perfect": sum(1 for d in details if "[PASS]" in d),
        "details": details,
    }


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=1800,
    volumes={"/cache": cache_volume},
)
def run_model_test(model_id: str) -> dict:
    """Test a single model on the benchmark words using proper Chat Template."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    import time

    gpu_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"[*] Testing {model_id} on {gpu_name} ({vram:.0f} GB VRAM)")

    tokenizer = AutoTokenizer.from_pretrained(model_id)

    load_start = time.time()
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
    load_time = time.time() - load_start
    print(f"  [{model_id}] Loaded in {load_time:.1f}s")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": FEW_SHOT_USER},
        {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
        {"role": "user", "content": f"Input: {json.dumps(TEST_WORDS, ensure_ascii=False)}"},
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    gen_start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=False,
        )
    gen_time = time.time() - gen_start

    resp = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    parsed = extract_json_array(resp)

    print(f"  [{model_id}] Generated in {gen_time:.1f}s ({len(parsed) if parsed else 0} items)")

    return {
        "model_id": model_id,
        "gpu": gpu_name,
        "vram_gb": round(vram, 1),
        "load_time_s": round(load_time, 1),
        "gen_time_s": round(gen_time, 1),
        "raw_output": resp[:2000],
        "parsed": parsed if parsed else [],
    }


@app.local_entrypoint()
def main():
    """Run all models in parallel on A100-80GB GPUs and compare results."""
    models = [
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-14B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct",
    ]

    print("=" * 72)
    print("TURKSPELL MODEL COMPARISON: Turkish Morphological Analysis (12 Words)")
    print("=" * 72)

    handles = []
    for model_id in models:
        print(f"  Launching: {model_id}")
        handles.append((model_id, run_model_test.spawn(model_id)))

    all_results = []
    for model_id, handle in handles:
        try:
            result = handle.get()
            all_results.append(result)
        except Exception as e:
            print(f"  [ERROR] {model_id} failed: {e}")

    print("\n" + "=" * 72)
    print("RESULTS")
    print("=" * 72)

    summary_rows = []
    for result in all_results:
        model_short = result["model_id"].split("/")[-1]
        parsed = result.get("parsed", [])
        scores = score_results(parsed, GROUND_TRUTH)

        print(f"\n--- {model_short} ---")
        print(f"  GPU: {result['gpu']} | Load: {result['load_time_s']}s | Inference: {result['gen_time_s']}s")
        print(f"  Lemma Accuracy:     {scores['lemma_acc']:.1f}%")
        print(f"  POS Accuracy:       {scores['pos_acc']:.1f}%")
        print(f"  Attribute Accuracy: {scores['attrs_acc']:.1f}%")
        print(f"  Perfect Matches:    {scores['perfect']}/{scores['total']}")
        for d in scores["details"]:
            print(d)

        summary_rows.append({
            "model": model_short,
            "lemma": f"{scores['lemma_acc']:.1f}%",
            "pos": f"{scores['pos_acc']:.1f}%",
            "attrs": f"{scores['attrs_acc']:.1f}%",
            "perfect": f"{scores['perfect']}/{scores['total']}",
            "gen_time": f"{result['gen_time_s']}s",
        })

    print("\n" + "=" * 72)
    print("SUMMARY TABLE")
    print("=" * 72)
    print(f"{'Model':<30} {'Lemma':>7} {'POS':>7} {'Attrs':>7} {'Perfect':>9} {'Speed':>8}")
    print("-" * 72)
    for row in summary_rows:
        print(f"{row['model']:<30} {row['lemma']:>7} {row['pos']:>7} {row['attrs']:>7} {row['perfect']:>9} {row['gen_time']:>8}")
    print("=" * 72)

    output_path = Path("raw_data/model_comparison_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nFull results saved to {output_path}")
