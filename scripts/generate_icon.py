from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ICONS = ASSETS / "icons"
VENDOR = ASSETS / "vendor"


def ensure_bootstrap_icons() -> None:
    required = (
        VENDOR / "bootstrap-icons.ttf",
        VENDOR / "bootstrap-icons.json",
        VENDOR / "BOOTSTRAP-ICONS-LICENSE",
    )
    if all(path.is_file() for path in required):
        return
    subprocess.run([sys.executable, str(ROOT / "scripts" / "fetch_bootstrap_icons.py")], check=True)


def render_glyph(name: str, size: int, color: str, destination: Path, *, canvas: int = 48) -> Image.Image:
    mapping = json.loads((VENDOR / "bootstrap-icons.json").read_text(encoding="utf-8"))
    font = ImageFont.truetype(str(VENDOR / "bootstrap-icons.ttf"), size=size)
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.text((canvas / 2, canvas / 2), chr(mapping[name]), font=font, fill=color, anchor="mm")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=True)
    return image


def generate_app_icon() -> None:
    scale = 4
    size = 256 * scale
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (38 * scale, 44 * scale, 222 * scale, 228 * scale),
        radius=52 * scale,
        fill=(5, 8, 22, 165),
    )
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16 * scale)))

    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    for y in range(28 * scale, 225 * scale):
        ratio = (y - 28 * scale) / (196 * scale)
        color = (int(104 + 28 * ratio), int(84 + 10 * ratio), int(255 - 22 * ratio), 255)
        layer_draw.line((30 * scale, y, 226 * scale, y), fill=color, width=1)
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (30 * scale, 28 * scale, 226 * scale, 224 * scale),
        radius=52 * scale,
        fill=255,
    )
    layer.putalpha(mask)
    image.alpha_composite(layer)

    mapping = json.loads((VENDOR / "bootstrap-icons.json").read_text(encoding="utf-8"))
    font = ImageFont.truetype(str(VENDOR / "bootstrap-icons.ttf"), size=126 * scale)
    ImageDraw.Draw(image).text(
        (128 * scale, 130 * scale),
        chr(mapping["cloud-arrow-down-fill"]),
        font=font,
        fill="white",
        anchor="mm",
    )

    final = image.resize((256, 256), Image.Resampling.LANCZOS)
    final.save(ASSETS / "icon.png", optimize=True)
    final.save(
        ASSETS / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    ICONS.mkdir(parents=True, exist_ok=True)
    ensure_bootstrap_icons()
    generate_app_icon()

    render_glyph("download", 38, "#FFFFFF", ICONS / "download.png")
    render_glyph("folder2-open", 37, "#172033", ICONS / "folder-light.png")
    render_glyph("folder2-open", 37, "#F5F7FF", ICONS / "folder-dark.png")
    render_glyph("question-circle", 34, "#69758C", ICONS / "question-light.png")
    render_glyph("question-circle", 34, "#9AA7C2", ICONS / "question-dark.png")
    print(f"Generated Clipify icons in {ASSETS}")


if __name__ == "__main__":
    main()
