import os
import zipfile
import shutil
import json
import argparse

# Extensions that must be stored as UTF-8 text (read explicitly, not via OS raw copy)
TEXT_EXTENSIONS = {'.json', '.txt', '.md', '.css', '.html', '.js'}

def package_profile(profile: str = "universal"):
    """Package a specific profile ('universal' or 'tdk') into its corresponding .xpi file."""
    _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if profile == "tdk":
        source_dir = os.path.join(_root_dir, "firefox-addon-tdk")
        xpi_name = "turkspell-tdk-addon.xpi"
        dic_src = os.path.join(_root_dir, "dist", "turkspell-tdk", "tr.dic")
        aff_src = os.path.join(_root_dir, "dist", "turkspell-tdk", "tr.aff")
    else:  # universal
        source_dir = os.path.join(_root_dir, "firefox-addon")
        xpi_name = "turkspell-addon.xpi"
        dic_src = os.path.join(_root_dir, "dist", "turkspell-universal", "tr.dic")
        aff_src = os.path.join(_root_dir, "dist", "turkspell-universal", "tr.aff")
        if not (os.path.exists(dic_src) and os.path.exists(aff_src)):
            dic_src = os.path.join(_root_dir, "tr.dic")
            aff_src = os.path.join(_root_dir, "tr.aff")

    # 1. Ensure dictionaries directory exists and copy appropriate dictionaries
    dict_dir = os.path.join(source_dir, "dictionaries")
    os.makedirs(dict_dir, exist_ok=True)
    if os.path.exists(dic_src) and os.path.exists(aff_src):
        shutil.copy(dic_src, os.path.join(dict_dir, "tr.dic"))
        shutil.copy(aff_src, os.path.join(dict_dir, "tr.aff"))

    # 2. Verify manifest.json is present
    manifest_path = os.path.join(source_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(
            f"manifest.json not found in {source_dir}. "
            "Make sure it exists before packaging."
        )

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"\n=== Packaging {profile.upper()} addon: {manifest.get('name', '(unnamed)')} v{manifest.get('version')} ===")
    print(f"Source: {source_dir}")
    print(f"Dictionaries: {dic_src}")

    # 3. Create zip (xpi) archive
    xpi_filename = os.path.join(_root_dir, xpi_name)
    if os.path.exists(xpi_filename):
        os.remove(xpi_filename)

    with zipfile.ZipFile(xpi_filename, "w", zipfile.ZIP_DEFLATED) as xpi:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, source_dir).replace(os.sep, "/")

                ext = os.path.splitext(file)[1].lower()
                if ext in TEXT_EXTENSIONS:
                    with open(filepath, "r", encoding="utf-8") as tf:
                        content = tf.read()
                    xpi.writestr(arcname, content.encode("utf-8"))
                else:
                    xpi.write(filepath, arcname)

                print(f"  + {arcname}")

    size_mb = os.path.getsize(xpi_filename) / (1024 * 1024)
    print(f"Successfully packaged: {xpi_filename} ({size_mb:.2f} MB)")
    return xpi_filename

def main():
    parser = argparse.ArgumentParser(description="Package Turkspell Firefox Extension(s)")
    parser.add_argument("--profile", choices=["universal", "tdk", "all"], default="all",
                        help="Profile to package: 'universal' (turkspell-addon.xpi), 'tdk' (turkspell-tdk-addon.xpi), or 'all' (both)")
    args = parser.parse_args()

    if args.profile == "all":
        package_profile("universal")
        package_profile("tdk")
    else:
        package_profile(args.profile)

if __name__ == "__main__":
    main()
