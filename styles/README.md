# Spatial Deck style library

What a Spatial Deck slide may look like, for people and for agents. Read this before styling a deck.

Audiences liked that Spatial Deck talks are dynamic and interactive, and said the styling read as generic AI design:
a near-black gradient with purple and teal glows, a starfield, Space Grotesk headings, cyan-to-purple gradient text,
glowing pills and the same dark noir on every slide. The library fixes that the way
[Keystone](https://github.com/ancarmona/keystone) does: taste lives in a curated library of looks, each with its
rules, tokens and example slides, not in model defaults. Nothing here changes the deck's builders or interactivity.
A look only restyles the markup they already produce.

- `look.md`: judgment. When to use the look, what it borrows from, do and don't.
- `look.json`: facts a script can check, such as tokens, type, motion grammar and the motion-graphic palette.
- `look.css`: the source of truth for how it renders.
- `examples/*.jpg`: the template's sample deck in that look (cover, chapter, two-pane case, figure case, bonus, close).

## Looks

Twelve looks plus the original. Browse them with example slides in [`index.html`](index.html) (regenerate with `python3 tools/build_look_gallery.py`).

| id | Name | Reads as | Example |
|---|---|---|---|
| `noir` | Noir (original) | The template's original look. It trips every tell below. Kept so existing talks don't change. | [examples](looks/noir/examples/) |
| [`sheet`](looks/sheet/look.md) | Drawing Set | Paper, ink and 1px hairlines in a drawing border with a title block; redline red is the one accent, blue pencil the second. | [cover](looks/sheet/examples/cover.jpg) |
| [`folio`](looks/folio/look.md) | Folio | Editorial print on a black page: warm white optical-size serif, one vermilion spot color, running head with folio number, lowercase italic kickers. | [cover](looks/folio/examples/cover.jpg) |
| [`house`](looks/house/look.md) | House | Theater program: warm black house, cream type, marquee-gold masthead band, condensed wood-type caps, serif program copy, a hard-edged followspot on chapter cards. | [cover](looks/house/examples/cover.jpg) |
| [`swiss`](looks/swiss/look.md) | Swiss | International Typographic Style: white paper, black grotesk, one signal red, flush-left on a six-column grid, hierarchy from size and position only. | [cover](looks/swiss/examples/cover.jpg) |
| [`transit`](looks/transit/look.md) | Transit | Wayfinding signage: white grotesk on black sign panels, a white rule under the band, chapters as colored route bullets. | [cover](looks/transit/examples/cover.jpg) |
| [`memo`](looks/memo/look.md) | Memo | A typewritten technical memorandum: one monospace, a SUBJECT / FROM / PAGE header, numbered paragraphs, a rubber-stamp red. | [cover](looks/memo/examples/cover.jpg) |
| [`riso`](looks/riso/look.md) | Riso | A risograph zine: two spot inks (federal blue and orange) on cream stock, overprint where they cross, a hard misregistered second pass on titles, halftone dots. | [cover](looks/riso/examples/cover.jpg) |
| [`bauhaus`](looks/bauhaus/look.md) | Bauhaus | Dessau-era printed matter: cream stock, black, the three primaries, a geometric sans set lowercase, circle / square / triangle as structure. | [cover](looks/bauhaus/examples/cover.jpg) |
| [`gallery`](looks/gallery/look.md) | Gallery | An exhibition: a deep green painted wall, works hung in white mats with a thin brass line, chapters as room introductions, tombstone labels. | [cover](looks/gallery/examples/cover.jpg) |
| [`cyanotype`](looks/cyanotype/look.md) | Cyanotype | Photogram plates: a Prussian blue ground, white where light was held back, plates numbered and captioned in italic. | [cover](looks/cyanotype/examples/cover.jpg) |
| [`broadside`](looks/broadside/look.md) | Broadside | A letterpress broadside: newsprint stock, everything centered, a slab display face with a book serif, thick-thin rules and fleurons, one red second color. | [cover](looks/broadside/examples/cover.jpg) |
| [`atlas`](looks/atlas/look.md) | Atlas | A survey map: buff paper, a neatline with a map collar, brown contours, blue water, letterspaced caps for names and italic for water features. | [cover](looks/atlas/examples/cover.jpg) |

## Use it

```bash
python3 tools/apply_look.py --html index.html --default sheet --motion-dir media/motion   # inline the library
```

Starting a new talk? `tools/new_talk.sh <slug> --title "…" --look <id>` bakes that look in as the default.

Then pick a look with `?look=sheet` in the URL, or set `body[data-look]` from a talk's options picker before the
runtime runs (the PMRE talk does this with its `theme` option). `apply_look.py` keeps the deck a single file. It
inlines `base.css` plus every `look.css` between sentinels, so it's safe to re-run after editing the library. With
`--motion-dir` it also writes `look.js`, which recolors seekable motion graphics written in the noir palette (colors,
fonts, glow filters, screen blending on paper). That works offline too, because the deck passes the look through
the iframe's `window.name`.

Check the result:

```bash
node tools/lint_look.mjs index.html --look sheet      # generic-tells lint on the rendered deck (exit 1 if > --max 1)
python3 tools/check_branding.py                       # a fork must not ship the template's social card / favicon
```

## Tokens (every look defines these)

| Group | Tokens | Notes |
|---|---|---|
| Color | `--paper` `--paper-2` `--ink` `--ink-2` `--ink-3` `--rule` `--rule-2` `--acc-1..4` | Builders' `--teal/--purple/--amber/--rose` map to `--acc-1..4`, so section accents keep working. One real accent per look; the others repeat or step toward ink. |
| Type | `--font-display` `--font-body` `--font-mono` | One pairing per look. Fonts load from one Google Fonts link: Archivo (with width axis), IBM Plex Mono, Newsreader (optical size), Big Shoulders Display, Libre Franklin, EB Garamond, Jost, Bricolage Grotesque, Alfa Slab One. |
| Scale | `--t-display` `--t-h1` `--t-h2` `--t-lead` `--t-body` `--t-label` | Shared, declared in `base.css` on `#deck` so they follow the 1920x1080 stage. The lead is larger than the template's tagline, so it stays legible on LED walls. |
| Space | `--s1`..`--s6` | 0.5, 1, 1.5, 2.5, 4 and 6.5 rem. |
| Motion | `--m-enter` `--m-enter-2` `--m-dur` `--m-ease` `--m-stagger` | One entrance per look, on the active slide only. Reduced motion lands on the final frame. |

Specificity ladder (handled by `apply_look.py`): template rules < `base.css` < a look. Write `:look` for the look's
scope and `:looked` for "any look but noir". Don't hand-write `body[data-look=…]`.

## The generic tells (what `lint_look.mjs` flags)

| Tell | Why it reads as default AI design | Measured as |
|---|---|---|
| `starfield` | Ambient particles say "tech" without saying anything about the talk | `canvas#stars` visible |
| `radial-glow-bg` | Soft purple and teal radial glows are the default hero background of generated pages | neon colors in a radial gradient on `.bg` |
| `gradient-text` | Cyan-to-violet text fill is the single most recognizable stock headline | `background-clip:text` with a gradient |
| `neon-palette` | Cyan, violet and magenta used as text color, with nothing tying them to the content | 3 or more text elements in that hue band |
| `glow` | Colored blurs of 16px or more on boxes or text | box-shadow, text-shadow or drop-shadow |
| `pill-tags` | Fully rounded translucent chips standing in for labels | radius at least half the height, translucent fill |
| `glass` | Frosted cards with backdrop blur | `backdrop-filter: blur` |
| `ai-font` | Space Grotesk, Inter, Outfit, Poppins, Manrope, Sora and DM Sans as the heading face | the computed family of most h1–h3 |

A look isn't "anything that passes the lint". Passing only proves the stock pieces are gone. Each look also has to
come from a real tradition (see each `look.md`) and keep one idea per slide.

## Adding a look (agent workflow)

1. Name its lineage first, a real printed or built tradition, and write `look.md` from it: what to borrow, what not to.
2. Copy a `look.json`, then set the tokens and a motion palette for every key in `motionSource`.
3. Write `look.css` with `:look` rules. Restyle builder classes. Don't add per-slide variants. If a layout needs
   structure CSS can't give it, add it to the look runtime in `apply_look.py`, the way the chapter badge split works.
4. Run `apply_look.py` and `build_look_gallery.py`, capture `examples/` (`tools/capture_slides.py --query look=<id>`), and run
   `lint_look.mjs --look <id>` (0 tells expected). Check it at 390px wide and with reduced motion.

Research and references behind these looks: KB `projects/spatial-deck/style-references.md`.
