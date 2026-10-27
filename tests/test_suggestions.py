# -*- coding: utf-8 -*-
"""
Turkspell Suggestion Ranking & Accuracy Test Suite
Validates that Hunspell's REP / MAP suggestion engine ranks the intended correction
at Top-1, Top-3, or Top-5, computing Mean Reciprocal Rank (MRR).
"""

import os
import sys
import subprocess
import unittest
from pathlib import Path

import shutil

ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = os.environ.get("TURKSPELL_DICT", str(ROOT_DIR / "tr"))

winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
HUNSPELL_BIN = shutil.which("hunspell") or "hunspell"


def get_batch_suggestions(words: list[str], dict_path: str = DICT_PATH) -> dict[str, list[str]]:
    """Runs hunspell -a for a list of words in a single fast process invocation."""
    aff_file = Path(f"{dict_path}.aff")
    dic_file = Path(f"{dict_path}.dic")
    if not aff_file.exists() or not dic_file.exists():
        raise FileNotFoundError(f"Dictionary files not found at {dict_path} (.aff/.dic)")
    p = subprocess.run(
        [HUNSPELL_BIN, "-d", dict_path, "-a"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    if p.returncode != 0:
        raise RuntimeError(f"hunspell process failed with code {p.returncode}: {p.stderr.strip()}")
    result = {w: [] for w in words}
    for line in p.stdout.splitlines():
        line = line.strip()
        if line.startswith("&"):
            parts = line.split(":", 1)
            header = parts[0].split()
            w = header[1]
            if len(parts) > 1:
                result[w] = [s.strip() for s in parts[1].split(",") if s.strip()]
    return result


def get_suggestions(word: str, dict_path: str = DICT_PATH) -> list[str]:
    """Runs hunspell -a for a single word and returns the ordered list of suggestions."""
    return get_batch_suggestions([word], dict_path=dict_path).get(word, [])


class TestSuggestionRanking(unittest.TestCase):
    """Tests suggestion quality for typical typos across morphological classes."""

    def assertPairsSuggested(self, test_pairs: list[tuple]):
        words = [p[0] for p in test_pairs]
        all_sugs = get_batch_suggestions(words)
        for typo, target, max_rank in test_pairs:
            with self.subTest(typo=typo, target=target):
                sugs = all_sugs.get(typo, [])
                self.assertTrue(
                    len(sugs) > 0,
                    f"No suggestions generated for typo '{typo}' (expected '{target}')"
                )
                top_n = sugs[:max_rank]
                self.assertIn(
                    target,
                    top_n,
                    f"Target '{target}' not in Top-{max_rank} suggestions for '{typo}'. Suggestions: {sugs[:5]}"
                )

    def test_palatal_l_suggestions(self):
        """Typos with illegal back vowels must suggest thin /l/ front-rounded vowels."""
        test_pairs = [
            ("alkolun", "alkolün", 1),
            ("alkolsuz", "alkolsüz", 1),
            ("kontrolsuz", "kontrolsüz", 1),
            ("alkolu", "alkolü", 1),
        ]
        self.assertPairsSuggested(test_pairs)

    def test_non_softening_loanwords_suggestions(self):
        """Voiced typos for non-softening roots must suggest unvoiced forms."""
        test_pairs = [
            ("felakedi", "felaketi", 1),
            ("icatı", "icadı", 1),
        ]
        self.assertPairsSuggested(test_pairs)

    def test_circumflex_suggestions(self):
        """Unhatted typos must suggest circumflex forms at Top-1."""
        test_pairs = [
            ("rüzgar", "rüzgâr", 1),
            ("adeta", "âdeta", 1),
            ("mahkum", "mahkûm", 1),
            ("hikaye", "hikâye", 1),
            ("imkani", "imkânı", 1),
        ]
        self.assertPairsSuggested(test_pairs)

    def test_false_negative_fixes(self):
        """Verifies that reported false negative typo inputs are rejected and gold targets ranked at top."""
        test_pairs = [
            ("bakicısıyla", "bakıcısıyla", 1),
            ("etkinleştirim", "etkinleştirdim", 1),
            ("mezhebide", "mezhebinde", 1),
            ("okumamakça", "okumamakla", 1),
            ("öllüleri", "ölçüleri", 1),
            ("ayakladırmaya", "ayaklandırmaya", 1),
            ("mlla", "malla", 1),
            ("yakalamanmışız", "yakalamamışız", 1),
            ("çoğalıldı", "çoğaltıldı", 1),
            ("misafirlersen", "misafirlerden", 1),
            ("teknolojilerinsen", "teknolojilerinden", 1),
            ("topraklarınsan", "topraklarından", 1),
            ("görüntülerinsen", "görüntülerinden", 1),
            ("çiftliklersen", "çiftliklerden", 1),
            ("goya", "boya", 1),
        ]
        self.assertPairsSuggested(test_pairs)

    def test_compound_and_separate_suggestions(self):
        """Verifies that commonly conjoined phrases and inflected auxiliary verbs are split and suggested at Top-1."""
        test_pairs = [
            ("farketti", "fark etti", 1),
            ("farkediyor", "fark ediyor", 1),
            ("farketmedi", "fark etmedi", 1),
            ("terketti", "terk etti", 1),
            ("terkediyor", "terk ediyor", 1),
            ("hakediyor", "hak ediyor", 1),
            ("arzediyorum", "arz ediyorum", 1),
            ("teşekkürederim", "teşekkür ederim", 1),
            ("teşekkürediyoruz", "teşekkür ediyoruz", 1),
            ("kabuletmek", "kabul etmek", 1),
            ("kabuledildi", "kabul edildi", 1),
            ("ricaederim", "rica ederim", 1),
            ("merakediyorum", "merak ediyorum", 1),
            ("devamediyor", "devam ediyor", 1),
            ("ifadeediyor", "ifade ediyor", 1),
            ("eldeedildi", "elde edildi", 1),
            ("yokoluyor", "yok oluyor", 1),
            ("varoluyor", "var oluyor", 1),
            ("sağolun", "sağ olun", 1),
            ("kayıpetmek", "kaybetmek", 1),
            ("kayıpetti", "kaybetti", 1),
            ("redetti", "reddetti", 1),
            ("haletti", "halletti", 1),
            ("haledildi", "halledildi", 1),
            ("hisetti", "hissetti", 1),
            ("ayırdetmek", "ayırt etmek", 1),
            ("yanyana", "yan yana", 1),
            ("artarda", "art arda", 1),
            ("dizdize", "diz dize", 1),
            ("uçuca", "uç uca", 1),
            ("haftasonu", "hafta sonu", 1),
            ("haftasonunda", "hafta sonunda", 1),
            ("haftaiçi", "hafta içi", 1),
            ("haftaiçinde", "hafta içinde", 1),
            ("doğumgününde", "doğum gününde", 1),
            ("herşey", "her şey", 1),
            ("herşeyden", "her şeyden", 1),
            ("birşey", "bir şey", 1),
            ("birşeyler", "bir şeyler", 1),
            ("hiçbirşey", "hiçbir şey", 1),
            ("hiçbirşeyden", "hiçbir şeyden", 1),
            ("hiçkimseye", "hiç kimseye", 1),
            ("herbirimiz", "her birimiz", 1),
            ("herzamanki", "her zamanki", 1),
            ("heryerde", "her yerde", 1),
            ("biranda", "bir anda", 1),
            ("şuan", "şu an", 1),
            ("şuanda", "şu anda", 1),
            ("pekçok", "pek çok", 1),
            ("yada", "ya da", 1),
            ("hemde", "hem de", 1),
            ("bencede", "bence de", 1),
            ("sencede", "sence de", 1),
            ("tabiki", "tabii ki", 1),
            ("tabiiki", "tabii ki", 1),
            ("iyiki", "iyi ki", 1),
            ("hoşçakal", "hoşça kal", 1),
        ]
        self.assertPairsSuggested(test_pairs)

    def test_mrr_benchmark(self):
        """Evaluates Mean Reciprocal Rank (MRR) across a comprehensive 25-word evaluation battery."""
        battery = [
            ("alkolun", "alkolün"),
            ("alkolsuz", "alkolsüz"),
            ("kontrolsuz", "kontrolsüz"),
            ("alkolu", "alkolü"),
            ("felakedi", "felaketi"),
            ("icatı", "icadı"),
            ("rüzgar", "rüzgâr"),
            ("adeta", "âdeta"),
            ("mahkum", "mahkûm"),
            ("hikaye", "hikâye"),
            ("imkani", "imkânı"),
            ("traş", "tıraş"),
            ("tesbih", "tespih"),
            ("herkez", "herkes"),
            ("kiprik", "kirpik"),
            ("eşki", "ekşi"),
            ("şarz", "şarj"),
            ("egsoz", "egzoz"),
            ("yanısıra", "yanı sıra"),
            ("farketmek", "fark etmek"),
            ("sağol", "sağ ol"),
            ("hoşgeldiniz", "hoş geldiniz"),
            ("sayili", "sayılı"),
            ("numarali", "numaralı"),
            ("klavuz", "kılavuz"),
        ]
        
        words_to_query = [b[0] for b in battery]
        all_sugs = get_batch_suggestions(words_to_query)
        
        rr_sum = 0.0
        top1_count = 0

        for typo, target in battery:
            suggestions = all_sugs.get(typo, [])
            if target in suggestions:
                rank = suggestions.index(target) + 1
                rr_sum += 1.0 / rank
                if rank == 1:
                    top1_count += 1

        mrr = rr_sum / len(battery)
        top1_pct = (top1_count / len(battery)) * 100

        print(f"\nSuggestion Battery MRR: {mrr:.3f} | Top-1 Accuracy: {top1_pct:.1f}% ({top1_count}/{len(battery)})")
        self.assertGreaterEqual(mrr, 0.90, f"MRR {mrr:.3f} fell below threshold 0.90")
        self.assertGreaterEqual(top1_pct, 90.0, f"Top-1 accuracy {top1_pct:.1f}% fell below 90%")

    def test_tdk_common_misspellings_top1(self):
        """Verifies Top-1 suggestion accuracy across TDK 'Sıkça Yapılan Yazım Yanlışları' and circumflex inflections."""
        test_pairs = [
            ("herkez", "herkes", 1),
            ("herkezden", "herkesten", 1),
            ("yalnış", "yanlış", 1),
            ("yanlız", "yalnız", 1),
            ("orjinal", "orijinal", 1),
            ("antreman", "antrenman", 1),
            ("muhattap", "muhatap", 1),
            ("espiri", "espri", 1),
            ("stajer", "stajyer", 1),
            ("poaça", "poğaça", 1),
            ("maydonoz", "maydanoz", 1),
            ("kolanya", "kolonya", 1),
            ("kanbur", "kambur", 1),
            ("penbe", "pembe", 1),
            ("perşenbe", "perşembe", 1),
            ("çarşanba", "çarşamba", 1),
            ("tiskinmek", "tiksinmek", 1),
            ("tesbit", "tespit", 1),
            ("isbat", "ispat", 1),
            ("malesef", "maalesef", 1),
            ("metod", "metot", 1),
            ("standard", "standart", 1),
            ("katalok", "katalog", 1),
            ("psikolok", "psikolog", 1),
            ("şarter", "şalter", 1),
            ("tazzik", "tazyik", 1),
            ("tenefüs", "teneffüs", 1),
            ("usül", "usul", 1),
            ("zıttı", "zıddı", 1),
            ("zıttına", "zıddına", 1),
            ("ahçı", "aşçı", 1),
            ("idda", "iddia", 1),
            ("iddea", "iddia", 1),
            ("müslüman", "Müslüman", 1),
            ("hristiyan", "Hristiyan", 1),
            ("yahudi", "Yahudi", 1),
            ("zekası", "zekâsı", 1),
            ("rüzgarlı", "rüzgârlı", 1),
            ("kağıdı", "kâğıdı", 1),
            ("mekanlar", "mekânlar", 1),
            ("şikayetçi", "şikâyetçi", 1),
            ("mahkumiyet", "mahkûmiyet", 1),
            ("imkansızlık", "imkânsızlık", 1),
            ("hikayeler", "hikâyeler", 1),
            ("muhafazakarlık", "muhafazakârlık", 1),
            ("hakimiyeti", "hâkimiyeti", 1),
            ("bekarlık", "bekârlık", 1),
            ("amalık", "âmâlık", 1),
            ("ademcilik", "âdemcilik", 1),
            ("mahkukat", "mahkûkât", 1),
        ]
        self.assertPairsSuggested(test_pairs)

    def test_morphological_error_suggestions_top1(self):
        """Verifies Top-1 suggestion accuracy for voicing, vowel-drop, and consonant assimilation errors."""
        test_pairs = [
            ("kitapı", "kitabı", 1),
            ("kitapım", "kitabım", 1),
            ("çocuka", "çocuğa", 1),
            ("sokakı", "sokağı", 1),
            ("kalpi", "kalbi", 1),
            ("kurtu", "kurdu", 1),
            ("gençi", "genci", 1),
            ("hukuğu", "hukuku", 1),
            ("cumhuriyedi", "cumhuriyeti", 1),
            ("pilodu", "pilotu", 1),
            ("zehiri", "zehri", 1),
            ("şehiri", "şehri", 1),
            ("oğulu", "oğlu", 1),
            ("kitapda", "kitapta", 1),
            ("yapdı", "yaptı", 1),
            ("gitdi", "gitti", 1),
            ("gitdiği", "gittiği", 1),
        ]
        self.assertPairsSuggested(test_pairs)

    def test_number_and_clock_time_suggestions_top1(self):
        """Verifies Top-1 suggestion accuracy for invalid ordinal, year, and clock-time suffixes."""
        test_pairs = [
            ("2'inci", "2'nci", 1),
            ("6'ıncı", "6'ncı", 1),
            ("6'nci", "6'ncı", 1),
            ("7'inci", "7'nci", 1),
            ("20'inci", "20'nci", 1),
            ("50'inci", "50'nci", 1),
            ("3'ncü", "3'üncü", 1),
            ("4'ncü", "4'üncü", 1),
            ("100'ncü", "100'üncü", 1),
            ("1923'de", "1923'te", 1),
            ("1923'den", "1923'ten", 1),
            ("1453'de", "1453'te", 1),
            ("2023'de", "2023'te", 1),
            ("2024'de", "2024'te", 1),
            ("2025'de", "2025'te", 1),
            ("2026'ta", "2026'da", 1),
            ("15.00'da", "15.00'te", 1),
            ("15.00'de", "15.00'te", 1),
            ("13.00'da", "13.00'te", 1),
            ("09.00'de", "09.00'da", 1),
            ("2'er", "2'şer", 1),
            ("6'ar", "6'şar", 1),
        ]
        self.assertPairsSuggested(test_pairs)

    def test_clitics_particles_and_conjunctions_top1(self):
        """Verifies Top-1 suggestion accuracy for joined question particles (mı/mi/mu/mü) and conjunctions (da/de, ki)."""
        test_pairs = [
            ("geldimi", "geldi mi", 1),
            ("oldumu", "oldu mu", 1),
            ("verdimi", "verdi mi", 1),
            ("gördünmü", "gördün mü", 1),
            ("biliyormu", "biliyor mu", 1),
            ("biliyormusun", "biliyor musun", 1),
            ("istiyormusun", "istiyor musun", 1),
            ("yaparmısın", "yapar mısın", 1),
            ("gelecekmisin", "gelecek misin", 1),
            ("olurmu", "olur mu", 1),
            ("olmazmı", "olmaz mı", 1),
            ("varmı", "var mı", 1),
            ("varmıydı", "var mıydı", 1),
            ("yokmu", "yok mu", 1),
            ("değilmi", "değil mi", 1),
            ("değilmiydi", "değil miydi", 1),
            ("güzelmi", "güzel mi", 1),
            ("iyimi", "iyi mi", 1),
            ("iyimisin", "iyi misin", 1),
            ("doğrumu", "doğru mu", 1),
            ("değilde", "değil de", 1),
            ("isede", "ise de", 1),
            ("vede", "ve de", 1),
            ("yinede", "yine de", 1),
            ("belkide", "belki de", 1),
            ("sankide", "sanki de", 1),
            ("bilede", "bile de", 1),
            ("zatende", "zaten de", 1),
            ("hiçde", "hiç de", 1),
            ("hiçte", "hiç de", 1),
            ("pekde", "pek de", 1),
            ("pekte", "pek de", 1),
            ("gelsede", "gelse de", 1),
            ("yapsada", "yapsa da", 1),
            ("olsada", "olsa da", 1),
            ("olursada", "olursa da", 1),
            ("olsamda", "olsam da", 1),
            ("bilsemde", "bilsem de", 1),
            ("geldimde", "geldim de", 1),
            ("yaptımda", "yaptım da", 1),
            ("evdede", "evde de", 1),
            ("buradada", "burada da", 1),
            ("bendede", "bende de", 1),
            ("aslındada", "aslında da", 1),
            ("içindede", "içinde de", 1),
            ("üzerindede", "üzerinde de", 1),
            ("biliyorumki", "biliyorum ki", 1),
            ("diyorumki", "diyorum ki", 1),
            ("anladımki", "anladım ki", 1),
            ("gördümki", "gördüm ki", 1),
            ("olurki", "olur ki", 1),
            ("olduki", "oldu ki", 1),
            ("dediki", "dedi ki", 1),
            ("demişki", "demiş ki", 1),
            ("biliyorsunki", "biliyorsun ki", 1),
            ("tutki", "tut ki", 1),
            ("yeterki", "yeter ki", 1),
            ("bilmemki", "bilmem ki", 1),
            ("nasılki", "nasıl ki", 1),
            ("öyleki", "öyle ki", 1),
            ("demekki", "demek ki", 1),
            ("kaldıki", "kaldı ki", 1),
            ("iyiki", "iyi ki", 1),
            ("tabiki", "tabii ki", 1),
            ("belliki", "belli ki", 1),
            ("elbetteki", "elbette ki", 1),
            ("neyseki", "neyse ki", 1),
            ("keşkeki", "keşke ki", 1),
        ]
        self.assertPairsSuggested(test_pairs)


if __name__ == "__main__":
    unittest.main()
