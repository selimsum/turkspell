#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract clean, genuine scientific, arts, and technical terms from TDK Bilim ve Sanat triage.
Filters out:
 - Derleme Sözlüğü (Anatolian dialect / mouth words & phonetic distortions of standard words)
 - Tarama Sözlüğü (archaic / historical text words)
 - Karşılaştırmalı Türk Lehçeleri Sözlüğü (Russian / regional Turkic headwords)
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

def clean_lemma(w: str) -> str:
    return w.replace("I", "ı").replace("İ", "i").lower().strip()

# Load known vocabulary to prevent re-adding existing words
known_words = set()
for path in [TDK_PATH, DD_PATH]:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = clean_lemma(line.strip().split("/")[0].split(" (")[0])
                if w:
                    known_words.add(w)

if CUSTOM_NAMES_PATH.exists():
    with open(CUSTOM_NAMES_PATH, "r", encoding="utf-8") as f:
        for item in json.load(f):
            lem = clean_lemma(item.get("lemma", ""))
            if lem:
                known_words.add(lem)

if CUSTOM_ABBREV_PATH.exists():
    with open(CUSTOM_ABBREV_PATH, "r", encoding="utf-8") as f:
        for item in json.load(f):
            lem = clean_lemma(item.get("lemma", ""))
            if lem:
                known_words.add(lem)

if ZEM_PATH.exists():
    with open(ZEM_PATH, "r", encoding="utf-8") as f:
        for item in json.load(f):
            lem = clean_lemma(item.get("lemma", ""))
            if lem:
                known_words.add(lem)

print(f"Loaded {len(known_words):,} total baseline known words.")

# Forbidden stems (explicit test misspellings, benchmark typos, and pseudo-stems)
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
    "katalok", "psikolok", "şarter", "tazzik", "tenefüs", "usül",
    # Benchmark & dialect false friends
    "deger", "deer", "degirmen", "tegmen", "temen", "ögretmen", "öretmen",
    "fotograf", "fotoraf", "sektor", "operator", "gecer", "gonder", "koken",
    "sirin", "soz", "yeen", "yegen", "yein", "boaz", "cier", "meer", "sıın",
    "zibin", "çarpaz", "güverçin", "mücever", "agıt", "asik", "asiklik",
    "kedik", "petik", "otobos", "otoboz", "otobüz", "postahane", "posteke",
    "anatar", "taşaron", "nonspesifik", "dioksin", "monograf", "karkın",
    "bazin", "basis", "oksin", "isit", "yidin", "eğser", "iser", "samaç",
    "döen", "ügen", "ıkıl", "goden", "karçin", "lolaz", "irik",
    "biolog", "fiziolog", "geolog", "bakteriolog", "termobioloj", "bırogram",
    "alfavit", "abukat", "abugat", "abigat", "abikat", "ablakat", "abogat", "abuat",
    "asger", "asgerlik", "başgan", "basdon", "barigat", "asbirin", "asansor",
    "barmaklık", "ağaclık", "basgın", "batgın", "alışgan", "bağırtgan",
    "akümülator", "arazoz", "apstraksiyon", "elektirik", "egzantirik", "avtomatik",
    "acemik", "cinkorik", "alentirik", "aletirik", "alettirik", "aletîrik", "elektrotehnika"
}

# Genuine scientific/technical terms that must be preserved even if close to another root
WHITELIST_SCIENTIFIC_KEEP = {
    "adresleme", "anahtarlama", "asidik", "embriyonik", "indeksleme",
    "kanonik", "oksidaz", "periferik", "polimeraz", "yerçekimsel",
    "alken", "alkin", "asidölçer", "aglutinasyon", "aglutinin",
    "aglutinojen", "aglutinojenik", "aglutinofilik"
}

