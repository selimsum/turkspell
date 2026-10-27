import os
import sys
import re
from pathlib import Path

# Path to benchmarks directory
BENCH_DIR = Path(r"../turkspell-benchmarks")

def patch_collision_filter():
    """Ensure CollisionFilter uses independent reference dictionaries, not Turkspell itself."""
    script_path = BENCH_DIR / "scripts" / "clean_benchmark_collisions.py"
    if not script_path.exists():
        print(f"Notice: {script_path} not found. Skipping benchmark repo patch.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure Turkspell is not used as an oracle for its own benchmark evaluation
    new_class = """class CollisionFilter:
    def __init__(self, extra_valid: set = None):
        self.universe = load_reference_universe()
        if extra_valid:
            self.universe |= {tlc(w) for w in extra_valid}
        self._speller_cache = {}
        # Independent external reference dictionaries (decoupled from Turkspell)
        self._ref_dicts = [
            os.path.join(config.EXTERNAL_DICTS_DIR, "harunzafer", "tr_TR").replace("\\\\", "/"),
            os.path.join(config.EXTERNAL_DICTS_DIR, "vdemir", "tr_TR").replace("\\\\", "/")
        ]

    def is_valid_anywhere(self, word: str) -> bool:
        w = tlc(word.strip())
        if w in self.universe:
            return True
        if w in self._speller_cache:
            return self._speller_cache[w]
            
        is_valid = False
        for d in self._ref_dicts:
            if os.path.exists(d + ".dic"):
                try:
                    import subprocess
                    p = subprocess.run(
                        ["hunspell", "-d", d, "-l"],
                        input=w + "\\n",
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=5
                    )
                    if w not in {line.strip() for line in p.stdout.splitlines()}:
                        is_valid = True
                        break
                except Exception:
                    pass
                    
        self._speller_cache[w] = is_valid
        return is_valid"""

    content = re.sub(r'class CollisionFilter:.*?(?=\ndef )', new_class + '\n\n', content, flags=re.DOTALL)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully patched clean_benchmark_collisions.py to decouple from Turkspell.")

if __name__ == "__main__":
    patch_collision_filter()
