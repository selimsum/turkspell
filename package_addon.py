import os
import zipfile
import shutil
import json

# Extensions that must be stored as UTF-8 text (read explicitly, not via OS raw copy)
TEXT_EXTENSIONS = {'.json', '.txt', '.md', '.css', '.html', '.js'}

def package_addon():
    addon_dir = os.path.abspath("firefox-addon")
    dictionaries_dir = os.path.join(addon_dir, "dictionaries")

    # 1. Ensure directories exist (don't wipe them — manifest.json is kept in source control)
    os.makedirs(dictionaries_dir, exist_ok=True)

    # 2. Copy dictionary files
    print("Copying tr.dic and tr.aff...")
    shutil.copy("tr.dic", os.path.join(dictionaries_dir, "tr.dic"))
    shutil.copy("tr.aff", os.path.join(dictionaries_dir, "tr.aff"))

    # 3. Verify manifest.json is present
    manifest_path = os.path.join(addon_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(
            "manifest.json not found in firefox-addon/. "
            "Make sure it exists before packaging."
        )
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"Packaging addon: {manifest.get('name', '(unnamed)')} v{manifest['version']}")

    # 4. Create zip (xpi) archive
    xpi_filename = "turkspell-addon.xpi"
    if os.path.exists(xpi_filename):
        os.remove(xpi_filename)

    print(f"Creating {xpi_filename}...")
    with zipfile.ZipFile(xpi_filename, "w", zipfile.ZIP_DEFLATED) as xpi:
        for root, dirs, files in os.walk(addon_dir):
            for file in files:
                filepath = os.path.join(root, file)
                # Always use forward slashes inside the ZIP (required for cross-platform)
                arcname = os.path.relpath(filepath, addon_dir).replace(os.sep, "/")

                ext = os.path.splitext(file)[1].lower()
                if ext in TEXT_EXTENSIONS:
                    # Read as explicit UTF-8 bytes so non-ASCII chars are preserved correctly
                    with open(filepath, "r", encoding="utf-8") as tf:
                        content = tf.read()
                    xpi.writestr(arcname, content.encode("utf-8"))
                else:
                    # Binary files (e.g. .dic, .aff) — copy raw bytes
                    xpi.write(filepath, arcname)

                print(f"  + {arcname}")

    size_mb = os.path.getsize(xpi_filename) / (1024 * 1024)
    print(f"\nSuccessfully packaged: {xpi_filename} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    package_addon()
