"""
Audit script for Turkish Open vs. Closed Compounds, Auxiliary Verbs (Etmek/Olmak),
SOMBAHÇEMİ Conjunctions, and TDK vs. Dil Derneği Profile Separation.

Verifies:
1. Consensus Open Compounds & Auxiliary Verb Typos:
   - 100% rejected across ALL 3 profiles (universal, tdk, dd)
   - 100% Top-1 suggestion accuracy across ALL 3 profiles
2. TDK-Open vs. Dil Derneği-Closed Compounds:
   - In [tdk] profile: 100% rejected as joined & 100% Top-1 suggestion for the spaced TDK form
   - In [dd] and [universal] profiles: 100% accepted as valid Dil Derneği closed compounds
3. Mandatory Closed Compounds (Joined Auxiliary Verbs, SOMBAHÇEMİ, Indefinites, -altı/-üstü/-evi):
   - 100% accepted across ALL 3 profiles (universal, tdk, dd)
"""

import subprocess
import sys

PROFILES = {
    "universal": "dist/turkspell-universal/tr",
    "tdk": "dist/turkspell-tdk/tr",
    "dd": "dist/turkspell-dd/tr",
}

# 1. Consensus invalid joined forms (open compounds & vowel-drop/gemination typos)
# Must be REJECTED and suggest the expected target at Top-1 in ALL 3 profiles.
CONSENSUS_INVALID_PAIRS = [
    # Auxiliary verbs (etmek / olmak) - infinitive, past, progressive, future, passive, nominal, negative
    ("farketmek", "fark etmek"),
    ("farkettim", "fark ettim"),
    ("farketti", "fark etti"),
    ("farkettik", "fark ettik"),
    ("farkettiler", "fark ettiler"),
    ("farketmedi", "fark etmedi"),
    ("farketmedim", "fark etmedim"),
    ("farkediyor", "fark ediyor"),
    ("farkediyorum", "fark ediyorum"),
    ("farkediyoruz", "fark ediyoruz"),
    ("farkedecek", "fark edecek"),
    ("farkeder", "fark eder"),
    ("farkedildi", "fark edildi"),
    ("farkedilmek", "fark edilmek"),
    ("farketme", "fark etme"),
    ("terketmek", "terk etmek"),
    ("terketti", "terk etti"),
    ("terkettiler", "terk ettiler"),
    ("terketmedi", "terk etmedi"),
    ("terkediyor", "terk ediyor"),
    ("terkedecek", "terk edecek"),
    ("terkedildi", "terk edildi"),
    ("arzederim", "arz ederim"),
    ("arzediyorum", "arz ediyorum"),
    ("arzetti", "arz etti"),
    ("arzedildi", "arz edildi"),
    ("arzetmek", "arz etmek"),
    ("haketmek", "hak etmek"),
    ("haketti", "hak etti"),
    ("hakettik", "hak ettik"),
    ("haketmedi", "hak etmedi"),
    ("hakediyor", "hak ediyor"),
    ("hakediyorum", "hak ediyorum"),
    ("hakedecek", "hak edecek"),
    ("yardımetmek", "yardım etmek"),
    ("yardımetti", "yardım etti"),
    ("yardımediyor", "yardım ediyor"),
    ("yardımedecek", "yardım edecek"),
    ("teşekküretmek", "teşekkür etmek"),
    ("teşekkürederim", "teşekkür ederim"),
    ("teşekkürediyorum", "teşekkür ediyorum"),
    ("teşekkürediyoruz", "teşekkür ediyoruz"),
    ("teşekküretti", "teşekkür etti"),
    ("kabuletmek", "kabul etmek"),
    ("kabuletti", "kabul etti"),
    ("kabuletmedi", "kabul etmedi"),
    ("kabulediyor", "kabul ediyor"),
    ("kabulediyorum", "kabul ediyorum"),
    ("kabuledildi", "kabul edildi"),
    ("kabuledecek", "kabul edecek"),
    ("ricaetmek", "rica etmek"),
    ("ricaederim", "rica ederim"),
    ("ricaediyorum", "rica ediyorum"),
    ("ricaetti", "rica etti"),
    ("dikkatetmek", "dikkat etmek"),
    ("dikkatetti", "dikkat etti"),
    ("dikkatediyor", "dikkat ediyor"),
    ("meraketmek", "merak etmek"),
    ("meraketti", "merak etti"),
    ("merakediyorum", "merak ediyorum"),
    ("merakediyor", "merak ediyor"),
    ("meraketme", "merak etme"),
    ("devametmek", "devam etmek"),
    ("devametti", "devam etti"),
    ("devamediyor", "devam ediyor"),
    ("devamedecek", "devam edecek"),
    ("takipetmek", "takip etmek"),
    ("takipetti", "takip etti"),
    ("takipediyor", "takip ediyor"),
    ("takipedildi", "takip edildi"),
    ("ifadeetmek", "ifade etmek"),
    ("ifadeetti", "ifade etti"),
    ("ifadeediyor", "ifade ediyor"),
    ("ifadeedildi", "ifade edildi"),
    ("iknaetmek", "ikna etmek"),
    ("iknaetti", "ikna etti"),
    ("iknaedildi", "ikna edildi"),
    ("iptaletmek", "iptal etmek"),
    ("iptaletti", "iptal etti"),
    ("iptaledildi", "iptal edildi"),
    ("kontroletmek", "kontrol etmek"),
    ("kontroletti", "kontrol etti"),
    ("kontroledildi", "kontrol edildi"),
    ("ziyaretetmek", "ziyaret etmek"),
    ("ziyaretetti", "ziyaret etti"),
    ("ziyaretedildi", "ziyaret edildi"),
    ("şikayetetmek", "şikâyet etmek"),
    ("şikâyetetmek", "şikâyet etmek"),
    ("şikâyetetti", "şikâyet etti"),
    ("tahminetmek", "tahmin etmek"),
    ("tahminetti", "tahmin etti"),
    ("tahminediyorum", "tahmin ediyorum"),
    ("tercihetmek", "tercih etmek"),
    ("tercihetti", "tercih etti"),
    ("tercihediyor", "tercih ediyor"),
    ("tercihedildi", "tercih edildi"),
    ("teklifetmek", "teklif etmek"),
    ("teklifetti", "teklif etti"),
    ("teklifedildi", "teklif edildi"),
    ("teslimetmek", "teslim etmek"),
    ("teslimetti", "teslim etti"),
    ("teslimedildi", "teslim edildi"),
    ("tespitetmek", "tespit etmek"),
    ("tespitetti", "tespit etti"),
    ("tespitedildi", "tespit edildi"),
    ("tavsiyeetmek", "tavsiye etmek"),
    ("tavsiyeederim", "tavsiye ederim"),
    ("tavsiyeetti", "tavsiye etti"),
    ("tebriketmek", "tebrik etmek"),
    ("tebrikederim", "tebrik ederim"),
    ("tebriketti", "tebrik etti"),
    ("tehditetmek", "tehdit etmek"),
    ("tehditetti", "tehdit etti"),
    ("tehditedildi", "tehdit edildi"),
    ("tenkitetmek", "tenkit etmek"),
    ("tenkitetti", "tenkit etti"),
    ("temsiletmek", "temsil etmek"),
    ("temsiletti", "temsil etti"),
    ("temsilediyor", "temsil ediyor"),
    ("teşviketmek", "teşvik etmek"),
    ("teşviketti", "teşvik etti"),
    ("tahsisetmek", "tahsis etmek"),
    ("tahsisetti", "tahsis etti"),
    ("tahsisedildi", "tahsis edildi"),
    ("takdiretmek", "takdir etmek"),
    ("takdiretti", "takdir etti"),
    ("tatminetmek", "tatmin etmek"),
    ("tatminetti", "tatmin etti"),
    ("tatminedici", "tatmin edici"),
    ("teminetmek", "temin etmek"),
    ("teminetti", "temin etti"),
    ("teminedildi", "temin edildi"),
    ("tereddütetmek", "tereddüt etmek"),
    ("tereddütetti", "tereddüt etti"),
    ("ispatetmek", "ispat etmek"),
    ("ispatetti", "ispat etti"),
    ("ispatedildi", "ispat edildi"),
    ("işgaletmek", "işgal etmek"),
    ("işgaletti", "işgal etti"),
    ("işgaledildi", "işgal edildi"),
    ("ihlaletmek", "ihlal etmek"),
    ("ihlaletti", "ihlal etti"),
    ("ihlaledildi", "ihlal edildi"),
    ("ihmaletmek", "ihmal etmek"),
    ("ihmaletti", "ihmal etti"),
    ("ihmaledildi", "ihmal edildi"),
    ("intiharetmek", "intihar etmek"),
    ("intiharetti", "intihar etti"),
    ("istifaetmek", "istifa etmek"),
    ("istifaetti", "istifa etti"),
    ("itirafetmek", "itiraf etmek"),
    ("itirafetti", "itiraf etti"),
    ("itirafedildi", "itiraf edildi"),
    ("itirazetmek", "itiraz etmek"),
    ("itirazetti", "itiraz etti"),
    ("ikametmek", "ikamet etmek"),
    ("ikametetti", "ikamet etti"),
    ("eldeetmek", "elde etmek"),
    ("eldeetti", "elde etti"),
    ("eldeedildi", "elde edildi"),
    ("eldeediyor", "elde ediyor"),
    ("yokolmak", "yok olmak"),
    ("yokoldu", "yok oldu"),
    ("yokoluyor", "yok oluyor"),
    ("yokolacak", "yok olacak"),
    ("varolmak", "var olmak"),
    ("varoldu", "var oldu"),
    ("varoluyor", "var oluyor"),
    ("varolacak", "var olacak"),
    ("sağol", "sağ ol"),
    ("sağolun", "sağ olun"),
    ("sağolsun", "sağ olsun"),

    # Joined auxiliary verbs where vowel drop or gemination was missed
    ("kayıpetmek", "kaybetmek"),
    ("kayıpetti", "kaybetti"),
    ("kayıpediyor", "kaybediyor"),
    ("kayıtetmek", "kaydetmek"),
    ("kayıtetti", "kaydetti"),
    ("sabıretmek", "sabretmek"),
    ("sabıretti", "sabretti"),
    ("şüküretmek", "şükretmek"),
    ("şüküretti", "şükretti"),
    ("seyiretmek", "seyretmek"),
    ("seyiretti", "seyretti"),
    ("emiretmek", "emretmek"),
    ("emiretti", "emretti"),
    ("keşifetmek", "keşfetmek"),
    ("keşifetti", "keşfetti"),
    ("redetmek", "reddetmek"),
    ("redetti", "reddetti"),
    ("rededildi", "reddedildi"),
    ("zanetmek", "zannetmek"),
    ("zanetti", "zannetti"),
    ("haletmek", "halletmek"),
    ("haletti", "halletti"),
    ("haledildi", "halledildi"),
    ("hisetmek", "hissetmek"),
    ("hisetti", "hissetti"),
    ("afetmek", "affetmek"),
    ("afedildi", "affedildi"),
    ("afediyor", "affediyor"),

    # Open determiners, pronouns, time expressions, food terms, and conjunctions (consensus in TDK & DD)
    ("birşey", "bir şey"),
    ("birşeyler", "bir şeyler"),
    ("birşeyi", "bir şeyi"),
    ("birşeyin", "bir şeyin"),
    ("birşeyden", "bir şeyden"),
    ("birşeye", "bir şeye"),
    ("herşey", "her şey"),
    ("herşeyi", "her şeyi"),
    ("herşeyin", "her şeyin"),
    ("herşeyden", "her şeyden"),
    ("herşeye", "her şeye"),
    ("herşeyde", "her şeyde"),
    ("hiçbirşey", "hiçbir şey"),
    ("hiçbirşeyi", "hiçbir şeyi"),
    ("hiçbirşeyin", "hiçbir şeyin"),
    ("hiçbirşeyden", "hiçbir şeyden"),
    ("hiçkimse", "hiç kimse"),
    ("hiçkimsenin", "hiç kimsenin"),
    ("hiçkimseye", "hiç kimseye"),
    ("hiçkimseden", "hiç kimseden"),
    ("herbir", "her bir"),
    ("herbiri", "her biri"),
    ("herbirimiz", "her birimiz"),
    ("herbirinin", "her birinin"),
    ("herbirine", "her birine"),
    ("hergün", "her gün"),
    ("hergünkü", "her günkü"),
    ("herzaman", "her zaman"),
    ("herzamanki", "her zamanki"),
    ("heryer", "her yer"),
    ("heryerde", "her yerde"),
    ("heryerden", "her yerden"),
    ("heryere", "her yere"),
    ("heran", "her an"),
    ("biran", "bir an"),
    ("biranda", "bir anda"),
    ("şuan", "şu an"),
    ("şuanda", "şu anda"),
    ("şuanki", "şu anki"),
    ("pekçok", "pek çok"),
    ("haftasonu", "hafta sonu"),
    ("haftasonunda", "hafta sonunda"),
    ("haftasonları", "hafta sonları"),
    ("haftasonuna", "hafta sonuna"),
    ("haftasonundan", "hafta sonundan"),
    ("haftaiçi", "hafta içi"),
    ("haftaiçinde", "hafta içinde"),
    ("doğumgünü", "doğum günü"),
    ("doğumgününde", "doğum gününde"),
    ("doğumgünüm", "doğum günüm"),
    ("doğumgünün", "doğum günün"),
    ("yeşilzeytin", "yeşil zeytin"),
    ("siyahzeytin", "siyah zeytin"),
    ("kuruüzüm", "kuru üzüm"),
    ("kurufasulye", "kuru fasulye"),
    ("yeşilsoğan", "yeşil soğan"),
    ("ardarda", "art arda"),
    ("artarda", "art arda"),
    ("yanyana", "yan yana"),
    ("içiçe", "iç içe"),
    ("üstütüste", "üst üste"),
    ("üstüste", "üst üste"),
    ("peşpeşe", "peş peşe"),
    ("elele", "el ele"),
    ("gözgöze", "göz göze"),
    ("başbaşa", "baş başa"),
    ("yüzyüze", "yüz yüze"),
    ("dizdize", "diz dize"),
    ("omuzomuza", "omuz omuza"),
    ("uçuca", "uç uca"),
    ("baştanbaşa", "baştan başa"),
    ("gündengüne", "günden güne"),
    ("yıldanyıla", "yıldan yıla"),
    ("yada", "ya da"),
    ("hemde", "hem de"),
    ("bencede", "bence de"),
    ("sencede", "sence de"),
    ("bizcede", "bizce de"),
    ("sizcede", "sizce de"),
    ("tabiki", "tabii ki"),
    ("tabiiki", "tabii ki"),
]

