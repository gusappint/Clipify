from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ICONS = ASSETS / "icons"
VENDOR = ASSETS / "vendor"
MASTER_ICON = ASSETS / "source" / "clipify-icon-1024.png"
PROVENANCE_KEY = "impeccable:prompt"  # read with `impeccable embed-prompt <file> --read`

sys.path.insert(0, str(ROOT))
from ytclip.theme import ICON_TONES  # noqa: E402

# UI glyph -> (Bootstrap Icons name, tone). Every glyph ships as <name>-light.png and <name>-dark.png.
GLYPHS: dict[str, tuple[str, str]] = {
    "status-queued": ("clock", "muted"),
    "status-saved": ("check-circle-fill", "success"),
    "status-failed": ("exclamation-circle-fill", "danger"),
    "status-cancelled": ("x-circle", "muted"),
    "notice-info": ("info-circle-fill", "accent"),
    "dismiss": ("x-lg", "secondary"),
    "thumb-placeholder": ("film", "muted"),
    "chevron": ("chevron-down", "secondary"),
}


def ensure_bootstrap_icons() -> None:
    required = (
        VENDOR / "bootstrap-icons.ttf",
        VENDOR / "bootstrap-icons.json",
        VENDOR / "BOOTSTRAP-ICONS-LICENSE",
    )
    if all(path.is_file() for path in required):
        return
    subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_bootstrap_icons.py")], check=True)


def provenance(text: str) -> PngInfo:
    info = PngInfo()
    info.add_text(PROVENANCE_KEY, text)
    return info


def render_glyph(name: str, color: str, destination: Path, *, canvas: int = 64) -> None:
    """Render one glyph supersampled, so CustomTkinter can scale it down cleanly at any DPI."""

    mapping = json.loads((VENDOR / "bootstrap-icons.json").read_text(encoding="utf-8"))
    scale = 4
    font = ImageFont.truetype(str(VENDOR / "bootstrap-icons.ttf"), size=round(canvas * 0.86) * scale)
    image = Image.new("RGBA", (canvas * scale, canvas * scale), (0, 0, 0, 0))
    ImageDraw.Draw(image).text(
        (canvas * scale / 2, canvas * scale / 2),
        chr(mapping[name]),
        font=font,
        fill=color,
        anchor="mm",
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    origin = f"Rendered by scripts/generate_icon.py from Bootstrap Icons 1.13.1 (MIT), glyph '{name}', colour {color}."
    image.resize((canvas, canvas), Image.Resampling.LANCZOS).save(destination, optimize=True, pnginfo=provenance(origin))


def generate_app_icon() -> None:
    if not MASTER_ICON.is_file():
        raise FileNotFoundError(f"Master icon not found: {MASTER_ICON}")
    with Image.open(MASTER_ICON) as source:
        master = source.convert("RGBA")
    origin = provenance(
        "Resized by scripts/generate_icon.py from assets/source/clipify-icon-1024.png, which was generated with "
        "OpenAI image generation through the Codex plugin; its prompt is in assets/source/clipify-icon-1024.prompt.txt."
    )
    master.resize((256, 256), Image.Resampling.LANCZOS).save(ASSETS / "icon.png", optimize=True, pnginfo=origin)
    master.resize((512, 512), Image.Resampling.LANCZOS).save(ASSETS / "icon-512.png", optimize=True, pnginfo=origin)
    master.save(
        ASSETS / "icon.ico",
        sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    ICONS.mkdir(parents=True, exist_ok=True)
    ensure_bootstrap_icons()
    generate_app_icon()

    render_glyph("download", "#FFFFFF", ICONS / "download.png")
    for stem, (glyph, tone) in GLYPHS.items():
        light, dark = ICON_TONES[tone]
        render_glyph(glyph, light, ICONS / f"{stem}-light.png")
        render_glyph(glyph, dark, ICONS / f"{stem}-dark.png")
    print(f"Generated Clipify icons in {ASSETS}")


if __name__ == "__main__":
    main()