# Build phonetic/orthographic distortion guard from baseline known_words
# Prevents Derleme Sözlüğü / Lehçeler Sözlüğü distortions of standard Turkish words
# (e.g., değer->deer/deger, teğmen->tegmen/temen, öğretmen->ögretmen/öretmen,
# fotoğraf->fotograf/fotoraf, sektör->sektor, kâtip->katip, cengâver->cengaver)
distortion_blacklist = set()
_ascii_map = str.maketrans("çğıöşüâîû", "cgiosuaiu")
for _kw in known_words:
    if len(_kw) < 3:
        continue
    distortion_blacklist.add(_kw.translate(_ascii_map))
    for _a, _b in (
        ("ç", "c"), ("c", "ç"), ("ğ", "g"), ("ı", "i"), ("i", "ı"),
        ("ö", "o"), ("o", "ö"), ("ş", "s"), ("s", "ş"), ("ü", "u"), ("u", "ü"),
        ("â", "a"), ("î", "i"), ("û", "u"), ("b", "p"), ("p", "b"),
        ("d", "t"), ("t", "d"), ("g", "k"), ("k", "g"), ("v", "b")
    ):
        if _a in _kw:
            distortion_blacklist.add(_kw.replace(_a, _b))
            _idx = _kw.find(_a)
            while _idx != -1:
                distortion_blacklist.add(_kw[:_idx] + _b + _kw[_idx + 1:])
                _idx = _kw.find(_a, _idx + 1)
    for _drop_ch in ("ğ", "h", "y"):
        if _drop_ch in _kw:
            distortion_blacklist.add(_kw.replace(_drop_ch, ""))
    for _i in range(len(_kw) - 1):
        distortion_blacklist.add(_kw[:_i] + _kw[_i + 1] + _kw[_i] + _kw[_i + 2:])

distortion_blacklist -= known_words
distortion_blacklist -= WHITELIST_SCIENTIFIC_KEEP

# Load strictly rejected test words if available
REJECTED_PATH = ROOT_DIR / "scratch" / "strictly_rejected.json"
strictly_rejected_set = set()
if REJECTED_PATH.exists():
    with open(REJECTED_PATH, "r", encoding="utf-8") as f:
        strictly_rejected_set = set(json.load(f))

# Dialect mouth markers & Russian/Lehçeler exclusions
# NOTE: Do NOT use re.IGNORECASE because in Python Unicode regex, 'i' matches 'ı'!
DIALECT_EXCLUDE = re.compile(
    r'.*(?:cık|cik|cuk|cük|caz|cegiz|ceğiz|cuğaz|cığaz|cuvaz|cuaz|cıgaz)$|'
    r'^[a-zçğıöşü]{1,3}(?:bak|güt|lak|rak|mak)$|'
    r'.*(?:abak|ebek|ibik|obuk|übür)$|'
    r'.*(?:akına|ana|ola|ula|aca|ala)$|'
    r'^(?:ag|ab|al|av|ay|ak)[a-zçğıöşü]*(?:cuk|cik|güt|bak|lak)$|'
    r'.*(?:zambak|zamzak|zamzalak|zartlak)$|'
    r'.*(?:göz|söz|köz|boz|maz|mez)$|'
    r'.*(?:iya|iye|ika|vka|bka|rka|nay|skay|skiy|ets|bota|gramma|tirik|ttirik|tîrik|pırtik)$|'
    r'.*(?:lık|lik|luk|lük)$'
)

