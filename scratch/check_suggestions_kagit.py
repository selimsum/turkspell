import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_words = ["kağıt", "kağıdın", "kağıdı"]

for word in test_words:
    result = subprocess.run(
        ['hunspell', '-a', '-d', 'tr'],
        input=word,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    print(f"Suggestions for '{word}':")
    print(result.stdout)
