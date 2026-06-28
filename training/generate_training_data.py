# generate_training_data.py
import os
import re
import csv
import subprocess
import json
from collections import Counter

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').replace('Î', 'î').replace('Â', 'â').replace('Û', 'û').lower()

def load_english_words():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    english_path = os.path.join(base_dir, "data", "english_words_large.txt")
    if not os.path.exists(english_path):
        print(f"Warning: {english_path} not found. English cleaning will be skipped.")
        return set()
    with open(english_path, "r", encoding="utf-8", errors="ignore") as f:
        return {turkish_lowercase(line.strip()) for line in f if line.strip()}

def load_roots():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    roots_path = os.path.join(base_dir, "data", "merged_dictionary_cleaned.txt")
    if not os.path.exists(roots_path):
        print(f"Warning: {roots_path} not found.")
        return set()
    with open(roots_path, "r", encoding="utf-8", errors="ignore") as f:
        return {turkish_lowercase(line.strip()) for line in f if line.strip()}

def process_corpus(file_path, english_words, proper_names_global):
    """
    Reads corpus, tokenizes, filters out non-alpha, tracks capitalized forms to identify proper names.
    Returns a Counter of lowercase candidates and a set of local proper names.
    """
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found. Skipping.")
        return Counter(), set()
        
    print(f"Processing corpus: {file_path}...")
    word_counter = Counter()
    capitalized_counts = Counter()
    total_counts = Counter()
    
    # Process line-by-line to manage memory
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # Tokenize words containing Turkish alphabetic characters and circumflexes
            tokens = re.findall(r'[a-zA-ZçÇğĞıİöÖşŞüÜâîûÂÎÛ]+', line)
            for tok in tokens:
                if len(tok) < 2:
                    continue
                # If it has digits or non-turkish chars, skip
                if re.search(r'[0-9]', tok):
                    continue
                    
                lower_tok = turkish_lowercase(tok)
                total_counts[lower_tok] += 1
                
                # Track if it is capitalized
                if tok[0].isupper():
                    capitalized_counts[lower_tok] += 1
                    
    # Proper names are words that are capitalized most of the time (e.g. > 70% of occurrences)
    # and occur at least 3 times.
    proper_names = set()
    for w, count in total_counts.items():
        if count >= 3:
            cap_ratio = capitalized_counts[w] / count
            if cap_ratio > 0.70:
                proper_names.add(w)
                
    # Filter candidates
    candidates = Counter()
    # Re-read or just iterate through total_counts
    for w, count in total_counts.items():
        # Clean English words
        if w in english_words:
            continue
        # Clean Proper names
        if w in proper_names or w in proper_names_global:
            continue
        # Remove words with Q, W, X
        if re.search(r'[qwxQWX]', w):
            continue
        candidates[w] = count
        
    return candidates, proper_names

