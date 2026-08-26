from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resource_root() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    return Path(bundle_root) if bundle_root else source_root()


def portable_root() -> Path:
    if not is_frozen():
        return source_root()

    executable = Path(sys.executable).resolve()
    if sys.platform == "darwin":
        for parent in executable.parents:
            if parent.suffix == ".app":
                return parent.parent
    return executable.parent


def worker_command() -> list[str]:
    if is_frozen():
        return [sys.executable, "--worker"]
    return [sys.executable, str(source_root() / "main.py"), "--worker"]


def find_deno() -> Path | None:
    executable_name = "deno.exe" if os.name == "nt" else "deno"
    candidates = [
        resource_root() / "tools" / executable_name,
        portable_root() / "tools" / executable_name,
        portable_root() / executable_name,
    ]

    resolved = shutil.which("deno")
    if resolved:
        candidates.append(Path(resolved))

    # Friendly fallback for the common manual Windows installation used by
    # this project owner. It does not affect portable bundles on other hosts.
    if os.name == "nt":
        candidates.append(Path.home() / "deno.exe")

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def find_ffmpeg() -> Path:
    try:
        import imageio_ffmpeg

        bundled = Path(imageio_ffmpeg.get_ffmpeg_exe())
        if bundled.is_file():
            return bundled.resolve()
    except (ImportError, RuntimeError):
        pass

    executable_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for candidate in (
        resource_root() / "tools" / executable_name,
        portable_root() / "tools" / executable_name,
    ):
        if candidate.is_file():
            return candidate.resolve()

    resolved = shutil.which("ffmpeg")
    if resolved:
        return Path(resolved).resolve()
    raise FileNotFoundError("FFmpeg не найден внутри приложения или в PATH")
