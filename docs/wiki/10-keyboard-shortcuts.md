# Keyboard Shortcuts

Complete reference for every key, gesture, and URL parameter.

---

## Navigation

| Key / Action | Effect |
|-------------|--------|
| `→` `Space` `PageDown` | Next step or next slide |
| `←` `PageUp` | Previous step or previous slide |
| `Home` | First slide |
| `End` | Last slide |

---

## Presentation Mode

| Key | Effect |
|-----|--------|
| `H` | Toggle all UI chrome (hide/show for presenting) |
| `F` or `F11` | Fullscreen (browser-native) |

---

## Presenter Tools

| Key | Effect |
|-----|--------|
| `N` | Open/close Presenter Popup (second window with notes + timer) |
| `Shift + N` | Toggle inline notes drawer |
| `Shift + P` | Toggle split presenter view (deck top 58%, notes bottom 42%) |

---

## Search

| Key | Effect |
|-----|--------|
| `/` or `Cmd/Ctrl + F` | Open search overlay (full-text across all slides) |
| `Escape` | Close search |

---

## Move Mode (`M` to toggle)

| Key / Action | Effect |
|-------------|--------|
| `M` | Enter/exit move mode |
| `Click` element | Select element (blue outline) |
| `Drag` selected | Translate (move) |
| `Shift + Drag` | Scale element |
| `Alt/Option + Drag` | Rotate element |
| `Cmd/Ctrl + Click` | Select parent element |
| `Cmd/Ctrl + Z` | Undo |
| `Cmd/Ctrl + Shift + Z` | Redo |
| `G` | Toggle 4×3 layout grid (A1–C4 zone labels) |
| `Double-click` text | Enter inline text editing |

### Z-Order Buttons (HUD)

| Button | Effect |
|--------|--------|
| ▲▲ | Send selected element to front |
| ▲ | Send forward one layer |
| ▼ | Send backward one layer |
| ▼▼ | Send to back |

### Scrubber / Keyframe Buttons (HUD)

| Control | Effect |
|---------|--------|
| Drag scrubber | Scrub animation timeline |
| ◆ on timeline | Click to seek to keyframe |
| `◆ KF` button | Capture transform at current scrub time |
| `✕ KF` button | Delete keyframe at current scrub time |

---

## Text Editing (double-click in Move Mode)

| Key | Effect |
|-----|--------|
| `Enter` | New bullet (in a `<li>`) |
| `Shift + Enter` | Line break within element |
| `Backspace` on empty bullet | Delete bullet |
| `Cmd/Ctrl + Enter` | Save and exit |
| `Escape` | Cancel (revert changes) |

---

## Annotation Mode (`A` to toggle)

| Key / Action | Effect |
|-------------|--------|
| `A` | Enter/exit annotation mode |
| Click any element | Add/edit note on that element |
| Click slide background | Capture `left:X%, top:Y%` position coordinates |
| Export button (panel) | Copy all annotations as markdown |

---

## Media Cycler Controls (on a cycler slide)

| Key | Effect |
|-----|--------|
| `Shift + →` | Next image/video |
| `Shift + ←` | Previous image/video |
| `Shift + ↑` | Resume auto-advance (if paused) |

---

## Mobile Gestures

| Gesture | Effect |
|---------|--------|
| Quick tap (< 15px, < 300ms) | Advance step or slide |
| Swipe left | Next slide |
| Swipe right | Previous slide |
| 👁 button (top right) | Toggle UI chrome |

---

## URL Parameters

| URL | Mode |
|-----|------|
| `index.html` | View mode — clean, no edit chrome |
| `index.html?edit` | Edit mode — all chrome, starts at Settings (slide 0) |
| `index.html?edit#5` | Edit mode starting at slide 5 |
| `index.html?view` | Explicit view mode (same as default) |
| `index.html?vertical` | Vertical scroll — slides stack top-to-bottom |
| `index.html?landscape` | Shows rotate-to-landscape prompt on portrait phones |
| `index.html?notes` | Phone speaker companion view |
| `index.html#N` | Jump to slide N (0-indexed; 0 = settings, 1 = cover) |
| `index.html#0` or `#00` | Settings slide |

---

## Quick Mode Reference

| You want to… | Do this |
|-------------|---------|
| Present cleanly | `H` to hide chrome, `→` to advance |
| Edit slide positions | `M` to enter move mode, drag |
| Leave notes for AI | `A` to annotate, Export to copy markdown |
| Open speaker notes | `N` for popup, `Shift+N` for drawer |
| Change theme | `?edit` URL, Settings slide |
| Find a specific slide | `/` to search |
| See all slides | Click the grid icon (top right) |
| Hide a slide | Grid → `Ctrl/Cmd + Click` thumbnail |
