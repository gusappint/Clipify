from __future__ import annotations

import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"
BASE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/roboto"


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Clipify build script"})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - fixed HTTPS source
        destination.write_bytes(response.read())


def main() -> None:
    FONTS.mkdir(parents=True, exist_ok=True)
    font_path = FONTS / "Roboto.ttf"
    license_path = FONTS / "OFL.txt"
    if not font_path.is_file():
        download(f"{BASE_URL}/Roboto%5Bwdth,wght%5D.ttf", font_path)
    if not license_path.is_file():
        download(f"{BASE_URL}/OFL.txt", license_path)
    print(f"Roboto downloaded to {FONTS}")


if __name__ == "__main__":
    main()
