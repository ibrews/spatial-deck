# Media

---

## Where to Put Files

Put all media in the `media/` directory. Subdirectories are fine and recommended:

```
media/
├── chapter-01/
│   ├── photo1.jpg
│   └── demo.mp4
└── chapter-02/
    └── screenshot.png
```

Reference files by relative path from the root: `'media/chapter-01/photo1.jpg'`.

---

## Supported Formats

| Format | Notes |
|--------|-------|
| `.jpg`, `.jpeg` | Recommended for photos |
| `.png` | Recommended for screenshots with transparency |
| `.webp` | Great compression, supported in all modern browsers |
| `.gif` | Animates in both direct `<img>` use and in the media cycler |
| `.mp4` | Preferred video format; plays everywhere |
| `.webm` | Good alternative; smaller files |
| `.mov` | Works but larger; convert to mp4 before committing |
| `.svg` | Scalable, no quality loss at any size |

---

## Resizing Images

GitHub has a 100MB file limit. Keep images under 2560px wide:

```bash
# Resize a single file in place
sips --resampleWidth 2560 media/photo.jpg

# Resize all JPGs in a folder
for f in media/project/*.jpg; do sips --resampleWidth 2560 "$f"; done
```

---

## Transcoding Videos

```bash
# Transcode large video (scale to 1280px wide, quality CRF 28)
ffmpeg -i input.mp4 -vf "scale=1280:-2" -crf 28 -preset fast output.mp4

# Quick check: will this fit GitHub's 100MB limit?
du -sh output.mp4
```

For YouTube clips and trimming, use the fleet tool — see [Import & Export Tools](08-import-export.md#video-clip-importer).

---

## Direct Image (`img: 'path'`)

The simplest option. Specify a relative path and the case study renders a standard `<img>` tag:

```javascript
{ title: 'My Project', img: 'media/project/hero.jpg', ... }
```

- No reveal animation, no cycling — just the image.
- If you want the pixelated reveal effect on a single image, use `MEDIA_CYCLER` with a one-item array instead.

---

## Media Cycler (`img: 'MEDIA_CYCLER'`)

The media cycler is a canvas-based gallery with a signature pixelated de-pixelation reveal effect. Use it when a case study has multiple images or a mix of images and video.

### Setup

1. Set `img: 'MEDIA_CYCLER'` on the case study in SECTIONS.
2. After the SECTIONS build loop (search for the end of the `SECTIONS.forEach` block), add an IIFE:

```javascript
(function(){
  const slide = allSlides.find(s =>
    s.querySelector?.('.case-title')?.textContent.includes('My Project'));
  if (!slide) return;
  buildMediaCycler(slide, [
    {type: 'image', src: 'media/project/photo1.jpg'},
    {type: 'image', src: 'media/project/photo2.jpg', flipH: true},
    {type: 'video', src: 'media/project/demo.mp4', loop: true},
  ], {imageDuration: 6000});
})();
```

### `buildMediaCycler` Options

```javascript
buildMediaCycler(slideElement, items, options)
```

| Option | Default | Description |
|--------|---------|-------------|
| `imageDuration` | `6000` | Milliseconds to hold each image before advancing |
| `portrait` | `false` | Use 9:16 canvas for vertical/portrait content |
| `enterDur` | `700` | Slide-in animation duration (ms) |
| `revealDur` | `1600` | Pixelated de-pixelation reveal duration (ms) |
| `exitDur` | `500` | Exit animation duration (ms) |

### Per-Item Flags

| Flag | Description |
|------|-------------|
| `flipH: true` | Mirror the image horizontally |
| `loop: true` | Loop a video continuously |

### Finding a Slide

Use any unique text from the case study title:
```javascript
// By case title
allSlides.find(s => s.querySelector?.('.case-title')?.textContent.includes('Your Title'))

// By slide index (0 = settings, 1 = cover, etc.)
allSlides[7]
```

### Keyboard Controls (while on a cycler slide)

| Key | Action |
|-----|--------|
| `Shift + →` | Next item |
| `Shift + ←` | Previous item |
| `Shift + ↑` | Resume auto-advance (if paused) |

---

## Embedded Iframe (`img: 'IFRAME:url'`)

Embed any web content directly in a case study slide:

```javascript
{ title: 'Live Demo', img: 'IFRAME:https://www.youtube.com/embed/VIDEO_ID', ... }
```

The `IFRAME:` prefix is stripped and the URL is placed in a responsive `<iframe>` with:
```html
allow="autoplay; fullscreen; xr-spatial-tracking"
```

### Common Sources

| Content | `img` value |
|---------|-------------|
| YouTube | `'IFRAME:https://www.youtube.com/embed/VIDEO_ID'` |
| Vimeo | `'IFRAME:https://player.vimeo.com/video/VIDEO_ID'` |
| Sketchfab | `'IFRAME:https://sketchfab.com/models/MODEL_ID/embed'` |
| Unreal Pixel Stream | `'IFRAME:https://your-server.com/stream'` |
| Any URL | `'IFRAME:https://example.com/page'` |

> **Note:** YouTube autoplay won't work unless the user has interacted with the page first (browser policy). Use `?autoplay=1&mute=1` in the YouTube embed URL to autoplay muted.

---

## GIFs

GIFs work in both direct and cycler contexts:

- **Direct `img: 'media/animation.gif'`**: renders as a normal `<img>` — GIF animates natively.
- **In a media cycler**: `buildMediaCycler` auto-detects `.gif` items and uses a cross-fading `<img>` rendering path (not canvas), so the GIF animates correctly.

```javascript
buildMediaCycler(slide, [
  {type: 'image', src: 'media/animation.gif'},
  {type: 'image', src: 'media/static.jpg'},
], {imageDuration: 4000});
```

---

## `placed` Layout — Multiple Images per Slide

For fine-grained positioning, use the `placed` layout instead of a media cycler. See [Content Authoring § Layout Types](02-content-authoring.md#layout-types).

---

## Offline Media

If you need the presentation to run completely offline (USB stick, no Wi-Fi):

1. Put all images and videos in `media/`.
2. Use the **📦 Export for Offline** button in the Settings slide — it patches the Three.js import map to point to a local `lib/` file and downloads the bundle.
3. Or manually: `curl -o lib/three.module.min.js "https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.min.js"` then update the import map in `index.html`.

Google Fonts are the other external dependency. If you need full offline font support, self-host the font file and replace the `@import url(...)` in the CSS.

---

## 3D Models (Three.js)

Three.js is already loaded via the import map. The bonus slide includes a working 3D monocle example — a procedural gold torus with teal glass that auto-rotates and supports click-drag interaction.

To load a GLTF/GLB model:

```javascript
const THREE = await import('three');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const loader = new GLTFLoader();
loader.load('media/model.glb', (gltf) => {
  scene.add(gltf.scene);
  // ... animate loop
});
```

See the bonus slide IIFE in `index.html` for a full lifecycle-managed example (init on slide enter, dispose on leave).
