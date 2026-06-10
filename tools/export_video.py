#!/usr/bin/env python3
"""Walkthrough video export — the whole deck, auto-played, as an MP4.

Unlike export_pdf.py (static pages), this records the LIVE deck: slide
transitions, multi-step builds, media-cycler reveals, videos, the
constellation map, 3D content — everything the browser renders. A headless
Chrome (driven by playwright-core via node) steps through every slide and
substep like a presenter would, recording the viewport; ffmpeg converts the
recording to a shareable H.264 MP4.

    python3 tools/export_video.py                          # deck.mp4 of index.html
    python3 tools/export_video.py --out talk.mp4 --dwell 4.5
    python3 tools/export_video.py --html ../my-talk/index.html
    python3 tools/export_video.py --url https://you.github.io/your-talk/
    python3 tools/export_video.py --gif hero.gif           # also emit a compact GIF

Requirements: Google Chrome (or CHROME_BIN), node + npm, ffmpeg. The one npm
package (playwright-core, drives Chrome and records) is auto-installed ONCE
into ~/.cache/spatial-deck/video-deps — never into this repo.

Known limits (reported after export): Web Audio SFX are not captured (the
recorder is video-only — lay a music bed on with ffmpeg afterwards); pacing is
fixed dwell-per-step, not your speaking pace.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture_slides import REPO, find_chrome

CACHE = Path.home() / ".cache" / "spatial-deck" / "video-deps"

RUNNER = r"""
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.SD_PW + '/playwright-core');
const cfg = JSON.parse(process.env.SD_CFG);
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  executablePath: cfg.chrome || undefined });
const ctx = await browser.newContext({
  viewport: { width: cfg.w, height: cfg.h },
  recordVideo: { dir: cfg.dir, size: { width: cfg.w, height: cfg.h } },
});
const page = await ctx.newPage();
await page.goto(cfg.url);
await page.waitForTimeout(cfg.startWait);
const info = await page.evaluate(() => {
  const s = [...document.querySelectorAll('#deck .slide')];
  let last = 0; s.forEach((el, i) => { if (el.dataset.hidden !== '1') last = i; });
  return { total: s.length, last };
});
// NOTE: the deck WRAPS to the cover when you advance past the last slide, so
// "press until nothing changes" never terminates. Instead: stop when we LAND
// on the last visible slide (playing out its substeps via the step
// indicator), and treat any hash decrease as a wrap => hard stop.
const state = () => page.evaluate(() => {
  const si = document.getElementById('step-indicator');
  return location.hash + '|' + (si ? si.innerHTML : '');
});
const hashIdx = (st) => { const h = st.split('|')[0].replace('#', '');
  return h === '' ? null : (h === '00' ? 0 : parseInt(h, 10)); };
