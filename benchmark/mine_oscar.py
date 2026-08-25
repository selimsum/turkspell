# -*- coding: utf-8 -*-
"""Mine genuine spelling errors directly from raw OSCAR corpus frequencies,
independent of this repository's curation (rejected_words.csv).

A candidate is a GENUINE error iff:
  - it is frequent in the raw OSCAR web-crawl frequency table
  - Turkish alphabetic, len>=3
  - not an authority word / de-hatted alias
  - not in any competitor dictionary (collision filter)
  - Zemberek morphology finds NO analysis -> not a valid inflected form

Output: benchmark/oscar_real_errors.json as [[word, freq], ...]
"""
import json
import logging
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark import config
from benchmark.lexicons import tlc, load_authority_index
from benchmark.collision_filter import CollisionFilter


def main(target=4000, max_scan=None):
    from zemberek import TurkishMorphology
    logging.getLogger("zemberek").setLevel(logging.ERROR)
    morph = TurkishMorphology.create_with_defaults()

    with open(os.path.join(config.RAW, "oscar_10m_corpus_frequencies.json"),
              encoding="utf-8") as f:
        oscar = json.load(f)

    idx = load_authority_index(config.AUTHORITY_FILES)
    blocked = idx["exact"] | idx["dehatted_aliases"]
    cf = CollisionFilter()
    universe = cf.universe | blocked

    tur = re.compile(r"^[a-zçğıöşüâîû]+$")

    candidates = []
    for w, f in oscar.items():
        w2 = tlc(w.strip())
        if len(w2) < 3 or not tur.match(w2):
            continue
        if w2 in universe:
            continue
        candidates.append((w2, f))
    candidates.sort(key=lambda x: -x[1])
    print(f"pre-filter candidates: {len(candidates)}", flush=True)

    rows = []
    checked = 0
    for w, f in candidates:
        if len(rows) >= target:
            break
        if max_scan and checked >= max_scan:
            break
        checked += 1
        analyses = morph.analyze(w)
        ok = any(a.item.secondary_pos is None or
                 a.item.secondary_pos.short_form != "Prop"
                 for a in analyses)
        if not ok:
            rows.append([w, f])
        if checked % 5000 == 0:
            print(f"checked {checked}, found {len(rows)}", flush=True)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "oscar_real_errors.json")
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(rows, out, ensure_ascii=False)
    print(f"DONE: {len(rows)} genuine errors from {checked} checked", flush=True)


if __name__ == "__main__":
    tgt = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    scan = int(sys.argv[2]) if len(sys.argv) > 2 else None
    main(tgt, scan)
