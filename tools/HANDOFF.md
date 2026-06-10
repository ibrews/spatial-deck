# Spatial Deck — Handoff for Fresh Session

**Status (updated 2026-04-18):** All fleet-first importer + exporter + QA tooling has shipped. The remaining roadmap is Claude-first (judgment-heavy) and should not be started speculatively — wait for a real user ask.

**Target model:** Sonnet 4.6 for any fleet-glue work (formulaic, JSON-validated). Opus for the Claude-first items below (they require taste). Fast Mode is fine for both.

## Where to pick up

If the user is here to **extend the importer suite** — you're mostly done. Read `README.md §🤝 Claude Design Handoff` for the complete tool list. The patterns doc is [`~/knowledge/departments/engineering/fleet-structured-json-playbook.md`](../../../knowledge/departments/engineering/fleet-structured-json-playbook.md) (outside the repo).

If the user is here to **adopt the new layouts** — [`tools/layouts/preview.html`](layouts/preview.html) shows them, [`tools/layouts/PATCH.md`](layouts/PATCH.md) has the exact splice. Not applied automatically because `index.html` usually has uncommitted edits.

If the user is here for **something CLAUDE-first** (judgment, UX, narrative) — see "Roadmap — CLAUDE-FIRST" below. Expect architectural conversation first, code second.

**Read first:**
- [README.md § 🤝 Claude Design Handoff](../README.md) — user-facing description of what exists
- [tools/fleet_client.py](fleet_client.py) — 90-line Ollama wrapper, already battle-tested
- [tools/import_tokens.py](import_tokens.py) + [tools/import_pptx.py](import_pptx.py) — the two shipped importers. Mimic their structure.
- [intelligence/research/parallel-builds/2026-04-17-claude-design-vs-spatial-deck.md](../intelligence/research/parallel-builds/2026-04-17-claude-design-vs-spatial-deck.md) — strategic context on why this track exists

## What's already shipped

| Feature | How it works | Commit |
|---|---|---|
| **Design-token import** | Any CSS/JSON/prose → `llama3.1:8b@Sam` normalizes to fixed schema → regex-validates hex → patches `:root{}` in `index.html` | cb9199e |
| **PPTX import** | `python-pptx` extracts text/images deterministically → `llama3.1:8b@Sam` rewrites body copy into tight bullets → merger splices between `// ── IMPORTED START ──` sentinels | ee415a1 |
| **Markdown import** | Regex parses `#`/`##`/`-`/`![]()`/`>` deterministically → optional `--tighten` via `llama3.1:8b@Sam` with `qwen3:8b@MBP` fallback → merger splices chapter | (this PR) |
| **HTML import** | BeautifulSoup chunks by `<section>`/headings → `qwen2.5-coder:14b@Archie` normalizes to `{title,subtitle,bullets}` with `qwen3-coder:30b@MBP` fallback → images (incl. `data:` URIs) land in `media/import-*/` | (this PR) |
| **PDF import** | `pdfplumber` per-page text sorted by y/x → `llama3.1:8b@Sam` normalizes → `page.crop().to_image()` for embedded rasters | 3a10a79-ish |
| **Slide linter** | Node subprocess evals SECTIONS as data → static checks (title/bullet length, dup titles, orphan numbers, empty taglines) → optional `--llm` semantic pass via `llama3.1:8b@Sam`. Never mutates. | acd4ff6 |
| **Timing estimator** | Same extractor → 150wpm/20s-per-bullet formula → markdown/JSON report with pacing traffic-light against `--target`; `--generate` drafts notes via `llama3.1:8b@Sam` | 3a10a79 |
| **Alt-text generator** | Vision via `gemma3:12b@Lenny` over local image paths in SECTIONS. JSON patch output only. `--scan-media` lists orphans. | 3451dcc |
| **Palette extractor** | Pillow + pure-Python k-means++ → hue/luminance map to token schema, synth missing accent hues from primary. Optional `--vibe` via Lenny vision. Round-trips through `import_tokens.py`. | 1ad39d4 |
| **SessionStart git-freshness hook** | Warns if repo is behind origin (unrelated to importers, but installed same day) | KB 73f067f9 |
| **Markdown exporter (`export_md.py`)** | Inverse of `import_md`. YAML-ish meta block preserves year/accent/short/tags/multiline-title. Round-trip verified: 0 diffs via `diff_decks.py`. | 0ecf1be |
| **HTML exporter (`export_html.py`)** | Static, no-JS single-page outline. Dark theme, accent bar per chapter. For email / print / review. | 1ab9f69 |
| **PPTX exporter (`export_pptx.py`)** | `python-pptx` emitter; round-trips cleanly through `import_pptx.py`. Accent bar, notes placeholder, 2-column layout. | 1ab9f69 |
| **Peer-review harness (`peer_review.py`)** | Two reviewers from different model families (`llama3.1:8b`@Sam narrative + `qwen2.5-coder:14b`@Archie structural), merge-vote collapses (case_title, category) buckets. Both-flagged = 🔴, solo = 🟡. | 1ab9f69 |
| **Multi-deck merge (`merge_decks.py`)** | Mechanical concatenation of N sources with conflict detection (year collision, duplicate titles, Jaccard near-duplicates over bullet tokens). Writes `.conflicts.md`. Editorial ordering stays with Claude. | 1ab9f69 |
| **Layout preview + splice patch** | `tools/layouts/preview.html` + `tools/layouts/PATCH.md`. Three new layouts (`split-50`, `bleed`, `trio`) as a preview page + the exact CSS/JS diff to splice when you want to adopt them. Not editing `index.html` directly (usually has uncommitted edits). | 0e67a2f |
| **Showcase chapter in sample deck** | `index.html` SECTIONS now includes CH 4 "Your Deck Is Data. Treat It Like Code." (rose accent, 3 cases showcasing the tool suite). | this session |
| **KB-deck importer (`import_kb_deck.py`)** | New importer for the per-slide-frontmatter format produced by overnight AI agents (SECTIONS.json + slides/NN-*.md). Reads design tokens, generates a self-contained HTML deck with speaker notes embedded as `window._deckSpeakerNotes` and slides color-coded by `_speaker` via `_kb_speaker_styling.css`. Different from `import_md.py` — see below. | (this session) |

