# Spatial Deck — AI Agent Handoff Prompt

> **Last updated:** 2026-05-06
> **Purpose:** Read this file at the start of any AI session working on this project. It gives you everything you need to be productive immediately.
> **Maintenance:** Update this file whenever you make significant changes to the architecture, add major features, or change conventions. Future sessions depend on this being accurate.

---

## What Is This?

Spatial Deck is a single-file HTML presentation framework. Everything — CSS, JS, config, and content — lives in `index.html`. No build process, no dependencies (except Three.js via CDN for the optional constellation map).

**Repo:** https://github.com/ibrews/spatial-deck
**Live demo:** Open `index.html` in any browser
**Origin:** Built for the Harvard XR Conference 2026 keynote, then extracted and generalized. See the original keynote at https://ibrews.github.io/harvardxr-keynote/

---

## Architecture at a Glance

```
index.html
├── <style> .......................... All CSS (~200 lines, minified)
├── <script type="importmap"> ....... Three.js CDN mapping
├── <div id="deck"> ................. Slide container (empty, JS fills it)
├── <script> (first) ................ SECTIONS config + BONUS const (~50 lines)
└── <script> (second, main) ......... Everything else (~750 lines):
    ├── Settings slide creation + theme editor
    ├── Cover / Bonus / Map / Close slide creation
    ├── SECTIONS.forEach → lesson + case slide generation
    ├── buildMediaCycler() function
    ├── Auto-wrap static images
    ├── Explicit media cycler IIFEs
    ├── Map constellation builder (startMap)
    ├── Slide navigation (goTo, nextVisible, slideSteps)
    ├── Annotation system
    ├── Move mode + undo/redo
    ├── Text editing
    ├── Search overlay
    ├── Slide grid
    ├── Speaker notes + presenter popup
    ├── Duration estimator
    └── Offline export helper
```

---

## Key Conventions

### SECTIONS Array
- Each entry: `{ year, accent, lesson: {title, tagline, short, tags, notes}, cases: [{title, subtitle, img, bullets, notes}] }`
- `accent` values: `'teal'`, `'purple'`, `'amber'`, `'rose'`
- `img` values: `'MEDIA_CYCLER'` (explicit cycler IIFE needed), `'path/to/image.jpg'` (renders as `<img>` tag), `'IFRAME:url'` (embedded iframe — YouTube, pixel stream, Sketchfab, etc.), `''` (gradient placeholder)
- Build loop `img` priority: `IFRAME:` prefix → iframe, real path → `<img>` tag, `MEDIA_CYCLER` → media cycler mount, empty → gradient placeholder
- `\n` in titles renders as a line break
- `<br>` and `<br><br>` work in taglines (double = paragraph gap)
- `\n` in bullets renders as `<br>`
- `notes` field is optional; used by speaker notes system

### Slide Types & dataset Attributes
- `dataset.type`: `'settings'`, `'cover'`, `'lesson'`, `'case'`, `'bonus'`, `'map'`, `'close'`
- `dataset.year`: the section's year (string)
- `dataset.section`: index into SECTIONS array
- `dataset.hidden`: `'1'` = hidden from navigation
- `dataset.parked`: `'1'` = moved to end by PARK IIFE

### Media Cycler
- `buildMediaCycler(slideEl, items, opts)` — call after slides are built
- Items: `{type:'image'|'video', src:'path', flipH:bool, loop:bool}`
- Options: `{imageDuration, portrait, enterDur, revealDur, exitDur}`
- Canvas dynamically adapts to source aspect ratio (no cropping)
- Single-item images stop after reveal; single-item videos loop
- Find slides by: `allSlides.find(s => s.querySelector?.('.case-title')?.textContent.includes('Title'))`

### Slide Steps
- `slideSteps.set(slideEl, { current:0, steps: [fn1, fn2, ...] })`
- Each click calls the next step function before advancing to next slide
- Steps registered via `setTimeout(()=>{slideSteps.set(...)}, 0)` to defer past declaration

### Theme System
- CSS custom properties on `:root`: `--bg`, `--teal`, `--purple`, `--amber`, `--rose`, `--text`, `--dim`, `--font`, `--para-gap`, `--tagline-scale`, `--title-scale`
- Settings slide has live controls, saved to `localStorage` key `'spatial-deck-cfg'`
- Font loaded via Google Fonts `@import` that's dynamically updated

### Navigation
- `goTo(n)` — main navigation function, handles animations + per-slide-type hooks
- `nextVisible(from, dir)` — skips hidden slides
- `current` = index into `allSlides` array
- `total` = `allSlides.length`
- URL hash: `#N` jumps to slide N (0-indexed, settings=0, cover=1). `#0` and `#00` both go to settings
- Counter displays `current` (settings shows "00"); grid carousel numbering is 0-indexed (00 for settings)
- `history.replaceState` writes `#current` on every navigation

