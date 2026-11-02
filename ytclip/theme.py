"""Design tokens for the Clipify window: colour, type and spacing."""

from __future__ import annotations

import sys
import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk


# (light, dark) pairs, the form CustomTkinter resolves against the system theme.
COLORS: dict[str, tuple[str, str]] = {
    "window": ("#FFFFFF", "#1E1F22"),
    "panel": ("#F9FAFB", "#25262A"),
    "field": ("#FFFFFF", "#2A2B2F"),
    "field_border": ("#D1D5DB", "#3F4148"),
    "field_border_strong": ("#9CA3AF", "#5A5D66"),
    "hairline": ("#E5E7EB", "#2E3035"),
    "text": ("#111827", "#F3F4F6"),
    "secondary": ("#4B5563", "#B4B9C2"),
    "muted": ("#6B7280", "#8E949E"),
    "accent": ("#2563EB", "#2563EB"),
    "accent_hover": ("#1D4ED8", "#1D4ED8"),
    "accent_text": ("#2563EB", "#60A5FA"),
    "on_accent": ("#FFFFFF", "#FFFFFF"),
    "button": ("#FFFFFF", "#2A2B2F"),
    "button_hover": ("#F3F4F6", "#33353A"),
    "menu": ("#F3F4F6", "#2A2B2F"),
    "menu_hover": ("#E5E7EB", "#33353A"),
    "disabled_text": ("#6B7280", "#8E949E"),
    "track": ("#E5E7EB", "#34363C"),
    "thumb": ("#F3F4F6", "#2A2B2F"),
    "info_soft": ("#EFF6FF", "#1C2740"),
    "info_line": ("#BFDBFE", "#2B3E66"),
    "success": ("#15803D", "#4ADE80"),
    "success_soft": ("#F0FDF4", "#162A1E"),
    "success_line": ("#BBF7D0", "#245238"),
    "danger": ("#DC2626", "#F87171"),
    "danger_soft": ("#FEF2F2", "#2E1B1D"),
    "danger_line": ("#FECACA", "#5A2A2E"),
}

# Glyph colours baked into the icon PNGs (light, dark); kept beside COLORS so they cannot drift.
ICON_TONES: dict[str, tuple[str, str]] = {
    "accent": ("#2563EB", "#60A5FA"),
    "success": COLORS["success"],
    "danger": COLORS["danger"],
    "muted": COLORS["muted"],
    "secondary": COLORS["secondary"],
}

PAGE_X = 24
RADIUS = 6
FIELD_HEIGHT = 40
PRIMARY_HEIGHT = 46


class Typography:
    """System UI faces: Segoe UI Variable on Windows 11, Segoe UI before it, SF on macOS."""

    def __init__(self, root: tk.Misc) -> None:
        families = set(tkfont.families(root))
        self._weighted = True
        if sys.platform == "win32" and "Segoe UI Variable Text" in families:
            self.text = "Segoe UI Variable Text"
            self.text_strong = self._first(families, "Segoe UI Variable Text Semibold", "Segoe UI Semibold")
            self.display = "Segoe UI Variable Display"
            self.display_strong = self._first(families, "Segoe UI Variable Display Semib", "Segoe UI Semibold")
            self._weighted = False
        elif sys.platform == "win32":
            self.text = self.display = "Segoe UI"
            self.text_strong = self.display_strong = self._first(families, "Segoe UI Semibold", "Segoe UI")
            self._weighted = self.text_strong == "Segoe UI"
        else:
            base = tkfont.nametofont("TkDefaultFont", root=root).actual("family")
            self.text = self.text_strong = self.display = self.display_strong = base
        # Static Segoe UI ships tabular figures, so live numbers stop jittering.
        self.numeric = "Segoe UI" if sys.platform == "win32" else self.text

    @staticmethod
    def _first(families: set[str], *candidates: str) -> str:
        return next((name for name in candidates if name in families), candidates[-1])

    def _strong(self, family: str) -> ctk.CTkFont:
        return ctk.CTkFont(family=family, size=13, weight="bold" if self._weighted else "normal")

    def body(self, size: int = 13) -> ctk.CTkFont:
        return ctk.CTkFont(family=self.text, size=size)

    def strong(self, size: int = 13) -> ctk.CTkFont:
        font = self._strong(self.text_strong)
        font.configure(size=size)
        return font

    def title(self, size: int = 20) -> ctk.CTkFont:
        font = self._strong(self.display_strong)
        font.configure(size=size)
        return font

    def numbers(self, size: int = 12) -> ctk.CTkFont:
        return ctk.CTkFont(family=self.numeric, size=size)

    def link(self, size: int = 12, *, underline: bool = False) -> ctk.CTkFont:
        return ctk.CTkFont(family=self.text, size=size, underline=underline)