## `import_kb_deck.py` — when to use it

`import_md.py` consumes a **single** markdown file (the SECTIONS-as-prose convention). `import_kb_deck.py` consumes a **directory** with this layout:

```
deck/
├── SECTIONS.json        # design tokens + canonical section/slide order
├── slides/
│   ├── 01-title.md      # YAML frontmatter (slide, section, speaker, layout, ...)
│   ├── 02-thesis.md     # body has h1/h2 title, paragraphs, bullets,
│   │                    #   "## Speaker Notes", "## Visual notes" sections
│   └── ...
└── README.md
```

This format is what overnight AI agents produce when drafting decks from the KB — every slide is its own file with rich frontmatter and speaker notes. The flat `import_md.py` convention can't represent that without losing data.

**Run it:**

```bash
python3 tools/import_kb_deck.py path/to/deck \
    --out /tmp/output.html \
    [--title "Override title"] \
    [--template path/to/index.html]
```

Defaults `--template` to the repo's own `index.html`. Output is a single self-contained HTML file: open in any browser, navigate with arrow keys.

**What it produces in addition to a normal deck:**

- `<style id="kb-design-tokens">` injected before `</head>` with CSS custom properties mapped from `design_tokens` in `SECTIONS.json` (bg_primary→--bg, accent_magenta→--rose, etc.).
- `<style id="kb-speaker-styling">` inlined from `tools/_kb_speaker_styling.css` — adds a left-edge accent bar and small speaker badge to slides based on `data-speaker`.
- `window._deckSpeakerNotes` and `window._deckSpeakers` globals so the existing presenter popup can pull notes by slide id.
- A small `kb-speaker-shim` script that walks SECTIONS and stamps `data-speaker` / `data-layout` on each rendered slide for the CSS to target.
- Frontmatter `layout:` hint preserved on each case as `_layout` for future Spatial Deck features.

**Gotchas (already handled, but noted for next-session debugging):**

- The template's engine script contains a `_notesWin.document.write(\`...</body></html>\`)` template literal. Naive `html.replace("</body>", ...)` would match the first occurrence inside that string — the importer uses `rfind("</body>")` to inject before the *real* body close.
- SECTIONS.json's `section` values are title-cased (e.g. `"Hook"`); slide frontmatter uses lowercase (`section: hook`). The importer uses SECTIONS.json's order as canonical and ignores frontmatter `section:` for grouping.
- Token names differ across variants (`accent_magenta` in coherent, `accent_warm` in bold). The mapping in `build_design_token_css()` covers all three nxtbld variants and gracefully ignores unknown tokens.

## Fleet endpoints (confirmed working 2026-04-18)

