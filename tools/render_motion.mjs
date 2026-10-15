// Render seekable HTML motion graphics (media/motion/*.html exposing window.seek(sec) + window.MOTION_END) to MP4 + poster PNG.
// Deterministic: every frame is seek()-ed, never screen-recorded, so output is identical run to run.
//   node tools/render_motion.mjs [name ...]            # default: every media/motion/*.html
//   PLAYWRIGHT_CORE=/path/to/node_modules/playwright-core FPS=30 node tools/render_motion.mjs lane
// Needs: Google Chrome, ffmpeg, and a playwright-core install (export_video.py's cache is tried first).
import { createRequire } from 'module';
import { execFileSync } from 'child_process';
import fs from 'fs'; import path from 'path'; import os from 'os';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const MOTION = path.join(ROOT, 'media/motion'), OUT = path.join(MOTION, 'mp4');
const cands = [process.env.PLAYWRIGHT_CORE, path.join(os.homedir(), '.cache/spatial-deck/video-deps/node_modules/playwright-core')].filter(Boolean);
const pwPath = cands.find(p => fs.existsSync(path.join(p, 'package.json')));
if (!pwPath) { console.error('playwright-core not found. Set PLAYWRIGHT_CORE=/abs/path/node_modules/playwright-core (or run tools/export_video.py once to install it).'); process.exit(2); }
const { chromium } = require(pwPath);
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const FPS = +(process.env.FPS || 30), HOLD = +(process.env.HOLD || 2);  // HOLD = seconds to hold the final frame
const names = process.argv.slice(2).length ? process.argv.slice(2) : fs.readdirSync(MOTION).filter(f => f.endsWith('.html')).map(f => f.replace(/\.html$/, ''));
fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ executablePath: CHROME, args: ['--hide-scrollbars'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, reducedMotion: 'no-preference' });
for (const n of names) {
  const url = 'file://' + path.join(MOTION, n + '.html') + '?t=0';
  await page.goto(url); await page.waitForFunction(() => typeof window.seek === 'function');
  await page.evaluate(() => document.fonts.ready);
  const end = await page.evaluate(() => window.MOTION_END);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'motion-' + n + '-'));
  const frames = Math.ceil(end * FPS);
  for (let i = 0; i <= frames; i++) {
    await page.evaluate(s => window.seek(s), Math.min(i / FPS, end));
    await page.screenshot({ path: path.join(tmp, String(i).padStart(5, '0') + '.png') });
  }
  const mp4 = path.join(OUT, n + '.mp4'), poster = path.join(OUT, n + '-poster.png');
  fs.copyFileSync(path.join(tmp, String(frames).padStart(5, '0') + '.png'), poster);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(tmp, '%05d.png'),
    '-vf', `tpad=stop_mode=clone:stop_duration=${HOLD},format=yuv420p`, '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-movflags', '+faststart', mp4]);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log(`${n}: ${frames + 1} frames @${FPS}fps -> ${path.relative(ROOT, mp4)} (${(fs.statSync(mp4).size / 1e6).toFixed(1)} MB)`);
}
await browser.close();
