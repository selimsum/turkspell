import sys
import subprocess
import re

sys.stdout.reconfigure(encoding='utf-8')

known_suffixes = {'nin', 'nın', 'yi', 'dan', 'nun', 'nı', 'di', 'yı', 'nde', 'lı', 'ka', 'nda', 'ri', 'daki', 'lar', 'ler', 'rı', 'nu', 'dı', 'du', 'tı', 'ğı', 'ği', 'dir', 'te', 'ta', 'den', 'ye', 'ya', 'tan', 'ten', 'ce', 'ca', 'ler', 'lar'}
known_web = {'com', 'tr', 'www', 'web', 'play', 'off', 'http', 'the', 'and', 'gov', 'anti', 'rock', 'jpg', 'aa', 'double', 'dha', 'https', 'tweet', 'tv', 'mp', 'in', 'of', 'for', 'on', 'to', 'at', 'is', 'by', 'with', 'from', 'as', 'an', 'are', 'this', 'that', 'it', 'not', 'be', 'or', 'all'}

freq_words = []
with open('scripts/phase1/data/ts_timeline_frequencies.txt', 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) == 2:
            w, cnt = parts[0], int(parts[1])
            if cnt >= 2000:
                if w.islower() and "'" not in w and len(w) >= 3 and w.isalpha():
                    if not any(c in w for c in 'wxq') and w not in known_suffixes and w not in known_web:
                        freq_words.append((w, cnt))
            else:
                break

p = subprocess.Popen(['hunspell', '-d', 'tr', '-l'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
out, _ = p.communicate('\n'.join(w[0] for w in freq_words))
misspelled = set(line.strip() for line in out.splitlines() if line.strip())

rejected = [(w, c) for w, c in freq_words if w in misspelled]
print(f"Candidates tested: {len(freq_words)}")
print(f"Rejected count: {len(rejected)}")
print(f"{'Word':25} {'Frequency':>10}")
print("-" * 37)
for w, c in rejected[:60]:
    print(f"{w:25} {c:10,}")
