# -*- coding: utf-8 -*-
"""
Turkspell Core Morphology & Regression Test Suite
Validates positive acceptance of legitimate Turkish morphology and
negative rejection of illegal/overgenerated forms across Hunspell profiles.
"""

import os
import sys
import subprocess
import unittest
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = str(ROOT_DIR / "tr")

def check_words(words: list[str], dict_path: str = DICT_PATH) -> tuple[list[str], list[str]]:
    """Runs hunspell -l and returns (accepted_words, rejected_words)."""
    p = subprocess.run(
        ["hunspell", "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    flagged = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    accepted = [w for w in words if w not in flagged]
    rejected = [w for w in words if w in flagged]
    return accepted, rejected


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
            "serçeparmak", "serçeparmağa", "serçeparmağı", "serçeparmağın", "serçeparmakta", "serçeparmaklar"
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


if __name__ == "__main__":
    unittest.main()
