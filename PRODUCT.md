# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

A broad, non-technical audience. Most people find Clipify on the GitHub releases page, unzip it, run it once or now and then, and want one thing: a YouTube video, or a piece of one, saved as a file. They do not read documentation, do not know what cookies, keyframes or FFmpeg are, and judge the app in the first ten seconds. The interface starts in English and switches to Russian in one click; both languages are first-class.

## Product Purpose

Clipify saves a YouTube video to disk, in full or only the part between a start and an end time, without installation or runtime setup. Success means: paste a link, press one button, get the file in a folder you can open, on the first try. When YouTube blocks the download, the person can recover inside the app (sign in once) without understanding why it happened.

## Positioning

A portable, single-window app that downloads only the requested range instead of the whole video, with an optional frame-accurate cut, and a one-time YouTube sign-in through a separate browser window that keeps the session beside the app. Everything it needs (download engine, media processor, JS runtime) ships inside the archive.

## Operating Context

- One compact window that sits beside the browser the link was copied from.
- Flow: copy a link in the browser, paste it, optionally set start/end, optionally pick a folder (default: the folder Clipify lives in), download, then open the folder or start another download.
- YouTube sometimes demands sign-in ("confirm you're not a bot", age checks). Sign-in opens Chrome, Edge or Brave in a separate window, detects the YouTube session, closes the window and saves YouTube-only cookies to `clipify-youtube-cookies.txt` beside the app. Expired sessions are refreshed the same way.
- Failures are written to `clipify.log` beside the app; the window shows the next step.
- The app follows the system light or dark theme.

## Capabilities and Constraints

- Accepts youtube.com and youtu.be links only.
- Time input: seconds, `MM:SS`, or `HH:MM:SS`; a comma or dot works as the decimal separator. Empty start means "from the beginning", empty end means "to the end".
- Frame-accurate trim re-encodes at the cut points: exact boundaries, slower, more CPU.
- Progress reports stages (checking components, reading video details, using the saved session, downloading, processing, merging tracks), percent, downloaded/total size, speed, time left; downloads can be cancelled.
- Never overwrites: a name clash produces a numbered copy. File names are sanitized and the full path is kept short enough for Windows.
- Keyboard: Ctrl+L focuses the link field, Enter starts the download.
- Stack: Python 3.11+, CustomTkinter 5.2.2 on Tk 8.6, Pillow; the download runs in a separate worker process. Packaged with PyInstaller for Windows x64, macOS Apple Silicon and macOS Intel (unsigned). There is no HTML or web view: the platform value `web` above stands for a custom-drawn design language that follows no mobile OS convention.
- Fonts and icons must be bundled files; nothing is fetched at runtime.

## Brand Commitments

- Name: Clipify.
- The author credit "by PanCrucian" stays visible in the app, and the "©PanCrucian" link to https://t.me/PanCrucian stays clickable.
- The app icon is to be redrawn for the new design, generated through the Codex plugin (decided 2026-11-02); the old violet cloud icon is not binding.
- Voice, in English and Russian: short and to the point. Verbs first, no filler; an error says what happened and what to do next. Russian addresses the user with «вы».
- Look: the category standard, chosen on purpose (2026-11-02). A clean, conventional downloader window executed at full craft, with no themed visual world. The quality bar is Downie on macOS. Two failure modes the owner named: a grey system dialog with no hierarchy, and template SaaS (lavender cards and pills, like the 1.x window).

## Evidence on Hand

- `README.md` and `README_PORTABLE.txt`: bilingual user documentation.
- No testimonials, usage numbers, ratings or press exist. Do not invent any.

## Product Principles

1. First launch succeeds without reading anything: paste, press, get the file.
2. Cutting a clip is optional but first-class, never a hurdle on the way to a full download.
3. Every failure ends with a next step the person can take inside the app.
4. Local and portable: the file, the session and the log live beside the app, and the app says so plainly.
5. English and Russian are equal; Russian runs longer and the layout must hold it.
