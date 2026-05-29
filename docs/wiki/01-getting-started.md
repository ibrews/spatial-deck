# Getting Started

## Prerequisites

- A browser (Chrome recommended; Firefox and Safari work)
- Git (optional — you can also just download the ZIP)
- A text editor or IDE (VS Code works great)

No Node.js. No npm. No build toolchain.

---

## Clone and Open

```bash
git clone https://github.com/ibrews/spatial-deck.git
cd spatial-deck
open index.html
```

The presentation loads immediately. Press `→` or `Space` to advance.

> **Serving locally:** `file://` works for almost everything. The only case where you need a local server is Three.js (the constellation map) in Chrome — if you see a same-origin warning, run `python3 -m http.server 8080` and open `http://localhost:8080`.

---

## What You're Looking At

When you open `index.html` you see the **sample deck** — "Is XR Right For Your Project?". This is the built-in demo content. You'll replace it with your own.

The UI has:
- A **slide counter** (top-left) — `01/NN` format
- A **slide grid button** (top-right, grid icon) — see all slides at once
- A **settings icon** — opens the theme editor (or press `#0` in the URL)
- A **search icon** (or press `/`) — full-text search across all slides

In presentation mode (default) most chrome is hidden. Press `?edit` in the URL to see everything.

---

## Understanding the File Structure

```
spatial-deck/
├── index.html      ← THE ENTIRE PRESENTATION
├── media/          ← Your images and videos go here
├── images/         ← AI-generated images shipped with the template
├── tools/          ← Optional Python scripts for importing/exporting
└── docs/           ← Screenshots and this wiki
```

Open `index.html` in your editor. The file has two `<script>` blocks:

1. **First script** (~50 lines near the top) — the `SECTIONS` array and `BONUS` constant. **This is where you write your content.**
2. **Second script** (~750 lines) — the engine: slide builder, navigation, media cycler, move mode, annotations, presenter tools. You usually don't touch this unless adding custom animations.

---

## Making Your First Edit

Find the `SECTIONS` array in the first script block. It looks like this:

```javascript
const SECTIONS = [
  {
    year: 2023, accent: 'teal',
    lesson: {
      title: 'Your Lesson\nGoes Here',
      tagline: 'A short explanation of what this lesson is about.',
      short: 'SHORT TAG',
      tags: 'Topic · Tag · Another',
      notes: 'What to say when this slide appears.'
    },
    cases: [
      {
        title: 'Case Study Title',
        subtitle: 'One-line description',
        img: '',  // empty = gradient placeholder
        bullets: ['First bullet', 'Second bullet', 'Third bullet'],
        notes: 'Talking points for this case study.'
      }
    ]
  }
];
```

Change `title` to something else, save, and reload the browser. The slide updates.

**That's the entire editing model.** See [Content Authoring](02-content-authoring.md) for the full SECTIONS reference.

---

## Forking for Your Talk

The recommended workflow: **one GitHub repo per talk**, forked from this template.

```bash
# Create your fork
gh repo create my-talk-2026 --public --clone
cd my-talk-2026

# Copy the template
cp /path/to/spatial-deck/index.html .
cp -r /path/to/spatial-deck/media .    # optional sample media
git add -A && git commit -m "Fork from spatial-deck" && git push

# Your talk lives here now — edit SECTIONS in index.html
```

When the template gets new features later:
```bash
git remote add template https://github.com/ibrews/spatial-deck.git
git fetch template && git merge template/main
# Resolve conflicts in SECTIONS (your content vs. sample content)
```

---

## Presenting

1. Open `index.html` in a browser on the presentation machine.
2. Press `H` to hide all UI chrome for a clean audience view.
3. Use `→` / `Space` to advance, `←` to go back.
4. Press `N` to open the **Presenter Popup** in a second window (speaker notes + timer).
5. On mobile: tap to advance, swipe left/right to navigate.

See [Presenter Tools](06-presenter-tools.md) for the full presenting workflow.

---

## URL Modes

| URL | What it does |
|-----|-------------|
| `index.html` | View mode — clean, no edit chrome |
| `index.html?edit` | Edit mode — all chrome visible, starts at Settings slide |
| `index.html?edit#5` | Edit mode, starting at slide 5 |
| `index.html?vertical` | Vertical scroll mode — slides flow top-to-bottom (great for sharing as a web doc) |
| `index.html?notes` | Phone speaker companion — notes-only view |
| `index.html#15` | Jump directly to slide 15 |

---

## Next Steps

- [Content Authoring](02-content-authoring.md) — fill in your SECTIONS
- [Media](03-media.md) — add images and videos
- [Theme & Settings](05-theme-settings.md) — customize colors and fonts
- [Presenter Tools](06-presenter-tools.md) — set up your presenter workflow
