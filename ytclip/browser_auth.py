from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .logging_utils import get_logger
from .platform_tools import portable_root


LOGGER = get_logger("browser_auth")
SETTINGS_FILENAME = "clipify-settings.json"
SUPPORTED_BROWSER_IDS = (
    "brave",
    "chrome",
    "chromium",
    "edge",
    "firefox",
    "opera",
    "safari",
    "vivaldi",
)
BROWSER_NAMES = {
    "brave": "Brave",
    "chrome": "Chrome",
    "chromium": "Chromium",
    "edge": "Edge",
    "firefox": "Firefox",
    "opera": "Opera",
    "safari": "Safari",
    "vivaldi": "Vivaldi",
}


def available_browser_ids(*, platform: str | None = None, os_name: str | None = None) -> tuple[str, ...]:
    current_platform = sys.platform if platform is None else platform
    current_os = os.name if os_name is None else os_name
    if current_platform == "darwin":
        return ("safari", "chrome", "edge", "firefox", "brave", "vivaldi", "opera")
    if current_os == "nt":
        return ("chrome", "edge", "firefox", "brave", "vivaldi", "opera")
    return ("chrome", "chromium", "firefox", "brave", "edge", "vivaldi", "opera")


def browser_display_name(browser_id: str) -> str:
    return BROWSER_NAMES.get(browser_id, browser_id.title())


def settings_path() -> Path:
    return portable_root() / SETTINGS_FILENAME


def load_auth_browser(path: Path | None = None) -> str | None:
    target = path or settings_path()
    if not target.is_file():
        return None
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        LOGGER.exception("Не удалось прочитать настройки Clipify: %s", target)
        return None
    browser_id = data.get("youtube_browser") if isinstance(data, dict) else None
    return browser_id if browser_id in SUPPORTED_BROWSER_IDS else None


def save_auth_browser(browser_id: str | None, path: Path | None = None) -> None:
    if browser_id is not None and browser_id not in SUPPORTED_BROWSER_IDS:
        raise ValueError(f"Unsupported browser: {browser_id}")
    target = path or settings_path()
    data: dict[str, object] = {}
    if target.is_file():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
        except (OSError, UnicodeError, json.JSONDecodeError):
            LOGGER.exception("Не удалось сохранить существующие настройки Clipify: %s", target)
    data["youtube_browser"] = browser_id
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