### URL Sharing Modes
- Default (no params) = view mode (presentation mode, edit chrome hidden)
- `?edit` = edit mode (all chrome visible, overrides mobile auto-hide)
- `?view` = explicit view mode
- `?landscape` = portrait-orientation prompt overlay on mobile

### Export Modes (`?print` / `?shot=N`) — 2026-06-09
- `?print` = all visible slides stacked as static 16:9 pages (print CSS near the vertical-mode block; `@page` 13.333×7.5in). Hidden slides excluded. Appends `#sd-print-manifest` (JSON: per-slide type/title/degradation flags) to `<body>` for the export tooling.
- `?shot=N` = slide N alone (absolute index, settings=0), full-viewport, chrome hidden — for per-slide screenshot capture.
- Both modes run synchronously at parse time: mode class applied, `slideSteps` run to completion (two chained `setTimeout`s later), `document.getAnimations().finish()`, media cyclers replaced by static first item (patch installed after the GIF wrapper), iframes → `.sd-iframe-ph` placeholder panels, videos frozen on an early frame.
- Driven by `tools/capture_slides.py` (headless Chrome; **treats the output artifact, not process exit, as completion** — Chrome 149/macOS often never exits after `--dump-dom`/`--screenshot`) and `tools/export_pdf.py` (PNG→JPEG→stdlib PDF writer, fidelity report).
- `tools/export_video.py` records the LIVE deck (no export mode — normal runtime) by auto-pressing ArrowRight through every slide/substep via playwright-core + system Chrome, then ffmpeg→MP4. End detection: hash + `#step-indicator` fingerprint unchanged for 2 presses at the last visible slide. ESM gotcha: `NODE_PATH` is ignored by `import` — the runner uses `createRequire(import.meta.url)` with an absolute path. playwright-core auto-installs to `~/.cache/spatial-deck/video-deps`.

### Mobile
- Auto-detect via `(max-width:900px)` or `(pointer:coarse)`
- Auto-enter presentation mode; 👁 button toggles chrome
- Tap (< 15px, < 300ms) = advance step/slide
- Swipe left/right = navigate (respects steps + hidden slides)

### Arrow Substep Toggle
- `arrowSubstep` in config (default: `true`), checkbox in Settings
- When On: arrows/tap/swipe step through sub-animations before advancing
- When Off: always skip to next full slide
- `window._arrowSubstep` flag checked by all navigation handlers

### SFX Cleanup
- `AudioContext` constructor is monkey-patched to auto-register in `_activeAudioCtxs` Set
- `window._killAllSfx()` closes all active contexts — called by `goTo()` on every slide change
- No manual registration needed; all SFX functions automatically tracked

### Z-Ordering
- Move mode HUD has ▲▲/▲/▼/▼▼ buttons for Send to Front/Forward/Backward/Back
- Operates on last-clicked/dragged element via `_lastMoveEl`
- Sets `style.zIndex` on the element

### Annotations & Move Mode
- Annotations saved to `localStorage` key `'sd-annos'`
- Move transforms auto-saved as annotations (`type: 'move'`) — appear in Annotations panel immediately
- Text edits saved as: `TEXT "new content"`
- Undo/redo: 50-action stack, `Cmd+Z` / `Cmd+Shift+Z`
- **Position annotations**: clicking slide background captures `left:X%, top:Y%` coordinates
- **Layout grid**: `G` key in move mode toggles 4×3 labeled grid (A1-C4 zones)
- **Clipboard snippets**: after drag, CSS position code auto-copied to clipboard

### Keyframe Animation System
- `◆ KF` button in scrubber captures last-moved element's transform at current scrub time
- Diamond markers (◆) on timeline show existing keyframes; click to seek
- `✕ KF` deletes the keyframe at current scrub time
- Keyframes persisted as annotations (`type: 'keyframe'`)
- Two or more keyframes on the same element build a WAAPI (Web Animations API) animation automatically
- Map node clicks are suppressed in move mode to prevent accidental navigation

### Slide Transitions
- Configurable in Settings slide: `slide` (default), `fade`, `zoom`, `none`
- Saved to localStorage config as `transition` property
- `goTo()` reads preference and uses corresponding CSS keyframes

### Auto-Save Snapshots
- Every 60 seconds after first interaction, annotations + config saved to `sd-snapshots`
- Keeps last 10 snapshots; skips if nothing changed
- "🔄 Restore Snapshot" button in Settings shows timestamped list
- Restoring replaces annotations + config and reloads page

