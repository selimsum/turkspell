import os

REPLACEMENTS = {
    "kağıt": "kâğıt",
    "kağıd": "kâğıd",
    "Kağıt": "Kâğıt",
    "Kağıd": "Kâğıd",
    
    "rüzgar": "rüzgâr",
    "Rüzgar": "Rüzgâr",
    
    "hikaye": "hikâye",
    "Hikaye": "Hikâye",
    
    "dükkan": "dükkân",
    "Dükkan": "Dükkân",
    
    "tezgah": "tezgâh",
    "Tezgah": "Tezgâh",
    
    "mekan": "mekân",
    "Mekan": "Mekân",
    
    "imkan": "imkân",
    "Imkan": "İmkân",
    
    "milli": "millî",
    "Milli": "Millî",
    
    "dini": "dinî",
    "Dini": "Dinî",
    
    "resmi": "resmî",
    "Resmi": "Resmî",
    
    "siyasi": "siyasî",
    "Siyasi": "Siyasî",
    
    "tarihi": "tarihî",
    "Tarihi": "Tarihî",
    
    "hukuki": "hukukî",
    "Hukuki": "Hukukî",
    
    "iktisadi": "iktisadî",
    "Iktisadi": "İktisadî",
    
    "ilmi": "ilmî",
    "Ilmi": "İlmî",
    
    "fiili": "fiilî",
    "Fiili": "Fiilî",
    
    "akli": "aklî",
    "Akli": "Aklî",
    
    "örfi": "örfî",
    "Örfi": "Örfî",
    
    "baki": "bakî",
    "Baki": "Bakî",
    
    "asgari": "asgarî",
    "Asgari": "Asgarî",
    
    "azami": "azamî",
    "Azami": "Azamî",
}

def fix_line(line):
    for target, replacement in REPLACEMENTS.items():
        line = line.replace(target, replacement)
    return line

def process_file(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return
        
    print(f"Processing {input_path} -> {output_path}...")
    lines_processed = 0
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            fout.write(fix_line(line))
            lines_processed += 1
            
    print(f"  Completed: {lines_processed} lines processed.")

def main():
    process_file("official_test.csv", "official_test_fixed.csv")
    process_file("official_test_v2.csv", "official_test_v2_fixed.csv")

if __name__ == "__main__":
    main()
