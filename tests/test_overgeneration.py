# -*- coding: utf-8 -*-
"""
Turkspell Overgeneration & Fuzzing Test Suite
Verifies that affix rules and flags do NOT overgenerate impossible Turkish words:
1. Illegal double buffer consonants (*kapıssı, *arabaynı)
2. Illegal vowel collisions (*acııydı, *kediin, *gülmeini)
3. Illegal verb formations (*debilecek, *debileceklerine)
4. Illegal vowel harmony violations (*evlar, *odalarımiz)
"""

import sys
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = os.environ.get("TURKSPELL_DICT", str(ROOT_DIR / "tr"))

sys.path.insert(0, str(ROOT_DIR / "build"))
from build_common import find_hunspell

HUNSPELL_BIN = find_hunspell() or "hunspell"


def check_illegal_words(words: list[str], dict_path: str = DICT_PATH) -> list[str]:
    """Runs hunspell -l on words that MUST be rejected. Returns any that leaked (were accepted)."""
    aff_file = Path(f"{dict_path}.aff")
    dic_file = Path(f"{dict_path}.dic")
    if not aff_file.exists() or not dic_file.exists():
        raise FileNotFoundError(f"Dictionary files not found at {dict_path} (.aff/.dic)")
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-l"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    if p.returncode != 0:
        raise RuntimeError(f"hunspell process failed with code {p.returncode}: {p.stderr.strip()}")
    flagged = set(line.strip() for line in p.stdout.splitlines() if line.strip())
    # A leaked word is one that hunspell accepted (NOT in flagged)
    leaked = [w for w in words if w not in flagged]
    return leaked


