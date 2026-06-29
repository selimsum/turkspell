import os
import zipfile
import shutil
import json

def package_addon():
    addon_dir = os.path.abspath("firefox-addon")
    dictionaries_dir = os.path.join(addon_dir, "dictionaries")
    
    # 1. Create clean build directories
    if os.path.exists(addon_dir):
        shutil.rmtree(addon_dir)
    os.makedirs(dictionaries_dir, exist_ok=True)
    
    # 2. Copy dictionary files
    print("Copying tr.dic and tr.aff...")
    shutil.copy("tr.dic", os.path.join(dictionaries_dir, "tr.dic"))
    shutil.copy("tr.aff", os.path.join(dictionaries_dir, "tr.aff"))
    
    # 3. Create manifest.json
    manifest = {
        "manifest_version": 3,
        "name": "Turkspell: Optimized Turkish Dictionary",
        "version": "1.0.0",
        "description": "High-performance, lightweight Turkish spell-checking dictionary utilizing the Dynamic Chained Flags architecture.",
        "author": "Turkspell",
        "browser_specific_settings": {
            "gecko": {
                "id": "turkspell@selimsum.org",
                "strict_min_version": "109.0"
            }
        },
        "dictionaries": {
            "tr": "dictionaries/tr.dic",
            "tr-TR": "dictionaries/tr.dic"
        }
    }
    
    manifest_path = os.path.join(addon_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("Created manifest.json")
    
    # 4. Create zip (xpi) archive
    xpi_filename = "turkspell-addon.xpi"
    if os.path.exists(xpi_filename):
        os.remove(xpi_filename)
        
    print(f"Creating {xpi_filename}...")
    with zipfile.ZipFile(xpi_filename, "w", zipfile.ZIP_DEFLATED) as xpi:
        for root, dirs, files in os.walk(addon_dir):
            for file in files:
                filepath = os.path.join(root, file)
                # Store files relative to addon_dir root
                arcname = os.path.relpath(filepath, addon_dir)
                xpi.write(filepath, arcname)
                
    print(f"Successfully packaged Firefox addon to {xpi_filename}")

if __name__ == "__main__":
    package_addon()
