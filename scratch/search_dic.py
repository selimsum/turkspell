import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('tr.dic', 'r', encoding='utf-8') as f:
    for line in f:
        line_clean = line.strip()
        # check if the word has 'kâğıt' or 'kağıt'
        if 'kâğıt' in line_clean or 'kağıt' in line_clean or 'kâğ' in line_clean:
            print(line_clean)
