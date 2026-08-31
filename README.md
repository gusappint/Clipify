# Clipify

A compact cross-platform desktop utility for downloading a full YouTube video or a selected time range. The interface is in Russian and is designed for a portable, no-install workflow.

[Download the latest Windows and macOS builds](https://github.com/gusappint/Clipify/releases/latest)

## Downloads

Ready-to-run ZIP archives are published on the [Releases page](https://github.com/gusappint/Clipify/releases):

- `Clipify-windows-x86_64.zip` — Windows x64.
- `Clipify-darwin-arm64.zip` — macOS on Apple Silicon.

The macOS build is currently unsigned. On first launch, macOS may require the user to explicitly allow the app in Privacy & Security settings.

## Features

- A single URL field with clipboard paste.
- Optional start and end boundaries in seconds, `MM:SS`, or `HH:MM:SS`.
- Start-only and end-only ranges.
- Optional frame-accurate cuts through FFmpeg re-encoding.
- Optional output folder; blank means next to the application.
- Portable filename sanitization: forbidden characters and reserved Windows names are replaced, Unicode is preserved, and title/path lengths are capped safely.
- Existing files are never replaced; repeated downloads receive ` (2)`, ` (3)`, and so on.
- Progress, speed, ETA, cancellation, and quick access to the output folder.
- Automatic light/dark appearance based on the operating-system setting.
- Bundled Roboto typography for consistent rendering on every platform.
- Failures are surfaced as in-app notifications and written to `clipify.log` next to the app.
- Bundled `yt-dlp`, EJS solver scripts, FFmpeg, and Deno in release builds.
- Native portable artifacts for Windows and macOS.

## Run from source

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

During development, Deno can be in `PATH`, inside `tools/`, next to the app, or explicitly at `%USERPROFILE%\deno.exe` on Windows.

## Test

```bash
python -m pytest
```

## Build a portable artifact

Build on each target operating system; PyInstaller does not cross-compile native GUI applications.

```bash
python -m pip install -r requirements-dev.txt
python scripts/build.py --fetch-deno
```

The result is written to `dist/` as a native executable/app bundle and a ZIP archive. The app itself embeds all runtime dependencies and does not require a Python installation.

On macOS, sign/notarize the `.app` for public distribution. On Linux, build on the oldest glibc-based distribution you intend to support.

The included `.github/workflows/build-portable.yml` workflow builds Windows and macOS artifacts on manual dispatch. A `v*` tag also publishes both ZIP archives as a GitHub Release.

## Project layout

- `main.py` — GUI/worker entry point.
- `ytclip/ui.py` — interface and process lifecycle.
- `ytclip/worker.py` — isolated yt-dlp worker.
- `ytclip/timecode.py` — time parsing and validation.
- `scripts/build.py` — reproducible native build and ZIP packaging.
- `scripts/fetch_deno.py` — platform-aware Deno downloader.
- `scripts/fetch_bootstrap_icons.py` — pinned Bootstrap Icons asset fetcher.
- `.github/workflows/build-portable.yml` — native three-OS build matrix.
