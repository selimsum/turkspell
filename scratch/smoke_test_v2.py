"""
Quick benchmark smoke test: check a set of real Turkish words against tr_v2.aff + tr_v2.dic.
Compare acceptance rate vs tr.aff + tr.dic.
"""
import subprocess
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Sample of real Turkish words (should be VALID in both old and new)
VALID_WORDS = """
ev evde evden evin evle evi eve
kitap kitabı kitaba kitapta kitaptan kitabın kitapla kitaplar kitaplarda kitaplardan
araba arabada arabadan arabanın arabayla arabalar
okul okulda okuldan okulun okullar okullarda
çocuk çocuğu çocuğa çocukta çocuktan çocuğun çocuklar
ülke ülkede ülkeden ülkenin ülkeler ülkelerde
güneş güneşte güneşten güneşin güneşler
yıldız yıldızda yıldızdan yıldızın yıldızlar
hava havada havadan havanın havalar
zaman zamanda zamandan zamanın zamanlar
insan insanda insandan insanın insanlar
para parada paradan paranın paralar
iş işte işten işin işler
yer yerde yerden yerin yerler
gün günde günden günün günler
su suda sudan suyun sular
yazmak yazdı yazıyor yazacak yazar yazmamalı yazabilir
gelmek geldi geliyor gelecek gelir gelmemeli gelebilir
okumak okudu okuyor okuyacak okur okuyabilir
görmek gördü görüyor görecek görür görebilir
""".strip().split()

# Also some INVALID words (should be rejected by both)
INVALID_WORDS = """xyz qrst abc123 evtar kitaplerden evlar""".split()

def check_batch(words, dic_base):
    """Run hunspell -l and return set of unknown words."""
    inp = '\n'.join(words) + '\n'
    result = subprocess.run(
        ['hunspell', '-d', dic_base, '-l'],
        input=inp, capture_output=True, text=True, encoding='utf-8', timeout=30
    )
    return {w.strip() for w in result.stdout.strip().split('\n') if w.strip()}

def run_smoke_test():
    print("=== Smoke Test: tr_v2.aff + tr_v2.dic ===\n")

    all_words = VALID_WORDS + INVALID_WORDS

    # Test old (v1)
    unknown_old = check_batch(all_words, 'tr_v1')
    # Test new (v2)
    unknown_new = check_batch(all_words, 'tr')

    # Valid words
    v1_accepted = [w for w in VALID_WORDS if w not in unknown_old]
    v2_accepted = [w for w in VALID_WORDS if w not in unknown_new]
    v1_rejected = [w for w in VALID_WORDS if w in unknown_old]
    v2_rejected = [w for w in VALID_WORDS if w in unknown_new]

    print(f"Valid words ({len(VALID_WORDS)} total):")
    print(f"  v1: {len(v1_accepted)}/{len(VALID_WORDS)} accepted ({len(v1_rejected)} missed)")
    print(f"  v2: {len(v2_accepted)}/{len(VALID_WORDS)} accepted ({len(v2_rejected)} missed)")

    if v2_rejected:
        print(f"\n  v2 MISSED (should be valid):")
        for w in v2_rejected[:20]:
            print(f"    {w}")

    # Invalid words (all should be rejected)
    v1_wrong_accept = [w for w in INVALID_WORDS if w not in unknown_old]
    v2_wrong_accept = [w for w in INVALID_WORDS if w not in unknown_new]

    print(f"\nInvalid words ({len(INVALID_WORDS)} total):")
    print(f"  v1: {len(INVALID_WORDS)-len(v1_wrong_accept)}/{len(INVALID_WORDS)} correctly rejected")
    print(f"  v2: {len(INVALID_WORDS)-len(v2_wrong_accept)}/{len(INVALID_WORDS)} correctly rejected")

    if v2_wrong_accept:
        print(f"\n  v2 WRONG ACCEPT (should be invalid): {v2_wrong_accept}")

    print()
    # Regression: words in v1 but not v2
    v1_only = set(v1_accepted) - set(v2_accepted)
    v2_only = set(v2_accepted) - set(v1_accepted)
    if v1_only:
        print(f"REGRESSION: {len(v1_only)} words accepted by v1 but NOT v2: {sorted(v1_only)[:10]}")
    if v2_only:
        print(f"IMPROVEMENT: {len(v2_only)} words accepted by v2 but NOT v1: {sorted(v2_only)[:10]}")
    if not v1_only and not v2_only:
        print("No regressions: v2 accepts same valid words as v1 ✓")

if __name__ == '__main__':
    run_smoke_test()
