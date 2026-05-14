# Spatial Deck — Claude Code Instructions

## What This Is

Spatial Deck is a single-file HTML presentation framework. Everything lives in `index.html` — CSS, JS, config, content. No build process, no npm, no bundler.

## Before You Start

**Read `HANDOFF_PROMPT.md`** in the repo root. It has the full architecture guide, conventions, and common tasks. This file gives you behavioral rules; the handoff prompt gives you technical context.

## Rules

### File Structure
- **Never split `index.html` into multiple files.** The single-file design is intentional.
- **Never add npm/webpack/vite/etc.** Zero build process is a core feature.
- The only external dependency is Three.js via CDN import map (optional, for constellation map).

### Editing SECTIONS
- The `SECTIONS` array near the top of the second `<script>` block drives all slide content.
- Changing SECTIONS automatically regenerates slides on page load.
- Use `\n` for line breaks in titles. Use `<br>` and `<br><br>` in taglines.
- Use `\n` for line breaks in bullets.
- `img: 'MEDIA_CYCLER'` requires a matching IIFE after the build loop.
- `img: 'path/to/file.jpg'` renders as a standard `<img>` tag (no media cycler, no pixelated reveal). Use `MEDIA_CYCLER` with a single-item array if you want the canvas-based reveal.
- `img: 'IFRAME:url'` embeds a responsive iframe.
- `img: ''` shows a gradient placeholder.
- Build loop priority: `IFRAME:` prefix → iframe, real path → `<img>` tag, `MEDIA_CYCLER` → media cycler mount, empty → gradient placeholder.

### Processing Annotation Dumps

