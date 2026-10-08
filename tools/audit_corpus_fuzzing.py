# -*- coding: utf-8 -*-
"""
Turkspell Corpus Fuzzing & Morphological Gap Discovery Tool (Method 1)

1. Gathers rich, natural Turkish text from multiple real-world corpora:
   - Turkish Wikipedia (via streaming Parquet)
   - Contemporary Turkish News (CNN Türk 2024 via streaming Parquet)
   - TDK 2026 Definitions & Authority Headwords
2. Cleanses and tokenizes text, aggregating token frequencies (min frequency threshold).
3. Evaluates all unique tokens through Hunspell (tr.aff / tr.dic).
4. Dissects failing tokens against TDK & Zemberek root lexicons:
   - Categorizes into:
     * Affix Chain Gaps (Root exists in dictionary, but valid affix combination fails)
     * Missing Lemmas (Legitimate root in TDK/Dil Derneği not in dictionary)
     * Spelling Errors / OOV / Noise
5. Outputs a prioritized, actionable markdown report and summary stats.
"""

import os
import sys
import re
import json
import time
import unicodedata
import subprocess
from collections import Counter, defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
LEX_DIR = os.path.join(BASE_DIR, "lexicons")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

TDK_WORDS_PATH = os.path.join(RAW_DIR, "tdk_words.txt")
DD_WORDS_PATH = os.path.join(RAW_DIR, "dil_dernegi_words.txt")
TDK_DIZIN_PATH = os.path.join(RAW_DIR, "tdk_dizin_2026.json")
ZEMBEREK_LEX_PATH = os.path.join(LEX_DIR, "zemberek_lexicon.json")

# Turkish lowercase conversion
def tr_lower(text: str) -> str:
    return (
        text.replace("İ", "i")
        .replace("I", "ı")
        .replace("Î", "î")
        .replace("Â", "â")
        .replace("Û", "û")
        .lower()
    )

# Turkish uppercase conversion
def tr_upper(text: str) -> str:
    return (
        text.replace("i", "İ")
        .replace("ı", "I")
        .replace("î", "Î")
        .replace("â", "Â")
        .replace("û", "Û")
        .upper()
    )

# Valid Turkish alphabet characters regex
_TR_CHARS = set("abcçdefgğhıijklmnoöprsştuüvyzâîû")
_TR_WORD_RE = re.compile(r"^[abcçdefgğhıijklmnoöprsştuüvyzâîû]+$")
_TOKEN_RE = re.compile(r"[a-zA-ZçÇğĞıİöÖşŞüÜâÂîÎûÛ]+")

def is_valid_tr_token(w: str) -> bool:
    if len(w) < 2 or len(w) > 35:
        return False
    # Check if contains invalid foreign letters
    for c in w:
        if c not in _TR_CHARS:
            return False
    # Check for excessive character repetition (3+ same chars like "çoook")
    for i in range(len(w) - 2):
        if w[i] == w[i+1] == w[i+2]:
            return False
    return True

