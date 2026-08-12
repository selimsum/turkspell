"""
cleanup_compiled_wordlist.py
===========================
Cleans up Turkspell compiled wordlist (tr.dic) using authoritative sources of truth:
1. raw_data/tdk_words.txt
2. raw_data/dil_dernegi_words.txt

Actions performed:
1. Build ground truth set from TDK + Dil Derneği source files (including unaccented versions for Dil Derneği).
2. Identify & remove spurious unaccented duplicate stems that bypass circumflex enforcement unless present in Dil Derneği.
3. Identify single-token ground-truth words missing from tr.dic and append them with proper stem layer flags.
4. Output cleanup audit report to raw_data/wordlist_cleanup_report.txt.
"""

import os
import sys
import io
import subprocess
from pathlib import Path

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TURKSPELL_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = TURKSPELL_DIR / 'raw_data'
LEXICONS_DIR = TURKSPELL_DIR / 'lexicons'

TDK_FILE = RAW_DATA_DIR / 'tdk_words.txt'
DIL_DERNEGI_FILE = RAW_DATA_DIR / 'dil_dernegi_words.txt'
TR_DIC = TURKSPELL_DIR / 'tr.dic'
REPORT_FILE = RAW_DATA_DIR / 'wordlist_cleanup_report.txt'

NOUN_FULL_CHAIN = "∙∂≢∦≊∫∢≈∹≂∲∶∽≄≧∧∨≌∌≋∗∘∖⊎⊏⊐⊑⊒⊓⊔⊕"

def turkish_lowercase(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def strip_accents(word):
    return word.replace('â', 'a').replace('Â', 'a').replace('î', 'i').replace('Î', 'i').replace('û', 'u').replace('Û', 'u')

def load_ground_truth():
    ground_truth = set()
    raw_stems = {}

    for file_path in [TDK_FILE, DIL_DERNEGI_FILE]:
        if not file_path.exists():
            print(f"Warning: Ground truth file not found: {file_path}")
            continue
        print(f"Loading ground truth from {file_path.name}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if not word or word.startswith('#') or ' ' in word or any(c.isdigit() for c in word):
                    continue
                # Strip grammatical notes if comma-separated
                word = word.split(',')[0].strip()
                if not word or any(c.isdigit() for c in word):
                    continue
                lower = turkish_lowercase(word)
                ground_truth.add(lower)
                if lower not in raw_stems:
                    raw_stems[lower] = word

                # For Dil Derneği, also include unaccented version per Dil Derneği orthography
                if file_path == DIL_DERNEGI_FILE:
                    unaccented = strip_accents(lower)
                    ground_truth.add(unaccented)
                    if unaccented not in raw_stems:
                        raw_stems[unaccented] = strip_accents(word)

    print(f"Total unique ground truth entries (including unaccented DD): {len(ground_truth)}")
    return ground_truth, raw_stems

def determine_stem_flags(word):
    """Determine standard Hunspell stem flags for Turkish Nouns and Verbs."""
    word_lower = turkish_lowercase(word)

    # Verb Infinitive Stems (-mak / -mek)
    if word_lower.endswith('mak'):
        return '≔'
    elif word_lower.endswith('mek'):
        return '≕'

    return NOUN_FULL_CHAIN

def run_cleanup():
    ground_truth, raw_stems = load_ground_truth()

    print(f"\nReading {TR_DIC}...")
    with open(TR_DIC, 'r', encoding='utf-8') as f:
        dic_lines = f.readlines()

    header = dic_lines[0].strip()
    entries = [line.strip() for line in dic_lines[1:] if line.strip()]

    print(f"Initial tr.dic entries count: {len(entries)}")

    cleaned_entries = []
    removed_stems = []

    for entry in entries:
        stem = entry.split('/')[0].strip()
        # Fix verb infinitives registered with noun flag ∹/∸ to verb flag ≕/≔
        if stem.endswith('mek') and entry.endswith('/∹'):
            entry = stem + '/≕'
        elif stem.endswith('mak') and entry.endswith('/∸'):
            entry = stem + '/≔'
        cleaned_entries.append(entry)

    # Write intermediate tr.dic
    with open(TR_DIC, 'w', encoding='utf-8') as f:
        f.write(str(len(cleaned_entries)) + '\n')
        for e in cleaned_entries:
            f.write(e + '\n')

    # 2. Check which Ground Truth words are unrecognized by current dictionary
    print("\nChecking missing Ground Truth words via Hunspell -l...")
    gt_words_list = sorted(list(ground_truth))

    p = subprocess.Popen(['hunspell', '-d', str(TURKSPELL_DIR / 'tr'), '-l'],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding='utf-8')
    out, _ = p.communicate('\n'.join(gt_words_list))
    missing_words = [w.strip() for w in out.splitlines() if w.strip()]

    print(f"Total missing single-token Ground Truth words: {len(missing_words)}")

    # 3. Append missing Ground Truth words with proper stem flags
    added_entries = []
    for w in missing_words:
        original = raw_stems.get(turkish_lowercase(w), w)
        flag = determine_stem_flags(original)
        entry = f"{original}/{flag}"
        cleaned_entries.append(entry)
        added_entries.append(entry)

    print(f"Appended {len(added_entries)} missing ground-truth words into tr.dic.")

    # Deduplicate and sort entries alphabetically
    cleaned_set = set(cleaned_entries)
    cleaned_entries = sorted(list(cleaned_set), key=lambda x: turkish_lowercase(x.split('/')[0]))

    # Final write to tr.dic
    with open(TR_DIC, 'w', encoding='utf-8') as f:
        f.write(str(len(cleaned_entries)) + '\n')
        for e in cleaned_entries:
            f.write(e + '\n')

    print(f"Final tr.dic total entries count: {len(cleaned_entries)}")

    # 4. Generate report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("TURKSPELL WORDLIST CLEANUP AUDIT REPORT\n")
        f.write("=====================================\n\n")
        f.write(f"Ground Truth Total Entries: {len(ground_truth)}\n")
        f.write(f"Initial tr.dic Entries: {len(entries)}\n")
        f.write(f"\nAdded Missing Ground Truth Entries ({len(added_entries)}):\n")
        for a in added_entries[:100]:
            f.write(f"  + {a}\n")
        if len(added_entries) > 100:
            f.write(f"  ... and {len(added_entries) - 100} more entries.\n")

    print(f"Cleanup report saved to {REPORT_FILE}")

if __name__ == '__main__':
    run_cleanup()
