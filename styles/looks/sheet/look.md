# Look: Drawing Set (`sheet`)

The deck reads as a set of construction documents. It's warm drafting paper with a 40px grid, a sheet border, and a
title block in the bottom-right corner (project, presenter and event, sheet number). Display type is condensed
architectural caps, labels are monospace, and redline red is the only real accent, with blue pencil as a second.
Use it for talks about building, design process, architecture or engineering, and anywhere "this was drawn, then
built" is the story.

**Lineage.** AIA and US National CAD Standard sheet conventions: border, title block, sheet numbers, detail callout
bubbles, numbered keynotes, dimension lines, redlines. Swiss flush-left alignment on a margin.

| Builder piece | In this look |
|---|---|
| Cover | Title sheet. Event as a redline label, the title in condensed caps (`.xr` in redline), the speaker as a title-block cell |
| Chapter (`lesson`) | Detail callout (section number over total, in a split circle), title, lead under a hairline, a dimension line where the old accent bar was |
| Two-pane case | The image framed as a detail, bullets as numbered keynotes in square tags |
| Statement (`big`) | A sheet note, not a poster: mono eyebrow, condensed title, caption on a redline bar |
| Full bleed / grid | 1px ink frames, labels as drawing tags in the cell corner |
| Close | Same left margin as the cover. Contact and QR in ruled boxes. The logo is inverted to ink |
| Motion graphics | Recolored to ink on paper: teal to blue pencil, rose to redline, purple to green pencil, amber to ochre. Glow filters removed, screen blending becomes multiply |

**Motion grammar: draw.** Titles wipe on left to right like a pen stroke (0.55s); copy fades in 180ms later.
Reduced motion shows the final frame.

**Do** keep one accent per slide, and keep labels in mono caps. **Don't** fill shapes with color, round corners, or
center a chapter card. Drawing sets are flush left.

Examples: [cover](examples/cover.jpg) · [chapter](examples/chapter.jpg) · [two-pane case](examples/case-two-pane.jpg) · [figure case](examples/case-figure.jpg) · [bonus](examples/bonus.jpg) · [close](examples/close.jpg)