def load_authority_roots():
    """Loads authoritative roots from TDK, Dil Dernegi, and Zemberek."""
    authorities = {} # root -> {'pos': ..., 'source': ...}
    
    # 1. TDK words
    if os.path.exists(TDK_WORDS_PATH):
        with open(TDK_WORDS_PATH, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                w = line.split("/")[0].strip()
                if " " not in w and len(w) >= 2:
                    w_low = tr_lower(w)
                    if is_valid_tr_token(w_low) and w_low not in authorities:
                        authorities[w_low] = {"source": "TDK"}

    # 2. Dil Derneği words
    if os.path.exists(DD_WORDS_PATH):
        with open(DD_WORDS_PATH, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                w = line.split("/")[0].strip()
                if " " not in w and len(w) >= 2:
                    w_low = tr_lower(w)
                    if is_valid_tr_token(w_low) and w_low not in authorities:
                        authorities[w_low] = {"source": "DilDernegi"}

    # 3. Zemberek lexicon
    if os.path.exists(ZEMBEREK_LEX_PATH):
        with open(ZEMBEREK_LEX_PATH, "r", encoding="utf-8") as f:
            z_data = json.load(f)
            for item in z_data:
                lem = item.get("lemma", "")
                pos = item.get("pos", "")
                if lem and " " not in lem:
                    lem_low = tr_lower(lem)
                    if lem_low in authorities:
                        authorities[lem_low]["pos"] = pos
                        authorities[lem_low]["zemberek"] = True
                    else:
                        authorities[lem_low] = {"source": "Zemberek", "pos": pos, "zemberek": True}

    return authorities

def fetch_corpus_frequencies(wiki_articles: int = 4000, news_articles: int = 5000, min_freq: int = 3):
    """Fetches text from Wikipedia and contemporary news, returning Counter of valid tokens."""
    import polars as pl
    word_counter = Counter()
    capital_counter = Counter()

    print(f"\n[1/4] Fetching and tokenizing corpus text...")
    
    # 1. Turkish Wikipedia
    wiki_url = "https://huggingface.co/datasets/wikimedia/wikipedia/resolve/main/20231101.tr/train-00000-of-00002.parquet"
    print(f"  Streaming {wiki_articles:,} articles from Turkish Wikipedia...")
    try:
        df_wiki = pl.read_parquet(wiki_url, n_rows=wiki_articles, columns=["text"])
        t0 = time.time()
        for text in df_wiki["text"]:
            if not text:
                continue
            # Normalization
            text = unicodedata.normalize("NFC", text).replace("\u0307", "")
            tokens = _TOKEN_RE.findall(text)
            for t in tokens:
                if t[0].isupper():
                    capital_counter[tr_lower(t)] += 1
                else:
                    word_counter[tr_lower(t)] += 1
        print(f"    Processed Wikipedia in {time.time() - t0:.1f}s.")
    except Exception as e:
        print(f"    Warning: Wikipedia streaming failed ({e}), continuing...")

    # 2. Contemporary News (CNN Türk 2024)
    news_url = "https://huggingface.co/datasets/denizzhansahin/Turkish_News_CNN-News-2024/resolve/main/data/train-00000-of-00001.parquet"
    print(f"  Streaming {news_articles:,} contemporary articles from CNN Turk News 2024...")
    try:
        df_news = pl.read_parquet(news_url, n_rows=news_articles, columns=["Icerik", "Baslik"])
        t0 = time.time()
        for row in df_news.iter_rows(named=True):
            content = (row.get("Baslik") or "") + " " + (row.get("Icerik") or "")
            if not content.strip():
                continue
            content = unicodedata.normalize("NFC", content).replace("\u0307", "")
            tokens = _TOKEN_RE.findall(content)
            for t in tokens:
                if t[0].isupper():
                    capital_counter[tr_lower(t)] += 1
                else:
                    word_counter[tr_lower(t)] += 1
        print(f"    Processed News in {time.time() - t0:.1f}s.")
    except Exception as e:
        print(f"    Warning: News streaming failed ({e}), continuing...")

    print(f"  Raw unique tokens found: {len(word_counter):,}")

    # 3. Cleanse & filter proper nouns and infrequent noise
    filtered_tokens = {}
    for word, freq in word_counter.items():
        if freq < min_freq:
            continue
        if not is_valid_tr_token(word):
            continue
        # Proper noun heuristic: if capitalized 85%+ of the time, treat as proper noun
        cap_freq = capital_counter.get(word, 0)
        total_occurrences = freq + cap_freq
        if cap_freq > 0 and (cap_freq / total_occurrences) > 0.85:
            continue
        filtered_tokens[word] = freq

    print(f"  Clean Turkish tokens retained (freq >= {min_freq}): {len(filtered_tokens):,}")
    return filtered_tokens

def run_hunspell_check(tokens: list, dict_name: str = "tr") -> set:
    """Runs hunspell -d <dict_name> -l on a list of tokens, returning failing set."""
    print(f"\n[2/4] Testing {len(tokens):,} tokens with Hunspell (dict: {dict_name})...")
    t0 = time.time()
    batch_size = 25000
    flagged = set()
    for i in range(0, len(tokens), batch_size):
        batch = tokens[i:i + batch_size]
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
    passed_count = len(tokens) - len(flagged)
    print(f"  Tested in {elapsed:.2f}s.")
    print(f"  Passed: {passed_count:,} ({passed_count / len(tokens):.2%})")
    print(f"  Failing / Flagged: {len(flagged):,} ({len(flagged) / len(tokens):.2%})")
    return flagged

def dissect_failing_words(flagged_words: list, token_freq: dict, authorities: dict):
    """Categorizes failing words into Affix Gaps, Missing Lemmas, and Noise/Typos."""
    print(f"\n[3/4] Dissecting {len(flagged_words):,} failing words...")
    
    affix_gaps = []       # Root in dictionary, but valid affix combination failed
    missing_lemmas = []   # Root in TDK/DD authority but NOT in active dictionary
    other_failing = []    # Spurious, typo, loanword, or complex unknown

    # Common productive suffix patterns for stemming
    # We look from right to left
    COMMON_VERB_AFFIXES = [
        # Participles + relative
        "ndakiler", "ndakileri", "ndakilerin", "ndakinde", "ndakinden", "ndakine", "ndaki",
        "ndekiler", "ndekileri", "ndekilerin", "ndekinde", "ndekinden", "ndekine", "ndeki",
        # Participles + equative / adverbial
        "duğunca", "düğünce", "tığınca", "tiğince", "tuğunca", "tüğünce",
        "dığınca", "diğince", "duğunda", "düğünde", "tığında", "tiğinde",
        "dıkça", "dikçe", "dukça", "dükçe", "tıkça", "tikçe", "tukça", "tükçe",
        # Converbs
        "cesine", "casına", "çesine", "çasına",
        "meksizin", "maksızın",
        "yalı", "yeli", "alı", "eli",
        "esiye", "asıya",
        "esiye", "asıya",
        "iverdi", "ivermiş", "ivermek",
        "ebilmek", "abilmek", "ebiliyor", "abiliyor", "ebildi", "abildi",
        "eyazdı", "ayazdı",
        "edurmak", "adurmak",
        # Passive / Causative
        "tirilmek", "tırılmak", "türülmek", "turulmak",
        "dirilmek", "dırılmak", "dürülmek", "durulmak",
        "tirmek", "tırmak", "türmek", "turmak",
        "dirmek", "dırmak", "dürmek", "durmak",
        # Basic verb endings
        "yor", "yorlar", "yordu", "yormuş", "yorsa",
        "acak", "ecek", "acaktı", "ecekti", "acaklar", "ecekler",
        "an", "en", "yan", "yen",
        "ar", "er", "ır", "ir", "ur", "ür",
        "mış", "miş", "muş", "müş",
        "dı", "di", "du", "dü", "tı", "ti", "tu", "tü",
        "malı", "meli",
        "mak", "mek", "ma", "me", "ış", "iş", "uş", "üş"
    ]
    
    # Sort affixes by length descending
    COMMON_VERB_AFFIXES.sort(key=len, reverse=True)

    for word in flagged_words:
        freq = token_freq.get(word, 0)

        # Check if the whole word is an authority headword (Missing Lemma)
        if word in authorities:
            auth_info = authorities[word]
            # If it's an authority root but failing in hunspell, it's a Missing Lemma!
            missing_lemmas.append({
                "word": word,
                "freq": freq,
                "source": auth_info.get("source", "TDK"),
                "pos": auth_info.get("pos", "Noun")
            })
            continue

        # Try to find a recognized root inside the word (Affix Gap)
        matched_gap = None
        for sfx in COMMON_VERB_AFFIXES:
            if word.endswith(sfx) and len(word) > len(sfx) + 1:
                potential_stem = word[:-len(sfx)]
                # Check directly or with infinitive
                stem_as_verb = potential_stem + "mak"
                stem_as_verb_e = potential_stem + "mek"
                
                # Check if potential stem exists in dictionary
                found_root = None
                if potential_stem in authorities and authorities[potential_stem].get("pos") in ("Verb", None):
                    found_root = potential_stem
                elif stem_as_verb in authorities:
                    found_root = stem_as_verb
                elif stem_as_verb_e in authorities:
                    found_root = stem_as_verb_e
                
                # Check voicing on stem (e.g., git -> gid-)
                if not found_root and potential_stem.endswith("d"):
                    voiced_t = potential_stem[:-1] + "t"
                    if voiced_t in authorities or (voiced_t + "mak") in authorities or (voiced_t + "mek") in authorities:
                        found_root = voiced_t

                if found_root:
                    matched_gap = {
                        "word": word,
                        "freq": freq,
                        "root": found_root,
                        "suffix": sfx,
                        "root_source": authorities.get(found_root, {}).get("source", "TDK")
                    }
                    break

        if matched_gap:
            affix_gaps.append(matched_gap)
        else:
            other_failing.append({"word": word, "freq": freq})

    # Sort each list by frequency descending
    affix_gaps.sort(key=lambda x: -x["freq"])
    missing_lemmas.sort(key=lambda x: -x["freq"])
    other_failing.sort(key=lambda x: -x["freq"])

    return affix_gaps, missing_lemmas, other_failing

def generate_report(total_tokens: int, passed_count: int, affix_gaps: list, missing_lemmas: list, other_failing: list):
    """Writes detailed findings to markdown report."""
    print(f"\n[4/4] Generating comprehensive audit report...")
    report_path = os.path.join(REPORTS_DIR, "corpus_fuzzing_report.md")
    
    # Analyze most frequent missing suffixes
    suffix_counter = Counter()
    for item in affix_gaps:
        suffix_counter[item["suffix"]] += item["freq"]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Turkspell Doğal Metin Külliyatı (Corpus Fuzzing) Raporu\n\n")
        f.write(f"- **Tarih**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Taranan Özgün Türkçe Sözcük**: {total_tokens:,}\n")
        f.write(f"- **Hunspell Başarı Oranı**: {passed_count:,} / {total_tokens:,} ({passed_count/total_tokens:.2%})\n")
        f.write(f"- **Toplam Tanınmayan Sözcük**: {total_tokens - passed_count:,} ({(total_tokens - passed_count)/total_tokens:.2%})\n\n")
        
        f.write("## 1. Tespit Özeti\n\n")
        f.write("| Kategori | Benzersiz Sözcük Sayısı | Toplam Külliyat Frekansı |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| **Morfolojik / Ek Zinciri Boşluğu (Grup A)** | {len(affix_gaps):,} | {sum(x['freq'] for x in affix_gaps):,} |\n")
        f.write(f"| **Eksik Kök / Madde Başı (Grup B)** | {len(missing_lemmas):,} | {sum(x['freq'] for x in missing_lemmas):,} |\n")
        f.write(f"| **Diğer / Tipik Hata / Yabancı (Grup C)** | {len(other_failing):,} | {sum(x['freq'] for x in other_failing):,} |\n\n")

        f.write("## 2. En Sık Görülen Eksik Ek Şablonları (Grup A)\n\n")
        f.write("| Ek / Ek Zinciri | Etkilenen Kelime Sayısı | Külliyat Ağırlığı |\n")
        f.write("| :--- | :--- | :--- |\n")
        for sfx, weight in suffix_counter.most_common(20):
            word_count = sum(1 for x in affix_gaps if x['suffix'] == sfx)
            f.write(f"| `-{sfx}` | {word_count:,} | {weight:,} |\n")
        f.write("\n")

        f.write("## 3. En Yüksek Frekanslı Morfolojik Boşluklar (İlk 40 Sözcük)\n\n")
        f.write("| Sıra | Hata Veren Kelime | Kök | Tespit Edilen Ek | Frekans |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for i, item in enumerate(affix_gaps[:40], 1):
            f.write(f"| {i} | `{item['word']}` | `{item['root']}` | `-{item['suffix']}` | {item['freq']:,} |\n")
        f.write("\n")

        f.write("## 4. En Yüksek Frekanslı Eksik Kökler (İlk 40 Sözcük)\n\n")
        f.write("| Sıra | Eksik Kök | Kaynak | Tür | Frekans |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for i, item in enumerate(missing_lemmas[:40], 1):
            f.write(f"| {i} | `{item['word']}` | {item['source']} | {item['pos']} | {item['freq']:,} |\n")
        f.write("\n")

    print(f"  Report written to: {report_path}")
    return report_path

def main():
    print("=" * 70)
    print("TURKSPELL CORPUS FUZZING & MORPHOLOGY DISCOVERY (METHOD 1)")
    print("=" * 70)

    # Load roots
    authorities = load_authority_roots()
    print(f"Loaded {len(authorities):,} authoritative roots (TDK, Dil Derneği, Zemberek).")

    # Fetch and filter corpus frequencies
    token_freq = fetch_corpus_frequencies(wiki_articles=4000, news_articles=5600, min_freq=3)
    tokens = sorted(token_freq.keys(), key=lambda w: -token_freq[w])

    # Run hunspell check
    flagged = run_hunspell_check(tokens, dict_name="tr")
    passed_count = len(tokens) - len(flagged)

    # Dissect failing words
    flagged_sorted = [w for w in tokens if w in flagged]
    affix_gaps, missing_lemmas, other_failing = dissect_failing_words(flagged_sorted, token_freq, authorities)

    # Report
    rep = generate_report(len(tokens), passed_count, affix_gaps, missing_lemmas, other_failing)
    
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY:")
    print(f"Total Unique Turkish Tokens Evaluated: {len(tokens):,}")
    print(f"Hunspell Accuracy on Real Natural Text: {passed_count / len(tokens):.2%}")
    print(f"Affix Chain Gaps Identified (Group A): {len(affix_gaps):,} words")
    print(f"Missing Lemmas Identified (Group B):   {len(missing_lemmas):,} words")
    print(f"Report File: {rep}")
    print("=" * 70)

if __name__ == "__main__":
    main()
