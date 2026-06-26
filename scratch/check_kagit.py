import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_words = ["kâğıt", "kâğıdın", "kâğıdı"]

# Check if these words are accepted by our dictionary
result = subprocess.run(['hunspell', '-d', 'tr', '-l'], input='\n'.join(test_words), capture_output=True, text=True, encoding='utf-8')
errors = result.stdout.splitlines()

print("Checking word acceptance in Turkspell:")
for word in test_words:
    status = "❌ ERROR (Rejected)" if word in errors else "✅ OK (Accepted)"
    print(f"  {word}: {status}")
