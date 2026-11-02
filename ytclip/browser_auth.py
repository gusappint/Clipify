from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from websockets.exceptions import WebSocketException
from websockets.sync.client import connect

from .logging_utils import get_logger
from .platform_tools import portable_root


LOGGER = get_logger("browser_auth")
COOKIE_FILENAME = "clipify-youtube-cookies.txt"
LOGIN_URL = (
    "https://accounts.google.com/ServiceLogin?service=youtube&"
    "continue=https%3A%2F%2Fwww.youtube.com%2Frobots.txt"
)
LOGIN_COOKIE_NAMES = {"SAPISID", "__Secure-1PAPISID", "__Secure-3PAPISID"}


class BrowserAuthError(RuntimeError):
    def __init__(self, message_key: str, **values: object) -> None:
        self.message_key = message_key
        self.values = values
        super().__init__(message_key)


class BrowserAuthCancelled(RuntimeError):
    pass


def youtube_cookie_path() -> Path:
    return portable_root() / COOKIE_FILENAME


def _browser_candidates() -> tuple[tuple[str, Path], ...]:
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        program_files = Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
        program_files_x86 = Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
        return (
            ("Chrome", program_files / "Google/Chrome/Application/chrome.exe"),
            ("Chrome", program_files_x86 / "Google/Chrome/Application/chrome.exe"),
            ("Chrome", local / "Google/Chrome/Application/chrome.exe"),
            ("Edge", program_files_x86 / "Microsoft/Edge/Application/msedge.exe"),
            ("Edge", program_files / "Microsoft/Edge/Application/msedge.exe"),
            ("Brave", program_files / "BraveSoftware/Brave-Browser/Application/brave.exe"),
            ("Brave", local / "BraveSoftware/Brave-Browser/Application/brave.exe"),
        )
    if sys.platform == "darwin":
        return (
            ("Chrome", Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")),
            ("Edge", Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")),
            ("Brave", Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")),
            ("Chromium", Path("/Applications/Chromium.app/Contents/MacOS/Chromium")),
        )

    candidates: list[tuple[str, Path]] = []
    for name, executable in (
        ("Chrome", "google-chrome"),
        ("Chromium", "chromium"),
        ("Chromium", "chromium-browser"),
        ("Edge", "microsoft-edge"),
        ("Brave", "brave-browser"),
    ):
        resolved = shutil.which(executable)
        if resolved:
            candidates.append((name, Path(resolved)))
    return tuple(candidates)


def find_auth_browser() -> tuple[str, Path]:
    for name, path in _browser_candidates():
        if path.is_file():
            return name, path.resolve()
    raise BrowserAuthError("error.auth_browser_missing")


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _devtools_websocket(port: int) -> str | None:
    try:
        with urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, UnicodeError, ValueError, URLError):
        return None
    websocket_url = payload.get("webSocketDebuggerUrl") if isinstance(payload, dict) else None
    return websocket_url if isinstance(websocket_url, str) else None


def _cdp_command(websocket_url: str, method: str) -> dict[str, Any]:
    request_id = 1
    try:
        with connect(websocket_url, open_timeout=3, close_timeout=1, proxy=None) as connection:
            connection.send(json.dumps({"id": request_id, "method": method}))
            while True:
                response = json.loads(connection.recv(timeout=4))
                if response.get("id") == request_id:
                    if "error" in response:
                        raise BrowserAuthError("error.auth_failed", error=response["error"])
                    result = response.get("result")
                    return result if isinstance(result, dict) else {}
    except BrowserAuthError:
        raise
    except (OSError, TimeoutError, ValueError, WebSocketException) as exc:
        raise BrowserAuthError("error.auth_failed", error=exc) from exc


def _youtube_cookies(cookies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for cookie in cookies:
        domain = str(cookie.get("domain") or "").lstrip(".").lower()
        if domain == "youtube.com" or domain.endswith(".youtube.com"):
            result.append(cookie)
    return result


def has_authenticated_youtube_session(cookies: list[dict[str, Any]]) -> bool:
    return any(str(cookie.get("name") or "") in LOGIN_COOKIE_NAMES for cookie in _youtube_cookies(cookies))


def save_youtube_cookies(cookies: list[dict[str, Any]], path: Path | None = None) -> Path:
    selected = _youtube_cookies(cookies)
    if not has_authenticated_youtube_session(selected):
        raise BrowserAuthError("error.auth_not_signed_in")

    lines = ["# Netscape HTTP Cookie File", "# Saved by Clipify. Keep this file private.", ""]
    for cookie in sorted(selected, key=lambda item: (str(item.get("domain")), str(item.get("name")))):
        domain = str(cookie.get("domain") or "")
        name = str(cookie.get("name") or "")
        value = str(cookie.get("value") or "")
        cookie_path = str(cookie.get("path") or "/")
        if any(character in name + value for character in ("\t", "\r", "\n")):
            continue
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        secure = "TRUE" if bool(cookie.get("secure")) else "FALSE"
        expires = cookie.get("expires", cookie.get("expirationDate", 0))
        try:
            expires_text = str(max(0, int(float(expires or 0))))
        except (TypeError, ValueError, OverflowError):
            expires_text = "0"
        if bool(cookie.get("httpOnly")):
            domain = f"#HttpOnly_{domain}"
        lines.append("\t".join((domain, include_subdomains, cookie_path, secure, expires_text, name, value)))

    target = path or youtube_cookie_path()
    temporary = target.with_suffix(target.suffix + ".tmp")
    newline = "\r\n" if os.name == "nt" else "\n"
    temporary.write_bytes((newline.join(lines) + newline).encode("utf-8"))
    os.chmod(temporary, 0o600)
    temporary.replace(target)
    return target


def _close_auth_browser(websocket_url: str | None, process: subprocess.Popen[bytes]) -> None:
    if websocket_url:
        try:
            _cdp_command(websocket_url, "Browser.close")
        except BrowserAuthError:
            LOGGER.debug("Не удалось закрыть окно авторизации через DevTools", exc_info=True)
    try:
        process.wait(timeout=4)
    except subprocess.TimeoutExpired:
        try:
            process.terminate()
            process.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            LOGGER.warning("Не удалось завершить отдельный браузер авторизации")


def authorize_youtube(cancel_event: threading.Event, timeout: float = 600) -> tuple[Path, str]:
    browser_name, browser_path = find_auth_browser()
    profile = Path(tempfile.mkdtemp(prefix="clipify-auth-"))
    port = _free_local_port()
    command = [
        str(browser_path),
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-allow-origins=http://127.0.0.1:{port}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-mode",
        "--new-window",
        LOGIN_URL,
    ]
    options: dict[str, object] = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True

    try:
        process = subprocess.Popen(command, **options)  # type: ignore[arg-type]
    except OSError as exc:
        raise BrowserAuthError("error.auth_browser_start", error=exc) from exc

    deadline = time.monotonic() + timeout
    websocket_url: str | None = None
    browser_was_ready = False
    try:
        while time.monotonic() < deadline:
            if cancel_event.is_set():
                raise BrowserAuthCancelled
            websocket_url = _devtools_websocket(port)
            if websocket_url:
                browser_was_ready = True
                result = _cdp_command(websocket_url, "Storage.getCookies")
                cookies = result.get("cookies")
                if isinstance(cookies, list) and has_authenticated_youtube_session(cookies):
                    return save_youtube_cookies(cookies), browser_name
            elif browser_was_ready or process.poll() is not None:
                raise BrowserAuthError("error.auth_browser_closed")
            time.sleep(1)
        raise BrowserAuthError("error.auth_timeout")
    finally:
        _close_auth_browser(websocket_url, process)
        shutil.rmtree(profile, ignore_errors=True)