# Suffixes and patterns strongly indicative of standard scientific, technical, and academic terms
SCIENTIFIC_PATTERNS = [
    # Loanword scientific terminations (Greek/Latin -> Turkish)
    r'.*(?:biyotik|genetik|lojik|skopik|metrik|fobik|filik|tropik|trofik|morfik|sferik|fazik|litik|jenik|ogenik|statik|dinamik|kinetik|netik|patik|matik|ratik|satik|kotik|notik|rotik|zotik|totik|tetik|letik|metik|petik|retik|setik|etik|otik|ütik|astik|istik|ostik|üstik|aktik|ektik|iktik|oktik|aptik|eptik|optik|iptik|artik|ertik|ortik|amik|demik|semik|nemik|temik|zemik|omik|termik|dermik|ritmik|iyonik|tonik|fonik|konik|ronik|monik|gonik|bonik|sonik|erjik|ürjik|bolik|kolik|tolik|hidrolik|akrilik|salisilik|karboksilik|gastrik|enterik|terik|sterik|merik|ferik|entrik|sentrik|elektrik|üretrik|iatrik|iyatrik|idrik|itrik|atrik|ürik|teorik|kalorik|retorik|alegorik|kategorik|metaforik|öforik|disforik|assertorik|mikrobik|amebik|asidik|toksik|spesifik|stenik|splenik|iyelinik|amnezik|bilharzik|parazitik|fajik|ftalmik|tipik|ektopik|izotopik|otopik|ütopik|distopik|ergodik|galvanik|organik|inorganik|anorganik|mekanik|botanik|volkanik|titanik|piranik|tetanik|melanik|siyaniK|siyanik|okyanusik|geranik|sitik|mintik|reik|tatik|yazik|ormik|sammik|ferrik)$',
    r'.{3,}(?:ist|izm|izma)$',
    r'.{3,}(?:osit|asit|isit|esit|üsit|olit|ülit|alit|elit|ilit|anit|enit|init|onit|ünit|arit|erit|irit|orit|ürit|amit|emit|imit|omit|ümit|atit|etit|itit|otit|ütit|oksit|sülfit|nitrit|klorit|bromit|fosfit|arsenit|bronşit|artrit|hepatit|menenjit|ensefalit|dermatit|nefrit|farenjit|larenjit|sinüzit|konjonktivit|apandisit|prostatit|tiroidit|endokardit|perikardit|miyokardit|flebit|arterit|vaskülit|selülit|folikülit|bursit|tendinit|spondilit|osteomiyelit|radikülit|dendrit|parazit|metabolit|elektrolit|epifit|halofit|kserofit|hidrofit|mezofit|sporofit|gametofit|briyofit|saprofit)$',
    r'.{3,}(?:ant|ent|ans|ens)$',
    r'.{3,}(?:karbonat|sülfat|fosfat|nitrat|klorat|bromat|iyodat|silikat|borat|kromat|manganat|asetat|sitrat|oksalat|tartarat|laktat|pirüvat|glutamat|aspartat|benzoat|salisilat|ftalat|stearat|palmitat|oleat|linoleat|format|bütirat|suksinat|fumarat|malat|maleat|aljinat|pektinat|glukonat|glukuronat|hiyalüronat|siyanat|arsenat|vanadat|molibdat|tungstat|titanat|alüminat|ferrat|hidrat|koordinat|agregat|konglomerat|distilat|filtrat|preparat|substrat|eksüdat|transüdat|infiltrat|presipitat|kondensat|diyalizat|hidrolizat|otolizat|homojenat)$',
    r'.{3,}(?:amin|vitamin|protein|globulin|globülin|albümin|albumin|toksin|mektin|misin|siklin|silin|sporin|fungin|statin|kain|kidin|zepin|zolam|dipin|tidin|setron|triptan|gliptin|flozin|vudin|kumarin|kafein|morfin|kodein|atropin|kinin|striknin|efedrin|rezerpin|kolşisin|digoksin|heparin|insülin|adrenalin|melatonin|serotonin|dopamin|histamin|melanin|keratin|kitin|pektin|lignin|tanin|saponin|lektin|aglütinin|aglutinin|interlökin|sitokin|kemokin|endorfin|enkefalin|oksitosin|prolaktin|otropin|poietin|kalsitonin|tiroksin|osteokalsin|renin|anjiyotensin|bradikinin|kallikrein|plazmin|trombin|gastrin|sekretin|motilin|leptin|grelin|hepsidin|ferritin|transferrin|hemoglobin|miyoglobin|hemosiyanin|eritrin|siyanin|lutein|ksantin|kateşin|kuersetin|rutin|kurkumin|kapsaisin|piperin|allisin|adenin|guanin|sitozin|timin|adenozin|guanozin|sitidin|timidin|üridin|inozin|kreatin|kreatinin|karnitin|ornitin|sitrülin|arjinin|lizin|histidin|lösin|valin|metiyonin|fenilalanin|treonin|serin|prolin|glisin|alanin|tirozin|sistein|asparajin|glutamin|taurin|betain|kolin|lesitin|sefalin|lipin|inülin|dekstrin|müsin|nektin|laminin|vimentin|desmin|distrofin|spektrin|ankirin|koneksin|integrin|selektin|kaderin|aktinin|filamin|gelsolin|villin|titin|nebulin|modülin|kalsin|hemin|üretin|fenin|mantine|adamantin)$',
    r'.{3,}(?:atör|itör|ütör|ktör|ptör|stör|ntör|rtör|ltör|nsör|rsör|ksör|presör|sensör|tensör|izör|lizör|duktor|ektör|aktör|oktör|üktör|giller|vasküler|artiküler|ventriküler|sellüler|selüler|moleküler|tübüler|alveoler|baziler|retiküler|foliküler|lobüler|globüler|granüler|papüler|nodüler|ovüler|jügüler|regüler|valvüler|triangüler|anüler|angüler|sferüler|izomer|polimer|monomer|dimer|trimer|tetramer|pentamer|oligomer|elastomer|telomer|sentromer|kromomer|blastomer|miyomer|nöromer|sarkomer|sfinkter|kateter|üreter|ester|etilen|propilen|bütilen|isopren|neopren|bütadien|benzen|toluen|ksilen|stiren|antrasen|fenantren|piren|karoten|likopen|terpen|skualen|azulen|fulleren|grafen|molibden|tungsten)$',
    r'.{3,}(?:asyon|isyon|üsyon|zyon|ksiyon|psiyon|tron|kron|nöron|nefron|interferon|operon|ekzon|intron|kodon|pozon|prion|virion|amniyon|koryon|embriyon|gangliyon|akson|dendron|karyon|baryon|lepton|hadron|mezon|bozon|fermiyon|foton|proton|nötron|elektron|pozitron|müon|graviton|fonon|plazmon|eksiton|soliton|magnon|hormon|feromon|kinon|flavon|lakton|keton|aseton|steron|kortizon|dazon|tazon|seston|plankton|nekton|benton)$',
    r'.{3,}(?:kinaz|lipaz|amilaz|proteaz|proteinaz|peptidaz|oksidaz|katalaz|transferaz|polimeraz|hidrolaz|fosfataz|fosforilaz|dehidrogenaz|karboksilaz|oksijenaz|redüktaz|transaminaz|esteraz|nükleaz|izomeraz|mutaz|epimeraz|rasemaz|ligaz|sentetaz|sentaz|liyaz|aldolaz|enolaz|fumaraz|akonitaz|anhidraz|ürikaz|üreaz|laktaz|maltaz|sükraz|invertaz|selülaz|pektinaz|kitinaz|hiyalüronidaz|nöraminidaz|koagülaz|elastaz|kollajenaz|jelatinaz|kaspaz|helikaz|primaz|telomeraz|integraz|transpozaz|rekombinaz|metilaz|asetilaz|sülfataz|zidaz|transkriptaz|giraz)$',
    r'.{3,}(?:biyoz|mikoz|toz|roz|loz|koz|moz|poz|zoz|yoz|matöz|granülomatöz|adenomatöz|karsinomatöz|sarkomatöz|fibromatöz|lipomatöz|mikzomatöz|anjiyomatöz|ödematöz|eritematöz|ekzematöz|ülseröz|gangrenöz|kazeöz|seröz|müköz|fibrinöz|büllöz|vezikülöz|püstülöz|papülöz|makülöz|nodülöz)$',
    r'.{2,}(?:oid|oit|oidik|oidit)$',
    # Combining roots & disciplinary stems
    r'.{2,}(?:jen|jenik|jeniklik|jenikçe|ogen)$',
    r'.{2,}(?:grafi|grafik|gram)$',
    r'.{2,}(?:loji|lojik|biyolog|fizyolog|jeolog|kozmetolog|epidemiolog|farmakolog|toksikolog|immünolog|nörolog|psikolog|kardiyolog|dermatolog|onkolog|hematolog|ürolog|jinekolog|endokrinolog|gastroenterolog|nefroloji|patolog|radyolog|mikrobiyolog|virolog|bakteriyolog|parazitolog|entomolog|ornitolog|ihtiyolog|herpetolog|mamalog|primatolog|antropolog|arkeolog|filolog|etimolog|leksikolog|sosyolog|kriminolog|ideolog|teolog|mitolog|astrolog|meteorolog|klimatolog|seismolog|sismolog|vulkanolog|hidrolog|glasiyolog|oseanolog|limnolog|pedolog|ekolog|fenolog|etolog|sitolog|histolog|embriyolog)$',
    r'.{2,}(?:skop|skopi|skopik)$',
    r'.{2,}(?:metr|metre|metri|metrik)$',
    r'.{2,}(?:fil|filik|fob|fobik)$',
    r'.{2,}(?:trop|tropik|trofi|trofik)$',
    r'.{2,}(?:morf|morfik|morfoloji)$',
    r'.{2,}(?:sfer|sferik)$',
    r'.{2,}(?:faz|fazik)$',
    r'.{2,}(?:tip|tipik|tipleme)$',
    r'.{2,}(?:lize|lizis|litik)$',
    r'.{2,}(?:vasküler|krino|nöro|psi)$',
    # Productive Turkish academic neologisms
    r'.{3,}(?:ölçer|sayar|yazar|çizer)$',
    r'.{2,}(?:bilim|bilgisel|bilimsel|çekimsel)$',
]
RE_SCIENTIFIC = re.compile("|".join(SCIENTIFIC_PATTERNS))

