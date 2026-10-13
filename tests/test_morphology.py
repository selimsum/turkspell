# -*- coding: utf-8 -*-
"""
Turkspell Core Morphology & Regression Test Suite
Validates positive acceptance of legitimate Turkish morphology and
negative rejection of illegal/overgenerated forms across Hunspell profiles.
"""

import os
import sys
import subprocess
import shutil
import unittest
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = os.environ.get("TURKSPELL_DICT", str(ROOT_DIR / "tr"))

winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
HUNSPELL_BIN = shutil.which("hunspell") or "hunspell"

def check_words(words: list[str], dict_path: str = DICT_PATH) -> tuple[list[str], list[str]]:
    """Runs hunspell -l and returns (accepted_words, rejected_words)."""
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    flagged = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    accepted = [w for w in words if w not in flagged]
    rejected = [w for w in words if w in flagged]
    return accepted, rejected


def is_tdk_profile(dict_path: str = None) -> bool:
    target = dict_path or os.environ.get("TURKSPELL_DICT", DICT_PATH)
    dic_path = target if target.endswith(".dic") else (target + ".dic")
    if os.path.exists(dic_path):
        with open(dic_path, "r", encoding="utf-8") as f:
            return not any(line.split('/')[0] == "zanaat" for line in f)
    return False


