# Import & Export Tools

The `tools/` directory contains Python scripts that bridge external content formats into Spatial Deck's SECTIONS format. Most use a local Ollama LLM fleet for normalization — see the [fleet client](#fleet-client) section for setup.

---

## Quick Reference

| Script | What it does |
|--------|-------------|
| `import_pptx.py` | PowerPoint → SECTIONS chapter JSON |
| `import_md.py` | Markdown → SECTIONS chapter JSON |
| `import_html.py` | HTML deck → SECTIONS chapter JSON |
| `import_pdf.py` | PDF → SECTIONS chapter JSON |
| `import_tokens.py` | Design tokens (CSS/JSON/prose) → `:root{}` patch |
| `sync_gslides.py` | Ongoing Google Slides sync |
| `merge_sections.py` | Splice imported chapter into SECTIONS |
| `import_video_clip.py` | YouTube/local video download + trim + encode |
| `export_md.py` | SECTIONS → Markdown |
| `export_html.py` | SECTIONS → static HTML outline |
| `export_pptx.py` | SECTIONS → `.pptx` |
| `lint_deck.py` | QA report on slide content |
| `estimate_timing.py` | Per-slide timing table + note drafting |
| `gen_alt_text.py` | AI-generated alt text for all images |
| `extract_palette.py` | Reference image → CSS color tokens |
| `diff_decks.py` | Diff two SECTIONS snapshots |
| `merge_decks.py` | Merge N decks, detect conflicts |
| `peer_review.py` | Two-model fleet critique of slides |

---

## Common Workflow: Importing Any Source

All importers output a JSON file. You then splice it into `index.html` with `merge_sections.py`.

```bash
# 1. Import (any format)
python3 tools/import_pptx.py my-deck.pptx

# 2. Preview the output
cat tools/imported-my-deck-HASH.json | python3 -m json.tool | head -50

# 3. Splice into SECTIONS
python3 tools/merge_sections.py tools/imported-my-deck-HASH.json

# 4. Open index.html and review
open index.html
```

`merge_sections.py` is idempotent — running it again replaces the previous import block (between `// ── IMPORTED START ──` and `// ── IMPORTED END ──` sentinels).

---

## PowerPoint Import

```bash
pip3 install python-pptx  # one-time
python3 tools/import_pptx.py path/to/deck.pptx
python3 tools/merge_sections.py tools/imported-<deck>-<hash>.json
```

What it does:
- Extracts titles, body text, speaker notes, and embedded images using `python-pptx`
- Routes each slide's body copy through `llama3.1:8b@Sam` to tighten bullets (2–4 per slide)
- Saves images to `media/import-<deck>-<hash>/`
- Use `--no-llm` to get raw extracted text without normalization

---

## Markdown Import

```bash
python3 tools/import_md.py path/to/talk.md
python3 tools/import_md.py path/to/talk.md --tighten   # LLM bullet cleanup
python3 tools/merge_sections.py tools/imported-<deck>-<hash>.json
```

Markdown conventions:
- `#` — deck title (next paragraph becomes tagline)
- `##` — slide title
- First paragraph after `##` — subtitle
- `-` / `*` / `+` lines — bullets
- `![alt](media/x.png)` — image (alt becomes subtitle if not set)
- `>` — speaker notes

---

## HTML Import (Claude Design Handoff)

```bash
pip3 install beautifulsoup4  # one-time
python3 tools/import_html.py path/to/deck.html
python3 tools/import_html.py path/to/deck.html --no-llm   # raw only
python3 tools/merge_sections.py tools/imported-<deck>-<hash>.json
```

Works with Claude Design exports, Framer exports, or hand-written HTML. Splits on `<section>`, `<article>`, `.slide`, or `[data-slide]` markers; falls back to heading-based splitting. Inline `data:` images are decoded and saved to disk.

---

## PDF Import

```bash
pip3 install pdfplumber  # one-time
python3 tools/import_pdf.py path/to/deck.pdf
python3 tools/merge_sections.py tools/imported-<deck>-<hash>.json
```

Handles two-column layouts correctly (InDesign/Keynote exports). Raster images are extracted when embedded. Scanned PDFs won't have extractable images.