class TestOvergenerationProtection(unittest.TestCase):
    """Tests that illegal morphological combinations are strictly rejected."""

    def test_double_buffer_consonants(self):
        """Buffer consonants (y, s, n) must never be doubled or misplaced."""
        illegal = [
            "kapıssı", "kapıssa", "arabannda", "arabaynı", "evnne",
            "masannın", "kediyni", "odassa", "elmaylaa", "kuzuyya"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Illegal double buffer consonants leaked: {leaked}")

    def test_vowel_collision_anomalies(self):
        """Vowel-initial suffixes must not attach to vowel-final stems without buffer consonant."""
        illegal = [
            "acııydı", "eliiydi", "anomaliine", "gülmeini", "enseindeki",
            "kediin", "kuzuun", "arabaa", "masaa", "tarlain", "tarlai"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Illegal vowel collisions leaked: {leaked}")

    def test_demek_yemek_broken_rules(self):
        """The notorious 'debileceklerine' bug must remain 100% purged."""
        illegal = [
            "debilecek", "debilecekler", "debileceklerine", "debileceklerini",
            "debilecekti", "debilecekmiş", "debilecektir",
            "yebilecek", "yebilecekler", "yebileceklerine", "yebileceklerini"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Broken demek/yemek forms leaked: {leaked}")

    def test_gross_vowel_harmony_violations(self):
        """Front-vowel stems taking back-vowel suffixes and vice versa."""
        illegal = [
            "evlar", "evdan", "evda", "evın",
            "kedilar", "kedidan", "kedida",
            "kapiler", "kapiden", "kapide",
            "odalere", "odalerde", "odalerden"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Gross vowel harmony violations leaked: {leaked}")

    def test_impossible_suffix_chains(self):
        """Double case markers and broken ablative/locative chains."""
        illegal = [
            "evdene", "okuldana", "masadada", "okuldanler",
            "arabadaın", "çocukdaden", "masadanler"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Impossible suffix chains leaked: {leaked}")

    def test_bare_virtual_stems(self):
        """Virtual stems guarded by NEEDAFFIX X must never be recognized as bare words."""
        illegal = [
            "bloğ", "tedariğ", "imalad", "cenned", "cehd", "kulb"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Bare virtual stems leaked into dictionary: {leaked}")

    def test_passive_l_stem_overgeneration(self):
        """Verb stems ending in 'l' must never take passive -Il- suffixes."""
        illegal = [
            "çoğalıldı", "alıldı", "çalıldı", "bululdu", "bilildi", "ölüldü", "kalıldı"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Passive l-stems overgenerated: {leaked}")

    def test_plural_copula_overgeneration(self):
        """Plural nouns and plural possessives must never take 2sg/1sg copulas (-sen/-san)."""
        illegal = [
            "misafirlersen", "teknolojilerinsen", "topraklarınsan", "görüntülerinsen", "çiftliklersen"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Plural singular copulas overgenerated: {leaked}")

    def test_chained_derivation_overgeneration(self):
        """Recursive chained affix pseudo-words (*kitaplıkçılıklaştırmak, *denizlikleşebilen) must be rejected."""
        illegal = [
            "denizlikleşebilen", "akılsızlıkçılıklaştırmak", "kapılılıkçılıklaştırmak",
            "havasızlıkçılıklaştırmak", "kitaplıkçılıklaştırmak", "topraksızlıkçılıklaştırmak",
            "dağlıkçılıklaştırmak", "insanlıkçılıklaştırmak", "kapısızlıkçılıklaştırmak",
            "çiçeklikleşebilen", "mühendislikleşebilen", "güneşlikleşebilen",
            "arabalıkçılıklaştırmak", "ormanlıkçılıklaştırmak", "avukatlıkçılıklaştırmak",
            "ağaçlıklılaşabilmek", "arabasızlıkçılıklaştırmak", "ağaçlıkçılıklaştırmak",
            "zamansızlıkçılıklaştırmak", "ağaçlılıkçılıklaştırmak", "masasızlıkçılıklaştırmak",
            "dünyalıkçılıklaştırmak", "şehircilikleştiriliverme", "dağlılıkçılıklaştırmak",
            "kalemlikleşebilen", "evlikleşebilen"
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Chained derivation pseudo-words leaked: {leaked}")

    def test_rounded_aorist_harmony_rejection(self):
        """Rounded aorist stems (-ur/-ür) must reject unrounded 2sg/2pl forms (*olursın, *görürsin)."""
        illegal = [
            "olursın", "olursınız", "bulursın", "bulursınız", "durursın",
            "vurursın", "görürsin", "görürsiniz", "ölürsin", "ölürsiniz",
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Unrounded 2nd-person forms on rounded aorists leaked: {leaked}")

    def test_voicing_copula_rounding_harmony(self):
        """1sg/1pl copulas (VC/vc) must respect rounding harmony."""
        illegal = [
            "devletüm", "devletüz", "kitabum", "sanatum",
            "pilotım", "pilotız", "stokım", "stokız",
            "çöpim", "çöpiz", "kulpım",
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Rounding-violating VC/vc copulas leaked: {leaked}")

    def test_invalid_24h_clock_times(self):
        """Only 24.00 is valid for hour 24; 24.01..24.59 must be rejected."""
        illegal = ["24.01'de", "24.15'te", "24.30'da", "24.59'da"]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Invalid 24h clock times leaked: {leaked}")

    def test_dotted_and_superscript_apostrophe_rejection(self):
        """TDK: abbreviations ending in '.' or superscripts must NOT take apostrophes or mismatched inflections."""
        illegal = [
            "vb.'leri", "vb.'ne", "vb.'de", "Alm.'dan", "Alm.'da",
            "İng.'yi", "İng.'de", "a.g.e.'de", "a.g.e.'den", "yy.'da",
            "Dr.'a", "Prof.'a", "T.C.'de", "T.C.ler", "a.lar",
            "cm³'e", "cm³'te", "cm³de", "m²'ye", "m²'de", "m²da",
            "6⁴'ten", "6⁴dan", "m²nci", "cm³üncü",
            "mat'ın", "zıt'a", "kal'ın", "ark'a",
        ]
        leaked = check_illegal_words(illegal)
        self.assertEqual(leaked, [], f"Illegal apostrophed or leaked abbreviation/override forms accepted: {leaked}")


if __name__ == "__main__":
    unittest.main()

