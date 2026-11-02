from __future__ import annotations

import ctypes
import json
import locale as system_locale_module
import os
import queue
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import uuid
import webbrowser
from collections.abc import Callable
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from tkinter import filedialog
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

import customtkinter as ctk
from customtkinter.windows.widgets.core_widget_classes import DropdownMenu
from PIL import Image, ImageDraw

from .browser_auth import (
    BrowserAuthCancelled,
    BrowserAuthError,
    authorize_youtube,
    youtube_cookie_path,
)
from .i18n import (
    DEFAULT_LOCALE,
    LOCALE_NAMES,
    SUPPORTED_LOCALES,
    format_duration,
    format_size,
    format_speed,
    translate,
)
from .logging_utils import LOG_FILENAME, get_logger
from .platform_tools import portable_root, resource_root, worker_command
from .theme import COLORS, FIELD_HEIGHT, PAGE_X, PRIMARY_HEIGHT, RADIUS, Typography
from .timecode import TimecodeError, describe_range, format_timecode, parse_timecode, validate_time_range
from .version import __version__
from .worker import EVENT_PREFIX


LOGGER = get_logger("ui")
WINDOW_SIZE = (740, 640)
MIN_SIZE = (680, 600)
SETTINGS_FILENAME = "clipify-settings.json"
AUTHOR_URL = "https://t.me/PanCrucian"
THUMBNAIL_URL = "https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
THUMB_SIZE = (80, 45)
FINISHED_STATES = frozenset({"saved", "failed", "cancelled"})
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_SIGN_IN_ERRORS = frozenset({"error.youtube_auth_required", "error.youtube_session_expired", "error.video_private"})
_FOCUS_RING = 2


def reading_time_ms(text: str) -> int:
    """Estimate comfortable reading time for a notice at roughly 190 words/minute."""

    word_count = max(1, len(text.split()))
    reading_seconds = 1.2 + word_count / 3.2
    return max(2800, min(15000, round(reading_seconds * 1000)))


def set_windows_app_id() -> bool:
    if os.name != "nt":
        return True
    try:
        result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(  # type: ignore[attr-defined]
            "PanCrucian.Clipify"
        )
    except (OSError, AttributeError):
        LOGGER.exception("Не удалось установить Windows AppUserModelID")
        return False
    if result != 0:
        LOGGER.error("Windows отклонила AppUserModelID, код: %s", result)
        return False
    return True


def normalize_youtube_url(value: str) -> str:
    """Return a YouTube URL ready for the worker, or raise ValueError with a copy key."""

    text = value.strip()
    if text and "://" not in text:
        text = f"https://{text}"
    try:
        parsed = urlparse(text)
    except ValueError as exc:
        raise ValueError("link.error.not_youtube") from exc
    host = (parsed.hostname or "").lower()
    allowed = host in {"youtu.be", "youtube.com"} or host.endswith((".youtu.be", ".youtube.com"))
    if parsed.scheme not in {"http", "https"} or not allowed:
        raise ValueError("link.error.not_youtube")
    return text


