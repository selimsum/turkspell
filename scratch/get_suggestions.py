import subprocess
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

words = [
    "kâğıtlrına",
    "kağıdın",
    "Türkiye'yde",
    "Atatürkün"
]

for word in words:
    # Run hunspell -d tr on a single word
    result = subprocess.run(
        ['hunspell', '-d', 'tr'],
        input=word,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    # Parse lines
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip() and not line.startswith('Hunspell')]
    
    print(f"\nWord: '{word}'")
    if not lines:
        print("  Status: Correct")
        continue
        
    for line in lines:
        if line.startswith('*'):
            print("  - Part/Word: Correct (no suggestions needed)")
        elif line.startswith('&'):
            parts = line.split(':')
            header = parts[0].split()
            part_word = header[1]
            sugs = parts[1].strip()
            print(f"  - Part '{part_word}': Incorrect. Suggestions: {sugs}")
        elif line.startswith('#'):
            parts = line.split()
            part_word = parts[1]
            print(f"  - Part '{part_word}': Incorrect. Suggestions: (None)")
        else:
            print(f"  - Line: {line}")
