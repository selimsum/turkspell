# -*- coding: utf-8 -*-
"""Rename Turkspell v0.6 Gold (TDK) to Turkspell v0.6 (TDK) and set Universal as default."""
from pathlib import Path

# 1. Update config.py
cfg_path = Path(r"C:\gemini\turkspell-benchmarks\benchmark\config.py")
cfg_text = cfg_path.read_text(encoding="utf-8")

old_cfg = """def get_turkspell_dictionaries() -> dict:
    \"\"\"Return dictionary bases for Turkspell variations in sibling checkout.\"\"\"
    dicts = {}
    
    # Flagship TDK profile at turkspell repo root
    flagship = TURKSPELL_REPO / "tr"
    if (TURKSPELL_REPO / "tr.aff").exists() and (TURKSPELL_REPO / "tr.dic").exists():
        dicts["Turkspell v0.6 Gold (TDK)"] = str(flagship)
    
    # DD Profile in dist/
    dd_profile = TURKSPELL_REPO / "dist" / "turkspell-v0.6-dd" / "tr"
    if Path(str(dd_profile) + ".aff").exists():
        dicts["Turkspell v0.6 (DD)"] = str(dd_profile)
        
    # Universal Profile in dist/
    univ_profile = TURKSPELL_REPO / "dist" / "turkspell-v0.6-universal" / "tr"
    if Path(str(univ_profile) + ".aff").exists():
        dicts["Turkspell v0.6 (Universal)"] = str(univ_profile)
        
    return dicts"""

new_cfg = """def get_turkspell_dictionaries() -> dict:
    \"\"\"Return dictionary bases for Turkspell variations in sibling checkout.\"\"\"
    dicts = {}
    
    # Universal Profile (Default edition)
    univ_profile = TURKSPELL_REPO / "dist" / "turkspell-v0.6-universal" / "tr"
    if Path(str(univ_profile) + ".aff").exists():
        dicts["Turkspell v0.6 (Universal)"] = str(univ_profile)
    elif (TURKSPELL_REPO / "tr.aff").exists() and (TURKSPELL_REPO / "tr.dic").exists():
        dicts["Turkspell v0.6 (Universal)"] = str(TURKSPELL_REPO / "tr")

    # TDK profile
    tdk_profile = TURKSPELL_REPO / "dist" / "turkspell-v0.6-tdk" / "tr"
    if Path(str(tdk_profile) + ".aff").exists():
        dicts["Turkspell v0.6 (TDK)"] = str(tdk_profile)
    elif (TURKSPELL_REPO / "tr.aff").exists():
        dicts["Turkspell v0.6 (TDK)"] = str(TURKSPELL_REPO / "tr")
    
    # DD Profile in dist/
    dd_profile = TURKSPELL_REPO / "dist" / "turkspell-v0.6-dd" / "tr"
    if Path(str(dd_profile) + ".aff").exists():
        dicts["Turkspell v0.6 (DD)"] = str(dd_profile)
        
    return dicts"""

if old_cfg in cfg_text:
    cfg_text = cfg_text.replace(old_cfg, new_cfg)
    cfg_path.write_text(cfg_text, encoding="utf-8")
    print("Updated benchmark/config.py successfully!")
else:
    print("Target block not found in benchmark/config.py")

# 2. Update cli.py
cli_path = Path(r"C:\gemini\turkspell-benchmarks\benchmark\cli.py")
cli_text = cli_path.read_text(encoding="utf-8")

cli_text = cli_text.replace(
    'print("  [1] Turkspell v0.6 Gold (Default - fast single-dictionary run)")',
    'print("  [1] Turkspell v0.6 (Universal) (Default - fast single-dictionary run)")'
)

old_cli_lookup = """    if mode in ("turkspell", "gold", "default"):
        # Just Turkspell Flagship
        for name, path in turkspell_all.items():
            if "Gold" in name or "TDK" in name:
                return {name: path}
        return dict(list(turkspell_all.items())[:1]) if turkspell_all else {}"""

new_cli_lookup = """    if mode in ("turkspell", "universal", "gold", "default"):
        # Just Turkspell Default (Universal)
        for name, path in turkspell_all.items():
            if "Universal" in name:
                return {name: path}
        return dict(list(turkspell_all.items())[:1]) if turkspell_all else {}"""

if old_cli_lookup in cli_text:
    cli_text = cli_text.replace(old_cli_lookup, new_cli_lookup)
    cli_path.write_text(cli_text, encoding="utf-8")
    print("Updated benchmark/cli.py successfully!")
else:
    print("Target lookup not found in benchmark/cli.py")

# 3. Update README.md in turkspell-benchmarks
bench_readme = Path(r"C:\gemini\turkspell-benchmarks\README.md")
bench_readme_text = bench_readme.read_text(encoding="utf-8")
bench_readme_text = bench_readme_text.replace("Turkspell v0.6 Gold (TDK)", "Turkspell v0.6 (TDK)")
bench_readme_text = bench_readme_text.replace("Turkspell v0.6 Gold (Universal)", "Turkspell v0.6 (Universal)")
bench_readme.write_text(bench_readme_text, encoding="utf-8")
print("Updated turkspell-benchmarks README.md successfully!")
