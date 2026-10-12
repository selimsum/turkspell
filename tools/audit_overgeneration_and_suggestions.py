# -*- coding: utf-8 -*-
"""
Comprehensive Audit of:
1. TDK "Sıkça Yapılan Yazım Yanlışları" (Overgeneration + Top-1 Suggestion Accuracy)
2. 534 Corpus-Mined Circumflex Mismatches & Mandatory Circumflex Stems + Inflections
3. Phonological & Morphological Overgeneration Battery (Voicing, Vowel Drop, Assimilation, Harmony, Palatal-L)
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = str(ROOT_DIR / "tr")
RAW_DIR = ROOT_DIR / "raw_data"

winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
HUNSPELL_BIN = shutil.which("hunspell") or "hunspell"


def check_words(words: list[str], dict_path: str = DICT_PATH) -> tuple[list[str], list[str]]:
    if not words:
        return [], []
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    flagged = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    accepted = [w for w in words if w not in flagged]
    rejected = [w for w in words if w in flagged]
    return accepted, rejected


def get_batch_suggestions(words: list[str], dict_path: str = DICT_PATH) -> dict[str, list[str]]:
    if not words:
        return {}
    # Query in chunks of 200 to keep Hunspell -a responsive
    result = {w: [] for w in words}
    chunk_size = 200
    for i in range(0, len(words), chunk_size):
        chunk = words[i : i + chunk_size]
        p = subprocess.run(
            [HUNSPELL_BIN, "-d", dict_path, "-a"],
            input="\n".join(chunk) + "\n",
            text=True,
            capture_output=True,
            encoding="utf-8",
        )
        for line in p.stdout.splitlines():
            line = line.strip()
            if line.startswith("&"):
                parts = line.split(":", 1)
                header = parts[0].split()
                if len(header) >= 2:
                    w = header[1]
                    if len(parts) > 1:
                        result[w] = [s.strip() for s in parts[1].split(",") if s.strip()]
    return result


# ==============================================================================
# 1. TDK "SIKÇA YAPILAN YAZIM YANLIŞLARI" BATTERY
# ==============================================================================
# Each entry is (wrong_spelling, correct_spelling)
# All wrong_spellings here must be REJECTED by Hunspell and suggest correct_spelling at Top-1!
TDK_COMMON_MISSPELLINGS = [
    # Lexical & Phonological Misspellings
    ("herkez", "herkes"),
    ("herkeze", "herkese"),
    ("herkezin", "herkesin"),
    ("herkezden", "herkesten"),
    ("yalnış", "yanlış"),
    ("yalnışlık", "yanlışlık"),
    ("yanlız", "yalnız"),
    ("yanlızca", "yalnızca"),
    ("yanlızlık", "yalnızlık"),
    ("orjinal", "orijinal"),
    ("orjinallik", "orijinallik"),
    ("antreman", "antrenman"),
    ("antremanda", "antrenmanda"),
    ("antremanı", "antrenmanı"),
    ("antrenör", None),  # antrenör is correct; antreman is wrong
    ("muhattap", "muhatap"),
    ("kiprik", "kirpik"),
    ("kirbit", "kibrit"),
    ("eşki", "ekşi"),
    ("şarz", "şarj"),
    ("şarzı", "şarjı"),
    ("egsoz", "egzoz"),
    ("eksoz", "egzoz"),
    ("egzos", "egzoz"),
    ("egsos", "egzoz"),
    ("şöför", "şoför"),
    ("pantalon", "pantolon"),
    ("entellektüel", "entelektüel"),
    ("vejeteryan", "vejetaryen"),
    ("insiyatif", "inisiyatif"),
    ("dinazor", "dinozor"),
    ("klavuz", "kılavuz"),
    ("klüp", "kulüp"),
    ("süpriz", "sürpriz"),
    ("meyva", "meyve"),
    ("makina", "makine"),
    ("döküman", "doküman"),
    ("tesbih", "tespih"),
    ("laboratuar", "laboratuvar"),
    ("labaratuvar", "laboratuvar"),
    ("labaratuar", "laboratuvar"),
    ("müteahit", "müteahhit"),
    ("müsade", "müsaade"),
    ("muaffakiyet", "muvaffakiyet"),
    ("konsensus", "konsensüs"),
    ("şurda", "şurada"),
    ("orda", "orada"),
    ("gardolap", "gardırop"),
    ("gardrop", "gardırop"),
    ("asvalt", "asfalt"),
    ("karnıbahar", "karnabahar"),
    ("komidin", "komodin"),
    ("parlemento", "parlamento"),
    ("sandöviç", "sandviç"),
    ("silahşör", "silahşor"),
    ("tahamül", "tahammül"),
    ("üniverste", "üniversite"),
    ("zerafet", "zarafet"),
    ("ahçı", "aşçı"),
    ("matba", "matbaa"),
    ("traş", "tıraş"),
    ("kareografi", "koreografi"),
    ("idda", "iddia"),
    ("iddea", "iddia"),
    ("mualif", "muhalif"),
    ("artiz", "artist"),
    ("acenta", "acente"),
    ("afaroz", "aforoz"),
    ("apandist", "apandisit"),
    ("aperatif", "aperitif"),
    ("arabesk", None),  # correct
    ("bilader", "birader"),
    ("bisküüt", "bisküvi"),
    ("birşey", "bir şey"),
    ("birşeyler", "bir şeyler"),
    ("birşeyi", "bir şeyi"),
    ("herşey", "her şey"),
    ("herşeyi", "her şeyi"),
    ("hiçbirşey", "hiçbir şey"),
    ("pekçok", "pek çok"),
    ("hergün", "her gün"),
    ("herzaman", "her zaman"),
    ("heryer", "her yer"),
    ("heran", "her an"),
    ("hiçkimse", "hiç kimse"),
    ("yanısıra", "yanı sıra"),
    ("peşisıra", "peşi sıra"),
    ("ardısıra", "ardı sıra"),
    ("haftasonu", "hafta sonu"),
    ("haftaiçi", "hafta içi"),
    ("yüzyüze", "yüz yüze"),
    ("başbaşa", "baş başa"),
    ("gözgöze", "göz göze"),
    ("yanyana", "yan yana"),
    ("artarda", "art arda"),
    ("ardarda", "art arda"),
    ("peşpeşe", "peş peşe"),
    ("elele", "el ele"),
    ("dizdize", "diz dize"),
    ("omuzomuza", "omuz omuza"),
    ("içiçe", "iç içe"),
    ("üstüste", "üst üste"),
    ("altalta", "alt alta"),
    ("sağol", "sağ ol"),
    ("sağolun", "sağ olun"),
    ("hoşçakal", "hoşça kal"),
    ("hoşçakalın", "hoşça kalın"),
    ("hoşgeldin", "hoş geldin"),
    ("hoşgeldiniz", "hoş geldiniz"),
    ("hoşbulduk", "hoş bulduk"),
    ("farketmek", "fark etmek"),
    ("farketti", "fark etti"),
    ("terketmek", "terk etmek"),
    ("terketti", "terk etti"),
    ("haketmek", "hak etmek"),
    ("haketti", "hak etti"),
    ("arzetmek", "arz etmek"),
    ("arzederim", "arz ederim"),
    ("ayırtetmek", "ayırt etmek"),
    ("ayırdetmek", "ayırt etmek"),
    ("yokolmak", "yok olmak"),
    ("varolmak", "var olmak"),
    ("tabiki", "tabii ki"),
    ("iyiki", "iyi ki"),
    ("demekki", "demek ki"),
    ("öyleki", "öyle ki"),
    # Additional high-frequency TDK "Sıkça Yapılan Yanlışlar"
    ("espri", None),  # correct
    ("espiri", "espri"),
    ("espirili", "esprili"),
    ("kıraathane", None),  # correct
    ("krathane", "kıraathane"),
    ("stajer", "stajyer"),
    ("stajerlik", "stajyerlik"),
    ("poaça", "poğaça"),
    ("pohaça", "poğaça"),
    ("maydonoz", "maydanoz"),
    ("meydan", None),
    ("kurdela", "kurdele"),
    ("kolanya", "kolonya"),
    ("kavun", None),
    ("kavanoz", None),
    ("kanbur", "kambur"),
    ("çember", None),
    ("çenber", "çember"),
    ("penbe", "pembe"),
    ("perşenbe", "perşembe"),
    ("çarşanba", "çarşamba"),
    ("anbar", "ambar"),
    ("zanbak", "zambak"),
    ("sünbül", "sümbül"),
    ("çiyan", "çıyan"),
    ("tiskinmek", "tiksinmek"),
    ("müslüman", "Müslüman"),
    ("hristiyan", "Hristiyan"),
    ("hıristiyan", "Hristiyan"),
    ("yahudi", "Yahudi"),
    ("ataşelik", None),
    ("ateşe", None),  # ateşe is dative of ateş, so don't flag ateşe
    ("ataşe", None),
    ("muatap", "muhatap"),
    ("muhatab", "muhatap"),
    ("vaad", "vaat"),
    ("tesbit", "tespit"),
    ("izah", None),
    ("isbat", "ispat"),
    ("ispat", None),
    ("gangaster", "gangster"),
    ("grapon", "krapon"),
    ("gardırop", None),
    ("giderayak", None),
    ("günübirlik", None),
    ("küpür", "kupür"),
    ("küsür", "küsur"),
    ("küsülat", "küsurat"),
    ("küsurat", None),
    ("maalesef", None),
    ("malesef", "maalesef"),
    ("mağlesef", "maalesef"),
    ("metod", "metot"),
    ("standart", None),
    ("standard", "standart"),
    ("monolog", None),
    ("diyalog", None),
    ("psikolog", None),
    ("katalog", None),
    ("katalok", "katalog"),
    ("monolok", "monolog"),
    ("diyalok", "diyalog"),
    ("psikolok", "psikolog"),
    ("radyasyon", None),
    ("sezaryan", "sezaryen"),
    ("şarter", "şalter"),
    ("şofben", None),
    ("şohben", "şofben"),
    ("tazyik", None),
    ("tazzik", "tazyik"),
    ("tazik", "tazyik"),
    ("tentürdiyot", None),
    ("tenefüs", "teneffüs"),
    ("teneffüs", None),
    ("terörist", None),
    ("terorist", "terörist"),
    ("unvan", None),
    ("usül", "usul"),
    ("zerzevat", None),
    ("zıttı", "zıddı"),
    ("zıttına", "zıddına"),
]

# Words valid in Dil Derneği (and thus accepted in Universal) that MUST be rejected
# and corrected at Top-1 in the strict TDK profile (dist/turkspell-tdk/tr):
TDK_STRICT_MISSPELLINGS = [
    ("sarmısak", "sarımsak"),
    ("rasgele", "rastgele"),
    ("burda", "burada"),
    ("nerde", "nerede"),
    ("ataç", "ataş"),
    ("sıradışı", "sıra dışı"),
    ("olağandışı", "olağan dışı"),
    ("yasadışı", "yasa dışı"),
    ("çağdışı", "çağ dışı"),
]


# ==============================================================================
# 2. MORPHOLOGICAL OVERGENERATION BATTERY (MUST BE REJECTED)
# ==============================================================================
MORPHOLOGICAL_OVERGENERATION_BATTERY = [
    # Unvoiced stems with unvoiced vowel suffixes (missing voicing)
    ("kitapı", "kitabı"),
    ("kitapa", "kitaba"),
    ("kitapın", "kitabın"),
    ("kitapım", "kitabım"),
    ("ağaçı", "ağacı"),
    ("ağaça", "ağaca"),
    ("ağaçın", "ağacın"),
    ("çocuku", "çocuğu"),
    ("çocuka", "çocuğa"),
    ("çocukun", "çocuğun"),
    ("sokakı", "sokağı"),
    ("sokaka", "sokağa"),
    ("sokakın", "sokağın"),
    ("ayakı", "ayağı"),
    ("ayaka", "ayağa"),
    ("kulakı", "kulağı"),
    ("kulaka", "kulağa"),
    ("kalpi", "kalbi"),
    ("kalpe", "kalbe"),
    ("kalpin", "kalbin"),
    ("renki", "rengi"),
    ("renke", "renge"),
    ("renkin", "rengin"),
    ("borçu", "borcu"),
    ("borça", "borca"),
    ("borçun", "borcun"),
    ("kâğıtı", "kâğıdı"),
    ("kâğıta", "kâğıda"),
    ("umutu", "umudu"),
    ("umuta", "umuda"),
    ("kanatı", "kanadı"),
    ("yurtu", "yurdu"),
    ("yurta", "yurda"),
    ("kurtu", "kurdu"),
    ("kurta", "kurda"),
    ("derti", "derdi"),
    ("derte", "derde"),
    ("genci", None),  # genci is valid
    ("gençi", "genci"),
    ("gençe", "gence"),
    # Non-voicing loanwords that were mistakenly voiced
    ("hukuğu", "hukuku"),
    ("hukuğa", "hukuka"),
    ("hukuğun", "hukukun"),
    ("ahlağı", "ahlakı"),
    ("ahlağa", "ahlaka"),
    ("evrağı", "evrakı"),
    ("evrağa", "evraka"),
    ("ittifağı", "ittifakı"),
    ("ittifağa", "ittifaka"),
    ("merağı", "merakı"),
    ("merağa", "meraka"),
    ("stoğu", "stoku"),
    ("stoğa", "stoka"),
    ("felakedi", "felaketi"),
    ("felakede", "felakete"),
    ("hakikadi", "hakikati"),
    ("tabiadı", "tabiatı"),
    ("sanadı", "sanatı"),
    ("devledi", "devleti"),
    ("cumhuriyedi", "cumhuriyeti"),
    ("edebiyadı", "edebiyatı"),
    ("inşaadı", "inşaatı"),
    ("hayadı", "hayatı"),
    ("saadi", "saati"),
    ("pakedi", "paketi"),
    ("biledi", None),  # bilemek -> biledi is valid!
    ("kasedi", "kaseti"),
    ("ankedi", "anketi"),
    ("rokedi", "roketi"),
    ("cekedi", "ceketi"),
    ("markedi", "marketi"),
    ("tabledi", "tableti"),
    ("internedi", "interneti"),
    ("pilodu", "pilotu"),
    ("robodu", "robotu"),
    # Missing vowel drop (excluding homonyms like buru->burunu, is->isimi, bey->beyini, akı->akılı)
    ("karına", None),  # karı -> karına is valid
    ("oğulu", "oğlu"),
    ("oğula", "oğla"),
    ("oğulun", "oğlun"),
    ("ömürü", "ömrü"),
    ("ömüre", "ömre"),
    ("ömürün", "ömrün"),
    ("şehiri", "şehri"),
    ("şehire", "şehre"),
    ("şehirin", "şehrin"),
    ("nehiri", "nehri"),
    ("nehire", "nehre"),
    ("nehirin", "nehrin"),
    ("zehiri", "zehri"),
    ("zehire", "zehre"),
    ("zehirin", "zehrin"),
    ("resimi", "resmi"),
    ("resime", "resme"),
    ("resimin", "resmin"),
    ("cisimi", "cismi"),
    ("cisime", "cisme"),
    ("cisimin", "cismin"),
    ("kısımı", "kısmı"),
    ("kısıma", "kısma"),
    ("kısımın", "kısmın"),
    ("göğüsü", "göğsü"),
    ("göğüse", "göğse"),
    ("omuzu", "omzu"),
    ("omuza", "omza"),
    ("omuzun", "omzun"),
    ("ufuku", "ufku"),
    ("ufuka", "ufka"),
    ("ufukun", "ufkun"),
    ("keyifi", "keyfi"),
    ("keyife", "keyfe"),
    ("keyifin", "keyfin"),
    ("sabırı", "sabrı"),
    ("sabıra", "sabra"),
    ("sabırın", "sabrın"),
    ("akıla", "akla"),
    ("fikiri", "fikri"),
    ("fikire", "fikre"),
    ("fikirin", "fikrin"),
    ("zikiri", "zikri"),
    ("zikire", "zikre"),
    ("şükürü", "şükrü"),
    ("şüküre", "şükre"),
    ("hükümü", "hükmü"),
    ("hüküme", "hükme"),
    ("zulümü", "zulmü"),
    ("zulüme", "zulme"),
    # Consonant assimilation violations (-da/-de instead of -ta/-te, -dı/-di instead of -tı/-ti)
    ("kitapda", "kitapta"),
    ("kitapdan", "kitaptan"),
    ("ağaçda", "ağaçta"),
    ("ağaçdan", "ağaçtan"),
    ("sokakda", "sokakta"),
    ("sokakdan", "sokaktan"),
    ("çocukda", "çocukta"),
    ("çocukdan", "çocuktan"),
    ("girişde", "girişte"),
    ("girişden", "girişten"),
    ("bakışda", "bakışta"),
    ("bakışdan", "bakıştan"),
    ("sınıfda", "sınıfta"),
    ("sınıfdan", "sınıftan"),
    ("mutfakda", "mutfakta"),
    ("mutfakdan", "mutfaktan"),
    ("yapdı", "yaptı"),
    ("gitdi", "gitti"),
    ("bakdı", "baktı"),
    ("seçdi", "seçti"),
    ("koşdu", "koştu"),
    ("çalışdı", "çalıştı"),
    ("yapdığı", "yaptığı"),
    ("gitdiği", "gittiği"),
    ("bakdığı", "baktığı"),
    # Palatal-L harmony violations
    ("alkolu", "alkolü"),
    ("alkolun", "alkolün"),
    ("alkolsuz", "alkolsüz"),
    ("alkollar", "alkoller"),
    ("kontrolu", "kontrolü"),
    ("kontrolun", "kontrolün"),
    ("kontrolsuz", "kontrolsüz"),
    ("sembolu", "sembolü"),
    ("petrolu", "petrolü"),
    ("protokolu", "protokolü"),
    ("ampulu", "ampulü"),
    ("ampulsuz", "ampulsüz"),
    ("mahsulu", "mahsulü"),
    ("usulu", "usulü"),
    ("meşgulu", "meşgulü"),
    ("mesulu", "mesulü"),
    ("mamulu", "mamulü"),
    ("makulu", "makulü"),
]


def main():
    print("=================================================================")
    print("1. Auditing TDK 'Sıkça Yapılan Yazım Yanlışları' Battery...")
    print("=================================================================")
    pos_controls = [w for w, c in TDK_COMMON_MISSPELLINGS if c is None and w.strip() == w]
    typo_pairs = [(w, c) for w, c in TDK_COMMON_MISSPELLINGS if c is not None]

    _, pos_rejected = check_words(pos_controls)
    if pos_rejected:
        print(f"  [!] Positive control words rejected: {pos_rejected}")

    typo_words = [w for w, _ in typo_pairs]
    accepted_typos, rejected_typos = check_words(typo_words)
    print(f"  Total universal typo pairs: {len(typo_pairs)}")
    print(f"  Leaked (accepted) typos: {len(accepted_typos)} -> {accepted_typos}")

    sugs_map = get_batch_suggestions(rejected_typos)
    top1_hits = 0
    top3_hits = 0
    missed_top1 = []
    for w, target in typo_pairs:
        if w in accepted_typos:
            missed_top1.append((w, target, "ACCEPTED_AS_VALID", []))
            continue
        sugs = sugs_map.get(w, [])
        if sugs and sugs[0] == target:
            top1_hits += 1
            top3_hits += 1
        elif target in sugs[:3]:
            top3_hits += 1
            missed_top1.append((w, target, f"RANK_{sugs.index(target)+1}", sugs[:5]))
        else:
            missed_top1.append((w, target, "NOT_IN_TOP3", sugs[:5]))

    print(f"  Top-1 Accuracy: {top1_hits}/{len(typo_pairs)} ({top1_hits/len(typo_pairs)*100:.1f}%)")
    print(f"  Top-3 Accuracy: {top3_hits}/{len(typo_pairs)} ({top3_hits/len(typo_pairs)*100:.1f}%)")
    if missed_top1:
        print(f"  Missed Top-1 ({len(missed_top1)}):")
        for w, t, status, s in missed_top1[:40]:
            print(f"    {w:18s} -> expected '{t:15s}' | {status:17s} | got {s}")

    tdk_dict_path = str(ROOT_DIR / "dist" / "turkspell-tdk" / "tr")
    if (ROOT_DIR / "dist" / "turkspell-tdk" / "tr.dic").exists():
        tdk_words = [w for w, _ in TDK_STRICT_MISSPELLINGS]
        acc_tdk, rej_tdk = check_words(tdk_words, dict_path=tdk_dict_path)
        tdk_sugs = get_batch_suggestions(rej_tdk, dict_path=tdk_dict_path)
        tdk_top1 = sum(1 for w, t in TDK_STRICT_MISSPELLINGS if w not in acc_tdk and tdk_sugs.get(w, [])[:1] == [t])
        print(f"  TDK-Strict Profile Only ({len(TDK_STRICT_MISSPELLINGS)} DD-accepted words): Leaked={len(acc_tdk)}, Top-1={tdk_top1}/{len(TDK_STRICT_MISSPELLINGS)}")

    print("\n=================================================================")
    print("2. Auditing Morphological Overgeneration Battery...")
    print("=================================================================")
    morph_pairs = [(w, c) for w, c in MORPHOLOGICAL_OVERGENERATION_BATTERY if c is not None]
    morph_words = [w for w, _ in morph_pairs]
    acc_morph, rej_morph = check_words(morph_words)
    print(f"  Total morphological error forms: {len(morph_pairs)}")
    print(f"  Leaked (accepted) forms: {len(acc_morph)} -> {acc_morph}")

    morph_sugs = get_batch_suggestions(rej_morph)
    m_top1 = 0
    m_top3 = 0
    m_missed = []
    for w, target in morph_pairs:
        if w in acc_morph:
            m_missed.append((w, target, "ACCEPTED_AS_VALID", []))
            continue
        sugs = morph_sugs.get(w, [])
        if sugs and sugs[0] == target:
            m_top1 += 1
            m_top3 += 1
        elif target in sugs[:3]:
            m_top3 += 1
            m_missed.append((w, target, f"RANK_{sugs.index(target)+1}", sugs[:5]))
        else:
            m_missed.append((w, target, "NOT_IN_TOP3", sugs[:5]))

    print(f"  Morphological Error Top-1 Suggestion: {m_top1}/{len(morph_pairs)} ({m_top1/len(morph_pairs)*100:.1f}%)")
    print(f"  Morphological Error Top-3 Suggestion: {m_top3}/{len(morph_pairs)} ({m_top3/len(morph_pairs)*100:.1f}%)")
    if m_missed:
        print(f"  Morphological Missed Top-1 ({len(m_missed)}):")
        for w, t, status, s in m_missed[:40]:
            print(f"    {w:18s} -> expected '{t:15s}' | {status:17s} | got {s}")

    print("\n=================================================================")
    print("3. Auditing Corpus-Mined Circumflex Entries & Inflections...")
    print("=================================================================")
    # Check parsed_10k_entries.json and authority_circumflex_entries.json
    circumflex_candidates = []
    circ_path = RAW_DIR / "authority_circumflex_entries.json"
    if circ_path.exists():
        with open(circ_path, encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                w = item["word"]
                uh = item["unhatted_lemma"]
                oh = item["official_hatted_lemma"]
                # Reconstruct expected hatted surface word
                if w.startswith(uh):
                    expected_w = oh + w[len(uh):]
                elif uh.endswith("t") and w.startswith(uh[:-1] + "d"):
                    expected_w = oh[:-1] + "d" + w[len(uh):]
                else:
                    expected_w = oh
                circumflex_candidates.append((w, expected_w))

    # Also build a comprehensive inflected circumflex test battery
    inflected_circ_stems = [
        ("zekâ", "zeka", ["", "sı", "sını", "sına", "sında", "sından", "lı", "sız"]),
        ("rüzgâr", "rüzgar", ["", "ı", "a", "da", "dan", "ın", "lar", "ları", "lı"]),
        ("kâğıt", "kağıt", ["", "ta", "tan", "lar", "ları", "larda"]),
        ("kâğıd", "kağıd", ["ı", "a", "ın", "ım", "ımız", "ında", "ından", "ını", "ına", "ıyla"]),
        ("mekân", "mekan", ["", "ı", "a", "da", "dan", "ın", "lar", "ları", "larda", "sal"]),
        ("şikâyet", "şikayet", ["", "i", "e", "te", "ten", "in", "im", "ler", "leri", "çi"]),
        ("mahkûm", "mahkum", ["", "u", "a", "da", "dan", "un", "lar", "ları", "iyet"]),
        ("imkân", "imkan", ["", "ı", "a", "da", "dan", "ın", "lar", "ları", "larımız", "sız", "sızlık"]),
        ("hikâye", "hikaye", ["", "yi", "ye", "de", "den", "nin", "si", "sini", "ler", "leri"]),
        ("muhafazakâr", "muhafazakar", ["", "lar", "lık", "lığın"]),
        ("erkân", "erkan", ["", "ı", "ın", "ına"]),
        ("harekât", "harekat", ["", "ı", "a", "ta", "tan", "ın", "ında"]),
        ("hâkimiyet", "hakimiyet", ["", "i", "e", "te", "ten", "in", "ini", "inde"]),
        ("iskân", "iskan", ["", "ı", "a", "da", "dan", "ın"]),
        ("kâtip", "katip", ["", "lik", "ler"]),
        ("kâtib", "katib", ["i", "e", "in"]),
        ("kâşif", "kaşif", ["", "i", "in", "ler", "leri"]),
        ("hünkâr", "hünkar", ["", "ı", "a", "ın"]),
        ("dükkân", "dükkan", ["", "ı", "a", "da", "dan", "ın", "lar", "ları"]),
        ("tezgâh", "tezgah", ["", "ı", "a", "ta", "tan", "ın", "lar", "ları"]),
        ("karargâh", "karargah", ["", "ı", "a", "ta", "tan", "ın", "ında"]),
        ("ikametgâh", "ikametgah", ["", "ı", "a", "ta", "tan", "ın"]),
        ("güzergâh", "güzergah", ["", "ı", "a", "ta", "tan", "ın", "ında"]),
        ("mükâfat", "mükafat", ["", "ı", "a", "ta", "tan", "ın", "lar"]),
        ("fedakâr", "fedakar", ["", "lık", "lığı", "ca", "lar"]),
        ("sahtekâr", "sahtekar", ["", "lık", "lığı", "lar"]),
        ("vekâlet", "vekalet", ["", "i", "e", "te", "ten", "in", "en", "name"]),
        ("nikâh", "nikah", ["", "ı", "a", "ta", "tan", "ın", "lı", "sız"]),
        ("kâinat", "kainat", ["", "ı", "a", "ta", "tan", "ın"]),
        ("sükût", "sükut", ["", "u", "a", "ta", "tan", "un"]),
        ("sükûnet", "sükunet", ["", "i", "e", "te", "ten", "in", "le", "li"]),
        ("kâbus", "kabus", ["", "u", "a", "ta", "tan", "un", "lar"]),
        ("bekâr", "bekar", ["", "lık", "lığı", "lar"]),
        ("inkâr", "inkar", ["", "ı", "a", "da", "dan", "ın", "cı"]),
        ("güzergâh", "güzergah", ["", "ı", "ta", "ında"]),
        ("aşikâr", "aşikar", ["", "dır"]),
        ("ahkâm", "ahkam", ["", "ı", "ın"]),
        ("yadigâr", "yadigar", ["", "ı", "ın", "lar"]),
        ("zanaatkâr", "zanaatkar", ["", "lar", "lık", "lığı"]),
        ("sanatkâr", "sanatkar", ["", "lar", "lık", "lığı"]),
        ("hizmetkâr", "hizmetkar", ["", "lar", "lık"]),
        ("günahkâr", "günahkar", ["", "lar", "lık"]),
        ("bestekâr", "bestekar", ["", "lar", "lık"]),
        ("cengâver", "cengaver", ["", "ler", "lik"]),
        ("malikâne", "malikane", ["", "si", "de", "ye", "ler"]),
    ]
    for hatted_stem, unhatted_stem, suffixes in inflected_circ_stems:
        for suf in suffixes:
            circumflex_candidates.append((unhatted_stem + suf, hatted_stem + suf))

    # Deduplicate circumflex_candidates
    seen_c = set()
    dedup_circ = []
    for u, h in circumflex_candidates:
        if (u, h) not in seen_c:
            seen_c.add((u, h))
            dedup_circ.append((u, h))

    u_words = [u for u, _ in dedup_circ]
    h_words = [h for _, h in dedup_circ]
    acc_u, rej_u = check_words(u_words)
    _, rej_h = check_words(h_words)
    print(f"  Total circumflex test pairs: {len(dedup_circ)}")
    if rej_h:
        print(f"  [!] Official hatted forms REJECTED ({len(rej_h)}): {rej_h}")
    print(f"  Unhatted forms accepted as valid ({len(acc_u)}): {acc_u}")

    circ_sugs = get_batch_suggestions(rej_u)
    c_top1 = 0
    c_top3 = 0
    c_missed = []
    for u, h in dedup_circ:
        if u in acc_u:
            c_missed.append((u, h, "ACCEPTED_AS_VALID", []))
            continue
        sugs = circ_sugs.get(u, [])
        sugs_lower = [s.replace("I", "ı").replace("İ", "i").lower() for s in sugs]
        h_lower = h.replace("I", "ı").replace("İ", "i").lower()
        if sugs_lower and sugs_lower[0] == h_lower:
            c_top1 += 1
            c_top3 += 1
        elif h_lower in sugs_lower[:3]:
            c_top3 += 1
            c_missed.append((u, h, f"RANK_{sugs_lower.index(h_lower)+1}", sugs[:5]))
        else:
            c_missed.append((u, h, "NOT_IN_TOP3", sugs[:5]))

    print(f"  Circumflex Top-1 Suggestion: {c_top1}/{len(dedup_circ)} ({c_top1/len(dedup_circ)*100:.1f}%)")
    print(f"  Circumflex Top-3 Suggestion: {c_top3}/{len(dedup_circ)} ({c_top3/len(dedup_circ)*100:.1f}%)")
    if c_missed:
        print(f"  Circumflex Missed Top-1 ({len(c_missed)}):")
        for u, h, status, s in c_missed[:50]:
            print(f"    {u:18s} -> expected '{h:15s}' | {status:17s} | got {s}")


if __name__ == "__main__":
    main()
