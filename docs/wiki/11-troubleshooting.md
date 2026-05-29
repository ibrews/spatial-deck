# Troubleshooting

---

## Slides Don't Update After Editing SECTIONS

**Cause:** Browser cached the old version.  
**Fix:** Hard-reload with `Cmd/Ctrl + Shift + R`. If that doesn't work, open DevTools → Application → Clear Storage → Clear site data.

---

## The Constellation Map Doesn't Appear / Three.js Error

**Cause:** Chrome blocks ES module imports from `file://` URLs due to CORS restrictions.  
**Fix:** Serve the file locally:
```bash
cd /path/to/your-deck
python3 -m http.server 8080
# Open http://localhost:8080
```

Firefox and Safari don't have this restriction — they work from `file://` directly.

---

## Audio Doesn't Play on First Slide

**Cause:** Browser policy requires user interaction before `AudioContext` can start.  
**Fix:** This is expected. After the user has pressed any key or clicked anything, audio works fine. Make sure your audio calls are wrapped in `try/catch` so a blocked first play doesn't throw an uncaught error.

---

## GIF Not Animating in Media Cycler

**Cause:** Older sessions or documentation may say "GIFs don't animate on canvas — convert to MP4." This was true before 2026-05. It is **no longer true.**

**Current behavior:** `buildMediaCycler` auto-detects `.gif` items and uses a cross-fading `<img>` rendering path (not canvas), so GIFs animate correctly. If your GIF isn't animating, check:
1. The file path is correct and the file exists
2. You're using the `{type: 'image', src: 'file.gif'}` syntax (not `type: 'video'`)
3. The GIF itself isn't a single-frame GIF

---

## Media File Won't Load

**Check these in order:**
1. **Path is correct** — paths are relative to `index.html`, e.g. `'media/project/photo.jpg'` not `'/media/project/photo.jpg'`
2. **File exists** — `ls media/project/photo.jpg`
3. **File isn't too large** — browsers struggle with images over ~10MB; resize with `sips --resampleWidth 2560 file.jpg`
4. **Video format** — `.mp4` with H.264 codec works everywhere; `.mov` may not play in all browsers; convert: `ffmpeg -i in.mov -c:v libx264 out.mp4`

---

## `git push` Rejected (File Too Large)

**Cause:** GitHub has a 100MB file limit per file.  
**Fix:**
```bash
# Check what's large
find . -size +90M -not -path './.git/*'

# Compress a video
python3 tools/import_video_clip.py large-video.mp4 --start 0:00 --end 99:00 \
    --max-mb 95 --out compressed.mp4

# If already committed: remove from history (destructive — backup first)
git filter-repo --path large-file.mp4 --invert-paths
git push --force
```

For ongoing large file management, consider Git LFS.

---

## Settings Aren't Saving / Resetting Unexpectedly

**Cause:** `localStorage` is per-origin. If you're opening the file from different paths (e.g. `file:///Users/alex/deck/index.html` vs `http://localhost:8080`), they have separate storage.

**Fix:** Stick to one URL for your working session. If settings keep resetting across machines, use the annotation export + "bake into source" workflow to persist settings in the code (see [AI Workflow — Settings Round-Trip](09-ai-workflow.md#settings-round-trip)).

---

## Move-Mode Transforms Not Persisting After Reload

**Cause:** This is expected! Move-mode transforms are saved as annotations to `localStorage`, which is per-browser. Someone else opening the file gets a clean state.

**Fix:** To share layout changes with others:
1. Export annotations (`A` → Export)
2. Give the export to an AI collaborator with "bake these transforms into source"
3. The AI updates inline `style` attributes in the generated slide DOM

---

## Curly Quotes Breaking JavaScript

**Cause:** The Edit tool (and some text editors) sometimes convert straight ASCII `'` into Unicode curly quotes (`'`/`'`) in replacement text. JavaScript doesn't accept curly quotes as string delimiters → syntax error.

**Symptoms:** A JS error like `Unexpected token '` or `Unterminated string literal` on a line you just edited.

**Fix:**
```bash
# Check for curly quotes in your JS
grep -n '[''']' index.html | head -20

# Replace with a Python one-liner
python3 -c "
data = open('index.html', 'rb').read()
data = data.replace('‘'.encode(), b\"'\").replace('’'.encode(), b\"'\")
open('index.html', 'wb').write(data)
"
```

---

## Slide Grid Shows Wrong Slide Count

**Cause:** Hidden slides or parked slides can shift the visual count.

**Fix:** The counter at top-left shows the position in the *visible* navigation sequence, not the raw DOM index. This is intentional — hidden slides don't count toward the public slide number.

---

## Speaker Notes Not Showing in Presenter Popup

**Check:**
1. `notes` field is present in the relevant SECTIONS entry (both `lesson.notes` and `cases[i].notes` are separate)
2. The popup was opened **after** page load (it syncs via BroadcastChannel — if you open it before the deck loads, it may miss the first update; navigate once to sync)
3. Both windows are in **the same browser** on the same machine (BroadcastChannel is intra-browser only; for cross-device use the `?notes` phone companion with cloud sync)

---

## `?notes` Phone View Not Syncing

**Cause:** BroadcastChannel only works within the same browser on the same device. The `?notes` view on your phone can't communicate directly with the deck on your laptop.

**Fix:** Set up cloud sync via Google Apps Script. See `tools/SETUP_NOTES_SYNC.md` for the full setup guide.

---

## Import Script: "Connection refused" or Fleet Errors

**Cause:** The LLM fleet (Ollama on Sam/Archie/Lenny) isn't reachable.

**Fix:** Pass `--no-llm` to any importer to skip the normalization step:
```bash
python3 tools/import_pptx.py deck.pptx --no-llm
```

You'll get raw extracted text without bullet tightening — still useful. Or start the Ollama service: `ollama serve` on the appropriate machine.

---

## Transition Animation Looks Choppy

**Cause:** High-resolution media or background styles (Aurora, Nebula, etc.) competing for GPU.

**Fix:**
- Try the "None" or "Fade" transition (Settings slide) — less expensive than "Slide"
- Set background style to "None" during performance-sensitive presentations
- Ensure videos in media cyclers are 1280px wide or less

---

## Page Loads Blank / No Slides

**Cause:** JavaScript syntax error in SECTIONS (usually a stray comma, missing bracket, or curly quote in a string).

**Fix:**
1. Open DevTools console (`Cmd/Ctrl + Option + J`)
2. Look for a red error, click the line number to see where
3. Common culprits: unclosed string, extra comma after the last item in an array, HTML tag in a bullet that's not properly escaped

The `.claude/hooks/validate-js.sh` hook (if present) catches these automatically during edits via Claude Code.