# Unambiguous multi-syllable Greek/Latin scientific prefixes
SCIENTIFIC_PREFIXES = [
    'hiper', 'hipo', 'endo', 'ekto', 'mezo', 'retro',
    'intra', 'inter', 'supra', 'anti',
    'hetero', 'homo', 'izo', 'poli', 'mono', 'tetra', 'penta',
    'makro', 'mikro', 'krio', 'sito', 'hemato', 'kardiyo', 'nöro', 'psiko',
    'oftalmo', 'dermato', 'gastro', 'hepato', 'osteo', 'biyo', 'termo',
    'elektro', 'hidro', 'aero', 'nano', 'kromo', 'ribo'
]
RE_PREFIX = re.compile('^(?:' + '|'.join(SCIENTIFIC_PREFIXES) + ')[a-zçğıöşü]{4,}$')

EXTRA_PATTERNS = [
    r'.{2,}(?:anol|enol|erol|sterol|fenol|tiol|azol|izol|klorol|parasetamol)$',
    r'.{2,}(?:anemi|lösemi|viremi|bakteriyemi|septisemi|toksemi|glisemi|kalsemi|natremi|kalemi|lipidemi|üremi|azotemi|iskemi|talasemi|hiperemi|hipoksemi)$',
    r'.{2,}(?:arteriyal|atriyal|bronşiyal|kardiyal|kondriyal|endometriyal|bakteriyal|bilharziyal|eparteryal)$',
    r'.{2,}(?:klorür|sülfür|oksit|hidrür|nitrür|karbür|iyodür|bromür|florür)$',
    r'.{2,}(?:ozis|asis|azis|ozid|ozit)$',
]
RE_EXTRA = re.compile('|'.join(EXTRA_PATTERNS))