When the user pastes a `# Annotations` block (exported from the deck's annotation panel, `A` key), it's a batch of edits to bake into source. Each entry looks like:

```
## N. <context> #<slide-num>
**Selector:** `<css-selector>`
**left:X%, top:Y% on slide #N**
**Note:** TEXT EDIT: "<truncated old>…" → "<truncated new>…"
**Full text:** <authoritative new text>
```

**Annotation type → action:**

| Type | How to recognize | Action |
|------|------------------|--------|
| **Text edit** | `Note: TEXT EDIT: ...` + `**Full text:**` line | Replace in source with **Full text** *verbatim*. The truncated `Note:` line is preview only — ignore it for the actual replacement. |
| **Transform** | `**TRANSFORM left:X%, top:Y% · translate(...)**` line | **Usually no-op.** Already in user's localStorage; applies at runtime. Only bake into source if user explicitly asks ("make this permanent for everyone"). |
| **Bare `Note:`** | Plain note, no `TEXT EDIT:` prefix | Ambiguous. Most common pattern: the note IS the new text content for the selected element (e.g., on an SVG `<text>` node, `Note: scope "locked"` means *set the node's text to that string*). Cross-reference the builder code. If still unclear, **ask** — don't guess. |
| **Settings block** | `## Current Settings (slide 0)` block at top of dump | If non-empty, bake values into the `D` defaults object near slide 0. Empty = no change. |

**Source-of-truth varies per annotation:** SECTIONS array (most common), layout builders, the BONUS object, the speaker-notes function, hardcoded SVG `<text>` strings inside builders. Read the selector and the surrounding builder code before editing.

**Workflow:**
1. Group edits by source location.
2. Apply with Edit/Write. The PostToolUse hook (`.claude/hooks/validate-js.sh`) parses all inline `<script>` blocks after each edit and blocks Claude if a token-level syntax error was introduced.
3. For layout-affecting changes (anything inside `placed`, `sg-collage`, or grid-based layouts), spawn a preview agent and screenshot before committing. Text-only edits in SECTIONS don't need preview.
4. One commit per annotation batch; message states the count and types.

**Gotchas (codified from prior incidents):**

1. **The Edit tool silently converts ASCII `'` to Unicode curly `'`/`'` in replacement text.** JavaScript doesn't accept curly quotes as string delimiters → syntax error. The hook catches it now, but to avoid the round-trip when editing JS strings: use a Python binary-replace, e.g. `data.replace('‘'.encode(), b"'").replace('’'.encode(), b"'")`. Preserve mid-string apostrophes that are valid U+2019 content (only fix the *delimiter* positions).
2. **Apostrophes inside JS single-quoted strings need `’`, not raw `'`.** A literal `'` mid-string terminates the string. Match the existing codebase style (`you’ve`, `we’re`).
3. **Ambiguous freeform notes get a question, not a guess.** "Let's get another image here" → ask which image and where.
4. **Index-based class assignments break under array inserts.** If a builder does `class="foo-${i%N}"` and those classes carry differential styles (grid spans, colors, animations), inserting in the middle of the array rotates all subsequent class assignments. Two safe patterns:
   - **Append at end** — only if visual order doesn't matter.
   - **Add a separate field** the builder renders with an explicit-position CSS class. (Pattern: `extraTile` config field → builder emits a tile with class `.sg-tile-fill-tr{grid-column:6;grid-row:1}` → slots without disturbing the auto-flow of other tiles.)
5. **TRANSFORM annotations are per-user localStorage state, not source state.** They auto-apply at runtime *for the annotating user*. Don't bake into source unless explicitly asked.

### Media
- Store in `media/` subdirectories. Use relative paths.
- Resize images to ≤2560px: `sips --resampleWidth 2560 file.jpg`
- Videos over 100MB: `ffmpeg -i in.mp4 -vf "scale=1280:-2" -crf 28 out.mp4`
- GIFs don't animate on canvas — convert to MP4 first.
- Max 5 images per project in media cyclers (keeps file sizes reasonable).

### Favicon — every fork gets its own
- **As soon as a fork has a real title (i.e. its `BONUS.title` / cover / `<title>` is set to something other than the template default), generate a favicon for it.** A talk-specific favicon shows up in browser tabs, GitHub Pages link previews, bookmarks, presenter notes windows, AirPlay receivers — anywhere the page is referenced.
- Generate `favicon.ico` (multi-resolution: 16, 32, 48), plus `favicon-16.png`, `favicon-32.png`, `favicon.svg` (if you have a vector source), and `apple-touch-icon.png` (180×180). Reference them with `<link rel="icon">` in `<head>`.
- **Quick path (macOS):** start from a 512×512 PNG of the talk's signature glyph or wordmark. `sips -s format png --resampleHeightWidth 32 32 src.png --out favicon-32.png`, then use ImageMagick or Pillow to write the `.ico` (sips can't make `.ico` directly): `python3 -c "from PIL import Image; im=Image.open('src.png'); im.save('favicon.ico', sizes=[(16,16),(32,32),(48,48)])"`.
- **Don't reuse the template favicon for a fork.** Even a fast color tweak of a base glyph beats showing the spatial-deck default in the talk's tab.
- If the deck has section accent colors (`--teal`, `--amber`, etc.), pick the one that best matches the talk's identity for the favicon background or stroke.

### Git & GitHub
- Commit after every meaningful change. Push frequently.
- GitHub file size limit: 100MB. Transcode large videos before committing.
- Use `.gitignore` for files that can't go to GitHub.
- Update `HANDOFF_PROMPT.md` after significant architectural changes.

### Code Style
- The file is densely packed (long lines, minimal whitespace). Match this style.
- Use `// ── Section Name ──` comment landmarks for major blocks.
- IIFEs `(function(){...})();` for isolated features.
- `slideSteps.set()` calls must be in `setTimeout(fn, 0)` (defers past declaration).
- Find slides by: `allSlides.find(s => s.querySelector?.('.case-title')?.textContent.includes('Title'))`

### Positioning
- The annotation system exports coordinates as `left:X%, top:Y%` percentages.
- When the user says "put X here" with coordinates, use `position:absolute` with those percentages.
- Layout grid zones: A1-A4 (top row), B1-B4 (middle), C1-C4 (bottom). A1=top-left, C4=bottom-right.

### Sound
- All audio uses Web Audio API (no external files).
- `playWhoosh()` = white-noise bandpass slide transition.
- `playBing()` = soft bell for media cycler transitions.
- Wrap audio in `try{}catch(e){}` — AudioContext requires user interaction first.
- `AudioContext` is monkey-patched — all instances auto-register for cleanup.
- `window._killAllSfx()` closes all active contexts (called by `goTo()` automatically).

### URL Params & Mobile
- Default = view mode (presentation mode on, edit chrome hidden).
- `?edit` = edit mode. `?view` = explicit view. `?landscape` = orientation prompt.
- Mobile auto-detected via `(pointer:coarse)`. 👁 button toggles chrome.
- Tap = advance. Swipe = navigate. Both respect `_arrowSubstep` toggle.

### Z-Ordering
- Move mode HUD: ▲▲/▲/▼/▼▼ buttons set `style.zIndex` on last-clicked element.
- Click any element in move mode to select it for z-ordering.

### Move Mode Auto-Save
- Dragging an element in move mode auto-saves the transform as an annotation (`type: 'move'`).
- These appear in the Annotations panel immediately — no manual save step needed.
- Map node clicks are suppressed in move mode to prevent accidental navigation.

### Keyframe Animation System
- The scrubber has a `◆ KF` button that captures last-moved element's transform at current scrub time.
- Diamond markers (◆) appear on the timeline for existing keyframes; `✕ KF` deletes them.
- Keyframes are persisted as annotations (`type: 'keyframe'`).
- Two or more keyframes on the same element automatically build a WAAPI animation.
- When adding custom animations, prefer the keyframe system over manual `slideSteps` for transform-based motion.

### Settings Slide (slide 0)
- Shows "Spatial Deck Creator v0.0.5" header.
- Counter shows "00" for settings, "01" for cover.
- URL hash `#0` and `#00` both go to settings. `#N` = slide N (0-indexed).
- Arrow substep toggle: On = step through animations, Off = skip to next slide.

## Common Patterns

```javascript
// Add a media cycler to a case study slide
(function(){
  const slide = allSlides.find(s => s.querySelector?.('.case-title')?.textContent.includes('Project Name'));
  if (!slide) return;
  buildMediaCycler(slide, [
    {type:'image', src:'media/project/01.jpg'},
    {type:'video', src:'media/project/demo.mp4', loop:true},
  ], {imageDuration:6000});
})();

// Add multi-step animation to a slide
setTimeout(()=>{
  slideSteps.set(mySlide, {
    current: 0,
    steps: [step1Fn, step2Fn, step3Fn]
  });
}, 0);

// Position an element at a specific location
element.style.cssText = 'position:absolute;left:45%;top:30%;z-index:2';
```
