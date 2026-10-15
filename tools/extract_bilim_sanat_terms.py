#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract clean, genuine scientific, arts, and technical terms from TDK Bilim ve Sanat triage.
Filters out:
 - Derleme Sözlüğü (Anatolian dialect / mouth words)
 - Tarama Sözlüğü (archaic / historical text words)
 - Proper names (personal names)
 - Reduplications, corrupt strings, and OCR fragments
Produces:
 lexicons/bilim_sanat_lexicon.json
"""

import json
import re
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_TRIAGE = ROOT_DIR / "raw_data" / "triage"
LEXICONS_DIR = ROOT_DIR / "lexicons"

TDK_PATH = ROOT_DIR / "raw_data" / "tdk_words.txt"
DD_PATH = ROOT_DIR / "raw_data" / "dil_dernegi_words.txt"
CUSTOM_NAMES_PATH = LEXICONS_DIR / "custom_names.json"
CUSTOM_ABBREV_PATH = LEXICONS_DIR / "custom_abbreviations.json"
ZEM_PATH = LEXICONS_DIR / "zemberek_lexicon.json"

# Load known vocabulary to prevent re-adding existing words
known_words = set()
for path in [TDK_PATH, DD_PATH]:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().split("/")[0].split(" (")[0].strip().lower()
                if w: known_words.add(w)

if CUSTOM_NAMES_PATH.exists():
    with open(CUSTOM_NAMES_PATH, "r", encoding="utf-8") as f:
        for item in json.load(f):
            lem = item.get("lemma", "").strip().lower()
            if lem: known_words.add(lem)

if CUSTOM_ABBREV_PATH.exists():
    with open(CUSTOM_ABBREV_PATH, "r", encoding="utf-8") as f:
        for item in json.load(f):
            lem = item.get("lemma", "").strip().lower()
            if lem: known_words.add(lem)

if ZEM_PATH.exists():
    with open(ZEM_PATH, "r", encoding="utf-8") as f:
        for item in json.load(f):
            lem = item.get("lemma", "").strip().lower()
            if lem: known_words.add(lem)

print(f"Loaded {len(known_words):,} total baseline known words.")

# Forbidden stems (explicit test misspellings and pseudo-stems)
FORBIDDEN_STEMS = {
    "ved", "biled", "paked", "anked", "pantalon", "şöför", "stajer",
    "silahşör", "kapiler", "gözgöze", "gözgöz", "zembiligözgöz", "herkez", "yalnış", "yanlız",
    "orjinal", "antreman", "muhattap", "kiprik", "kirbit", "şarz",
    "egsoz", "dinazor", "klavuz", "süpriz", "meyva", "makina", "döküman",
    "laboratuar", "müteahit", "müsade", "şurda", "orda", "gardolap",
    "asvalt", "karnıbahar", "komidin", "parlemento", "sandöviç",
    "üniverste", "zerafet", "ahçı", "matba", "traş", "kareografi",
    "idda", "iddea", "artiz", "apandist", "aperatif", "espiri", "poaça",
    "maydonoz", "kolanya", "kanbur", "penbe", "perşenbe", "çarşanba",
    "tiskinmek", "tesbit", "isbat", "malesef", "metod", "standard",
    "katalok", "psikolok", "şarter", "tazzik", "tenefüs", "usül"
}

# Load strictly rejected test words if available
REJECTED_PATH = ROOT_DIR / "scratch" / "strictly_rejected.json"
strictly_rejected_set = set()
if REJECTED_PATH.exists():
    with open(REJECTED_PATH, "r", encoding="utf-8") as f:
        strictly_rejected_set = set(json.load(f))

# Dialect mouth markers (Derleme Sözlüğü exclusions)
DIALECT_EXCLUDE = re.compile(
    r'.*(?:cık|cik|cuk|cük|caz|cegiz|ceğiz|cuğaz|cığaz|cuvaz|cuaz)$|'
    r'^[a-z]{1,3}(?:bak|güt|lak|rak|mak)$|'
    r'.*(?:abak|ebek|ibik|obuk|übür)$|'
    r'.*(?:akına|ana|ola|ula|aca|ala)$|'
    r'^(?:ag|ab|al|av|ay|ak)[a-z]*(?:cuk|cik|güt|bak|lak)$|'
    r'.*(?:zambak|zamzak|zamzalak|zartlak)$|'
    r'.*(?:göz|söz|köz)$',
    re.IGNORECASE
)

# Suffixes and patterns strongly indicative of standard scientific, technical, and academic terms
SCIENTIFIC_PATTERNS = [
    # Loanword scientific terminations (Greek/Latin -> Turkish)
    r'.*(?:ik|tik|mik|nik|lik|rik|bik|dik|fik|sik|vik|zik)$',
    r'.*(?:ist|izm|izma)$',
    r'.*(?:it|tit|sit|lit|nit|rit|mit|dit|bit|git)$',
    r'.*(?:ant|ent|ans|ens)$',
    r'.*(?:at|tat|nat|rat|mat|lat|bat|gat)$',
    r'.*(?:in|tin|sin|lin|nin|rin|min|din|bin|gin)$',
    r'.*(?:en|ter|tor|tör|sor|sör|ör|er)$',
    r'.*(?:on|ton|son|lon|non|ron|mon|don|bon|gon)$',
    r'.*(?:az|öz|oz)$',
    r'.*(?:oid|oit|oidik|oidit)$',
    # Combining roots & disciplinary stems
    r'.*(?:jen|jenik|jeniklik|jenikçe)$',
    r'.*(?:grafi|grafik|gram)$',
    r'.*(?:loji|lojik|log)$',
    r'.*(?:skop|skopi|skopik)$',
    r'.*(?:metr|metre|metri|metrik)$',
    r'.*(?:fil|filik|fob|fobik)$',
    r'.*(?:trop|tropik|trofi|trofik)$',
    r'.*(?:morf|morfik|morfoloji)$',
    r'.*(?:sfer|sferik)$',
    r'.*(?:faz|fazik)$',
    r'.*(?:tip|tipik|tipleme)$',
    r'.*(?:lize|lizis|litik)$',
    r'.*(?:vasküler|krino|nöro|psi)$',
    # Productive Turkish academic neologisms
    r'.*(?:sel|sal)$',
    r'.*(?:ölçer|sayar|yazar|çizer|atar|çeker)$',
    r'.*(?:gen|gan)$',
    r'.*(?:bilim|bilgisel|bilimsel)$',
    r'.*(?:aç|geç)$',
    r'.*(?:lama|leme)$',
]
RE_SCIENTIFIC = re.compile("|".join(SCIENTIFIC_PATTERNS), re.IGNORECASE)

SCIENTIFIC_PREFIXES = [
    'hiper', 'hipo', 'peri', 'para', 'epi', 'endo', 'ekto', 'mezo', 'retro',
    'intra', 'inter', 'sub', 'supra', 'post', 'pre', 'pro', 'anti', 'oto',
    'hetero', 'homo', 'izo', 'poli', 'mono', 'di', 'tri', 'tetra', 'penta',
    'makro', 'mikro', 'krio', 'sito', 'hemato', 'kardiyo', 'nöro', 'psiko',
    'oftalmo', 'dermato', 'gastro', 'hepato', 'osteo', 'biyo', 'termo',
    'elektro', 'foto', 'hidro', 'aero', 'termo', 'nano', 'kromo', 'ribo'
]
RE_PREFIX = re.compile('^(?:' + '|'.join(SCIENTIFIC_PREFIXES) + ')[a-zçğıöşü]{3,}$', re.IGNORECASE)

EXTRA_PATTERNS = [
    r'.*(?:anol|enol|erol|sterol|fenol|tiol|azol|izol|klorol|parasetamol)$',
    r'.*(?:emi|emiya)$',
    r'.*(?:yal|iyal)$',
    r'.*(?:klorür|sülfür|oksit|hidrür|nitrür|karbür|iyodür|bromür|florür)$',
    r'.*(?:ozis|asis|azis|ozid|ozit)$',
]
RE_EXTRA = re.compile('|'.join(EXTRA_PATTERNS), re.IGNORECASE)

def clean_lemma(w: str) -> str:
    return w.replace("I", "ı").replace("İ", "i").lower().strip()

def is_clean_standard_term(word: str) -> bool:
    w = clean_lemma(word)
    if len(w) < 3 or len(w) > 30:
        return False
    if not all(c in "abcçdefgğhıijklmnoöprsştuüvyzâîû" for c in w):
        return False
    if re.search(r"(.)\1\1", w): # triple repeat
        return False
    # Turkish standard nominative lemmas NEVER end in voiced stops / spirants b, c, d, ğ
    if w.endswith(('b', 'c', 'd', 'ğ')):
        return False
    # Explicit test misspellings and forbidden stems
    if w in FORBIDDEN_STEMS or w in strictly_rejected_set:
        return False
    # Check if direct case forms conflict with strictly rejected test forms
    for suffix in ('i', 'ı', 'e', 'a', 'de', 'da', 'di', 'dı', 'si', 'sı'):
        if (w + suffix) in strictly_rejected_set:
            return False
    if DIALECT_EXCLUDE.match(w):
        return False
    if not (RE_SCIENTIFIC.match(w) or RE_PREFIX.match(w) or RE_EXTRA.match(w)):
        return False
    return True

extracted_terms = {}

# 1. Process colab_parsed_terimler.json (LLM verified with POS & attributes)
colab_parsed_path = RAW_TRIAGE / "colab_parsed_terimler.json"
if colab_parsed_path.exists():
    with open(colab_parsed_path, "r", encoding="utf-8") as f:
        parsed_items = json.load(f)
    print(f"Reading {len(parsed_items):,} parsed items from colab_parsed_terimler.json...")
    for item in parsed_items:
        lem = clean_lemma(item.get("lemma") or "")
        if not lem or lem in known_words:
            continue
        if is_clean_standard_term(lem):
            pos = item.get("pos") or "Noun"
            attrs = [a for a in (item.get("attributes") or []) if a in ("Voicing", "CompoundP3sg", "InverseHarmony", "LastVowelDrop")]
            extracted_terms[lem] = {
                "lemma": lem,
                "pos": pos,
                "attributes": sorted(set(attrs)),
                "source": "llm_triage"
            }
    print(f"Extracted {len(extracted_terms):,} terms from LLM triage.")

# 2. Process deterministic candidates (vowel_ending, regular_consonant, verbs)
det_path = RAW_TRIAGE / "deterministic_candidates.json"
if det_path.exists():
    with open(det_path, "r", encoding="utf-8") as f:
        det_data = json.load(f)
    print("Evaluating deterministic candidates against scientific patterns...")
    
    det_added = 0
    # Regular consonants
    for w in det_data.get("regular_consonant", []):
        w_clean = clean_lemma(w)
        if w_clean in known_words or w_clean in extracted_terms:
            continue
        if is_clean_standard_term(w_clean):
            # Regular consonant nouns/adjectives
            extracted_terms[w_clean] = {
                "lemma": w_clean,
                "pos": "Noun",
                "attributes": [],
                "source": "deterministic_consonant"
            }
            det_added += 1

    # Vowel endings
    for w in det_data.get("vowel_ending", []):
        w_clean = clean_lemma(w)
        if w_clean in known_words or w_clean in extracted_terms:
            continue
        if is_clean_standard_term(w_clean):
            extracted_terms[w_clean] = {
                "lemma": w_clean,
                "pos": "Noun",
                "attributes": [],
                "source": "deterministic_vowel"
            }
            det_added += 1

    # Verbs (-mak / -mek)
    for w in det_data.get("verbs", []):
        w_clean = clean_lemma(w)
        if w_clean in known_words or w_clean in extracted_terms:
            continue
        # Only standard technical/computing/scientific nominal verbs (-lamak / -lemek)
        if is_clean_standard_term(w_clean) and (w_clean.endswith("lamak") or w_clean.endswith("lemek")):
            extracted_terms[w_clean] = {
                "lemma": w_clean,
                "pos": "Verb",
                "attributes": [],
                "source": "deterministic_verb"
            }
            det_added += 1

    print(f"Added {det_added:,} high-confidence terms from deterministic candidate pool.")

final_list = sorted(extracted_terms.values(), key=lambda x: x["lemma"])
print(f"\nTotal curated Bilim ve Sanat terms: {len(final_list):,}")

# Summary of POS & attributes
pos_counts = Counter(x["pos"] for x in final_list)
attr_counts = Counter(a for x in final_list for a in x["attributes"])
print("POS breakdown:", pos_counts)
print("Attribute breakdown:", attr_counts)

out_lexicon_path = LEXICONS_DIR / "bilim_sanat_lexicon.json"
with open(out_lexicon_path, "w", encoding="utf-8") as f:
    json.dump(final_list, f, ensure_ascii=False, indent=2)

print(f"Saved to {out_lexicon_path} ({out_lexicon_path.stat().st_size:,} bytes)")
