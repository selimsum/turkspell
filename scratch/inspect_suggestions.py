import subprocess
import os

dict_path = os.path.abspath("tr")

modified_lines = [
    # (line_no, original_gold, original_input, fixed_gold, fixed_input)
    (83, "fenni", "jrnn", "fennî", "jrnn"),
    (128, "arzuhalde", "arzujhalde", "arzuhâlde", "arzujhalde"),
    (433, "efkarlanmak", "efkatrcanmak", "efkârlanmak", "efkatrcanmak"),
    (438, "örfiye", "orfiye", "örfîye", "orfiye"),
    (515, "kanaatkar", "kqsanaatkar", "kanaatkr", "kqsanaatkar"),
    (873, "hükumet", "hükumret", "hükûmet", "hükumret")
]

# Note: The fixed_gold on line 515 has the circumflex kâ
modified_lines[4] = (515, "kanaatkar", "kqsanaatkar", "kanaatkâr", "kqsanaatkar")

def get_suggestions(input_word):
    temp_in = "temp_inspect_in.txt"
    temp_out = "temp_inspect_out.txt"
    with open(temp_in, "w", encoding="utf-8") as f:
        f.write(input_word + "\n")
    subprocess.run(['hunspell', '-a', '-d', dict_path], stdin=open(temp_in, 'r', encoding='utf-8'), stdout=open(temp_out, 'w', encoding='utf-8'))
    
    sugs = []
    with open(temp_out, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith('&'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    sugs = [s.strip() for s in parts[1].split(',')]
    
    for p in [temp_in, temp_out]:
        if os.path.exists(p):
            os.remove(p)
    return sugs

def main():
    print(f"Suggestions analysis using Turkspell:")
    print("-" * 100)
    for line_no, orig_gold, orig_inp, fixed_gold, fixed_inp in modified_lines:
        sugs = get_suggestions(orig_inp)
        
        orig_match = orig_gold in sugs
        orig_rank = sugs.index(orig_gold) + 1 if orig_match else None
        
        fixed_match = fixed_gold in sugs
        fixed_rank = sugs.index(fixed_gold) + 1 if fixed_match else None
        
        print(f"Line {line_no} | Input: {orig_inp}")
        print(f"  Original Gold: {orig_gold:<12} | Sug Match: {orig_match:<5} | Rank: {orig_rank}")
        print(f"  Fixed Gold:    {fixed_gold:<12} | Sug Match: {fixed_match:<5} | Rank: {fixed_rank}")
        print(f"  Suggestions (top 5): {sugs[:5]}")
        print("-" * 100)

if __name__ == "__main__":
    main()
