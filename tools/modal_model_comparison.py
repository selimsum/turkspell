"""
tools/modal_model_comparison.py
================================
Head-to-head comparison of Modal LLM models for Turkish morphological analysis & rule mining.
Evaluates accuracy across:
  1. Lemma / Root extraction
  2. Part of Speech (POS)
  3. Phonological Attributes (Voicing, NoVoicing, LastVowelDrop, Doubling, InverseHarmony, CompoundP3sg)
  4. Derivation Depth & Category (0: inflection, 1-2: productive derivation, 3+: lexicalized lemma, null: typo/foreign)

Usage:
    modal run tools/modal_model_comparison.py
"""

import json
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import modal

app = modal.App("turkspell-model-comparison")

cache_volume = modal.Volume.from_name("turkspell-cache", create_if_missing=True)

vllm_image = (
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
   - 'NoVoicing': ONLY if "lemma" ends in p, ç, t, k, g and does NOT soften before a vowel suffix (e.g., "kod" does not end in p/ç/t/k so []; "ahlak" -> ahlakı has 'NoVoicing'; "sepet" -> sepeti has 'NoVoicing'; "osteoklast" -> osteoklastı has 'NoVoicing').
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

# 25-word comprehensive Ground Truth covering all 4 architectural categories
GROUND_TRUTH = {
    # Category 1: Inflection & Phonological Attributes
    "kitabından":                {"lemma": "kitap",              "pos": "Noun",               "attrs": ["Voicing"],        "depth": [0]},
    "ağzını":                    {"lemma": "ağız",               "pos": "Noun",               "attrs": ["LastVowelDrop"],  "depth": [0]},
    "burnundan":                 {"lemma": "burun",              "pos": "Noun",               "attrs": ["LastVowelDrop"],  "depth": [0]},
    "alkolü":                    {"lemma": "alkol",              "pos": "Noun",               "attrs": ["InverseHarmony"], "depth": [0]},
    "amiralin":                  {"lemma": "amiral",             "pos": "Noun",               "attrs": ["InverseHarmony"], "depth": [0]},
    "hakkını":                   {"lemma": "hak",                "pos": "Noun",               "attrs": ["Doubling"],       "depth": [0]},
    "zammın":                    {"lemma": "zam",                "pos": "Noun",               "attrs": ["Doubling"],       "depth": [0]},
    "ahlakı":                    {"lemma": "ahlak",              "pos": "Noun",               "attrs": ["NoVoicing"],      "depth": [0]},
    "osteoklastlar":             {"lemma": "osteoklast",         "pos": "Noun",               "attrs": ["NoVoicing", []],  "depth": [0]},
    "gökkuşağı":                 {"lemma": "gökkuşağı",          "pos": "Noun",               "attrs": ["CompoundP3sg"],   "depth": [0]},
    "yıldızlararası":            {"lemma": "yıldızlararası",     "pos": ["Noun", "Adjective"],"attrs": ["CompoundP3sg"],   "depth": [0, 1]},
    "nörolojik":                 {"lemma": "nörolojik",          "pos": "Adjective",          "attrs": ["NoVoicing", []],  "depth": [0, 1]},
    # Category 2: 1-2 Level Productive Derivations
    "uzaylıların":               {"lemma": "uzaylı",             "pos": ["Noun", "Adjective"],"attrs": [],                 "depth": [1]},
    "dijitalleşme":              {"lemma": "dijitalleşme",       "pos": "Noun",               "attrs": [],                 "depth": [1, 2]},
    "yapıvermişlerdi":           {"lemma": "yapıvermek",         "pos": "Verb",               "attrs": [],                 "depth": [0, 1]},
    "gözlükçüden":               {"lemma": "gözlükçü",           "pos": "Noun",               "attrs": [],                 "depth": [2]},
    "yerelleştirmesi":           {"lemma": ["yerelleştirme", "yerelleştirmek"], "pos": ["Noun", "Verb"], "attrs": [],      "depth": [2]},
    "okunabilirliği":            {"lemma": "okunabilirlik",      "pos": "Noun",               "attrs": ["Voicing"],        "depth": [2, 3]},
    # Category 3: 3+ Level Lexicalized Derivations
    "sürdürülebilirliklerinden": {"lemma": "sürdürülebilirlik",  "pos": "Noun",               "attrs": ["Voicing"],        "depth": [3]},
    "kurumsallaştırılması":      {"lemma": ["kurumsallaştırılma", "kurumsallaştırmak", "kurumsallaştırılmak"], "pos": ["Noun", "Verb"], "attrs": [], "depth": [3]},
    "biyouyumluluk":             {"lemma": "biyouyumluluk",      "pos": "Noun",               "attrs": ["Voicing", []],    "depth": [0, 2, 3]},
    # Category 4: Typos, Foreign & Brands
    "orjinal":                   {"lemma": None,                 "pos": None,                 "attrs": None,               "depth": [None], "correction": "orijinal"},
    "yalnış":                    {"lemma": None,                 "pos": None,                 "attrs": None,               "depth": [None], "correction": "yanlış"},
    "google":                    {"lemma": None,                 "pos": None,                 "attrs": None,               "depth": [None]},
    "instagram":                 {"lemma": None,                 "pos": None,                 "attrs": None,               "depth": [None]},
}

TEST_WORDS = list(GROUND_TRUTH.keys())


def turkish_lower(s):
    if s is None:
        return None
    return (
        str(s)
        .replace("I", "ı")
        .replace("İ", "i")
        .replace("Î", "î")
        .replace("Â", "â")
        .replace("Û", "û")
        .lower()
    )


def extract_json_array(text: str):
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


def score_results(results: list[dict], ground_truth: dict) -> dict:
    correct_lemma = 0
    correct_pos = 0
    correct_attrs = 0
    correct_depth = 0
    total = len(ground_truth)
    details = []

    by_word = {turkish_lower(r.get("word", "")): r for r in results if isinstance(r, dict)}

    for word, gt in ground_truth.items():
        res = by_word.get(turkish_lower(word))
        if res is None:
            details.append(f"  [MISS] {word} (missing from output)")
            continue

        pred_lemma = turkish_lower(res.get("lemma"))
        gt_lemmas = [turkish_lower(x) for x in gt["lemma"]] if isinstance(gt["lemma"], list) else [turkish_lower(gt["lemma"])]
        lemma_ok = pred_lemma in gt_lemmas

        pred_pos = res.get("pos")
        gt_pos = gt["pos"]
        pos_ok = (pred_pos in gt_pos) if isinstance(gt_pos, list) else (pred_pos == gt_pos)

        pred_attrs = sorted(res.get("attributes") or []) if res.get("attributes") is not None else None
        gt_attrs = gt["attrs"]
        if gt_attrs is None:
            attrs_ok = pred_attrs is None
        elif any(isinstance(x, list) for x in gt_attrs):
            acceptable = [sorted(x) if isinstance(x, list) else [x] for x in gt_attrs]
            attrs_ok = pred_attrs in acceptable
        else:
            attrs_ok = pred_attrs == sorted(gt_attrs)

        pred_depth = res.get("derivation_depth")
        depth_ok = pred_depth in gt["depth"]

        if lemma_ok:
            correct_lemma += 1
        if pos_ok:
            correct_pos += 1
        if attrs_ok:
            correct_attrs += 1
        if depth_ok:
            correct_depth += 1

        status = "PASS" if (lemma_ok and pos_ok and attrs_ok) else "FAIL"
        detail = f"  [{status}] {word:<26}"
        if not lemma_ok:
            detail += f" | lemma: '{res.get('lemma')}' (exp {gt['lemma']})"
        if not pos_ok:
            detail += f" | pos: '{pred_pos}' (exp {gt_pos})"
        if not attrs_ok:
            detail += f" | attrs: {res.get('attributes')} (exp {gt['attrs']})"
        if not depth_ok:
            detail += f" | depth: {pred_depth} (exp {gt['depth']})"
        details.append(detail)

    return {
        "total": total,
        "lemma_acc": correct_lemma / total * 100 if total > 0 else 0,
        "pos_acc": correct_pos / total * 100 if total > 0 else 0,
        "attrs_acc": correct_attrs / total * 100 if total > 0 else 0,
        "depth_acc": correct_depth / total * 100 if total > 0 else 0,
        "perfect": sum(1 for d in details if "[PASS]" in d),
        "details": details,
    }


@app.function(
    image=vllm_image,
    gpu="H100",
    timeout=1800,
    volumes={"/cache": cache_volume},
)
def run_vllm_model_test(model_id: str) -> dict:
    """Runs high-speed FP8 / MoE inference on Modal H100 GPU using vLLM."""
    import torch
    from vllm import LLM, SamplingParams

    gpu_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"[*] Loading {model_id} with vLLM on {gpu_name} ({vram:.0f} GB VRAM)...")

    load_start = time.time()
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
    load_time = time.time() - load_start
    print(f"  [{model_id}] Loaded in {load_time:.1f}s")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": FEW_SHOT_USER},
        {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
        {"role": "user", "content": f"Input: {json.dumps(TEST_WORDS, ensure_ascii=False)}"},
    ]

    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=3072,
    )

    gen_start = time.time()
    try:
        outputs = llm.chat(
            messages=[messages],
            sampling_params=sampling_params,
            chat_template_kwargs={"enable_thinking": False},
        )
    except TypeError:
        outputs = llm.chat(
            messages=[messages],
            sampling_params=sampling_params,
        )
    gen_time = time.time() - gen_start

    resp = outputs[0].outputs[0].text
    parsed = extract_json_array(resp)
    print(f"  [{model_id}] Generated in {gen_time:.2f}s ({len(parsed) if parsed else 0} items)")

    return {
        "model_id": model_id,
        "gpu": gpu_name,
        "vram_gb": round(vram, 1),
        "load_time_s": round(load_time, 1),
        "gen_time_s": round(gen_time, 2),
        "raw_output": resp[:2500],
        "parsed": parsed if parsed else [],
    }


