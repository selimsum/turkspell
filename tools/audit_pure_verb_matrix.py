# -*- coding: utf-8 -*-
"""
Pure Verb-Only & Noun-Only Paradigm Matrix Auditor
==================================================
Tests the actual affix rules in tr.aff by creating a minimal dictionary containing
ONLY the base verb infinitives (without pre-derived verbal nouns in tr.dic masking gaps!)
and testing every grammatical combination across all 13 verb stem classes.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "build"))
from utf8_flag_mapping import LONG_TO_UTF8

# Find hunspell
winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
HUNSPELL_BIN = shutil.which("hunspell") or "hunspell"


def get_verb_flags_from_dic(verbs: list[str]) -> dict[str, str]:
    found = {}
    with open(ROOT_DIR / "tr.dic", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "/" in line:
                w, fl = line.split("/", 1)
                if w in verbs:
                    found[w] = fl
    return found


def run_pure_verb_matrix():
    # 13 canonical verbs representing all 13 verb classes in Turkspell:
    # VB: yapmak (back unrounded cons)
    # VR: kurmak (back rounded cons)
    # VF: севmek / gelmek (front unrounded cons)
    # VG: görmek (front rounded cons)
    # VA: başlamak (back unrounded vowel)
    # VS: okumak (back rounded vowel)
    # VE: beklemek (front unrounded vowel)
    # VH: yürümek (front rounded vowel)
    # VK: tatmak (back unrounded voicing)
    # VL: yutmak/avunmak -> wait let's check which verb has VL
    # VM: etmek (front unrounded voicing)
    # VN: gütmek (front rounded voicing)
    # VY: demek (narrowing verb)
    rep_verbs = [
        "yapmak", "koymak", "gelmek", "görmek",
        "başlamak", "okumak", "beklemek", "yürümek",
        "tatmak", "etmek", "gitmek", "gütmek", "demek", "edilmek"
    ]
    verb_flags = get_verb_flags_from_dic(rep_verbs)
    
    # Create temporary pure-verb dictionary
    tmp_dir = ROOT_DIR / "reports" / "tmp_pure_verb"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT_DIR / "tr.aff", tmp_dir / "pure.aff")
    
    with open(tmp_dir / "pure.dic", "w", encoding="utf-8") as f:
        f.write(f"{len(verb_flags)}\n")
        for v, fl in sorted(verb_flags.items()):
            f.write(f"{v}/{fl}\n")

    dict_prefix = str(tmp_dir / "pure")

    # Now let's generate comprehensive grammatical paradigms for "yapmak", "koymak", "gelmek", "görmek", "başlamak", "beklemek", "okumak", "yürümek", "etmek"
    # Let's test on 'yapmak' (back unrounded), 'koymak' (back rounded), 'gelmek' (front unrounded), 'görmek' (front rounded), 'başlamak' (vowel back), 'beklemek' (vowel front), 'etmek' (voicing)
    paradigms = {
        # 1. Positive Verbal Noun (-ma / -me) bare & cases (when -ma/-me is NOT a separate entry in .dic!)
        "1. Positive Verbal Noun (-ma/-me) Bare & Cases": [
            "yapma", "yapmayı", "yapmaya", "yapmada", "yapmadan", "yapmanın", "yapmayla",
            "koyma", "koymayı", "koymaya", "koymada", "koymadan", "koymanın", "koymayla",
            "gelme", "gelmeyi", "gelmeye", "gelmede", "gelmeden", "gelmenin", "gelmeyle",
            "görme", "görmeyi", "görmeye", "görmede", "görmeden", "görmenin", "görmeyle",
            "başlama", "başlamayı", "başlamaya", "başlamada", "başlamadan", "başlamanın", "başlamayla",
            "bekleme", "beklemeyi", "beklemeye", "beklemede", "beklemeden", "beklemenin", "beklemeyle",
        ],
        # 2. Negative Verbal Noun (-mama / -meme) bare & cases
        "2. Negative Verbal Noun (-mama/-meme) Bare & Cases": [
            "yapmama", "yapmamayı", "yapmamaya", "yapmamada", "yapmamadan", "yapmamanın", "yapmamayla",
            "koymama", "koymamayı", "koymamaya", "koymamada", "koymamadan", "koymamanın", "koymamayla",
            "gelmeme", "gelmemeyi", "gelmemeye", "gelmemede", "gelmemeden", "gelmemenin", "gelmemeyle",
            "görmeme", "görmemeyi", "görmemeye", "görmemede", "görmemeden", "görmemenin", "görmemeyle",
        ],
        # 3. Inability Verbal Noun (-amama / -ememe) bare, cases & possessives
        "3. Inability Verbal Noun (-amama/-ememe) Bare, Cases & Possessives": [
            "yapamama", "yapamamayı", "yapamamaya", "yapamamada", "yapamamadan", "yapamamanın", "yapamamayla",
            "koyamama", "koyamamayı", "koyamamaya", "koyamamada", "koyamamadan", "koyamamanın", "koyamamayla",
            "gelememe", "gelememeyi", "gelememeye", "gelememede", "gelememeden", "gelememenin", "gelememeyle",
            "görememe", "görememeyi", "görememeye", "görememede", "görememeden", "görememenin", "görememeyle",
            "yapamamam", "yapamaman", "yapamamamız", "yapamamanız", "yapamamaları",
            "yapamamamdan", "yapamamamızdan", "yapamamalarından", "yapamamasından", "yapamamasında",
            "koyamamasından", "koyamamamızın", "gelememesinden", "gelemememizden",
        ],
        # 4. Ability Verbal Noun (-abilme / -ebilme) bare, cases & possessives
        "4. Ability Verbal Noun (-abilme/-ebilme) Bare, Cases & Possessives": [
            "yapabilme", "yapabilmeyi", "yapabilmeye", "yapabilmede", "yapabilmeden", "yapabilmenin", "yapabilmeyle",
            "koyabilme", "koyabilmeyi", "koyabilmeye", "koyabilmede", "koyabilmeden", "koyabilmenin", "koyabilmeyle",
            "gelebilme", "gelebilmeyi", "gelebilmeye", "gelebilmede", "gelebilmeden", "gelebilmenin", "gelebilmeyle",
            "görebilme", "görebilmeyi", "görebilmeye", "görebilmede", "görebilmeden", "görebilmenin", "görebilmeyle",
            "başlayabilme", "başlayabilmeyi", "başlayabilmeye", "başlayabilmede", "başlayabilmeden", "başlayabilmenin", "başlayabilmeyle",
            "edebilme", "edebilmeyi", "edebilmeye", "edebilmede", "edebilmeden", "edebilmenin", "edebilmeyle",
            "yapabilmem", "yapabilmen", "yapabilmesi", "yapabilmemiz", "yapabilmeniz", "yapabilmeleri",
            "yapabilmemi", "yapabilmeme", "yapabilmemde", "yapabilmemden", "yapabilmemin", "yapabilmemle",
            "yapabilmemizi", "yapabilmemize", "yapabilmemizde", "yapabilmemizden", "yapabilmemizin",
            "yapabilmelerini", "yapabilmelerine", "yapabilmelerinde", "yapabilmelerinden", "yapabilmelerinin",
        ],
        # 5. Ability Infinitive (-abilmek / -ebilmek) cases
        "5. Ability Infinitive (-abilmek/-ebilmek) Cases & Copulas": [
            "yapabilmek", "yapabilmekte", "yapabilmekten", "yapabilmekle", "yapabilmektir", "yapabilmekti", "yapabilmektense",
            "koyabilmek", "koyabilmekte", "koyabilmekten", "koyabilmekle", "koyabilmektir", "koyabilmekti", "koyabilmektense",
            "edebilmek", "edebilmekte", "edebilmekten", "edebilmekle", "edebilmektir", "edebilmekti", "edebilmektense",
        ],
        # 6. Ability Participles (-abildiği, -abileceği) bare & cases
        "6. Ability Participles (-abildiği, -abileceği) Bare & Cases": [
            "yapabildiği", "yapabildiğim", "yapabildiğin", "yapabildiğimiz", "yapabildiğiniz", "yapabildikleri",
            "yapabildiğimizi", "yapabildiğimizden", "yapabildiğinizi", "yapabildiklerini", "yapabildiklerinden",
            "yapabildiklerim", "yapabildiklerimiz", "yapabildikleriniz",
            "yapabileceği", "yapabileceğim", "yapabileceğin", "yapabileceğimiz", "yapabileceğiniz", "yapabilecekleri",
            "yapabileceğimizi", "yapabileceğimizden", "yapabileceklerini", "yapabileceklerinden",
            "yapabileceklerim", "yapabileceklerimiz", "yapabilecekleriniz",
            "koyabildiğim", "koyabildiğimiz", "koyabileceğim", "koyabileceğimiz",
            "edebildiğim", "edebildiğimiz", "edebileceğim", "edebileceğimiz",
        ],
        # 7. Inability Participles (-amadığı, -amayacağı) bare & cases
        "7. Inability Participles (-amadığı, -amayacağı) Bare & Cases": [
            "yapamadığı", "yapamadığım", "yapamadığın", "yapamadığımız", "yapamadığınız", "yapamadıkları",
            "yapamadığımı", "yapamadığımdan", "yapamadığımızı", "yapamadığımızdan", "yapamadıklarını",
            "yapamadıklarım", "yapamadıklarımız", "yapamadıklarınız",
            "yapamayacağı", "yapamayacağım", "yapamayacağın", "yapamayacağımız", "yapamayacağınız", "yapamayacakları",
            "yapamayacağımı", "yapamayacağımdan", "yapamayacağımızı", "yapamayacağımızdan",
            "koyamadığım", "koyamadığın", "koyamadığımız", "koyamadığınız",
            "edemediğim", "edemediğin", "edemediğimiz", "edemediğiniz",
        ],
        # 8. Ability Evidential & Conditional & Necessitative & Converbs
        "8. Ability Evidential, Conditional, Necessitative & Converbs": [
            "yapabilmiş", "yapabilmişim", "yapabilmişsin", "yapabilmişiz", "yapabilmişsiniz", "yapabilmişler",
            "yapabilse", "yapabilsem", "yapabilsen", "yapabilsek", "yapabilseniz", "yapabilseler",
            "yapabilseydi", "yapabilseydim", "yapabilseydin", "yapabilseydik", "yapabilseydiniz", "yapabilseydiler",
            "yapabilmeli", "yapabilmeliyim", "yapabilmelisin", "yapabilmeliyiz", "yapabilmelisiniz", "yapabilmeliler",
            "yapabilince", "yapabilinceye", "yapabildikçe", "yapabildikten", "yapabilmeksizin",
        ],
        # 9. Inability Evidential & Conditional & Necessitative & Converbs
        "9. Inability Evidential, Conditional, Necessitative & Converbs": [
            "yapamamış", "yapamamışım", "yapamamışsın", "yapamamışız", "yapamamışsınız", "yapamamışlar",
            "yapamasa", "yapamasam", "yapamasan", "yapamasak", "yapamasanız", "yapamasalar",
            "yapamasaydı", "yapamasaydım", "yapamasaydın", "yapamasaydık", "yapamasaydınız", "yapamasaydılar",
            "yapamamalı", "yapamamalıyım", "yapamamalısın", "yapamamalıyız", "yapamamalısınız", "yapamamalılar",
            "yapamayınca", "yapamayıncaya", "yapamadıkça", "yapamadıktan", "yapamamaksızın", "yapamadan",
        ],
        # 10. Negative Evidential & Future & Conditional Copulas
        "10. Negative Evidential, Future & Conditional Copulas": [
            "yapmamıştı", "yapmamıştım", "yapmamıştın", "yapmamıştık", "yapmamıştınız", "yapmamıştılar",
            "yapmayacaktı", "yapmayacaktım", "yapmayacaktın", "yapmayacaktık", "yapmayacaktınız", "yapmayacaktılar",
            "yapmayacakmış", "yapmayacakmışım", "yapmayacaksa", "yapmayacaksam", "yapmayacaksak",
            "yapmasaydı", "yapmasaydım", "yapmasaydın", "yapmasaydık", "yapmasaydınız", "yapmasaydılar",
            "yapmadıysa", "yapmadıysam", "yapmadıysan", "yapmadıysak", "yapmadıysanız", "yapmadıysalar",
        ],
        # 11. Converb & Similative & Optative Chains (-asıya, -madıkça, -acakken, -mışken, -casına)
        "11. Converb & Similative Chains (-asıya, -alı/-eli, -acakken, -mışken, -casına)": [
            "yapasıya", "koyasıya", "göresiye", "edilesiye", "edesiye", "gidesiye", "diyesiye", "başlayasıya",
            "okuyalı", "yürüyeli", "edeli", "gideli", "tadalı", "diyeli",
            "yapacakken", "koyacakken", "gelecekken", "görecekken",
            "yapmışken", "koymuşken", "gelmişken", "görmüşken",
            "yapmamışken", "koymamışken", "gelmemişken", "görmemişken",
            "yapamayacakken", "koyamayacakken", "gelemeyecekken",
            "yapabilecekken", "koyabilecekken", "gelebilecekken",
            "yaparcasına", "koyarcasına", "gelircesine", "görürcesine",
            "yapmazcasına", "gelmezcesine", "yapamazcasına", "gelemezcesine",
        ],
        # 12. Verbal Noun (-ış / -iş / -uş / -üş) Bare, Cases & Possessives
        "12. Verbal Noun (-ış/-iş/-uş/-üş) Bare, Cases & Possessives": [
            "yapış", "yapışı", "yapışa", "yapışta", "yapıştan", "yapışın", "yapışla", "yapışlar",
            "koyuş", "koyuşu", "koyuşa", "koyuşta", "koyuştan", "koyuşun", "koyuşla", "koyuşlar",
            "geliş", "gelişi", "gelişe", "gelişte", "gelişten", "gelişin", "gelişle", "gelişler",
            "görüş", "görüşü", "görüşe", "görüşte", "görüşten", "görüşün", "görüşle", "görüşler",
            "okuyuş", "okuyuşu", "okuyuşa", "okuyuşta", "okuyuştan", "okuyuşun",
            "yürüyüş", "yürüyüşü", "yürüyüşe", "yürüyüşte", "yürüyüşten", "yürüyüşün",
            "yapışım", "yapışın", "yapışımız", "yapışınız", "yapışları",
            "yapışımdan", "yapışımızdan", "yapışlarından",
        ],
        # 13. Positive & Negative Participles (-dığı, -acağı, -madığı, -mayacağı)
        "13. Positive & Negative Participles (-dığı, -acağı, -madığı, -mayacağı)": [
            "yaptığı", "yaptığım", "yaptığın", "yaptığımız", "yaptığınız", "yaptıkları",
            "yaptıklarım", "yaptıklarımız", "yaptıklarınız", "yaptıklarımdan", "yaptıklarımızdan",
            "yapacağı", "yapacağım", "yapacağın", "yapacağımız", "yapacağınız", "yapacakları",
            "yapacaklarım", "yapacaklarımız", "yapacaklarınız", "yapacaklarımdan", "yapacaklarımızdan",
            "yapmadığı", "yapmadığım", "yapmadığın", "yapmadığımız", "yapmadığınız", "yapmadıkları",
            "yapmadıklarım", "yapmadıklarımız", "yapmadıklarınız", "yapmadıklarımdan", "yapmadıklarımızdan",
            "yapmayacağı", "yapmayacağım", "yapmayacağın", "yapmayacağımız", "yapmayacağınız", "yapmayacakları",
            "yapmayacaklarım", "yapmayacaklarımız", "yapmayacaklarınız", "yapmayacaklarımdan",
            "dediği", "dediğim", "dediğimiz", "diyeceği", "diyeceğim", "diyeceğimiz", "diyeceklerim", "diyeceklerimizden",
            "deyiş", "deyişi", "deyişe", "deyişte", "deyişten", "deyişin",
        ],
        # 14. Progressive Formal (-makta/-mekte) + Person & Copula across Polarities
        "14. Progressive Formal (-makta/-mekte) + Person & Copula": [
            "yapmakta", "yapmaktayım", "yapmaktasın", "yapmaktayız", "yapmaktasınız", "yapmaktalar",
            "yapmaktaydı", "yapmaktaymış", "yapmaktaysa",
            "yapmamakta", "yapmamaktayım", "yapmamaktayız", "yapmamaktaydı",
            "yapamamakta", "yapamamaktayım", "yapamamaktayız", "yapamamaktaydı",
            "yapabilmekte", "yapabilmekteyim", "yapabilmektesin", "yapabilmekteyiz", "yapabilmektesiniz", "yapabilmekteler",
            "yapabilmekteydi", "yapabilmekteymiş",
        ],
        # 15. Complex Compound Tenses on Ability & Inability (-abiliyordu, -abilecekti, -abilirdi, -amazdı, -abilmeliydi)
        "15. Complex Compound Tenses on Ability & Inability": [
            "yapabiliyordu", "yapabiliyordum", "yapabiliyordun", "yapabiliyorduk", "yapabiliyordunuz", "yapabiliyordular",
            "yapamıyordu", "yapamıyordum", "yapamıyordun", "yapamıyorduk", "yapamıyordunuz",
            "yapabilecekti", "yapabilecektim", "yapabilecektin", "yapabilecektik", "yapabilecektiniz", "yapabilecektiler",
            "yapabilecekmiş", "yapabilecekmişim", "yapabilecekmişiz",
            "yapamayacaktı", "yapamayacaktım", "yapamayacaktın", "yapamayacaktık", "yapamayacaktınız",
            "yapamayacakmış", "yapamayacakmışım", "yapamayacakmışız",
            "yapabilirdi", "yapabilirdim", "yapabilirdin", "yapabilirdik", "yapabilirdiniz", "yapabilirdiler",
            "yapamazdı", "yapamazdım", "yapamazdın", "yapamazdık", "yapamazdınız", "yapamazdılar",
            "yapabilmeliydi", "yapabilmeliydim", "yapabilmeliydik",
            "yapamamalıydı", "yapamamalıydım", "yapamamalıydık",
        ]
    }

    print("=" * 80)
    print("PURE VERB-ONLY PARADIGM MATRIX AUDIT (No Noun Crutches from tr.dic)")
    print("=" * 80)

    total_tested = 0
    total_rejected = 0

    for name, word_list in paradigms.items():
        p = subprocess.run(
            [HUNSPELL_BIN, "-d", dict_prefix, "-l"],
            input="\n".join(word_list) + "\n",
            text=True,
            capture_output=True,
            encoding="utf-8"
        )
        rejected = [line.strip() for line in p.stdout.splitlines() if line.strip()]
        accepted_cnt = len(word_list) - len(rejected)
        total_tested += len(word_list)
        total_rejected += len(rejected)
        status = "PASS" if not rejected else "GAP!"
        print(f"\n[{status}] {name} ({accepted_cnt}/{len(word_list)} accepted)")
        if rejected:
            print(f"   Rejected ({len(rejected)}): {rejected}")

    print("\n" + "=" * 80)
    print(f"OVERALL PURE VERB MATRIX: {total_tested - total_rejected}/{total_tested} accepted | {total_rejected} GAPS FOUND")
    print("=" * 80)

    shutil.rmtree(tmp_dir, ignore_errors=True)


def run_pure_noun_matrix():
    rep_nouns = [
        "ev", "kitap", "kitab", "ağaç", "ağac", "burun", "burn",
        "su", "suyum", "suyun", "suyu", "suyumuz", "suyunuz",
        "araba", "kedi", "kutu", "ütü", "göz", "kol", "güzel", "büyük"
    ]
    noun_flags = get_verb_flags_from_dic(rep_nouns)

    tmp_dir = ROOT_DIR / "reports" / "tmp_pure_noun"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT_DIR / "tr.aff", tmp_dir / "pure.aff")

    with open(tmp_dir / "pure.dic", "w", encoding="utf-8") as f:
        f.write(f"{len(noun_flags)}\n")
        for w, fl in sorted(noun_flags.items()):
            f.write(f"{w}/{fl}\n")

    dict_prefix = str(tmp_dir / "pure")

    noun_paradigms = {
        "N1. Possessive + Case Chains": [
            "evimde", "evimden", "evimle", "evlerimde", "evlerimizden", "evlerimizle",
            "kitabımda", "kitabımdan", "kitabımla", "kitaplarımdan", "kitaplarımızdan",
            "burnumda", "burnumdan", "burnumla", "burunlarımızdan",
            "suyum", "suyun", "suyu", "suyumuz", "suyunuz", "suları",
            "suyumda", "suyumdan", "suyunda", "suyundan", "suyumuzdan", "suyunuzdan", "sularından",
            "arabamda", "arabamdan", "arabamızdan", "arabalarımızdan",
        ],
        "N2. Relativizer (-ki / -daki / -deki) + Plural & Cases": [
            "evdeki", "evdekiler", "evdekileri", "evdekilere", "evdekilerde", "evdekilerden", "evdekilerin", "evdekilerle",
            "evdekini", "evdekine", "evdekinde", "evdekinden", "evdekinin", "evdekiyle",
            "kitaptaki", "kitaptakiler", "kitaptakileri", "kitaptakilerden", "kitaptakilerin",
            "kitaptakini", "kitaptakine", "kitaptakinden", "kitaptakinin",
            "evimdeki", "evimdekiler", "evimdekileri", "evimdekilerden",
            "evimizdeki", "evimizdekiler", "evimizdekilerden",
            "evlerindeki", "evlerindekiler", "evlerindekilerden",
            "kitabımdaki", "kitabımdakiler", "kitabımdakilerden",
            "arabamdaki", "arabamdakiler", "arabamızdaki",
        ],
        "N3. Locative & Nominal Predication / Copula": [
            "evdeyim", "evdesin", "evdedir", "evdeyiz", "evdesiniz", "evdeler", "evdedirler",
            "evdeydim", "evdeydin", "evdeydi", "evdeydik", "evdeydiniz", "evdeydiler",
            "evdeymişim", "evdeymişsin", "evdeymiş", "evdeymişiz", "evdeymişsiniz", "evdeymişler",
            "evdeysem", "evdeysen", "evdeyse", "evdeysek", "evdeyseniz", "evdeyseler",
            "evdeyseydi", "evdeyseydim", "evdeyseydik",
            "evdeyken", "kitaptaydı", "kitaptayken", "arabadaydı", "arabadayken",
            "güzelim", "güzelsin", "güzeldir", "güzeliz", "güzelsiniz", "güzeller",
            "güzeldim", "güzeldin", "güzeldi", "güzeldik", "güzeldiniz", "güzeldiler",
            "güzelmişim", "güzelmişsin", "güzelmiş", "güzelmişiz", "güzelmişsiniz",
            "güzelse", "güzelsem", "güzelsen", "güzelsek", "güzelseniz", "güzelseler",
            "güzelseydi", "güzelseydim", "güzelseydik", "güzelken",
        ],
        "N4. Productive Derivations (-lık, -lı, -sız, -cı, -ca) + Inflections": [
            "güzellik", "güzelliği", "güzelliğe", "güzellikte", "güzellikten", "güzelliğin", "güzelliğim", "güzelliğimiz",
            "büyüklük", "büyüklüğü", "büyüklüğe", "büyüklükten", "büyüklüğün",
            "kitaplık", "kitaplığı", "kitaplığa", "kitaplıkta", "kitaplıktan",
            "evli", "evliler", "evlilerin", "evlilik", "evlilikten", "evliliğin",
            "evsiz", "evsizler", "evsizlerin", "evsizlik", "evsizlikten", "evsizliğin", "evsizliği",
            "kitaplı", "kitapsız", "kitapsızlık", "kitapsızlıktan", "kitapsızlığın",
            "kitapçı", "kitapçılık", "kitapçılıktan", "kitapçılığın", "kitapçılığı",
            "arabalı", "arabasız", "arabasızlık", "arabasızlıktan",
            "kutusuz", "kutusuzluk", "kutusuzluktan", "ütüsüz", "ütüsüzlük", "ütüsüzlükten",
            "güzelce", "büyükçe",
        ]
    }

    print("\n" + "=" * 80)
    print("PURE NOUN/ADJECTIVE PARADIGM MATRIX AUDIT (No Derived Crutches from tr.dic)")
    print("=" * 80)

    total_tested = 0
    total_rejected = 0

    for name, word_list in noun_paradigms.items():
        p = subprocess.run(
            [HUNSPELL_BIN, "-d", dict_prefix, "-l"],
            input="\n".join(word_list) + "\n",
            text=True,
            capture_output=True,
            encoding="utf-8"
        )
        rejected = [line.strip() for line in p.stdout.splitlines() if line.strip()]
        accepted_cnt = len(word_list) - len(rejected)
        total_tested += len(word_list)
        total_rejected += len(rejected)
        status = "PASS" if not rejected else "GAP!"
        print(f"\n[{status}] {name} ({accepted_cnt}/{len(word_list)} accepted)")
        if rejected:
            print(f"   Rejected ({len(rejected)}): {rejected}")

    print("\n" + "=" * 80)
    print(f"OVERALL PURE NOUN MATRIX: {total_tested - total_rejected}/{total_tested} accepted | {total_rejected} GAPS FOUND")
    print("=" * 80)

    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_pure_verb_matrix()
    run_pure_noun_matrix()

