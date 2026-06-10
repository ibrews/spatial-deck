# Spatial Deck Trailer — Production Plan

**Goal:** a trailer built on **real product footage** that SELLS — targeted at
the Capafy marketplace audience (e-commerce/marketing buyers, non-developers).
No git, no terminal, no "deck as code" in the buyer-facing cut. (The existing
`spatial-deck-promo.mp4` is a 17s dev-flavored typography teaser — keep for
GitHub/social; `footage/draft-cut.mp4` was a mechanics draft, superseded.)

**Status: v2 SHIPPED — `trailer-capafy.mp4` (33.1s, with soundtrack).**
Structure: beige "Q3 Strategy Update" cold open → "Every deck looks the
same." → **Harvard keynote real footage** → "Meet Spatial Deck" (real stages:
Harvard · FMX · NXT BLD) → media-rich cases (Body of Mine pixel-reveal,
Vodafone) → "Start with what you already have" → "Get back one file" →
constellation map → "Works offline. No lock-in. Yours forever." → CTA
"Spatial Deck Maker on Capafy" + repo URL.

**v2 design decisions:**
- **Narrator cards are LIGHT** (ink-on-paper, `card-light.html.tmpl`); real
  deck footage stays dark and carries a "● REAL TALK FOOTAGE · HARVARD XR
  KEYNOTE" pill (`footage-chip.png`, PIL-rendered) — sell-voice vs product
  footage is unmistakable.
- **Soundtrack is synthesized** (`make_music.py`, numpy → WAV): dull 55Hz
  drone + clock ticks under the boring open, whoosh at the Spatial Deck
  reveal, then a building 116 BPM groove (kick → hats → bass → arp → pad,
  Am–F–C–G), thinning under the constellation map, resolving with the deck's
  bell register over the CTA. Boring = flat & quiet; Spatial Deck = alive.
- Window B avoids the Four Seasons slide (its video recorded as a black box —
  media didn't load in headless capture; re-record or pick around such slides).

**Remaining for v3 (optional):** VO, a real (licensed) music track if the
synth bed isn't enough, 9:16/1:1 social crops, re-capture at slower dwell for
longer holds. Footage regenerates with
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
