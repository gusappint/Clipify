# -*- mode: python ; coding: utf-8 -*-

import os
import platform
from pathlib import Path

from PyInstaller.utils.hooks import collect_all
from ytclip.version import __version__


ROOT = Path(SPECPATH)

datas = []
binaries = []
hiddenimports = []

for package in ("customtkinter", "imageio_ffmpeg", "yt_dlp", "yt_dlp_ejs"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

ui_assets = [ROOT / "assets" / "icon.png", ROOT / "assets" / "icon.ico", *(ROOT / "assets" / "icons").glob("*.png")]
for asset in ui_assets:
    if asset.is_file():
        destination = "assets/icons" if asset.parent.name == "icons" else "assets"
        datas.append((str(asset), destination))

for font_asset in (ROOT / "assets" / "fonts").glob("*"):
    if font_asset.is_file():
        datas.append((str(font_asset), "assets/fonts"))

deno_name = "deno.exe" if os.name == "nt" else "deno"
deno_candidates = [ROOT / "tools" / deno_name]
if os.name == "nt":
    deno_candidates.append(Path.home() / "deno.exe")
for deno in deno_candidates:
    if deno.is_file():
        binaries.append((str(deno), "tools"))
        break

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

icon = str(ROOT / "assets" / "icon.ico") if (ROOT / "assets" / "icon.ico").is_file() else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Clipify",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
    version=str(ROOT / "assets" / "version_info.txt") if platform.system() == "Windows" else None,
)

if platform.system() == "Darwin":
    app = BUNDLE(
        exe,
        name="Clipify.app",
        icon=icon,
        bundle_identifier="com.pancrucian.clipify",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "CFBundleShortVersionString": __version__,
            "CFBundleVersion": __version__,
        },
    )