### Map Constellation
- Center text: "IS XR RIGHT / FOR YOUR PROJECT?" (updates with deck content)
- Bonus node positioned bottom-right outside the circle
- Node clicks suppressed in move mode

### Settings Slide
- Shows "Spatial Deck Creator v0.0.5 / by Alex Coulombe" header
- Slide 0, accessible via `#0` or `#00`

### Speaker Notes
- `notes` field in SECTIONS config (string)
- `N` key opens presenter popup (BroadcastChannel sync)
- `Shift+N` toggles inline drawer
- `Shift+P` toggles **split presenter view**: deck shrinks to top 58%, notes drawer pins to bottom 42% (no overlap). Auto-opens the notes drawer. Toggle again to exit.
- Duration estimator: ~20s/bullet, ~150wpm prose, 30s default per noteless slide

### Haptic Pacing Alerts (mobile only — `navigator.vibrate`, no-op on desktop)
- **Light pulse (120ms)** — once per minute when elapsed > 110% of estimated duration (running behind)
- **Hard double-pulse (250–80–250ms)** — every 10 seconds during the final minute of the talk
- Both fire inside `updateTimers()` (runs in both main deck and `?notes` modes)
- Reset state (`_lastVibMinute`, `_lastVibTenSec`) cleared on timer reset

### `?notes` Collapsible Slide Preview
- 🖼 button in the topbar toggles a collapsible thumbnail panel above the notes content
- Shows calibrated 160×90 thumbnail for the current slide (from `sd-thumbs-<deckId>` localStorage)
- Falls back to slide title + "Calibrate to see thumbnail" hint if no thumbnail exists
- Panel updates automatically on slide change when open

### `?notes` Phone Speaker Companion (2026-05-06)
- URL: append `?notes` (e.g. `index.html?notes`) → renders a phone-optimized speaker view instead of the deck
- Topbar: ▶/⏸ timer, ⟲ long-press reset, 🔓 padlock clicker, 📋 view toggle (script ↔ bullets), ✎ edit current, ⋯ settings drawer
- Bottom: ← / Up next thumbnail / → buttons. No tap-zone navigation — use the buttons.
- Settings drawer: Default view (bullets/script), 🔁 Calibrate Videos & Thumbs, 📤 Reseed from SECTIONS, ≡ Edit all (full doc), ⏱ Set target finish
- **Cloud sync** via Google Apps Script Web App bound to a Google Sheet. Setup: see `tools/SETUP_NOTES_SYNC.md`. Drop `notes-config.json` (gitignored) at repo root with `{"gasUrl":"...","deckId":"..."}`. First load auto-seeds the sheet from SECTIONS notes.
- Without `notes-config.json` → local-only mode (toast notification, no overlay). Edits stay in localStorage per device.
- Calibration sweep captures `<video>.duration` and 160×90 thumbnails per slide → cached to localStorage `sd-thumbs-<deckId>` and pushed to sheet `meta.calibration`.
- Pacing: wall-clock target finish, projected finish via adaptive WPM (samples completed slides, floors 90, caps 220). `(over video)` marker in script tells the estimator that words after it are spoken concurrent with video.
- Padlock clicker: when 🔒, phone advances broadcast to laptop via sheet `meta.state` polled at 1s. Same Tailscale/LAN restrictions apply (BroadcastChannel is intra-browser; sheet relay handles cross-device).

### Animated Background Styles (2026-05-06)
- Settings slide → "Background Style" picker: None / Aurora / Ember / Ghost / Nebula / Extreme
- Settings slide → "Background Blend" picker: Screen / Soft Light / Overlay / Hard Light / Color Dodge / Lighten / Color Burn / Multiply / Difference / Normal
- Pure CSS, GPU-only (`transform` + `filter:blur` on `will-change` layers, `mix-blend-mode` on overlay container). Inactive overlays are `display:none` so unused animations don't run.
- Wired via `body[data-bg-style]` attribute and `--bg-blend` CSS variable, both set in `apply()`.
- The `.cfg-panel` becomes more transparent when bg style is non-`none` so you can preview the effect on slide 0 in real time.
- Test/preview page: `tools/bg-preview.html` (also includes a 🖼 Image overlay toggle to judge readability over a static image).

### Annotations & Settings Round-Trip
- Annotation panel (press `A`) now pins a "⚙ Slide 0 · current settings (auto-tracked)" card at the top, listing every cfg key. Auto-refreshes on any `apply()` call.
- "Copy All" markdown export prepends a "Current Settings" section listing all cfg values.
- Workflow: user tweaks slide 0 settings → exports annotations → pastes back to AI → AI updates `D` defaults to match. Lossless round-trip.

