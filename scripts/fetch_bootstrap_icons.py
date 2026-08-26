from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "assets" / "vendor"
VERSION = "1.13.1"
BASE_URL = f"https://raw.githubusercontent.com/twbs/icons/v{VERSION}"


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Clipify build script"})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed HTTPS source
        destination.write_bytes(response.read())


def main() -> None:
    VENDOR.mkdir(parents=True, exist_ok=True)
    mapping_path = VENDOR / "bootstrap-icons.json"
    woff_path = VENDOR / "bootstrap-icons.woff"
    license_path = VENDOR / "BOOTSTRAP-ICONS-LICENSE"

    download(f"{BASE_URL}/font/bootstrap-icons.json", mapping_path)
    download(f"{BASE_URL}/font/fonts/bootstrap-icons.woff", woff_path)
    download(f"{BASE_URL}/LICENSE", license_path)

    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    required = {"cloud-arrow-down-fill", "download", "folder2-open", "question-circle"}
    missing = sorted(required - mapping.keys())
    if missing:
        raise RuntimeError(f"Bootstrap Icons mapping is missing: {', '.join(missing)}")

    font = TTFont(woff_path)
    font.flavor = None
    font.save(VENDOR / "bootstrap-icons.ttf")
    print(f"Bootstrap Icons {VERSION} downloaded to {VENDOR}")


if __name__ == "__main__":
    main()
