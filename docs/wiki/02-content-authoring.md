# Content Authoring

All your content lives in the `SECTIONS` array and `BONUS` constant near the top of `index.html`'s first `<script>` block.

---

## The SECTIONS Array

Each entry in SECTIONS represents one **chapter** — a lesson slide plus its case study slides.

### Full Schema

```javascript
const SECTIONS = [
  {
    year: 2024,           // Number — appears on the lesson slide
    accent: 'teal',       // 'teal' | 'purple' | 'amber' | 'rose'
    lesson: {
      title: 'Lesson Title\nWith Line Breaks',
      tagline: 'Body text that explains the lesson.<br><br>Second paragraph.',
      short: 'SHORT',     // Abbreviated tag shown on the constellation map
      tags: 'Tag · Tag · Tag',
      notes: 'Speaker notes: what to say on this slide.'
    },
    cases: [
      {
        title: 'Case Study Title',
        subtitle: 'One-line description of the project',
        img: '',           // See "img values" below
        layout: 'default', // Optional — see "Layout Types" below
        bullets: [
          'First key point',
          'Second key point',
          'Third key point'
        ],
        notes: 'What to say on this case study slide.'
      }
    ]
  }
];
```

### `accent` Values

| Value | Color |
|-------|-------|
| `'teal'` | Blue-green |
| `'purple'` | Violet |
| `'amber'` | Gold/orange |
| `'rose'` | Pink/red |

The accent color drives the lesson slide header, bullet color, and subtle glow.

---

## `img` Values

| Value | What renders |
|-------|-------------|
| `''` | Gradient placeholder (uses accent color) |
| `'media/photo.jpg'` | Standard `<img>` tag |
| `'MEDIA_CYCLER'` | Canvas-based gallery (requires a matching IIFE — see [Media](03-media.md)) |
| `'IFRAME:https://...'` | Responsive embedded iframe (YouTube, Vimeo, Sketchfab, pixel streams) |

The build loop checks in this priority order: `IFRAME:` prefix → iframe; real file path → `<img>`; `MEDIA_CYCLER` → cycler mount point; empty → gradient.

---

## Text Formatting

### Titles

Use `\n` for line breaks in titles:
```javascript
title: 'Constraint Is\nOpportunity'
// Renders as two-line title
```

### Taglines

Use `<br>` for a line break, `<br><br>` for a paragraph gap:
```javascript
tagline: 'First sentence.<br><br>Second paragraph — more space above.'
```

### Bullets

Use `\n` within a bullet string to add a line break inside that bullet:
```javascript
bullets: ['Main point\nSub-detail on second line', 'Next point']
```

---

## Layout Types

Case studies support four layouts. Set `layout:` on the case object.

### `default` (no need to set — this is the fallback)

48% media left, 52% content right. The standard case study.

### `placed`

Full-bleed slide with absolutely positioned images/videos. Best for show-don't-tell slides where you want precise pixel placement.

```javascript
{
  title: 'Optional overlay title',
  subtitle: 'Optional subtitle',
  layout: 'placed',
  placedImages: [
    ['media/bg.jpg',     0,  0, 100, 100],              // [src, left%, top%, w%, h%]
    ['media/overlay.png', 10, 20, 40,  50],
    ['media/clip.mp4',   50, 30, 45,  60],              // .mp4 auto-detected as <video>
    ['media/img.jpg',     0,  0, 100, 100, 'center bottom'] // 6th param = object-position
  ],
  notes: 'What to say.'
}
```

- Coordinates are percentages of slide dimensions.
- `.mp4`, `.webm`, `.mov` files auto-render as `<video muted loop autoplay>`.
- The 6th optional parameter sets CSS `object-position` (default: `'center center'`).
- `title` and `subtitle` float above all images at z-index 2.
- No `bullets` — placed slides are purely visual.

### `big`

Full-screen typographic statement. Use when one big sentence IS the slide.

```javascript
{
  layout: 'big',
  bigText: 'The constraint\nis the design.',
  title: 'Eyebrow text (optional)',      // small text above bigText
  subtitle: 'Italic subhead (optional)', // appears between title and bigText
  bigCaption: 'Small italic caption.',   // small text below bigText
  notes: 'What to say.'
}
```

### `split-50`, `bleed`, `trio`

Three additional layouts are available as an optional patch. See [`tools/layouts/preview.html`](../../tools/layouts/preview.html) for visual previews and [`tools/layouts/PATCH.md`](../../tools/layouts/PATCH.md) for the splice instructions.

---

## Slide Types

The framework automatically generates these slide types. You don't create most of them directly.

| Type | Source | What it is |
|------|--------|-----------|
| `settings` | Auto-generated (slide 0) | Theme editor, hidden from navigation |
| `cover` | Hardcoded | Title slide with the deck name |
| `lesson` | Each `SECTIONS[i].lesson` | Year + lesson number + title + tagline |
| `case` | Each `SECTIONS[i].cases[j]` | Image/media + title + bullets |
| `bonus` | `BONUS` constant | Amber-accent closing statement |
| `map` | Auto-generated | Animated constellation of all lessons |
| `close` | Hardcoded | QR code + contact info |

---

## The BONUS Constant

There's a single special slide at the end before the closing slide, styled with the amber accent. Edit the `BONUS` const (in the first script block, right after `SECTIONS`):

```javascript
const BONUS = {
  title: 'The closing thought.',
  subtitle: 'Optional subtitle.',
  notes: 'What to say here.'
};
```

---

## Cover and Close Slides

The cover and close slides are hardcoded in the engine block. To customize them, search for the `buildCover()` and `buildClose()` function calls (or look for `data-type="cover"` and `data-type="close"` in the generated DOM). You can update text directly in those functions in the second script block.

---

## Speaker Notes

Every `lesson` and every `cases` entry can have a `notes` field. Notes appear in:
- The inline notes drawer (`Shift+N`)
- The presenter popup (`N`)
- The `?notes` phone companion view
- The duration estimator (Settings slide)

Formatting conventions:
- **Bullets**: start lines with `-` or `•` — the duration estimator treats each as ~20 seconds
- **Prose**: full sentences — counted at ~150 words/minute
- **Video cue**: include `(over video)` in the note to tell the estimator those words are spoken concurrent with video (not counted toward talk length)

```javascript
notes: '- Open with the problem\n- Show before/after\n- (over video) Narrate the transformation\n- Ask for questions'
```

---

## Hiding and Parking Slides

### Hiding

`Ctrl/Cmd + Click` any slide thumbnail in the grid to hide it. Hidden slides:
- Show at 30% opacity with a dashed border in the grid
- Are skipped by all navigation (arrows, swipe, keyboard)
- Can still be jumped to directly by clicking their thumbnail

### Parking

Add slide indices to the `PARK` array (in the main script block) to move slides to the end of the deck. Useful for "maybe" slides you might want to reference in Q&A.

```javascript
const PARK = [5, 8]; // move slides 5 and 8 to the end
```

Indices are 0-based and reference the *pre-park* position.

---

## Updating the Deck Title and Cover

The cover text and constellation map center text are set in the engine. To change them, search the second script for:
- `BONUS.title` vicinity for the map center text
- The `buildCover` section for cover slide copy

---

## Tips

- **Keep titles short** — two lines max renders best. Long titles truncate at small font sizes.
- **Three bullets is the sweet spot** — the layout is designed for 2–4.
- **Year doesn't have to be a calendar year** — it's just a label. `chapter: 1` style numbering works fine if you're not doing a year-retrospective format.
- **`accent` is per-chapter, not per-slide** — all cases in a chapter share the chapter's accent.
