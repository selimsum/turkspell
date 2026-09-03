"""Post-build sanity checks for tr.dic / tr.aff.

Exists because a path regression once shipped a dictionary missing 989 words
(all custom names and abbreviations) while the build still printed
"Compile complete!" and exited 0. These checks are the tripwire for that class
of failure: structural integrity plus a presence sample drawn from the source
lexicons, so a silently-dropped input fails the build instead of the release.

Run directly (python build/validate_build.py) or via compile_hunspell.py.
Exits non-zero on any error; warnings are reported but do not fail.
"""

import json
import os
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Floor, not a target — guards against a truncated or half-written dictionary.
MIN_ENTRIES = 90_000
MAX_ENTRIES = 200_000
# Fraction of sampled lexicon lemmas that must be present in tr.dic.
MIN_PRESENCE = 0.95


def _tlc(s: str) -> str:
    """Turkish lowercase (I->ı, İ->i)."""
    return s.replace('I', 'ı').replace('İ', 'i').lower()


def _load_dic(path):
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    declared = lines[0].strip()
    body = [l for l in lines[1:] if l.strip()]
    return declared, body


def check_dic(path, errors, warnings):
    declared, body = _load_dic(path)

    if not declared.isdigit():
        errors.append(f"tr.dic: first line must be an entry count, got {declared!r}")
    elif int(declared) != len(body):
        errors.append(
            f"tr.dic: header declares {declared} entries but file holds {len(body)}"
        )

    if len(body) < MIN_ENTRIES:
        errors.append(
            f"tr.dic: only {len(body):,} entries (floor is {MIN_ENTRIES:,}) - "
            f"an input lexicon was probably dropped"
        )
    elif len(body) > MAX_ENTRIES:
        warnings.append(f"tr.dic: {len(body):,} entries exceeds expected {MAX_ENTRIES:,}")

    # A second '/' means a slash leaked in from a source lemma, so Hunspell
    # parses the rest of the word as flag characters.
    malformed = [l for l in body if l.count('/') > 1]
    if malformed:
        errors.append(
            f"tr.dic: {len(malformed)} entries contain more than one '/' "
            f"(flags would be misparsed), e.g. {malformed[:3]}"
        )

    blank = [l for l in body if not l.split('/')[0].strip()]
    if blank:
        errors.append(f"tr.dic: {len(blank)} entries have an empty word form")

    dupes = sum(n - 1 for n in Counter(body).values() if n > 1)
    if dupes:
        warnings.append(f"tr.dic: {dupes:,} byte-identical duplicate lines")

    return body


def check_aff(path, errors, warnings):
    with open(path, encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f]

    header = {}
    for l in lines[:60]:
        p = l.split()
        if len(p) == 2 and p[0] in ('SET', 'FLAG', 'NOSUGGEST', 'KEEPCASE', 'NEEDAFFIX', 'LANG'):
            header[p[0]] = p[1]

    if header.get('SET') != 'UTF-8':
        errors.append(f"tr.aff: expected 'SET UTF-8', got {header.get('SET')!r}")
    if header.get('FLAG') != 'UTF-8':
        errors.append(
            f"tr.aff: expected 'FLAG UTF-8' after remap, got {header.get('FLAG')!r} - "
            f"the flag remap step did not run"
        )
    for key in ('NOSUGGEST', 'KEEPCASE', 'NEEDAFFIX'):
        val = header.get(key)
        if val is None:
            errors.append(f"tr.aff: missing {key} declaration")
        elif len(val) != 1:
            errors.append(
                f"tr.aff: {key} is {val!r}; under FLAG UTF-8 it must be a single character"
            )

    # Every SFX/PFX block header declares its rule count; a mismatch makes
    # Hunspell silently misparse the remainder of the block.
    mismatches = []
    cur = declared = count = None
    for l in lines:
        p = l.split()
        if len(p) >= 4 and p[0] in ('SFX', 'PFX') and p[2] in ('Y', 'N'):
            if cur is not None and declared != count:
                mismatches.append((cur, declared, count))
            cur, declared, count = p[1], int(p[3]), 0
        elif cur is not None and len(p) >= 3 and p[0] in ('SFX', 'PFX'):
            count += 1
    if cur is not None and declared != count:
        mismatches.append((cur, declared, count))

    if mismatches:
        errors.append(
            f"tr.aff: {len(mismatches)} affix blocks declare the wrong rule count, "
            f"e.g. {mismatches[:3]}"
        )

    rules = [
        l for l in lines
        if l.startswith(('SFX', 'PFX')) and len(l.split()) >= 4 and l.split()[2] not in ('Y', 'N')
    ]
    if not rules:
        errors.append("tr.aff: no affix rules found")
    dup = sum(n - 1 for n in Counter(rules).values() if n > 1)
    if dup:
        warnings.append(f"tr.aff: {dup:,} exactly duplicated affix rules ({dup / len(rules):.1%})")

    return header


