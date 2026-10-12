"""Audit apostrophe inflections of all 10,505 abbreviations (custom_abbrevs.txt)
and 5,146 proper names (custom_names.txt) against tr.dic / tr.aff using Hunspell.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
ABBREVS_PATH = ROOT / "lexicons" / "custom_abbreviations.json"
NAMES_PATH = ROOT / "lexicons" / "custom_names.json"
DIC_PATH = ROOT / "tr.dic"


def find_hunspell() -> str:
    candidates = [
        ROOT / "tools" / "hunspell" / "bin" / "hunspell.exe",
        Path(r"C:\msys64\mingw64\bin\hunspell.exe"),
        Path(r"C:\msys64\ucrt64\bin\hunspell.exe"),
        Path(r"C:\Program Files\hunspell\bin\hunspell.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return "hunspell"


def check_words_batch(words: list[str]) -> set[str]:
    if not words:
        return set()
    hunspell_bin = find_hunspell()
    dic_base = str(ROOT / "tr")
    rejected = set()
    chunk_size = 5000
    for i in range(0, len(words), chunk_size):
        chunk = words[i : i + chunk_size]
        payload = "\n".join(chunk) + "\n"
        proc = subprocess.run(
            [hunspell_bin, "-d", dic_base, "-i", "UTF-8", "-l"],
            input=payload.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
            w = line.strip()
            if w:
                rejected.add(w)
    return rejected


def main():
    dic_map = {}
    with open(DIC_PATH, encoding="utf-8") as f:
        f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "/" in line:
                h, fl = line.split("/", 1)
            else:
                h, fl = line, ""
            dic_map[h] = fl

    abbrevs = []
    with open(ABBREVS_PATH, encoding="utf-8") as f:
        for item in json.load(f):
            lem = item.get("lemma", "").strip()
            if lem:
                abbrevs.append(lem)

    names = []
    with open(NAMES_PATH, encoding="utf-8") as f:
        for item in json.load(f):
            lem = item.get("lemma", "").strip()
            if lem:
                names.append(lem)

    print(f"Loaded {len(abbrevs):,} custom_abbrevs and {len(names):,} custom_names.")

    unflagged_abbrevs = [a for a in abbrevs if not dic_map.get(a, "")]
    unflagged_names = [n for n in names if not dic_map.get(n, "")]
    print(f"Unflagged abbreviations in tr.dic: {len(unflagged_abbrevs):,} / {len(abbrevs):,}")
    print(f"Unflagged proper names in tr.dic : {len(unflagged_names):,} / {len(names):,}")

    # Test high-profile real-world Turkish abbreviation & proper name inflections
    gold_tests = [
        # Initialisms read letter-by-letter (front vowel 'e' reading for B, C, Ç, D, F, G, H, J, K, L, M, N, P, R, S, Ş, T, V, Y, Z)
        "TBMM'de", "TBMM'den", "TBMM'ye", "TBMM'yi", "TBMM'nin", "TBMM'deki",
        "ABD'de", "ABD'den", "ABD'ye", "ABD'yi", "ABD'nin", "ABD'li",
        "AB'de", "AB'den", "AB'ye", "AB'yi", "AB'nin",
        "BM'de", "BM'den", "BM'ye", "BM'yi", "BM'nin",
        "CHP'de", "CHP'den", "CHP'ye", "CHP'yi", "CHP'nin", "CHP'li", "CHP'liler",
        "MHP'de", "MHP'den", "MHP'ye", "MHP'yi", "MHP'nin", "MHP'li",
        "AKP'de", "AKP'den", "AKP'ye", "AKP'yi", "AKP'nin", "AKP'li",
        "DEM'de", "DEM'den", "DEM'e",
        "TDK'de", "TDK'den", "TDK'ye", "TDK'yi", "TDK'nin",
        "TDK'da", "TDK'dan", "TDK'ya", "TDK'yı", "TDK'nın",
        "SGK'de", "SGK'den", "SGK'ye", "SGK'yi", "SGK'nin",
        "SGK'da", "SGK'dan", "SGK'ya", "SGK'yı", "SGK'nın",
        "KYK'de", "KYK'den", "KYK'ye", "KYK'yi", "KYK'nin",
        "KYK'da", "KYK'dan", "KYK'ya", "KYK'yı", "KYK'nın",
        "TSK'de", "TSK'den", "TSK'ye", "TSK'yi", "TSK'nin",
        "TSK'da", "TSK'dan", "TSK'ya", "TSK'yı", "TSK'nın",
        "TCK'de", "TCK'den", "TCK'ye", "TCK'da", "TCK'dan", "TCK'ya",
        "TTK'de", "TTK'ye", "TTK'da", "TTK'ya",
        "YÖK'te", "YÖK'ten", "YÖK'e", "YÖK'ü", "YÖK'ün",
        "RTÜK'te", "RTÜK'ten", "RTÜK'e", "RTÜK'ü", "RTÜK'ün",
        "TÜİK'te", "TÜİK'ten", "TÜİK'e", "TÜİK'i", "TÜİK'in",
        "MİT'te", "MİT'ten", "MİT'e", "MİT'i", "MİT'in",
        "ÖSYM'de", "ÖSYM'den", "ÖSYM'ye", "ÖSYM'yi", "ÖSYM'nin",
        "KPSS'de", "KPSS'den", "KPSS'ye", "KPSS'yi", "KPSS'nin",
        "YKS'de", "YKS'den", "YKS'ye", "YKS'yi", "YKS'nin",
        "LGS'de", "LGS'den", "LGS'ye", "LGS'yi", "LGS'nin",
        "KDV'de", "KDV'den", "KDV'ye", "KDV'yi", "KDV'nin", "KDV'si", "KDV'li",
        "ÖTV'de", "ÖTV'den", "ÖTV'ye", "ÖTV'yi", "ÖTV'nin", "ÖTV'si",
        "TCMB'de", "TCMB'den", "TCMB'ye", "TCMB'nin",
        "BDDK'de", "BDDK'ye", "BDDK'da", "BDDK'ya", "BDDK'nın", "BDDK'nin",
        "SPK'de", "SPK'ye", "SPK'da", "SPK'ya", "SPK'nın", "SPK'nin",
        "EPDK'de", "EPDK'ye", "EPDK'da", "EPDK'ya", "EPDK'nın",
        "KVKK'de", "KVKK'ye", "KVKK'da", "KVKK'ya", "KVKK'nın",
        "TRT'de", "TRT'den", "TRT'ye", "TRT'yi", "TRT'nin",
        "PTT'de", "PTT'den", "PTT'ye", "PTT'yi", "PTT'nin",
        "THY'de", "THY'den", "THY'ye", "THY'yi", "THY'nin",
        "TCDD'de", "TCDD'den", "TCDD'ye", "TCDD'nin",
        "İBB'de", "İBB'den", "İBB'ye", "İBB'yi", "İBB'nin",
        "ABB'de", "ABB'den", "ABB'ye", "ABB'nin",
        "GSYİH'nin", "GSYİH'ye", "GSYİH'de",
        "DNA'sı", "DNA'nın", "DNA'ya", "DNA'da", "DNA'dan",
        "RNA'sı", "RNA'nın", "RNA'ya", "RNA'da",
        "STK'ler", "STK'lerin", "STK'lere", "STK'lerde", "STK'lar", "STK'ların", "STK'lara", "STK'larda",
        "KOBİ'ler", "KOBİ'lerin", "KOBİ'lere", "KOBİ'lerde",
        "İHA'lar", "İHA'ların", "İHA'lara", "İHA'larda",
        "SİHA'lar", "SİHA'ların", "SİHA'lara", "SİHA'larda",
        "CEO'su", "CEO'sunun", "CEO'ya", "CEO'nun", "CEO'lar",
        "CFO'su", "CTO'su",
        "TV'de", "TV'den", "TV'ye", "TV'yi", "TV'nin", "TV'ler",
        "PC'de", "PC'den", "PC'ye", "PC'yi", "PC'nin",
        "ABD'liler", "AB'liler",
        # Acronyms read as words (hecelenerek okunan kısaltmalar)
        "TÜBİTAK'ta", "TÜBİTAK'tan", "TÜBİTAK'a", "TÜBİTAK'ı", "TÜBİTAK'ın",
        "ASELSAN'da", "ASELSAN'dan", "ASELSAN'a", "ASELSAN'ı", "ASELSAN'ın",
        "HAVELSAN'da", "HAVELSAN'dan", "HAVELSAN'a", "HAVELSAN'ın",
        "ROKETSAN'da", "ROKETSAN'dan", "ROKETSAN'a", "ROKETSAN'ın",
        "TUSAŞ'ta", "TUSAŞ'tan", "TUSAŞ'a", "TUSAŞ'ın",
        "TÜPRAŞ'ta", "TÜPRAŞ'tan", "TÜPRAŞ'a", "TÜPRAŞ'ı", "TÜPRAŞ'ın",
        "BOTAŞ'ta", "BOTAŞ'tan", "BOTAŞ'a", "BOTAŞ'ın",
        "TEDAŞ'ta", "TEDAŞ'tan", "TEDAŞ'a", "TEDAŞ'ın",
        "TEKNOFEST'te", "TEKNOFEST'ten", "TEKNOFEST'e", "TEKNOFEST'in",
        "NATO'da", "NATO'dan", "NATO'ya", "NATO'yu", "NATO'nun",
        "UNESCO'da", "UNESCO'dan", "UNESCO'ya", "UNESCO'yu", "UNESCO'nun",
        "UNICEF'te", "UNICEF'ten", "UNICEF'e", "UNICEF'in",
        "FIFA'da", "FIFA'dan", "FIFA'ya", "FIFA'nın",
        "UEFA'da", "UEFA'dan", "UEFA'ya", "UEFA'nın",
        "FİBA'da", "FİBA'ya", "FİBA'nın",
        "OPEC'te", "OPEC'ten", "OPEC'e", "OPEC'in",
        "OECD'de", "OECD'den", "OECD'ye", "OECD'nin",
        "IMF'de", "IMF'den", "IMF'ye", "IMF'nin",
        "DSÖ'de", "DSÖ'den", "DSÖ'ye", "DSÖ'nün",
        "AFAD'da", "AFAD'dan", "AFAD'a", "AFAD'ın",
        "TOKİ'de", "TOKİ'den", "TOKİ'ye", "TOKİ'nin",
        "İSKİ'de", "İSKİ'den", "İSKİ'ye", "İSKİ'nin",
        "ASKİ'de", "ASKİ'den", "ASKİ'ye", "ASKİ'nin",
        "İZSU'da", "İZSU'dan", "İZSU'ya", "İZSU'nun",
        " ÇAYKUR'da".strip(), "ÇAYKUR'dan", "ÇAYKUR'a", "ÇAYKUR'un",
        "İŞKUR'da", "İŞKUR'dan", "İŞKUR'a", "İŞKUR'un",
        "TÜRKPATENT'te", "TÜRKPATENT'e", "TÜRKPATENT'in",
        "TÜRKSOY'da", "TÜRKSOY'dan", "TÜRKSOY'a", "TÜRKSOY'un",
        "TÜRKSAT'ta", "TÜRKSAT'tan", "TÜRKSAT'a", "TÜRKSAT'ın",
        "TÜमोSAN".replace("मो", "MO") + "'da",
        # Units & lower/mixed abbreviations
        "TL'lik", "TL'ye", "TL'den", "TL'de", "TL'nin", "TL'si",
        "cm'lik", "cm'ye", "cm'den", "cm'de", "cm'nin",
        "mm'lik", "mm'ye", "mm'den", "mm'de",
        "km'lik", "km'ye", "km'den", "km'de",
        "kg'lık", "kg'a", "kg'dan", "kg'da", "kg'ın",
        "gr'lık", "gr'a", "gr'dan", "gr'da",
        "mg'lık", "mg'a", "mg'dan",
        "GB'lık", "GB'ı", "GB'a", "GB'ta", "GB'tan",
        "MB'lık", "MB'ı", "MB'a", "MB'ta", "MB'tan",
        "TB'lık", "TB'ı", "TB'a",
        # Tech brands & Proper names
        "iPhone'u", "iPhone'a", "iPhone'da", "iPhone'dan", "iPhone'un", "iPhone'lar",
        "iPad'i", "iPad'e", "iPad'de", "iPad'den", "iPad'in",
        "YouTube'da", "YouTube'dan", "YouTube'a", "YouTube'u", "YouTube'un",
        "WhatsApp'ta", "WhatsApp'tan", "WhatsApp'a", "WhatsApp'ı", "WhatsApp'ın",
        "Google'da", "Google'dan", "Google'a", "Google'ı", "Google'ın",
        "Twitter'da", "Twitter'dan", "Twitter'a", "Twitter'ı", "Twitter'ın",
        "Instagram'da", "Instagram'dan", "Instagram'a", "Instagram'ı", "Instagram'ın",
        "Facebook'ta", "Facebook'tan", "Facebook'a", "Facebook'u", "Facebook'un",
        "Microsoft'ta", "Microsoft'tan", "Microsoft'a", "Microsoft'un",
        "Linux'ta", "Linux'tan", "Linux'a", "Linux'u", "Linux'un",
        "Windows'ta", "Windows'tan", "Windows'a", "Windows'u", "Windows'un",
        "Android'de", "Android'den", "Android'e", "Android'i", "Android'in",
        # Turkish geographical/historical/compound proper names
        "İstanbul'da", "İstanbul'dan", "İstanbul'a", "İstanbul'u", "İstanbul'un", "İstanbullu",
        "Ankara'da", "Ankara'dan", "Ankara'ya", "Ankara'yı", "Ankara'nın", "Ankaralı",
        "İzmir'de", "İzmir'den", "İzmir'e", "İzmir'i", "İzmir'in", "İzmirli",
        "Çanakkale'de", "Çanakkale'den", "Çanakkale'ye", "Çanakkale'nin",
        "Boğaziçi'nde", "Boğaziçi'nden", "Boğaziçi'ne", "Boğaziçi'nin", "Boğaziçi'ni",
        "Rumeli'de", "Rumeli'den", "Rumeli'ye", "Rumeli'nin",
        " Kadıköy'de".strip(), "Kadıköy'den", "Kadıköy'e", "Kadıköy'ün",
        "Atatürk'te", "Atatürk'ten", "Atatürk'e", "Atatürk'ü", "Atatürk'ün",
    ]
    rejected_gold = check_words_batch(gold_tests)
    print(f"\nGold test battery: {len(gold_tests) - len(rejected_gold)}/{len(gold_tests)} passed ({len(rejected_gold)} rejected)")
    for w in gold_tests:
        if w in rejected_gold:
            base = w.split("'")[0]
            print(f"  REJECTED: {w:20s} [base in dic={base in dic_map}, flags={dic_map.get(base, '')!r}]")


if __name__ == "__main__":
    main()
