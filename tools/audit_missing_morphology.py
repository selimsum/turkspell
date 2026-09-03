# -*- coding: utf-8 -*-
"""
Turkspell Morphological Gap & Affix Audit Tool

Scans missing/failing words in Turkspell from the OSCAR frequency corpus,
dissects them against authoritative TDK and Dil Derneği roots, and
categorizes phonological mismatches and missing affix chains.
"""

import os
import sys
import json
import subprocess
import time
from collections import Counter, defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
OSCAR_PATH = os.path.join(RAW_DIR, "oscar_10m_corpus_frequencies.json")
TDK_PATH = os.path.join(RAW_DIR, "tdk_words.txt")
DD_PATH = os.path.join(RAW_DIR, "dil_dernegi_words.txt")
ATTRIBUTES_PATH = os.path.join(RAW_DIR, "corpus_attested_attributes.json")

def tr_lower(s: str) -> str:
    return s.replace("İ", "i").replace("I", "ı").replace("Î", "î").replace("Â", "â").replace("Û", "û").lower()

def load_authorities():
    roots = set()
    for path in [TDK_PATH, DD_PATH]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    w = line.split("/")[0]
                    if " " not in w and len(w) >= 2:
                        roots.add(tr_lower(w))
    return roots

def audit_morphology(limit: int = 50000, dict_name: str = "tr"):
    print(f"[1/4] Loading authorities and OSCAR frequency corpus (top {limit:,} words)...")
    roots = load_authorities()
    print(f"  Loaded {len(roots):,} authority roots from TDK & Dil Derneği.")
    
    with open(OSCAR_PATH, "r", encoding="utf-8") as f:
        oscar_data = json.load(f)
        
    top_items = sorted(oscar_data.items(), key=lambda x: -x[1])[:limit]
    words = [w for w, _ in top_items]
    freq_map = {w: f for w, f in top_items}
    
    print(f"[2/4] Testing words with Hunspell (dict: {dict_name})...")
    t0 = time.time()
    batch_size = 25000
    flagged = set()
    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]
        p = subprocess.run(
            ["hunspell", "-d", dict_name, "-l"],
            input="\n".join(batch) + "\n",
            text=True,
            capture_output=True,
            encoding="utf-8",
            cwd=BASE_DIR
        )
        for line in p.stdout.splitlines():
            line_s = line.strip()
            if line_s:
                flagged.add(line_s)
                
    elapsed = time.time() - t0
    failing_words = [w for w in words if w in flagged]
    print(f"  Tested {len(words):,} words in {elapsed:.2f}s.")
    print(f"  Passed: {len(words) - len(failing_words):,} ({(len(words) - len(failing_words))/len(words):.2%})")
    print(f"  Failing: {len(failing_words):,} ({len(failing_words)/len(words):.2%})")
    
    print("[3/4] Dissecting failing words against authority roots...")
    voicing_rev = {"b": "p", "c": "ç", "d": "t", "ğ": "k", "g": "k"}
    proper_endings = ("spor", "oğlu", "oglu", "türk", "turk", "soy", "can", "taş", "tas", "han", "er", "al", "ay")
    
    circumflex_stems = {
        "imkan": "imkân", "mekan": "mekân", "dukkan": "dükkân", "dükkan": "dükkân",
        "ruzgar": "rüzgâr", "rüzgar": "rüzgâr", "hikaye": "hikâye", "mahkum": "mahkûm",
        "sukut": "sükût", "sükut": "sükût", "ruku": "rükû", "rüku": "rükû",
        "mefkure": "mefkûre", "kufi": "kûfi", "meskun": "meskûn", "asikar": "aşikâr",
        "ahkam": "ahkâm", "baskatip": "başkâtip", "basmekan": "başmekân", "agah": "agâh",
        "adeta": "âdeta", "hal": "hâl", "hala": "hâlâ", "lazim": "lâzım", "kafi": "kâfi"
    }
    
    results = {
        "circumflex_omission": [],
        "proper_compound": [],
        "novoicing_loanword_gap": [],
        "inverse_harmony_gap": [],
        "general_affix_gap": [],
        "no_authority_root": []
    }
    
    known_novoicing = {
        "imalat", "tahsilat", "beraat", "cennet", "bürokrat", "akıbet", "aktivist",
        "adalat", "ahret", "harekat", "tatbikat", "dakik", "politik", "antik",
        "melik", "malik", "patik", "vilayet", "bereket", "dehşet", "sadakat",
        "hakikat", "cemaat", "menfaat", "seyahat", "kâinat", "tadilat", "salat"
    }
    
    known_palatal = {
        "kontrol", "alkol", "rol", "başrol", "sembol", "petrol", "protokol",
        "kolesterol", "metropol", "usul", "mahsul", "alveol", "ampul", "kabul"
    }
    
    for w in failing_words:
        f = freq_map[w]
        w_low = tr_lower(w)
        
        # 1. Circumflex check
        is_circ = False
        for unh in circumflex_stems:
            if w_low == unh or w_low.startswith(unh):
                results["circumflex_omission"].append((w, f, circumflex_stems[unh]))
                is_circ = True
                break
        if is_circ:
            continue
            
        # 2. Compound proper noun check
        if any(w_low.endswith(pe) and len(w_low) > len(pe) + 2 for pe in proper_endings):
            results["proper_compound"].append((w, f))
            continue
            
        # 3. Root matching
        matched_root = None
        matched_suf = None
        for i in range(len(w_low) - 1, 1, -1):
            st = w_low[:i]
            suf = w_low[i:]
            if st in roots:
                matched_root = st
                matched_suf = suf
                break
            if st[-1] in voicing_rev:
                unv = st[:-1] + voicing_rev[st[-1]]
                if unv in roots:
                    matched_root = unv
                    matched_suf = suf
                    break
                    
        if not matched_root:
            results["no_authority_root"].append((w, f))
            continue
            
        # Check specific linguistic gaps
        if matched_root in known_novoicing:
            results["novoicing_loanword_gap"].append((w, f, matched_root, matched_suf))
        elif matched_root in known_palatal:
            results["inverse_harmony_gap"].append((w, f, matched_root, matched_suf))
        else:
            results["general_affix_gap"].append((w, f, matched_root, matched_suf))
            
    print("\n[4/4] Morphological Audit Summary:")
    print(f"  1. NoVoicing Loanword Gaps (e.g. imalatı, cenneti): {len(results['novoicing_loanword_gap']):,} words (Freq: {sum(x[1] for x in results['novoicing_loanword_gap']):,})")
    print(f"  2. Inverse Harmony / İnce 'l' Gaps (e.g. kontrolden, kabulü): {len(results['inverse_harmony_gap']):,} words (Freq: {sum(x[1] for x in results['inverse_harmony_gap']):,})")
    print(f"  3. Circumflex Root Omissions (e.g. imkanı, rüzgar): {len(results['circumflex_omission']):,} words (Freq: {sum(x[1] for x in results['circumflex_omission']):,})")
    print(f"  4. Compound Proper Surnames (e.g. çavuşoğlu, belediyespor): {len(results['proper_compound']):,} words (Freq: {sum(x[1] for x in results['proper_compound']):,})")
    print(f"  5. Other General Affix Gaps: {len(results['general_affix_gap']):,} words (Freq: {sum(x[1] for x in results['general_affix_gap']):,})")
    print(f"  6. No Recognized Authority Root: {len(results['no_authority_root']):,} words (Freq: {sum(x[1] for x in results['no_authority_root']):,})")
    
    return results

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 30000
    dict_name = sys.argv[2] if len(sys.argv) > 2 else "tr"
    audit_morphology(limit, dict_name)
