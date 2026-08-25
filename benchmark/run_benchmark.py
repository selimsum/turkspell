# -*- coding: utf-8 -*-
"""Evaluate Hunspell dictionaries against the Turkspell Benchmark V3 dataset.

Engine: hunspell CLI (C++, fast, matches Firefox's engine family) run in ONE
streaming process per dictionary. Fallback: spylls (slow, ~1 word/sec).

Metrics: detection precision/recall/F1, correction@1, correction@3 — overall
and per slice. Space-normalized comparison (so 'hersey -> her şey' counts).

Usage:
  python benchmark/run_benchmark.py                       # all dicts, full set
  python benchmark/run_benchmark.py --only tr --limit 100 # smoke test
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark import config

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def tlc(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def norm(s: str) -> str:
    """Case-fold + collapse all whitespace for fair suggestion matching."""
    return " ".join(tlc(s).split())


def find_dictionary_dirs() -> dict:
    """Return {display_name: dict_dir} for Turkspell + external dictionaries."""
    dirs = {"turkspell": config.BASE_DIR}
    ext = config.EXTERNAL_DICTS_DIR
    if os.path.isdir(ext):
        for name in sorted(os.listdir(ext)):
            sub = os.path.join(ext, name)
            if not os.path.isdir(sub):
                continue
            # dict dir = folder containing a .dic (possibly in dictionaries/)
            for root, _d, files in os.walk(sub):
                if any(f.endswith(".dic") for f in files):
                    dirs[name] = root
                    break
    return dirs


def load_dataset(limit=None):
    miss_path = os.path.join(config.OUTPUT_DIR, "bench_v3_misspelled.csv")
    clean_path = os.path.join(config.OUTPUT_DIR, "bench_v3_clean.csv")
    with open(miss_path, encoding="utf-8") as f:
        misspelled = list(csv.DictReader(f))
    with open(clean_path, encoding="utf-8") as f:
        clean = list(csv.DictReader(f))
    if limit:
        misspelled = misspelled[:limit]
        clean = clean[:limit]
    return clean, misspelled


def evaluate_hunspell_cli(dict_dir: str, words: list):
    """Run hunspell -a once over all words; return {word: [suggestions]}."""
    env = dict(os.environ)
    env.setdefault("DICPATH", "")
    p = subprocess.run(
        ["hunspell", "-d", dict_dir.rstrip("/\\").replace("\\", "/"), "-a"],
        input="\n".join(w["input"] for w in words) + "\n",
        text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    results = {}
    current = None
    for line in p.stdout.splitlines():
        if not line or line.startswith(("@", "*")):
            continue
        parts = line.split(":", 1)
        head = parts[0]
        fields = head.split()
        if line.startswith(("&", "?")) and len(fields) >= 2:
            current = fields[1]
            if "&" == line[0] and len(parts) > 1:
                sugs = [s.strip() for s in parts[1].split(",")]
                results.setdefault(current, sugs)
        elif line.startswith("+") or (current and line.strip() and not line[0].isdigit()):
            continue
    return results


def _dict_name(dict_dir: str) -> str:
    """hunspell -d needs <path>/<name> where <name>.aff/.dic exist.

    Turkspell's files live at repo root as tr.aff/tr.dic; external dicts may
    use another basename. Find it.
    """
    dd = dict_dir.replace("\\", "/").rstrip("/")
    for cand in ("tr", "tr_TR", "tur"):
        if os.path.exists(os.path.join(dd, cand + ".dic")):
            return f"{dd}/{cand}"
    # fall back: first .dic in the dir
    for fn in sorted(os.listdir(dd)):
        if fn.endswith(".dic"):
            return f"{dd}/{fn[:-4]}"
    raise FileNotFoundError(f"no .dic in {dict_dir}")


def evaluate(clean, misspelled, dict_dir):
    flagged_map = {}
    dname = _dict_name(dict_dir)

    # --- detection via single -l pass ---
    all_inputs = [w["input"] for w in clean] + [w["input"] for w in misspelled]
    p = subprocess.run(
        ["hunspell", "-d", dname, "-l"],
        input="\n".join(all_inputs) + "\n",
        text=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    if p.returncode != 0 and not p.stdout:
        raise RuntimeError(f"hunspell failed: {p.stderr[:200]}")
    flagged = set(l.strip() for l in p.stdout.splitlines() if l.strip())
    fp_words = [w for w in clean if w["input"] in flagged]

    # --- suggestions for flagged misspelled only ---
    to_suggest = [w for w in misspelled if w["input"] in flagged]
    sug_map = {}
    if to_suggest:
        chunks = [to_suggest[i:i+2000] for i in range(0, len(to_suggest), 2000)]
        for chunk in chunks:
            p = subprocess.run(
                ["hunspell", "-d", dname, "-a"],
                input="\n".join(w["input"] for w in chunk) + "\n",
                text=True, capture_output=True, encoding="utf-8",
                errors="replace",
            )
            for line in p.stdout.splitlines():
                if not line or line.startswith("@"):
                    continue
                if line.startswith("&"):
                    head, _, tail = line.partition(":")
                    word = head.split()[1]
                    sugs = [s.strip() for s in tail.split(",") if s.strip()]
                    sug_map.setdefault(word, sugs)
                elif line.startswith("?"):
                    word = line.split()[1]
                    sug_map.setdefault(word, [])


    total_clean = len(clean)
    fp = len(fp_words)
    precision = (total_clean - fp) / total_clean * 100 if total_clean else 100.0
    recall = len(flagged & {w["input"] for w in misspelled}) / len(misspelled) * 100

    corr1_ok = 0; corr3_ok = 0; corr_total = 0
    per_slice = {}
    for w in misspelled:
        if w["input"] not in flagged:
            continue
        corr_total += 1
        gold = norm(w["gold"]) if w["gold"] else None
        sugs = sug_map.get(w["input"], [])
        top = [norm(s) for s in sugs[:3]]
        hit1 = hit3 = False
        if gold is not None:
            hit1 = bool(top) and top[0] == gold
            hit3 = gold in top
        elif top:
            # corpus_real entries have no gold; count as corrected if ANY
            # suggestion differs from input (weak signal, noted in output)
            hit1 = top[0] != norm(w["input"])
        corr1_ok += hit1; corr3_ok += hit3
        sl = w["slice"]
        st = per_slice.setdefault(sl, {"n": 0, "c1": 0})
        st["n"] += 1; st["c1"] += hit1

    result = {
        "dictionary": os.path.basename(dict_dir.rstrip("/\\")),
        "precision": round(precision, 2),
        "false_positives": fp,
        "fp_samples": [w["input"] for w in fp_words][:10],
        "recall": round(recall, 2),
        "f1": round(2 * precision * recall / (precision + recall), 2)
              if precision + recall else 0.0,
        "correction_total": corr_total,
        "correction_at_1": round(corr1_ok / corr_total * 100, 2)
                           if corr_total else None,
        "correction_at_3": round(corr3_ok / corr_total * 100, 2)
                           if corr_total else None,
        "per_slice_correction_at_1": {
            sl: f"{st['c1']}/{st['n']}" for sl, st in sorted(per_slice.items())
        },
        "note": ("corpus_real slice has no gold; c1 counts 'any different "
                 "suggestion' for those rows" if any(
                     w["slice"] == "corpus_real" for w in misspelled) else ""),
    }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="evaluate a single dictionary by dir name")
    ap.add_argument("--limit", type=int, help="cap dataset size (smoke tests)")
    args = ap.parse_args()

    clean, misspelled = load_dataset(args.limit)
    print(f"Dataset: {len(misspelled)} misspelled / {len(clean)} clean")
    dirs = find_dictionary_dirs()
    if args.only:
        dirs = {k: v for k, v in dirs.items() if k == args.only}
    print(f"Dictionaries: {list(dirs)}")

    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    date = datetime.now().strftime("%Y%m%d")
    summaries = []
    for name, ddir in dirs.items():
        print(f"Evaluating {name} ({ddir})...")
        try:
            r = evaluate(clean, misspelled, ddir)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue
        r["dictionary"] = name
        out = os.path.join(config.RESULTS_DIR, f"{date}_{name}.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(r, f, indent=2, ensure_ascii=False)
        summaries.append(r)
        print(f"  P={r['precision']} R={r['recall']} F1={r['f1']} "
              f"c@1={r['correction_at_1']}")

    # summary markdown
    md = ["# Turkspell Benchmark V3 Results\n",
          f"Generated: {datetime.now().isoformat(timespec='seconds')}\n",
          "| Dictionary | Precision % | Recall % | F1 % | Correction@1 % | Correction@3 % |",
          "|---|---|---|---|---|---|"]
    for r in sorted(summaries, key=lambda x: -(x["correction_at_1"] or 0)):
        md.append(f"| **{r['dictionary']}** | {r['precision']} | {r['recall']} "
                  f"| {r['f1']} | {r['correction_at_1']} | "
                  f"{r['correction_at_3']} |")
    with open(os.path.join(config.RESULTS_DIR, "summary.md"),
              "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n" + "\n".join(md))


if __name__ == "__main__":
    main()
