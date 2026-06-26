"""
Fast batch validation for tr_v2.aff — uses a single hunspell -l call with all test words.
"""
import io
import sys
import subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = Path(r'c:\gemini\turkspell')
AFF  = BASE / 'tr.aff'

sys.path.append(str(BASE))
import generate_grammar_rules as gen

ev_chain = gen.get_noun_chain("F1")
kitap_chain = gen.get_noun_chain("V1")
araba_chain = gen.get_noun_chain("B3")
kutu_chain = gen.get_noun_chain("B4")
göz_chain = gen.get_noun_chain("F2")
kedi_chain = gen.get_noun_chain("F3")
köprü_chain = gen.get_noun_chain("F4")

SIMPLIFIED_DIC = f"""11
ev/{ev_chain}
kitap/{kitap_chain}
araba/{araba_chain}
kutu/{kutu_chain}
göz/{göz_chain}
kedi/{kedi_chain}
köprü/{köprü_chain}
yazmak/VB
gelmek/VF
okumak/VR
görmek/VG
"""

TESTS = [
    # (word, expected_valid, description)
    ('ev',          True,  'bare stem'),
    ('evi',         True,  'AC: accusative front unrounded'),
    ('eve',         True,  'DA: dative front'),
    ('evde',        True,  'LO: locative voiced'),
    ('evden',       True,  'AB: ablative'),
    ('evin',        True,  'GE: genitive'),
    ('evle',        True,  'IN: instrumental'),
    ('evler',       True,  'PF: plural front'),
    ('evlere',      True,  'PF: plural dative'),
    ('evlerde',     True,  'PF: plural locative'),
    ('evlerden',    True,  'PF: plural ablative'),
    ('evlerin',     True,  'PF: plural genitive'),
    ('evlerle',     True,  'PF: plural instrumental'),
    ('evine',       True,  'P3: 3sg poss dative'),
    ('evinde',      True,  'P3: 3sg poss locative'),
    ('evinden',     True,  'P3: 3sg poss ablative'),
    ('evinin',      True,  'P3: 3sg poss genitive'),
    ('eviyle',      True,  'P3: 3sg poss instrumental'),
    ('evimde',      True,  'P1: 1sg poss locative'),
    ('evimin',      True,  'P1: 1sg poss genitive'),
    ('evimize',     True,  'PM: 1pl poss dative'),
    ('eviniz',      True,  'P5: 2sg poss'),
    ('evdir',       True,  'CL: copula -dir'),
    ('evdi',        True,  'CL: copula past -di'),
    ('evmiş',       True,  'CL: copula narrative'),
    ('evse',        True,  'CL: copula conditional'),
    ('evken',       True,  'CL: copula adverbial -ken'),
    # back consonant voicing
    ('kitap',       True,  'bare stem back voicing'),
    ('kitabı',      True,  'AC: accusative voicing p->b'),
    ('kitaba',      True,  'DA: dative voicing'),
    ('kitapta',     True,  'LO: locative unvoiced'),
    ('kitaptan',    True,  'AB: ablative unvoiced'),
    ('kitabın',     True,  'GE: genitive voicing'),
    ('kitapla',     True,  'IN: instrumental'),
    ('kitaplar',    True,  'PB: plural back'),
    ('kitaplarda',  True,  'PB: plural locative'),
    ('kitaplardan', True,  'PB: plural ablative'),
    ('kitapların',  True,  'PB: plural genitive'),
    ('kitabının',   True,  'P3: 3sg poss gen back voicing'),
    # back vowel-ending
    ('araba',       True,  'bare stem back vowel'),
    ('arabayı',     True,  'AC: accusative back vowel y-buffer'),
    ('arabaya',     True,  'DA: dative back vowel y-buffer'),
    ('arabada',     True,  'LO: locative back vowel nda'),
    ('arabadan',    True,  'AB: ablative back vowel'),
    ('arabanın',    True,  'GE: genitive back vowel'),
    ('arabayla',    True,  'IN: instrumental back vowel'),
    ('arabalar',    True,  'PB: plural back vowel'),
    # verbs
    ('yazmak',      True,  'VB: verb infinitive'),
    ('yazdı',       True,  'VB: past tense'),
    ('yazıyor',     True,  'VB: present continuous'),
    ('yazacak',     True,  'VB: future'),
    ('yazar',       True,  'VB: aorist'),
    ('yazabilir',   True,  'VB: capability aorist'),
    ('gelmek',      True,  'VF: front verb infinitive'),
    ('geldi',       True,  'VF: past'),
    ('geliyor',     True,  'VF: present continuous'),
    # negatives (must be INVALID)
    ('evta',        False, 'invalid: front + -ta locative'),
    ('evlar',       False, 'invalid: front + back plural'),
    ('kitaplerden', False, 'invalid: back + front plural ablative'),
    ('xyz',         False, 'unknown word'),
]


def write_test_files():
    """Write test.aff and test.dic."""
    test_aff = BASE / 'tr_v2_test.aff'
    test_dic = BASE / 'tr_v2_test.dic'

    with open(AFF, encoding='utf-8') as f:
        aff_content = f.read()
    with open(test_aff, 'w', encoding='utf-8', newline='\n') as f:
        f.write(aff_content)
    with open(test_dic, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SIMPLIFIED_DIC)

    return str(BASE / 'tr_v2_test')


def run_batch_check(words: list[str], dic_base: str) -> set[str]:
    """Run hunspell -l on all words at once. Returns set of UNKNOWN words."""
    word_input = '\n'.join(words) + '\n'
    result = subprocess.run(
        ['hunspell', '-d', dic_base, '-l'],
        input=word_input,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=60
    )
    unknown = set(result.stdout.strip().split('\n'))
    return {w for w in unknown if w}


def run_validation():
    print('Writing test files...')
    dic_base = write_test_files()

    all_words = [word for word, _, _ in TESTS]
    print(f'Running batch hunspell check on {len(all_words)} words...')
    unknown = run_batch_check(all_words, dic_base)

    passed = failed = 0
    print(f"\n{'Word':<22} {'Expected':<10} {'Got':<10} {'Result':<8} {'Note'}")
    print('-' * 95)

    for word, expected_valid, desc in TESTS:
        actual_valid = word not in unknown
        ok = actual_valid == expected_valid
        status = 'PASS' if ok else 'FAIL'
        print(f'{word:<22} {"valid" if expected_valid else "invalid":<10} {"valid" if actual_valid else "invalid":<10} {status:<8} {desc}')
        if ok:
            passed += 1
        else:
            failed += 1

    print()
    print(f'Results: {passed} passed, {failed} failed')
    if failed == 0:
        print('VALIDATION PASSED')
    else:
        print(f'VALIDATION: {failed} failures')


if __name__ == '__main__':
    run_validation()
