import os
import shutil

winget_pkg_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
for root, dirs, files in os.walk(winget_pkg_dir):
    if "hunspell.exe" in files:
        if root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = root + os.pathsep + os.environ["PATH"]
        break
