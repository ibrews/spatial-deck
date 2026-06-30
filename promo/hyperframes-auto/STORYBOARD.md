# STORYBOARD — Spatial Deck Promo (Auto)

**Format:** 1920×1080
**Duration:** 17s (4 beats)
**Audio:** None (silent — VO deferred per skill scope note).
**VO direction:** n/a — on-screen typography carries the narrative.
**Style basis:** DESIGN.md (Spatial Deck's deep-indigo radial surface, 5-color neon palette, Space Grotesk + JetBrains Mono).

## Global direction

- Every beat sits on the shared radial indigo surface with a breathing rose aura and faint scanlines — continuity glue.
- Two techniques per beat minimum: (a) per-word kinetic typography and (b) a continuous ambient pulse attached to the master timeline.
- No iframes — any "deck" we show is a static panel styled to evoke the runtime. Captured hero screenshot is mounted as a floating device frame in beat 3.
- Color discipline: one dominant accent per beat (rose → purple → teal → rose-teal).

## Asset audit

| Asset                                                 | Type       | Beat(s) | Role                                                  |
| ----------------------------------------------------- | ---------- | ------- | ----------------------------------------------------- |
| capture/screenshots/scroll-000.png                    | Screenshot | Beat 3  | Floating deck "device" panel behind 18/4 stat         |
| capture/assets/fonts/V8mQoQDjQSkFtoMM3T6r8E7mF71Q...  | Font TTFs  | all     | Space Grotesk family — `@font-face` locally            |
| capture/assets/fonts/tDbY2o-flEEny0FZhsfKu5WU4zr3E... | Font TTFs  | all     | JetBrains Mono family — `@font-face` locally           |
| (none — SVG folder is empty)                          | —          | —       | SKIP (no SVG assets captured; compensate with CSS)    |

Utilization check: the one captured screenshot and both captured font families are used. No product SVGs were captured, so feature/chapter chips and the Claude Design bridge are CSS-only by necessity.

---

## BEAT 1 — "DECK IS DATA, CODE" (0.0 – 3.5s)

**Concept:** Cold open on the hero thesis. A dark indigo void breathes; the headline assembles word-by-word and the two emphasis words (`data.` and `code.`) ignite with a rose→purple→teal gradient wipe. A mono kicker above reads `SPATIAL DECK · PROMO`.

**Visual:** Radial indigo background fills 1920×1080. Rose aura pulses at 0.35→0.75 opacity on a 0.47s beat (128 BPM, sine.inOut, yoyo). Kicker types in first. Then the 8 headline words stagger-drop (y:40→0, opacity:0→1, 0.35s, stagger 0.1s, back.out(1.4)). On the gradient words, a 300% background-position sweep runs across the full beat.

**Mood:** "Terminal + aurora." Clean, confident, developer-native — not cinematic, not corporate.

**Assets:** Fonts only. No images.

**Animation choreography:**
- Kicker: DROPS in from y:-24, fades 0→1 over 0.45s.
- Title words: CASCADE in, staggered 0.1s.
- Gradient words: SHIMMER across their background 0→3.5s.
- Aura: BREATHES continuously (7 half-beats).

**Transition OUT:** CSS velocity-matched upward — `y:-80, blur:16px, opacity:0` over 0.4s power2.in on the whole scene.

**Depth layers:** BG: radial indigo. MG: aura (blend:screen). FG: kicker + headline.

**SFX:** (deferred)

---

## BEAT 2 — "HAND OFF FROM CLAUDE DESIGN" (3.5 – 8.0s)

**Concept:** The deck's input side. A terminal card types a single import command; three success lines appear; five color swatches (the 5 tokens) pop in with back-out bounce. Purple dominates.

**Visual:** Terminal card (black/60 + 1px white/14 border, 16px radius) centered, 900px wide. Mono line: `$ python tools/import_tokens.py claude-design.css`. Then three green `→/✓` output lines fade in sequentially. Below, five 54px rounded swatches (teal/purple/rose/amber/green) cascade in (scale:0.3, rotate:-12 → 1, 0) stagger 0.12s. Card itself does a 1.0→1.015 breath zoom across the beat.

**Mood:** Dev tooling demo. Tight, tactile, satisfying — like `pnpm install` finishing clean.

**Assets:** Fonts only. CSS + text.

**Animation:**
- Terminal card: DROPS in (y:50→0, 0.6s).
- Output lines: SLIDE in from x:-10, stagger 0.4s, starting at +0.9s.
- Swatches: POP in with back.out(1.6), stagger 0.12s, starting at +2.4s.
- Card: BREATH zoom 1.0→1.015 across scene.

**Transition OUT:** CSS blur-through — `blur:0→16px, opacity:1→0` over 0.35s power2.in.

**Depth layers:** BG: radial + breathing aura. MG: terminal card with shadow. FG: swatches.

---

## BEAT 3 — "18 SLIDES · 4 CHAPTERS" (8.0 – 12.5s)

**Concept:** Proof. A big stat lands (`18` and `4`) while the captured hero screenshot floats as a tilted device panel behind it, with four chapter chips snapping into a row below.

**Visual:** Screenshot of the hero page (`capture/screenshots/scroll-000.png`) mounted inside a rounded 12px panel with a rose 2px border, tilted at `rotationY:-8deg` in a 1200-perspective wrapper. Slow Ken Burns: scale 1.02→1.08, x -8→8 across the beat. Overlaid in the center: massive mono numbers "18" (teal) and "4" (amber) separated by `·`, 180px, with labels `SLIDES` / `CHAPTERS` under each. Below: 4 pill chips (CH 1 teal, CH 2 purple, CH 3 amber, CH 4 rose).

**Mood:** Confident receipt. The deck is real, and here's the shape of it.

**Assets:** `capture/screenshots/scroll-000.png` — the hero screenshot, used as the floating device.

**Animation:**
- Screenshot panel: FADES + TILTS in (opacity 0→1, rotationY -20→-8, 0.6s power2.out).
- Screenshot image: Ken Burns across full beat (scale+x).
- Stat numbers: COUNT UP (0→18 teal; 0→4 amber) over 0.9s starting +0.5s.
- Chapter chips: SNAP in (y:20→0, scale:0.75→1) stagger 0.18s starting at +2.2s.
- Chips: scale pulse 1.08 stagger yoyo starting at +3.5s.

**Transition OUT:** CSS zoom-through — `scale:1→1.2, blur:0→20px, opacity:1→0` over 0.35s power3.in.

**Depth layers:** BG: radial + aura. MG: tilted screenshot panel. FG: stat numbers + chips.

---

## BEAT 4 — "MERGE. DIFF. SHIP." + CTA (12.5 – 17.0s)

**Concept:** End card / thesis closer. Three mono verbs arrive like hammer strikes, then the logo gradient locks in and the URL badge glows on.

**Visual:** Three word-cards center-stacked horizontally: `Merge.` (rose), `Diff.` (teal), `Ship.` (purple) — 72px Space Grotesk bold, each in its own color. They slam in staggered (x:-60→0, opacity:0→1, 0.25s each, power3.out, stagger 0.22s). Half a second later, a large gradient `Spatial Deck` logo materializes below (96px, gradient rose→purple→teal, 300% background-position sweep across the rest of the beat). Underneath: mono tagline `ZERO BUILD · ONE FILE · YOURS TO FORK`. Then the URL badge `github.com/ibrews/spatial-deck` fades in with a teal glow halo.

**Mood:** Closer. Clear, confident, call-to-action without a button.

**Assets:** Fonts only.

**Animation:**
- Verb cards: SLAM in from x:-60, stagger 0.22s.
- Logo: SCALE in 1.05→1 + opacity 0→1 at +1.0s (0.55s power2.out).
- Logo gradient: sweep 0%→300% background-position from +1.0 to beat end.
- Tagline: FADES up +1.4s.
- URL badge: FADES in +1.8s, glow pulse yoyo 3x through end.
- Aura: BREATHES.

**Transition OUT:** Hard end (scene fades to black via the beat ending — no exit animation needed).

**Depth layers:** BG: radial + aura. MG: verb row. FG: logo + URL.

---

## Production architecture

```
promo/hyperframes-auto/
├── hyperframes.json
├── DESIGN.md
├── SCRIPT.md
├── STORYBOARD.md
├── index.html                        orchestrator — mounts the 4 beats on one timeline
├── capture/                          from Step 1
│   ├── screenshots/scroll-000.png
│   ├── assets/fonts/*.ttf
│   └── extracted/*
└── compositions/
    ├── beat-1-hook.html
    ├── beat-2-handoff.html
    ├── beat-3-scale.html
    └── beat-4-closer.html
```
