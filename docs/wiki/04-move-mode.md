# Move Mode & Layout

Move mode lets you drag any element on any slide into a new position without touching code. Transforms are auto-saved and exported as annotations so you can hand them to an AI to bake into source.

---

## Entering and Exiting

Press `M` to toggle move mode on/off. A HUD appears at the bottom of the slide showing modifier hints and z-order buttons.

> Move mode persists across slides — you can navigate while in move mode and reposition elements on different slides without toggling off.

---

## Dragging Elements

Click to select any element (it gets a blue outline), then drag to move it. The element gets `position:absolute; left:X%; top:Y%` set as inline style.

After releasing, the CSS position string is **automatically copied to your clipboard**:
```
📋 Position copied: left:45%, top:32%
```

This is designed for the AI workflow: drag something into place visually, paste the coordinate into a prompt, and the AI can bake it into source code precisely.

### Modifier Drags

| Modifier | Drag behavior |
|----------|--------------|
| No modifier | Translate (move) |
| `Shift + drag` | Scale element |
| `Alt/Option + drag` | Rotate element |
| `Cmd/Ctrl + click` | Select parent element |

---

## Z-Ordering (Layering)

When elements overlap, use the HUD buttons to control stacking order. Click or drag any element to select it, then:

| Button | Action | Keyboard |
|--------|--------|----------|
| ▲▲ | Send to Front | — |
| ▲ | Send Forward one layer | — |
| ▼ | Send Backward one layer | — |
| ▼▼ | Send to Back | — |

A toast notification shows the new `z-index` value.

---

## Undo / Redo

| Keys | Action |
|------|--------|
| `Cmd/Ctrl + Z` | Undo last move/edit |
| `Cmd/Ctrl + Shift + Z` | Redo |

The undo stack holds up to 50 actions. Undo history is per-session (not persisted).

---

## Layout Grid (`G` key)

Press `G` while in move mode to toggle a 4×3 labeled grid overlay:

```
 A1  |  A2  |  A3  |  A4
─────┼──────┼──────┼─────
 B1  |  B2  |  B3  |  B4
─────┼──────┼──────┼─────
 C1  |  C2  |  C3  |  C4
```

- Zone labels appear on the slide so you can say "put X in zone B3" unambiguously
- When the grid is visible, annotation exports include the zone label
- `G` again turns the grid off

---

## Annotation Position Capture

While in **annotation mode** (`A` key), clicking the slide **background** (not an element) captures the coordinates of that point:

```
POSITION: left:45.2%, top:32.1% (on slide #15, type: lesson, year: 2023)
```

This is useful when you want to tell an AI where to place a *new* element that doesn't exist yet.

---

## Text Editing

Double-click any text element in move mode to edit it inline.

| Key | Effect |
|-----|--------|
| `Enter` | New bullet (when editing a `<li>`) |
| `Shift + Enter` | Line break within the element |
| `Backspace` on empty bullet | Delete that bullet |
| `Cmd/Ctrl + Enter` | Save and exit edit mode |
| `Escape` | Cancel edit (reverts changes) |

Text edits are saved as annotations (`TEXT "new content"`). Export annotations and give them to your AI to bake into the source `SECTIONS` array.

---

## Keyframe Animations

The scrubber timeline at the bottom of the screen (in move mode) supports per-element keyframe animations via the Web Animations API.

### Creating a Keyframe Animation

1. Enter move mode (`M`).
2. **Move the element to its starting position**, then drag the scrubber to the time you want (e.g., 0%).
3. Click **◆ KF** to capture the current transform at that time.
4. **Move the element to its ending position**, then drag the scrubber to the end time (e.g., 100%).
5. Click **◆ KF** again.
6. Two or more keyframes on the same element automatically build a WAAPI animation.

### Scrubber Controls

| Control | Effect |
|---------|--------|
| Drag scrubber | Scrub through the slide's animation timeline |
| ◆ markers on timeline | Click to seek to that keyframe's time |
| `◆ KF` button | Capture transform at current scrub time |
| `✕ KF` button | Delete keyframe at current scrub time |

Keyframes are persisted as annotations (`type: 'keyframe'`). Export your annotations to hand to an AI if you want them baked into source.

---

## Auto-Save of Moves

Every drag transform is automatically saved to `localStorage` as an annotation (`type: 'move'`). You don't need to manually export after each drag — the position persists across browser reloads immediately.

To share your layout changes with others (who won't have your localStorage), export annotations (`A` key → Export) and either:
- Give them to an AI to bake into source
- Or ask a collaborator to import the annotation export

---

## Tips

- **Shift+drag to scale** is great for making images larger without changing the template globally. Combined with `overflow:visible` (which move mode sets automatically), scaled-up elements won't clip.
- **The grid zone labels (A1–C4) persist in annotation exports** — your AI collaborator can read "Zone: B2" and place things in the right quadrant.
- **`Cmd+click` to select parent** is useful when a click keeps selecting a child element inside a container you want to move.
