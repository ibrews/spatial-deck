# Claude Design vs. Spatial Deck — Positioning Research

**Date:** 2026-04-17
**Author:** Research pass for Alex Coulombe / Agile Lens
**Subject:** How should Spatial Deck be positioned now that Anthropic has launched Claude Design?

---

## 1. What is Claude Design?

Claude Design is an Anthropic Labs product announced **April 17, 2026**, powered by **Claude Opus 4.7**. It is a conversational visual-creation canvas — the closest comparison is "Figma + Canva + Gamma, all driven by Claude." Users describe what they want; Claude produces an initial design on a virtual canvas; users refine it through chat, inline comments, direct edits, or purpose-built sliders for color/spacing/layout.

It is currently rolling out in **research preview to Claude Pro, Max, Team, and Enterprise** subscribers. It is **off by default for Enterprise** (admins must enable it in Organization settings).

### Core features

- **Conversational canvas.** A central virtual canvas shows the artifact in progress. Refinement happens through chat, inline comments, direct text edits, and Claude-generated sliders (e.g. spacing, color, layout).
- **Design-system awareness.** Claude Design can read a company's codebase and design files to apply an existing brand/design system automatically — colors, typography, components.
- **Multi-modal input.** Text prompts, image/document uploads (DOCX, PPTX, XLSX), codebase references, web capture.
- **Collaboration.** Org-scoped sharing with view-only or edit access.
- **Code-powered prototypes.** Supports "voice, video, shaders, 3D and built-in AI" inside artifacts — not just static slides.
- **Claude Code handoff.** Produces handoff bundles compatible with Claude Code for development follow-through.

### Export formats

- PDF
- PPTX
- Organization-scoped URL
- **Standalone HTML file**
- Canva (send-to)
- Saved folder/bundle

### Target audience

