from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
from pathlib import Path

from .logging_utils import get_logger
from .platform_tools import resource_root


LOGGER = get_logger("fonts")
FONT_FAMILY = "Roboto"


def _register_windows(font: Path) -> bool:
    private_font = 0x10
    result = ctypes.windll.gdi32.AddFontResourceExW(str(font), private_font, 0)  # type: ignore[attr-defined]
    return bool(result)


def _register_linux(font: Path) -> bool:
    library_name = ctypes.util.find_library("fontconfig")
    if not library_name:
        return False
    fontconfig = ctypes.CDLL(library_name)
    fontconfig.FcConfigGetCurrent.restype = ctypes.c_void_p
    fontconfig.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    fontconfig.FcConfigAppFontAddFile.restype = ctypes.c_bool
    fontconfig.FcConfigBuildFonts.argtypes = [ctypes.c_void_p]
    fontconfig.FcConfigBuildFonts.restype = ctypes.c_bool
    config = fontconfig.FcConfigGetCurrent()
    return bool(config and fontconfig.FcConfigAppFontAddFile(config, os.fsencode(font)) and fontconfig.FcConfigBuildFonts(config))


def _register_macos(font: Path) -> bool:
    core_foundation_name = ctypes.util.find_library("CoreFoundation")
    core_text_name = ctypes.util.find_library("CoreText")
    if not core_foundation_name or not core_text_name:
        return False
    core_foundation = ctypes.CDLL(core_foundation_name)
    core_text = ctypes.CDLL(core_text_name)
    core_foundation.CFURLCreateFromFileSystemRepresentation.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_long,
        ctypes.c_bool,
    ]
    core_foundation.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
    core_foundation.CFRelease.argtypes = [ctypes.c_void_p]
    core_text.CTFontManagerRegisterFontsForURL.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
    core_text.CTFontManagerRegisterFontsForURL.restype = ctypes.c_bool
    encoded = os.fsencode(font)
    url = core_foundation.CFURLCreateFromFileSystemRepresentation(None, encoded, len(encoded), False)
    if not url:
        return False
    try:
        return bool(core_text.CTFontManagerRegisterFontsForURL(url, 1, None))
    finally:
        core_foundation.CFRelease(url)


def register_bundled_font() -> bool:
    font = resource_root() / "assets" / "fonts" / "Roboto.ttf"
    if not font.is_file():
        LOGGER.error("Файл Roboto не найден: %s", font)
        return False
    try:
        if os.name == "nt":
            registered = _register_windows(font)
        elif sys.platform == "darwin":
            registered = _register_macos(font)
        else:
            registered = _register_linux(font)
    except (OSError, AttributeError, TypeError):
        LOGGER.exception("Не удалось зарегистрировать Roboto")
        return False
    if registered:
        LOGGER.info("Roboto зарегистрирован из %s", font)
    else:
        LOGGER.error("Операционная система отклонила регистрацию Roboto: %s", font)
    return registered