@app.local_entrypoint()
def main():
    models = [
        "Qwen/Qwen3.6-35B-A3B-FP8",
        "Qwen/Qwen3.5-27B-FP8",
    ]

    print("=" * 84)
    print(f"TURKSPELL MODAL GPU MODEL COMPARISON ({len(TEST_WORDS)} Challenging Words)")
    print("=" * 84)

    handles = []
    for model_id in models:
        print(f"  Launching on H100: {model_id}")
        handles.append((model_id, run_vllm_model_test.spawn(model_id)))

    all_results = []
    # Preserve previously captured Qwen3.8-2.4T-A95B result if present
    output_path = Path("raw_data/model_comparison_results.json")
    if output_path.exists():
        try:
            prev = json.loads(output_path.read_text(encoding="utf-8"))
            for item in prev:
                if item.get("model_id") == "Qwen/Qwen3.8-2.4T-A95B" and item.get("parsed"):
                    all_results.append(item)
        except Exception:
            pass

    for model_id, handle in handles:
        try:
            result = handle.get()
            all_results.append(result)
        except Exception as e:
            print(f"  [ERROR] {model_id} failed: {e}")

    print("\n" + "=" * 84)
    print("DETAILED EVALUATION RESULTS")
    print("=" * 84)

    summary_rows = []
    for result in all_results:
        model_short = result["model_id"].split("/")[-1]
        parsed = result.get("parsed", [])
        scores = score_results(parsed, GROUND_TRUTH)

        print(f"\n--- {model_short} ({result['gen_time_s']}s) ---")
        print(f"  Lemma Accuracy:     {scores['lemma_acc']:.1f}%")
        print(f"  POS Accuracy:       {scores['pos_acc']:.1f}%")
        print(f"  Attribute Accuracy: {scores['attrs_acc']:.1f}%")
        print(f"  Depth Accuracy:     {scores['depth_acc']:.1f}%")
        print(f"  Perfect Matches:    {scores['perfect']}/{scores['total']}")
        for d in scores["details"]:
            if "[FAIL]" in d or "[MISS]" in d:
                print(d)

        summary_rows.append({
            "model": model_short,
            "lemma": f"{scores['lemma_acc']:.1f}%",
            "pos": f"{scores['pos_acc']:.1f}%",
            "attrs": f"{scores['attrs_acc']:.1f}%",
            "depth": f"{scores['depth_acc']:.1f}%",
            "perfect": f"{scores['perfect']}/{scores['total']}",
            "gen_time": f"{result['gen_time_s']}s",
        })

    print("\n" + "=" * 84)
    print("SUMMARY TABLE")
    print("=" * 84)
    print(f"{'Model':<28} {'Lemma':>7} {'POS':>7} {'Attrs':>7} {'Depth':>7} {'Perfect':>9} {'Latency':>9}")
    print("-" * 84)
    for row in summary_rows:
        print(
            f"{row['model']:<28} {row['lemma']:>7} {row['pos']:>7} "
            f"{row['attrs']:>7} {row['depth']:>7} {row['perfect']:>9} {row['gen_time']:>9}"
        )
    print("=" * 84)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nFull results saved to {output_path}")
