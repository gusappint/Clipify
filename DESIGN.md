---
name: Clipify
description: The category-standard YouTube downloader window, executed at Downie's level of care.
colors:
  window: "#FFFFFF"
  window-dark: "#1E1F22"
  panel: "#F9FAFB"
  panel-dark: "#25262A"
  field: "#FFFFFF"
  field-dark: "#2A2B2F"
  field-border: "#D1D5DB"
  field-border-dark: "#3F4148"
  field-border-strong: "#9CA3AF"
  field-border-strong-dark: "#5A5D66"
  hairline: "#E5E7EB"
  hairline-dark: "#2E3035"
  ink: "#111827"
  ink-dark: "#F3F4F6"
  secondary: "#4B5563"
  secondary-dark: "#B4B9C2"
  muted: "#6B7280"
  muted-dark: "#8E949E"
  action-blue: "#2563EB"
  action-blue-hover: "#1D4ED8"
  link-blue: "#2563EB"
  link-blue-dark: "#60A5FA"
  on-accent: "#FFFFFF"
  button-hover: "#F3F4F6"
  button-hover-dark: "#33353A"
  track: "#E5E7EB"
  track-dark: "#34363C"
  info-soft: "#EFF6FF"
  info-soft-dark: "#1C2740"
  info-line: "#BFDBFE"
  info-line-dark: "#2B3E66"
  success: "#15803D"
  success-dark: "#4ADE80"
  success-soft: "#F0FDF4"
  success-line: "#BBF7D0"
  danger: "#DC2626"
  danger-dark: "#F87171"
  danger-soft: "#FEF2F2"
  danger-line: "#FECACA"
typography:
  display:
    fontFamily: "Segoe UI Variable Display, Segoe UI, -apple-system, SF Pro Display, system-ui, sans-serif"
    fontSize: "clamp(2.25rem, 1.4rem + 2.6vw, 3.5rem)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Segoe UI Variable Display, Segoe UI, -apple-system, SF Pro Display, system-ui, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Segoe UI Variable Display Semibold, Segoe UI Semibold, -apple-system, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 600
  action:
    fontFamily: "Segoe UI Variable Text Semibold, Segoe UI Semibold, -apple-system, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 600
  body-strong:
    fontFamily: "Segoe UI Variable Text Semibold, Segoe UI Semibold, -apple-system, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
  body:
    fontFamily: "Segoe UI Variable Text, Segoe UI, -apple-system, SF Pro Text, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  label:
    fontFamily: "Segoe UI Variable Text, Segoe UI, -apple-system, SF Pro Text, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
  numeric:
    fontFamily: "Segoe UI, -apple-system, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    fontFeature: "tnum"
rounded:
  hairline: "2px"
  sm: "4px"
  control: "6px"
  container: "8px"
spacing:
  gap-xs: "8px"
  gap-sm: "12px"
  row-inset: "14px"
  section: "16px"
  page-x: "24px"
  field-height: "40px"
  primary-height: "46px"
  header-height: "56px"
components:
  button-primary:
    backgroundColor: "{colors.action-blue}"
    textColor: "{colors.on-accent}"
    typography: "{typography.action}"
    rounded: "{rounded.control}"
    height: "{spacing.primary-height}"
  button-primary-hover:
    backgroundColor: "{colors.action-blue-hover}"
  button-secondary:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    typography: "{typography.body-strong}"
    rounded: "{rounded.control}"
    height: "{spacing.field-height}"
  button-secondary-hover:
    backgroundColor: "{colors.button-hover}"
  button-row-action:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    height: "30px"
    width: "96px"
  input-text:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "{spacing.field-height}"
  input-readonly-path:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "{spacing.field-height}"
    padding: "0 12px"
  notice-info:
    backgroundColor: "{colors.info-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.container}"
    padding: "9px 6px 9px 12px"
  list-panel:
    backgroundColor: "{colors.window}"
    rounded: "{rounded.container}"
  list-row:
    backgroundColor: "{colors.window}"
    textColor: "{colors.ink}"
    typography: "{typography.body-strong}"
    padding: "12px 14px"
  progress-track:
    backgroundColor: "{colors.track}"
    rounded: "{rounded.hairline}"
    height: "4px"
---

# Design System: Clipify

## Overview

