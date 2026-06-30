# Design System

## Overview

Spatial Deck's promo page is a dark, technical-poetic landing for a single-file HTML presentation framework. The visual identity leans "terminal meets aurora" — deep near-black backgrounds washed with a radial purple-to-indigo glow, accented by a vibrant five-color neon palette (teal, purple, amber, rose, green). Typography is split between a geometric sans (Space Grotesk) for headlines and a crisp monospace (JetBrains Mono) for labels, commands, and kickers. The feel is confident, developer-native, and just playful enough to signal that the deck is alive.

## Colors

- **Primary Surface 1**: `#0B0820` — deep indigo/near-black page background (radial gradient inner stop).
- **Primary Surface 2**: `#060810` — outer background fill for the gradient.
- **Primary Content**: `#F0F4FF` — soft off-white for body text and headlines.
- **Accent Rose**: `#F43F5E` — primary emphasis, auras, CTA glows, "punctuation" color.
- **Accent Teal**: `#00D4FF` — secondary emphasis, URLs, CTA border.
- **Accent Purple**: `#A78BFA` — labels, Claude Design bridge side.
- **Accent Amber**: `#F59E0B` — chapter 3 / warning tone.
- **Accent Green**: `#22C55E` — terminal success output.
- **Traffic Lights**: `#FF5F57` / `#FEBC2E` / `#28C840` — used on faux terminal chrome.

## Typography

- **Sans-Serif (Headings & Body)**: Space Grotesk, weights 400/500/600/700. Tight tracking (~-0.025em), large hero sizes (72–104px on a 1080 stage).
- **Monospace (Labels, Kickers, Commands, URLs)**: JetBrains Mono, weights 400/500/700. Wide letter-spacing (2–6px), frequent ALL CAPS for kickers and badges.
- **Hierarchy**: Hero title ~104px · Slide titles 64–72px · Body/description 22–26px · Mono kickers/labels 14–18px with 4–6px tracking.

## Elevation

Depth comes from layered light, not drop shadows. A radial indigo-to-black gradient sits under every scene; a low-opacity rose "aura" radial blends on top via `mix-blend-mode: screen` and breathes continuously. A faint 2-3px horizontal scanline overlay adds a subtle CRT texture. UI surfaces (terminal cards, chip pills, end-card URL) use semi-transparent blacks (`rgba(0,0,0,0.6–0.75)`) with 1–2px color-tinted borders and soft outer shadows (`0 24px 80px rgba(0,0,0,0.6)`). No hard drop shadows on text.

## Components

- **Terminal Card**: Black translucent panel, traffic-light dots top-left, mono prompt lines with colored `$`, command, arg tokens; green success output lines animated in sequentially.
- **Color Swatch Row**: Five ~54px rounded squares (teal/purple/rose/amber/green) in a line, used as "5 tokens synced" proof.
- **Chapter Chips**: Pill-shaped 2px-bordered monospace tags in teal/purple/amber/rose variants (e.g. "CH 1 · DEFINE THE SPATIAL").
- **Feature Grid**: Three-up cards per side (Claude Design: TOKENS/STYLES/HANDOFF vs Spatial Deck: LIVING DECK/ZERO BUILD/YOURS TO FORK) joined by a large rose arrow.
- **End-Card URL Badge**: Teal mono URL inside a 2px teal-outlined rounded rectangle with a glow halo.
- **Kicker Label**: All-caps mono tag above titles, half-transparent ink, wide letter-spacing.

## Do's and Don'ts

### Do's

- Keep every scene on the deep indigo radial background — consistency is the brand.
- Use the 5-color accent palette as punctuation, not fill — one or two accents per beat.
- Pair mono kickers with sans headlines — the contrast is the voice.
- Animate the aura continuously (breath) so no frame is ever fully static.
- Use gradient text (`linear-gradient(90deg, rose, purple, teal)` clipped to text) for "hero" words — it's the signature look.

### Don'ts

- Do not use full-screen dark linear gradients — H.264 banding; stick to the radial.
- Do not put bright solid color backgrounds — palette is accent only, never surface.
- Do not stack two GSAP transforms on the same element (e.g. y + scale) — animate a child wrapper for the second transform.
- Do not use Google Fonts at runtime — fonts are Space Grotesk + JetBrains Mono loaded via `@font-face` from the repo's fonts (Google Fonts CDN is acceptable only as a fallback).
- Do not add `repeat: -1` or `Math.random()` — renders must be deterministic.
