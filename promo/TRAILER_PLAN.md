# Spatial Deck Trailer — Production Plan

**Goal:** a trailer built on **real product footage** that SELLS — targeted at
the Capafy marketplace audience (e-commerce/marketing buyers, non-developers).
No git, no terminal, no "deck as code" in the buyer-facing cut. (The existing
`spatial-deck-promo.mp4` is a 17s dev-flavored typography teaser — keep for
GitHub/social; `footage/draft-cut.mp4` was a mechanics draft, superseded.)

**Status: v1 SHIPPED — `trailer-capafy.mp4` (33.7s, silent).** Structure:
beige "Q3 Strategy Update" cold open → "Every deck looks the same." →
**Harvard keynote real footage** (cover + transitions) → "Meet Spatial Deck"
(real stages: Harvard · FMX · NXT BLD) → media-rich case slides (Body of
Mine) → "Start with what you already have" (notes · PDF · old PowerPoint) →
"Get back one file" (double-click · live link · PDF) → constellation map with
the pixel avatar walking the ring → "Works offline. No lock-in. Yours
forever." → CTA: "Spatial Deck Maker on Capafy" + repo URL.

**Remaining for v2:** music bed (the #1 missing piece), optional VO, a
9:16/1:1 crop for social, and possibly re-capturing select Harvard moments at
slower dwell for smoother holds. Sources in `trailer-src/` (card template +
assemble.py); footage regenerates with
`python3 tools/export_video.py --html ~/harvardxr-keynote/index.html --keep-webm …`.

## Beat structure

| # | Time | Beat | Footage | Status |
|---|------|------|---------|--------|
| 1 | 0–5s | **Pain** — beige bullet-point PowerPoint, "Your work is spatial. Your slides aren't." | Typography / mock slide | ❌ to build (HyperFrames) |
| 2 | 5–20s | **The reveal** — cover, media-cycler pixel reveal, case slides, transitions | `footage/hero.webm` ✅ | ✅ captured |
| 3 | 20–32s | **The workflow** — Google Slides draft → `sync_gslides.py pull` terminal → deck updates → move-mode drag → annotation export | `footage/movemode.webm` ✅ (move mode); terminal + gslides side ❌ | partial |
| 4 | 32–42s | **Constellation map + share story** — map animation; "One file. USB stick. Live link. And yes — a PDF button." (show `export_pdf.py` fidelity report output) | `footage/map.webm` ✅; export terminal ❌ | partial |
| 5 | 42–50s | **Kicker** — "Spatial Deck. Free. Open source. One file." → repo URL | `footage/../endcard` (draft version exists in cut) | draft ✅ |

## Capture infrastructure (reproducible)

- `footage/capture.mjs` — playwright-core + system Chrome (`channel:'chrome'`),
  records 1280×720 webm of scripted deck interaction. `NODE_PATH=<dir with
  playwright-core> node capture.mjs`. Add scenes by copying a `record()` block.
- Terminal beats: record with `asciinema`/screen capture, or fake cleanly in
  HyperFrames (the existing promo's beat 2 already has the terminal-card style —
  reuse it with the real `sync_gslides.py pull` / `export_pdf.py` output text).
- Higher-fidelity hero footage: re-capture against the **Harvard keynote deck**
  (`ibrews.github.io/harvardxr-keynote`) — richer media than the sample deck.
  Same script, different URL. Confirm rights/content sensitivities first.

## Remaining work

1. Beat 1 + polished beat 5 in HyperFrames (reuse `hyperframes-auto/` design system).
2. Terminal overlay shots for beats 3–4 (real tool output, styled card).
3. Music + (optional) VO — script spine exists at `hyperframes-auto/SCRIPT.md`,
   extend to the 5-beat structure.
4. Final cut at 1920×1080; export 16:9 master + 1:1 and 9:16 crops for social.
5. Replace the README hero GIF if the Harvard-deck recapture looks better.

## Draft cut (what exists today)

`footage/draft-cut.mp4` — 29s, silent: hero footage (14s) ⤬ move mode (7s) ⤬
constellation map (5.5s) ⤬ end card (4.5s), 0.5s crossfades. Assembled with
ffmpeg xfade; end card rendered from `footage/endcard.html` via
`tools/capture_slides.py`'s Chrome layer.