# 2. TDK-Open vs. Dil Derneği-Closed Compounds
# In [tdk] profile: must be REJECTED and suggest the spaced form at Top-1.
# In [dd] and [universal] profiles: must be ACCEPTED as valid Dil Derneği closed compounds.
TDK_OPEN_DD_CLOSED_PAIRS = [
    ("doğalgaz", "doğal gaz"),
    ("doğalgazda", "doğal gazda"),
    ("doğalgazla", "doğal gazla"),
    ("doğalgaza", "doğal gaza"),
    ("doğalgazdan", "doğal gazdan"),
    ("doğalgazın", "doğal gazın"),
    ("önyargı", "ön yargı"),
    ("önyargılı", "ön yargılı"),
    ("önyargısız", "ön yargısız"),
    ("önyargının", "ön yargının"),
    ("önyargılar", "ön yargılar"),
    ("önyargılardan", "ön yargılardan"),
    ("önsöz", "ön söz"),
    ("önsözde", "ön sözde"),
    ("önsözü", "ön sözü"),
    ("önsözünde", "ön sözünde"),
    ("altyazı", "alt yazı"),
    ("altyazılı", "alt yazılı"),
    ("altyazısız", "alt yazısız"),
    ("bilimkurgu", "bilim kurgu"),
    ("anadil", "ana dil"),
    ("anadili", "ana dili"),
    ("anadilinde", "ana dilinde"),
    ("anadiline", "ana diline"),
    ("işbirliği", "iş birliği"),
    ("işbirliğinde", "iş birliğinde"),
    ("işbirliğine", "iş birliğine"),
    ("işbirliğiyle", "iş birliğiyle"),
    ("işgücü", "iş gücü"),
    ("işbölümü", "iş bölümü"),
    ("özgüven", "öz güven"),
    ("özgüvenli", "öz güvenli"),
    ("özgüvensiz", "öz güvensiz"),
    ("özgüveni", "öz güveni"),
    ("kuruyemiş", "kuru yemiş"),
    ("kuruyemişçi", "kuru yemişçi"),
    ("çiğköfte", "çiğ köfte"),
    ("adaçayı", "ada çayı"),
    ("acıbadem", "acı badem"),
    ("dilbilgisi", "dil bilgisi"),
    ("dilbilim", "dil bilimi"),
    ("dilbilimci", "dil bilimci"),
    ("dilbilimsel", "dil bilimsel"),
    ("sesbilim", "ses bilimi"),
    ("sesbilimci", "ses bilimci"),
    ("toplumbilim", "toplum bilimi"),
    ("toplumbilimci", "toplum bilimci"),
    ("ruhbilim", "ruh bilimi"),
    ("ruhbilimci", "ruh bilimci"),
    ("yerbilim", "yer bilimi"),
    ("gökbilim", "gök bilimi"),
    ("ilkönce", "ilk önce"),
    ("sıradışı", "sıra dışı"),
    ("olağandışı", "olağan dışı"),
    ("yasadışı", "yasa dışı"),
    ("çağdışı", "çağ dışı"),
    ("dindışı", "din dışı"),
    ("ahlakdışı", "ahlak dışı"),
    ("kanundışı", "kanun dışı"),
    ("yurtdışı", "yurt dışı"),
    ("yurtdışında", "yurt dışında"),
    ("yurtdışından", "yurt dışından"),
    ("yurtdışına", "yurt dışına"),
    ("yurtiçi", "yurt içi"),
    ("yurtiçinde", "yurt içinde"),
]

