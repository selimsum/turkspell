"""
Use an LLM to perform morphological analysis on undetected Turkish words,
extracting root lemmas, POS tags, and morphotactic attributes.

Usage:
    python llm_morphology_parser.py [--model MODEL_ID] [--input FILE] [--limit N] [--batch-size N]

Requirements:
    pip install transformers torch accelerate
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

SYSTEM_PROMPT = """You are an expert morphological analyzer for Turkish.
Your task is to parse a list of Turkish words and determine:
1. The correct Root Lemma (in lowercase). For verbs, include the infinitive suffix (e.g., "yapmak", not "yap").
2. The Part of Speech (POS): one of 'Noun', 'Verb', 'Adjective', 'Adverb'.
3. Attributes (list of strings, can be empty []):
   - 'Voicing' if the last consonant of the root changes when a vowel-starting suffix is appended (e.g., kitap->kitabı, renk->rengi, ağaç->ağacı, umut->umudu).
   - 'LastVowelDrop' if the last vowel of the root drops when inflected (e.g., burun->burnu, ağız->ağzı).
   - 'CompoundP3sg' for compound words with inherent 3rd person possessive (e.g., yıldızlararası, gökkuşağı).

Rules:
- If a word is a typo, brand name, foreign word (English, Latin, etc.), or gibberish, set all fields to null.
- If a word is just an inflected form of a common root, still parse it normally.
- Respond ONLY with a valid JSON array. No markdown fences, no explanations, no extra text.
"""

FEW_SHOT = """Example:
Input: ["kitabımızdan", "yapıvermiş", "süpersimetrik", "google", "nörobiyolojik", "osteoklastlar", "paratiroid"]
Output:
[
  {"word": "kitabımızdan", "lemma": "kitap", "pos": "Noun", "attributes": ["Voicing"]},
  {"word": "yapıvermiş", "lemma": "yapıvermek", "pos": "Verb", "attributes": []},
  {"word": "süpersimetrik", "lemma": "süpersimetrik", "pos": "Adjective", "attributes": []},
  {"word": "google", "lemma": null, "pos": null, "attributes": null},
  {"word": "nörobiyolojik", "lemma": "nörobiyolojik", "pos": "Adjective", "attributes": []},
  {"word": "osteoklastlar", "lemma": "osteoklast", "pos": "Noun", "attributes": []},
  {"word": "paratiroid", "lemma": "paratiroid", "pos": "Noun", "attributes": []}
]"""

VALID_POS = {'Noun', 'Verb', 'Adjective', 'Adverb'}


def turkish_lowercase(text):
    return (
        text.replace('I', '\u0131').replace('\u0130', 'i')
        .replace('\u00ce', '\u00ee').replace('\u00c2', '\u00e2').replace('\u00db', '\u00fb')
        .lower()
    )


def load_root_words():
    """Load the merged root dictionary (lemmas only)."""
    dictionaries = set()
    path = 'merged_dictionary_cleaned.txt'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                w = line.strip()
                if w:
                    dictionaries.add(turkish_lowercase(w))
    return dictionaries


def load_candidates(input_file, limit):
    """Load candidate words from the undetected words file."""
    candidates = []
    with open(input_file, 'r', encoding='utf-8') as f:
        header = next(f, None)  # Skip header
        for line in f:
            parts = line.strip().split('\t')
            if parts and parts[0]:
                candidates.append(parts[0])
            if len(candidates) >= limit:
                break
    return candidates


def load_existing_results(output_path):
    """Load previously parsed results for resumability."""
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            already_parsed = {r['word'] for r in data if isinstance(r, dict)}
            print(f"Loaded {len(already_parsed)} previously parsed words from {output_path}")
            return data, already_parsed
        except (json.JSONDecodeError, KeyError):
            pass
    return [], set()


def extract_json_array(text):
    """Robustly extract a JSON array from LLM output that may contain wrapping."""
    # Strip markdown fences
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = text.strip()

    # Try to find the JSON array boundaries
    start = text.find('[')
    if start == -1:
        return None

    # Find matching closing bracket
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


def validate_result(result):
    """Validate a single parsed result object."""
    if not isinstance(result, dict):
        return False
    if 'word' not in result:
        return False
    # Null results (foreign words) are valid
    if result.get('lemma') is None:
        return True
    # Check POS
    if result.get('pos') not in VALID_POS:
        return False
    # Check lemma is a non-empty string
    if not isinstance(result.get('lemma'), str) or not result['lemma'].strip():
        return False
    # Check attributes is a list
    if not isinstance(result.get('attributes'), list):
        return False
    return True


def parse_candidates_with_llm(model_id, input_file, limit, batch_size):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run extract_oscar_vocab.py first.")
        sys.exit(1)

    # Load root words as source of truth
    root_words = load_root_words()
    print(f"Loaded {len(root_words)} root words from merged_dictionary_cleaned.txt.")

    # Load candidates
    candidates = load_candidates(input_file, limit)
    if not candidates:
        print("No candidates found to process.")
        return

    # Load existing results for resumability
    output_path = "oscar_parsed_candidates.json"
    parsed_results, already_parsed = load_existing_results(output_path)

    # Filter out already-parsed words
    remaining = [w for w in candidates if w not in already_parsed]
    print(f"Total candidates: {len(candidates)}, already parsed: {len(already_parsed)}, remaining: {len(remaining)}")

    if not remaining:
        print("All candidates have already been parsed. Nothing to do.")
        return

    # Lazy import torch to give a clear error message
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("Error: 'transformers' and 'torch' are required.")
        print("Install with: pip install transformers torch accelerate")
        sys.exit(1)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device} | Model: {model_id}")

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto"
    )

    total_batches = (len(remaining) + batch_size - 1) // batch_size
    new_lemmas = set()  # Track unique lemmas for deduplication

    for batch_idx in range(0, len(remaining), batch_size):
        batch = remaining[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        print(f"\n--- Batch {batch_num}/{total_batches} ({len(batch)} words) ---")

        prompt = (
            f"{SYSTEM_PROMPT}\n\n{FEW_SHOT}\n\n"
            f"Input: {json.dumps(batch)}\nOutput:\n"
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=2048,
                do_sample=False,
            )

        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

        batch_results = extract_json_array(response)
        if batch_results is None:
            print(f"  WARNING: Failed to parse JSON from LLM response. Skipping batch.")
            print(f"  Raw response (first 500 chars): {response[:500]}")
            continue

        valid_count = 0
        for res in batch_results:
            if not validate_result(res):
                print(f"  Skipped invalid result: {res}")
                continue

            word = res.get('word', '')
            lemma = res.get('lemma')

            if lemma is None:
                # Foreign/invalid word — skip
                already_parsed.add(word)
                continue

            # Check if root lemma is in our valid root words
            lower_lemma = turkish_lowercase(lemma)
            if lower_lemma not in root_words:
                print(f"  ⊘ {word} → lemma '{lemma}' not in merged_dictionary_cleaned.txt (skipped)")
                already_parsed.add(word)
                continue

            # Deduplication: don't add the same lemma twice
            if lemma not in new_lemmas:
                new_lemmas.add(lemma)
                parsed_results.append(res)
                valid_count += 1
                print(f"  ✓ {word} → lemma: {lemma}, POS: {res['pos']}, attrs: {res['attributes']}")
            else:
                print(f"  ⊘ {word} → lemma: {lemma} (duplicate, skipped)")

            already_parsed.add(word)

        print(f"  Batch result: {valid_count} new lemmas extracted")

        # Save after every batch for crash resilience
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_results, f, ensure_ascii=False, indent=2)

    print(f"\nDone! Total unique lemmas extracted: {len(parsed_results)}")
    print(f"Results saved to {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse Turkish morphology using an LLM")
    parser.add_argument('--model', type=str, default='Qwen/Qwen2.5-Coder-7B-Instruct',
                        help='Hugging Face model ID (default: Qwen/Qwen2.5-Coder-7B-Instruct)')
    parser.add_argument('--input', type=str, default='oscar_undetected_words.txt',
                        help='Input file of undetected words (default: oscar_undetected_words.txt)')
    parser.add_argument('--limit', type=int, default=500,
                        help='Maximum number of candidates to process (default: 500)')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Number of words per LLM batch (default: 10)')
    args = parser.parse_args()

    parse_candidates_with_llm(
        model_id=args.model,
        input_file=args.input,
        limit=args.limit,
        batch_size=args.batch_size
    )
