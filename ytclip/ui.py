from __future__ import annotations

import ctypes
import json
import os
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog
from urllib.parse import urlparse

import customtkinter as ctk
from PIL import Image

from .font_loader import FONT_FAMILY, register_bundled_font
from .logging_utils import LOG_FILENAME, get_logger
from .platform_tools import portable_root, resource_root, worker_command
from .timecode import TimecodeError, describe_range, format_timecode, parse_timecode, validate_time_range
from .worker import EVENT_PREFIX


LOGGER = get_logger("ui")
COMPACT_WIDTH = 615
COMPACT_HEIGHT = 500
PROGRESS_HEIGHT = 565


def toast_duration_ms(text: str) -> int:
    """Estimate comfortable toast reading time at roughly 190 words/minute."""

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

COLORS = {
    "background": ("#F4F6FB", "#0B1020"),
    "surface": ("#FFFFFF", "#121A2E"),
    "surface_alt": ("#F7F8FC", "#0F1729"),
    "surface_hover": ("#EEF1F7", "#19243D"),
    "border": ("#DCE2EE", "#263451"),
    "text": ("#172033", "#F5F7FF"),
    "muted": ("#69758C", "#9AA7C2"),
    "subtle": ("#8A94A7", "#6F7C98"),
    "accent": ("#6948F5", "#7C5CFC"),
    "accent_hover": ("#5938E3", "#9278FF"),
    "accent_soft": ("#EEEAFE", "#211D45"),
    "accent_text": ("#5A3BDC", "#C9BDFF"),
    "progress_track": ("#E6E9F1", "#202A43"),
    "success": ("#0F9B75", "#2DD4A4"),
    "success_soft": ("#E3F7F1", "#123A35"),
    "success_hover": ("#CDEFE5", "#195147"),
    "warning": ("#B96A05", "#FFB454"),
    "warning_soft": ("#FFF3DC", "#3C2C1A"),
    "danger": ("#D43B52", "#FF6B7A"),
    "danger_soft": ("#FCE8EC", "#3C202B"),
}


class ClipifyApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=COLORS["background"])
        self.title("Clipify")
        self.geometry(f"{COMPACT_WIDTH}x{COMPACT_HEIGHT}")
        self.minsize(COMPACT_WIDTH, COMPACT_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.report_callback_exception = self._report_callback_exception

        self.process: subprocess.Popen[str] | None = None
        self.events: queue.Queue[dict[str, object]] = queue.Queue()
        self.last_output: Path | None = None
        self.event_file: Path | None = None
        self.had_worker_error = False
        self.cancelled = False
        self._progress_running = False
        self._window_icon: tk.PhotoImage | None = None
        self._toast_after: str | None = None
        self._auto_expanded = False
        self._images: dict[str, ctk.CTkImage] = {}

        self.url_var = tk.StringVar()
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.exact_var = tk.BooleanVar(value=False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._set_icon()
        self._load_images()
        self._build_ui()
        self.url_var.trace_add("write", self._sync_primary_download_state)
        self._sync_primary_download_state()
        self._install_thread_exception_handler()
        LOGGER.info("Clipify запущен; журнал: %s", portable_root() / LOG_FILENAME)
        self.after(100, self._poll_events)

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
        try:
            app_icon = self._pil_image(assets / "icon.png")
            download = self._pil_image(icons / "download.png")
            folder_light = self._pil_image(icons / "folder-light.png")
            folder_dark = self._pil_image(icons / "folder-dark.png")
            question_light = self._pil_image(icons / "question-light.png")
            question_dark = self._pil_image(icons / "question-dark.png")
            self._images = {
                "app": ctk.CTkImage(light_image=app_icon, dark_image=app_icon, size=(56, 56)),
                "download": ctk.CTkImage(light_image=download, dark_image=download, size=(18, 18)),
                "folder": ctk.CTkImage(
                    light_image=folder_light,
                    dark_image=folder_dark,
                    size=(18, 18),
                ),
                "question": ctk.CTkImage(
                    light_image=question_light,
                    dark_image=question_dark,
                    size=(17, 17),
                ),
            }
        except (OSError, ValueError):
            LOGGER.exception("Не удалось загрузить изображения интерфейса")
            self._images = {}

    def _build_ui(self) -> None:
        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.grid(row=0, column=0, sticky="nsew", padx=30, pady=(24, 26))
        shell.grid_columnconfigure(0, weight=1)

        self._build_header(shell)
        self._build_form(shell)
        self._build_toast()

    def _build_header(self, parent: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="",
            image=self._images.get("app"),
            width=56,
            height=56,
        ).grid(row=0, column=0, rowspan=2, padx=(0, 14))
        ctk.CTkLabel(
            header,
            text="Clipify by PanCrucian",
            anchor="w",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=26, weight="bold"),
        ).grid(row=0, column=1, columnspan=2, sticky="sw")
        ctk.CTkLabel(
            header,
            text="Скачивайте YouTube видео целиком или фрагментом",
            anchor="w",
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=1, sticky="nw", pady=(0, 2))
        copyright_label = ctk.CTkLabel(
            header,
            text="©PanCrucian",
            anchor="e",
            text_color=COLORS["accent_text"],
            font=ctk.CTkFont(size=12, underline=True),
        )
        copyright_label.grid(row=1, column=2, sticky="ne", pady=(0, 2))
        copyright_label.bind("<Button-1>", self._open_author_link)

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["surface"],
            corner_radius=22,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=1, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=0, column=0, sticky="ew", padx=22, pady=20)
        content.grid_columnconfigure(0, weight=1)

        self._field_label(content, "Ссылка на YouTube", row=0)
        url_row = ctk.CTkFrame(content, fg_color="transparent")
        url_row.grid(row=1, column=0, sticky="ew", pady=(7, 18))
        url_row.grid_columnconfigure(0, weight=1)
        self.url_entry = self._entry(url_row, self.url_var, "https://youtube.com/watch?v=…")
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.paste_button = ctk.CTkButton(
            url_row,
            text="Вставить",
            width=90,
            height=42,
            corner_radius=12,
            fg_color=COLORS["accent_soft"],
            hover_color=COLORS["surface_hover"],
            text_color=COLORS["accent_text"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._paste_url,
        )
        self.paste_button.grid(row=0, column=1)

        optional_header = ctk.CTkFrame(content, fg_color="transparent")
        optional_header.grid(row=2, column=0, sticky="ew")
        self._field_label(optional_header, "Опциональные параметры", row=0)

        optional_row = ctk.CTkFrame(content, fg_color="transparent")
        optional_row.grid(row=3, column=0, sticky="ew", pady=(7, 18))
        optional_row.grid_columnconfigure(3, weight=1)

        start_group = self._compact_field(optional_row, "Начало", column=0)
        self.start_entry = self._entry(start_group, self.start_var, "0:00", width=112)
        self.start_entry.grid(row=1, column=0)
        ctk.CTkLabel(
            optional_row,
            text="→",
            width=28,
            text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=17),
        ).grid(row=0, column=1, sticky="s", pady=(0, 8))
        end_group = self._compact_field(optional_row, "Конец", column=2)
        self.end_entry = self._entry(end_group, self.end_var, "1:30", width=112)
        self.end_entry.grid(row=1, column=0)
        self.start_entry.bind("<FocusOut>", lambda _event: self._normalize_time(self.start_var))
        self.end_entry.bind("<FocusOut>", lambda _event: self._normalize_time(self.end_var))
        self.range_hint = ctk.CTkLabel(
            optional_row,
            text="Форматы: секунды или часы:минуты:секунды",
            anchor="w",
            height=16,
            text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=10),
        )
        self.range_hint.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

        output_group = self._compact_field(optional_row, "Папка сохранения", column=3, padx=(14, 14))
        output_group.grid_columnconfigure(0, weight=1)
        self.output_entry = self._entry(output_group, self.output_var, "Выберите папку")
        self.output_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.folder_button = ctk.CTkButton(
            output_group,
            text="",
            image=self._images.get("folder"),
            width=42,
            height=42,
            corner_radius=12,
            fg_color=COLORS["surface_hover"],
            hover_color=COLORS["border"],
            command=self._choose_output,
        )
        self.folder_button.grid(row=1, column=1)

        exact_group = ctk.CTkFrame(content, fg_color="transparent")
        exact_group.grid(row=4, column=0, sticky="w", pady=(0, 18))
        self.exact_switch = ctk.CTkSwitch(
            exact_group,
            text="Точные границы кадра",
            variable=self.exact_var,
            onvalue=True,
            offvalue=False,
            progress_color=COLORS["accent"],
            button_color=("#FFFFFF", "#FFFFFF"),
            button_hover_color=("#ECE8FF", "#E6E2FF"),
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=12),
        )
        self.exact_switch.grid(row=0, column=0)
        self.exact_help_button = ctk.CTkButton(
            exact_group,
            text="",
            image=self._images.get("question"),
            width=28,
            height=28,
            corner_radius=9,
            fg_color="transparent",
            hover_color=COLORS["surface_hover"],
            command=self._show_exact_help,
        )
        self.exact_help_button.grid(row=0, column=1, padx=(4, 0))

        self.action_host = ctk.CTkFrame(content, fg_color="transparent")
        self.action_host.grid(row=5, column=0, sticky="ew")
        self.action_host.grid_columnconfigure(0, weight=1)

        self.download_button = ctk.CTkButton(
            self.action_host,
            text="Скачать видео",
            image=self._images.get("download"),
            compound="left",
            height=50,
            corner_radius=14,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_download,
        )
        self.download_button.grid(row=0, column=0, sticky="ew")
        self._build_progress(self.action_host)

    def _build_progress(self, parent: ctk.CTkFrame) -> None:
        self.progress_card = ctk.CTkFrame(
            parent,
            fg_color=COLORS["surface_alt"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.progress_card.grid(row=0, column=0, sticky="ew")
        self.progress_card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        top.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            top,
            text="Готов к загрузке",
            anchor="w",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.status_label.grid(row=0, column=0, sticky="ew")
        self.percent_label = ctk.CTkLabel(
            top,
            text="",
            text_color=COLORS["accent_text"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.percent_label.grid(row=0, column=1, sticky="e")

        self.progress = ctk.CTkProgressBar(
            self.progress_card,
            height=7,
            corner_radius=7,
            fg_color=COLORS["progress_track"],
            progress_color=COLORS["accent"],
        )
        self.progress.grid(row=1, column=0, sticky="ew", padx=16)
        self.progress.set(0)

        lower = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        lower.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 11))
        lower.grid_columnconfigure(0, weight=1)
        self.meta_label = ctk.CTkLabel(
            lower,
            text="",
            anchor="w",
            text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=11),
        )
        self.meta_label.grid(row=0, column=0, sticky="ew")

        self.cancel_button = ctk.CTkButton(
            lower,
            text="Отмена",
            width=74,
            height=30,
            corner_radius=9,
            fg_color="transparent",
            hover_color=COLORS["danger_soft"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._cancel_download,
        )

        self.open_button = ctk.CTkButton(
            lower,
            text="",
            image=self._images.get("folder"),
            width=38,
            height=30,
            corner_radius=9,
            fg_color=COLORS["success_soft"],
            hover_color=COLORS["success_hover"],
            command=self._open_output,
        )

        self.new_download_button = ctk.CTkButton(
            lower,
            text="Скачать ещё видео",
            image=self._images.get("download"),
            compound="left",
            width=158,
            height=30,
            corner_radius=9,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="white",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._prepare_new_download,
        )

        self.notice_label = ctk.CTkLabel(
            self.progress_card,
            text="",
            anchor="w",
            justify="left",
            wraplength=780,
            text_color=COLORS["warning"],
            font=ctk.CTkFont(size=10),
        )
        self.progress_card.grid_remove()

    def _compact_field(
        self,
        parent: ctk.CTkFrame,
        label_text: str,
        *,
        column: int,
        padx: tuple[int, int] = (0, 0),
    ) -> ctk.CTkFrame:
        group = ctk.CTkFrame(parent, fg_color="transparent")
        group.grid(row=0, column=column, sticky="ew", padx=padx)
        ctk.CTkLabel(
            group,
            text=label_text,
            anchor="w",
            height=18,
            text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=10),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 3))
        return group

    def _build_toast(self) -> None:
        self._toast_frame = ctk.CTkFrame(
            self,
            width=620,
            height=48,
            corner_radius=0,
            border_width=1,
        )
        self._toast_label = ctk.CTkLabel(
            self._toast_frame,
            width=1,
            text="",
            justify="left",
            wraplength=520,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self._toast_label.pack(fill="both", expand=True, padx=16, pady=11)
        self._toast_frame.bind("<Button-1>", lambda _event: self._hide_toast())
        self._toast_label.bind("<Button-1>", lambda _event: self._hide_toast())

    def _field_label(self, parent: ctk.CTkFrame, text: str, row: int) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            parent,
            text=text,
            anchor="w",
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        label.grid(row=row, column=0, sticky="w")
        return label

    def _entry(
        self,
        parent: ctk.CTkFrame,
        variable: tk.StringVar,
        placeholder: str,
        *,
        width: int | None = None,
    ) -> ctk.CTkEntry:
        options: dict[str, object] = {}
        if width is not None:
            options["width"] = width
        return ctk.CTkEntry(
            parent,
            textvariable=variable,
            placeholder_text=placeholder,
            height=42,
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["surface_alt"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["subtle"],
            font=ctk.CTkFont(size=12),
            **options,
        )

    def _install_thread_exception_handler(self) -> None:
        def handle_thread_exception(args: threading.ExceptHookArgs) -> None:
            LOGGER.error(
                "Необработанное исключение в потоке %s",
                args.thread.name if args.thread else "unknown",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )
            self.events.put(
                {
                    "event": "ui_exception",
                    "text": f"Системная ошибка. Подробности записаны в {LOG_FILENAME}",
                }
            )

        threading.excepthook = handle_thread_exception

    def _report_callback_exception(self, exc_type: type[BaseException], exc: BaseException, trace: object) -> None:
        LOGGER.error("Ошибка обработчика интерфейса", exc_info=(exc_type, exc, trace))
        self._toast(f"Системная ошибка. Подробности записаны в {LOG_FILENAME}", "danger")

    def _toast(self, text: str, tone: str = "accent") -> None:
        if self._toast_after is not None:
            self.after_cancel(self._toast_after)
        palette = {
            "accent": (COLORS["accent_soft"], COLORS["accent"], COLORS["accent_text"]),
            "warning": (COLORS["warning_soft"], COLORS["warning"], COLORS["warning"]),
            "danger": (COLORS["danger_soft"], COLORS["danger"], COLORS["danger"]),
            "success": (COLORS["success_soft"], COLORS["success"], COLORS["success"]),
        }
        background, border, foreground = palette.get(tone, palette["accent"])
        self._toast_frame.configure(fg_color=background, border_color=border)
        toast_width = max(280, self.winfo_width())
        self._toast_label.configure(text=text, text_color=foreground, wraplength=toast_width - 32)
        self._toast_frame.place(relx=0.5, rely=1.0, y=0, anchor="s", relwidth=1.0)
        self._toast_frame.lift()
        self._toast_after = self.after(toast_duration_ms(text), self._expire_toast)

    def _hide_toast(self) -> None:
        if self._toast_after is not None:
            try:
                self.after_cancel(self._toast_after)
            except tk.TclError:
                pass
            self._toast_after = None
        self._toast_frame.place_forget()

    def _expire_toast(self) -> None:
        self._toast_after = None
        self._toast_frame.place_forget()

    def _open_author_link(self, _event: object | None = None) -> None:
        try:
            if not webbrowser.open("https://t.me/PanCrucian"):
                raise OSError("браузер не принял ссылку")
        except Exception as exc:  # noqa: BLE001 - system browser errors vary by platform
            LOGGER.exception("Не удалось открыть ссылку автора")
            self._toast(f"Не удалось открыть ссылку: {exc}", "danger")

    def _show_exact_help(self) -> None:
        self._toast(
            "Точные границы создают фрагмент ровно по указанному времени, но обработка займёт больше времени.",
            "accent",
        )

    def _paste_url(self) -> None:
        try:
            value = self.clipboard_get().strip()
        except tk.TclError:
            self._toast("Буфер обмена пуст", "warning")
            return
        self.url_var.set(value)
        self.url_entry.focus_set()
        self.url_entry.icursor("end")

    def _choose_output(self) -> None:
        initial = self.output_var.get().strip() or str(portable_root())
        try:
            selected = filedialog.askdirectory(parent=self, initialdir=initial, title="Куда сохранить видео")
        except (OSError, tk.TclError) as exc:
            LOGGER.exception("Не удалось открыть выбор папки")
            self._toast(f"Не удалось выбрать папку: {exc}", "danger")
            return
        if selected:
            self.output_var.set(selected)

    def _normalize_time(self, variable: tk.StringVar) -> None:
        value = variable.get().strip()
        if not value:
            return
        try:
            parsed = parse_timecode(value)
        except TimecodeError:
            return
        variable.set(format_timecode(parsed))

    def _validate_url(self, value: str) -> str:
        text = value.strip()
        try:
            parsed = urlparse(text)
        except ValueError as exc:
            raise ValueError("Проверьте ссылку на видео") from exc
        host = (parsed.hostname or "").lower()
        allowed = host == "youtu.be" or host.endswith(".youtu.be") or host == "youtube.com" or host.endswith(
            ".youtube.com"
        )
        if parsed.scheme not in {"http", "https"} or not allowed:
            raise ValueError("Нужна ссылка на youtube.com или youtu.be")
        return text

    def _start_download(self) -> None:
        if self.process and self.process.poll() is None:
            return

        try:
            url = self._validate_url(self.url_var.get())
            start = parse_timecode(self.start_var.get())
            end = parse_timecode(self.end_var.get())
            validate_time_range(start, end)
        except (ValueError, TimecodeError) as exc:
            LOGGER.info("Проверка параметров не пройдена: %s", exc)
            self._toast(str(exc), "warning")
            return

        output = Path(self.output_var.get().strip()).expanduser() if self.output_var.get().strip() else portable_root()
        try:
            event_handle = tempfile.NamedTemporaryFile(prefix="clipify-events-", suffix=".jsonl", delete=False)
            event_handle.close()
            self.event_file = Path(event_handle.name)
            command = [
                *worker_command(),
                "--url",
                url,
                "--output",
                str(output),
                "--event-file",
                str(self.event_file),
            ]
            if start is not None:
                command.extend(("--start", str(start)))
            if end is not None:
                command.extend(("--end", str(end)))
            if self.exact_var.get():
                command.append("--exact")

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
            self.process = subprocess.Popen(command, **popen_options)  # type: ignore[arg-type]
        except (OSError, ValueError) as exc:
            LOGGER.exception("Не удалось запустить процесс загрузки")
            if self.event_file is not None:
                self.event_file.unlink(missing_ok=True)
            self.event_file = None
            self._toast(f"Не удалось запустить загрузку: {exc}", "danger")
            return

        LOGGER.info("Запущена загрузка в %s; диапазон: %s", output, describe_range(start, end))
        self.had_worker_error = False
        self.cancelled = False
        self.last_output = None
        self._show_progress_context()
        self._set_busy(True)
        self._set_result_actions("busy")
        self._set_status("Готов к загрузке", describe_range(start, end))
        self._start_indeterminate()
        threading.Thread(
            target=self._read_worker,
            args=(self.process, self.event_file),
            name="clipify-worker-events",
            daemon=True,
        ).start()

    def _read_worker(self, process: subprocess.Popen[str], event_file: Path) -> None:
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

                self._queue_event_lines(lines)
                if process.poll() is not None:
                    try:
                        with event_file.open("r", encoding="utf-8") as stream:
                            stream.seek(position)
                            self._queue_event_lines(stream.readlines())
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
            self.events.put({"event": "process_exit", "code": code})
        except Exception as exc:  # noqa: BLE001 - surface every background failure in the GUI
            LOGGER.exception("Сбой чтения событий загрузчика")
            self.events.put({"event": "ui_exception", "text": f"Сбой загрузчика: {exc}"})

    def _queue_event_lines(self, lines: list[str]) -> None:
        for raw_line in lines:
            line = raw_line.strip()
            if not line.startswith(EVENT_PREFIX):
                if line:
                    LOGGER.warning("Неизвестный вывод загрузчика: %s", line[:500])
                continue
            try:
                self.events.put(json.loads(line[len(EVENT_PREFIX) :]))
            except json.JSONDecodeError:
                LOGGER.exception("Повреждённое событие загрузчика: %s", line[:500])

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                try:
                    self._handle_event(event)
                except Exception:  # noqa: BLE001 - event loop must remain alive
                    LOGGER.exception("Не удалось обработать событие: %r", event)
                    self._toast(f"Системная ошибка. Подробности записаны в {LOG_FILENAME}", "danger")
        except queue.Empty:
            pass
        self.after(100, self._poll_events)

    def _handle_event(self, event: dict[str, object]) -> None:
        kind = event.get("event")
        if kind == "status":
            self._set_status(str(event.get("text", "Работаем…")))
        elif kind == "warning":
            self._show_notice(str(event.get("text", "")))
        elif kind == "progress":
            percent = event.get("percent")
            if isinstance(percent, (int, float)):
                self._stop_indeterminate()
                self.progress.set(max(0, min(float(percent) / 100, 1)))
                self.percent_label.configure(text=f"{float(percent):.0f}%")
            speed = str(event.get("speed") or "")
            eta = event.get("eta")
            eta_text = f" · осталось {int(float(eta))} с" if isinstance(eta, (int, float)) else ""
            size = str(event.get("downloaded") or "")
            total = str(event.get("total") or "")
            total_text = f" из {total}" if total else ""
            self.meta_label.configure(text=f"{size}{total_text} · {speed}{eta_text}".strip(" ·"))
        elif kind == "complete":
            self.last_output = Path(str(event.get("filepath", portable_root())))
            self._finish_success()
        elif kind in {"error", "log_error"}:
            if self.cancelled:
                return
            self.had_worker_error = True
            self._show_error(str(event.get("text", "Не удалось скачать видео")))
        elif kind == "ui_exception":
            self.had_worker_error = True
            self._show_error(str(event.get("text", "Системная ошибка")))
        elif kind == "process_exit":
            code = int(event.get("code", 1))
            self.process = None
            if code != 0 and not self.had_worker_error and not self.cancelled:
                self._show_error("Загрузка завершилась с ошибкой")
            elif code == 0 and not self.last_output:
                self._finish_success()
            self._set_busy(False)

    def _set_status(self, text: str, meta: str | None = None) -> None:
        self.status_label.configure(text=text, text_color=COLORS["text"])
        if meta is not None:
            self.meta_label.configure(text=meta)

    def _show_notice(self, text: str) -> None:
        concise = text.replace("WARNING: ", "").strip()
        if len(concise) > 180:
            concise = concise[:177] + "…"
        LOGGER.warning("Предупреждение загрузчика: %s", text)
        self.notice_label.configure(text=concise, text_color=COLORS["warning"])
        self.notice_label.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 10))
        self._toast(concise, "warning")

    def _show_error(self, text: str) -> None:
        LOGGER.error("Ошибка загрузки: %s", text)
        self._stop_indeterminate()
        self.progress.set(0)
        self.percent_label.configure(text="")
        self.status_label.configure(text="Не удалось скачать", text_color=COLORS["danger"])
        self.meta_label.configure(text=text)
        self.notice_label.grid_remove()
        self._show_progress_context()
        self._set_result_actions("error")
        self._toast(text, "danger")
        if not (self.process and self.process.poll() is None):
            self._set_busy(False)

    def _finish_success(self) -> None:
        LOGGER.info("Видео сохранено: %s", self.last_output)
        self._stop_indeterminate()
        self.progress.set(1)
        self.percent_label.configure(text="100%")
        self.status_label.configure(text="Видео готово", text_color=COLORS["success"])
        if self.last_output and self.last_output.is_file():
            self.meta_label.configure(text=self.last_output.name)
        else:
            self.meta_label.configure(text="Файл сохранён в выбранную папку")
        self.url_var.set("")
        self.start_var.set("")
        self.end_var.set("")
        self.notice_label.grid_remove()
        self._set_result_actions("success")
        self._toast("Видео успешно сохранено", "success")

    def _set_result_actions(self, mode: str) -> None:
        for button in (self.cancel_button, self.open_button, self.new_download_button):
            button.grid_remove()
        if mode == "busy":
            self.cancel_button.grid(row=0, column=1, padx=(10, 0))
            self.cancel_button.configure(state="normal")
        elif mode == "success":
            self.open_button.grid(row=0, column=1, padx=(10, 0))
            self.new_download_button.grid(row=0, column=2, padx=(8, 0))
        elif mode == "error":
            self.new_download_button.grid(row=0, column=1, padx=(10, 0))

    def _show_progress_context(self) -> None:
        self.download_button.grid_remove()
        self.progress_card.grid()
        if self.state() == "normal" and self.winfo_height() < PROGRESS_HEIGHT:
            width = max(self.winfo_width(), COMPACT_WIDTH)
            self.geometry(f"{width}x{PROGRESS_HEIGHT}")
            self._auto_expanded = True

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for widget in (
            self.url_entry,
            self.start_entry,
            self.end_entry,
            self.output_entry,
            self.paste_button,
            self.folder_button,
            self.exact_switch,
            self.exact_help_button,
        ):
            widget.configure(state=state)
        self.download_button.configure(state="disabled" if busy else "normal")
        self.new_download_button.configure(state=state)
        if not busy:
            self.cancel_button.configure(state="disabled")
            self._sync_primary_download_state()

    def _sync_primary_download_state(self, *_args: object) -> None:
        busy = bool(self.process and self.process.poll() is None)
        state = "normal" if self.url_var.get().strip() and not busy else "disabled"
        self.download_button.configure(state=state)

    def _prepare_new_download(self) -> None:
        if self.process and self.process.poll() is None:
            return
        self.last_output = None
        self.had_worker_error = False
        self.cancelled = False
        self._stop_indeterminate()
        self.progress.set(0)
        self.percent_label.configure(text="")
        self.notice_label.grid_remove()
        self.progress_card.grid_remove()
        self.download_button.grid()
        self._set_busy(False)
        if self._auto_expanded and self.state() == "normal":
            width = max(self.winfo_width(), COMPACT_WIDTH)
            self.geometry(f"{width}x{COMPACT_HEIGHT}")
            self._auto_expanded = False
        self.url_entry.focus_set()

    def _start_indeterminate(self) -> None:
        self.progress.set(0)
        self.percent_label.configure(text="")
        self.progress.start()
        self._progress_running = True

    def _stop_indeterminate(self) -> None:
        if self._progress_running:
            self.progress.stop()
            self._progress_running = False

    def _cancel_download(self) -> None:
        process = self.process
        if not process or process.poll() is not None:
            return
        self.cancelled = True
        self.had_worker_error = True
        self._terminate_process_tree(process)
        self._stop_indeterminate()
        self.progress.set(0)
        self.percent_label.configure(text="")
        self.status_label.configure(text="Загрузка отменена", text_color=COLORS["warning"])
        self.meta_label.configure(text="Можно изменить параметры и попробовать снова")
        self._set_result_actions("error")
        self._set_busy(False)
        self._toast("Загрузка отменена", "warning")
        LOGGER.info("Загрузка отменена пользователем")

    def _terminate_process_tree(self, process: subprocess.Popen[str]) -> None:
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

    def _open_output(self) -> None:
        target = self.last_output.parent if self.last_output and self.last_output.is_file() else self.last_output
        if not target or not target.exists():
            target = Path(self.output_var.get().strip()) if self.output_var.get().strip() else portable_root()
        try:
            if os.name == "nt":
                os.startfile(target)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
        except (OSError, ValueError) as exc:
            LOGGER.exception("Не удалось открыть папку %s", target)
            self._toast(f"Не удалось открыть папку: {exc}", "danger")

    def _on_close(self) -> None:
        if self.process and self.process.poll() is None:
            self._terminate_process_tree(self.process)
        LOGGER.info("Clipify завершён")
        self.destroy()


def run_app() -> None:
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    app_id_ready = set_windows_app_id()
    font_ready = register_bundled_font()
    try:
        ctk.ThemeManager.theme["CTkFont"]["family"] = FONT_FAMILY
    except (KeyError, TypeError):
        LOGGER.exception("Не удалось применить Roboto к теме интерфейса")
        font_ready = False

    def handle_unhandled(exc_type: type[BaseException], exc: BaseException, trace: object) -> None:
        LOGGER.critical("Необработанная ошибка приложения", exc_info=(exc_type, exc, trace))

    sys.excepthook = handle_unhandled
    app = ClipifyApp()
    if not font_ready or not app_id_ready:
        missing_component = "Roboto" if not font_ready else "значок Windows"
        app.after(
            250,
            lambda: app._toast(
                f"Не удалось подключить {missing_component}. Подробности записаны в {LOG_FILENAME}",
                "danger",
            ),
        )
    app.mainloop()
