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

ROOT_DIR = Path(__file__).resolve().parent.parent
DICT_PATH = str(ROOT_DIR / "tr")


def get_batch_suggestions(words: list[str], dict_path: str = DICT_PATH) -> dict[str, list[str]]:
    """Runs hunspell -a for a list of words in a single fast process invocation."""
    p = subprocess.run(
        ["hunspell", "-d", dict_path, "-a"],
        input="\n".join(words) + "\n",
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
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

    def assertSuggestedInTopN(self, typo: str, target: str, n: int = 3):
        suggestions = get_suggestions(typo)
        self.assertTrue(
            len(suggestions) > 0,
            f"No suggestions generated for typo '{typo}' (expected '{target}')"
        )
        top_n = suggestions[:n]
        self.assertIn(
            target,
            top_n,
            f"Target '{target}' not in Top-{n} suggestions for '{typo}'. Suggestions: {suggestions[:5]}"
        )

    def test_palatal_l_suggestions(self):
        """Typos with illegal back vowels must suggest thin /l/ front-rounded vowels."""
        test_pairs = [
            ("alkolun", "alkolün", 1),
            ("alkolsuz", "alkolsüz", 1),
            ("kontrolsuz", "kontrolsüz", 1),
            ("alkolu", "alkolü", 1),
        ]
        for typo, target, max_rank in test_pairs:
            with self.subTest(typo=typo, target=target):
                self.assertSuggestedInTopN(typo, target, n=max_rank)

    def test_non_softening_loanwords_suggestions(self):
        """Voiced typos for non-softening roots must suggest unvoiced forms."""
        test_pairs = [
            ("felakedi", "felaketi", 1),
            ("icatı", "icadı", 1),
        ]
        for typo, target, max_rank in test_pairs:
            with self.subTest(typo=typo, target=target):
                self.assertSuggestedInTopN(typo, target, n=max_rank)

    def test_circumflex_suggestions(self):
        """Unhatted typos must suggest circumflex forms at Top-1."""
        test_pairs = [
            ("rüzgar", "rüzgâr", 1),
            ("adeta", "âdeta", 1),
            ("mahkum", "mahkûm", 1),
            ("hikaye", "hikâye", 1),
            ("imkani", "imkânı", 1),
        ]
        for typo, target, max_rank in test_pairs:
            with self.subTest(typo=typo, target=target):
                self.assertSuggestedInTopN(typo, target, n=max_rank)

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


if __name__ == "__main__":
    unittest.main()