def check_presence(body, errors, warnings):
    """Confirm each source lexicon actually reached the dictionary.

    This is the check that catches a silently-skipped input file.
    """
    forms = {l.split('/')[0] for l in body}
    folded = {_tlc(w) for w in forms}

    lex_dir = os.path.join(BASE_DIR, 'lexicons')
    for fname, label in (
        ('custom_names.json', 'custom names'),
        ('custom_abbreviations.json', 'custom abbreviations'),
    ):
        path = os.path.join(lex_dir, fname)
        if not os.path.exists(path):
            warnings.append(f"{fname} not found - skipping presence check")
            continue
        with open(path, encoding='utf-8') as f:
            entries = json.load(f)
        lemmas = [e['lemma'] for e in entries if isinstance(e, dict) and e.get('lemma')]
        if not lemmas:
            continue
        missing = [w for w in lemmas if w not in forms and _tlc(w) not in folded]
        rate = 1 - len(missing) / len(lemmas)
        if rate < MIN_PRESENCE:
            errors.append(
                f"only {rate:.1%} of {len(lemmas)} {label} reached tr.dic "
                f"(floor {MIN_PRESENCE:.0%}); {len(missing)} missing, "
                f"e.g. {missing[:5]} - the lexicon was probably not loaded"
            )
        elif missing:
            warnings.append(f"{len(missing)}/{len(lemmas)} {label} missing, e.g. {missing[:5]}")


def validate(dic_path='tr.dic', aff_path='tr.aff', verbose=True):
    """Validate a built dictionary pair. Returns (errors, warnings)."""
    errors, warnings = [], []

    for p in (dic_path, aff_path):
        if not os.path.exists(p):
            errors.append(f"{p} does not exist")
    if errors:
        return errors, warnings

    body = check_dic(dic_path, errors, warnings)
    check_aff(aff_path, errors, warnings)
    check_presence(body, errors, warnings)
    check_regression_tests(errors)

    if verbose:
        dic_mb = os.path.getsize(dic_path) / 1048576
        aff_mb = os.path.getsize(aff_path) / 1048576
        print(f"  tr.dic: {len(body):,} entries, {dic_mb:.2f} MB")
        print(f"  tr.aff: {aff_mb:.2f} MB")
        print(f"  total footprint: {dic_mb + aff_mb:.2f} MB")

    return errors, warnings


def check_regression_tests(errors):
    test_script = os.path.join(BASE_DIR, "tests", "test_morphology.py")
    if os.path.exists(test_script):
        import subprocess
        res = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "tests"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if res.returncode != 0:
            errors.append(f"Morphology regression tests failed:\n{res.stdout}\n{res.stderr}")
        else:
            print("  morphological regression tests: PASSED (100% OK)")


def main():
    dic = sys.argv[1] if len(sys.argv) > 1 else 'tr.dic'
    aff = sys.argv[2] if len(sys.argv) > 2 else 'tr.aff'

    print(f"Validating {dic} / {aff} ...")
    errors, warnings = validate(dic, aff)

    for w in warnings:
        print(f"  WARNING: {w}")
    for e in errors:
        print(f"  ERROR:   {e}")

    if errors:
        print(f"\nFAILED: {len(errors)} error(s), {len(warnings)} warning(s).")
        return 1
    print(f"\nOK: 0 errors, {len(warnings)} warning(s).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