Founders, PMs, marketers, and designers who need quick pitch decks, one-pagers, prototypes, landing pages, and marketing collateral. Positioned explicitly as a **Figma/Canva competitor** (Figma's stock reportedly dropped on the announcement).

### Limitations (inferred from coverage and product page)

- **Research preview** — feature set and stability will churn.
- **Subscription-gated** — requires a paid Claude plan; usage counts against subscription limits with paid overages.
- **Opinionated output.** Claude generates "polished" designs that conform to the provided design system; bespoke, performance-weird, or idiosyncratic work (custom canvas animations, WAAPI choreography, Web Audio, live-coded behaviors) is not the target.
- **Cloud-only.** No `file://` or USB-stick-from-a-podium story. No offline mode comparable to Spatial Deck's "copy the folder and go."
- **Not a presenter tool.** No speaker-notes popup, no pacing/timing estimator, no presenter-mode shortcut, no on-stage annotation layer. It produces the deck; it doesn't run the deck.
- **Limited runtime interactivity once exported.** PPTX/PDF export collapses richer behavior. Exported standalone HTML retains code-prototype behavior but is not a live-editable presenter surface.

### Sources

- [Anthropic — Introducing Claude Design by Anthropic Labs](https://www.anthropic.com/news/claude-design-anthropic-labs)
- [TechCrunch — Anthropic launches Claude Design](https://techcrunch.com/2026/04/17/anthropic-launches-claude-design-a-new-product-for-creating-quick-visuals/)
- [VentureBeat — Anthropic just launched Claude Design](https://venturebeat.com/technology/anthropic-just-launched-claude-design-an-ai-tool-that-turns-prompts-into-prototypes-and-challenges-figma)
- [The New Stack — Figma and Canva rival built on Claude](https://thenewstack.io/anthropic-claude-design-launch/)
- [Gizmodo — Figma stock nosedives on announcement](https://gizmodo.com/anthropic-launches-claude-design-figma-stock-immediately-nosedives-2000748071)
- [The Register — Because who needs designers?](https://www.theregister.com/2026/04/17/anthropic_debuts_claude_design/)
- [Glen Rhodes — Prototype and artifact generator powered by Opus 4.7](https://glenrhodes.com/anthropic-launches-claude-design-a-prototype-and-artifact-generator-powered-by-opus-4-7-vision-model/)
- [MacRumors — Claude Design for prototypes, pitch decks, and mockups](https://www.macrumors.com/2026/04/17/anthropic-claude-design/)
- [Engadget — Anthropic now has a design assistant too](https://www.engadget.com/ai/anthropic-now-has-a-design-assistant-too-150000903.html)

---

## 2. Spatial Deck — current strengths (for contrast)

Spatial Deck is a **single-file HTML** presentation framework. It is already AI-friendly by design (drop the file into a context window, edit the `SECTIONS` array, ship). Its actual differentiators versus a Gamma/Canva/Claude-Design-style generator are operational and runtime-side, not "generate me a deck" side:

- **Single file, zero build, works from `file://` and USB.** Runs from a Harvard podium without a network.
- **Presenter infrastructure.** `N` opens a BroadcastChannel-synced presenter popup with notes, next-slide preview, elapsed time, estimated remaining time, and pacing indicator. Duration estimator built from notes heuristics.
- **Live annotation + coordinate export.** Annotation mode, 4×3 layout grid (A1–C4 zones), clipboard-copied `left:X%, top:Y%` snippets. This is a **handoff protocol** for AI collaborators — exact coordinates, not vague descriptions.
- **Move mode with auto-saved transforms.** Drag/scale/rotate any element, changes persist as annotations (`type:'move'`), undo/redo stack (50 deep).
- **Keyframe animation system.** `◆ KF` button captures element transforms at scrub-time; 2+ keyframes on an element auto-build a WAAPI animation. Persisted as annotations (`type:'keyframe'`).
- **Media cycler with pixelated reveal.** Canvas-based image/video gallery with a distinctive de-pixelation reveal, per-item `flipH`/`loop`, auto-advance, `Shift+Arrow` control.
- **Three.js constellation map.** Auto-generated from the SECTIONS array; clickable nodes jump to lessons. Import-map based; swappable to local file for offline.
- **Web Audio SFX.** `playWhoosh`, `playBing`, automatic `AudioContext` cleanup on slide change via monkey-patched constructor.
- **URL param modes.** `?edit` / `?view` / `?landscape`, hash-based slide deep links.
- **Mobile-native.** Auto-detect, tap-to-advance, swipe nav, 👁 chrome toggle.
- **Theme editor + auto-save snapshots.** Live color/font/scale controls, 60-second rolling snapshots, one-click restore.
- **Iframe embeds.** `IFRAME:` prefix for YouTube, Vimeo, pixel-streamed UE5, Sketchfab — with `allow="autoplay;fullscreen;xr-spatial-tracking"` already set.
- **Git-native.** Version-controllable, diffable, forkable-per-talk.

The honest framing: Spatial Deck is a **runtime/authoring IDE for presenters**, not a generative design tool. Claude Design is a **generative design tool that happens to output decks**. They are not actually competing in the same lane.

---

## 3. Option A — Position Spatial Deck as a handoff companion to Claude Design

In this framing, Claude Design is upstream (generate the polished skeleton), Spatial Deck is downstream (make it performant, presentable on-stage, and AI-iterable up to showtime).

### What would matter

1. **Claude Design HTML import.** Claude Design exports standalone HTML. Build a one-click "Import from Claude Design" flow in the Settings slide: paste an HTML file or URL, extract slide-like regions (headings + media + body), and synthesize a `SECTIONS` entry per page. Lossy on layout, but the whole Spatial Deck point is that the `SECTIONS` array is authoritative — you want the *content*, not the pixel-perfect layout.
2. **PPTX → SECTIONS importer.** Use the `anthropic-skills:pptx` skill (already available in this environment) or a lightweight JS parser to slurp a PPTX export into `SECTIONS`. This is where most of the Claude Design → Spatial Deck handoff will actually happen because PPTX is the lowest-common-denominator export.
3. **Design-system ingestion parity.** Claude Design reads a company's tokens. Spatial Deck's theme editor already exposes `--bg`, `--teal`, `--purple`, `--amber`, `--rose`, font, scales. Add a "paste design tokens JSON" input that maps common token shapes (`colors.primary`, `typography.heading`) into CSS custom props. Then Claude Design output and Spatial Deck output look identical at the brand level.
4. **Claude Code handoff compatibility.** Claude Design produces handoff bundles for Claude Code. Ship a documented schema in `HANDOFF_PROMPT.md` that says: "If you received a Claude Design handoff bundle, here's how to translate it into a SECTIONS entry." This is almost free — the handoff prompt already exists.
5. **Export *back* to Claude Design's formats.** Spatial Deck already has offline export. Add PPTX export (one slide per SECTION via a canvas snapshot + text layer) and PDF export (print to PDF with a print stylesheet). This closes the loop: you can round-trip.
6. **Pitch: "the live presenter's Claude Design companion."** Market Spatial Deck not as "another deck tool" but as the thing you use *after* Claude Design when you actually have to walk on stage, tweak at the last minute, read notes, annotate live, and run from a flash drive in an auditorium with bad Wi-Fi.

### Why this works

- Zero feature-race anxiety. You are not trying to out-generate Opus 4.7.
- Claude Design's weakest link (presenter mode, offline, live authoring on-stage) is Spatial Deck's strongest link.
- Importers are small, well-scoped work — days, not months.

### Risk

- You are hitched to another company's product roadmap. If Anthropic adds speaker notes + presenter popup + offline export in v2 (they will, eventually), the moat narrows.
- Discoverability: "companion tool for Claude Design" is a narrower pitch than Claude Design itself and depends on Anthropic's marketing surface.

---

## 4. Option B — Make Spatial Deck feature-rich enough to stand alone

In this framing, Spatial Deck competes on its own merits as a **code-native, performer-oriented deck framework** — the opposite end of the market from Claude Design's Canva-replacement positioning.

### Gaps that would need to close

1. **Generative authoring flow.** Today you still write `SECTIONS` entries by hand (or prompt Claude to do it). A first-run wizard — "describe your talk" → generated SECTIONS skeleton → drop-in media placeholders — would close the cold-start gap Claude Design nails.
2. **Media generation in-app.** `nano-banana` / `pixellab` MCPs are available in the broader environment; a "Generate a placeholder image for this slide" button that calls out to an image provider would eliminate the "I need to leave the tool to get assets" friction. Cache generated media locally to preserve offline-first.
3. **Slide layouts beyond lesson/case/bonus/map/close.** Claude Design's canvas is layout-free. Spatial Deck has five slide types and they all smell a bit Harvard-XR-keynote-ish. Add: quote slide, timeline slide, comparison/split slide, full-bleed media slide, section-break slide. Templatize them.
4. **Collaboration.** Claude Design has org-scoped sharing with edit permissions. Spatial Deck is git-native, which is great for engineers and terrible for everyone else. Offer an optional "publish to Spatial Deck Cloud" (or Netlify-style zero-config drop) with view/edit links — without breaking the file://-offline story.
5. **Design system import parity.** Same as Option A #3 — this matters either way.
6. **Richer text/layout tools.** Double-click-to-edit exists; a live rich-text toolbar (bold/italic/link/color) would raise the ceiling for non-technical users.
7. **Export completeness.** PPTX, PDF, shareable URL, and single-HTML-bundle exports — at parity with Claude Design.
8. **Thumbnail/preview generation.** Claude Design's canvas gives visual feedback on every slide; Spatial Deck's slide grid does too, but thumbnails are live-rendered. A faster static-thumbnail cache would improve the authoring experience significantly for 30+ slide decks.
9. **Outline/structure view.** A dedicated outline panel that shows titles + notes and lets you drag-reorder sections. Today reordering requires editing the SECTIONS array.
10. **Component library.** A small registry of reusable in-slide components (stat counter, progress bar, callout box) callable from `SECTIONS` with a `component: 'Stat', props: {value: '10M', label: 'users'}` pattern. This is where Spatial Deck can actually be more powerful than Claude Design — because it's code.

### Why this works

- Independence from Anthropic's product roadmap.
- Clearer story: "the open-source, code-native, performer-oriented deck framework."
- Doubling down on the existing strengths (keyframe system, Web Audio, iframes, XR/pixel-stream embeds) that Claude Design will never prioritize because those are not what PMs and founders need.

### Risk

- Real engineering cost (weeks, not days) to close the cold-start and layout gaps.
- Risk of feature-sprawl — the single-file constraint gets harder to hold as you add generators, layouts, exporters, thumbnail caches, and a cloud story.
- The "single HTML file" constraint collides with a cloud-sync story. Either the single-file rule softens (regression) or cloud stays out of scope (feature gap).

---

## 5. Recommendation — Hybrid, but heavily weighted toward Option A in the short term

**Short term (next 2–4 weeks): lean Option A. Ship the handoff story.**

- Announce Spatial Deck as **"the presenter's companion to Claude Design"** within a week of Claude Design's research preview press cycle — you can ride their launch coverage instead of fighting it.
- Build two importers: **PPTX → SECTIONS** (use the existing `anthropic-skills:pptx` skill as a reference implementation) and **Claude Design standalone-HTML → SECTIONS**. These are days of work, not weeks.
- Add a "paste design tokens" input to the Settings theme editor. Nearly free.
- Update the `README.md` "What Makes This Different" table to add a **Claude Design** column. Honest comparison: generation/editing = Claude Design wins; runtime/performer/offline/animation = Spatial Deck wins.
- Update `HANDOFF_PROMPT.md` with a "If a user arrives with a Claude Design handoff bundle" section.

**Medium term (next 1–3 months): pick a few Option B items that don't betray the single-file constraint.**

- Add 2–3 new slide layouts (quote, timeline, full-bleed). Pure wins, no architecture drift.
- Ship a `component:` field in SECTIONS with a small starter registry. Leans into Spatial Deck's actual unfair advantage (it's code).
- Add PPTX + PDF export. Required either way.
- **Do not** build a cloud/collaboration layer. It breaks the single-file story and you will lose a Figma-funded arms race.

**Do not try to compete with Claude Design on generation.** Opus 4.7 on a managed canvas will always out-generate a single-file framework. But Claude Design will never be the thing you run from a USB stick at a conference where the venue Wi-Fi is down, and it will never have a WAAPI keyframe scrubber or a Web Audio whoosh. That is your moat — defend it.

### Why hybrid, weighted toward A

Because the existing strengths of Spatial Deck (presenter mode, offline, live annotation, keyframe scrubber, WAAPI animation, Web Audio, XR iframe embeds, git-native, AI-editable) are **already downstream strengths**. They are what you reach for *after* the deck has been generated. Option A is just naming what's already true. Option B is a much bigger investment with more uncertain payoff against a well-funded opponent.

The hybrid play captures the best of both: ride Claude Design's launch for distribution, close the 2–3 layout/generation gaps that matter for standalone credibility, and keep the single-file soul intact.

---

## 6. Concrete next actions

1. Write a 3-paragraph blog post / README section: **"Spatial Deck + Claude Design: better together."** Publish within the week.
2. Prototype PPTX import using the `anthropic-skills:pptx` skill. Target: given a Claude Design PPTX export, auto-generate a working Spatial Deck HTML.
3. Prototype Claude Design standalone-HTML import. Heuristic extraction of `<section>`/`<h1>`/`<img>`/body into SECTIONS entries.
4. Add a "Design tokens JSON" textarea to the Settings slide theme editor.
5. Update `README.md` with a Claude Design comparison row and a "Works with Claude Design" badge near the top.
6. Update `HANDOFF_PROMPT.md` with the Claude Design handoff convention.
7. File issues for the three medium-term layout additions (quote / timeline / full-bleed) and the `component:` registry.

---

*End of report.*