class TestCopularAndPredicates(unittest.TestCase):
    """Verifies copular/predicate inflections for değil and ait."""

    def test_degil_inflections(self):
        words = [
            "değil", "değildir", "değilim", "değilsin", "değiliz",
            "değilsiniz", "değiller", "değildi", "değilmiş", "değilse", "değilken"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing değil forms: {rejected}")

    def test_ait_inflections(self):
        words = ["ait", "aittir", "aitti", "aitmiş", "aitler", "aitse", "aittirler"]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing ait forms: {rejected}")

    def test_idi_imis_inflections(self):
        words = [
            "idi", "idim", "idin", "idik", "idiniz", "idiler", "idiyse",
            "imiş", "imişim", "imişsin", "imişiz", "imişsiniz", "imişler", "imişse", "imiştir"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing idi/imiş forms: {rejected}")


class TestPalatalL(unittest.TestCase):
    """Verifies thin /l/ loanwords take front-rounded vowel suffixes (-ü, -ün, -e, -süz)."""

    def test_palatal_l_positive(self):
        words = [
            "alkol", "alkolü", "alkolün", "alkole", "alkoller", "alkollü", "alkolsüz",
            "ampul", "ampulü", "ampulün", "ampule", "ampuller", "ampulsüz",
            "kontrol", "kontrolün", "kontrolünde", "kontrolünden", "kontrolüne",
            "kontrolünüz", "kontrollü", "kontrolsüz",
            "otokontrol", "otokontrolü",
            "rol", "rolün", "rolünde", "rolünden", "rolüne", "roller",
            "başrol", "başrolü", "başrolünde", "başroller",
            "sembol", "sembolü", "sembolün", "sembolüne", "semboller",
            "petrol", "petrolü", "petrolün", "petrole", "petroller",
            "protokol", "protokolü", "protokolün", "protokolüne", "protokoller",
            "kolesterol", "kolesterolü", "kolesterolün",
            "metropol", "metropolün", "metropoller",
            "usul", "usulü", "usulüne", "usuller",
            "mahsul", "mahsulü", "mahsulün", "mahsuller",
            "alveol", "alveolün", "alveole", "alveoller"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing palatal /l/ forms: {rejected}")

    def test_palatal_l_negative_rejection(self):
        """Illegal back-vowel forms must be rejected as typos."""
        wrong_words = [
            "alkolu", "alkolun", "alkolsuz", "alkollar",
            "ampulsuz", "ampullar",
            "kontrolsuz", "kontrolun",
            "rolsuz", "sembolsuz", "petrolsuz"
        ]
        accepted, rejected = check_words(wrong_words)
        self.assertEqual(accepted, [], f"Illegal back-vowel forms leaked: {accepted}")


class TestNonSofteningLoanwords(unittest.TestCase):
    """Verifies loanwords like felaket and stok do NOT voice (felaketi not felakedi, stoku not stoğu)."""

    def test_felaket_positive(self):
        words = [
            "felaket", "felaketi", "felakete", "felaketin",
            "felaketinde", "felaketinden", "felaketini", "felaketinin"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing felaket forms: {rejected}")

    def test_felaket_negative_rejection(self):
        wrong_words = ["felakedi", "felakede", "felakedin", "felakedinde"]
        accepted, rejected = check_words(wrong_words)
        self.assertEqual(accepted, [], f"Voiced felaket forms leaked: {accepted}")

    def test_zanaat_positive(self):
        if is_tdk_profile():
            self.skipTest("zanaat is unique to Dil Derneği (omitted in TDK profile)")
        words = [
            "zanaat", "zanaatı", "zanaata", "zanaatın", "zanaatında",
            "zanaatından", "zanaatını", "zanaatının", "zanaatıyla",
            "zanaatlar", "zanaatları", "zanaatlarında"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing zanaat forms: {rejected}")

    def test_zanaat_negative_rejection(self):
        wrong_words = ["zanaate", "zanaati", "zanaatler", "zanaatiyle", "zanaadı"]
        accepted, rejected = check_words(wrong_words)
        self.assertEqual(accepted, [], f"Illegal front-vowel/voiced zanaat forms leaked: {accepted}")

    def test_stok_positive(self):
        words = [
            "stok", "stoku", "stokun", "stokuna", "stokunun",
            "stokta", "stoktan", "stoklar", "stoksuz", "stoklu"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing stok forms: {rejected}")

    def test_stok_negative_rejection(self):
        wrong_words = ["stoğu", "stoğa", "stoğun", "stoğunda"]
        accepted, rejected = check_words(wrong_words)
        self.assertEqual(accepted, [], f"Voiced stok forms leaked: {accepted}")


class TestSecondVowelDrop(unittest.TestCase):
    """Verifies second-vowel drop roots like zehir and emir drop vowel when vowel-suffixed."""

    def test_zehir_and_emir(self):
        words = [
            "zehir", "zehri", "zehre", "zehrinde", "zehrine", "zehrini", "zehrinin",
            "zehirler", "zehirli", "zehirsiz",
            "emir", "emri", "emrimde", "emrin", "emrine", "emrini", "emrinin",
            "emirler", "emirde"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing vowel-drop forms: {rejected}")


class TestVirtualStems(unittest.TestCase):
    """Verifies NEEDAFFIX virtual stems for secondary pronominal 'n' and softened roots."""

    def test_pronominal_n_stems(self):
        words = [
            # art -> ard
            "art", "ardı", "ardına", "ardında", "ardından", "artlar", "artta",
            # icat -> icad
            "icat", "icadı", "icada", "icadın", "icadına", "icadında", "icadından", "icadını", "icatlar",
            # kap -> kab
            "kap", "kabı", "kaba", "kabın", "kabına", "kabında", "kabından", "kabını", "kaplar", "kapta",
            # kayıt -> kayd
            "kayıt", "kaydı", "kaydına", "kaydında", "kaydından", "kaydını", "kayıtlar", "kayıtta",
            # lop -> lob
            "lop", "lobu", "loba", "lobun", "lobuna", "lobunu", "lobunun", "loblar", "loblarda", "lobların",
            # ilmek -> ilmeğ
            "ilmek", "ilmeği", "ilmeğin", "ilmeğine", "ilmekler", "ilmekleri", "ilmeklerin", "ilmeklerden",
            # serçeparmak -> serçeparmağ
            "serçeparmak", "serçeparmağa", "serçeparmağı", "serçeparmağın", "serçeparmakta", "serçeparmaklar",
            # tat -> tad
            "tat", "tadı", "tada", "tadın", "tadım", "tadımız", "tadınız", "tadında", "tadından", "tadını", "tadına", "tadıyla", "tatlar", "tatsız", "tatlı",
            # uç -> uc
            "uç", "ucu", "uca", "ucun", "ucum", "ucumuz", "ucunuz", "ucunda", "ucundan", "ucunu", "ucuna", "ucuyla", "uçlar", "uçsuz", "uçlu",
            # cep -> ceb
            "cep", "cebi", "cebe", "cebin", "cebim", "cebimiz", "cebiniz", "cebinde", "cebinden", "cebini", "cebine", "cebiyle", "cepler", "cepsiz", "cepli",
            # gök -> göğ
            "gök", "göğü", "göğe", "göğün", "göğüm", "göğümüz", "göğünüz", "göğünde", "göğünden", "göğünü", "göğüne", "göğüyle", "gökler", "göksüz",
            # öç -> öc
            "öç", "öcüm", "öcü", "öce", "öcün", "öcümüz", "öcünüz", "öcünde", "öcünden", "öcünü", "öcüne", "öcüyle",
            # but -> bud
            "but", "budu", "buda", "budun", "budum", "budumuz", "budunda", "budunu", "butlar",
            # ut -> ud
            "ut", "udu", "uda", "udun", "udum", "udunda", "udunu", "utlar",
            # kulp -> kulb
            "kulp", "kulbu", "kulba", "kulbun", "kulbum", "kulbunda", "kulbunu", "kulplar",
            # ceht -> cehd
            "ceht", "cehdi", "cehde", "cehdin", "cehdim", "cehdinde", "cehdini"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing virtual stem inflections: {rejected}")


class TestAuthorityHeadwords(unittest.TestCase):
    """Verifies legitimate TDK and Dil Derneği words."""

    def test_compounds_and_derivatives(self):
        words = [
            "çıtır", "çerçöp", "çerçöpü", "tutamak", "tutamakları", "tutamaklarla",
            "sürücüsüz", "statüsüz", "kovuksuz", "temsilen", "sanayiinde",
            "buzdağı", "buzdağları", "buzdağında", "buzdağından", "buzdağının",
            "gökcismi", "gökcisimleri", "gökcisimlerinin", "gökcisminde",
            "fas", "go", "hut", "çad"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing authority words: {rejected}")

    def test_camii_and_compound_terms(self):
        words = [
            "cami", "camiler", "camisi", "camide", "camiden", "camiye",
            "camii", "camiine", "camiinde", "camiinden", "camiini", "camiinin"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing cami/camii forms: {rejected}")

    def test_teskilat_inflections(self):
        words = [
            "teşkilat", "teşkilatı", "teşkilatın", "teşkilata", "teşkilatta",
            "teşkilattan", "teşkilatlar", "teşkilatları", "teşkilatlarında"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Failing teşkilat forms: {rejected}")


class TestMandatoryCircumflex(unittest.TestCase):
    """Verifies that words with mandatory circumflex in TDK/DD reject unhatted clones."""

    def test_circumflex_enforcement(self):
        # Pairs: (valid_hatted, invalid_unhatted)
        pairs = [
            ("topyekûn", "topyekun"),
            ("âlemşümul", "alemşümul"),
            ("âlemşümullük", "alemşümullük"),
            ("Âdemci", "Ademci"),
            ("âdemci", "ademci"),
            ("sükût", "sükut"),
            ("mahkûm", "mahkum"),
            ("rükû", "rüku"),
            ("sükûn", "sükun"),
            ("sükûnet", "sükunet"),
            ("kâin", "kain"),
            ("meskûn", "meskun"),
            ("melekût", "melekut"),
            ("gülgûn", "gülgun"),
            ("âcizlik", "acizlik"),
            ("hâkimlik", "hakimlik"),
        ]
        valid_words = [p[0] for p in pairs]
        invalid_words = [p[1] for p in pairs]

        accepted, rejected = check_words(valid_words)
        self.assertEqual(rejected, [], f"Valid circumflex words rejected: {rejected}")

        accepted, rejected = check_words(invalid_words)
        self.assertEqual(accepted, [], f"Illegal unhatted words incorrectly accepted: {accepted}")


class TestFalseRejectRescues(unittest.TestCase):
    """Verifies legitimate morphological inflections rescued from rejected_words.csv."""

    def test_loanword_voicing_rescues(self):
        """Validates blok and tedarik loanword voicing inflections while rejecting bare virtual stems."""
        valid_words = [
            "blok", "bloku", "bloğu", "bloğunda", "bloğundan", "bloğunu", "bloğumuz",
            "tedarik", "tedariki", "tedariği", "tedariğinde", "tedariğini", "tedariğinden"
        ]
        accepted, rejected = check_words(valid_words)
        self.assertEqual(rejected, [], f"Failing loanword voicing forms: {rejected}")

    def test_arabic_loanword_possessive_rescues(self):
        """Validates irregular 3rd-person possessive chains on mevki, sanayi, nezdinde."""
        valid_words = [
            "mevki", "mevkisi", "mevkii", "mevkiinde", "mevkiinden", "mevkiindeki", "mevkiinin",
            "sanayi", "sanayisi", "sanayii", "sanayiinde", "sanayiinden", "sanayiindeki",
            "nezdinde", "nezdindeki", "nezdindekiler"
        ]
        accepted, rejected = check_words(valid_words)
        self.assertEqual(rejected, [], f"Failing Arabic loanword possessive forms: {rejected}")

    def test_authoritative_root_rescues(self):
        """Validates rescued TDK/DD roots mut and ayaklamak."""
        valid_words = [
            "mut", "muttan", "mutun", "mutu", "mutlar",
            "ayaklamak", "ayakladı", "ayaklar"
        ]
        accepted, rejected = check_words(valid_words)
        self.assertEqual(rejected, [], f"Failing authoritative root forms: {rejected}")


class TestReportedWordsAndUnits(unittest.TestCase):
    """Verifies positive acceptance of reported words and unit symbols, and negative rejection of double-ki artifacts."""

    def test_reported_fifteen_words(self):
        """All 15 reported words must be accepted by Turkspell."""
        words = [
            "anki", "Stadı'nda", "trendlerine", "Sahili'ni", "zamankinden",
            "batımını", "Kolombiya'nın", "tescillenmiş", "Ligi'nde", "Takımı'nın",
            "nm", "mAh", "ml", "kW", "kWh"
        ]
        accepted, rejected = check_words(words)
        self.assertEqual(rejected, [], f"Reported words failing: {rejected}")

    def test_unit_symbols(self):
        """Extended scientific and technical unit symbols must be accepted."""
        units = [
            "kHz", "THz", "fps", "kbps", "Mbps", "dpi", "ppi",
            "mV", "mA", "kA", "mW", "MW", "GW", "Wh", "mWh", "MWh", "GWh",
            "pF", "nF", "uF", "µF", "mF", "mH", "hPa", "kPa", "mbar", "psi",
            "kN", "kJ", "MJ", "GJ", "cal", "eV", "keV", "MeV", "GeV",
            "dB", "dBA", "dBm", "lm", "lx", "mmol", "ppm", "ppb",
            "ms", "ns", "ps", "µs", "µm", "cl", "dl"
        ]
        accepted, rejected = check_words(units)
        self.assertEqual(rejected, [], f"Unit symbols failing: {rejected}")

    def test_double_ki_negative_rejection(self):
        """Typo/artifact forms with duplicated kiki must be rejected."""
        wrong_words = ["zamankikinden", "ndakikinden", "nınkikiler", "nunkikilerden"]
        accepted, rejected = check_words(wrong_words)
        self.assertEqual(accepted, [], f"Illegal double-ki artifacts leaked: {accepted}")


class TestDualVoicing(unittest.TestCase):
    """
    Verifies dual-voicing words where Dil Derneği specifies unvoiced inflections
    and TDK specifies voiced inflections (e.g. stereoskop, teleskop, bergamot, baç).
    Both variants must be accepted, while bare virtual stems must be rejected.
    """

    def test_stereoskop_dual_voicing(self):
        if is_tdk_profile():
            self.skipTest("Dual unvoiced forms are Dil Derneği specific (omitted in TDK profile)")
        valid = [
            "stereoskop", "stereoskopu", "stereoskobu", "stereoskopa", "stereoskoba",
            "stereoskopun", "stereoskobun", "stereoskopum", "stereoskobum",
            "stereoskopumuz", "stereoskobumuz", "stereoskoplar", "stereoskopta", "stereoskoptan"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid stereoskop forms failing: {rejected}")

    def test_teleskop_dual_voicing(self):
        if is_tdk_profile():
            self.skipTest("Dual unvoiced forms are Dil Derneği specific (omitted in TDK profile)")
        valid = [
            "teleskop", "teleskopu", "teleskobu", "teleskopa", "teleskoba",
            "teleskopun", "teleskobun", "teleskopum", "teleskobum",
            "teleskopumuz", "teleskobumuz", "teleskoplar", "teleskopta", "teleskoptan",
            "radyoteleskop", "radyoteleskopu", "radyoteleskobu"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid teleskop forms failing: {rejected}")

    def test_bergamot_dual_voicing(self):
        if is_tdk_profile():
            self.skipTest("Dual unvoiced forms are Dil Derneği specific (omitted in TDK profile)")
        valid = [
            "bergamot", "bergamotu", "bergamodu", "bergamota", "bergamoda",
            "bergamotun", "bergamodun", "bergamotum", "bergamodum",
            "bergamotumuz", "bergamodumuz", "bergamotlar", "bergamotta", "bergamottan"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid bergamot forms failing: {rejected}")

    def test_bac_dual_voicing(self):
        if is_tdk_profile():
            self.skipTest("Dual unvoiced forms are Dil Derneği specific (omitted in TDK profile)")
        valid = [
            "baç", "baçı", "bacı", "baça", "baca", "baçın", "bacın",
            "baçım", "bacım", "baçımız", "bacımız", "baçlar", "baçta", "baçtan"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid baç forms failing: {rejected}")

    def test_dual_voicing_bare_virtual_stems_rejected(self):
        """Bare virtual stems without required affixes must be rejected."""
        invalid = ["stereoskob", "teleskob", "bergamod", "bac", "stereoskoblar", "teleskoblar", "bergamodlar", "baclar"]
        accepted, rejected = check_words(invalid)
        self.assertEqual(accepted, [], f"Illegal bare or mismatched virtual stems leaked: {accepted}")


class TestZemberekAnomalyRescues(unittest.TestCase):
    """
    Verifies systematic fixes for Zemberek omissions:
    - Missing LastVowelDrop (mühür->mührü, hısım->hısmı, koyun->koynu, etc.)
    - Monosyllabic / short noun voicing (dip->dibi, smaç->smacı, step->stebi, etc.)
    - Misclassified non-verb -mak words (ahmak->ahmağı, çomak->çomağı, madımak->madımağı)
    - Consonant doubling (müstahak->müstahakkı, serhat->serhaddi, teletıp->teletıbbı)
    """

    def test_vowel_drop_rescues(self):
        valid = [
            "mühür", "mührü", "mühre", "mührün", "mührüm", "mührümüz", "mührünüz",
            "hısım", "hısmı", "hısma", "hısmın", "hısmım", "hısmımız",
            "atıf", "atfı", "atfa", "atfın", "atfım",
            "koyun", "koynu", "koyna", "koynun", "koynum", "koynunda", "koynundan", "koynuna",
            "kayın", "kaynı", "kayna", "kaynın", "kaynım",
            "kabız", "kabzı", "kabza", "kabzın", "kabzında"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid vowel-drop forms failing: {rejected}")

    def test_short_noun_and_doubling_rescues(self):
        valid = [
            "dip", "dibi", "dibe", "dibin", "dibim", "dibimiz", "dibiniz", "dibinde", "dibinden", "dibine", "dibini",
            "ahmak", "ahmağı", "ahmağa", "ahmağın", "ahmaklar", "ahmakça", "ahmaklık",
            "çomak", "çomağı", "çomağa", "çomağın", "çomaklar",
            "madımak", "madımağı", "madımağın",
            "tutamak", "tutamağı",
            "aşık", "aşığı", "aşığına",
            "müstahak", "müstahakkı", "müstahakkını",
            "serhat", "serhaddi", "serhaddinde",
            "teletıp", "teletıbbı",
            "smaç", "smacı", "smacında",
            "step", "stebi",
            "trip", "tribi"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid short noun / doubling forms failing: {rejected}")

    def test_timeline_corpus_rescues(self):
        """Verifies high-frequency rescues discovered via Turkish News Timeline corpus."""
        valid = [
            "gol", "golü", "gole", "golün", "golünü", "golüyle", "golüm", "golümüz", "golünüz", "goller", "golsüz", "gollü",
            "suyu", "suyunu", "suyunun", "suyuna", "suyunda", "suyundan", "suyuyla",
            "odur", "sezonki", "sezonkiler", "sezonkinin", "sezonkinden"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Timeline rescues failing: {rejected}")

        invalid = ["golin", "goli", "golsuz", "suyuda", "suyunı"]
        accepted, rejected = check_words(invalid)
        self.assertEqual(accepted, [], f"Illegal palatal/suyu forms leaked: {accepted}")

    def test_artmak_and_non_voicing_verbs(self):
        """Verifies verbs like artmak, uçmak, çakmak, ekmek do not erroneously voice root consonants."""
        valid = [
            "artmak", "artan", "artıyor", "artacak", "artar", "arttı", "artmış", "artsa", "artmalı",
            "uçmak", "uçan", "uçuyor", "uçacak",
            "çakmak", "çakan", "çakıyor", "çakacak",
            "ekmek", "eken", "ekiyor", "ekecek"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid non-voicing verb forms failing: {rejected}")

        invalid = ["ardıyor", "ardacak"]
        accepted, rejected = check_words(invalid)
        self.assertEqual(accepted, [], f"Illegal voiced verb forms leaked: {accepted}")

    def test_equative_participles(self):
        """Verifies equative case (-nca / -nce) on 3sg participles (-dığı, -diği, -duğu, -düğü)."""
        valid = [
            "olduğunca", "yaptığınca", "geldiğince", "gördüğünce", "bulduğunca",
            "aldığınca", "olabildiğince", "istediğince", "bildiğince", "yettiğince"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid equative participle forms failing: {rejected}")

    def test_participle_locative_relative_ki(self):
        """Verifies relative -ki and its inflections on locative participles (-dığındaki, -diğindeki)."""
        valid = [
            "olduğundaki", "olduğundakiler", "olduğundakini", "olduğundakine", "olduğundakinden",
            "yaptığındaki", "yaptığındakiler", "yaptığındakini", "yaptığındakine",
            "geldiğindeki", "geldiğindekiler", "geldiğindekini", "geldiğindekine",
            "gördüğündeki", "gördüğündekiler", "gördüğündekini", "gördüğündekine",
            "baktığındaki", "bulduğundaki", "aldığındaki", "yaptığımdaki", "geldiğimdeki"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid participle relative -ki forms failing: {rejected}")

    def test_compound_verbs_aorist(self):
        """Verifies that compound verbs with monosyllabic bases preserve their Aorist -ar/-er and causatives preserve -ür."""
        valid = [
            "varsayar", "varsayarlar", "varsayardı", "varsayarmış", "varsayarsa",
            "vazgeçer", "vazgeçerler", "vazgeçerdi", "vazgeçermiş", "vazgeçerse",
            "alıkoyar", "alıkoyarlar", "alıkoyardı", "alıkoyarmış", "alıkoyarsa", "alıkoydu", "alıkoydular",
            "dönüştürür", "dönüştürürler", "dönüştürdü", "dönüştürmüş"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid compound verb aorist forms failing: {rejected}")

    def test_negative_imperative_and_bare_verbal_nouns(self):
        """Verifies 2nd person singular negative imperative and bare -ma/-me forms across verb stems."""
        valid = [
            "yakınlaşma", "yayınlama", "yapma", "gitme", "bakma", "gelme", "dönme", "koşma"
        ]
        if not is_tdk_profile():
            valid.append("sıkılaşma")
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid negative imperative / verbal nouns failing: {rejected}")

    def test_corpus_mined_authority_grammar_fixes(self):
        """Verifies the 4 corpus-mined authority-strict grammar fixes:
        1. 'ad' vowel-starting case/possessive suffixes
        2. '-dIktAn' converb on voicing & narrowing verbs (etmek, gitmek, demek, yemek)
        3. Passive verb stems of official TDK/DD verbs
        4. Noun harmony, non-voicing, palatal-l, and akarsu inflections
        """
        valid = [
            # 1. 'ad' inflections
            "adı", "adını", "adıyla", "adında", "adının", "adındaki", "adından", "adın", "adıydı", "adınız",
            # 2. '-dIktAn' converbs
            "ettikten", "gittikten", "kaybettikten", "fethettikten", "keşfettikten",
            "reddettikten", "hallettikten", "dedikten", "yedikten", "tattıktan", "güttükten",
            # 3. Passive verb inflections
            "karşılaşılan", "kazandırılmıştır", "onurlandırıldı", "ayrıştırılarak",
            "kastedilmiş", "sentezlenen", "kavuşturuldu", "tutturulmuş", "tutuşturuldu",
            "standartlaştırılmış", "yaygınlaştırılması", "kitaplaştırıldı", "mükemmelleştirilmiş",
            # 4. Noun harmony, non-voicing, palatal-l, and akarsu
            "pasaportu", "folkloru", "suikaste", "suikasti", "hilafeti", "velayeti",
            "genotipi", "ziraati", "veliahtı", "ilahiyatı", "satrapı",
            "portalları", "marmelatı", "nekropolü", "akropolü", "parabolün",
            "hiperbolün", "etanolün", "trolü", "akarsuyun", "akarsuyunun"
        ]
        if not is_tdk_profile():
            valid.append("fenotipi")
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Corpus-mined authority grammar forms failing: {rejected}")

    def test_inability_and_negative_verbal_nouns(self):
        """Verifies bare -amama/-ememe and -mama/-meme verbal nouns and case inflections."""
        valid = [
            # Inability bare verbal nouns (-amama / -ememe) and case forms
            "koyamama", "koyamamada", "koyamamadan", "koyamamayla", "koyamamaya", "koyamamayı", "koyamamanın",
            "yapamama", "yapamamada", "yapamamadan", "yapamamayla",
            "gidememe", "gidememede", "gidememeden", "gidememeyle",
            "alamama", "uyuyamama", "anlayamama", "diyememe", "yiyememe",
            # Regular negative verbal nouns (-mama / -meme) and case forms
            "koymama", "koymamada", "koymamadan", "koymamayla",
            "yapmama", "yapmamada", "yapmamadan", "yapmamayla"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid inability/negative verbal nouns failing: {rejected}")

    def test_pure_paradigm_matrix_rescues(self):
        """Verifies all verb and noun/adjective paradigm gaps uncovered by the Pure Paradigm Matrix Audit."""
        valid = [
            # Ability verbal nouns (-abilme/-ebilme) bare, cases & possessives
            "yapabilmeyi", "yapabilmeye", "yapabilmede", "yapabilmeden", "yapabilmenin", "yapabilmeyle",
            "yapabilmem", "yapabilmen", "yapabilmemiz", "yapabilmeniz", "yapabilmeleri",
            "yapabilmemden", "yapabilmemizden", "yapabilmelerinden",
            "koyabilmeyi", "koyabilmemiz", "gelebilmeyi", "gelebilmemiz", "görebilmeyi", "görebilmemiz",
            # Ability infinitive (-abilmek/-ebilmek) cases & copulas
            "yapabilmekten", "yapabilmekle", "yapabilmektir", "yapabilmekti", "yapabilmeksizin",
            "koyabilmekten", "koyabilmeksizin", "gelebilmekten", "gelebilmeksizin",
            # Ability & positive/negative participles + plural possessives
            "yapabildiğim", "yapabildiğimiz", "yapabileceğim", "yapabileceğimiz",
            "yapabildiklerim", "yapabildiklerimiz", "yapabileceklerim", "yapabileceklerimiz",
            "yapacaklarım", "yapacaklarımız", "yapacaklarımdan", "yapacaklarımızdan",
            "diyeceği", "diyeceğim", "diyeceğimiz", "diyeceklerim", "diyeceklerimizden",
            # Ability evidential, conditional, necessitative, progressive & converbs
            "yapabilmişim", "yapabilmişsin", "yapabilmişiz", "yapabilmişsiniz", "yapabilmişçesine",
            "yapabilse", "yapabilsem", "yapabilsen", "yapabilsek", "yapabilseniz", "yapabilseler",
            "yapabilseydi", "yapabilseydim", "yapabilseydin", "yapabilseydik", "yapabilseydiniz",
            "yapabilmeliyim", "yapabilmelisiniz", "yapabilmeliydi", "yapabilmeliydim", "yapabilmeliydik",
            "yapabilmekteyim", "yapabilmektesin", "yapabilmekteyiz", "yapabilmektesiniz", "yapabilmekteler",
            "yapabilinceye", "yapamayıncaya", "yapamamaksızın",
            # Converb & similative chains (-asıya/-esiye, -alı/-eli, -casına/-cesine)
            "yapasıya", "koyasıya", "göresiye", "edilesiye", "edesiye", "gidesiye", "diyesiye", "başlayasıya",
            "okuyalı", "yürüyeli", "edeli", "gideli", "tadalı", "diyeli",
            "yapmazcasına", "gelmezcesine", "yapamazcasına", "gelemezcesine",
            "yapmamışçasına", "gelmemişçesine", "yapamamışçasına", "gelememişçesine",
            # Verbal noun (-ış/-iş/-uş/-üş) across all stem classes including VH/VS/VY
            "okuyuş", "okuyuşu", "okuyuşa", "okuyuşta", "okuyuştan", "okuyuşun",
            "yürüyüş", "yürüyüşü", "yürüyüşe", "yürüyüşte", "yürüyüşten", "yürüyüşün",
            "deyiş", "deyişi", "deyişe", "deyişte", "deyişten", "deyişin",
            "yapışım", "yapışımız", "yapışımdan", "yapışımızdan", "yapışlarından",
            # 2-hop abstract noun derivations (-lılık, -sızlık, -cılık) & rounded vowel stems (-suz/-süz)
            "evlilikten", "evliliğin", "evsizlikten", "evsizliğin", "evsizliği",
            "kitapsızlıktan", "kitapsızlığın", "kitapçılıktan", "kitapçılığın", "kitapçılığı",
            "arabasızlıktan", "kutusuz", "kutusuzluk", "kutusuzluktan", "ütüsüz", "ütüsüzlük", "ütüsüzlükten",
            # Nominal compound conditional copulas (-saydı/-seydi, -ysaydı/-yseydi)
            "evdeyseydi", "evdeyseydim", "evdeyseydik", "güzelseydi", "güzelseydim", "güzelseydik"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid pure paradigm matrix forms failing: {rejected}")

    def test_corpus_mined_inflection_rescues(self):
        """Verifies all verbal, derivational, palatal-L, and homonym inflections rescued by corpus mining."""
        valid = [
            # 2-level verb derivations (DL/DT/DE -> VB/VF + passive/causative)
            "serbestleştirilmesi", "serbestleştirilmesini", "serbestleştirilmesine",
            "derinleşmesini", "yaygınlaşmıştır", "yaygınlaşmıştı",
            "sorunsallaştırılması", "taçlandırılmış", "kuşkulanılan", "biçimlendirilen",
            # Compound auxiliary verb aspects (-agel/-egel, -akal/-ekal, -adur/-edur, -ayaz/-eyaz, -ıver/-iver)
            "kullanılagelen", "tartışılagelen", "anlatılagelen", "kullanılagelmiş", "yapılagelen", "süregelen",
            "bakakaldı", "donakaldı", "düşeyazdı", "yapıverdi", "deyiverdi", "okuyuverdi",
            # Productive passive voice (-ıl/-il/-ul/-ül) on consonant & voicing stems
            "yuvarlatılmış", "inceltilmiş", "ilerletilen", "hicvedildiği", "katedilen",
            # o/u palatal-L roots & sol/bol homonyms
            "makulü", "makule", "makuldür", "gayrimenkulü", "gayrimenkule", "gayrimenkuller",
            "şarampole", "şarampolü", "profiterolü", "mentolü", "mentollü", "bemolü", "monopolü",
            "sola", "solu", "solda", "soldan", "solcu", "solü",
            "bola", "bolu", "boldur", "bolluk",
            "kaşkolu", "kaşkola", "turnusolu",
            # Homonym roots (kül, hal, sır, şık, cebir)
            "külü", "küle", "külün", "külde", "külden", "küllü",
            "hali", "hale", "halin", "halli",
            "sırı", "sıra", "sırın", "sırrı",
            "şıkı", "şıktır", "şıklık", "şıkkı",
            "cebiri", "cebirin", "cebire", "cebri",
            # Postpositives, ayn-ending loanwords & non-voicing stems
            "dolayısıyla", "dolayısı", "göreyse", "göredir", "ötürüdür", "dairdir",
            "ginsengi", "suikastı", "suikasta", "suikastta",
            "müştemilatı", "mercii", "menşei", "tevkii", "karbondioksiti", "karbondioksidi",
            # TDK Dizin 81k audit fixes (palatal-L, homonyms, voicing/doubling, dead verb flag rescue)
            "meşgulü", "meşgule", "mesulü", "mesule", "mamulü", "malulü", "maktulü",
            "menüsküsü", "çöpü", "şoku", "hatmi", "hatime",
            "katile", "katili", "katli", "kadire", "kadiri", "kadri", "nefisi", "nefsi",
            "ağızı", "ağzı", "hayırı", "hayrı", "kayıtı", "kaydı",
            "belagati", "kabahati", "nasihati", "helaki", "istimlaki",
            "marmeladı", "veliahdı", "santigradı", "patiği", "boydağı", "mıncığı",
            "tamlananın", "tamlayanın", "adlandırımın", "sesletimin", "güpürü", "bıttımı"
        ]
        if not is_tdk_profile():
            valid.extend(["öneki", "soneki"])
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid corpus-mined inflections failing: {rejected}")

        # Ensure true vowel-drop omissions and consonant-assimilation typos remain rejected
        invalid = ["oğula", "şehire", "omuza", "kısıma", "göğüse", "hacime", "beyite", "takdığı", "üretiği"]
        accepted_inv, _ = check_words(invalid)
        self.assertEqual(accepted_inv, [], f"Invalid typos leaked: {accepted_inv}")

    def test_abbreviations_and_proper_nouns_apostrophe_inflections(self):
        """Verifies apostrophe inflections across letter-by-letter initialisms, word acronyms, units, and brands."""
        valid = [
            "TBMM'de", "TBMM'den", "TBMM'ye", "TBMM'yi", "TBMM'nin", "TBMM'deki",
            "ABD'de", "ABD'den", "ABD'ye", "ABD'yi", "ABD'nin", "ABD'li", "ABD'liler",
            "AB'de", "AB'den", "AB'ye", "AB'yi", "AB'nin", "AB'liler",
            "CHP'de", "CHP'ye", "CHP'yi", "CHP'nin", "CHP'li", "CHP'liler",
            "MHP'ye", "MHP'li", "AKP'de", "AKP'ye", "AKP'nin", "AKP'li",
            "TDK'de", "TDK'ye", "TDK'nin", "TDK'da", "TDK'ya", "TDK'nın",
            "SGK'de", "SGK'ye", "SGK'da", "SGK'ya", "KYK'ye", "KYK'ya", "TSK'ye", "TSK'ya",
            "YÖK'te", "YÖK'ten", "YÖK'e", "YÖK'ü", "YÖK'ün",
            "RTÜK'te", "RTÜK'ten", "RTÜK'e", "RTÜK'ü", "RTÜK'ün",
            "TÜİK'te", "TÜİK'ten", "TÜİK'e", "TÜİK'in",
            "MİT'te", "MİT'ten", "MİT'e", "MİT'in",
            "ÖSYM'de", "ÖSYM'ye", "ÖSYM'yi", "ÖSYM'nin",
            "KPSS'ye", "YKS'ye", "LGS'ye",
            "KDV'ye", "KDV'yi", "KDV'nin", "KDV'si", "KDV'li", "KDV'siz",
            "ÖTV'ye", "ÖTV'yi", "ÖTV'nin", "ÖTV'si",
            "TRT'ye", "PTT'ye", "THY'ye", "TCMB'ye", "BDDK'ya", "BDDK'ye", "SPK'ya", "EPDK'ya", "KVKK'ya",
            "STK'ler", "STK'lar", "KOBİ'ler", "İHA'lar", "SİHA'lar", "CEO'su", "CEO'ya",
            "TÜBİTAK'ta", "TÜBİTAK'tan", "TÜBİTAK'a", "TÜBİTAK'ın",
            "ASELSAN'da", "ASELSAN'dan", "ASELSAN'a", "ASELSAN'ın",
            "TÜPRAŞ'ta", "TÜPRAŞ'tan", "BOTAŞ'ta", "TEDAŞ'ta", "TUSAŞ'ta", "TEKNOFEST'te",
            "NATO'da", "NATO'ya", "NATO'nun", "UNESCO'ya", "UNICEF'te", "OPEC'te", "OECD'ye", "IMF'ye",
            "TL'lik", "TL'ye", "TL'si", "cm'lik", "cm'ye", "cm'de", "mm'lik", "km'lik",
            "kg'lık", "kg'dan", "gr'lık", "gr'dan", "mg'lık", "GB'lık", "GB'ta", "MB'lık", "MB'ta",
            "iPhone'u", "iPhone'a", "iPhone'da", "iPhone'un", "iPad'i", "iPad'e", "iPad'de",
            "YouTube'da", "YouTube'dan", "YouTube'a", "YouTube'u", "YouTube'un",
            "WhatsApp'ta", "WhatsApp'tan", "Google'da", "Google'dan", "Twitter'da", "Twitter'dan",
            "Linux'ta", "Linux'tan", "İstanbul'da", "Ankara'ya", "Boğaziçi'nde", "Atatürk'te"
        ]
        accepted, rejected = check_words(valid)
        self.assertEqual(rejected, [], f"Valid abbreviation/proper-noun inflections failing: {rejected}")

    def test_overgeneration_and_tdk_misspelling_rejection(self):
        """Verifies strict rejection of morphological overgeneration and TDK common misspellings."""
        invalid_forms = [
            # Missing voicing on voicing stems (including 1sg copula)
            "kitapı", "kitapa", "kitapın", "kitapım", "ağaçı", "ağaça", "çocuku", "çocuka",
            "sokakı", "sokaka", "ayakı", "ayaka", "kulakı", "kalpi", "kalpe", "kalpin",
            "renki", "renke", "borçu", "borça", "umutu", "umuta", "kanatı", "yurtu", "yurta",
            "kurtu", "kurta", "derti", "derte", "gençi", "gençe",
            # False voicing on non-voicing loanwords
            "hukuğu", "hukuğa", "ahlağı", "evrağı", "ittifağı", "merağı", "stoğu", "felakedi",
            "hakikadi", "tabiadı", "sanadı", "devledi", "cumhuriyedi", "edebiyadı", "inşaadı",
            "hayadı", "saadi", "pakedi", "kasedi", "ankedi", "rokedi", "cekedi", "markedi",
            "tabledi", "internedi", "pilodu", "robodu",
            # Missing vowel drop
            "oğulu", "oğula", "ömürü", "ömüre", "şehiri", "şehire", "nehiri", "nehire",
            "zehiri", "zehire", "zehirin", "resimi", "resime", "cisimi", "cisime", "kısımı",
            "göğüsü", "göğüse", "omuzu", "omuza", "ufuku", "ufuka", "keyifi", "keyife",
            "sabırı", "sabıra", "akıla", "fikiri", "fikire", "hükümü", "zulümü",
            # Missing consonant assimilation
            "kitapda", "kitapdan", "ağaçda", "sokakda", "çocukda", "girişde", "bakışda",
            "sınıfda", "mutfakda", "yapdı", "gitdi", "bakdı", "seçdi", "koşdu", "çalışdı",
            "yapdığı", "gitdiği", "bakdığı",
            # TDK common misspellings & mandatory circumflex/proper-noun forms
            "herkez", "herkeze", "herkezden", "yalnış", "yanlız", "orjinal", "antreman",
            "muhattap", "kiprik", "kirbit", "eşki", "şarz", "egsoz", "şöför", "pantalon",
            "vejeteryan", "insiyatif", "dinazor", "klavuz", "klüp", "süpriz", "meyva",
            "makina", "döküman", "tesbih", "laboratuar", "müteahit", "müsade", "şurda",
            "orda", "gardolap", "asvalt", "karnıbahar", "komidin", "parlemento", "sandöviç",
            "silahşör", "üniverste", "zerafet", "ahçı", "matba", "traş", "kareografi",
            "idda", "iddea", "artiz", "apandist", "aperatif", "espiri", "stajer", "poaça",
            "maydonoz", "kolanya", "kanbur", "penbe", "perşenbe", "çarşanba", "tiskinmek",
            "tesbit", "isbat", "malesef", "metod", "standard", "katalok", "psikolok",
            "şarter", "tazzik", "tenefüs", "usül", "zıttı", "zıttına",
            "müslüman", "hristiyan", "hıristiyan", "yahudi",
            "alimlik", "bekar", "bekarlık", "hayasız", "hayasızca"
        ]
        accepted, _ = check_words(invalid_forms)
        self.assertEqual(accepted, [], f"Overgenerated or misspelled forms leaked: {accepted}")

        # Verify that non-voicing [pçtk] stems still accept 1sg/1pl copula (-ım/-im/-um/-üm, -ız/-iz/-uz/-üz)
        valid_copulas = ["devletim", "devletiz", "sanatım", "sanatız", "milletiz", "pilotum", "pilotuz", "çöpüz", "matım", "matız", "Müslüman", "Müslümanlık", "Hristiyan", "Hristiyanlık"]
        _, rej_copulas = check_words(valid_copulas)
        self.assertEqual(rej_copulas, [], f"Valid non-voicing copula or proper noun forms rejected: {rej_copulas}")

    def test_numbers_ordinals_dates_and_clock_times(self):
        """Verifies apostrophe inflections and strict negative rejection on numbers, ordinals, years, and clock times."""
        valid_numbers = [
            "1'de", "1'den", "1'inci", "1'incisi", "2'de", "2'ye", "2'nci", "2'ncisi", "2'şer", "2'ydi",
            "3'te", "3'ten", "3'üncü", "3'üncüsü", "3'er", "3'lü", "4'te", "4'üncü", "5'te", "5'inci",
            "6'da", "6'dan", "6'ya", "6'ncı", "6'ncısı", "6'şar", "7'de", "7'ye", "7'nci", "8'de", "8'inci",
            "9'da", "9'uncu", "10'da", "10'uncu", "20'de", "20'nci", "30'da", "30'uncu", "30'ların",
            "40'ta", "40'ıncı", "50'de", "50'si", "50'nci", "60'ta", "60'ıncı", "70'te", "70'inci",
            "80'de", "80'inci", "80'lerde", "90'da", "90'ıncı", "90'lardan", "100'de", "100'üncü", "100'lerce",
            "1000'de", "1000'inci", "1.000'de", "10.000'de", "100.000'de", "1.000.000'da",
            "1071'de", "1453'te", "1881'de", "1915'te", "1919'da", "1920'de", "1923'te", "1923'ten",
            "1923'teki", "1923'tedir", "1938'de", "1980'lerde", "2000'lerde", "2023'te", "2024'te",
            "2025'te", "2026'da", "2026'dan", "2026'ya", "2026'nın",
            "09.00'da", "10.00'da", "12.00'de", "13.00'te", "14.00'te", "15.00'te", "15.00'ten",
            "16.00'da", "17.00'de", "18.00'de", "19.00'da", "20.00'de", "23.00'te", "24.00'te",
            "09.15'te", "10.30'da", "14.45'te", "16.20'de", "18.40'ta", "21.50'de",
            "1923’te", "2026’da", "2’nci", "6’ncı", "15.00’te"
        ]
        _, rej_valid = check_words(valid_numbers)
        self.assertEqual(rej_valid, [], f"Valid number/date/time forms rejected: {rej_valid}")

        invalid_numbers = [
            "1'nci", "2'inci", "3'ncü", "4'ncü", "5'nci", "6'ıncı", "6'nci", "7'inci",
            "8'nci", "9'ncu", "10'ncu", "20'inci", "50'inci", "100'ncü",
            "1'te", "2'te", "3'de", "4'de", "5'de", "6'ta", "7'te", "8'te", "9'ta", "10'ta",
            "40'da", "60'da", "70'de", "1453'de", "1923'de", "1923'den", "2023'de", "2024'de",
            "2025'de", "2026'ta", "09.00'de", "13.00'da", "14.00'da", "15.00'da", "15.00'de",
            "2'er", "6'ar", "7'er", "3'şer"
        ]
        acc_invalid, _ = check_words(invalid_numbers)
        self.assertEqual(acc_invalid, [], f"Invalid number/date/time forms leaked: {acc_invalid}")

    def test_open_and_closed_compounds_and_auxiliary_verbs(self):
        """Verifies mandatory closed compounds, rejection of consensus open compounds, and TDK/DD profile differences."""
        valid_closed = [
            "kaybetmek", "kaybetti", "kaybediyor", "kaydetmek", "kaydetti", "kaydediyor",
            "sabretmek", "sabretti", "şükretmek", "şükretti", "seyretmek", "seyretti",
            "emretmek", "emretti", "keşfetmek", "keşfetti", "devretmek", "devretti",
            "affetmek", "affetti", "hissetmek", "hissetti", "reddetmek", "reddetti",
            "zannetmek", "zannetti", "halletmek", "halletti", "halledildi",
            "vazgeçmek", "vazgeçti", "varsaymak", "varsaydı", "öngörmek", "öngördü",
            "başvurmak", "başvurdu", "alıkoymak", "alıkoydu",
            "sanki", "oysaki", "mademki", "belki", "hâlbuki", "çünkü", "meğerki", "illaki",
            "biraz", "birçok", "birçoğu", "birkaç", "birkaçı", "birtakım", "herhangi",
            "hiçbir", "hiçbiri", "hiçbirimiz", "bilinçaltı", "denizaltı", "gözaltı",
            "ayaküstü", "suçüstü", "olağanüstü", "gökyüzü", "yeryüzü", "başbakan",
            "yayınevi", "öğretmenevi", "huzurevi", "dershane", "hastane", "pastane",
            "eczane", "depremzede", "kazazede", "insanoğlu", "kızılötesi", "morötesi"
        ]
        _, rej_closed = check_words(valid_closed)
        self.assertEqual(rej_closed, [], f"Valid closed compounds rejected: {rej_closed}")

        invalid_consensus_open = [
            "farketmek", "farketti", "farkediyor", "farketmedi", "terketmek", "terketti",
            "terkediyor", "haketmek", "haketti", "hakediyor", "arzediyorum", "arzetti",
            "yardımetmek", "yardımediyor", "teşekkürederim", "teşekkürediyoruz",
            "kabuletmek", "kabuletti", "kabuledildi", "kabulediyor", "ricaederim",
            "dikkatetti", "merakediyorum", "devamediyor", "devamedecek", "ifadeediyor",
            "eldeedildi", "yokoldu", "yokoluyor", "varoluyor", "sağol", "sağolun",
            "kayıpetmek", "kayıpetti", "kayıtetmek", "sabıretmek", "redetmek", "redetti",
            "zanetti", "haletmek", "haletti", "haledildi", "hisetti", "afetmek", "afedildi",
            "birşey", "birşeyler", "birşeyden", "herşey", "herşeyi", "herşeyden",
            "hiçbirşey", "hiçbirşeyden", "hiçkimse", "hiçkimsenin", "herbir", "herbiri",
            "hergün", "herzaman", "heryerde", "biran", "biranda", "şuan", "şuanda",
            "haftasonu", "haftasonunda", "haftaiçi", "haftaiçinde", "doğumgünü",
            "doğumgününde", "yanyana", "içiçe", "üstüste", "peşpeşe", "elele", "gözgöze",
            "yüzyüze", "uçuca", "yada", "hemde", "bencede", "sencede", "bizcede", "sizcede",
            "tabiki", "tabiiki", "yeşilzeytin", "siyahzeytin", "kuruüzüm", "kurufasulye"
        ]
        acc_open, _ = check_words(invalid_consensus_open)
        self.assertEqual(acc_open, [], f"Invalid joined open compounds leaked: {acc_open}")

        dd_closed_tdk_open = [
            "doğalgaz", "doğalgazda", "önyargı", "önyargılı", "önsöz", "altyazı",
            "altyazılı", "bilimkurgu", "anadil", "anadili", "işbirliği", "işbirliğinde",
            "özgüven", "özgüvenli", "kuruyemiş", "çiğköfte", "ilkönce", "sıradışı",
            "olağandışı", "yasadışı", "yurtdışı", "yurtdışında", "yurtiçi"
        ]
        acc_prof, rej_prof = check_words(dd_closed_tdk_open)
        if is_tdk_profile():
            self.assertEqual(acc_prof, [], f"DD-only closed compounds leaked in TDK profile: {acc_prof}")
        else:
            self.assertEqual(rej_prof, [], f"DD closed compounds rejected in Universal/DD profile: {rej_prof}")

    def test_clitics_particles_and_conjunctions(self):
        """Verifies acceptance of standalone question particles & bound -ki and rejection of joined mı/mi/mu/mü, da/de, and ki typos."""
        valid_clitics_and_ki = [
            "mı", "mi", "mu", "mü",
            "mıyım", "miyim", "muyum", "müyüm",
            "mısın", "misin", "musun", "müsün",
            "mıyız", "miyiz", "muyuz", "müyüz",
            "mısınız", "misiniz", "musunuz", "müsünüz",
            "mıdır", "midir", "mudur", "müdür",
            "mıydı", "miydi", "muydu", "müydü",
            "mıydım", "miydim", "muydum", "müydüm",
            "mıydın", "miydin", "muydun", "müydün",
            "mıydık", "miydik", "muyduk", "müydük",
            "mıydınız", "miydiniz", "muydunuz", "müydünüz",
            "mıymış", "miymiş", "muymuş", "müymüş",
            "benimki", "seninki", "onunki", "bizimki", "sizinki", "onlarınki",
            "dünkü", "bugünkü", "yarınki", "önceki", "sonraki", "şimdiki",
            "evdeki", "okuldaki", "buradaki", "oradaki", "neredeki", "içindeki", "üzerindeki",
            "buradayım", "buradasın", "buradadır", "buradalar", "neredeyim", "neredeler"
        ]
        _, rej_valid = check_words(valid_clitics_and_ki)
        self.assertEqual(rej_valid, [], f"Valid standalone particles or bound -ki forms rejected: {rej_valid}")

        invalid_joined_clitics = [
            "geldimi", "gittimi", "oldumu", "verdimi", "geldinmi", "gördünmü", "anladınmı",
            "geliyormu", "biliyormu", "biliyormusun", "istiyormusun", "yaparmısın",
            "gelecekmisin", "olurmu", "olmazmı", "olacakmı", "varmı", "varmıydı", "varmıdır",
            "yokmu", "yokmuydu", "değilmi", "değilmiydi", "güzelmi", "iyimi", "iyimisin",
            "tamammı", "doğrumu", "değilde", "isede", "vede", "amada", "ancakda", "fakatda",
            "hattada", "yinede", "genede", "belkide", "sankide", "çünküde", "bilede",
            "zatende", "hiçde", "hiçte", "pekde", "pekte", "çokda", "gelsede", "yapsada",
            "olsada", "olursada", "istersede", "gelsekde", "olsamda", "bilsemde", "geldimde",
            "gittimde", "yaptımda", "baktımda", "gördümde", "evdede", "okuldada", "buradada",
            "oradada", "bendede", "sendede", "bizdede", "sizdede", "aslındada", "sonundada",
            "içindede", "üzerindede", "yanındada", "biliyorumki", "diyorumki", "anladımki",
            "gördümki", "baktımki", "sanırımki", "umarımki", "olurki", "olduki", "dediki",
            "demişki", "biliyorsunki", "görüyorsunki", "inanıyorumki", "düşünüyorumki",
            "unutmayalımki", "varsayalımki", "tutki", "yeterki", "bilmemki", "nedendirki",
            "nasılki", "öyleki", "şöyleki", "demekki", "kaldıki", "iyiki", "belliki",
            "şüphesizki", "elbetteki", "gerçiki", "neyseki", "keşkeki"
        ]
        acc_invalid, _ = check_words(invalid_joined_clitics)
        self.assertEqual(acc_invalid, [], f"Invalid joined clitics leaked: {acc_invalid}")

    def test_corpus_mined_derivational_and_inflectional_affixes(self):
        """Verifies positive acceptance of corpus-mined technical roots, compounds, and derivations."""
        valid_words = [
            # Technical root 'kod' regular case and possessive inflections
            "kod", "kodu", "koda", "kodun", "kodda", "koddan", "kodlar", "kodları", "kodların",
            "kodum", "kodumuz", "kodunuz", "kodlu", "kodsuz", "kodcu", "kodluk", "kodunu", "kodunda",
            # Inter-X compound adjectives (-lararası / -lerarası)
            "yıldızlararası", "gezegenlerarası", "dinlerarası", "bankalararası", "eyaletlerarası", "buzullararası",
            # Scientific compound derivations and abstract nouns
            "kütleçekim", "kütleçekimi", "kütleçekimsel", "yerçekimsel", "dilbilgisel", "vektörel",
            "maruziyet", "maruziyeti", "maruziyetin", "maruziyete", "maruziyetler",
            "temsiliyet", "temsiliyeti", "tekabüliyet",
            "asteroit", "asteroitler", "asteroitlerin", "asteroite", "asteroidi", "asteroidin",
            "psikiyatrik", "psikiyatrist", "psikiyatristler",
            "asidik", "embriyonik", "periferik", "taksonomik", "kanonik", "mikroskopik",
            "polimeraz", "oksidaz", "senkronize", "plasebo", "rapçi", "küçükresim",
            # Computing verbal nouns (-lama / -leme)
            "adresleme", "anahtarlama", "kablolama", "haritalama", "lisanslama", "tünelleme", "indeksleme"
        ]
        _, rej = check_words(valid_words)
        self.assertEqual(rej, [], f"Corpus-mined affix derivations rejected: {rej}")


if __name__ == "__main__":
    unittest.main()