> **Provider resolution (2026-06-09):** `fleet_client.py` no longer assumes the
> Tailscale fleet. It resolves providers in order: (1) `tools/providers.json`
> explicit config (gitignored — see `providers.json.example`), (2) env
> auto-detect (`ANTHROPIC_API_KEY` → Claude Haiku, `OPENAI_API_KEY` →
> gpt-4o-mini with `OPENAI_BASE_URL` override, `OLLAMA_HOST`), (3) a probe of
> local Ollama at `localhost:11434`, (4) the fleet table below as last
> fallback, (5) `NoProviderError` + a stderr hint — importers catch it and fall
> back to deterministic output (`--no-llm` paths). The `model`/`endpoint` args
> importers pass are honored when an Ollama endpoint serves the call and
> ignored by hosted APIs. Vision calls (`call_vision`) ride the same chain.
> Diagnostic: `python3 tools/fleet_client.py --probe-only`.

```
sam    100.127.46.63:11434   llama3.1:8b        — structured JSON, classification (fleet winner for these)
archie 100.103.192.41:11434  qwen2.5-coder:14b  — code parsing, HTML/XML
lenny  100.78.179.55:11434   qwen3-coder:30b, gemma3:27b — code-gen, design/visual
mbp    100.95.59.11:11434    qwen3-coder:30b    — code-gen fallback
```

Fort is offline (has been 5+ nights as of 2026-04-17). Sam can be flaky — `Connection refused` means Ollama daemon stopped; the machine is fine. Route to Archie's `llama3.1:8b` as fallback.

## What we learned (apply to every new importer)

1. **Single-pass only.** The fleet collapses on "revise this JSON" prompts. If parse fails, re-prompt with a *different* prompt, never "please fix."
2. **Validate structure, not semantics.** Hex regex, enum check, required-keys check. Trust the model's judgment on the text itself — it's better than you'd expect.
3. **Deterministic extraction first, LLM for cleanup.** `python-pptx` handles XML. BeautifulSoup handles HTML. The LLM only rewrites prose or classifies.
4. **Fall back silently to raw.** If LLM normalization fails, use the raw extracted text. Don't block the user on model reliability.
5. **Sentinel-based splicing is idempotent.** `// ── IMPORTED START ──` / `// ── IMPORTED END ──` lets you re-import as many times as you like.
6. **Match the existing `js_string()` emitter in merge_sections.py** — it handles backslash/quote/newline escaping correctly. Don't reinvent.
7. **No JSON mode in Ollama.** Always append `"Return ONLY valid JSON. No prose."` and parse defensively (`_extract_json` in fleet_client handles fences, stray prose, `<think>` blocks).
8. **Per-slide chunking for Sam.** 16GB RAM machine — don't send entire files. One slide per call, parallelize across machines if speed matters.

## Roadmap — FLEET-FIRST (ship with minimal Claude oversight)

### ~~A. Standalone-HTML importer~~ ✅ SHIPPED
See `tools/import_html.py`. Structural-selector chunking with heading fallback; Archie primary, MBP fallback; `data:` URIs decoded to `media/`.

### ~~B. Markdown importer~~ ✅ SHIPPED
See `tools/import_md.py`. `#`/`##`/`-`/`![]()`/`>` convention, deterministic parse, optional `--tighten`.

### ~~C. Slide linter~~ ✅ SHIPPED — `tools/lint_deck.py`
### ~~D. Image alt-text generator~~ ✅ SHIPPED — `tools/gen_alt_text.py`
### ~~E. PDF importer~~ ✅ SHIPPED — `tools/import_pdf.py`
### ~~F. Speaker-note timing estimator~~ ✅ SHIPPED — `tools/estimate_timing.py`
### ~~G. Palette from reference image~~ ✅ SHIPPED — `tools/extract_palette.py`

## Roadmap — CLAUDE-FIRST (judgment / UX / reasoning)

### H. `component:` registry *(architecture refactor)*
**Why Claude:** Design-space exploration. SECTIONS is config; this adds a new slide-type layer. Needs thinking about extensibility vs the project's "single-file, no-build" ethos.
**Starting point:** Consider whether `component:` should be a string enum matching a JS dispatch table, or a template literal evaluated at build. Trade-offs matter.

### I. 2–3 new slide layouts
**Why Claude:** CSS + visual judgment. Possible additions: split-screen (text left, media right, 50/50), full-bleed media with overlay caption, three-column comparison.
**Starting point:** Look at `case-slide` and `lesson-slide` classes in `index.html` as templates; clone + modify.

