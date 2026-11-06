import os
import shutil
import subprocess
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class NativeHunspellAdapter:
    def __init__(self, dict_path: str):
        self.dict_path = dict_path
        winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
        for root, _, files in os.walk(winget_pkg_dir):
            if "hunspell.exe" in files and root not in os.environ.get("PATH", ""):
                os.environ["PATH"] = root + os.pathsep + os.environ.get("PATH", "")
                break
        self.bin = shutil.which("hunspell")
        if not self.bin:
            raise RuntimeError("hunspell binary not found in PATH")

    def lookup_batch(self, words: list[str]) -> set[str]:
        p = subprocess.run(
            [self.bin, "-d", self.dict_path, "-l"],
            input="\n".join(words) + "\n",
            text=True,
            capture_output=True,
            encoding="utf-8",
        )
        return set(line.strip() for line in p.stdout.splitlines() if line.strip())


def evaluate_test_set(d, name, correct_words, misspelled_words):
    print(f"\n{'='*70}")
    print(f"EVALUATING: {name}")
    print(f"{'='*70}")

    if hasattr(d, "lookup_batch"):
        flagged_clean = d.lookup_batch(correct_words)
        fp_words = [w for w in correct_words if w in flagged_clean]
        flagged_typos = d.lookup_batch(misspelled_words)
        fn_words = [w for w in misspelled_words if w not in flagged_typos]
    else:
        fp_words = [w for w in correct_words if not d.lookup(w)]
        fn_words = [w for w in misspelled_words if d.lookup(w)]

    total_clean = len(correct_words)
    clean_correct = total_clean - len(fp_words)
    precision = (clean_correct / total_clean * 100) if total_clean else 100.0

    print(f"--- Precision (Clean Words) ---")
    print(f"  Total Clean Words: {total_clean:,}")
    print(f"  Correctly Recognized: {clean_correct:,} ({precision:.2f}%)")
    print(f"  False Positives (Valid words flagged as error): {len(fp_words):,}")
    if fp_words:
        print(f"  Sample FPs: {fp_words[:10]}")

    total_typos = len(misspelled_words)
    typos_detected = total_typos - len(fn_words)
    recall = (typos_detected / total_typos * 100) if total_typos else 100.0

    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    print(f"\n--- Recall (Misspelled Words) ---")
    print(f"  Total Misspelled Words: {total_typos:,}")
    print(f"  Correctly Flagged: {typos_detected:,} ({recall:.2f}%)")
    print(f"  False Negatives (Missed typos): {len(fn_words):,}")
    if fn_words:
        print(f"  Sample FNs: {fn_words[:10]}")

    print(f"\n--- Overall Detection F1-Score: {f1:.2f}% ---")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Loading Turkspell Hunspell dictionary...")
    start_t = time.time()
    dict_base = os.path.join(base_dir, 'tr')
    d = NativeHunspellAdapter(dict_base)
    print(f"Dictionary loaded in {time.time() - start_t:.2f}s")

    sample_correct = [
        "akıllanmıyorsun", "aldatmışsın", "alıyorlarmış", "başkaldırıyorum",
        "durduramazdık", "gülüyordum", "öğretiyorlardı", "inandıklarımızın",
        "izliyorlardı", "kurtaramayacağız", "rüzgâr", "kâğıt", "hikâye", "hükûmet",
        "ayrılamadığına", "konuşabiliyorlar", "temizlemiyorum", "şakalaşıyorlar",
        "çalıştırabiliyorsunuz", "seviştiklerinde", "tanımadığımızı", "yıkıldıklarını",
        "yayımlanmışsa", "yayınlanamayacak", "zenginleştirdiğine", "özelleşmesi"
    ]

    sample_misspelled = [
        "aalizindeki", "aamıyorsak", "abartırsı", "hikaye", "ruzgar",
        "Computer", "0azarlar", "b3klediğinizden", "4ejim", "Strong", "Chocolate"
    ]

    evaluate_test_set(d, "Turkspell Core Linguistic Regression Suite", sample_correct, sample_misspelled)


if __name__ == '__main__':
    main()
