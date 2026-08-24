# -*- coding: utf-8 -*-
"""Deterministic typo mutation engines for benchmark generation.

Three families of realistic Turkish typos:
  keyboard   - adjacent-key substitutions on the Turkish QWERTY layout
  diacritic  - ASCII-typing collapses (ş->s, ğ->g, ı->i, ö->o, ü->u, ç->c)
  phonetic   - metathesis, silent-ğ deletion, suffix vowel reduction

Each mutator returns (input, gold, note) or None if no mutation is possible.
All are deterministic given the passed random.Random instance.
"""
import re

# --- Turkish QWERTY adjacency rows (matches tr.aff KEY groups, lowercase) ---
_ROWS = [
    "qwertyuıopğü",
    "asdfghjklşi",
    "zxcvbnmçö",
]
KEY_NEIGHBORS = {}
for _row in _ROWS:
    for _i, _ch in enumerate(_row):
        _nbrs = []
        if _i > 0:
            _nbrs.append(_row[_i - 1])
        if _i < len(_row) - 1:
            _nbrs.append(_row[_i + 1])
        # vertical neighbors: same index in row above/below when exists
        KEY_NEIGHBORS.setdefault(_ch, set()).update(_nbrs)

for _ri in range(len(_ROWS) - 1):
    _upper, _lower = _ROWS[_ri], _ROWS[_ri + 1]
    for _i, _ch in enumerate(_upper):
        for _j in (_i - 1, _i, _i + 1):
            if 0 <= _j < len(_lower):
                KEY_NEIGHBORS[_ch].add(_lower[_j])
                KEY_NEIGHBORS.setdefault(_lower[_j], set()).add(_ch)

# --- ASCII-typing folds ---
DIACRITIC_FOLDS = {
    "ş": "s", "ğ": "g", "ç": "c", "ö": "o", "ü": "u", "ı": "i", "â": "a",
}

# --- Phonetic patterns (regex on word, replacement template) ---
_PHONETIC_PATTERNS = [
    # metathesis: nl <-> ln (yalnız -> yanlız class)
    (re.compile(r"^(.*)nl(.*)$"), r"\1ln\2", "metathesis-nl"),
    # silent ğ deletion between vowels (değil family is suffix-level; use ağız-like)
    (re.compile(r"^(.{1,})ğ([aeıioöuü])"), r"\1\2", "silent-gh-drop"),
    # future -acak/-ecek reduction: drop the linking vowel
    (re.compile(r"acak$"), "cak", "future-reduction"),
    (re.compile(r"ecek$"), "cek", "future-reduction"),
    (re.compile(r"acağ"), "cağ", "future-reduction"),
    (re.compile(r"eceğ"), "ceğ", "future-reduction"),
    # -iyor elision
    (re.compile(r"ıyor$"), "iyo", "iyor-elision"),
    (re.compile(r"iyor$"), "iyo", "iyor-elision"),
    (re.compile(r"uyor$"), "uyo", "iyor-elision"),
    (re.compile(r"üyor$"), "üyo", "iyor-elision"),
]


def mutate_keyboard(word: str, rng):
    """Substitute one character with a QWERTY-tr neighbor."""
    candidates = []
    for i, ch in enumerate(word.lower()):
        for nbr in KEY_NEIGHBORS.get(ch, ()):
            if nbr != ch:
                candidates.append((i, nbr))
    if not candidates:
        return None
    i, nbr = rng.choice(candidates)
    inp = word[:i] + nbr + word[i + 1:]
    if inp == word:
        return None
    return inp, word, f"key:{word[i]}->{nbr}"


def mutate_diacritic(word: str, rng):
    """Fold one diacritic character to its ASCII twin."""
    positions = [i for i, ch in enumerate(word.lower())
                 if ch in DIACRITIC_FOLDS]
    if not positions:
        return None
    i = rng.choice(positions)
    folded = DIACRITIC_FOLDS[word.lower()[i]]
    inp = word[:i] + folded + word[i + 1:]
    return inp, word, f"fold:{word[i]}->{folded}"


def mutate_phonetic(word: str, rng):
    """Apply one phonetic pattern (metathesis / ğ-drop / suffix reduction)."""
    low = word.lower()
    applicable = [(pat, repl, name) for pat, repl, name in _PHONETIC_PATTERNS
                  if pat.search(low)]
    if not applicable:
        return None
    pat, repl, name = rng.choice(applicable)
    inp = pat.sub(repl, low, count=1)
    if inp == low:
        return None
    return inp, low, name