let presses = 0, prev = await state(), prevIdx = hashIdx(prev);
const maxPresses = Math.max(40, info.total * 14);
while (presses < maxPresses) {
  await page.keyboard.press('ArrowRight'); presses++;
  await page.waitForTimeout(120); // let hash/HUD update
  const st = await state();
  const idx = hashIdx(st);
  if (idx !== null && prevIdx !== null && idx < prevIdx) break; // wrapped past the end
  const slideChanged = st.split('|')[0] !== prev.split('|')[0];
  prev = st; if (idx !== null) prevIdx = idx;
  await page.waitForTimeout(slideChanged ? cfg.dwell : cfg.stepDwell);
  if (idx !== null && idx >= info.last) {
    // On the last slide. Play out substeps: press while the step indicator
    // changes; an empty/unchanged indicator means the next press would wrap.
    while (presses < maxPresses) {
      const before = await state();
      if (before.split('|')[1] === '') break;        // no substeps -> done
      await page.keyboard.press('ArrowRight'); presses++;
      await page.waitForTimeout(120);
      const after = await state();
      if (hashIdx(after) !== idx) break;             // wrapped -> done
      if (after === before) break;                   // substeps exhausted
      await page.waitForTimeout(cfg.stepDwell);
    }
    break;
  }
}
await page.waitForTimeout(cfg.tail);
const video = page.video();
await ctx.close(); await browser.close();
console.log(JSON.stringify({ webm: await video.path(), presses, slides: info.total }));
"""


def ensure_playwright():
    env = os.environ.get("SD_PLAYWRIGHT_DIR")
    candidates = [Path(env) if env else None,
                  CACHE / "node_modules",
                  ]
    for c in candidates:
        if c and (c / "playwright-core" / "package.json").exists():
            return c
    npm = shutil.which("npm")
    if not npm:
        sys.exit("error: node/npm required for video export (brew install node)")
    print(f"installing playwright-core into {CACHE} (one-time)…", file=sys.stderr)
    CACHE.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([npm, "install", "playwright-core", "--prefix", str(CACHE),
                        "--no-fund", "--no-audit"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"error: npm install playwright-core failed:\n{r.stderr[-500:]}")
    return CACHE / "node_modules"


def main():
    ap = argparse.ArgumentParser(description="Record an auto-played walkthrough of the deck as MP4")
    ap.add_argument("--html", default=str(REPO / "index.html"))
    ap.add_argument("--url", help="record a live URL instead of a local file")
    ap.add_argument("--out", default="deck.mp4")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--dwell", type=float, default=3.5, help="seconds to hold each new slide (default 3.5)")
    ap.add_argument("--step-dwell", type=float, default=1.8, help="seconds between substeps (default 1.8)")
    ap.add_argument("--start-wait", type=float, default=3.0, help="seconds on the cover before starting")
    ap.add_argument("--tail", type=float, default=2.5, help="seconds to hold the final slide")
    ap.add_argument("--crf", type=int, default=21)
    ap.add_argument("--gif", metavar="PATH", help="also emit a compact GIF (960px, 12fps)")
    ap.add_argument("--keep-webm", metavar="PATH", help="keep the raw recording here")
    args = ap.parse_args()

    node = shutil.which("node") or sys.exit("error: node required (brew install node)")
    ffmpeg = shutil.which("ffmpeg") or sys.exit("error: ffmpeg required (brew install ffmpeg)")
    chrome = find_chrome()
    node_modules = ensure_playwright()

    url = args.url or Path(args.html).resolve().as_uri()
    with tempfile.TemporaryDirectory(prefix="sd-video-") as tmp:
        runner = Path(tmp) / "runner.mjs"
        runner.write_text(RUNNER)
        cfg = {"url": url, "w": args.width, "h": args.height, "dir": tmp,
               "dwell": int(args.dwell * 1000), "stepDwell": int(args.step_dwell * 1000),
               "startWait": int(args.start_wait * 1000), "tail": int(args.tail * 1000),
               "chrome": chrome}
        env = {**os.environ, "SD_CFG": json.dumps(cfg), "SD_PW": str(node_modules)}
        print(f"recording walkthrough of {url} at {args.width}x{args.height}…", file=sys.stderr)
        r = subprocess.run([node, str(runner)], capture_output=True, text=True, env=env,
                           timeout=3600)
        if r.returncode != 0:
            sys.exit(f"error: recorder failed:\n{r.stderr[-800:]}")
        out_line = [l for l in r.stdout.strip().splitlines() if l.startswith("{")][-1]
        result = json.loads(out_line)
        webm = result["webm"]
        print(f"recorded {result['presses']} advances across {result['slides']} slides", file=sys.stderr)

        if args.keep_webm:
            shutil.copy(webm, args.keep_webm)
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", webm,
                        "-c:v", "libx264", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", args.out], check=True)
        if args.gif:
            subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", webm,
                            "-vf", "fps=12,scale=960:-1:flags=lanczos,split[a][b];"
                                   "[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                            args.gif], check=True)

    dur = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error",
                          "-show_entries", "format=duration", "-of", "csv=p=0", args.out],
                         capture_output=True, text=True).stdout.strip()
    size_mb = Path(args.out).stat().st_size / 1e6
    print(f"wrote {args.out} — {float(dur or 0):.0f}s, {size_mb:.1f} MB")
    print("\n── Fidelity notes ──")
    print("  · everything the browser renders is captured live (transitions, builds,")
    print("    cyclers, videos, map, 3D)")
    print("  · Web Audio SFX are NOT captured — recorder is video-only; add a music")
    print(f"    bed with: ffmpeg -i {args.out} -i music.mp3 -c:v copy -shortest out.mp4")
    print("  · pacing is fixed dwell-per-step (--dwell/--step-dwell), not speech-timed")


if __name__ == "__main__":
    main()
