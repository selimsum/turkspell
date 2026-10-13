import subprocess
import sys
from pathlib import Path

ROOT = Path(r"c:\gemini\turkspell")
HUNSPELL = "hunspell"

PROFILES = {
    "universal": str(ROOT / "dist" / "turkspell-universal" / "tr"),
    "tdk": str(ROOT / "dist" / "turkspell-tdk" / "tr"),
    "dd": str(ROOT / "dist" / "turkspell-dd" / "tr"),
}

# Pillar 1: Valid standalone question particles, bound -ki forms, and locative copulas
VALID_FORMS = [
    # Standalone question particles (mı/mi/mu/mü + person & copula inflections)
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
    # Valid bound -ki forms (pronouns, time adverbs, locative -daki/-deki, lexicalized SOMBAHÇEMİ)
    "benimki", "seninki", "onunki", "bizimki", "sizinki", "onlarınki",
    "benimkiler", "bizimkilerde", "seninkini", "onunkinden",
    "dünkü", "dünkünden", "bugünkü", "bugünküler", "yarınki", "yarınkini",
    "önceki", "öncekilerden", "sonraki", "sonrakilere", "şimdiki", "şimdikiler",
    "evdeki", "evdekiler", "okuldaki", "okuldakiler",
    "buradaki", "oradaki", "neredeki", "içindeki", "üzerindeki", "nezdindeki",
    "sanki", "oysaki", "mademki", "belki", "hâlbuki", "çünkü", "meğerki", "illaki",
    # Valid locative copula & plural forms
    "buradayım", "buradasın", "buradadır", "buradayız", "buradasınız", "buradalar", "buradaydı",
    "neredeyim", "neredesin", "nerededir", "neredeyiz", "neredesiniz", "neredeler", "neredeydi",
    "içindedir", "üzerindedir", "yanındadır",
]

# Pillar 2: Joined question particle typos -> Top-1 spaced suggestion
JOINED_QUESTION_TYPOS = [
    ("geldimi", "geldi mi"),
    ("gittimi", "gitti mi"),
    ("oldumu", "oldu mu"),
    ("aldımı", "aldı mı"),
    ("verdimi", "verdi mi"),
    ("baktımı", "baktı mı"),
    ("yaptımı", "yaptı mı"),
    ("kaldımı", "kaldı mı"),
    ("geldinmi", "geldin mi"),
    ("gittinmi", "gittin mi"),
    ("oldunmu", "oldun mu"),
    ("aldınmı", "aldın mı"),
    ("gördünmü", "gördün mü"),
    ("duydunmu", "duydun mu"),
    ("anladınmı", "anladın mı"),
    ("geliyormu", "geliyor mu"),
    ("gidiyormu", "gidiyor mu"),
    ("oluyormu", "oluyor mu"),
    ("yapıyormu", "yapıyor mu"),
    ("biliyormu", "biliyor mu"),
    ("istiyormu", "istiyor mu"),
    ("geliyormusun", "geliyor musun"),
    ("biliyormusun", "biliyor musun"),
    ("istiyormusun", "istiyor musun"),
    ("yapıyormusun", "yapıyor musun"),
    ("bakıyormusun", "bakıyor musun"),
    ("biliyormusunuz", "biliyor musunuz"),
    ("istiyormusunuz", "istiyor musunuz"),
    ("gelirmisin", "gelir misin"),
    ("yaparmısın", "yapar mısın"),
    ("yaparmısınız", "yapar mısınız"),
    ("olurmu", "olur mu"),
    ("olmazmı", "olmaz mı"),
    ("istermisin", "ister misin"),
    ("istermisiniz", "ister misiniz"),
    ("edermisin", "eder misin"),
    ("gelecekmisin", "gelecek misin"),
    ("yapacakmısın", "yapacak mısın"),
    ("olacakmı", "olacak mı"),
    ("gidecekmisin", "gidecek misin"),
    ("geleyimmi", "geleyim mi"),
    ("yapayımmı", "yapayım mı"),
    ("gidelimmi", "gidelim mi"),
    ("yapalımmı", "yapalım mı"),
    ("varmı", "var mı"),
    ("varmıydı", "var mıydı"),
    ("varmıdır", "var mıdır"),
    ("varmıymış", "var mıymış"),
    ("yokmu", "yok mu"),
    ("yokmuydu", "yok muydu"),
    ("yokmudur", "yok mudur"),
    ("yokmuymuş", "yok muymuş"),
    ("değilmi", "değil mi"),
    ("değilmiydi", "değil miydi"),
    ("değilmidir", "değil midir"),
    ("değilmiymiş", "değil miymiş"),
    ("güzelmi", "güzel mi"),
    ("iyimi", "iyi mi"),
    ("iyimisin", "iyi misin"),
    ("iyimisiniz", "iyi misiniz"),
    ("tamammı", "tamam mı"),
    ("doğrumu", "doğru mu"),
    ("yanlışmı", "yanlış mı"),
    ("mümkünmü", "mümkün mü"),
    ("şartmı", "şart mı"),
    ("kolaymı", "kolay mı"),
    ("zormu", "zor mu"),
]

