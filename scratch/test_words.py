import subprocess

words = [
    "Atatürk", "atatürk", "Atatürğ", "Atatürk'ün", "Atatürğ'ün", 
    "Atatürk'e", "Atatürğ'e", "Cumhurbaşkanınca", "cumhurbaşkanınca"
]

p = subprocess.Popen(['hunspell', '-d', 'tr', '-a'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8')
output, err = p.communicate("\n".join(words) + "\n")

print(output)
