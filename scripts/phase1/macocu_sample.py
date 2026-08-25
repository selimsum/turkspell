import json
import time
from collections import Counter

file_path = r"C:\gemini\turkspell\raw_data\MaCoCu-Genre.tr.jsonl"
print(f"Sampling genres from: {file_path}...\n")

genres = Counter()
forum_samples = []
other_samples = []

start = time.time()
with open(file_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 100000:
            break
            
        try:
            data = json.loads(line)
            genre = data.get('genre', 'Unknown')
            genres[genre] += 1
            
            text = (data.get('title', '') + " | " + data.get('text', '')).strip()
            
            # Save some short samples
            if len(text) > 50 and len(text) < 200:
                if 'forum' in genre.lower() and len(forum_samples) < 3:
                    forum_samples.append(f"[{genre}] {text}")
                elif 'forum' not in genre.lower() and len(other_samples) < 3:
                    other_samples.append(f"[{genre}] {text}")
                    
        except json.JSONDecodeError:
            pass

print("--- GENRE DISTRIBUTION (First 100,000 lines) ---")
for g, count in genres.most_common():
    print(f"{g}: {count:,} ({(count/100000)*100:.1f}%)")

print("\n--- FORUM SAMPLES ---")
for s in forum_samples:
    print(s)

print("\n--- NON-FORUM SAMPLES ---")
for s in other_samples:
    print(s)
