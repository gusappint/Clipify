from __future__ import annotations

import argparse
import platform
import shutil
import stat
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def deno_asset() -> tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    architecture = "aarch64" if machine in {"arm64", "aarch64"} else "x86_64"

    targets = {
        ("windows", "x86_64"): ("deno-x86_64-pc-windows-msvc.zip", "deno.exe"),
        ("windows", "aarch64"): ("deno-aarch64-pc-windows-msvc.zip", "deno.exe"),
        ("linux", "x86_64"): ("deno-x86_64-unknown-linux-gnu.zip", "deno"),
        ("linux", "aarch64"): ("deno-aarch64-unknown-linux-gnu.zip", "deno"),
        ("darwin", "x86_64"): ("deno-x86_64-apple-darwin.zip", "deno"),
        ("darwin", "aarch64"): ("deno-aarch64-apple-darwin.zip", "deno"),
    }
    try:
        return targets[(system, architecture)]
    except KeyError as exc:
        raise SystemExit(f"Unsupported platform: {system}/{architecture}") from exc


def download_deno(force: bool = False) -> Path:
    asset, executable = deno_asset()
    destination = TOOLS / executable
    if destination.exists() and not force:
        print(f"Deno already exists: {destination}")
        return destination

    url = f"https://github.com/denoland/deno/releases/latest/download/{asset}"
    TOOLS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ytclip-deno-") as temp_dir:
        archive = Path(temp_dir) / asset
        print(f"Downloading {url}")
        request = urllib.request.Request(url, headers={"User-Agent": "YT-Clip-Build/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        with zipfile.ZipFile(archive) as package:
            member = next((name for name in package.namelist() if Path(name).name == executable), None)
            if not member:
                raise RuntimeError(f"{executable} not found in {asset}")
            with package.open(member) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)

    destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"Saved: {destination}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the Deno runtime used by Clipify")
    parser.add_argument("--force", action="store_true", help="replace an existing runtime")
    args = parser.parse_args()
    download_deno(force=args.force)


if __name__ == "__main__":
    main()