### J. Keyframe animation auto-generation from prose intent
**Why Claude:** "Make the title fade in then the bullets cascade" → WAAPI keyframes on the right elements. Intent parsing + DOM mapping is genuinely hard for local models (no reasoning >6/10 on the fleet).
**Starting point:** Spatial Deck's existing keyframe system is at `// ── Keyframe Animation System ──` in index.html. Extend the `◆ KF` button flow.

### K. Narrative coach / slide-reorder suggester
**Why Claude:** Requires understanding story arc. Given a SECTIONS array, suggest reorderings, flag "setup missing before payoff," identify missing transitions.

### L. Importer UI panel inside the deck
**Why Claude:** Needs UX thought. Could add a hidden admin slide that takes drag-and-drop `.pptx` / `.css` and runs the Python tools server-side (or WASM-side for offline).
**Watch out for:** Violates the "no build process, one file" core promise if done wrong. Probably needs to stay CLI-only.

## Roadmap — HYBRID

### M. End-to-end "Claude Design → Spatial Deck" demo
Combine A + the existing token importer. Fleet extracts structure, Claude writes the README/demo narrative + social card. Good candidate for a PR that demonstrates the companion-mode positioning publicly.

### N. Multi-deck merge
Fleet extracts SECTIONS from N source decks, Claude resolves overlap/conflicts and picks a narrative order. Pure Python for the merge; Claude for the editorial pass.

## Gotchas the fresh session should know

- **`index.html` is densely packed** — long lines, minimal whitespace. Match the existing style. CLAUDE.md in `.claude/` enforces this.
- **Don't add a build step.** No npm, no webpack, no bundler. It's a hill to die on.
- **Commit after every shipped slice.** Local-only. Only push when the user asks (`git push origin main`). Previous session pushed without asking — the user didn't mind but it's not the default.
- **The user's `index.html` often has uncommitted edits.** Leave them alone. Dry-run importers or use `--html /tmp/copy.html` for testing.
- **Node is available** (`/opt/homebrew/bin/node`) for JS syntax validation of the patched `index.html`. Use `node --check`.
- **`python-pptx` is installed** via `pip3 install --user --break-system-packages`. `beautifulsoup4` and `pdfplumber` are not yet.
- **Every importer should have a `--dry-run` flag** (tokens) or a separate merge step (pptx). Never overwrite `index.html` in one shot without the user seeing output first.
- **KB at `~/knowledge/`** has the fleet roster (`departments/engineering/infrastructure-overview.md`) and the nightly eval manifest (`fleet/delegation-manifest.md` — re-check before pipeline building).
- **Fleet routing is a moving target.** Fort is offline today; llama3.1:8b also exists on Archie. Check `curl http://<ip>:11434/api/tags` before committing to an endpoint.

## Suggested first move for the fresh session

**Everything fleet-tractable has shipped** (A–G + the bonus round: reverse importers, peer review, multi-deck merge, layouts, deck diff). Don't re-implement; read the tool before rebuilding it.

If the user asks for more, the remaining roadmap (H–N) is **Claude-first** and should start with a design conversation, not code:

- **H.** `component:` registry → architecture call (enum vs template literal; fits "single-file, no-build" ethos?)
- **I.** New layouts → **preview + patch shipped** at `tools/layouts/`; just needs the user to review + splice
- **J.** Prose → WAAPI keyframes → intent parsing + DOM targeting; local models fail here
- **K.** Narrative coach / reorder suggester → story-arc reasoning
- **L.** In-deck importer UI panel → UX decision (violates "no build step" if done wrong)
- **M.** End-to-end "Claude Design → Spatial Deck" demo → hybrid: fleet plumbing + Claude narrative
- **N.** Multi-deck **editorial** merge → mechanical merger shipped; the narrative-order pass remains

## Where the KB + docs live

- **In-repo README** — authoritative feature list, quickstart, fleet routing table
- **In-repo `tools/HANDOFF.md`** — this file; fresh-session briefing
- **KB `projects/spatial-deck/overview.md`** — cross-project context, upcoming talks, architecture sketch
- **KB `departments/engineering/fleet-structured-json-playbook.md`** — reusable patterns for any fleet-backed importer (not just this project)
- **KB `intelligence/decisions/2026-04-18-spatial-deck-fleet-importer-suite.md`** — decision record for why fleet-first was chosen and what worked
- **KB `departments/engineering/fleet-delegation-lessons.md`** — post-mortems including the "two-reviewer pattern works / local models can't do narrative" findings from this session