def find_misspelled_words(words_list, dict_path="tr"):
    """
    Runs hunspell -l on the list of words to identify misspelled/unrecognized words.
    """
    print(f"Running Hunspell on {len(words_list)} unique candidates...")
    temp_file = "temp_dataset_words.txt"
    with open(temp_file, "w", encoding="utf-8", newline="\n") as f:
        for w in words_list:
            f.write(w + "\n")
            
    # Run hunspell -l
    try:
        with open(temp_file, 'r', encoding='utf-8') as stdin_f:
            p = subprocess.Popen(
                ['hunspell', '-d', dict_path, '-l'],
                stdin=stdin_f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = p.communicate()
    except FileNotFoundError:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise RuntimeError(
            "\n\n[ERROR] 'hunspell' binary was not found on your system.\n"
            "If you are running on Lightning.ai Studio (Linux/Ubuntu), please install it by running the following command in the Studio terminal:\n\n"
            "    sudo apt-get update && sudo apt-get install -y hunspell\n\n"
        )
    
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    unrecognized = set(stdout.decode('utf-8', errors='replace').splitlines())
    return unrecognized

def generate_training_data():
    print("=== STARTING TRAINING DATA GENERATION ===")
    
    # Ensure local dictionary is compiled first
    print("Recompiling dictionary to ensure tr.aff is up to date...")
    try:
        import compile_hunspell
        compile_hunspell.compile_dictionary()
    except Exception as e:
        print(f"Error compiling dictionary: {e}")
        
    english_words = load_english_words()
    roots = load_roots()
    
    # Process both corpora
    proper_names = set()
    candidates = Counter()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for corp in ["wiki_corpus.txt", "magazine_corpus.txt"]:
        corp_path = os.path.join(base_dir, "data", corp)
        cand, prop = process_corpus(corp_path, english_words, proper_names)
        candidates.update(cand)
        proper_names.update(prop)
        
    print(f"Total unique cleaned candidates: {len(candidates)}")
    
    # Take high-frequency candidates (e.g. freq >= 10) to avoid random typos in the corpus
    high_freq_candidates = [w for w, count in candidates.items() if count >= 10]
    print(f"High-frequency candidates (freq >= 10): {len(high_freq_candidates)}")
    
    # Find unrecognized words (False Negatives)
    unrecognized = find_misspelled_words(high_freq_candidates)
    print(f"Total unrecognized high-frequency words: {len(unrecognized)}")
    
    # Group unrecognized words by their root stems
    # We find if a prefix of the unrecognized word is a known root
    grouped_gaps = {}
    for w in unrecognized:
        longest_root = ""
        for r in roots:
            if w.startswith(r) and len(r) > len(longest_root):
                # Ensure the remainder looks like Turkish suffixes (e.g. doesn't contain random characters)
                suffix = w[len(r):]
                if suffix and re.match(r'^[aeıioöuüâîûbçdfgğhjklmnprsştvyz]+$', suffix):
                    longest_root = r
        if longest_root:
            if longest_root not in grouped_gaps:
                grouped_gaps[longest_root] = []
            grouped_gaps[longest_root].append(w)
            
    # Filter groups that have at least 3 unrecognized inflections (indicates a missing rule/aspect pattern)
    valid_groups = {r: infs for r, infs in grouped_gaps.items() if len(infs) >= 3}
    print(f"Grouped root gaps identified: {len(valid_groups)}")
    
    # Load generate_grammar_rules.py content to provide context for the prompt
    with open("generate_grammar_rules.py", "r", encoding="utf-8") as f:
        grammar_rules_code = f.read()
        
    # Extract only the suffix templates definitions (to keep context window short)
    tam_match = re.search(r'TAM\s*=\s*\[(.*?)\]', grammar_rules_code, re.DOTALL)
    copulas_match = re.search(r'COPULAS_VOWEL\s*=\s*\[(.*?)\]', grammar_rules_code, re.DOTALL)
    
    tam_context = tam_match.group(0) if tam_match else "TAM = []"
    copulas_context = copulas_match.group(0) if copulas_match else "COPULAS_VOWEL = []"
    
    samples = []
    for root, infs in sorted(valid_groups.items()):
        # Create the training prompt
        instruction = f"Determine the missing suffix templates and propose code edits for generate_grammar_rules.py to accept unrecognized forms of root '{root}'."
        
        # We will formulate output suggestions by matching the suffix pattern
        # Since this is a training dataset generator, we mock/infer the optimal output formats
        # to teach the model how to edit. For example, if unrecognized inflections have 'iverdi',
        # the model should output the python addition: TAM.append(...) or a new rule group.
        
        suggested_suffix_templates = []
        for inf in infs:
            suffix = inf[len(root):]
            # Simple heuristic template mapping (e.g. replace actual vowels with harmony variables A, I, U, D, C)
            # e.g., 'di' -> 'dI', 'ler' -> 'lAr', 'diler' -> 'dIlAr'
            template = suffix.replace('ı', 'I').replace('i', 'I').replace('u', 'U').replace('ü', 'U')
            template = template.replace('a', 'A').replace('e', 'A')
            template = template.replace('d', 'D').replace('t', 'D').replace('c', 'C').replace('ç', 'C')
            suggested_suffix_templates.append(template)
            
        suggested_suffix_templates = sorted(list(set(suggested_suffix_templates)))
        
        input_text = (
            f"Root stem: {root}\n"
            f"Unrecognized inflections found in corpus: {', '.join(infs)}\n\n"
            f"Current generator suffix templates context:\n"
            f"{tam_context}\n"
            f"{copulas_context}"
        )
        
        # We want the output to be python code block modifying the suffix lists or template definitions
        output_text = (
            f"To resolve the unrecognized inflections for '{root}', we need to add the following suffix templates:\n"
            f"```python\n"
            f"# Suggested additions to TAM list:\n"
            f"TAM.extend({json.dumps(suggested_suffix_templates)})\n"
            f"```"
        )
        
        samples.append({
            "instruction": instruction,
            "input": input_text,
            "output": output_text
        })
        
    # Write to train_dataset.jsonl
    output_dataset = "train_dataset.jsonl"
    with open(output_dataset, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            
    print(f"Generated {len(samples)} training pairs and saved to {output_dataset}.")
    print("=== DATASET GENERATION COMPLETE ===")

if __name__ == "__main__":
    generate_training_data()