def youtube_video_id(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    parts = [part for part in parsed.path.split("/") if part]
    if host == "youtu.be" or host.endswith(".youtu.be"):
        candidate = parts[0] if parts else ""
    else:
        candidate = (parse_qs(parsed.query).get("v") or [""])[0]
        if not candidate and len(parts) >= 2 and parts[0] in {"shorts", "live", "embed", "v"}:
            candidate = parts[1]
    return candidate if _VIDEO_ID.match(candidate) else None


def system_locale() -> str:
    language = ""
    try:
        if os.name == "nt":
            language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()  # type: ignore[attr-defined]
            return "ru" if language_id & 0x3FF == 0x19 else DEFAULT_LOCALE
        if sys.platform == "darwin":
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleLanguages"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            language = result.stdout.strip().strip("()").split(",")[0].strip().strip('"')
        else:
            language = system_locale_module.getlocale()[0] or os.environ.get("LANG", "")
    except (OSError, subprocess.SubprocessError, AttributeError, ValueError):
        LOGGER.warning("Не удалось определить язык системы", exc_info=True)
    return "ru" if language.lower().startswith("ru") else DEFAULT_LOCALE


def settings_path() -> Path:
    return portable_root() / SETTINGS_FILENAME


def load_settings() -> dict[str, object]:
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        LOGGER.warning("Не удалось прочитать настройки", exc_info=True)
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(**values: object) -> None:
    target = settings_path()
    temporary = target.with_suffix(target.suffix + ".tmp")
    try:
        current = load_settings()
        current.update(values)
        temporary.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(target)
    except OSError:
        LOGGER.warning("Не удалось сохранить настройки", exc_info=True)


def hairline(parent: tk.Misc) -> ctk.CTkFrame:
    """A 1px rule. CustomTkinter skips drawing frames this thin, so the canvas colour carries it."""

    return ctk.CTkFrame(parent, height=1, fg_color=COLORS["hairline"], bg_color=COLORS["hairline"], corner_radius=0)


def fit_end(text: str, font: tkfont.Font, width: float) -> str:
    """Trim text with a trailing ellipsis until it fits the given width."""

    if width <= 0 or font.measure(text) <= width:
        return text
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if font.measure(text[:middle].rstrip() + "…") <= width:
            low = middle
        else:
            high = middle - 1
    return text[:low].rstrip() + "…"


def fit_middle(text: str, font: tkfont.Font, width: float) -> str:
    """Trim the middle of a path so both the drive and the final folder stay visible."""

    if width <= 0 or font.measure(text) <= width:
        return text
    low, high = 0, len(text)
    while low < high:
        keep = (low + high + 1) // 2
        head, tail = text[: (keep + 1) // 2], text[len(text) - keep // 2 :] if keep // 2 else ""
        if font.measure(f"{head}…{tail}") <= width:
            low = keep
        else:
            high = keep - 1
    head, tail = text[: (low + 1) // 2], text[len(text) - low // 2 :] if low // 2 else ""
    return f"{head}…{tail}"


@dataclass
class DownloadJob:
    number: int
    url: str
    output: Path
    start: float | None
    end: float | None
    exact: bool
    video_id: str | None = None
    queued_at: int = 0
    finished_at: float = 0.0
    token: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: str = "queued"
    title: str = ""
    status_key: str = "job.queued"
    status_values: dict[str, object] = field(default_factory=dict)
    percent: float | None = None
    downloaded: float | None = None
    total: float | None = None
    speed: float | None = None
    eta: float | None = None
    message_key: str | None = None
    message_values: dict[str, object] = field(default_factory=dict)
    result: Path | None = None
    process: subprocess.Popen[bytes] | None = None
    event_file: Path | None = None
    reported_error: bool = False
    auth_generation: int = 0

    def reset(self, queued_at: int) -> None:
        self.queued_at = queued_at
        self.finished_at = 0.0
        self.token = uuid.uuid4().hex[:12]
        self.state = "queued"
        self.status_key = "job.queued"
        self.status_values = {}
        self.percent = self.downloaded = self.total = self.speed = self.eta = None
        self.message_key = None
        self.message_values = {}
        self.result = None
        self.process = None
        self.event_file = None
        self.reported_error = False


class DownloadRow(ctk.CTkFrame):
    """One job in the downloads list: thumbnail, title, live status and its next action."""

    def __init__(self, master: tk.Misc, app: "ClipifyApp", job: DownloadJob) -> None:
        super().__init__(master, fg_color="transparent", corner_radius=0)
        self.app = app
        self.job = job
        self.grid_columnconfigure(1, weight=1)

        self.thumb = ctk.CTkLabel(
            self,
            text="",
            width=THUMB_SIZE[0],
            height=THUMB_SIZE[1],
            fg_color=COLORS["thumb"],
            corner_radius=4,
            image=app.images.get("thumb-placeholder"),
        )
        self.thumb.grid(row=0, column=0, rowspan=3, padx=(14, 12), pady=12, sticky="n")

        self.title = ctk.CTkLabel(self, text="", anchor="w", font=app.type.strong(13), text_color=COLORS["text"])
        self.title.grid(row=0, column=1, sticky="ew", pady=(11, 0))

        status_line = ctk.CTkFrame(self, fg_color="transparent")
        status_line.grid(row=1, column=1, sticky="ew", pady=(1, 0))
        status_line.grid_columnconfigure(1, weight=1)
        self.status_icon = ctk.CTkLabel(status_line, text="", width=14, height=18)
        self.status = ctk.CTkLabel(
            status_line,
            text="",
            anchor="w",
            justify="left",
            font=app.type.numbers(12),
            text_color=COLORS["muted"],
        )
        self.status.grid(row=0, column=1, sticky="ew")

        self.progress = ctk.CTkProgressBar(
            self,
            height=4,
            corner_radius=2,
            fg_color=COLORS["track"],
            progress_color=COLORS["accent"],
        )
        self.progress.set(0)
        self._progress_mode = "determinate"

        self.actions = ctk.CTkFrame(self, fg_color="transparent")
        self.actions.grid(row=0, column=2, rowspan=3, padx=(12, 14), pady=12, sticky="e")
        self.action = app.secondary_button(
            self.actions, "", self._run_action, height=30, width=96, size=12, focusable=False
        )
        self.action.grid(row=0, column=0)
        self._action_kind = ""

        hairline(self).grid(row=3, column=0, columnspan=3, sticky="ew", padx=14)
        self.bind("<Configure>", lambda _event: self._fit_texts(), add="+")
        for widget in (self, self.thumb, self.title, self.status):
            widget.bind("<Double-Button-1>", self.open_result, add="+")
        app.make_focusable(self.action, self._run_action)

    def _fit_texts(self) -> None:
        scaling = ctk.ScalingTracker.get_widget_scaling(self)
        width = self.title.winfo_width() / scaling
        if width > 20:
            self.title.configure(text=fit_end(self._title_text(), self.title.cget("font"), width - 4))
            self.status.configure(wraplength=max(120, width - 24))

    def _title_text(self) -> str:
        if self.job.title:
            return self.job.title
        return re.sub(r"^https?://(www\.)?", "", self.job.url)

    def set_thumbnail(self, image: ctk.CTkImage) -> None:
        # A rounded CTkLabel pads its image by the corner radius; the picture carries its own corners.
        self.thumb.configure(image=image, fg_color="transparent", corner_radius=0)

    def refresh(self) -> None:
        job, app = self.job, self.app
        range_text = describe_range(job.start, job.end, app.locale)
        icon_name = {
            "queued": "status-queued",
            "saved": "status-saved",
            "failed": "status-failed",
            "cancelled": "status-cancelled",
        }.get(job.state)
        tone = COLORS["danger"] if job.state == "failed" else COLORS["muted"]

        if job.state == "running":
            text = self._running_text(range_text)
        elif job.state == "saved":
            size = self._result_size()
            text = " · ".join(part for part in (app.tr("job.saved"), size, range_text) if part)
        elif job.state == "failed":
            text = app.tr(self._failure_key(), **job.message_values)
        elif job.state == "cancelled":
            text = f"{app.tr('job.cancelled')} · {range_text}"
        else:
            text = f"{app.tr('job.queued')} · {range_text}"

        self.status.configure(text=text, text_color=tone)
        if icon_name and icon_name in app.images:
            self.status_icon.configure(image=app.images[icon_name])
            self.status_icon.grid(row=0, column=0, padx=(0, 6), sticky="n")
        else:
            self.status_icon.grid_remove()

        if job.state == "running":
            self.progress.grid(row=2, column=1, sticky="ew", pady=(7, 13))
            if job.percent is None:
                if self._progress_mode != "indeterminate":
                    self.progress.configure(mode="indeterminate")
                    self.progress.start()
                    self._progress_mode = "indeterminate"
            else:
                if self._progress_mode != "determinate":
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                    self._progress_mode = "determinate"
                self.progress.set(max(0.0, min(job.percent / 100, 1.0)))
        else:
            if self._progress_mode == "indeterminate":
                self.progress.stop()
                self.progress.configure(mode="determinate")
                self._progress_mode = "determinate"
            self.progress.grid_remove()

        if job.state == "running":
            kind = "cancel"
        elif job.state == "queued":
            kind = "remove"
        elif job.state == "saved":
            kind = "show"
        else:
            kind = self._sign_in_kind() or "retry"
        self._set_action(kind)
        self._fit_texts()

    def _signed_in_since_failure(self) -> bool:
        return self.job.message_key in _SIGN_IN_ERRORS and self.job.auth_generation != self.app.auth_generation

    def _failure_key(self) -> str:
        key = self.job.message_key or "error.download"
        if self._signed_in_since_failure():
            return "job.signed_in_retry"
        if key == "error.video_private" and self.app.signed_in():
            return "error.video_private_no_access"
        return key

    def _sign_in_kind(self) -> str | None:
        """The next step for a sign-in failure: sign in (again) until a newer session exists."""

        job = self.job
        if job.state != "failed" or self._signed_in_since_failure():
            return None
        if job.message_key == "error.youtube_session_expired":
            return "sign_in_again"
        if job.message_key in {"error.youtube_auth_required", "error.video_private"} and not self.app.signed_in():
            return "sign_in"
        return None

    def _running_text(self, range_text: str) -> str:
        job, app = self.job, self.app
        if job.percent is None:
            stage = app.tr(job.status_key, **job.status_values)
            return f"{stage} · {range_text}"
        parts = [f"{job.percent:.0f}%"]
        downloaded = format_size(job.downloaded, app.locale)
        total = format_size(job.total, app.locale)
        if downloaded and total:
            parts.append(app.tr("progress.size", downloaded=downloaded, total=total))
        speed = format_speed(job.speed, app.locale)
        if speed:
            parts.append(speed)
        if job.eta is not None:
            parts.append(app.tr("progress.eta", time=format_duration(job.eta, app.locale)))
        return " · ".join(parts)

    def _result_size(self) -> str:
        try:
            if self.job.result and self.job.result.is_file():
                return format_size(self.job.result.stat().st_size, self.app.locale)
        except OSError:
            return ""
        return format_size(self.job.total, self.app.locale)

    def _set_action(self, kind: str) -> None:
        labels = {
            "cancel": "action.cancel",
            "remove": "action.remove",
            "show": "action.show_file",
            "sign_in": "action.sign_in",
            "sign_in_again": "session.sign_in_again",
            "retry": "action.retry",
        }
        self._action_kind = kind
        primary = kind in {"sign_in", "sign_in_again"}
        self.action.configure(
            text=self.app.tr(labels[kind]),
            width=118 if kind in {"show", "sign_in_again"} else 96,
            fg_color=COLORS["accent"] if primary else COLORS["button"],
            hover_color=COLORS["accent_hover"] if primary else COLORS["button_hover"],
            text_color=COLORS["on_accent"] if primary else COLORS["text"],
        )
        self.app.set_ring_base(self.action, 0 if primary else 1, COLORS["accent"] if primary else COLORS["field_border"])

    def _run_action(self) -> None:
        actions = {
            "cancel": self.app.cancel_job,
            "remove": self.app.remove_job,
            "show": self.app.show_result,
            "retry": self.app.retry_job,
            "sign_in": lambda _job: self.app.start_auth(),
            "sign_in_again": lambda _job: self.app.start_auth(),
        }
        actions[self._action_kind](self.job)

    def open_result(self, _event: object | None = None) -> None:
        if self.job.state == "saved":
            self.app.open_file(self.job)


class ClipifyApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=COLORS["window"])
        self.title("Clipify")
        self.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
        self.minsize(*MIN_SIZE)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.report_callback_exception = self._report_callback_exception

        settings = load_settings()
        saved_locale = settings.get("language")
        self.locale = saved_locale if saved_locale in SUPPORTED_LOCALES else system_locale()
        saved_folder = settings.get("folder")
        self.output_dir = Path(saved_folder) if isinstance(saved_folder, str) and Path(saved_folder).is_dir() else None

        self.type = Typography(self)
        self.events: queue.Queue[dict[str, object]] = queue.Queue()
        self.jobs: list[DownloadJob] = []
        self.rows: dict[int, DownloadRow] = {}
        self._job_counter = 0
        self.auth_in_progress = False
        self.auth_generation = 0
        self.auth_cancel_event = threading.Event()
        self._window_icon: tk.PhotoImage | None = None
        self._notice_after: str | None = None
        self._notice_key: str | None = None
        self._notice_values: dict[str, object] = {}
        self._link_error: str | None = None
        self._range_error: str | None = None
        self._thumbnails: dict[str, ctk.CTkImage] = {}
        self._placeholders: dict[ctk.CTkEntry, ctk.CTkLabel] = {}
        self._ring_base: dict[ctk.CTkBaseClass, tuple[int, tuple[str, str]]] = {}
        self._queue_counter = 0
        self.images: dict[str, ctk.CTkImage] = {}

        self.url_var = tk.StringVar()
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        self.exact_var = tk.BooleanVar(value=False)
        self.language_var = tk.StringVar(value=LOCALE_NAMES[self.locale])  # type: ignore[index]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._set_icon()
        self._load_images()
        self._build_header()
        self._build_form()
        self._build_notice()
        self._build_list()
        self._build_footer()
        self._refresh_copy()

        self.url_var.trace_add("write", self._on_link_changed)
        self.start_var.trace_add("write", self._on_range_changed)
        self.end_var.trace_add("write", self._on_range_changed)
        self._sync_download_button()
        self._install_thread_exception_handler()
        LOGGER.info("Clipify %s запущен; журнал: %s", __version__, portable_root() / LOG_FILENAME)
        self.bind("<Control-l>", self._focus_link)
        self.bind("<Control-L>", self._focus_link)
        self.bind("<Return>", lambda _event: self.queue_download())
        self.after(100, self._poll_events)

    # ----- assets -------------------------------------------------------------------------

    def _set_icon(self) -> None:
        assets = resource_root() / "assets"
        png_path = assets / "icon.png"
        ico_path = assets / "icon.ico"
        if not png_path.is_file():
            LOGGER.warning("Иконка окна не найдена: %s", png_path)
            return
        try:
            self._window_icon = tk.PhotoImage(file=str(png_path))
            self.iconphoto(True, self._window_icon)
            if os.name == "nt" and ico_path.is_file():
                self.iconbitmap(str(ico_path))
        except tk.TclError:
            LOGGER.exception("Не удалось установить иконку окна")
            self._window_icon = None

    @staticmethod
    def _pil_image(path: Path) -> Image.Image:
        with Image.open(path) as source:
            return source.convert("RGBA").copy()

    def _load_images(self) -> None:
        assets = resource_root() / "assets"
        icons = assets / "icons"
        sizes = {
            "status-queued": 14,
            "status-saved": 14,
            "status-failed": 14,
            "status-cancelled": 14,
            "notice-info": 16,
            "dismiss": 12,
            "thumb-placeholder": 20,
            "chevron": 12,
        }
        try:
            logo = self._pil_image(assets / "icon.png")
            download = self._pil_image(icons / "download.png")
            self.images["logo"] = ctk.CTkImage(light_image=logo, dark_image=logo, size=(30, 30))
            self.images["download"] = ctk.CTkImage(light_image=download, dark_image=download, size=(16, 16))
            for name, size in sizes.items():
                self.images[name] = ctk.CTkImage(
                    light_image=self._pil_image(icons / f"{name}-light.png"),
                    dark_image=self._pil_image(icons / f"{name}-dark.png"),
                    size=(size, size),
                )
            self.images["notice-success"] = ctk.CTkImage(
                light_image=self._pil_image(icons / "status-saved-light.png"),
                dark_image=self._pil_image(icons / "status-saved-dark.png"),
                size=(16, 16),
            )
            self.images["notice-danger"] = ctk.CTkImage(
                light_image=self._pil_image(icons / "status-failed-light.png"),
                dark_image=self._pil_image(icons / "status-failed-dark.png"),
                size=(16, 16),
            )
        except (OSError, ValueError):
            LOGGER.exception("Не удалось загрузить изображения интерфейса")

    # ----- building blocks -------------------------------------------------------------------

    def tr(self, key: str, **values: object) -> str:
        return translate(self.locale, key, **values)

    def secondary_button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], object],
        *,
        height: int = FIELD_HEIGHT,
        width: int = 0,
        size: int = 13,
        focusable: bool = True,
    ) -> ctk.CTkButton:
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,  # type: ignore[arg-type]
            width=width,
            height=height,
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLORS["field_border"],
            fg_color=COLORS["button"],
            hover_color=COLORS["button_hover"],
            text_color=COLORS["text"],
            text_color_disabled=COLORS["disabled_text"],
            font=self.type.strong(size),
        )
        self._ring_base[button] = (1, COLORS["field_border"])
        if focusable:
            self.make_focusable(button, command)
        return button

    def set_ring_base(self, widget: ctk.CTkBaseClass, width: int, color: tuple[str, str]) -> None:
        """Remember a control's resting border so the focus ring can restore it."""

        self._ring_base[widget] = (width, color)
        if self.focus_get() is widget:
            self._ring(widget, True)
        else:
            widget.configure(border_width=width, border_color=color)

    def _ring(self, widget: ctk.CTkBaseClass, on: bool) -> None:
        width, color = self._ring_base.get(widget, (0, COLORS["accent"]))
        if isinstance(widget, ctk.CTkLabel):
            widget.configure(font=self.type.link(12, underline=on))
            return
        if isinstance(widget, ctk.CTkCheckBox):
            widget.configure(border_color=COLORS["accent"] if on else COLORS["field_border_strong"])
            return
        if on:
            ring = COLORS["text"] if color == COLORS["accent"] else COLORS["accent"]
            widget.configure(border_width=_FOCUS_RING, border_color=ring)
        else:
            widget.configure(border_width=width, border_color=color)

    def make_focusable(self, widget: ctk.CTkBaseClass, activate: Callable[[], object]) -> None:
        """Let Tab reach a CustomTkinter control and Enter or Space press it, with a visible ring."""

        def press(_event: object) -> str:
            activate()
            return "break"

        # Tab focuses the frame itself; CustomTkinter's focus_set() moves focus to an inner label.
        # Bind both so the control answers the keyboard either way.
        tk.Frame.configure(widget, takefocus=1)
        for sequence in ("<Return>", "<KP_Enter>", "<space>"):
            tk.Frame.bind(widget, sequence, press, "+")
            widget.bind(sequence, press, add="+")
        for sequence, on in (("<FocusIn>", True), ("<FocusOut>", False)):
            tk.Frame.bind(widget, sequence, lambda _event, state=on: self._ring(widget, state), "+")
            widget.bind(sequence, lambda _event, state=on: self._ring(widget, state), add="+")

    def _entry(self, parent: tk.Misc, variable: tk.StringVar, *, width: int = 0) -> ctk.CTkEntry:
        entry = ctk.CTkEntry(
            parent,
            textvariable=variable,
            width=width or 140,
            height=FIELD_HEIGHT,
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLORS["field_border"],
            fg_color=COLORS["field"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted"],
            font=self.type.body(13),
        )
        entry.bind("<FocusIn>", lambda _event: self._mark_entry(entry, focused=True), add="+")
        entry.bind("<FocusOut>", lambda _event: self._mark_entry(entry, focused=False), add="+")

        # CustomTkinter hides placeholders on entries bound to a variable, so draw our own.
        placeholder = ctk.CTkLabel(
            entry,
            text="",
            width=1,
            height=1,
            anchor="w",
            cursor="xterm",
            text_color=COLORS["muted"],
            font=self.type.body(13),
        )
        placeholder.bind("<Button-1>", lambda _event: entry.focus_set(), add="+")

        def sync_placeholder(*_args: object) -> None:
            if variable.get():
                placeholder.place_forget()
            else:
                placeholder.place(x=8, rely=0.5, anchor="w")

        variable.trace_add("write", sync_placeholder)
        sync_placeholder()
        self._placeholders[entry] = placeholder
        return entry

    def _set_placeholder(self, entry: ctk.CTkEntry, text: str) -> None:
        self._placeholders[entry].configure(text=text)

    def _mark_entry(self, entry: ctk.CTkEntry, *, focused: bool) -> None:
        invalid = (entry is self.url_entry and self._link_error) or (
            entry in (self.start_entry, self.end_entry) and self._range_error and entry is self._range_error_entry
        )
        if invalid:
            entry.configure(border_color=COLORS["danger"], border_width=1)
        elif focused:
            entry.configure(border_color=COLORS["accent"], border_width=2)
        else:
            entry.configure(border_color=COLORS["field_border"], border_width=1)

    def _label(self, parent: tk.Misc, *, strong: bool = False, size: int = 13, tone: str = "text") -> ctk.CTkLabel:
        return ctk.CTkLabel(
            parent,
            text="",
            anchor="w",
            justify="left",
            text_color=COLORS[tone],
            font=self.type.strong(size) if strong else self.type.body(size),
        )

    def _link(
        self, parent: tk.Misc, command: Callable[[], object], *, size: int = 12, tone: str = "accent_text"
    ) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            parent,
            text="",
            cursor="hand2",
            text_color=COLORS[tone],
            font=self.type.link(size),
        )
        hover = self.type.link(size, underline=True)
        rest = self.type.link(size)
        label.bind("<Enter>", lambda _event: label.configure(font=hover), add="+")
        label.bind("<Leave>", lambda _event: label.configure(font=rest if self.focus_get() is not label else hover), add="+")
        label.bind("<Button-1>", lambda _event: command(), add="+")  # type: ignore[operator]
        self.make_focusable(label, command)  # type: ignore[arg-type]
        return label

    # ----- layout -------------------------------------------------------------------------

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent", height=56, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=PAGE_X)
        header.grid_columnconfigure(3, weight=1)
        header.grid_propagate(False)
        header.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(header, text="", image=self.images.get("logo"), width=30, height=30).grid(
            row=0, column=0, padx=(0, 10)
        )
        ctk.CTkLabel(
            header,
            text="Clipify",
            text_color=COLORS["text"],
            font=self.type.title(20),
        ).grid(row=0, column=1)
        self.by_label = self._label(header, size=12, tone="muted")
        self.by_label.grid(row=0, column=2, padx=(8, 0), pady=(5, 0))

        self.language_button = self.secondary_button(header, "", self._open_language_menu, height=32, width=112, size=12)
        self.language_button.configure(image=self.images.get("chevron"), compound="right", font=self.type.body(12))
        self.language_button.grid(row=0, column=4, sticky="e")
        self.language_menu = DropdownMenu(
            self,
            values=[LOCALE_NAMES[locale] for locale in SUPPORTED_LOCALES],
            command=self._change_locale,
            fg_color=COLORS["field"],
            hover_color=COLORS["menu"],
            text_color=COLORS["text"],
            font=self.type.body(13),
        )
        hairline(self).grid(row=1, column=0, sticky="ew")

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew", padx=PAGE_X, pady=(12, 0))
        form.grid_columnconfigure(0, weight=1)

        self.link_label = self._label(form, strong=True)
        self.link_label.grid(row=0, column=0, sticky="w")
        link_row = ctk.CTkFrame(form, fg_color="transparent")
        link_row.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        link_row.grid_columnconfigure(0, weight=1)
        self.url_entry = self._entry(link_row, self.url_var)
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.paste_button = self.secondary_button(link_row, "", self._paste_url, width=92)
        self.paste_button.grid(row=0, column=1)
        self.link_message = self._label(form, size=12, tone="danger")
        self.link_message.configure(height=20)
        self.link_message.grid(row=2, column=0, sticky="ew", pady=(2, 4))

        options = ctk.CTkFrame(form, fg_color="transparent")
        options.grid(row=3, column=0, sticky="ew")
        options.grid_columnconfigure(2, weight=1)
        self.start_label = self._label(options, strong=True)
        self.start_label.grid(row=0, column=0, sticky="w")
        self.end_label = self._label(options, strong=True)
        self.end_label.grid(row=0, column=1, sticky="w", padx=(12, 0))
        self.folder_label = self._label(options, strong=True)
        self.folder_label.grid(row=0, column=2, sticky="w", padx=(12, 0))

        self.start_entry = self._entry(options, self.start_var, width=120)
        self.start_entry.grid(row=1, column=0, pady=(6, 0))
        self.end_entry = self._entry(options, self.end_var, width=120)
        self.end_entry.grid(row=1, column=1, padx=(12, 0), pady=(6, 0))
        self._range_error_entry: ctk.CTkEntry | None = None
        for entry, variable in ((self.start_entry, self.start_var), (self.end_entry, self.end_var)):
            entry.bind("<FocusOut>", lambda _event, var=variable: self._normalize_time(var), add="+")

        folder_row = ctk.CTkFrame(options, fg_color="transparent")
        folder_row.grid(row=1, column=2, sticky="ew", padx=(12, 0), pady=(6, 0))
        folder_row.grid_columnconfigure(0, weight=1)
        self.folder_field = ctk.CTkFrame(
            folder_row,
            height=FIELD_HEIGHT,
            corner_radius=RADIUS,
            border_width=1,
            border_color=COLORS["field_border"],
            fg_color=COLORS["panel"],
        )
        self.folder_field.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.folder_field.grid_propagate(False)
        self.folder_field.grid_columnconfigure(0, weight=1)
        self.folder_field.grid_rowconfigure(0, weight=1)
        self.folder_value = ctk.CTkLabel(
            self.folder_field,
            text="",
            anchor="w",
            text_color=COLORS["text"],
            font=self.type.body(13),
            cursor="hand2",
        )
        self.folder_value.grid(row=0, column=0, sticky="ew", padx=12)
        for widget in (self.folder_field, self.folder_value):
            widget.bind("<Button-1>", lambda _event: self._choose_output(), add="+")
        self.folder_field.bind("<Configure>", lambda _event: self._refresh_folder(), add="+")
        self.folder_button = self.secondary_button(folder_row, "", self._choose_output, width=104)
        self.folder_button.grid(row=0, column=1)

        self.range_message = self._label(options, size=12, tone="muted")
        self.range_message.configure(height=20)
        self.range_message.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(2, 4))

        exact_row = ctk.CTkFrame(form, fg_color="transparent")
        exact_row.grid(row=4, column=0, sticky="w", pady=(2, 0))
        self.exact_box = ctk.CTkCheckBox(
            exact_row,
            text="",
            variable=self.exact_var,
            onvalue=True,
            offvalue=False,
            width=24,
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
            border_width=2,
            border_color=COLORS["field_border_strong"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            checkmark_color=COLORS["on_accent"],
            text_color=COLORS["text"],
            font=self.type.body(13),
        )
        self.exact_box.grid(row=0, column=0)
        self.make_focusable(self.exact_box, self.exact_box.toggle)
        self.exact_hint = self._label(exact_row, size=12, tone="muted")
        self.exact_hint.grid(row=0, column=1, padx=(10, 0))

        self.download_button = ctk.CTkButton(
            form,
            text="",
            image=self.images.get("download"),
            compound="left",
            height=PRIMARY_HEIGHT,
            corner_radius=RADIUS,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["on_accent"],
            text_color_disabled=COLORS["disabled_text"],
            font=self.type.strong(15),
            command=self.queue_download,
        )
        self.download_button.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        self._ring_base[self.download_button] = (0, COLORS["accent"])
        self.make_focusable(self.download_button, self.queue_download)

    def _build_notice(self) -> None:
        self.notice = ctk.CTkFrame(self, corner_radius=8, border_width=1)
        self.notice.grid_columnconfigure(1, weight=1)
        self.notice_icon = ctk.CTkLabel(self.notice, text="", width=16)
        self.notice_icon.grid(row=0, column=0, padx=(12, 8), pady=10, sticky="n")
        self.notice_text = ctk.CTkLabel(
            self.notice,
            text="",
            anchor="w",
            justify="left",
            text_color=COLORS["text"],
            font=self.type.body(12),
        )
        self.notice_text.grid(row=0, column=1, sticky="ew", pady=9)
        self.notice_close = ctk.CTkButton(
            self.notice,
            text="",
            image=self.images.get("dismiss"),
            width=26,
            height=26,
            corner_radius=RADIUS,
            fg_color="transparent",
            hover_color=COLORS["menu_hover"],
            border_color=COLORS["accent"],
            command=self._hide_notice,
        )
        self.notice_close.grid(row=0, column=2, padx=(6, 6), pady=6, sticky="n")
        self._ring_base[self.notice_close] = (0, COLORS["accent"])
        self.make_focusable(self.notice_close, self._hide_notice)
        self.notice.bind("<Configure>", self._wrap_notice, add="+")

    def _build_list(self) -> None:
        panel = ctk.CTkFrame(
            self,
            corner_radius=8,
            border_width=1,
            border_color=COLORS["hairline"],
            fg_color=COLORS["window"],
        )
        panel.grid(row=4, column=0, sticky="nsew", padx=PAGE_X, pady=(16, 0))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)

        head = ctk.CTkFrame(panel, fg_color="transparent", height=40)
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(2, 0))
        head.grid_columnconfigure(1, weight=1)
        head.grid_propagate(False)
        head.grid_rowconfigure(0, weight=1)
        self.list_title = self._label(head, strong=True)
        self.list_title.grid(row=0, column=0, sticky="w")
        self.list_count = self._label(head, size=12, tone="muted")
        self.list_count.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.clear_link = self._link(head, self.clear_finished)
        hairline(panel).grid(row=1, column=0, sticky="ew", padx=1)

        self.list_body = ctk.CTkScrollableFrame(
            panel,
            fg_color=COLORS["window"],
            corner_radius=0,
            scrollbar_button_color=COLORS["field_border"],
            scrollbar_button_hover_color=COLORS["field_border_strong"],
        )
        self.list_body.grid(row=2, column=0, sticky="nsew", padx=1, pady=(0, 6))
        self.list_body.grid_columnconfigure(0, weight=1)
        self.list_body._parent_canvas.bind("<Configure>", lambda _event: self._sync_scrollbar(), add="+")
        self.list_body.bind("<Configure>", lambda _event: self._sync_scrollbar(), add="+")

        self.empty_state = ctk.CTkFrame(self.list_body, fg_color="transparent")
        self.empty_state.grid_columnconfigure(0, weight=1)
        self.empty_title = self._label(self.empty_state, strong=True)
        self.empty_title.configure(anchor="center")
        self.empty_title.grid(row=0, column=0, pady=(26, 4))
        self.empty_body = self._label(self.empty_state, size=12, tone="muted")
        self.empty_body.configure(anchor="center", justify="center", wraplength=420)
        self.empty_body.grid(row=1, column=0, padx=24)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent", height=40)
        footer.grid(row=5, column=0, sticky="ew", padx=PAGE_X)
        footer.grid_propagate(False)
        footer.grid_rowconfigure(0, weight=1)
        footer.grid_columnconfigure(2, weight=1)
        self.session_label = self._label(footer, size=12, tone="secondary")
        self.session_label.grid(row=0, column=0, sticky="w")
        self.session_link = self._link(footer, self._session_action)
        self.session_link.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.version_label = self._label(footer, size=12, tone="muted")
        self.version_label.configure(text=f"v{__version__}")
        self.version_label.grid(row=0, column=3, sticky="e", padx=(0, 12))
        self.author_link = self._link(footer, self._open_author_link)
        self.author_link.configure(text="©PanCrucian")
        self.author_link.grid(row=0, column=4, sticky="e")

    # ----- copy and state ------------------------------------------------------------------

    def _open_language_menu(self) -> None:
        button = self.language_button
        self.language_menu.open(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height() + 4)

    def _change_locale(self, selection: str) -> None:
        locale = next((code for code, name in LOCALE_NAMES.items() if name == selection), DEFAULT_LOCALE)
        if locale == self.locale:
            return
        self.locale = locale
        save_settings(language=locale)
        self._refresh_copy()
        LOGGER.info("Язык интерфейса изменён: %s", locale)

    def _refresh_copy(self) -> None:
        self.language_var.set(LOCALE_NAMES[self.locale])  # type: ignore[index]
        self.language_button.configure(text=LOCALE_NAMES[self.locale])  # type: ignore[index]
        self.by_label.configure(text=self.tr("brand.by"))
        self.link_label.configure(text=self.tr("link.label"))
        self._set_placeholder(self.url_entry, self.tr("link.placeholder"))
        self.paste_button.configure(text=self.tr("link.paste"))
        self.start_label.configure(text=self.tr("range.start"))
        self.end_label.configure(text=self.tr("range.end"))
        self._set_placeholder(self.start_entry, self.tr("range.start.placeholder"))
        self._set_placeholder(self.end_entry, self.tr("range.end.placeholder"))
        self.folder_label.configure(text=self.tr("folder.label"))
        self.folder_button.configure(text=self.tr("folder.change"))
        self.exact_box.configure(text=self.tr("exact.label"))
        self.exact_hint.configure(text=self.tr("exact.hint"))
        self.list_title.configure(text=self.tr("list.title"))
        self.clear_link.configure(text=self.tr("list.clear"))
        self.empty_title.configure(text=self.tr("list.empty.title"))
        self.empty_body.configure(text=self.tr("list.empty.body"))
        self._show_link_error(self._link_error)
        self._show_range_message()
        self._sync_download_button()
        self._refresh_folder()
        self._refresh_session()
        self._refresh_list()
        if self._notice_key:
            self.notice_text.configure(text=self.tr(self._notice_key, **self._notice_values))

    def _refresh_folder(self) -> None:
        path = str(self.output_dir or portable_root())
        scaling = ctk.ScalingTracker.get_widget_scaling(self)
        width = self.folder_field.winfo_width() / scaling - 26
        self.folder_value.configure(text=fit_middle(path, self.folder_value.cget("font"), width))

    def _refresh_session(self) -> None:
        if self.auth_in_progress:
            self.session_label.configure(text=self.tr("session.waiting"))
            self.session_link.configure(text=self.tr("session.cancel"))
        elif self.signed_in():
            self.session_label.configure(text=self.tr("session.signed_in"))
            self.session_link.configure(text=self.tr("session.sign_in_again"))
        else:
            self.session_label.configure(text=self.tr("session.signed_out"))
            self.session_link.configure(text=self.tr("session.sign_in"))

    def _refresh_list(self) -> None:
        finished = sum(1 for job in self.jobs if job.state in FINISHED_STATES)
        self.list_count.configure(text=str(len(self.jobs)) if self.jobs else "")
        if finished:
            self.clear_link.grid(row=0, column=2, sticky="e")
        else:
            self.clear_link.grid_remove()
        if self.jobs:
            self.empty_state.grid_remove()
        else:
            self.empty_state.grid(row=0, column=0, sticky="ew")
        for job in self.jobs:
            if job.state in FINISHED_STATES and not job.finished_at:
                job.finished_at = time.monotonic()
            self.rows[job.number].refresh()
        self._regrid_rows()
        self._sync_title()
        self.after_idle(self._sync_scrollbar)

    def _sync_title(self) -> None:
        running = self._running_job()
        if running and running.percent is not None:
            self.title(f"{running.percent:.0f}% · Clipify")
        else:
            self.title("Clipify")

    def _request_attention(self) -> None:
        """Flash the taskbar button when a download ends while Clipify is in the background."""

        if os.name != "nt" or self.focus_displayof() is not None:
            return

        class FlashInfo(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint),
                ("hwnd", ctypes.c_void_p),
                ("dwFlags", ctypes.c_uint),
                ("uCount", ctypes.c_uint),
                ("dwTimeout", ctypes.c_uint),
            ]

        try:
            handle = ctypes.windll.user32.GetParent(self.winfo_id())  # type: ignore[attr-defined]
            info = FlashInfo(ctypes.sizeof(FlashInfo), handle, 0x2 | 0xC, 0, 0)  # tray until focused
            ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))  # type: ignore[attr-defined]
        except (OSError, AttributeError):
            LOGGER.debug("Не удалось привлечь внимание к окну", exc_info=True)

    def _sync_scrollbar(self) -> None:
        canvas = self.list_body._parent_canvas
        try:
            overflow = canvas.yview() != (0.0, 1.0)
        except tk.TclError:
            return
        scrollbar = self.list_body._scrollbar
        if overflow and not scrollbar.winfo_ismapped():
            scrollbar.grid()
        elif not overflow and scrollbar.winfo_ismapped():
            scrollbar.grid_remove()

    def signed_in(self) -> bool:
        return youtube_cookie_path().is_file()

    def _sync_download_button(self, *_args: object) -> None:
        clip = bool(self.start_var.get().strip() or self.end_var.get().strip())
        self.download_button.configure(text=self.tr("action.download_clip" if clip else "action.download_video"))

    def _on_link_changed(self, *_args: object) -> None:
        if self._link_error:
            self._show_link_error(None)
        self._sync_download_button()

    def _on_range_changed(self, *_args: object) -> None:
        if self._range_error:
            self._range_error = None
            self._range_error_entry = None
            self._show_range_message()
        self._sync_download_button()

    def _show_link_error(self, key: str | None) -> None:
        self._link_error = key
        self.link_message.configure(text=self.tr(key) if key else "")
        self._mark_entry(self.url_entry, focused=self.focus_get() is self.url_entry._entry)

    def _show_range_message(self) -> None:
        if self._range_error:
            self.range_message.configure(text=self.tr(self._range_error), text_color=COLORS["danger"])
        else:
            self.range_message.configure(text=self.tr("range.hint"), text_color=COLORS["muted"])
        for entry in (self.start_entry, self.end_entry):
            self._mark_entry(entry, focused=self.focus_get() is entry._entry)

    def _wrap_notice(self, _event: object | None = None) -> None:
        scaling = ctk.ScalingTracker.get_widget_scaling(self)
        width = self.notice.winfo_width() / scaling - 80
        if width > 100:
            self.notice_text.configure(wraplength=width)

    # ----- notices ------------------------------------------------------------------------

    def show_notice(self, key: str, tone: str = "info", *, auto_hide: bool = False, **values: object) -> None:
        palettes = {
            "info": ("info_soft", "info_line", "notice-info"),
            "success": ("success_soft", "success_line", "notice-success"),
            "danger": ("danger_soft", "danger_line", "notice-danger"),
        }
        background, line, icon = palettes.get(tone, palettes["info"])
        self._notice_key = key
        self._notice_values = values
        self.notice.configure(fg_color=COLORS[background], border_color=COLORS[line])
        self.notice_icon.configure(image=self.images.get(icon))
        text = self.tr(key, **values)
        self.notice_text.configure(text=text)
        self.notice.grid(row=3, column=0, sticky="ew", padx=PAGE_X, pady=(14, 0))
        self._wrap_notice()
        if self._notice_after is not None:
            self.after_cancel(self._notice_after)
            self._notice_after = None
        if auto_hide:
            self._notice_after = self.after(reading_time_ms(text) + 2000, self._hide_notice)

    def _hide_notice(self) -> None:
        if self._notice_after is not None:
            try:
                self.after_cancel(self._notice_after)
            except tk.TclError:
                pass
            self._notice_after = None
        self._notice_key = None
        self._notice_values = {}
        self.notice.grid_remove()

    # ----- form actions -------------------------------------------------------------------

    def _focus_link(self, _event: object | None = None) -> str:
        self.url_entry.focus_set()
        self.url_entry.select_range(0, "end")
        return "break"

    def _paste_url(self) -> None:
        try:
            value = self.clipboard_get().strip()
        except tk.TclError:
            value = ""
        if not value:
            self._show_link_error("link.error.empty_clipboard")
            return
        self.url_var.set(value)
        self.url_entry.focus_set()
        self.url_entry.icursor("end")
        try:
            normalize_youtube_url(value)
        except ValueError as exc:
            self._show_link_error(str(exc))

    def _choose_output(self) -> None:
        initial = str(self.output_dir or portable_root())
        try:
            selected = filedialog.askdirectory(parent=self, initialdir=initial, title=self.tr("folder.dialog"))
        except (OSError, tk.TclError):
            LOGGER.exception("Не удалось открыть выбор папки")
            self.show_notice("error.choose_folder", "danger")
            return
        if selected:
            self.output_dir = Path(selected)
            save_settings(folder=str(self.output_dir))
            self._refresh_folder()

    def _normalize_time(self, variable: tk.StringVar) -> None:
        value = variable.get().strip()
        if not value:
            return
        try:
            formatted = format_timecode(parse_timecode(value))
        except TimecodeError:
            return
        if formatted != value:
            variable.set(formatted)

    def queue_download(self) -> None:
        if not self.url_var.get().strip():
            self._show_link_error("link.error.empty")
            self.url_entry.focus_set()
            return
        try:
            url = normalize_youtube_url(self.url_var.get())
        except ValueError as exc:
            self._show_link_error(str(exc))
            self.url_entry.focus_set()
            return
        start = end = None
        for entry, variable, target in ((self.start_entry, self.start_var, "start"), (self.end_entry, self.end_var, "end")):
            try:
                value = parse_timecode(variable.get())
            except TimecodeError as exc:
                self._range_error, self._range_error_entry = exc.message_key, entry
                self._show_range_message()
                entry.focus_set()
                return
            if target == "start":
                start = value
            else:
                end = value
        try:
            validate_time_range(start, end)
        except TimecodeError as exc:
            self._range_error, self._range_error_entry = exc.message_key, self.end_entry
            self._show_range_message()
            self.end_entry.focus_set()
            return

        self._job_counter += 1
        self._queue_counter += 1
        job = DownloadJob(
            number=self._job_counter,
            queued_at=self._queue_counter,
            url=url,
            output=(self.output_dir or portable_root()).expanduser(),
            start=start,
            end=end,
            exact=bool(self.exact_var.get()),
            video_id=youtube_video_id(url),
        )
        self.jobs.append(job)
        self.rows[job.number] = DownloadRow(self.list_body, self, job)
        self._fetch_thumbnail(job)
        LOGGER.info("Загрузка #%s добавлена: %s", job.number, describe_range(start, end, "ru"))

        self.url_var.set("")
        self.start_var.set("")
        self.end_var.set("")
        self.url_entry.focus_set()
        self._refresh_list()
        self._start_next_job()

    def _display_order(self) -> list[DownloadJob]:
        running = [job for job in self.jobs if job.state == "running"]
        waiting = sorted((job for job in self.jobs if job.state == "queued"), key=lambda job: job.queued_at)
        finished = sorted(
            (job for job in self.jobs if job.state in FINISHED_STATES),
            key=lambda job: job.finished_at,
            reverse=True,
        )
        return running + waiting + finished

    def _regrid_rows(self) -> None:
        for index, job in enumerate(self._display_order()):
            self.rows[job.number].grid(row=index + 1, column=0, sticky="ew")

    # ----- jobs ---------------------------------------------------------------------------

    def _running_job(self) -> DownloadJob | None:
        return next((job for job in self.jobs if job.state == "running"), None)

    def _job(self, number: object) -> DownloadJob | None:
        return next((job for job in self.jobs if job.number == number), None)

    def _start_next_job(self) -> None:
        if self.auth_in_progress or self._running_job():
            return
        waiting = sorted((job for job in self.jobs if job.state == "queued"), key=lambda job: job.queued_at)
        if waiting:
            self._launch(waiting[0])

    def _launch(self, job: DownloadJob) -> None:
        try:
            event_handle = tempfile.NamedTemporaryFile(prefix="clipify-events-", suffix=".jsonl", delete=False)
            event_handle.close()
            job.event_file = Path(event_handle.name)
            command = [
                *worker_command(),
                "--url",
                job.url,
                "--output",
                str(job.output),
                "--event-file",
                str(job.event_file),
                "--job-token",
                job.token,
            ]
            if job.start is not None:
                command.extend(("--start", str(job.start)))
            if job.end is not None:
                command.extend(("--end", str(job.end)))
            if job.exact:
                command.append("--exact")
            cookie_file = youtube_cookie_path()
            if cookie_file.is_file():
                command.extend(("--cookies-file", str(cookie_file)))

            environment = os.environ.copy()
            environment["PYTHONUTF8"] = "1"
            environment["PYTHONIOENCODING"] = "utf-8"
            popen_options: dict[str, object] = {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
                "env": environment,
            }
            if os.name == "nt":
                popen_options["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                popen_options["start_new_session"] = True
            job.process = subprocess.Popen(command, **popen_options)  # type: ignore[arg-type]
        except (OSError, ValueError):
            LOGGER.exception("Не удалось запустить процесс загрузки #%s", job.number)
            if job.event_file is not None:
                job.event_file.unlink(missing_ok=True)
            job.event_file = None
            job.state = "failed"
            job.message_key = "error.start_download"
            self._refresh_list()
            self.after(50, self._start_next_job)
            return

        LOGGER.info("Запущена загрузка #%s в %s", job.number, job.output)
        job.state = "running"
        job.status_key = "status.preparing"
        self._refresh_list()
        threading.Thread(
            target=self._read_worker,
            args=(job.number, job.process, job.event_file),
            name=f"clipify-worker-events-{job.number}",
            daemon=True,
        ).start()

    def _read_worker(self, number: int, process: subprocess.Popen[bytes], event_file: Path) -> None:
        position = 0
        read_error_logged = False
        try:
            while True:
                try:
                    with event_file.open("r", encoding="utf-8") as stream:
                        stream.seek(position)
                        lines = stream.readlines()
                        position = stream.tell()
                except OSError:
                    lines = []
                    if not read_error_logged:
                        LOGGER.exception("Не удалось прочитать канал событий загрузчика")
                        read_error_logged = True

                self._queue_event_lines(number, lines)
                if process.poll() is not None:
                    try:
                        with event_file.open("r", encoding="utf-8") as stream:
                            stream.seek(position)
                            self._queue_event_lines(number, stream.readlines())
                    except OSError:
                        if not read_error_logged:
                            LOGGER.exception("Не удалось прочитать финальные события загрузчика")
                    break
                time.sleep(0.08)

            code = process.wait()
            try:
                event_file.unlink(missing_ok=True)
            except OSError:
                LOGGER.exception("Не удалось удалить временный канал событий")
            self.events.put({"job": number, "event": "process_exit", "code": code})
        except Exception:  # noqa: BLE001 - surface every background failure in the GUI
            LOGGER.exception("Сбой чтения событий загрузчика")
            self.events.put({"job": number, "event": "error", "key": "error.worker_read"})

    def _queue_event_lines(self, number: int, lines: list[str]) -> None:
        for raw_line in lines:
            line = raw_line.strip()
            if not line.startswith(EVENT_PREFIX):
                if line:
                    LOGGER.warning("Неизвестный вывод загрузчика: %s", line[:500])
                continue
            try:
                event = json.loads(line[len(EVENT_PREFIX) :])
            except json.JSONDecodeError:
                LOGGER.exception("Повреждённое событие загрузчика: %s", line[:500])
                continue
            if isinstance(event, dict):
                self.events.put({**event, "job": number})

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                try:
                    self._handle_event(event)
                except Exception:  # noqa: BLE001 - the event loop must stay alive
                    LOGGER.exception("Не удалось обработать событие: %r", event)
                    self.show_notice("error.system", "danger", log=LOG_FILENAME)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _handle_event(self, event: dict[str, object]) -> None:
        kind = event.get("event")
        if kind in {"auth_success", "auth_error", "auth_cancelled"}:
            self._handle_auth_event(event)
            return
        if kind == "thumbnail":
            self._apply_thumbnail(event)
            return
        if kind == "ui_exception":
            self.show_notice(str(event.get("key") or "error.system"), "danger", log=LOG_FILENAME)
            return

        job = self._job(event.get("job"))
        if job is None:
            return
        row = self.rows.get(job.number)
        if kind == "status":
            key = event.get("key")
            if isinstance(key, str) and key and job.state == "running":
                job.status_key = key
                job.status_values = {name: value for name, value in event.items() if name not in {"event", "key", "job"}}
                if key != "status.starting_download":
                    job.percent = None
        elif kind == "meta":
            title = event.get("title")
            if isinstance(title, str) and title.strip():
                job.title = title.strip()
            video_id = event.get("video_id")
            if isinstance(video_id, str) and not job.video_id and _VIDEO_ID.match(video_id):
                job.video_id = video_id
                self._fetch_thumbnail(job)
        elif kind == "progress" and job.state == "running":
            percent = event.get("percent")
            job.percent = float(percent) if isinstance(percent, (int, float)) else job.percent
            for name in ("downloaded", "total", "speed", "eta"):
                value = event.get(name)
                setattr(job, name, float(value) if isinstance(value, (int, float)) else None)
        elif kind == "complete":
            job.result = Path(str(event.get("filepath") or job.output))
            job.state = "saved"
            job.percent = 100.0
            LOGGER.info("Загрузка #%s сохранена: %s", job.number, job.result)
        elif kind == "error":
            if job.state == "cancelled":
                return
            job.reported_error = True
            job.state = "failed"
            job.auth_generation = self.auth_generation
            key = event.get("key")
            job.message_key = key if isinstance(key, str) and key else "error.download"
            job.message_values = {
                name: value for name, value in event.items() if name not in {"event", "key", "job", "text"}
            }
            LOGGER.error("Загрузка #%s не удалась: %s", job.number, job.message_key)
        elif kind == "process_exit":
            code = event.get("code")
            job.process = None
            if job.state == "running":
                if code == 0:
                    job.state = "saved"
                    job.result = job.result or job.output
                elif not job.reported_error:
                    job.state = "failed"
                    job.message_key = "error.download_exit"
            if job.state in FINISHED_STATES:
                self._request_attention()
            if job.state == "cancelled":
                self._discard_partial_files(job)
            self._refresh_list()
            self._start_next_job()
            return
        if row is not None:
            row.refresh()
        if kind == "progress":
            self._sync_title()
        if kind in {"complete", "error"}:
            self._refresh_list()

    def cancel_job(self, job: DownloadJob) -> None:
        process = job.process
        if job.state != "running" or not process or process.poll() is not None:
            return
        job.state = "cancelled"
        self._terminate_process_tree(process)
        LOGGER.info("Загрузка #%s отменена", job.number)
        self._refresh_list()

    def remove_job(self, job: DownloadJob) -> None:
        if job.state == "running":
            return
        self.jobs = [item for item in self.jobs if item is not job]
        row = self.rows.pop(job.number, None)
        if row is not None:
            row.destroy()
        self._refresh_list()

    def retry_job(self, job: DownloadJob) -> None:
        if job.state not in {"failed", "cancelled"}:
            return
        self._queue_counter += 1
        job.reset(self._queue_counter)
        self._refresh_list()
        self._start_next_job()

    def clear_finished(self) -> None:
        for job in [job for job in self.jobs if job.state in FINISHED_STATES]:
            self.remove_job(job)

    def show_result(self, job: DownloadJob) -> None:
        target = job.result if job.result and job.result.exists() else job.output
        try:
            if target.is_file():
                if os.name == "nt":
                    subprocess.Popen(["explorer", f"/select,{target}"])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", "-R", str(target)])
                else:
                    subprocess.Popen(["xdg-open", str(target.parent)])
            elif target.is_dir():
                if os.name == "nt":
                    os.startfile(target)  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(target)])
                else:
                    subprocess.Popen(["xdg-open", str(target)])
            else:
                raise FileNotFoundError(target)
        except (OSError, ValueError):
            LOGGER.exception("Не удалось открыть папку %s", target)
            self.show_notice("error.open_folder", "danger")

    def open_file(self, job: DownloadJob) -> None:
        target = job.result
        if not target or not target.is_file():
            self.show_result(job)
            return
        try:
            if os.name == "nt":
                os.startfile(target)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
        except (OSError, ValueError):
            LOGGER.exception("Не удалось открыть файл %s", target)
            self.show_notice("error.open_folder", "danger")

    def _discard_partial_files(self, job: DownloadJob) -> None:
        marker = f".__clipify_{job.token}"
        try:
            for path in job.output.iterdir():
                if marker in path.name and path.is_file():
                    path.unlink(missing_ok=True)
        except OSError:
            LOGGER.warning("Не удалось удалить недокачанные файлы #%s", job.number, exc_info=True)

    def _terminate_process_tree(self, process: subprocess.Popen[bytes]) -> None:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                os.killpg(process.pid, signal.SIGTERM)
        except OSError:
            LOGGER.exception("Не удалось завершить дерево процессов штатно")
            try:
                process.kill()
            except OSError:
                LOGGER.exception("Не удалось принудительно завершить процесс")

    # ----- thumbnails ---------------------------------------------------------------------

    def _fetch_thumbnail(self, job: DownloadJob) -> None:
        video_id = job.video_id
        if not video_id:
            return
        if video_id in self._thumbnails:
            self.rows[job.number].set_thumbnail(self._thumbnails[video_id])
            return

        def download() -> None:
            try:
                request = Request(THUMBNAIL_URL.format(video_id=video_id), headers={"User-Agent": "Clipify"})
                with urlopen(request, timeout=6) as response:  # noqa: S310 - fixed HTTPS host
                    data = response.read(512_000)
                image = Image.open(BytesIO(data)).convert("RGBA")
            except (OSError, ValueError):
                LOGGER.info("Обложка %s недоступна", video_id)
                return
            self.events.put({"event": "thumbnail", "video_id": video_id, "image": image})

        threading.Thread(target=download, name=f"clipify-thumb-{video_id}", daemon=True).start()

    def _apply_thumbnail(self, event: dict[str, object]) -> None:
        video_id, image = event.get("video_id"), event.get("image")
        if not isinstance(video_id, str) or not isinstance(image, Image.Image):
            return
        scale = 3
        framed = image.resize((THUMB_SIZE[0] * scale, THUMB_SIZE[1] * scale), Image.Resampling.LANCZOS)
        mask = Image.new("L", framed.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, *framed.size), radius=4 * scale, fill=255)
        framed.putalpha(mask)
        picture = ctk.CTkImage(light_image=framed, dark_image=framed, size=THUMB_SIZE)
        self._thumbnails[video_id] = picture
        for job in self.jobs:
            if job.video_id == video_id:
                self.rows[job.number].set_thumbnail(picture)

    # ----- YouTube sign-in ----------------------------------------------------------------

    def _session_action(self) -> None:
        if self.auth_in_progress:
            self.auth_cancel_event.set()
        else:
            self.start_auth()

    def start_auth(self) -> None:
        if self.auth_in_progress:
            return
        self.auth_in_progress = True
        self.auth_cancel_event.clear()
        self._refresh_session()
        self.show_notice("notice.auth_started", "info")
        threading.Thread(target=self._run_auth, name="clipify-youtube-auth", daemon=True).start()

    def _run_auth(self) -> None:
        try:
            cookie_file, browser = authorize_youtube(self.auth_cancel_event)
            LOGGER.info("Авторизация YouTube завершена через %s; cookies: %s", browser, cookie_file)
            self.events.put({"event": "auth_success", "browser": browser})
        except BrowserAuthCancelled:
            LOGGER.info("Авторизация YouTube отменена")
            self.events.put({"event": "auth_cancelled"})
        except BrowserAuthError as exc:
            LOGGER.exception("Не удалось авторизоваться в YouTube")
            self.events.put({"event": "auth_error", "key": exc.message_key, **exc.values})
        except Exception as exc:  # noqa: BLE001 - auth failures must reach the GUI
            LOGGER.exception("Неожиданная ошибка авторизации YouTube")
            self.events.put({"event": "auth_error", "key": "error.auth_failed", "error": str(exc)})

    def _handle_auth_event(self, event: dict[str, object]) -> None:
        self.auth_in_progress = False
        kind = event.get("event")
        if kind == "auth_success":
            self.auth_generation += 1
            self.show_notice("notice.auth_success", "success", auto_hide=True, browser=event.get("browser", ""))
        elif kind == "auth_error":
            key = event.get("key")
            self.show_notice(key if isinstance(key, str) and key else "error.auth_failed", "danger")
        else:
            self._hide_notice()
        self._refresh_session()
        self._refresh_list()
        self._start_next_job()

    # ----- misc ---------------------------------------------------------------------------

    def _open_author_link(self) -> None:
        try:
            if not webbrowser.open(AUTHOR_URL):
                raise OSError("browser rejected the link")
        except Exception:  # noqa: BLE001 - system browser errors vary by platform
            LOGGER.exception("Не удалось открыть ссылку автора")
            self.show_notice("error.open_author", "danger")

    def _install_thread_exception_handler(self) -> None:
        def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
            LOGGER.error(
                "Необработанное исключение в потоке %s",
                args.thread.name if args.thread else "unknown",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )
            self.events.put({"event": "ui_exception", "key": "error.system"})

        threading.excepthook = handle_thread_exception

    def _report_callback_exception(self, exc_type: type[BaseException], exc: BaseException, trace: object) -> None:
        LOGGER.error("Ошибка обработчика интерфейса", exc_info=(exc_type, exc, trace))
        self.show_notice("error.system", "danger", log=LOG_FILENAME)

    def _on_close(self) -> None:
        self.auth_cancel_event.set()
        for job in self.jobs:
            if job.process and job.process.poll() is None:
                job.state = "cancelled"
                self._terminate_process_tree(job.process)
        LOGGER.info("Clipify завершён")
        self.destroy()


def run_app() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app_id_ready = set_windows_app_id()

    def handle_unhandled(exc_type: type[BaseException], exc: BaseException, trace: object) -> None:
        LOGGER.critical("Необработанная ошибка приложения", exc_info=(exc_type, exc, trace))

    sys.excepthook = handle_unhandled
    app = ClipifyApp()
    if not app_id_ready:
        app.after(
            250,
            lambda: app.show_notice(
                "error.missing_component",
                "danger",
                component=app.tr("component.windows_icon"),
                log=LOG_FILENAME,
            ),
        )
    app.mainloop()
