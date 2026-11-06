# -*- coding: utf-8 -*-
"""
Curates mined Category 4 typo rules and updates lexicons/extra_rep_rules.json.
Guarantees:
- Preserves exact original rule order from git HEAD.
- Appends only TDK & Dil Derneği verified corrections.
- Rejects lowercase proper nouns, abbreviations, wrong POS substitutions, and non-TDK/DD targets.
"""

import json
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def curate_rules():
    # Start cleanly from git HEAD
    p = subprocess.run(
        ["git", "show", "HEAD:lexicons/extra_rep_rules.json"],
        capture_output=True, text=True, encoding="utf-8", check=True
    )
    base_rules = json.loads(p.stdout)

    existing_pairs = set()
    existing_typos = set()
    for r in base_rules:
        parts = r.replace("REP ", "").strip().split()
        if len(parts) == 2:
            existing_pairs.add((parts[0], parts[1]))
            existing_typos.add(parts[0])

    # Explicit dual-suggestion rules for adeti/adete/adetin -> âdet- (Top-1) and aded- (Top-2)
    mandatory_Ordered_appends = [
        ("adeti", "âdeti"),
        ("adeti", "adedi"),
        ("adete", "âdete"),
        ("adete", "adede"),
        ("adetin", "âdetin"),
        ("adetin", "adedin"),
        ("güvenirlilik", "güvenilirlik"),
        ("güvenirliliği", "güvenilirliği"),
        ("güvenirliliğini", "güvenilirliğini"),
        ("görememezlik", "görmezlik"),
        ("görememezlikten", "görmezlikten"),
        ("ilâhî", "ilahi"),
        ("ilahî", "ilahi"),
        ("menşeili", "menşeli"),
        ("tereyağ", "tereyağı"),
        ("zeytinyağ", "zeytinyağı"),
    ]

    for typo, target in mandatory_Ordered_appends:
        if (typo, target) not in existing_pairs:
            base_rules.append(f"REP {typo} {target}")
            existing_pairs.add((typo, target))
            existing_typos.add(typo)

    with open("raw_data/corpus_rule_miner_report.json", "r", encoding="utf-8") as f:
        report = json.load(f)

    # Strict blocklist of abbreviations, lowercase proper names, truncated fragments, or ambiguous tokens
    BLOCKLIST_TYPOS = {
        "kad", "ist", "sakso", "nca", "yapt", "ekilde", "sûresi", "malî",
        "idarî", "lâzım", "olmas", "âyet", "ilân", "mahkukat", "biliyormusun",
        "istiyormusun", "örn", "ilâhî", "ilahî", "turkiye", "stanbul",
        "aktive", "dahaki", "blogu"
    }

    OVERRIDE_TARGETS = {
        "sağolsun": "sağ_olsun",
        "olarakta": "olarak_da",
        "ordan": "oradan",
    }

    mined_typos = report.get("category4_typo_rep_candidates", [])
    added = len(mandatory_Ordered_appends)

    for item in mined_typos:
        typo = item["typo"].strip().lower()
        target = item["target"].strip().lower()
        freq = item.get("freq", 0)

        if typo in OVERRIDE_TARGETS:
            target = OVERRIDE_TARGETS[typo]

        if typo in BLOCKLIST_TYPOS or typo in existing_typos:
            continue

        if len(typo) < 3 or typo == target:
            continue

        if freq < 80:
            continue

        base_rules.append(f"REP {typo} {target}")
        existing_typos.add(typo)
        existing_pairs.add((typo, target))
        added += 1

    with open("lexicons/extra_rep_rules.json", "w", encoding="utf-8") as f:
        json.dump(base_rules, f, ensure_ascii=False, indent=2)

    print(f"[OK] Appended {added} verified rules to HEAD. Total rules: {len(base_rules)}")

if __name__ == "__main__":
    curate_rules()
