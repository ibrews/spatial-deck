# AI Workflow

Spatial Deck is designed from the ground up to be edited by LLMs. The single-file architecture, SECTIONS data model, and annotation export system are all built around AI-collaborative authoring.

---

## Why It Works With AI

- **Single file** — paste the whole thing (or the relevant section) into a context window
- **Config-driven** — change SECTIONS, slides update; no imperative DOM manipulation needed
- **Semantic class names** — `.case-title`, `.lesson-title`, `.case-bullet`, etc. are unambiguous
- **Comment landmarks** — `// ── Section Name ──` let the AI navigate the file without reading all of it
- **Annotation export** — export positions and text edits as markdown, paste into a prompt, the AI bakes them into source

---

## Starting a New Session

The repo includes `HANDOFF_PROMPT.md` — a comprehensive briefing document for AI agents:

```
Read HANDOFF_PROMPT.md and then help me with my presentation.
```

The handoff prompt covers: file structure, SECTIONS config format, media cycler API, slide steps, theme system, navigation hooks, and known quirks. It's kept up to date as the framework evolves.

**Keep `HANDOFF_PROMPT.md` updated.** When you add a custom IIFE or a new feature, update the handoff prompt so future AI sessions understand your deck.

---

## The Annotation Export Workflow

This is the core human-AI loop for layout work:

1. **Open the deck** in your browser.
2. **Drag elements into position** using move mode (`M`). The CSS coordinates auto-copy to clipboard.
3. **Leave text notes** using annotation mode (`A`). Click any element, type a note.
4. **Export annotations** — press `A` to open the annotation panel, then click Export. You get a markdown block like:

```markdown
## 1. Case title on slide #4
**Selector:** `.case-title`
**left:42%, top:18% on slide #4**
**Note:** TEXT EDIT: "Old title…" → "New title"
**Full text:** The New Exact Title Text
```

5. **Paste into a prompt** to your AI:

```
Here are my annotation edits — please bake them into the SECTIONS array:

[paste the annotation export]
```

6. The AI updates the source code. You reload and verify.

---

## Annotation Types

| Type | How to spot it | What the AI does |
|------|---------------|-----------------|
| Text edit | `Note: TEXT EDIT: "old…" → "new…"` + `**Full text:**` line | Replace with **Full text** verbatim |
| Position/move | `TRANSFORM left:X%, top:Y% · translate(...)` | Usually no-op (already in localStorage); bake to source only if asked |
| Plain note | `Note: some text` | Usually means "set this element's text to this string" — verify with the selector |

---

## Settings Round-Trip

The annotation export also includes a "Current Settings" block listing all config values (colors, fonts, scales, transition style, etc.). This lets you:

1. Tweak settings on slide 0 visually
2. Export annotations
3. Paste to AI with "update the D defaults object to match Current Settings"
4. The AI patches the hardcoded defaults in the `D` object

This is a **lossless round-trip** — the deck ships with your preferences baked in for anyone who opens it fresh.

---

## Example Prompts

These patterns work well:

**Adding content:**
```
Read HANDOFF_PROMPT.md. Add a new lesson to SECTIONS:
- Year: 2024
- Accent: purple
- Title: "The Fastest Way to Learn Is to Ship"
- Tagline: "Every project taught us something we couldn't have learned in theory."
- Two case studies: [describe them]
```

**Media cycler:**
```
Add a media cycler to the "AR at Scale" case study slide with these three images:
media/ar/site-01.jpg, media/ar/site-02.jpg, media/ar/overview.mp4 (loop: true)
```

**Editing from annotations:**
```
Here is the annotation export from my presentation session.
Please bake all TEXT EDIT annotations into the SECTIONS array,
and update any position transforms I've marked as "make permanent".

[paste export]
```

**Theming:**
```
Change the teal accent color to #0EA5E9 and the purple to #8B5CF6 in the :root block.
```

**Timing check:**
```
Look at the notes fields across all my SECTIONS entries.
Using the 150-wpm prose / 20-sec-per-bullet formula, estimate how long my talk will be.
Flag any slides with no notes.
```

---

## Working With Claude Design

[Claude Design](https://claude.ai/design) generates beautiful visual layouts — Spatial Deck is a natural runtime for them.

**Claude Design → Spatial Deck handoff:**

1. Export from Claude Design as HTML
2. Run `python3 tools/import_html.py exported.html`
3. Run `python3 tools/merge_sections.py tools/imported-exported-HASH.json`
4. Use `python3 tools/import_tokens.py` to pull the design tokens if Claude Design exported a CSS file

**Spatial Deck → Claude Design handoff:**

Export your SECTIONS as markdown (`python3 tools/export_md.py`) and paste it into a Claude Design session as the slide structure to style.

---

## Tips for AI Editing

- **Give context in the handoff**: "I'm presenting this at a 20-minute conference talk to a technical audience" helps the AI make better content decisions.
- **Reference the HANDOFF_PROMPT.md patterns**: the AI can follow them precisely if you say "use the pattern from HANDOFF_PROMPT.md for adding a media cycler".
- **Don't send the whole file unless needed**: for content edits, paste just the SECTIONS array. For layout changes, paste the annotation export. For engine changes, paste the relevant IIFE.
- **Curly quote gotcha**: if the AI produces edits with curly apostrophes (`'`/`'`) inside JavaScript string literals, the JS will break. Ask your AI assistant to use straight quotes in any JS strings.
