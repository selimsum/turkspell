import os

# Precise word-level prefix or exact replacements
def correct_word(word):
    if not word:
        return word
        
    word_lower = word.lower()
    
    # 1. Exact matches
    exact_matches = {
        "cinsi": "cinsî",
        "fenni": "fennî",
        "takribi": "takribî",
        "örfi": "örfî",
        "örfiye": "örfîye",
        "örfiyece": "örfîyece",
    }
    if word_lower in exact_matches:
        # Preserve capitalization style
        val = exact_matches[word_lower]
        if word[0].isupper():
            return val[0].upper() + val[1:]
        return val

    # 2. Root/prefix replacements with safety checks
    # format: (root_to_find, replacement, exceptions_list)
    prefix_rules = [
        # Kağıt / Kağıd
        ("kağıt", "kâğıt", []),
        ("kağıd", "kâğıd", []),
        ("Kağıt", "Kâğıt", []),
        ("Kağıd", "Kâğıd", []),
        
        # Hükümet / Hükumet
        ("hükümet", "hükûmet", []),
        ("hükumet", "hükûmet", []),
        ("Hükümet", "Hükûmet", []),
        ("Hükumet", "Hükûmet", []),
        
        # Aşık
        ("aşık", "âşık", []),
        ("Aşık", "Âşık", []),
        
        # Rüzgar
        ("rüzgar", "rüzgâr", []),
        ("Rüzgar", "Rüzgâr", []),
        
        # Hikaye
        ("hikaye", "hikâye", []),
        ("Hikaye", "Hikâye", []),
        
        # Dükkan
        ("dükkan", "dükkân", []),
        ("Dükkan", "Dükkân", []),
        
        # Tezgah
        ("tezgah", "tezgâh", []),
        ("Tezgah", "Tezgâh", []),
        
        # Mekan (must not match mekanik)
        ("mekan", "mekân", ["mekanik"]),
        ("Mekan", "Mekân", ["Mekanik", "mekanik"]),
        
        # Imkan
        ("imkan", "imkân", []),
        ("Imkan", "İmkân", []),
        
        # Inkar
        ("inkar", "inkâr", []),
        ("Inkar", "İnkâr", []),
        
        # Hizmetkar
        ("hizmetkar", "hizmetkâr", []),
        ("Hizmetkar", "Hizmetkâr", []),
        
        # Kanaatkar
        ("kanaatkar", "kanaatkâr", []),
        ("Kanaatkar", "Kanaatkâr", []),
        
        # Dahiyane
        ("dahiyane", "dâhiyane", []),
        ("Dahiyane", "Dâhiyane", []),
        
        # Efkarlan / Efkarlı
        ("efkarlan", "efkârlan", []),
        ("Efkarlan", "Efkârlan", []),
        ("efkarlı", "efkârlı", []),
        ("Efkarlı", "Efkârlı", []),
        
        # Kaşane
        ("kaşane", "kâşâne", []),
        ("Kaşane", "Kâşâne", []),
        
        # Lapseki
        ("lapseki", "lâpseki", []),
        ("Lapseki", "Lâpseki", []),
        
        # Şehriyar
        ("şehriyar", "şehriyâr", []),
        ("Şehriyar", "Şehriyâr", []),
        
        # Hallice
        ("hallice", "hâllice", []),
        ("Hallice", "Hâllice", []),
        
        # Kanunusani
        ("kanunusani", "kânunusani", []),
        ("Kanunusani", "Kânunusani", []),
        
        # Katibiadil
        ("katibiadil", "kâtibiadil", []),
        ("Katibiadil", "Kâtibiadil", []),
        
        # Arzuhal
        ("arzuhal", "arzuhâl", []),
        ("Arzuhal", "Arzuhâl", []),
        
        # Resmileş / Merkezileş / Millileş
        ("resmileş", "resmîleş", []),
        ("Resmileş", "Resmîleş", []),
        ("merkezileş", "merkezîleş", []),
        ("Merkezileş", "Merkezîleş", []),
        ("millileş", "millîleş", []),
        ("Millileş", "Millîleş", []),
    ]
    
    for prefix, rep, exceptions in prefix_rules:
        if word.startswith(prefix):
            # Check exceptions
            is_exception = False
            for exc in exceptions:
                if word.startswith(exc):
                    is_exception = True
                    break
            if not is_exception:
                return word.replace(prefix, rep, 1)
                
    return word

def process_file(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return
        
    print(f"Processing {input_path} -> {output_path}...")
    lines_processed = 0
    replacements_made = 0
    
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
         
        # Copy header
        header = next(fin)
        fout.write(header)
        lines_processed += 1
        
        for line in fin:
            line_str = line.strip()
            if not line_str:
                fout.write("\n")
                continue
            parts = line_str.split(',')
            if len(parts) == 2:
                gold, inp = parts[0], parts[1]
                gold_fixed = correct_word(gold)
                inp_fixed = correct_word(inp)
                
                if gold_fixed != gold or inp_fixed != inp:
                    replacements_made += 1
                fout.write(f"{gold_fixed},{inp_fixed}\n")
            else:
                fout.write(line)
            lines_processed += 1
            
    print(f"  Completed: {lines_processed} lines processed. Made {replacements_made} line corrections.")

def main():
    process_file("official_test.csv", "official_test_fixed.csv")
    process_file("official_test_v2.csv", "official_test_v2_fixed.csv")
    process_file("spell-checking-and-correction/evaluation/data/one_million_test_set.csv", "spell-checking-and-correction/evaluation/data/one_million_test_set_fixed.csv")

if __name__ == "__main__":
    main()
