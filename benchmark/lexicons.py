# -*- coding: utf-8 -*-
"""Turkish-aware lexicon loading utilities for the benchmark."""
HATS = str.maketrans("âîûÂÎÛ", "aiuAIU")


def tlc(s: str) -> str:
    """Turkish-aware lowercase (I->ı, İ->i)."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def _strip_head(line: str) -> str:
    """Strip Hunspell flags and whitespace: 'ekmek/N1' -> 'ekmek'."""
    return line.split("/")[0].strip()


def load_authority_set(paths) -> set:
    """Load wordlist(s); strip flags; Turkish-lowercase. Returns a flat set."""
    out = set()
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                head = _strip_head(line)
                if head:
                    out.add(tlc(head))
    return out


def load_authority_index(paths) -> dict:
    """Load wordlist(s) into a hat-aware index.

    Returns dict with:
      exact           - every entry exactly as listed, Turkish-lowercased
      hatted          - entries containing â/î/û (hatted spellings)
      dehatted_aliases- ASCII-folded forms of hatted entries. These are NOT
                        sanctioned spellings; they exist so we can DETECT an
                        input like 'neftilesmek' as a hatted-only variant.
    """
    exact = set()
    hatted = set()
    dehatted_aliases = set()
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                head = _strip_head(line)
                if not head:
                    continue
                low = tlc(head)
                exact.add(low)
                if any(c in low for c in "âîû"):
                    hatted.add(low)
                    dehatted_aliases.add(low.translate(HATS))
    return {"exact": exact, "hatted": hatted, "dehatted_aliases": dehatted_aliases}
