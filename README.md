# Clipify

Download a full YouTube video or save only the part you need. Clipify is a compact, portable desktop app for Windows and macOS. No installation or separate runtime setup is required.

**Current version: 1.1.0**

[Download Clipify for Windows or macOS](https://github.com/gusappint/Clipify/releases/latest)

## How to use it

1. Paste a YouTube link.
2. Add a start or end time if you want a clip.
3. Choose a folder, or leave it blank to save beside Clipify.
4. Select **Download video**.

Enter time as seconds, `MM:SS`, or `HH:MM:SS`. Turn on **Frame-accurate trim** when the exact first and last frames matter.

## What Clipify handles for you

- Downloads complete videos or open-ended and fixed-length clips.
- Starts in English and switches between English and Russian in one click.
- Matches the system light or dark theme.
- Shows progress, speed, remaining time, and a cancel action.
- Keeps existing files and numbers new copies automatically.
- Cleans unsafe file-name characters and limits long paths.
- Records technical failures in `clipify.log` and shows a clear next step in the app.

Choose `Clipify-darwin-arm64.zip` for Apple Silicon or `Clipify-darwin-x86_64.zip` for an Intel Mac. Release packages include the required download and media components. The macOS builds are unsigned, so the first launch may need approval in **System Settings → Privacy & Security**.

## Русский

Скачивайте YouTube-видео целиком или сохраняйте только нужный фрагмент. Clipify — компактное portable-приложение для Windows и macOS, которому не нужна установка.

[Скачать Clipify для Windows или macOS](https://github.com/gusappint/Clipify/releases/latest)

### Как скачать видео

1. Вставьте ссылку на YouTube.
2. При необходимости укажите начало или конец фрагмента.
3. Выберите папку или оставьте поле пустым, чтобы сохранить рядом с Clipify.
4. Нажмите **Скачать видео**.

Время можно указать в секундах, формате `ММ:СС` или `ЧЧ:ММ:СС`. Включите **Точные границы кадра**, если важны точные начало и конец фрагмента.

Для Mac с Apple Silicon скачайте `Clipify-darwin-arm64.zip`, для Mac с процессором Intel — `Clipify-darwin-x86_64.zip`.

Clipify поддерживает светлую и тёмную темы, не заменяет существующие файлы, обезопасит имя файла и сохранит подробности сбоя в `clipify.log`.

## Run from source

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

During development, Deno can be in `PATH`, in `tools/`, beside the app, or at `%USERPROFILE%\deno.exe` on Windows.

## Test and build

```bash
python -m pytest
python -m pip install -r requirements-dev.txt
python scripts/build.py --fetch-deno
```

PyInstaller builds native applications, so run the build on each target operating system. The GitHub Actions workflow builds Windows x64, macOS Apple Silicon, and macOS Intel packages. Pushing a `v*` tag publishes all three ZIP files as a GitHub Release.

## Project layout

- `main.py` — app entry point.
- `ytclip/ui.py` — interface and download lifecycle.
- `ytclip/i18n.py` — English and Russian interface copy.
- `ytclip/worker.py` — isolated download worker.
- `ytclip/timecode.py` — time parsing and validation.
- `ytclip/version.py` — current application version.
- `scripts/build.py` — native build and ZIP packaging.
- `.github/workflows/build-portable.yml` — Windows and macOS release builds.
- `.agent/skills/` — project-local UX writing and design-polish skills.