---

## Design Token Import

```bash
python3 tools/import_tokens.py path/to/tokens.css
python3 tools/import_tokens.py path/to/tokens.json
python3 tools/import_tokens.py --dry-run path/to/tokens.css  # preview only
```

Accepts CSS `:root{}` exports, JSON palette objects, or a text file with prose color descriptions. Normalizes to Spatial Deck's token schema (`--bg`, `--teal`, `--purple`, `--amber`, `--rose`, `--text`, `--dim`) and patches the `:root{}` block in `index.html` in place.

---

## Google Slides Sync (Ongoing)

For decks that are still being edited in Google Slides, `sync_gslides.py` maintains a diff-aware sync rather than a one-shot import.

```bash
# First time — initialize from a shared Google Slides URL
python3 tools/sync_gslides.py init "https://docs.google.com/presentation/d/<ID>/edit"

# Pull latest changes
python3 tools/sync_gslides.py pull
python3 tools/sync_gslides.py pull --dry-run   # diff only, no changes

# Mark slide status
python3 tools/sync_gslides.py mark p13 generated  # done
python3 tools/sync_gslides.py mark p16 locked --note "hand-tuned, don't revert"

# See what needs work
python3 tools/sync_gslides.py status --pending
```

Slide states:
- `pending` — needs work (new, or content changed since last pull)
- `generated` — implemented in SECTIONS; auto-reverts to `pending` if source changes
- `locked` — won't auto-revert (diff still reported)

Requires the Google Slides doc to be shared "anyone with the link can view." For private docs, download the PPTX manually and pass `--no-download`.

---

## Video Clip Importer

Pull YouTube clips or trim local video files:

```bash
# YouTube — download + trim in one shot
python3 tools/import_video_clip.py "https://youtu.be/VIDEO_ID" \
    --start 1:23 --end 1:45 --out media/project/clip.mp4

# Local file — trim only
python3 tools/import_video_clip.py ~/Downloads/video.mp4 \
    --start 0:30 --duration 8 --out media/project/intro.mp4

# Two-phase — download first for scrubbing in QuickTime, then trim
python3 tools/import_video_clip.py "https://youtu.be/ID" \
    --download-only --out work/raw.mp4
open work/raw.mp4   # find exact timestamps
python3 tools/import_video_clip.py work/raw.mp4 \
    --start 1:23 --end 1:45 --out media/project/clip.mp4

# Fit GitHub's 100MB limit
python3 tools/import_video_clip.py SOURCE --start 0:00 --end 5:00 \
    --max-mb 95 --out media/long.mp4
```

| Flag | Default | Description |
|------|---------|-------------|
| `--quality` | `high` (CRF 21, 1280px) | Encode quality |
| `--max-mb` | `0` (disabled) | Auto-shrink ladder to fit a size budget |
| `--audio` | keep | Use `mute` to drop audio |
| `--download-only` | off | Download without trimming/encoding |

Requires `yt-dlp` and `ffmpeg` on PATH.

---

## Export Tools

### Pixel-faithful exports (PDF, visual PPTX, PNGs)

The deck itself is the renderer: headless Chrome drives the built-in `?print` / `?shot=N` modes, so layouts, themes, placed media, and move-mode tweaks export exactly as presented. Requires Google Chrome (or `CHROME_BIN`); no Python deps on macOS.

```bash
python3 tools/export_pdf.py  --out talk.pdf             # one 16:9 page per slide
python3 tools/export_pdf.py  --print-css --out talk.pdf # vector-text alternative
python3 tools/export_pptx.py --visual --out talk.pptx   # full-bleed slide images + notes
python3 tools/capture_slides.py --out-dir shots/        # just the per-slide PNGs
```

What degrades (and is listed in the post-export **fidelity report**): media cyclers freeze on their first item, iframes become a placeholder panel showing the URL, videos freeze on an early frame, the constellation map captures as-rendered. Hidden slides are excluded, matching the live deck.

You can also just open `index.html?print` in a browser and File → Print.

### Structural exports (editable, content-only)

Round-trip your deck's *content* to other formats — presentation is approximated:

