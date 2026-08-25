import os
import re
from collections import Counter
from datasets import load_dataset
from tqdm import tqdm
import multiprocessing

def extract_words(text):
    """Extracts valid Turkish words from text."""
    # Matches Turkish letters, including apostrophes for proper nouns
    words = re.findall(r'[a-zA-ZçğıöşüÇĞIÖŞÜ]+(?:\'[a-zA-ZçğıöşüÇĞIÖŞÜ]+)?', text.lower())
    return words

def process_batch(examples):
    """Processes a batch of dataset examples to extract word frequencies."""
    batch_counter = Counter()
    for text in examples['text']:
        if text:
            batch_counter.update(extract_words(text))
    return {'word_counts': [dict(batch_counter)]}

def main():
    print("Loading Turkish Wikipedia dataset (2023)...")
    # Load Wikipedia (Turkish)
    dataset = load_dataset("wikimedia/wikipedia", "20231101.tr", split="train")
    print(f"Loaded {len(dataset):,} articles.")
    
    print("Extracting word frequencies using CPU/multiprocessing...")
    # Map function to process in batches
    counts_dataset = dataset.map(
        process_batch, 
        batched=True, 
        batch_size=1000, 
        num_proc=multiprocessing.cpu_count(),
        remove_columns=dataset.column_names
    )
    
    print("Aggregating frequencies...")
    final_counter = Counter()
    for row in tqdm(counts_dataset):
        final_counter.update(row['word_counts'])
        
    print(f"Extracted {len(final_counter):,} unique words.")
    
    # Filter words with frequency >= 2
    filtered_words = {k: v for k, v in final_counter.items() if v >= 2}
    print(f"Kept {len(filtered_words):,} unique words (freq >= 2).")
    
    os.makedirs("data", exist_ok=True)
    out_path = "data/wiki_word_frequencies.txt"
    print(f"Saving to {out_path}...")
    
    # Sort by frequency (descending)
    sorted_words = sorted(filtered_words.items(), key=lambda item: item[1], reverse=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        for word, count in sorted_words:
            f.write(f"{word}\t{count}\n")
            
    print("Done!")

if __name__ == "__main__":
    main()