# 3. Mandatory Closed Compounds (Valid in ALL 3 profiles: universal, tdk, dd)
MANDATORY_CLOSED_VALID = [
    # Joined auxiliary verbs with vowel drop or consonant gemination
    "kaybetmek", "kaybetti", "kaybediyor", "kaybedecek", "kaybedildi",
    "kaydetmek", "kaydetti", "kaydediyor", "kaydedecek", "kaydedildi",
    "sabretmek", "sabretti", "sabrediyor", "sabredecek",
    "şükretmek", "şükretti", "şükrediyor",
    "seyretmek", "seyretti", "seyrediyor", "seyredecek",
    "emretmek", "emretti", "emrediyor",
    "keşfetmek", "keşfetti", "keşfediyor", "keşfedildi",
    "devretmek", "devretti", "devrediyor", "devredildi",
    "affetmek", "affetti", "affediyor", "affedildi",
    "hissetmek", "hissetti", "hissediyor", "hissedildi",
    "reddetmek", "reddetti", "reddediyor", "reddedildi",
    "zannetmek", "zannetti", "zannediyor", "zannediyorum",
    "halletmek", "halletti", "hallediyor", "halledildi",
    # Fused compound verbs
    "vazgeçmek", "vazgeçti", "vazgeçiyor",
    "varsaymak", "varsaydı", "varsayıyor",
    "öngörmek", "öngördü", "öngörüyor", "öngörüldü",
    "başvurmak", "başvurdu", "başvuruyor",
    "elvermek", "elverdi", "elveriyor",
    "alıkoymak", "alıkoydu", "alıkoyuyor",
    # SOMBAHÇEMİ conjunctions
    "sanki", "oysaki", "mademki", "belki", "hâlbuki", "çünkü", "meğerki", "illaki",
    # Indefinite pronouns & determiners
    "biraz", "birazdan", "birçok", "birçoğu", "birkaç", "birkaçı",
    "birtakım", "herhangi", "hiçbir", "hiçbiri", "hiçbirimiz", "hiçbiriniz",
    # -altı, -üstü, -üzeri, -başı, -evi, -hane, -name, -zede compounds
    "bilinçaltı", "bilinçaltında", "denizaltı", "gözaltı", "gözaltına", "ayakaltı",
    "ayaküstü", "suçüstü", "akşamüstü", "öğleüzeri", "olağanüstü", "gerçeküstü",
    "gökyüzü", "gökyüzünde", "yeryüzü", "yeryüzünde",
    "başbakan", "başsavcı", "başhekim", "başrol", "başyapıt", "başvuru",
    "aşevi", "yayınevi", "öğretmenevi", "huzurevi", "polisevi", "gözlemevi",
    "dershane", "kütüphane", "hastane", "pastane", "postane", "eczane",
    "siyasetname", "seyahatname", "depremzede", "kazazede", "afetzede",
    "insanoğlu", "eloğlu", "kızılötesi", "morötesi",
]