# Pillar 3: Joined conjunction da/de typos -> Top-1 spaced suggestion
JOINED_DADE_TYPOS = [
    ("değilde", "değil de"),
    ("isede", "ise de"),
    ("vede", "ve de"),
    ("amada", "ama da"),
    ("ancakda", "ancak da"),
    ("fakatda", "fakat da"),
    ("hattada", "hatta da"),
    ("yinede", "yine de"),
    ("genede", "gene de"),
    ("belkide", "belki de"),
    ("sankide", "sanki de"),
    ("çünküde", "çünkü de"),
    ("bilede", "bile de"),
    ("zatende", "zaten de"),
    ("hiçde", "hiç de"),
    ("hiçte", "hiç de"),
    ("pekde", "pek de"),
    ("pekte", "pek de"),
    ("çokda", "çok da"),
    ("hemde", "hem de"),
    ("yada", "ya da"),
    ("bencede", "bence de"),
    ("sencede", "sence de"),
    ("bizcede", "bizce de"),
    ("sizcede", "sizce de"),
    ("gelsede", "gelse de"),
    ("yapsada", "yapsa da"),
    ("olsada", "olsa da"),
    ("olursada", "olursa da"),
    ("istersede", "isterse de"),
    ("bilsede", "bilse de"),
    ("görsede", "görse de"),
    ("gitsede", "gitse de"),
    ("gelsekde", "gelsek de"),
    ("yapsakda", "yapsak da"),
    ("olsamda", "olsam da"),
    ("bilsemde", "bilsem de"),
    ("görsemde", "görsem de"),
    ("istesemde", "istesem de"),
    ("geldimde", "geldim de"),
    ("gittimde", "gittim de"),
    ("yaptımda", "yaptım da"),
    ("baktımda", "baktım da"),
    ("aldımda", "aldım da"),
    ("gördümde", "gördüm de"),
    ("dedimde", "dedim de"),
    ("evdede", "evde de"),
    ("okuldada", "okulda da"),
    ("buradada", "burada da"),
    ("oradada", "orada da"),
    ("şuradada", "şurada da"),
    ("neredede", "nerede de"),
    ("bendede", "bende de"),
    ("sendede", "sende de"),
    ("bizdede", "bizde de"),
    ("sizdede", "sizde de"),
    ("aslındada", "aslında da"),
    ("sonundada", "sonunda da"),
    ("içindede", "içinde de"),
    ("üzerindede", "üzerinde de"),
    ("yanındada", "yanında da"),
    ("hakkındada", "hakkında da"),
    ("arasındada", "arasında da"),
    ("sayesindede", "sayesinde de"),
]

# Pillar 4: Joined conjunction ki typos -> Top-1 spaced suggestion
JOINED_KI_TYPOS = [
    ("biliyorumki", "biliyorum ki"),
    ("diyorumki", "diyorum ki"),
    ("anladımki", "anladım ki"),
    ("gördümki", "gördüm ki"),
    ("baktımki", "baktım ki"),
    ("sanırımki", "sanırım ki"),
    ("umarımki", "umarım ki"),
    ("olurki", "olur ki"),
    ("olduki", "oldu ki"),
    ("dediki", "dedi ki"),
    ("demişki", "demiş ki"),
    ("biliyorsunki", "biliyorsun ki"),
    ("görüyorsunki", "görüyorsun ki"),
    ("inanıyorumki", "inanıyorum ki"),
    ("düşünüyorumki", "düşünüyorum ki"),
    ("unutmayalımki", "unutmayalım ki"),
    ("varsayalımki", "varsayalım ki"),
    ("tutki", "tut ki"),
    ("yeterki", "yeter ki"),
    ("bilmemki", "bilmem ki"),
    ("nedendirki", "nedendir ki"),
    ("olmazki", "olmaz ki"),
    ("gelmezki", "gelmez ki"),
    ("diyorki", "diyor ki"),
    ("geliyorki", "geliyor ki"),
    ("olacakki", "olacak ki"),
    ("gelecekki", "gelecek ki"),
    ("nasılki", "nasıl ki"),
    ("öyleki", "öyle ki"),
    ("şöyleki", "şöyle ki"),
    ("böyleki", "böyle ki"),
    ("demekki", "demek ki"),
    ("kaldıki", "kaldı ki"),
    ("iyiki", "iyi ki"),
    ("tabiki", "tabii ki"),
    ("tabiiki", "tabii ki"),
    ("belliki", "belli ki"),
    ("şüphesizki", "şüphesiz ki"),
    ("elbetteki", "elbette ki"),
    ("gerçiki", "gerçi ki"),
    ("neyseki", "neyse ki"),
    ("keşkeki", "keşke ki"),
    ("zatenki", "zaten ki"),
]


