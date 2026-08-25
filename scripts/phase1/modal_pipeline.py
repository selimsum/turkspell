import modal
import json
import os
import sys

# Define the Modal App
app = modal.App("turkspell-ml-classifier")

MODEL_ID = "Qwen/Qwen2.5-32B-Instruct"

# Pre-download the model into the container image to save time on boot
def download_model():
    from huggingface_hub import snapshot_download
    snapshot_download(MODEL_ID)

image = (
    modal.Image.from_registry(
        "vllm/vllm-openai:latest",
        setup_dockerfile_commands=[
            "RUN ln -sf /usr/bin/python3 /usr/bin/python",
            "ENTRYPOINT []"
        ]
    )
    .pip_install("huggingface_hub")
    .run_function(download_model)
)

# Define the GPU worker class with A100 80GB
@app.cls(gpu="A100-80GB", timeout=3600, image=image)
class WordClassifier:
    @modal.enter()
    def setup(self):
        from vllm import LLM, SamplingParams
        
        # Load the LLM into VRAM
        print(f"Loading {MODEL_ID} into VRAM via vLLM...")
        self.llm = LLM(model=MODEL_ID, max_model_len=4096)
        
        # Strict formatting, deterministic sampling
        self.sampling_params = SamplingParams(
            temperature=0.0, 
            max_tokens=80,
            stop=["<|im_end|>"]
        )
        
    @modal.method()
    def classify_words(self, words: list[str]):
        # Construct chat templates adhering strictly to TDK and Dil Dernegi
        prompts = []
        for w in words:
            prompt = f"""<|im_start|>system
You are an expert Turkish computational linguist validating words for Turkish spellchecking (strict TDK and Dil Derneği rules).
Analyze the given word.
If it is a foreign word (e.g. 'the', 'online', 'computer'), an HTML/URL artifact, a fragment/suffix (e.g. 'nin', 'nda', 'lar'), or a clear typo/misspelling (e.g. 'cok' instead of 'çok', 'mekan' instead of 'mekân'), return: {{"valid": false}}
If it is a valid Turkish root word, a valid proper noun, or a valid acronym (e.g. 'PKK', 'Covid', 'Bülent', 'Erdoğan'), return:
{{"valid": true, "pos": "<Noun|Verb|Adjective|ProperNoun|Acronym>", "attributes": []}}
ONLY output raw JSON. No markdown blocks, no explanation.<|im_end|>
<|im_start|>user
Word: {w}<|im_end|>
<|im_start|>assistant
"""
            prompts.append(prompt)
            
        print(f"Running vLLM batched inference on {len(prompts)} words...")
        outputs = self.llm.generate(prompts, self.sampling_params)
        
        results = {}
        for w, output in zip(words, outputs):
            results[w] = output.outputs[0].text.strip()
            
        return results

@app.local_entrypoint()
def main(input_file: str = "scripts/phase1/data/missing_roots_candidates.txt", output_file: str = "scripts/phase1/data/classified_stems.json", limit: int = 10000):
    if not os.path.exists(input_file):
        print(f"ERROR: Could not find {input_file}. Are you running this from the turkspell root directory?")
        return

    words = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 1:
                w = parts[0]
                if len(w) >= 2 and not w.isdigit() and not w.startswith(('http', 'www', 'quot', 'amp', 'nbsp')):
                    if not any(c in '<>{}[]|\\^~`*+=$%@#/' for c in w):
                        words.append(w)
            if len(words) >= limit:
                break
                
    print(f"Loaded {len(words):,} clean missing root candidates from {input_file} (limit: {limit:,}).")
    print("Connecting to Modal cloud GPUs (A100 80GB)...")
    
    classifier = WordClassifier()
    all_results = {}
    
    # Load existing results if resuming
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                all_results = json.load(f)
            print(f"Resuming: Loaded {len(all_results):,} already classified entries.")
        except Exception:
            pass
            
    # Filter words already classified
    words_to_classify = [w for w in words if w not in all_results]
    print(f"Words to classify on Modal: {len(words_to_classify):,}")
    
    if not words_to_classify:
        print("All words are already classified!")
        return

    chunk_size = 2000
    for i in range(0, len(words_to_classify), chunk_size):
        chunk = words_to_classify[i:i+chunk_size]
        print(f"Sending chunk {i//chunk_size + 1}/{(len(words_to_classify)//chunk_size)+1} to cloud ({len(chunk)} words)...")
        
        chunk_results = classifier.classify_words.remote(chunk)
        all_results.update(chunk_results)
        
        # Save intermediate progress
        with open(output_file, "w", encoding="utf-8") as out:
            json.dump(all_results, out, ensure_ascii=False, indent=2)
            
    print(f"SUCCESS! All {len(all_results):,} words classified. Final results saved to {output_file}")

