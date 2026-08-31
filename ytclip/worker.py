from __future__ import annotations

import argparse
import json
import math
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessor
from yt_dlp.utils import DownloadError, download_range_func

from .logging_utils import get_logger
from .platform_tools import find_deno, find_ffmpeg


EVENT_PREFIX = "YTCLIP_EVENT:"
_event_file: Path | None = None
_event_lock = threading.Lock()
LOGGER = get_logger("worker")


class WorkerUserError(ValueError):
    def __init__(self, message_key: str) -> None:
        self.message_key = message_key
        super().__init__(message_key)


def emit(event: str, **payload: Any) -> None:
    message = {"event": event, **payload}
    line = f"{EVENT_PREFIX}{json.dumps(message, ensure_ascii=False)}\n"
    with _event_lock:
        if _event_file is not None:
            try:
                with _event_file.open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(line)
                return
            except OSError:
                LOGGER.exception("Не удалось записать событие %s в %s", event, _event_file)
        stdout_buffer = getattr(sys.stdout, "buffer", None)
        if stdout_buffer is not None:
            stdout_buffer.write(line.encode("utf-8"))
            stdout_buffer.flush()
        elif sys.stdout is not None:
            sys.stdout.write(line.encode("ascii", "backslashreplace").decode("ascii"))
            sys.stdout.flush()


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _human_bytes(value: float | int | None) -> str:
    if value is None:
        return ""
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(size) < 1024 or unit == "GiB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return ""


class WorkerLogger:
    def debug(self, message: str) -> None:
        LOGGER.debug("Внутренняя утилита: %s", message)
        if message.startswith("[youtube]"):
            emit("status", key="status.fetching_info")
        elif message.startswith("[Merger]"):
            emit("status", key="status.merging_video_audio")
        elif message.startswith("[download] Destination"):
            emit("status", key="status.starting_download")

    def info(self, message: str) -> None:
        self.debug(message)

    def warning(self, message: str) -> None:
        LOGGER.warning("Внутренняя утилита: %s", message)
        emit("warning", text=message)

    def error(self, message: str) -> None:
        LOGGER.error("Внутренняя утилита: %s", message)
        emit("log_error", text=message)


def _progress_hook(data: dict[str, Any]) -> None:
    status = data.get("status")
    if status == "downloading":
        downloaded = _safe_float(data.get("downloaded_bytes")) or 0.0
        total = _safe_float(data.get("total_bytes")) or _safe_float(data.get("total_bytes_estimate"))
        percent = min(downloaded / total * 100, 100.0) if total else None
        emit(
            "progress",
            percent=percent,
            speed=_human_bytes(_safe_float(data.get("speed"))) + "/s" if data.get("speed") else "",
            eta=_safe_float(data.get("eta")),
            downloaded=_human_bytes(downloaded),
            total=_human_bytes(total),
        )
    elif status == "finished":
        emit("status", key="status.processing_file")


def _postprocessor_hook(data: dict[str, Any]) -> None:
    if data.get("status") == "started":
        emit("status", key="status.merging_tracks")


def _find_result(output_dir: Path, video_id: str | None, started_at: float) -> Path | None:
    files = [
        path
        for path in output_dir.iterdir()
        if path.is_file()
        and not path.name.endswith((".part", ".ytdl"))
        and path.stat().st_mtime >= started_at - 3
        and (not video_id or f"[{video_id}]" in path.name)
    ]
    return max(files, key=lambda path: path.stat().st_mtime, default=None)


def finalize_unique_result(temporary: Path, job_token: str) -> Path:
    """Remove the private job marker and preserve every existing download."""

    marker = f".__clipify_{job_token}"
    if marker not in temporary.name:
        return temporary

    clean_name = temporary.name.replace(marker, "", 1)
    desired = temporary.with_name(clean_name)
    index = 1
    while True:
        candidate = desired if index == 1 else desired.with_name(f"{desired.stem} ({index}){desired.suffix}")
        try:
            # A hard link is an atomic, no-overwrite reservation and works
            # because both names live in the same output directory.
            os.link(temporary, candidate)
        except FileExistsError:
            index += 1
            continue
        except OSError:
            # FAT/exFAT and some network shares do not support hard links.
            # Windows rename is still no-overwrite; on POSIX the existence
            # check narrows the unavoidable fallback race substantially.
            if candidate.exists():
                index += 1
                continue
            try:
                temporary.rename(candidate)
            except FileExistsError:
                index += 1
                continue
            return candidate
        temporary.unlink()
        return candidate


