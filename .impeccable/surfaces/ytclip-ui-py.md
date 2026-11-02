---
version: 1
slug: "ytclip-ui-py"
primary_target: "ytclip/ui.py"
related_targets: []
---

# Main window

Scope: the single Clipify window (desktop, CustomTkinter), every state: idle, typing, validation, queued, downloading, saved, failed, cancelled, YouTube sign-in, English and Russian, light and dark.

Mode: Operate. Audience: non-technical people who downloaded a release from GitHub. Task: paste a YouTube link, optionally set start/end and folder, download, open the result. Constraints: one window around 720×600 (resizable), system light/dark theme, EN and RU, bundled assets only.

## Direction contract

THESIS: The category-standard downloader done at Downie's level of care: one link field, one blue Download button, and a downloads list that shows every job's progress, result and next step in place. It refuses both the 1.x lavender SaaS card and the grey system dialog.

OWN-WORLD: Platform neutrals: white window, ink #111827, secondary #4B5563, hairlines #E5E7EB, a single action blue #2563EB; dark mode mirrors it on #1E1F22 with #F3F4F6 ink; filled controls keep #2563EB so white labels hold AA, and only text links lighten to #60A5FA. System UI type (Segoe UI Variable / Segoe UI on Windows, SF Pro on macOS) in a tight 12/13/15/20 scale. 6px radii, 1px borders, standard inputs, checkbox, dropdown and list rows; Bootstrap Icons glyphs at one weight.

STORY: A first-time visitor sees immediately what to paste and what to press. Clip times and folder are optional and sit in one row. The list below confirms each download and offers the next action (show the file, retry, sign in) without toasts or modals.

FIRST VIEWPORT: 720×600. Header 56px: blue logo tile, "Clipify", "by PanCrucian", language dropdown at right, hairline below. Body: link label, input with Paste button; one row of Start (120px), End (120px), Save to (folder + Change…); exact-cut checkbox; full-width 46px blue Download button. A bordered Downloads list fills the remaining height with a teaching empty state. Footer: YouTube sign-in status at left, ©PanCrucian at right.

FORM: Canon (the category standard, the standing exit), chosen by the user over the rolled metro-line direction; it is not on the ordered list. Quality bar: Downie (macOS). seed:45673cd19a4d77de

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Open decisions

- None blocking. The app icon is regenerated through the Codex plugin to match this look.