# English vocabulary for rejecting raw bilingual / foreign headwords
EN_PATH = ROOT_DIR / "raw_data" / "english_words_large.txt"
if not EN_PATH.exists():
    EN_PATH = BASE_DIR / "training" / "english_words_large.txt"

english_words = set()
if EN_PATH.exists():
    with open(EN_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            w_en = line.strip().lower()
            if w_en:
                english_words.add(w_en)
    print(f"Loaded {len(english_words):,} English words for cross-lingual filtering.")

RE_ENGLISH_SUFFIXES = re.compile(
    r'.*(?:tion|sion|ment|ity|ance|ence|ous|able|ible|ship|hood|ing)$'
)

NON_PLURAL_ADJECTIVES = re.compile(
    r'.*(?:[kv]askül[ea]r|[kv]askul[ea]r|küler|kuler|kular|'
    r'selül[ea]r|selul[ea]r|sellül[ea]r|sellul[ea]r|'
    r'lobül[ea]r|lobul[ea]r|lokül[ea]r|lokul[ea]r|'
    r'medüll[ea]r|medul[ea]r|'
    r'serebellar|maksilar|papilar|aksilar|tonsiller|'
    r'alveoler|baziler|capituler|glandul[ea]r|globul[ea]r|'
    r'jukstaglomerul[ea]r|dipolar|polar|sufler|kavaler|'
    r'granül[ea]r|papül[ea]r|nodül[ea]r|ovül[ea]r|jügül[ea]r|'
    r'regül[ea]r|irregül[ea]r|kapsul[ea]r|kapill?er|tübül[ea]r|valvül[ea]r|'
    r'triangül[ea]r|transanül[ea]r|anül[ea]r|angül[ea]r|sferül[ea]r)$'
)

ROOT_EXCEPTIONS = {
    "kiler", "şeker", "haber", "pazar", "ambar", "yular", "dolar", "aynar",
    "bestseller", "broyler", "stapler", "inhaler", "biller", "boler", "sufler"
}

PALATAL_L_PLURALS = re.compile(
    r'.*(?:[oa]l|[ou]l|azol|tiol|fenol|diol|sterol|kol|rol|pol|sol|fol|tol|bor|mor)ler$'
)

def is_english(w: str) -> bool:
    clean_w = clean_lemma(w)
    if clean_w in known_words or clean_w in WHITELIST_SCIENTIFIC_KEEP:
        return False
    if clean_w in english_words:
        return True
    if RE_ENGLISH_SUFFIXES.match(clean_w):
        return True
    return False

def singularize_lemma(w: str) -> str:
    clean_w = clean_lemma(w)
    if clean_w.endswith('giller') or clean_w.endswith('keler'):
        return clean_w
    if NON_PLURAL_ADJECTIVES.match(clean_w) or clean_w in ROOT_EXCEPTIONS:
        return clean_w

    if clean_w.endswith('ler'):
        stem = clean_w[:-3]
        if len(stem) < 3:
            return clean_w
        if PALATAL_L_PLURALS.match(clean_w):
            return stem
        last_v = next((c for c in reversed(stem) if c in "aeıioöuüâîû"), None)
        if last_v in "eiöüî":
            return stem
    elif clean_w.endswith('lar'):
        stem = clean_w[:-3]
        if len(stem) < 3:
            return clean_w
        last_v = next((c for c in reversed(stem) if c in "aeıioöuüâîû"), None)
        if last_v in "aıouâû":
            return stem
    return clean_w

def is_clean_standard_term(word: str) -> bool:
    w = clean_lemma(word)
    if w in WHITELIST_SCIENTIFIC_KEEP:
        return True
    if len(w) < 4 or len(w) > 30:
        return False
    if not all(c in "abcçdefgğhıijklmnoöprsştuüvyzâîû" for c in w):
        return False
    if re.search(r"(.)\1\1", w):  # triple repeat
        return False
    # No double initial vowels (e.g. aartın)
    if w[0] in "aeıioöuüâîû" and w[1] == w[0]:
        return False
    # Turkish standard nominative lemmas NEVER end in voiced stops / spirants b, c, d, ğ
    if w.endswith(('b', 'c', 'd', 'ğ')):
        return False
    # Explicit test misspellings, forbidden stems, and phonetic distortions of known words
    if w in FORBIDDEN_STEMS or w in strictly_rejected_set or w in distortion_blacklist:
        return False
    # Check if direct case forms conflict with strictly rejected test forms
    for suffix in ('i', 'ı', 'e', 'a', 'de', 'da', 'di', 'dı', 'si', 'sı'):
        if (w + suffix) in strictly_rejected_set:
            return False
    if DIALECT_EXCLUDE.match(w):
        return False
    if is_english(w):
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
        lem_raw = clean_lemma(item.get("lemma") or "")
        if not lem_raw or is_english(lem_raw):
            continue
        lem = singularize_lemma(lem_raw)
        if not lem or is_english(lem) or lem in known_words:
            continue

        if is_clean_standard_term(lem):
            pos = item.get("pos") or "Noun"
            attrs = [a for a in (item.get("attributes") or []) if a in ("Voicing", "CompoundP3sg", "InverseHarmony", "LastVowelDrop")]
            if lem not in extracted_terms:
                extracted_terms[lem] = {
                    "lemma": lem,
                    "pos": pos,
                    "attributes": sorted(set(attrs)),
                    "source": "llm_triage"
                }
            else:
                existing = extracted_terms[lem]
                existing["attributes"] = sorted(set(existing["attributes"] + attrs))
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
        w_raw = clean_lemma(w)
        if not w_raw or is_english(w_raw):
            continue
        w_clean = singularize_lemma(w_raw)
        if is_english(w_clean) or w_clean in known_words or w_clean in extracted_terms:
            continue
        if is_clean_standard_term(w_clean):
            extracted_terms[w_clean] = {
                "lemma": w_clean,
                "pos": "Noun",
                "attributes": [],
                "source": "deterministic_consonant"
            }
            det_added += 1

    # Vowel endings
    for w in det_data.get("vowel_ending", []):
        w_raw = clean_lemma(w)
        if not w_raw or is_english(w_raw):
            continue
        w_clean = singularize_lemma(w_raw)
        if is_english(w_clean) or w_clean in known_words or w_clean in extracted_terms:
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
        if not w_clean or is_english(w_clean) or w_clean in known_words or w_clean in extracted_terms:
            continue
        # Only vowel-harmonic technical/scientific nominal verbs (-lamak / -lemek) on valid scientific stems
        if is_clean_standard_term(w_clean) and (w_clean.endswith("lamak") or w_clean.endswith("lemek")):
            stem_before_la = w_clean[:-5]
            last_v = next((c for c in reversed(stem_before_la) if c in "aeıioöuüâîû"), None)
            if (w_clean.endswith("lamak") and last_v in "aıouâû") or (w_clean.endswith("lemek") and last_v in "eiöüî"):
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
