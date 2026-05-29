# Theme & Settings

The Settings slide (slide 0) is a live theme editor. Every change previews in real time and persists across browser restarts via `localStorage`.

---

## Accessing Settings

Three ways:
- Navigate to `index.html?edit` — lands on slide 0 by default
- Append `#0` or `#00` to the URL: `index.html#0`
- Click the settings icon in the top-right chrome

The Settings slide doesn't appear in the normal presentation flow — navigation skips it. It's only accessible directly.

---

## Color Controls

### Primary & Secondary Colors

Two hex color pickers update the accent colors throughout the deck. The primary maps to the first accent slot; secondary to the second. The four accents (`--teal`, `--purple`, `--amber`, `--rose`) are set per-chapter in SECTIONS — these controls let you adjust the actual color values those names resolve to.

Tip: use `tools/extract_palette.py` to pull a palette from a reference image automatically. See [Import & Export Tools](08-import-export.md#palette-from-reference-image).

### Background Darkness

A slider that controls `--bg`. Drag left for lighter, right for darker.

---

## Font Controls

### Font Family

Choose from presets or type any Google Font name:
- Space Grotesk (default)
- Inter
- Outfit
- JetBrains Mono
- Playfair Display
- _Enter any name from fonts.google.com_

The `@import url(...)` in the CSS updates dynamically. Custom fonts load from Google Fonts.

### Title Scale

Adjusts `--title-scale` from 60% to 130%. Controls title font sizes across all slides.

### Tagline Scale

Adjusts `--tagline-scale` from 60% to 150%. Controls body/tagline text sizes.

### Paragraph Gap

Controls `--para-gap` — the extra space inserted on double `<br><br>` line breaks in taglines.

---

## Transition Style

Choose the animation between slides:

| Style | Effect |
|-------|--------|
| **Slide** (default) | Horizontal slide left or right |
| **Fade** | Simple opacity crossfade |
| **Zoom** | Scale + fade (zoom in going forward, zoom out going back) |
| **None** | Instant swap, no animation |

---

## Background Styles

A visual layer behind your slides — purely aesthetic, never interferes with content. Six styles:

| Style | Effect |
|-------|--------|
| **None** (default) | Clean dark background |
| **Aurora** | Soft drifting color clouds |
| **Ember** | Warm glowing embers rising |
| **Ghost** | Subtle floating wisps |
| **Nebula** | Deep-space star field with color haze |
| **Extreme** | High-intensity version of the current style |

### Background Blend Mode

Controls how the background layer mixes with slide content. Options: Screen, Soft Light, Overlay, Hard Light, Color Dodge, Lighten, Color Burn, Multiply, Difference, Normal.

All background styles are GPU-only (CSS `transform` + `filter:blur` on `will-change` layers) — they don't impact scroll or layout performance. Inactive styles are `display:none` so unused animations don't run.

> Preview background styles at `tools/bg-preview.html` — includes a toggle to overlay a static image so you can judge readability.

---

## Arrow Substep Toggle

**On** (default): pressing `→`, tapping, or swiping steps through sub-animations on a slide before advancing to the next slide.

**Off**: every advance goes straight to the next full slide. Good for fast Q&A navigation.

This is also settable per-session from the toggle in Settings.

---

## Image Hold Duration

How long the media cycler holds each image before advancing. Default: 6000ms (6 seconds). This is a global default; individual cycler IIFEs can override it with their own `imageDuration` option.

---

## Auto-Save Snapshots

Spatial Deck saves your work automatically:
- Every **60 seconds** after first interaction
- Saves both your **annotations** (positions, text edits) and **config** (all settings)
- Keeps the last **10 snapshots**

### Restoring a Snapshot

Click **🔄 Restore Snapshot** in Settings to see a timestamped list. Click any snapshot to restore — annotations and config are rolled back and the page reloads.

This is your safety net if you accidentally move something and want to go back.

---

## Export for Offline

Click **📦 Export for Offline** in Settings to generate a self-contained version:
1. Downloads Three.js locally to `lib/`
2. Patches the import map in `index.html` to use the local file
3. The result works from `file://` on any computer, no internet needed

For full offline support (fonts too), self-host your Google Font:
1. Download the font files from fonts.google.com
2. Add a local `@font-face` rule in the `<style>` block
3. Remove the Google Fonts `@import`

---

## Duration Estimator

The Settings slide shows an estimated total talk duration based on all speaker notes in SECTIONS. The formula:
- Bullet-style notes: ~20 seconds per bullet
- Prose-style notes: ~150 words per minute
- No notes: 30 seconds default per slide
- Multi-step slides: +5 seconds per step

This is the same formula used by the pacing indicator in the Presenter Popup.

---

## CSS Custom Properties

All theme values are CSS custom properties on `:root`. You can hardcode defaults by editing the `:root` block in the `<style>` tag:

```css
:root {
  --bg: #0a0a0f;
  --teal: #2dd4bf;
  --purple: #a78bfa;
  --amber: #fbbf24;
  --rose: #fb7185;
  --text: #f8fafc;
  --dim: #94a3b8;
  --font: 'Space Grotesk';
  --para-gap: 0.8em;
  --tagline-scale: 1;
  --title-scale: 1;
}
```

Changes to `:root` are the hardcoded defaults; `localStorage` values override them at runtime. If you want to ship a deck with specific defaults (so it looks right even for someone who's never opened your Settings), set them in `:root`.