def run_hunspell_batch(dic_base: str, words: list[str]) -> dict[str, tuple[bool, list[str]]]:
    p = subprocess.run(
        ["hunspell", "-d", dic_base, "-a"],
        input="\n".join(words) + "\n",
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    out_lines = [
        line.strip()
        for line in p.stdout.splitlines()
        if line.strip() and not line.startswith("@(#)")
    ]
    results = {}
    for w, line in zip(words, out_lines):
        if line[0] in ("*", "+", "-"):
            results[w] = (True, [])
        elif line.startswith("&"):
            sugs = [s.strip() for s in line.split(":", 1)[1].split(",")]
            results[w] = (False, sugs)
        else:
            results[w] = (False, [])
    return results


def main() -> int:
    all_passed = True

    print("=" * 72)
    print("TURKSPELL COMPOUNDS, AUXILIARY VERBS & PROFILE SEPARATION AUDIT")
    print("=" * 72)

    for prof_name, dic_base in PROFILES.items():
        print(f"\n--- Profile: [{prof_name.upper()}] ({dic_base}) ---")

        # 1. Consensus Invalid Pairs
        inv_words = [w for w, _ in CONSENSUS_INVALID_PAIRS]
        inv_res = run_hunspell_batch(dic_base, inv_words)
        leaks = []
        misses = []
        for w, exp in CONSENSUS_INVALID_PAIRS:
            accepted, sugs = inv_res[w]
            if accepted:
                leaks.append((w, exp))
            elif not sugs or sugs[0] != exp:
                misses.append((w, exp, sugs[:3]))

        print(
            f"  [1] Consensus Open / Aux Typos : "
            f"Rejected {len(CONSENSUS_INVALID_PAIRS) - len(leaks)}/{len(CONSENSUS_INVALID_PAIRS)} | "
            f"Top-1 {len(CONSENSUS_INVALID_PAIRS) - len(leaks) - len(misses)}/{len(CONSENSUS_INVALID_PAIRS)}"
        )
        if leaks:
            all_passed = False
            print(f"      LEAKS: {leaks}")
        if misses:
            all_passed = False
            for w, exp, got in misses:
                print(f"      MISS : {w} -> exp '{exp}', got {got}")

        # 2. TDK-Open vs DD-Closed
        tdk_dd_words = [w for w, _ in TDK_OPEN_DD_CLOSED_PAIRS]
        tdk_dd_res = run_hunspell_batch(dic_base, tdk_dd_words)
        if prof_name == "tdk":
            t_leaks = []
            t_misses = []
            for w, exp in TDK_OPEN_DD_CLOSED_PAIRS:
                accepted, sugs = tdk_dd_res[w]
                if accepted:
                    t_leaks.append((w, exp))
                elif not sugs or sugs[0] != exp:
                    t_misses.append((w, exp, sugs[:3]))
            print(
                f"  [2] TDK-Open vs DD-Closed      : "
                f"Rejected {len(TDK_OPEN_DD_CLOSED_PAIRS) - len(t_leaks)}/{len(TDK_OPEN_DD_CLOSED_PAIRS)} | "
                f"Top-1 {len(TDK_OPEN_DD_CLOSED_PAIRS) - len(t_leaks) - len(t_misses)}/{len(TDK_OPEN_DD_CLOSED_PAIRS)}"
            )
            if t_leaks:
                all_passed = False
                print(f"      TDK LEAKS: {t_leaks}")
            if t_misses:
                all_passed = False
                for w, exp, got in t_misses:
                    print(f"      TDK MISS : {w} -> exp '{exp}', got {got}")
        else:
            dd_rejects = [w for w, _ in TDK_OPEN_DD_CLOSED_PAIRS if not tdk_dd_res[w][0]]
            print(
                f"  [2] DD-Closed Acceptance       : "
                f"Accepted {len(TDK_OPEN_DD_CLOSED_PAIRS) - len(dd_rejects)}/{len(TDK_OPEN_DD_CLOSED_PAIRS)}"
            )
            if dd_rejects:
                all_passed = False
                print(f"      DD FALSE REJECTS: {dd_rejects}")

        # 3. Mandatory Closed Compounds
        closed_res = run_hunspell_batch(dic_base, MANDATORY_CLOSED_VALID)
        closed_rejects = [w for w in MANDATORY_CLOSED_VALID if not closed_res[w][0]]
        print(
            f"  [3] Mandatory Closed Compounds : "
            f"Accepted {len(MANDATORY_CLOSED_VALID) - len(closed_rejects)}/{len(MANDATORY_CLOSED_VALID)}"
        )
        if closed_rejects:
            all_passed = False
            print(f"      CLOSED FALSE REJECTS: {closed_rejects}")

    print("\n" + "=" * 72)
    if all_passed:
        print("ALL COMPOUND & PROFILE SEPARATION CHECKS PASSED (100% ACCURACY)!")
        return 0
    else:
        print("SOME CHECKS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