def safe_title_budget(output_dir: Path, *, windows: bool | None = None) -> int:
    """Return a conservative UTF-8 byte budget for the video title.

    yt-dlp adds the stable video ID and extension outside this budget. On
    Windows we also stay below the traditional MAX_PATH boundary because some
    FFmpeg builds and removable drives still use it even on modern systems.
    """

    is_windows = os.name == "nt" if windows is None else windows
    if not is_windows:
        return 180

    directory_length = len(str(output_dir.resolve()))
    fixed_name_overhead = 48  # ID, extension, private job marker and numeric suffix margin
    available = 240 - directory_length - fixed_name_overhead
    if available < 40:
        raise WorkerUserError("error.output_path_too_long")
    return min(160, available)


def build_options(args: argparse.Namespace, job_token: str) -> dict[str, Any]:
    ffmpeg = find_ffmpeg()
    # FFmpegFD.available() currently checks this context variable instead of
    # the YoutubeDL API parameter when partial downloads are requested.
    FFmpegPostProcessor._ffmpeg_location.set(str(ffmpeg))
    deno = find_deno()
    output_dir = Path(args.output).resolve()
    title_budget = safe_title_budget(output_dir)

    options: dict[str, Any] = {
        "format": "bv*+ba/b",
        "outtmpl": str(output_dir / f"%(title).{title_budget}B [%(id)s].__clipify_{job_token}.%(ext)s"),
        "ffmpeg_location": str(ffmpeg),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
        "noprogress": True,
        "continuedl": True,
        "overwrites": False,
        "retries": 10,
        "fragment_retries": 10,
        # Use the strictest portable filename rules on every OS. This replaces
        # forbidden characters and protects Windows reserved names while
        # preserving Unicode titles (including Cyrillic).
        "windowsfilenames": True,
        "trim_file_name": 210,
        "progress_hooks": [_progress_hook],
        "postprocessor_hooks": [_postprocessor_hook],
        "logger": WorkerLogger(),
    }
    if deno:
        options["js_runtimes"] = {"deno": {"path": str(deno)}}

    if args.start is not None or args.end is not None:
        start = args.start if args.start is not None else 0.0
        end = args.end if args.end is not None else float("inf")
        options["download_ranges"] = download_range_func([], [(start, end)])
        options["force_keyframes_at_cuts"] = args.exact

    return options


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--start", type=float)
    parser.add_argument("--end", type=float)
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--event-file")
    return parser.parse_args(argv)


def worker_main(argv: list[str]) -> int:
    global _event_file
    args = parse_args(argv)
    _event_file = Path(args.event_file).resolve() if args.event_file else None
    output_dir = Path(args.output).resolve()
    started_at = time.time()
    job_token = uuid.uuid4().hex[:10]

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Запущен загрузчик; папка: %s", output_dir)
        emit("status", key="status.checking_tools")
        options = build_options(args, job_token)
        emit("status", key="status.fetching_info")
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(args.url, download=True)

        video_id = info.get("id") if isinstance(info, dict) else None
        result = _find_result(output_dir, video_id, started_at)
        if result is not None:
            result = finalize_unique_result(result, job_token)
        LOGGER.info("Загрузка завершена; результат: %s", result or output_dir)
        emit("complete", filepath=str(result) if result else str(output_dir))
        return 0
    except DownloadError as exc:
        LOGGER.exception("Ошибка загрузки или сети")
        emit("error", text=str(exc).removeprefix("ERROR: "))
    except WorkerUserError as exc:
        LOGGER.exception("Ошибка параметров загрузчика")
        emit("error", key=exc.message_key)
    except FileNotFoundError as exc:
        LOGGER.exception("Компонент загрузчика не найден")
        key = "error.ffmpeg_missing" if "FFmpeg" in str(exc) else "error.download"
        emit("error", key=key)
    except (OSError, ValueError) as exc:
        LOGGER.exception("Системная ошибка загрузчика")
        emit("error", text=str(exc))
    except Exception as exc:  # noqa: BLE001 - worker must report unexpected failures to the GUI
        LOGGER.exception("Неожиданная ошибка загрузчика")
        emit("error", key="error.unexpected_worker", error=str(exc))
    return 1


if __name__ == "__main__":
    raise SystemExit(worker_main(sys.argv[1:]))
