"""
tools/corpus_rule_miner.py
===========================
Synthesizes FineWeb-2 (tur_Latn) unrecognized corpus candidates and Modal LLM
morphological parses into Turkspell's 4 Hunspell architectural categories:

  1. Category 1 (derivation_depth == 0..1): Missing root flags (Voicing, NoVoicing,
     LastVowelDrop, Doubling, InverseHarmony, Aorist, Derivations) on verified TDK/DD roots.
  2. Category 2 (derivation_depth == 1..2): Productive 1-2 level suffix patterns missing
     from build/generate_grammar_rules.py (tr.aff).
  3. Category 3 (derivation_depth >= 3): High-frequency lexicalized 3+ level derived lemmas
     whose base_root is strictly verified in TDK/Dil Derneği, routed to tr.dic as intermediate
     stems to respect Hunspell's 2-fold suffixing limit without overgeneration.
  4. Category 4 (Typo / Diacritic Drop): High-frequency corpus misspellings mapped to valid
     TDK/DD targets for REP table enhancement (lexicons/extra_rep_rules.json).

Usage:
    python tools/corpus_rule_miner.py [--apply]
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_data"
LEX_DIR = BASE_DIR / "lexicons"

VOWELS = "aeıioöuüâîû"
BACK_VOWELS = "aıouâû"
FRONT_VOWELS = "eiöüî"

ASCII_MAP = str.maketrans("çğıöşüâîû", "cgiosuaiu")

DETACHED_SUFFIXES = {
    "nın", "nin", "nun", "nün", "ın", "in", "un", "ün",
    "dan", "den", "tan", "ten", "ndan", "nden",
    "da", "de", "ta", "te", "nda", "nde",
    "daki", "deki", "taki", "teki", "ndaki", "ndeki",
    "dir", "dır", "dur", "dür", "tir", "tır", "tur", "tür",
    "lar", "ler", "ları", "leri", "ların", "lerin", "lara", "lere",
    "larda", "lerde", "lardan", "lerden", "larla", "lerle",
    "yla", "yle", "la", "le", "na", "ne", "nı", "ni", "nu", "nü",
    "lık", "lik", "luk", "lük", "lı", "li", "lu", "lü",
    "sız", "siz", "suz", "süz", "cı", "ci", "cu", "cü",
    "çı", "çi", "çu", "çü", "ncı", "nci", "ncu", "ncü",
    "ıncı", "inci", "uncu", "üncü", "ca", "ce", "ça", "çe",
    "ım", "im", "um", "üm", "ımız", "imiz", "umuz", "ümüz",
    "mız", "miz", "muz", "müz", "nız", "niz", "nuz", "nüz",
    "sı", "si", "su", "sü", "yı", "yi", "yu", "yü", "ya", "ye",
    "dı", "di", "du", "dü", "tı", "ti", "tu", "tü",
    "mış", "miş", "muş", "müş", "ysa", "yse", "ken",
}

FOREIGN_AND_WEB_STOPWORDS = {
    "the", "and", "for", "you", "this", "that", "with", "from", "your", "all",
    "are", "have", "not", "can", "will", "one", "more", "about", "what", "when",
    "http", "https", "html", "php", "www", "com", "org", "net", "gov", "edu",
    "online", "email", "admin", "login", "user", "firstname", "lastname",
    "play", "full", "flash", "off", "ios", "red", "rock", "ipad", "iphone",
    "google", "facebook", "twitter", "instagram", "youtube", "whatsapp",
    "windows", "android", "linux", "wordpress", "pdf", "jpg", "png", "gif",
    "escort", "porn", "sex", "casino", "bet", "bonus", "slot", "anti", "bkz",
    "like", "use", "made", "some", "aloe", "alone", "base", "face", "code",
    "take", "save", "home", "game", "time", "name", "site", "date", "line",
    "file", "case", "page", "care", "live", "love", "life", "make", "give",
    "come", "type", "size", "rate", "note", "mode", "side", "wide", "rule",
    "role", "sale", "male", "tale", "scale", "style", "state", "space", "place",
    "price", "phone", "image", "share", "store", "score", "force", "source",
    "course", "house", "mouse", "cause", "pause", "value", "issue", "true",
    "blue", "free", "tree", "see", "fee", "area", "idea", "data", "meta",
    "beta", "java", "void", "null", "char", "int", "var", "let", "def",
    "new", "old", "big", "top", "low", "hot", "out", "now", "how", "who",
    "why", "way", "day", "may", "pay", "say", "key", "buy", "try", "dry",
    "pro", "max", "min", "plus", "ultra", "super", "mega", "mini", "micro",
    "auto", "info", "demo", "logo", "foto", "photo", "video", "audio", "radio",
    "studio", "euro", "zero", "hero", "ergo", "solo", "polo", "yolo",
    "link", "ping", "ring", "king", "wing", "sing", "song", "long", "bank",
    "tank", "rank", "dark", "mark", "park", "work", "fork", "port", "sort",
    "part", "cart", "mart", "start", "smart", "chart", "heart", "hard", "card",
    "yard", "ward", "word", "lord", "ford", "gold", "cold", "hold", "bold",
    "fold", "told", "sold", "wild", "mild", "child", "build", "field", "world",
    "server", "client", "system", "program", "project", "product", "service",
    "design", "media", "social", "digital", "global", "local", "normal",
    "portal", "total", "final", "legal", "metal", "model", "hotel", "panel",
    "level", "label", "table", "cable", "title", "apple", "google", "mobile",
}

GENUINE_2LETTER_ROOTS = {
    "su", "el", "ev", "iş", "at", "ot", "et", "ip", "ok", "ak", "ay", "oy",
    "üç", "on", "öz", "az", "iz", "av", "aş", "eş", "ek", "uç", "öç", "ad",
    "un", "in", "en", "an", "al", "il", "ol", "öl", "öp", "iç", "aç", "uç",
}

NOUN_ENDS_EXCL = {
    "parmak", "ırmak", "ekmek", "yemek", "çakmak", "tokmak", "yaşmak",
    "kaymak", "ilmek", "basamak", "mercimek", "damak", "yumak", "oymak",
    "yamak", "hamak", "sumak", "kaçamak", "kuymak", "ramak", "somak",
    "tomak", "emek", "ahmak", "çomak", "madımak", "tutamak", "başmak"
}


def tlc(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def strip_hat(s: str) -> str:
    return s.replace("â", "a").replace("î", "i").replace("û", "u")


def ascii_fold(s: str) -> str:
    return s.translate(ASCII_MAP)


def get_last_vowel(w: str) -> str:
    for c in reversed(w):
        if c in VOWELS:
            return c
    return ""


def load_authority_sets():
    tdk_words = set()
    dd_words = set()
    for fname, target in [("tdk_words.txt", tdk_words), ("dil_dernegi_words.txt", dd_words)]:
        fpath = RAW_DIR / fname
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                for line in f:
                    w = line.strip()
                    if not w or w.startswith("#"):
                        continue
                    if "/" in w:
                        head, _, alt = w.partition("/")
                        h_clean = tlc(head.split(" (")[0].strip())
                        if " " not in h_clean:
                            target.add(h_clean)
                        if " " not in alt.strip():
                            target.add(tlc(alt.strip()))
                    else:
                        w_clean = tlc(w.split(" (")[0].strip())
                        if " " not in w_clean:
                            target.add(w_clean)
    return tdk_words, dd_words, tdk_words | dd_words


def build_stem_lookup(authority_set: set[str]):
    """Builds reverse lookup maps from mutated stems back to authority lemmas."""
    verb_roots = {}      # verb_stem -> verb_lemma (e.g. "gel" -> "gelmek")
    voiced_nouns = {}    # voiced_stem -> noun_lemma (e.g. "kitab" -> "kitap")
    vdrop_nouns = {}     # dropped_stem -> noun_lemma (e.g. "akl" -> "akıl")
    doubled_nouns = {}   # doubled_stem -> noun_lemma (e.g. "hakk" -> "hak")
    unhatted_map = defaultdict(list)

    voicing_table = {"p": "b", "ç": "c", "t": "d", "k": "ğ", "g": "ğ"}

    for w in authority_set:
        if any(c in w for c in "âîû"):
            unhatted_map[strip_hat(w)].append(w)

        if w.endswith(("mak", "mek")) and w not in NOUN_ENDS_EXCL and len(w) > 3:
            vroot = w[:-3]
            verb_roots[vroot] = w
            if vroot.endswith("t"):
                verb_roots[vroot[:-1] + "d"] = w
        else:
            if len(w) >= 2 and w[-1] in voicing_table:
                if w.endswith("nk"):
                    voiced_nouns[w[:-1] + "g"] = w
                else:
                    voiced_nouns[w[:-1] + voicing_table[w[-1]]] = w
            if len(w) >= 4 and w[-1] not in VOWELS and w[-2] in "ıiuü" and w[-3] not in VOWELS:
                vdrop_nouns[w[:-2] + w[-1]] = w
            if sum(1 for c in w if c in VOWELS) == 1 and w[-1] not in VOWELS:
                doubled_nouns[w + w[-1]] = w

    return verb_roots, voiced_nouns, vdrop_nouns, doubled_nouns, unhatted_map


NOMINAL_INFLECTIONS = [
    "", "lar", "ler",
    "ı", "i", "u", "ü", "yı", "yi", "yu", "yü", "nı", "ni", "nu", "nü",
    "a", "e", "ya", "ye", "na", "ne",
    "da", "de", "ta", "te", "nda", "nde",
    "dan", "den", "tan", "ten", "ndan", "nden",
    "ın", "in", "un", "ün", "nın", "nin", "nun", "nün",
    "la", "le", "yla", "yle", "ca", "ce", "ça", "çe",
    "ım", "im", "um", "üm", "m",
    "ın", "in", "un", "ün", "n",
    "sı", "si", "su", "sü",
    "ımız", "imiz", "umuz", "ümüz", "mız", "miz", "muz", "müz",
    "ınız", "iniz", "unuz", "ünüz", "nız", "niz", "nuz", "nüz",
    "ları", "leri", "ların", "lerin", "lara", "lere", "larda", "lerde", "lardan", "lerden", "larla", "lerle",
    "sına", "sine", "suna", "süne", "sında", "sinde", "sunda", "sünde",
    "sından", "sinden", "sundan", "sünden", "sını", "sini", "sunu", "sünü",
    "sının", "sinin", "sunun", "sünün", "sıyla", "siyle", "suyla", "süyle",
    "ına", "ine", "una", "üne", "ında", "inde", "unda", "ünde",
    "ından", "inden", "undan", "ünden", "ını", "ini", "unu", "ünü",
    "ının", "inin", "unun", "ünün", "ıyla", "iyle", "uyla", "üyle",
    "daki", "deki", "taki", "teki", "ndaki", "ndeki", "sındaki", "sindeki", "ındaki", "indeki",
    "dır", "dir", "dur", "dür", "tır", "tir", "tur", "tür",
    "ydı", "ydi", "ydu", "ydü", "ymış", "ymiş", "ymuş", "ymüş",
]

VERB_INFLECTIONS = [
    "", "mak", "mek", "ma", "me", "ması", "mesi", "masını", "mesini", "masına", "mesine",
    "masında", "mesinde", "masından", "mesinden", "masının", "mesinin", "masıyla", "mesiyle",
    "makla", "mekle", "makta", "mekte", "maktadır", "mektedir", "maktaydı", "mekteydi",
    "dı", "di", "du", "dü", "tı", "ti", "tu", "tü",
    "dık", "dik", "duk", "dük", "tık", "tik", "tuk", "tük",
    "dılar", "diler", "dular", "düler", "tılar", "tiler", "tular", "tüler",
    "mış", "miş", "muş", "müş", "mıştır", "miştir", "muştur", "müştür",
    "ıyor", "iyor", "uyor", "üyor", "yor", "ıyordu", "iyordu", "uyordu", "üyordu",
    "acak", "ecek", "yacak", "yecek", "acaktır", "ecektir", "acaktı", "ecekti",
    "an", "en", "yan", "yen", "anlar", "enler", "yanlar", "yenler",
    "dığı", "diği", "duğu", "düğü", "tığı", "tiği", "tuğu", "tüğü",
    "dığını", "diğini", "duğunu", "düğünü", "tığını", "tiğini", "tuğunu", "tüğünü",
    "dığına", "diğine", "duğuna", "düğüne", "tığına", "tiğine", "tuğuna", "tüğüne",
    "dığında", "diğinde", "duğunda", "düğünde", "tığında", "tiğinde", "tuğunda", "tüğünde",
    "dığından", "diğinden", "duğundan", "düğünden", "tığından", "tiğinden", "tuğundan", "tüğünden",
    "dıkları", "dikleri", "dukları", "dükleri", "tıkları", "tikleri", "tukları", "tükleri",
    "acağı", "eceği", "yacağı", "yeceği", "acağını", "eceğini", "yacağını", "yeceğini",
    "arak", "erek", "yarak", "yerek", "ıp", "ip", "up", "üp", "yıp", "yip", "yup", "yüp",
    "ınca", "ince", "unca", "ünce", "yınca", "yince", "yunca", "yünce",
    "madan", "meden", "maksızın", "meksizin", "dıkça", "dikçe", "dukça", "dükçe", "tıkça", "tikçe", "tukça", "tükçe",
    "malı", "meli", "malıdır", "melidir", "sa", "se", "saydı", "seydi",
    "ır", "ir", "ur", "ür", "ar", "er", "r",
    "abilir", "ebilir", "yabilir", "yebilir", "amaz", "emez", "yamaz", "yemez",
    "abilen", "ebilen", "yabilen", "yebilen", "abilecek", "ebilecek", "yabilecek", "yebilecek",
    "abildiği", "ebildiği", "yabildiği", "yebildiği",
]

# 1-2 level productive derivational suffixes to probe for Category 2
PRODUCTIVE_DERIV_PATTERNS = [
    ("sal", "Noun->Adj (-sal)"),
    ("sel", "Noun->Adj (-sel)"),
    ("sallık", "Noun->Adj->Noun (-sallık)"),
    ("sellik", "Noun->Adj->Noun (-sellik)"),
    ("sallığ", "Noun->Adj->Noun (-sallığ-)"),
    ("selliğ", "Noun->Adj->Noun (-selliğ-)"),
    ("laş", "Noun->Verb (-laş-)"),
    ("leş", "Noun->Verb (-leş-)"),
    ("laştır", "Noun->Verb (-laştır-)"),
    ("leştir", "Noun->Verb (-leştir-)"),
    ("lan", "Noun->Verb (-lan-)"),
    ("len", "Noun->Verb (-len-)"),
    ("landır", "Noun->Verb (-landır-)"),
    ("lendir", "Noun->Verb (-lendir-)"),
    ("sever", "Noun->Noun (-sever)"),
    ("zede", "Noun->Noun (-zede)"),
]

THREE_PLUS_TEMPLATES = [
    # Noun + -sal/-sel (1) + -laş/-leş (2) + -mak/-mek or -tır/-tir (3)
    ("sallaş", "sallaşmak", "Verb", 3, False),
    ("selleş", "selleşmek", "Verb", 3, False),
    ("sallaştır", "sallaştırmak", "Verb", 3, False),
    ("selleştir", "selleştirmek", "Verb", 3, False),
    ("sallaştırıl", "sallaştırılmak", "Verb", 4, False),
    ("selleştiril", "selleştirilmek", "Verb", 4, False),
    # Noun + -sız/-siz (1) + -laş/-leş (2) + -mak/-mek or -tır/-tir (3)
    ("sızlaş", "sızlaşmak", "Verb", 3, False),
    ("sizleş", "sizleşmek", "Verb", 3, False),
    ("suzlaş", "suzlaşmak", "Verb", 3, False),
    ("süzleş", "süzleşmek", "Verb", 3, False),
    ("sızlaştır", "sızlaştırmak", "Verb", 3, False),
    ("sizleştir", "sizleştirmek", "Verb", 3, False),
    ("suzlaştır", "suzlaştırmak", "Verb", 3, False),
    ("süzleştir", "süzleştirmek", "Verb", 3, False),
    ("sızlaştırıl", "sızlaştırılmak", "Verb", 4, False),
    ("sizleştiril", "sizleştirilmek", "Verb", 4, False),
    ("suzlaştırıl", "suzlaştırılmak", "Verb", 4, False),
    ("süzleştiril", "süzleştirilmek", "Verb", 4, False),
    # Noun + -lı/-li (1) + -laş/-leş (2) + -tır/-tir (3)
    ("lılaş", "lılaşmak", "Verb", 3, False),
    ("lileş", "lileşmek", "Verb", 3, False),
    ("lulaş", "lulaşmak", "Verb", 3, False),
    ("lüleş", "lüleşmek", "Verb", 3, False),
    ("lılaştır", "lılaştırmak", "Verb", 3, False),
    ("lileştir", "lileştirmek", "Verb", 3, False),
    ("lulaştır", "lulaştırmak", "Verb", 3, False),
    ("lüleştir", "lüleştirmek", "Verb", 3, False),
    # Noun + -laştır/-leştir (1-2) + -ıl/-il (3) passive
    ("laştırıl", "laştırılmak", "Verb", 3, False),
    ("leştiril", "leştirilmek", "Verb", 3, False),
    ("landırıl", "landırılmak", "Verb", 3, False),
    ("lendiril", "lendirilmek", "Verb", 3, False),
    # Verb + passive (-ıl/-il/-ul/-ül/-ın/-in/-un/-ün) + potential (-abilir/-ebilir) + -lik/-lık (3)
    ("ılabilirlik", "ılabilirlik", "Noun", 3, True),
    ("ilebilirlik", "ilebilirlik", "Noun", 3, True),
    ("ulabilirlik", "ulabilirlik", "Noun", 3, True),
    ("ülebilirlik", "ülebilirlik", "Noun", 3, True),
    ("ılabilirliğ", "ılabilirlik", "Noun", 3, True),
    ("ilebilirliğ", "ilebilirlik", "Noun", 3, True),
    ("ulabilirliğ", "ulabilirlik", "Noun", 3, True),
    ("ülebilirliğ", "ülebilirlik", "Noun", 3, True),
    ("ınabilirlik", "ınabilirlik", "Noun", 3, True),
    ("inebilirlik", "inebilirlik", "Noun", 3, True),
    ("ınabilirliğ", "ınabilirlik", "Noun", 3, True),
    ("inebilirliğ", "inebilirlik", "Noun", 3, True),
    ("abilirlik", "abilirlik", "Noun", 3, True),
    ("ebilirlik", "ebilirlik", "Noun", 3, True),
    ("abilirliğ", "abilirlik", "Noun", 3, True),
    ("ebilirliğ", "ebilirlik", "Noun", 3, True),
    ("yabilirlik", "yabilirlik", "Noun", 3, True),
    ("yebilirlik", "yebilirlik", "Noun", 3, True),
    ("yabilirliğ", "yabilirlik", "Noun", 3, True),
    ("yebilirliğ", "yebilirlik", "Noun", 3, True),
    ("amazlık", "amazlık", "Noun", 3, True),
    ("emezlik", "emezlik", "Noun", 3, True),
    ("amazlığ", "amazlık", "Noun", 3, True),
    ("emezliğ", "emezlik", "Noun", 3, True),
]

KNOWN_TYPO_FIXES = {
    "cok": "çok",
    "yada": "ya_da",
    "icin": "için",
    "adeta": "âdeta",
    "imkanı": "imkânı",
    "imkan": "imkân",
    "imkanları": "imkânları",
    "imkansız": "imkânsız",
    "imkanlar": "imkânlar",
    "imkanlarını": "imkânlarını",
    "imkanlarından": "imkânlarından",
    "imkanlarıyla": "imkânlarıyla",
    "imkanına": "imkânına",
    "imkanının": "imkânının",
    "şikayet": "şikâyet",
    "şikayetçi": "şikâyetçi",
    "şikayetler": "şikâyetler",
    "şikayetleri": "şikâyetleri",
    "şikayeti": "şikâyeti",
    "kağıt": "kâğıt",
    "kağıdı": "kâğıdı",
    "kağıtları": "kâğıtları",
    "hikaye": "hikâye",
    "hikayesi": "hikâyesi",
    "hikayeler": "hikâyeler",
    "hikayeleri": "hikâyeleri",
    "birşey": "bir_şey",
    "birşeyi": "bir_şeyi",
    "birşeyler": "bir_şeyler",
    "bişey": "bir_şey",
    "herşey": "her_şey",
    "herşeyi": "her_şeyi",
    "herşeyin": "her_şeyin",
    "herşeyden": "her_şeyden",
    "hergün": "her_gün",
    "herkez": "herkes",
    "herkeze": "herkese",
    "herkezin": "herkesin",
    "mekan": "mekân",
    "mekanı": "mekânı",
    "mekanlar": "mekânlar",
    "mekanları": "mekânları",
    "rüzgar": "rüzgâr",
    "rüzgarı": "rüzgârı",
    "rüzgarın": "rüzgârın",
    "hemde": "hem_de",
    "vede": "ve_de",
    "yinede": "yine_de",
    "belkide": "belki_de",
    "sankide": "sanki_de",
    "hattada": "hatta_da",
    "bilede": "bile_de",
    "zatende": "zaten_de",
    "isede": "ise_de",
    "hiçte": "hiç_de",
    "pekte": "pek_de",
    "pekiyi": "pek_iyi",
    "guzel": "güzel",
    "degil": "değil",
    "zeka": "zekâ",
    "zekası": "zekâsı",
    "zekalı": "zekâlı",
    "tiroid": "tiroit",
    "oldugu": "olduğu",
    "oldugunu": "olduğunu",
    "şuan": "şu_an",
    "şuanda": "şu_anda",
    "şuanki": "şu_anki",
    "hic": "hiç",
    "hicbir": "hiçbir",
    "hiçbirşey": "hiçbir_şey",
    "nasil": "nasıl",
    "yanısıra": "yanı_sıra",
    "mahkum": "mahkûm",
    "bır": "bir",
    "diger": "diğer",
    "orjinal": "orijinal",
    "eger": "eğer",
    "gun": "gün",
    "tabiki": "tabii_ki",
    "tabiiki": "tabii_ki",
    "once": "önce",
    "dogru": "doğru",
    "orda": "orada",
    "burda": "burada",
    "şurda": "şurada",
    "ordaki": "oradaki",
    "burdaki": "buradaki",
    "inkar": "inkâr",
    "sey": "şey",
    "artik": "artık",
    "nikah": "nikâh",
    "nikahı": "nikâhı",
    "tezgah": "tezgâh",
    "tezgahı": "tezgâhı",
    "dükkan": "dükkân",
    "dükkanı": "dükkânı",
    "dukkan": "dükkân",
    "karargah": "karargâh",
    "karargahı": "karargâhı",
    "güzergah": "güzergâh",
    "güzergahı": "güzergâhı",
    "yadigar": "yadigâr",
    "işgüzar": "işgüzâr",
    "fedakar": "fedakâr",
    "fedakarlık": "fedakârlık",
    "sahtekar": "sahtekâr",
    "sahtekarlık": "sahtekârlık",
    "sanatkar": "sanatkâr",
    "zanaatkar": "zanaatkâr",
    "makina": "makine",
    "makinası": "makinesi",
    "makinalar": "makineler",
    "makinaları": "makineleri",
}


def analyze_candidates():
    tdk_words, dd_words, authority_set = load_authority_sets()
    verb_roots, voiced_nouns, vdrop_nouns, doubled_nouns, unhatted_map = build_stem_lookup(authority_set)

    cand_path = RAW_DIR / "fineweb2_unrecognized_candidates.json"
    if not cand_path.exists():
        print(f"Error: {cand_path} not found.")
        return None

    with open(cand_path, encoding="utf-8") as f:
        candidates = json.load(f)

    unrec_set = {tlc(e["word"]) for e in candidates}

    # Build ASCII-folded map of RECOGNIZED words from FineWeb-2 frequencies
    recognized_by_ascii = {}
    fw2_freq_path = RAW_DIR / "fineweb2_corpus_frequencies.json"
    if fw2_freq_path.exists():
        with open(fw2_freq_path, encoding="utf-8") as f:
            fw2_freqs = json.load(f)
        for rw, rfreq in fw2_freqs.items():
            rw_low = tlc(rw)
            if rw_low not in unrec_set and rfreq >= 10:
                af = ascii_fold(rw_low)
                if af != rw_low:
                    # Keep highest-frequency recognized word for each ASCII fold
                    if af not in recognized_by_ascii or rfreq > recognized_by_ascii[af][1]:
                        recognized_by_ascii[af] = (rw_low, rfreq)

    llm_parsed_map = {}
    parsed_path = RAW_DIR / "fineweb2_parsed_entries.json"
    if parsed_path.exists():
        with open(parsed_path, encoding="utf-8") as f:
            for item in json.load(f):
                if isinstance(item, dict) and item.get("word"):
                    llm_parsed_map[tlc(item["word"])] = item
        print(f"Loaded {len(llm_parsed_map):,} Modal LLM morphological parses from {parsed_path.name}.")

    cat1_root_flags = defaultdict(lambda: {"attrs": set(), "total_freq": 0, "examples": []})
    cat2_affix_gaps = defaultdict(lambda: {"total_freq": 0, "roots": set(), "examples": []})
    cat3_lexicalized = defaultdict(lambda: {"pos": "Noun", "base_root": "", "depth": 3, "total_freq": 0, "examples": []})
    cat4_typos = {}
    llm_candidates = []

    for entry in candidates:
        w = tlc(entry["word"])
        freq = entry["freq"]

        if w in DETACHED_SUFFIXES or w in FOREIGN_AND_WEB_STOPWORDS or len(w) <= 2:
            continue

        # 1. Explicit Typo Map
        if w in KNOWN_TYPO_FIXES and KNOWN_TYPO_FIXES[w]:
            cat4_typos[w] = {"target": KNOWN_TYPO_FIXES[w], "freq": freq, "reason": "known_typo"}
            continue

        # 2. Check if w is an unhatted version of a mandatory hatted authority word
        matched_unhatted = False
        for suf in NOMINAL_INFLECTIONS:
            if suf and not w.endswith(suf):
                continue
            stem = w[: len(w) - len(suf)] if suf else w
            if len(stem) >= 3 and stem in unhatted_map and stem not in authority_set:
                hatted_lemma = unhatted_map[stem][0]
                cat4_typos[w] = {
                    "target": hatted_lemma + suf,
                    "freq": freq,
                    "reason": f"circumflex_drop({hatted_lemma})",
                }
                matched_unhatted = True
                break
            if len(stem) >= 3 and stem[-1] in ("b", "c", "d", "ğ"):
                rev_map = {"b": "p", "c": "ç", "d": "t", "ğ": "k"}
                unvoiced = stem[:-1] + rev_map[stem[-1]]
                if unvoiced in unhatted_map and unvoiced not in authority_set:
                    hatted_lemma = unhatted_map[unvoiced][0]
                    hatted_voiced = hatted_lemma[:-1] + stem[-1]
                    cat4_typos[w] = {
                        "target": hatted_voiced + suf,
                        "freq": freq,
                        "reason": f"circumflex_voiced_drop({hatted_lemma})",
                    }
                    matched_unhatted = True
                    break
        if matched_unhatted:
            continue

        # 3. Check if w is a de-ASCII / diacritic-omission typo of a recognized high-frequency word
        # Exclude genuine InverseHarmony loanwords (e.g. kanaati vs kanaatı where stem ends in -at/-al/-ol/-ul)
        af_w = ascii_fold(w)
        if af_w in recognized_by_ascii:
            rw_target, rw_freq = recognized_by_ascii[af_w]
            # Check if the ONLY difference is ı vs i in the suffix after an -at/-al/-ol/-ul loanword
            is_inverse_loan_cand = False
            for suf_f, suf_b in [("i", "ı"), ("ine", "ına"), ("inde", "ında"), ("inden", "ından"), ("ini", "ını"), ("inin", "ının"), ("im", "ım"), ("imiz", "ımız")]:
                if w.endswith(suf_f) and rw_target.endswith(suf_b):
                    base_s = w[: len(w) - len(suf_f)]
                    if base_s == rw_target[: len(rw_target) - len(suf_b)] and base_s.endswith(("at", "al", "ol", "ul", "ak")):
                        is_inverse_loan_cand = True
                        break
            if not is_inverse_loan_cand and rw_freq >= freq:
                cat4_typos[w] = {
                    "target": rw_target,
                    "freq": freq,
                    "reason": f"de_ascii_typo(target_freq={rw_freq})",
                }
                continue

        # Collect morphologically complex Turkish candidates for Modal H100 LLM parsing
        if len(w) >= 6 and any(c in w for c in "çğıöşü") and len(llm_candidates) < 600:
            llm_candidates.append({"word": w, "freq": freq})

        # 4. Check Category 3: 3+ Level Lexicalized Derivations on Verified Authority Roots
        matched_cat3 = False
        for suf_is_verb, inf_list in [(True, VERB_INFLECTIONS), (False, NOMINAL_INFLECTIONS)]:
            for inf in inf_list:
                if inf and not w.endswith(inf):
                    continue
                stem_before_inf = w[: len(w) - len(inf)] if inf else w
                if len(stem_before_inf) < 6:
                    continue
                for tpl_match, tpl_lemma_suf, tpl_pos, tpl_depth, base_is_verb in THREE_PLUS_TEMPLATES:
                    if (tpl_pos == "Verb") != suf_is_verb:
                        continue
                    if stem_before_inf.endswith(tpl_match):
                        base_cand = stem_before_inf[: len(stem_before_inf) - len(tpl_match)]
                        if len(base_cand) < 2:
                            continue
                        base_root = None
                        if base_is_verb:
                            if base_cand in verb_roots:
                                base_root = verb_roots[base_cand]
                        else:
                            if base_cand in authority_set:
                                base_root = base_cand
                            elif base_cand in voiced_nouns:
                                base_root = voiced_nouns[base_cand]
                        if base_root:
                            derived_lemma = base_cand + tpl_lemma_suf
                            info = cat3_lexicalized[derived_lemma]
                            info["pos"] = tpl_pos
                            info["base_root"] = base_root
                            info["depth"] = tpl_depth
                            info["total_freq"] += freq
                            if len(info["examples"]) < 5:
                                info["examples"].append(f"{w} ({freq})")
                            matched_cat3 = True
                            break
                if matched_cat3:
                    break
            if matched_cat3:
                break
        if matched_cat3:
            continue

        # 5. Check Category 2: Productive 1-2 Level Derivational Suffix Gaps on Authority Roots
        matched_cat2 = False
        for suf_is_verb, inf_list in [(True, VERB_INFLECTIONS), (False, NOMINAL_INFLECTIONS)]:
            for inf in inf_list:
                if inf and not w.endswith(inf):
                    continue
                stem_before_inf = w[: len(w) - len(inf)] if inf else w
                if len(stem_before_inf) < 4:
                    continue
                for d_suf, d_label in PRODUCTIVE_DERIV_PATTERNS:
                    if stem_before_inf.endswith(d_suf):
                        base_cand = stem_before_inf[: len(stem_before_inf) - len(d_suf)]
                        if (len(base_cand) >= 3 or base_cand in GENUINE_2LETTER_ROOTS) and base_cand in authority_set:
                            c2 = cat2_affix_gaps[d_label]
                            c2["total_freq"] += freq
                            c2["roots"].add(base_cand)
                            if len(c2["examples"]) < 6:
                                c2["examples"].append(f"{w}->{base_cand} ({freq})")
                            matched_cat2 = True
                            break
                if matched_cat2:
                    break
            if matched_cat2:
                break
        if matched_cat2:
            continue

        # 6. Check Category 1: Inflectional Rejections on Authority Roots
        matched_cat1 = False
        for inf in NOMINAL_INFLECTIONS:
            if not inf or not w.endswith(inf):
                continue
            stem = w[: len(w) - len(inf)]
            if len(stem) < 3 and stem not in GENUINE_2LETTER_ROOTS:
                continue
            if stem in voiced_nouns:
                root = voiced_nouns[stem]
                c1 = cat1_root_flags[root]
                c1["attrs"].add("Voicing")
                c1["total_freq"] += freq
                if len(c1["examples"]) < 5:
                    c1["examples"].append(f"{w} ({freq})")
                matched_cat1 = True
                break
            elif stem in vdrop_nouns:
                root = vdrop_nouns[stem]
                c1 = cat1_root_flags[root]
                c1["attrs"].add("LastVowelDrop")
                c1["total_freq"] += freq
                if len(c1["examples"]) < 5:
                    c1["examples"].append(f"{w} ({freq})")
                matched_cat1 = True
                break
            elif stem in doubled_nouns:
                root = doubled_nouns[stem]
                c1 = cat1_root_flags[root]
                c1["attrs"].add("Doubling")
                c1["total_freq"] += freq
                if len(c1["examples"]) < 5:
                    c1["examples"].append(f"{w} ({freq})")
                matched_cat1 = True
                break
            elif stem in authority_set:
                # Guard: If stem has a mandatory circumflex twin (e.g. adet / âdet, kar / kâr),
                # an unvoiced form like "adeti" is a circumflex or voicing typo, NOT a NoVoicing rule!
                if stem in unhatted_map:
                    continue
                c1 = cat1_root_flags[stem]
                if stem[-1] in "pçtk" and inf[0] in VOWELS:
                    c1["attrs"].add("NoVoicing")
                lv = get_last_vowel(stem)
                if lv in BACK_VOWELS and any(fv in inf for fv in FRONT_VOWELS):
                    c1["attrs"].add("InverseHarmony")
                c1["total_freq"] += freq
                if len(c1["examples"]) < 5:
                    c1["examples"].append(f"{w} ({freq})")
                matched_cat1 = True
                break
        if matched_cat1:
            continue

        for inf in VERB_INFLECTIONS:
            if not inf or not w.endswith(inf):
                continue
            stem = w[: len(w) - len(inf)]
            if len(stem) < 2:
                continue
            if stem in verb_roots:
                v_lemma = verb_roots[stem]
                c1 = cat1_root_flags[v_lemma]
                if inf.startswith(("ar", "er")):
                    c1["attrs"].add("Aorist_A")
                elif inf.startswith(("ır", "ir", "ur", "ür")):
                    c1["attrs"].add("Aorist_I")
                else:
                    c1["attrs"].add(f"VerbInflection:{inf}")
                c1["total_freq"] += freq
                if len(c1["examples"]) < 5:
                    c1["examples"].append(f"{w} ({freq})")
                matched_cat1 = True
                break
        if matched_cat1:
            continue

        # 7. Incorporate Modal LLM parses if available
        if w in llm_parsed_map:
            p = llm_parsed_map[w]
            b_root = tlc(p.get("base_root") or "")
            lemma = tlc(p.get("lemma") or "")
            depth = p.get("derivation_depth")
            pos = p.get("pos") or "Noun"
            attrs = p.get("attributes") or []
            corr = p.get("correction")
            is_valid = p.get("is_valid", bool(lemma and not corr))

            if corr:
                corr_clean = tlc(corr).replace(" ", "_")
                if corr_clean != w:
                    cat4_typos[w] = {"target": corr_clean, "freq": freq, "reason": "llm_typo_correction"}
            elif is_valid and b_root in authority_set:
                if depth == 0:
                    c1 = cat1_root_flags[b_root]
                    if attrs:
                        c1["attrs"].update(attrs)
                    else:
                        c1["attrs"].add(f"LLM_Lemma:{lemma}")
                    c1["total_freq"] += freq
                    if len(c1["examples"]) < 5:
                        c1["examples"].append(f"{w} ({freq})")
                elif depth in (1, 2):
                    c2 = cat2_affix_gaps[f"LLM_{pos} (depth={depth}): {lemma}"]
                    c2["total_freq"] += freq
                    c2["roots"].add(b_root)
                    if len(c2["examples"]) < 5:
                        c2["examples"].append(f"{w}->{b_root} ({freq})")
                elif depth is not None and depth >= 3 and len(lemma) >= 5:
                    info = cat3_lexicalized[lemma]
                    info["pos"] = pos
                    info["base_root"] = b_root
                    info["depth"] = depth
                    info["total_freq"] += freq
                    if len(info["examples"]) < 5:
                        info["examples"].append(f"{w} ({freq})")

    # Sort and serialize report
    cat1_list = [
        {
            "root": k,
            "missing_attrs": sorted(list(v["attrs"])),
            "total_freq": v["total_freq"],
            "examples": v["examples"],
        }
        for k, v in sorted(cat1_root_flags.items(), key=lambda x: x[1]["total_freq"], reverse=True)
        if v["total_freq"] >= 10 and v["attrs"]
    ]

    cat2_list = [
        {
            "pattern": k,
            "total_freq": v["total_freq"],
            "root_count": len(v["roots"]),
            "examples": v["examples"],
        }
        for k, v in sorted(cat2_affix_gaps.items(), key=lambda x: x[1]["total_freq"], reverse=True)
    ]

    cat3_list = [
        {
            "lemma": k,
            "pos": v["pos"],
            "base_root": v["base_root"],
            "derivation_depth": v["depth"],
            "total_freq": v["total_freq"],
            "examples": v["examples"],
        }
        for k, v in sorted(cat3_lexicalized.items(), key=lambda x: x[1]["total_freq"], reverse=True)
        if v["total_freq"] >= 10
    ]

    cat4_list = [
        {
            "typo": k,
            "target": v["target"],
            "freq": v["freq"],
            "reason": v["reason"],
        }
        for k, v in sorted(cat4_typos.items(), key=lambda x: x[1]["freq"], reverse=True)
        if v["freq"] >= 25
    ]

    report = {
        "summary": {
            "total_candidates_analyzed": len(candidates),
            "cat1_missing_root_flags_count": len(cat1_list),
            "cat2_productive_affix_gaps_count": len(cat2_list),
            "cat3_lexicalized_3plus_lemmas_count": len(cat3_list),
            "cat4_typo_rep_candidates_count": len(cat4_list),
        },
        "category1_missing_root_flags": cat1_list[:100],
        "category2_productive_affix_gaps": cat2_list[:100],
        "category3_lexicalized_3plus_lemmas": cat3_list[:150],
        "category4_typo_rep_candidates": cat4_list[:200],
    }

    report_path = RAW_DIR / "corpus_rule_miner_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    llm_in_path = RAW_DIR / "fineweb2_llm_input.json"
    with open(llm_in_path, "w", encoding="utf-8") as f:
        json.dump(llm_candidates, f, ensure_ascii=False, indent=2)

    print("=" * 72)
    print("TURKSPELL FINEWEB-2 CORPUS RULE MINER REPORT")
    print("=" * 72)
    print(f"Total FineWeb-2 Unrecognized Candidates Analyzed : {len(candidates):,}")
    print(f"Category 1 (Missing Root Flags, depth=0..1)       : {len(cat1_list):,} roots")
    print(f"Category 2 (Productive Affix Gaps, depth=1..2)    : {len(cat2_list):,} patterns")
    print(f"Category 3 (3+ Level Lexicalized Lemmas, freq>=10): {len(cat3_list):,} lemmas")
    print(f"Category 4 (High-Freq Typo -> REP, freq>=25)      : {len(cat4_list):,} pairs")
    print(f"\nReport saved to: {report_path}")

    print("\n--- Top 20 Category 1 (Root Flag) Candidates ---")
    for item in cat1_list[:20]:
        print(f"  {item['root']:<18} | attrs={item['missing_attrs']} | freq={item['total_freq']:,} | ex={item['examples'][:3]}")

    print("\n--- Category 2 (Productive 1-2 Level Affix Gaps) ---")
    for item in cat2_list[:15]:
        print(f"  {item['pattern']:<32} | roots={item['root_count']:<4} | freq={item['total_freq']:,} | ex={item['examples'][:3]}")

    print("\n--- Top 20 Category 3 (3+ Level Lexicalized Lemmas) ---")
    for item in cat3_list[:20]:
        print(f"  {item['lemma']:<26} ({item['pos']}, root={item['base_root']}, depth={item['derivation_depth']}) | freq={item['total_freq']:,} | ex={item['examples'][:3]}")

    print("\n--- Top 25 Category 4 (Typo -> REP) Candidates ---")
    for item in cat4_list[:25]:
        print(f"  {item['typo']:<18} -> {item['target']:<18} | freq={item['freq']:,} ({item['reason']})")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply high-confidence Category 3 & 4 updates")
    args = parser.parse_args()
    analyze_candidates()
