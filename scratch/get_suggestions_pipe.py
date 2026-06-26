import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

words = [
    "kâğıtlrına",
    "kağıdın",
    "Türkiye'yde",
    "Atatürkün"
]

# Run hunspell in pipe mode (-a)
# We can pass all words at once, each on a new line.
input_text = "\n".join(words) + "\n"

# In pipe mode, hunspell prints a header first (starts with @)
# then for each word, it prints:
# - * if the word is correct
# - & word count offset: sug1, sug2... if incorrect with suggestions
# - # word offset if incorrect with no suggestions
# - for compounds/multiword, it might print multiple lines, followed by an empty line as a delimiter.

p = subprocess.Popen(
    ['hunspell', '-a', '-d', 'tr'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

stdout, stderr = p.communicate(input=input_text)

print("Hunspell Raw Output:")
print(stdout)
print("Stderr:")
print(stderr)
