import json
import os
import re
import sys
import subprocess
import argparse

def tag_exists(version):
    """Checks if a git tag v{version} already exists locally."""
    try:
        tag_name = f"v{version}"
        res = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag_name}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False
        )
        return res.returncode == 0
    except Exception:
        return False

def is_merge_commit():
    """Checks if the HEAD commit is a merge commit (has more than 1 parent)."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "HEAD^2"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False
        )
        return res.returncode == 0
    except Exception:
        return False

def get_previous_commit_version():
    """Gets the version in firefox-addon/manifest.json from the parent commit (HEAD~1)."""
    try:
        res = subprocess.run(
            ["git", "show", "HEAD~1:firefox-addon/manifest.json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False
        )
        if res.returncode == 0 and res.stdout:
            data = json.loads(res.stdout)
            return data.get("version")
    except Exception as e:
        print(f"Warning checking previous git version: {e}")
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
    prev_ver = get_previous_commit_version()

    # 1. Determine new version
    # If the user manually changed the manifest version in a non-merge commit to a new, unreleased tag, keep it.
    if not is_merge_commit() and prev_ver and current_ver != prev_ver and not tag_exists(current_ver):
        new_ver = current_ver
        print(f"Detected manual unreleased version change in manifest.json: {prev_ver} -> {new_ver}")
    elif args.bump_type != "auto":
        new_ver = bump_version_string(current_ver, args.bump_type)
        print(f"Bumping version ({args.bump_type}): {current_ver} -> {new_ver}")
    else:
        new_ver = bump_version_string(current_ver, "patch")
        print(f"Auto-bumping version (patch): {current_ver} -> {new_ver}")

    # Ensure new_ver does not collide with any already released tag
    while tag_exists(new_ver):
        bumped = bump_version_string(new_ver, "patch")
        print(f"Tag v{new_ver} already exists! Advancing to v{bumped}")
        new_ver = bumped

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

