import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

words = [
    "resmîleştrme",
    "millîlermizin"
]

input_text = "\n".join(words) + "\n"

p = subprocess.Popen(
    ['hunspell', '-a', '-d', 'tr'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8'
)

stdout, stderr = p.communicate(input=input_text)

print("Hunspell Suggestions Output:")
print(stdout)