def query_hunspell(dic_path: str, words: list[str]) -> list[tuple[bool, list[str]]]:
    p = subprocess.run(
        [str(HUNSPELL), "-d", dic_path],
        input="\n".join(words) + "\n",
        text=True,
         encoding="utf-8",
        capture_output=True,
    )
    lines = [l for l in p.stdout.splitlines()[1:] if l.strip()]
    results = []
    for l in lines:
        if l.startswith(("*", "+", "-")):
            results.append((True, []))
        elif l.startswith("&"):
            sugs = [s.strip() for s in l.split(": ", 1)[1].split(",")]
            results.append((False, sugs))
        else:
            results.append((False, []))
    return results


def audit_pillar_rejection(dic_path: str, pairs: list[tuple[str, str]]) -> tuple[int, int, list[str]]:
    words = [w for w, _ in pairs]
    res = query_hunspell(dic_path, words)
    rej_ok = 0
    top1_ok = 0
    failures = []
    for (w, expected), (accepted, sugs) in zip(pairs, res):
        if not accepted:
            rej_ok += 1
        top1 = sugs[0] if sugs else None
        if not accepted and top1 == expected:
            top1_ok += 1
        else:
            failures.append(f"  {w:18s} -> accepted={accepted}, top1={top1!r} (expected {expected!r})")
    return rej_ok, top1_ok, failures


def main() -> int:
    overall_ok = True
    print("=" * 78)
    print("TURKSPELL CLITICS, PARTICLES & CONJUNCTIONS AUDIT (mı/mi/mu/mü, da/de, ki)")
    print("=" * 78)

    for prof_name, dic_path in PROFILES.items():
        print(f"\n--- Profile: [{prof_name.upper()}] ---")

        # Pillar 1: Valid forms
        res_valid = query_hunspell(dic_path, VALID_FORMS)
        valid_ok = sum(1 for acc, _ in res_valid if acc)
        print(f"  1. Valid Standalone Particles & Bound -ki : {valid_ok}/{len(VALID_FORMS)} ({100.0*valid_ok/len(VALID_FORMS):.1f}%)")
        if valid_ok < len(VALID_FORMS):
            overall_ok = False
            for w, (acc, sugs) in zip(VALID_FORMS, res_valid):
                if not acc:
                    print(f"     [REJECTED VALID] {w} -> {sugs[:3]}")

        # Pillar 2: Joined Question Particles
        q_rej, q_top1, q_fails = audit_pillar_rejection(dic_path, JOINED_QUESTION_TYPOS)
        print(f"  2. Joined Question Particles (mı/mısın)   : Rej {q_rej}/{len(JOINED_QUESTION_TYPOS)} | Top-1 {q_top1}/{len(JOINED_QUESTION_TYPOS)} ({100.0*q_top1/len(JOINED_QUESTION_TYPOS):.1f}%)")
        if q_fails:
            overall_ok = False
            for f in q_fails:
                print("    ", f)

        # Pillar 3: Joined Conjunction da/de
        d_rej, d_top1, d_fails = audit_pillar_rejection(dic_path, JOINED_DADE_TYPOS)
        print(f"  3. Joined Conjunction da/de               : Rej {d_rej}/{len(JOINED_DADE_TYPOS)} | Top-1 {d_top1}/{len(JOINED_DADE_TYPOS)} ({100.0*d_top1/len(JOINED_DADE_TYPOS):.1f}%)")
        if d_fails:
            overall_ok = False
            for f in d_fails:
                print("    ", f)

        # Pillar 4: Joined Conjunction ki
        k_rej, k_top1, k_fails = audit_pillar_rejection(dic_path, JOINED_KI_TYPOS)
        print(f"  4. Joined Conjunction ki                  : Rej {k_rej}/{len(JOINED_KI_TYPOS)} | Top-1 {k_top1}/{len(JOINED_KI_TYPOS)} ({100.0*k_top1/len(JOINED_KI_TYPOS):.1f}%)")
        if k_fails:
            overall_ok = False
            for f in k_fails:
                print("    ", f)

    print("\n" + "=" * 78)
    if overall_ok:
        print("ALL CLITIC & PARTICLE AUDITS PASSED AT 100% ACROSS ALL 3 PROFILES!")
        return 0
    else:
        print("SOME CLITIC & PARTICLE AUDITS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