```bash
python3 tools/export_md.py --out outline.md            # full deck → markdown
python3 tools/export_md.py --chapter 1 --out ch1.md    # single chapter
python3 tools/export_html.py --out deck-outline.html   # static no-JS HTML
python3 tools/export_pptx.py --out deck.pptx           # editable two-column .pptx
```

`export_md.py` ↔ `import_md.py` is a verified 0-diff round-trip (uses `<!-- spatial-deck ... -->` metadata blocks to preserve year, accent, short, tags, multi-line titles).

Structural exporters print a fidelity report too: advanced layouts (`big`/`placed`/grid) collapse to the two-column approximation, cyclers/iframes/videos are placeholders or dropped — the report tells you exactly which slides are affected.

---

## Slide Linter

```bash
python3 tools/lint_deck.py
python3 tools/lint_deck.py --json
python3 tools/lint_deck.py --llm --limit 10   # semantic review via local LLM
```

Never mutates. Reports: title/bullet length, duplicate titles, empty taglines, orphan numbers (digits in body but not title). `--llm` adds a semantic pass for vague or redundant bullets.

---

## Speaker-Note Timing

```bash
python3 tools/estimate_timing.py --target 20          # 20-minute talk
python3 tools/estimate_timing.py --generate > patch.json  # draft notes for empty slides
```

Outputs per-slide duration table with total and a traffic-light indicator vs. `--target`. `--generate` drafts notes via `llama3.1:8b@Sam` for slides with no notes (outputs JSON patch, never mutates `index.html`).

---

## Alt-Text Generator

```bash
python3 tools/gen_alt_text.py --limit 5     # smoke-test on 5 images
python3 tools/gen_alt_text.py               # full deck
python3 tools/gen_alt_text.py --scan-media  # list orphaned media files
```

Uses `gemma3:12b@Lenny` (vision model) to draft 10–20 word alt text for each local image. Outputs JSON patch. SVG files are skipped.

---

## Palette from Reference Image

```bash
python3 tools/extract_palette.py photo.jpg
python3 tools/extract_palette.py photo.jpg --vibe  # add mood phrase comment
python3 tools/import_tokens.py tools/palette-photo.css  # apply to index.html
```

K-means++ on the downsampled image → maps to Spatial Deck CSS tokens. Synthesizes accent colors for missing hues to keep the palette coherent.

---

## Deck Diff

```bash
python3 tools/diff_decks.py old.html new.html
python3 tools/diff_decks.py index.html tools/imported-foo.json --json
```

Field-level diff of two SECTIONS snapshots. Useful before re-merging or after pulling template updates.

---

## Multi-Deck Merge

```bash
python3 tools/merge_decks.py index.html other.html fork.html --out merged.json
python3 tools/merge_decks.py a.html b.html --drop-duplicates --prefix-year
```

Concatenates SECTIONS from multiple sources, detects year collisions and near-duplicate cases, writes a `.conflicts.md` report.

---

## Peer Review

```bash
python3 tools/peer_review.py index.html
python3 tools/peer_review.py tools/imported-foo.json --chapter 0
```

Two models (llama3.1:8b@Sam for narrative clarity, qwen2.5-coder:14b@Archie for structural consistency) each critique the deck independently. Near-duplicate flags are merged; issues both models flag get 🔴, solo flags get 🟡.

---

## Fleet Client

Most tools call `tools/fleet_client.py` internally. Edit the `ENDPOINTS` table at the top of that file to match your Ollama endpoints.

Default fleet assignments:

| Task | Model | Machine | Fallback |
|------|-------|---------|---------|
| Normalization (PPTX/PDF/tokens) | `llama3.1:8b` | Sam | Archie / MBP `qwen3-coder:30b` |
| Bullet tightening | `llama3.1:8b` | Sam | `qwen3:8b` @ MBP |
| HTML slide normalization | `qwen2.5-coder:14b` | Archie | `qwen3-coder:30b` @ MBP |
| Alt-text + palette vibe | `gemma3:12b` (vision) | Lenny | `gemma3:27b` |

If you don't have an Ollama fleet, pass `--no-llm` to any importer to get raw extracted text without LLM normalization. The tools still work — you just get less-polished output.