**Creative North Star: "The Well-Made Standard"**

Clipify is the downloader window everyone already knows how to use: one link field, one blue button, a list of downloads. It earns its place by finish rather than invention. Platform neutrals carry the whole window, a single action blue marks the one thing to press, and every job's progress, result and next step lives in place in the list, never in a toast or a modal. The quality bar is Downie on macOS.

Density is compact desktop: a resizable window around 720×600, 13px body text, 40px controls, 24px page margins, hairlines instead of cards. The website at docs/ is the same world in CSS: the same neutrals, the same blue, the same system faces, the same 6px controls, scaled up for reading.

The system rejects two named failure modes: the grey system dialog with no hierarchy, and template SaaS (lavender cards and pills, as in the 1.x window).

**Key Characteristics:**
- White (or #1E1F22 graphite) window, cool gray ink ladder, one action blue.
- System UI faces only; weight and size carry hierarchy, never colour.
- 1px borders and hairlines, 6px controls, 8px containers, no shadows inside the app.
- Status is spoken by a 14px glyph plus a coloured line of text, not by chips or badges.
- Every light value has a dark twin; the window follows the system theme.

## Colors

A cool gray neutral ladder with one blue for action and two semantic tones for outcomes; every token is a light/dark pair resolved against the system theme.

### Primary
- **Action Blue** (`action-blue`): the fill of the Download button, of row actions that are the next step (Sign in, Sign in again), the checked checkbox, the progress bar, the focus border on fields and the focus ring on secondary buttons. It does not change in dark mode, on purpose: white text needs its contrast, and a lighter blue would wash the button out.
- **Pressed Blue** (`action-blue-hover`): hover on every blue-filled control, both themes.
- **Link Blue** (`link-blue` / `link-blue-dark`): text-only links (Clear finished, Sign in, ©PanCrucian) and the info glyph. This is the one place blue lightens in dark mode, because it sits on graphite as text, not as a fill.

### Neutral
- **Window** (`window` / `window-dark`): the window, the downloads list body, the website page.
- **Panel** (`panel` / `panel-dark`): the read-only folder path field and website hover fills; one quiet step off the window.
- **Field** (`field` / `field-dark`): editable inputs, secondary buttons, the language menu.
- **Field Border** (`field-border` / `field-border-dark`): resting 1px border on inputs and secondary buttons; also the scrollbar thumb.
- **Strong Border** (`field-border-strong` / `-dark`): the unchecked checkbox outline and scrollbar hover.
- **Hairline** (`hairline` / `hairline-dark`): the rule under the header, the list header rule, row dividers, the list panel outline, every website section border.
- **Ink** (`ink` / `ink-dark`): titles, labels, field text, row titles.
- **Secondary** (`secondary` / `secondary-dark`): footer session status, website lead and body copy, dismiss and chevron glyphs.
- **Muted** (`muted` / `muted-dark`): placeholders, hints, counts, version, row status lines, queued and cancelled glyphs.
- **Button Hover** (`button-hover` / `-dark`) and **Track** (`track` / `-dark`): secondary-button hover and the empty progress track.

### Semantic
- **Success** (`success` / `success-dark`, with `success-soft` and `success-line`): the Saved glyph and the success notice.
- **Danger** (`danger` / `danger-dark`, with `danger-soft` and `danger-line`): failure glyphs, failure status lines, invalid-field borders, the error notice.
- **Info** (`info-soft` / `info-line`): the default notice banner's fill and border.

### Named Rules
**The One Blue Rule.** Action Blue fills exactly one kind of thing: the action the person should take next. One full-width Download button per window; inside the list, a row action turns blue only when it is the recovery step (sign in). Retry, Cancel, Remove and Show in folder stay neutral.

**The Paired Token Rule.** No colour enters the app as a single value. Every token is a (light, dark) pair in `ytclip/theme.py`, and icon glyph colours are derived from the same pairs (`ICON_TONES`) so baked PNGs cannot drift from the palette.

## Typography

**Display Font:** Segoe UI Variable Display (with Segoe UI, then the macOS system face)
**Body Font:** Segoe UI Variable Text (with Segoe UI, then the macOS system face)
**Numeric Font:** static Segoe UI on Windows, for its tabular figures

**Character:** The platform's own voice, chosen on purpose instead of a bundled face: it renders natively at every DPI, covers Cyrillic fully, and makes the window feel like it belongs to the OS.

### Hierarchy
- **Display** (600, clamp 2.25–3.5rem, 1.08): website hero headline only.
- **Headline** (600, 1.875rem, 1.2): website section headings.
- **Title** (semibold, 20px): the "Clipify" wordmark in the 56px app header.
- **Action** (semibold, 15px): the primary Download button label.
- **Body Strong** (semibold, 13px): field labels, secondary button labels, the Downloads heading, row titles, empty-state title.
- **Body** (regular, 13px): field text, placeholders, checkbox label, menu items. Website body is 1rem/1.6.
- **Label** (regular, 12px): hints, the byline, counts, notice text, footer, links, compact buttons.
- **Numeric** (regular, 12px, tabular): live progress lines (percent, sizes, speed, time left), so figures do not jitter.

### Named Rules
**The Semibold Family Rule.** On Windows 11 the strong roles use the named Semibold family ("Segoe UI Variable Text Semibold"), not `weight="bold"` on the variable face; Tk would otherwise synthesize a heavier bold. Bold weight is used only when no Semibold family exists.

**The Two-Step Ramp Rule.** The app's ramp is 12 / 13 / 15 / 20. A new size must justify itself against these four.

## Layout

The window is a single column with a fixed 24px page margin (`page-x`). Top to bottom: a 56px header (logo tile, wordmark, byline, language menu at right) over a full-width hairline; the form (link label, link field + Paste; one row of Start 120px, End 120px, Save to path + Change…; exact-cut checkbox with inline hint; full-width 46px Download button); an optional notice banner; the bordered downloads list, which takes every remaining pixel; a 40px footer with the YouTube session status at left and version + ©PanCrucian at right.

Rhythm: 6px from label to control, 8px between a field and its attached button, 12px between fields in a row, 14px before the Download button and the notice, 16px before the list. A 20px reserved message line under the link and time fields holds hints and errors, so validation never shifts the layout. Russian runs longer; button widths (92–118px) are sized for it.

List rows: 80×45 thumbnail (4px corners), 14px side insets, 12px vertical padding, title and status stacked, one action at the right, a hairline between rows inset 14px.

Website: content column `min(1120px, 100% - 48px)` (32px gutters under 560px); two-column hero (1.18fr / 1fr) collapsing to one column under 900px; 72px section padding (56px on narrow screens); three-up steps and two-up feature list collapse to one column.

## Elevation & Depth

The app is flat. Depth comes from tonal steps (window → panel → field) and 1px lines, never from shadow; CustomTkinter has no shadow primitive and the system does not want one. The website adds exactly one shadow, under the product screenshot, to lift the window image off the page.

### Shadow Vocabulary
- **Product shot** (`0 18px 40px -18px rgba(17,24,39,0.35), 0 4px 12px -6px rgba(17,24,39,0.18)`; dark: `0 18px 44px -16px rgba(0,0,0,0.7), 0 4px 12px -6px rgba(0,0,0,0.5)`): website screenshot only.

### Named Rules
**The Line Not Lift Rule.** Separation is a hairline or a 1px border. If something needs to stand apart inside the window, it gets a border or a tonal fill, not a shadow.

**The Drawn Hairline Rule.** CustomTkinter skips drawing frames 1px tall, so a hairline is a 1px frame whose `bg_color` is set to the hairline colour as well as its `fg_color`. Use the `hairline()` helper; never a 1px frame with `fg_color` alone.

## Shapes

Gently rounded and consistent: 6px (`control`) on every interactive control (inputs, all buttons, the language menu trigger, the notice dismiss), 8px (`container`) on containers (downloads list, notice banner), 4px (`sm`) on small items (thumbnail placeholder, checkbox, website `kbd`), 2px on the 4px progress bar. Borders are always 1px at rest; focus thickens to 2px. Loaded thumbnails are shown square-cornered. The website's numbered step markers are the only circles.

## Components

### Buttons
Conventional, quiet, sized to the field they sit beside.
- **Shape:** 6px corners (`control`).
- **Primary:** Action Blue fill, white 15px semibold label, 46px tall, full width of the form, with a white download glyph at left. Disabled uses the muted disabled text.
- **Secondary:** Field fill, 1px Field Border, ink 13px semibold label, 40px tall (Paste, Change…). The language trigger is the 32px/12px variant with a chevron at right.
- **Row action:** 30px tall, 96px wide (118px for Show in folder and Sign in again), 12px label; neutral by default, Action Blue only for the sign-in recovery step.
- **Hover / Focus:** hover swaps to the hover token. Keyboard focus draws a 2px ring: Action Blue on neutral buttons, Ink on blue-filled buttons so the ring stays visible against the fill. Enter and Space activate every focusable control.
- **Website:** same 46px height and 6px radius, 16px horizontal padding, 160ms ease-out background transition.

### Inputs / Fields
- **Style:** Field fill, 1px Field Border, 6px corners, 40px tall, 13px body text.
- **Placeholder:** muted text drawn as an overlay label at x=8. CustomTkinter hides native placeholders on variable-bound entries, so the overlay is the mechanism; it hides when the variable has text and focuses the entry on click.
- **Focus:** border goes to Action Blue at 2px.
- **Error:** border goes to Danger at 1px, with the message in Danger in the reserved line below; at rest that line shows a muted format hint.
- **Read-only path:** the Save to field is a Panel-filled box with the path middle-truncated (drive and final folder stay visible), paired with Change….
- **Checkbox:** 18px box, 4px corners, 2px Strong Border unchecked, Action Blue fill with white check when on; focus turns the border blue. A 12px muted hint sits 10px to its right.

### Notice Banner
A tinted, bordered strip between the form and the list: 8px corners, 1px line, 16px glyph at left, 12px ink text that wraps, a 26px transparent dismiss button at right. Three tones (info, success, danger) each use their `-soft` fill and `-line` border. It replaces dialogs; auto-hiding notices stay for reading time plus 2 seconds.

### Downloads List (signature)
A window-coloured panel with an 8px corner and 1px hairline outline. Header row (40px): "Downloads" in body strong, a muted count, a Clear finished link at right, a hairline below. Each row: thumbnail (film glyph placeholder until the real frame arrives), title in body strong truncated with an ellipsis, a status line led by a 14px glyph (clock for waiting, filled check for saved, filled exclamation for failed, x-circle for cancelled) in muted or Danger text, a 4px Action Blue progress bar on a Track while running, and exactly one action. Empty state: a centred body-strong title over a muted 12px teaching line.

### Links
Text-only, 12px, Link Blue (or Secondary where the link is metadata). Underline appears on hover and on keyboard focus; no buttons dressed as links. Website links underline at 1px with 3px offset, 2px on hover.

### Iconography
Bootstrap Icons 1.13.1 at one weight, rendered by `scripts/generate_icon.py` into light and dark PNGs from `ICON_TONES`, 64px supersampled and scaled down (14px status, 16px notice, 12px chevron and dismiss). Website icons are inline SVG from the same set. The app icon is a blue tile with a white download arrow, generated from `assets/source/clipify-icon-1024.png`.

## Do's and Don'ts

### Do:
- **Do** take every colour from the (light, dark) pairs in `ytclip/theme.py`; add a new token as a pair or not at all.
- **Do** keep Action Blue at #2563EB in dark mode for filled controls, and use Link Blue (#60A5FA) only for text on graphite.
- **Do** use the system faces through `Typography` and the 12 / 13 / 15 / 20 ramp; use the numeric face for live figures.
- **Do** draw 1px rules with the `hairline()` helper and placeholders with the overlay label.
- **Do** give every focusable control a visible 2px focus state and Enter/Space activation.
- **Do** report outcomes in place: a glyph and a status line in the row, a notice banner above the list.
- **Do** size buttons and labels for the Russian copy, which runs longer than English.

### Don't:
- **Don't** add a second filled-blue button to a view; row recovery actions are the only exception.
- **Don't** introduce toasts, modals or pills for status.
- **Don't** add shadows inside the app.
- **Don't** bundle a display or text typeface; the system faces are the decision.
- **Don't** rebuild the lavender cards and pills of the 1.x window, or flatten the window into a grey dialog with no hierarchy.
- **Don't** mix icon sets or weights; new glyphs come from Bootstrap Icons through `GLYPHS` in `scripts/generate_icon.py`.
