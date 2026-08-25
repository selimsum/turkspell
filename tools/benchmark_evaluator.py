import os
import sys
import time
from spylls.hunspell import Dictionary

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def evaluate_test_set(d, name, correct_words, misspelled_words):
    print(f"\n{'='*70}")
    print(f"EVALUATING: {name}")
    print(f"{'='*70}")
    
    # 1. Evaluate Precision on Correct Words (Checking for False Positives)
    fp_words = [w for w in correct_words if not d.lookup(w)]
    total_clean = len(correct_words)
    clean_correct = total_clean - len(fp_words)
    precision = (clean_correct / total_clean * 100) if total_clean else 100.0
    
    print(f"--- Precision (Clean Words) ---")
    print(f"  Total Clean Words: {total_clean:,}")
    print(f"  Correctly Recognized: {clean_correct:,} ({precision:.2f}%)")
    print(f"  False Positives (Valid words flagged as error): {len(fp_words):,}")
    if fp_words:
        print(f"  Sample FPs: {fp_words[:10]}")

    # 2. Evaluate Recall on Misspelled Words (Checking for False Negatives)
    fn_words = [w for w in misspelled_words if d.lookup(w)]
    total_typos = len(misspelled_words)
    typos_detected = total_typos - len(fn_words)
    recall = (typos_detected / total_typos * 100) if total_typos else 100.0
    
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    
    print(f"\n--- Recall (Misspelled Words) ---")
    print(f"  Total Misspelled Words: {total_typos:,}")
    print(f"  Correctly Flagged: {typos_detected:,} ({recall:.2f}%)")
    print(f"  False Negatives (Missed typos): {len(fn_words):,}")
    if fn_words:
        print(f"  Sample FNs: {fn_words[:10]}")
        
    print(f"\n--- Overall Detection F1-Score: {f1:.2f}% ---")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Loading Turkspell Hunspell dictionary...")
    start_t = time.time()
    d = Dictionary.from_files(os.path.join(base_dir, 'tr'))
    print(f"Dictionary loaded in {time.time() - start_t:.2f}s")
    
    sample_correct = [
        "akıllanmıyorsun", "aldatmışsın", "alıyorlarmış", "başkaldırıyorum", 
        "durduramazdık", "gülüyordum", "öğretiyorlardı", "inandıklarımızın", 
        "izliyorlardı", "kurtaramayacağız", "rüzgâr", "kâğıt", "hikâye", "hükûmet",
        "ayrılamadığına", "konuşabiliyorlar", "temizlemiyorum", "şakalaşıyorlar",
        "çalıştırabiliyorsunuz", "seviştiklerinde", "tanımadığımızı", "yıkıldıklarını",
        "yayımlanmışsa", "yayınlanamayacak", "zenginleştirdiğine", "özelleşmesi"
    ]
    
    sample_misspelled = [
        "aalizindeki", "aamıyorsak", "abartırsı", "hikaye", "ruzgar",
        "Computer", "0azarlar", "b3klediğinizden", "4ejim", "Strong", "Chocolate"
    ]
    
    evaluate_test_set(d, "Turkspell Core Linguistic Regression Suite", sample_correct, sample_misspelled)

if __name__ == '__main__':
    main()