### `?edit` URL Behavior
- `?edit` with no hash → lands on slide 0 (settings) so users can configure first.
- `?edit#5` (or any explicit hash) → normal `goToFromHash` flow.
- View mode (no `?edit`) → cover slide as before.

---

## Common Tasks

### Add a new lesson with cases
1. Add entry to SECTIONS array with year, accent, lesson, cases
2. If using MEDIA_CYCLER, add an IIFE after the build loop:
   ```javascript
   (function(){
     const slide = allSlides.find(s => s.querySelector?.('.case-title')?.textContent.includes('Title'));
     if (!slide) return;
     buildMediaCycler(slide, [{type:'image', src:'media/...'}], {imageDuration:6000});
   })();
   ```
3. If the lesson needs multi-step animation, register `slideSteps`

### Change the theme
- Edit CSS custom properties in `:root` for defaults
- Or use the Settings slide live controls (persisted to localStorage)

### Add media
1. Copy images/videos to `media/` subfolder
2. Resize to ≤2560px: `sips --resampleWidth 2560 file.jpg --out file.jpg`
3. Videos over 100MB: transcode with `ffmpeg -i in.mp4 -vf "scale=1280:-2" -crf 28 -preset fast out.mp4`
4. Reference via relative path in SECTIONS or media cycler IIFE

### Pull a video clip from YouTube or local source
Use `tools/import_video_clip.py` (added 2026-05-06):
```bash
# YouTube one-shot — download + trim + encode at full quality
python3 tools/import_video_clip.py "https://youtu.be/ID" --start 1:23 --end 1:45 --out media/foo.mp4

# Drive workflow — download manually first, then trim local file
python3 tools/import_video_clip.py ~/Downloads/video.mp4 --start 0:30 --duration 8 --out media/intro.mp4

# Two-phase YouTube — grab the source for scrubbing, then trim
python3 tools/import_video_clip.py "URL" --download-only --out work/raw.mp4
python3 tools/import_video_clip.py work/raw.mp4 --start 1:23 --end 1:45 --out media/clip.mp4

# Force size reduction post-trim (default is full quality, no shrink)
python3 tools/import_video_clip.py SOURCE --start 0:00 --end 5:00 --max-mb 95 --out media/long.mp4
```
- Default `--quality high` (CRF 21, 1280×720). Default `--max-mb 0` (no auto-shrink). Set `--max-mb 95` to fit GitHub's 100MB limit.
- Drive URLs are explicitly rejected with a 3-step manual-download recipe (no SA key on disk for browser-side API access).

### Park/hide slides
- **Park**: Add index to `PARK` array (0-indexed, pre-park position)
- **Hide**: `Ctrl+Click` thumbnail in slide grid, or set `dataset.hidden='1'`

### Export for offline
- Use the "📦 Export for Offline" button in Settings
- Or manually download Three.js + fonts (see README)

---

## Files

| File | Purpose |
|------|---------|
| `index.html` | The entire presentation |
| `images/` | AI-generated images (4 PNGs, 2 SVGs) |
| `media/` | Images, videos, GIFs (optional) |
| `tools/` | Fleet-powered importers (Claude Design handoff) — Python scripts that call local Ollama endpoints over Tailscale to normalize inbound content. Start here: `tools/fleet_client.py` (thin wrapper), `tools/import_tokens.py` (design-token → `:root{}` patcher), `tools/import_pptx.py` (PowerPoint → SECTIONS chapter JSON via llama3.1:8b), `tools/merge_sections.py` (splices imported chapter into SECTIONS between `// ── IMPORTED START ──` / `// ── IMPORTED END ──` sentinels, idempotent). `tools/samples/` has example inputs. |
| `docs/` | README screenshots |
| `social.html` | 1200×630 social sharing card |
| `social.png` | Pre-rendered social image |
| `README.md` | User-facing documentation |
| `HANDOFF_PROMPT.md` | You are here |

---

## Sample Content

The default deck is "Is XR Right For Your Project?" with 3 chapters and 6 case studies. Content is generic/anonymized (no client-specific references). Cover: "Spatial Deck · Open-Source Presentation Framework" / "Is XR Right For Your Project?". Bonus: "The Best XR Project Is the One You Don't Need". Closing: "Let's Talk." / "Thinking spatially?" with single QR code to the GitHub repo. Uses 6 AI-generated images from `images/` (4 PNGs, 2 SVGs). Replace SECTIONS + BONUS to create your own talk.

---

## Known Quirks

