import os
import sys
import json
import time
import uuid
import base64
import hmac
import hashlib
import zipfile
import shutil
import argparse
import subprocess
import urllib.request
import urllib.parse
import urllib.error

def create_jwt(issuer: str, secret: str) -> str:
    """Generate a HS256 JWT for Mozilla AMO API authentication."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    
    now = int(time.time())
    payload = {
        "iss": issuer,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + 300,  # 5 minutes validity
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    
    return f"{header_b64}.{payload_b64}.{signature}"

def api_get(url: str, issuer: str, secret: str, max_retries: int = 3, timeout: int = 30):
    """Make an authenticated GET request to AMO API with retry on 5xx errors."""
    for attempt in range(1, max_retries + 1):
        token = create_jwt(issuer, secret)
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"JWT {token}")
        req.add_header("User-Agent", "turkspell-release-automation")
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                return resp.status, json.loads(data.decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (500, 502, 503, 504) and attempt < max_retries:
                print(f"AMO API returned HTTP {e.code} on {url}. Retrying in 5s (attempt {attempt}/{max_retries})...")
                time.sleep(5)
                continue
            try:
                body = e.read().decode("utf-8")
                err_json = json.loads(body)
            except Exception:
                err_json = {"error": str(e)}
            return e.code, err_json
        except Exception as e:
            if attempt < max_retries:
                print(f"Network error calling AMO API: {e}. Retrying in 5s...")
                time.sleep(5)
                continue
            return 0, {"error": str(e)}
    return 0, {"error": "Max retries exceeded"}

def download_signed_file(file_url: str, output_path: str, issuer: str, secret: str) -> bool:
    """
    Download signed .xpi from AMO. Handles redirects to CDN/S3
    without forwarding the Authorization header to external hosts.
    """
    token = create_jwt(issuer, secret)
    
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(file_url)
    if "addons.mozilla.org" in file_url:
        req.add_header("Authorization", f"JWT {token}")
    req.add_header("User-Agent", "turkspell-release-automation")

    target_url = file_url
    is_external = False

    try:
        resp = opener.open(req, timeout=60)
        content = resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            target_url = e.headers.get("Location")
            is_external = "addons.mozilla.org" not in target_url
            download_req = urllib.request.Request(target_url)
            download_req.add_header("User-Agent", "turkspell-release-automation")
            if not is_external:
                download_req.add_header("Authorization", f"JWT {token}")
            with urllib.request.urlopen(download_req, timeout=120) as dl_resp:
                content = dl_resp.read()
        else:
            print(f"Failed to download from {file_url}: HTTP {e.code}")
            return False
    except Exception as e:
        print(f"Failed to download from {file_url}: {e}")
        return False

    temp_path = output_path + ".tmp"
    with open(temp_path, "wb") as f:
        f.write(content)

    # Validate that it is a valid zip/xpi
    try:
        with zipfile.ZipFile(temp_path, "r") as zf:
            bad_file = zf.testzip()
            if bad_file is not None:
                print(f"Corrupted zip in downloaded XPI at file: {bad_file}")
                os.remove(temp_path)
                return False
    except zipfile.BadZipFile:
        print("Downloaded file is not a valid zip archive.")
        os.remove(temp_path)
        return False

    if os.path.exists(output_path):
        os.remove(output_path)
    shutil.move(temp_path, output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Successfully downloaded signed .xpi to {output_path} ({size_mb:.2f} MB)")
    return True

def try_fetch_signed_xpi(addon_id: str, version: str, issuer: str, secret: str, output_path: str) -> bool:
    """Query AMO API for version details and download the file if available and approved."""
    encoded_id = urllib.parse.quote(addon_id)
    url = f"https://addons.mozilla.org/api/v5/addons/addon/{encoded_id}/versions/{version}/"
    status_code, data = api_get(url, issuer, secret)

    if status_code == 404:
        # Try prepending 'v' if plain version didn't match
        url_v = f"https://addons.mozilla.org/api/v5/addons/addon/{encoded_id}/versions/v{version}/"
        status_code, data = api_get(url_v, issuer, secret)

    if status_code != 200:
        return False

    # Extract file object
    file_obj = data.get("file")
    if not file_obj:
        files = data.get("files", [])
        if files and isinstance(files, list):
            file_obj = files[0]

    if not file_obj or not isinstance(file_obj, dict):
        print(f"Version {version} exists on AMO, but no file object was found in API response.")
        return False

    file_url = file_obj.get("url")
    file_status = file_obj.get("status", "")
    print(f"AMO API Version {version} file status: {file_status}")

    if not file_url:
        print(f"Version {version} found on AMO, but download URL is not yet populated.")
        return False

    return download_signed_file(file_url, output_path, issuer, secret)

def run_web_ext_sign(source_dir: str, issuer: str, secret: str, artifacts_dir: str) -> subprocess.CompletedProcess:
    """Run `npx web-ext sign` with generous approval and request timeouts."""
    cmd = [
        "npx", "web-ext", "sign",
        "--source-dir", source_dir,
        "--api-key", issuer,
        "--api-secret", secret,
        "--channel", "unlisted",
        "--artifacts-dir", artifacts_dir,
        "--approval-timeout", "600000",
        "--timeout", "600000",
    ]
    print(f"Running: npx web-ext sign --source-dir {source_dir} --channel unlisted --approval-timeout 600000...")
    # On Windows, npx is a cmd script
    shell = os.name == "nt"
    return subprocess.run(cmd, capture_output=True, text=True, shell=shell)

def main():
    parser = argparse.ArgumentParser(description="Sign Firefox Add-on with Mozilla AMO and automatic retry resilience")
    parser.add_argument("--version", help="Extension version (default: from manifest.json)")
    parser.add_argument("--addon-id", help="Gecko Addon ID (default: from manifest.json)")
    parser.add_argument("--source-dir", default="./firefox-addon", help="Source directory")
    parser.add_argument("--output", default="./turkspell-addon.xpi", help="Output signed .xpi destination path")
    parser.add_argument("--artifacts-dir", default="./signed_dist", help="web-ext artifacts directory")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_dir = os.path.normpath(os.path.join(root_dir, args.source_dir))
    output_path = os.path.normpath(os.path.join(root_dir, args.output))
    artifacts_dir = os.path.normpath(os.path.join(root_dir, args.artifacts_dir))

    # Read credentials
    issuer = os.getenv("AMO_KEY") or os.getenv("AMO_JWT_ISSUER")
    secret = os.getenv("AMO_SECRET") or os.getenv("AMO_JWT_SECRET")

    if not issuer or not secret:
        print("AMO credentials not configured (AMO_KEY/AMO_SECRET missing).")
        print("Proceeding with unsigned .xpi package.")
        sys.exit(0)

    # Determine Addon ID & Version from manifest.json if not provided
    manifest_path = os.path.join(source_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"Error: manifest.json not found at {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    addon_id = args.addon_id or manifest.get("browser_specific_settings", {}).get("gecko", {}).get("id") or "tr-TR@dic.turkspell"
    version = args.version or manifest.get("version", "0.1.0")

    print(f"=== AMO Signing Pipeline for {addon_id} v{version} ===")

    # 1. Pre-check: Check if this version is ALREADY approved and signed on AMO
    print(f"Pre-checking if v{version} is already signed and available on AMO...")
    if try_fetch_signed_xpi(addon_id, version, issuer, secret, output_path):
        print(f"Success! Version {version} was already signed on AMO. Downloaded signed .xpi.")
        sys.exit(0)

    # 2. Run web-ext sign
    os.makedirs(artifacts_dir, exist_ok=True)
    sign_res = run_web_ext_sign(source_dir, issuer, secret, artifacts_dir)

    print("--- web-ext stdout ---")
    print(sign_res.stdout)
    if sign_res.stderr:
        print("--- web-ext stderr ---")
        print(sign_res.stderr)

    # Check if web-ext produced a signed .xpi directly
    signed_candidates = []
    if os.path.exists(artifacts_dir):
        for f in os.listdir(artifacts_dir):
            if f.endswith(".xpi"):
                signed_candidates.append(os.path.join(artifacts_dir, f))

    if sign_res.returncode == 0 and signed_candidates:
        latest_file = max(signed_candidates, key=os.path.getmtime)
        shutil.copyfile(latest_file, output_path)
        print(f"Successfully signed .xpi with web-ext: {output_path}")
        sys.exit(0)

    # 3. Resilience Fallback:
    # If web-ext failed (e.g. 502 Bad Gateway during polling, timeout, or 409 Conflict),
    # the addon may have been uploaded and is currently being processed or already approved!
    print(f"\nweb-ext sign exited with code {sign_res.returncode}.")
    print("Initiating resilient status polling via Mozilla AMO API directly...")

    max_poll_seconds = 360  # 6 minutes
    poll_interval = 15
    start_time = time.time()
    attempt = 1

    while time.time() - start_time < max_poll_seconds:
        print(f"Polling AMO API for signed .xpi (Attempt {attempt}, elapsed {int(time.time() - start_time)}s)...")
        if try_fetch_signed_xpi(addon_id, version, issuer, secret, output_path):
            print(f"Resilient recovery succeeded! Downloaded signed .xpi for v{version}.")
            sys.exit(0)
        
        attempt += 1
        time.sleep(poll_interval)

    print(f"Error: Unable to obtain signed .xpi for v{version} after {max_poll_seconds} seconds.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
