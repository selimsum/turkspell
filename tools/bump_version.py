import json
import os
import re
import sys
import subprocess
import argparse

def get_git_diff_version():
    """Checks if firefox-addon/manifest.json version was manually changed in the latest git commit."""
    try:
        res = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--", "firefox-addon/manifest.json"],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0 and res.stdout:
            for line in res.stdout.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    match = re.search(r'"version":\s*"([^"]+)"', line)
                    if match:
                        return match.group(1)
    except Exception as e:
        print(f"Warning checking git diff: {e}")
    return None

def bump_version_string(current_ver, bump_type):
    parts = current_ver.split(".")
    while len(parts) < 3:
        parts.append("0")
    
    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        # Fallback if version string is unusual
        return current_ver

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch or auto
        patch += 1

    return f"{major}.{minor}.{patch}"

def main():
    parser = argparse.ArgumentParser(description="Bump Turkspell extension version")
    parser.add_argument("--bump-type", choices=["patch", "minor", "major", "auto"], default="auto", help="Type of version bump")
    parser.add_argument("--repo-owner", default="selimsum", help="GitHub repo owner")
    parser.add_argument("--repo-name", default="turkspell", help="GitHub repo name")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(root_dir, "firefox-addon", "manifest.json")
    update_json_path = os.path.join(root_dir, "update.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    current_ver = manifest.get("version", "0.1.0")

    # 1. Check if user manually changed version in git commit
    manual_ver = get_git_diff_version()
    if manual_ver and manual_ver != current_ver:
        new_ver = manual_ver
        print(f"Detected manual version change in manifest.json: {current_ver} -> {new_ver}")
    elif args.bump_type != "auto" or manual_ver is None:
        new_ver = bump_version_string(current_ver, args.bump_type)
        print(f"Bumping version ({args.bump_type}): {current_ver} -> {new_ver}")
    else:
        new_ver = manual_ver

    # 2. Update manifest.json
    manifest["version"] = new_ver
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 3. Update update.json
    update_link = f"https://github.com/{args.repo_owner}/{args.repo_name}/releases/download/v{new_ver}/turkspell-addon.xpi"
    update_data = {
        "addons": {
            "tr-TR@dic.turkspell": {
                "updates": [
                    {
                        "version": new_ver,
                        "update_link": update_link
                    }
                ]
            }
        }
    }
    with open(update_json_path, "w", encoding="utf-8") as f:
        json.dump(update_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Updated manifests to version {new_ver}")

    # Set GITHUB_OUTPUT if running in GitHub Actions
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"version={new_ver}\n")

if __name__ == "__main__":
    main()