- **Any `</script>` inside a JS string MUST be written `<\/script>`.** The HTML parser ends the script block at the literal sequence regardless of JS string context. The presenter-popup `document.write(\`...\`)` template is the danger zone — an unescaped closer there (commit 67c8a1a) terminated the main runtime script mid-template-literal and the whole deck failed to boot until efdebf0. The PostToolUse validate-js hook catches this; don't bypass it with raw python file writes.
- `file://` URLs in Chrome trigger same-origin warnings for Three.js imports — harmless, or serve via `python3 -m http.server`
- AudioContext requires user interaction before first sound plays (browser policy)
- GIFs don't animate on canvas-rendered MEDIA_CYCLER — but as of 2026-05-06, `buildMediaCycler` auto-detects `.gif` items and switches to a cross-fading `<img>` rendering path so they animate. For non-cycler use (img tag), GIFs always animate. The "convert to MP4" workaround only matters if you're using the canvas pipeline explicitly.
- Very large media (>100MB) can't push to GitHub without Git LFS — use `tools/import_video_clip.py` with `--max-mb 95` to fit
- `slideSteps` must be registered in `setTimeout(fn, 0)` to defer past the `const slideSteps` declaration
- `mix-blend-mode` blends with the parent's background — apply at the overlay container level, NOT individual children. (Shipped this fix in `bg-preview.html` after seeing the effect not reach an image; the overlay container needs the blend mode for it to mix with siblings.)

---

*Keep this file updated. Future you (and future AI sessions) will thank present you.*

---

## Conventions

### Fork per presentation, not edits to main

`ibrews/spatial-deck` main = framework + template (`index.html`) + tools (`tools/import_*`, `export_*`, `lint_deck`, `peer_review`, etc.). Each *talk* is a self-contained fork where SECTIONS are baked into the fork's `index.html`.

- **Generic tools** (importers, exporters, linters) → commit to main. Precedent: `tools/import_kb_deck.py` (`6e41777`), `tools/import_fmx_deck.py` (`6e2847e`).
- **Deck CONTENT for a real talk** → create a fork (e.g., `ibrews/fmx-2026-spatial-storytelling`). Bake SECTIONS into the fork's `index.html`.
- **Editorial source-of-truth** can live in `~/knowledge/projects/<talk>/deck/`. The KB is the editing surface; the fork is the deliverable. Importer bridges them.
- **One-off /tmp HTML render** for review is fine. Before stage delivery, the talk's SECTIONS should be in its own fork.

**Do not** commit talk-specific SECTIONS.json, slide copy, or hero images to this main repo. Tools yes; talks no.

Canonical version of this rule: `~/knowledge/projects/spatial-deck/conventions.md`.

---

## FMX 2026 Session Learnings (added 2026-05-08)

### New layouts added to template
`placed` and `big` are now in the template (`index.html`). See the SECTIONS config comment for full docs.

**`placed` usage:**
```javascript
{ title:'Optional overlay title', subtitle:'Optional subtitle',
  layout:'placed', placedImages:[
    ['media/image.png', 5, 10, 60, 80],        // [src, left%, top%, w%, h%]
    ['media/video.mp4', 50, 20, 45, 60],        // .mp4 auto-detected as <video>
    ['media/img.jpg', 0, 0, 100, 100, 'center bottom']  // 6th param = object-position
  ], notes:'Speaker notes here' }
```

**`big` usage:**
```javascript
{ layout:'big', bigText:'The constraint\nis the design.', notes:'...' }
// Optional fields: title (eyebrow above), subtitle (italic below title),
//                  bigCaption (small italic below bigText)
```

### Video placeholder detection
When extracting from PPTX, any full-bleed image **under ~50KB** is almost certainly a Google Slides video thumbnail frame, not a real image. Before using it as `img:`, check `videos.json` for a local MP4 match. If none found, the slide needs a video file that wasn't embedded in the PPTX export.

### Git workflow for media-heavy repos
Committing large GIFs/videos to git history makes future pushes permanently slow (objects stay in pack even after deletion). Prevention:
1. Add to `.gitignore` **before** first `git add`: `*.gif` (over threshold), large video patterns
2. Use `tools/import_video_clip.py --max-mb 95` to fit GitHub's 100MB limit
3. If already committed large files: `git checkout --orphan fresh` → remove large files → commit → `git push --force origin HEAD:main`. Orphan branch has no history = small pack = reliable push.

### PPTX extraction script
`extract_pptx2.py` in the FMX fork is more robust than `tools/import_pptx.py` for media extraction (hash-based filenames, GIF detection, relationship traversal). Consider merging improvements upstream.
