// Generic-tells lint: flags the stock "AI deck" look in a rendered Spatial Deck.
// It loads the deck in headless Chrome (?print, so every visible slide is laid out) with the look you name, and reads
// COMPUTED styles, so it judges what the audience sees, not what the CSS source happens to contain. It also scans
// seekable motion graphics for glow filters and the neon palette, and says whether they can be recolored (look.js).
//   node tools/lint_look.mjs [path/to/index.html] [--look sheet] [--query "theme=sheet"] [--max 1] [--json]
// Exit 1 when more tells fire than --max (default 1). Tells and why each one reads as generic: styles/README.md.
import { createRequire } from 'module';
import fs from 'fs'; import path from 'path'; import os from 'os';
const require = createRequire(import.meta.url);
const args = process.argv.slice(2); const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const html = path.resolve(args.find(a => a.endsWith('.html')) || path.join(ROOT, 'index.html'));
const look = opt('--look', ''), extra = opt('--query', ''), MAX = +opt('--max', 1), JSONOUT = args.includes('--json');
const cands = [process.env.PLAYWRIGHT_CORE, path.join(os.homedir(), '.cache/spatial-deck/video-deps/node_modules/playwright-core')].filter(Boolean);
const pw = cands.find(p => fs.existsSync(path.join(p, 'package.json')));
if (!pw) { console.error('playwright-core not found: set PLAYWRIGHT_CORE, or run tools/export_video.py once to install it.'); process.exit(2); }
const { chromium } = require(pw);
const browser = await chromium.launch({ executablePath: process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = []; page.on('pageerror', e => errors.push(e.message));
const q = ['print', look && 'look=' + look, extra].filter(Boolean).join('&');
await page.goto('file://' + html + '?' + q); await page.waitForTimeout(1200); await page.evaluate(() => document.fonts.ready);
const found = await page.evaluate(() => {
  const NEON = [[0, 212, 255], [167, 139, 250], [124, 58, 237], [0, 255, 255], [168, 85, 247], [236, 72, 153]];
  const AI_FONTS = /^(space grotesk|inter|outfit|poppins|manrope|sora|plus jakarta sans|dm sans)$/i;
  const rgbs = s => [...(s || '').matchAll(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/g)].map(m => [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]]);
  const neon = c => c[3] > .25 && NEON.some(n => Math.hypot(c[0] - n[0], c[1] - n[1], c[2] - n[2]) < 60);
  const vis = e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > .05 && r.width > 2 && r.height > 2; };
  const inDeck = e => e.closest('#deck .slide') || e.closest('.bg');
  const T = { starfield: [], 'gradient-text': [], 'neon-palette': [], glow: [], 'pill-tags': [], 'ai-font': [], 'radial-glow-bg': [], glass: [] };
  const name = e => (e.id ? '#' + e.id : '') + (typeof e.className === 'string' && e.className ? '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.') : '') || e.tagName.toLowerCase();
  const stars = document.getElementById('stars'); if (stars && vis(stars)) T.starfield.push('canvas#stars');
  document.querySelectorAll('.bg *, .bg').forEach(e => { if (!vis(e)) return; const b = getComputedStyle(e).backgroundImage; if (/radial-gradient/.test(b) && rgbs(b).some(neon)) T['radial-glow-bg'].push(name(e)); });
  let neonCount = 0; const fontSeen = {};
  document.querySelectorAll('#deck .slide *').forEach(e => {
    if (!vis(e) || !inDeck(e) || e.closest('.slide-settings')) return;
    const s = getComputedStyle(e); const txt = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (txt && /text/.test(s.webkitBackgroundClip + s.backgroundClip) && /gradient/.test(s.backgroundImage)) T['gradient-text'].push(name(e));
    if (txt && (neon(rgbs(s.color)[0] || [0, 0, 0, 0]))) neonCount++;
    const sh = s.boxShadow + ' ' + s.textShadow + ' ' + s.filter;
    if (/(\d+)px/.test(sh) && [...sh.matchAll(/(\d+(?:\.\d+)?)px/g)].some(m => +m[1] >= 16) && rgbs(sh).some(c => c[3] > .2 && !(c[0] < 40 && c[1] < 40 && c[2] < 40))) T.glow.push(name(e));
    const r = e.getBoundingClientRect(), rad = parseFloat(s.borderTopLeftRadius) || 0;
    if (txt && rad >= r.height / 2 - 1 && r.height < 70 && r.width < 420 && (rgbs(s.backgroundColor).some(c => c[3] > 0 && c[3] < .4) || rgbs(s.borderTopColor).some(neon))) T['pill-tags'].push(name(e));
    if (/blur\(/.test(s.backdropFilter || '') && r.width > 120) T.glass.push(name(e));
    if (txt && /^H[1-3]$/.test(e.tagName)) { const f = s.fontFamily.split(',')[0].replace(/["']/g, '').trim(); fontSeen[f] = (fontSeen[f] || 0) + 1; }
  });
  if (neonCount >= 3) T['neon-palette'].push(`${neonCount} text elements in cyan/violet/magenta`);
  const top = Object.entries(fontSeen).sort((a, b) => b[1] - a[1])[0];
  if (top && AI_FONTS.test(top[0])) T['ai-font'].push(`headings set in ${top[0]} (${top[1]})`);
  const uniq = a => [...new Set(a)]; Object.keys(T).forEach(k => T[k] = uniq(T[k]));
  return { look: document.body.dataset.look || 'noir', tells: T };
});
// the background layer is hidden in ?print, so check it on one slide as presented (?shot=1, the cover)
await page.goto('file://' + html + '?' + ['shot=1', look && 'look=' + look, extra].filter(Boolean).join('&')); await page.waitForTimeout(900);
const bgTells = await page.evaluate(() => {
  const NEON = [[0, 212, 255], [167, 139, 250], [124, 58, 237], [168, 85, 247], [236, 72, 153]];
  const rgbs = s => [...(s || '').matchAll(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/g)].map(m => [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]]);
  const neon = c => NEON.some(n => Math.hypot(c[0] - n[0], c[1] - n[1], c[2] - n[2]) < 60);
  const vis = e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > .05 && r.width > 2; };
  const out = { starfield: [], 'radial-glow-bg': [] }; const st = document.getElementById('stars');
  if (st && vis(st) && [...document.querySelectorAll('.bg *')].every(e => e === st || vis(st))) out.starfield.push('canvas#stars');
  document.querySelectorAll('.bg, .bg *').forEach(e => { if (!vis(e)) return; const b = getComputedStyle(e).backgroundImage; if (/radial-gradient/.test(b) && rgbs(b).some(neon)) out['radial-glow-bg'].push((e.className || e.tagName).toString().split(' ')[0]); });
  return out;
});
for (const k of Object.keys(bgTells)) found.tells[k] = [...new Set([...found.tells[k], ...bgTells[k]])];
await browser.close();
// motion graphics next to the deck: glow filters, neon hexes, and whether look.js can recolor them
const mdir = path.join(path.dirname(html), 'media', 'motion'); const motion = [];
if (fs.existsSync(mdir)) for (const f of fs.readdirSync(mdir).filter(f => f.endsWith('.html'))) {
  const t = fs.readFileSync(path.join(mdir, f), 'utf8');
  const glow = (t.match(/<filter[\s\S]*?feGaussianBlur/g) || []).length, neonHex = (t.match(/#(00d4ff|a78bfa|7c3aed)/gi) || []).length;
  if (glow || neonHex) motion.push({ file: f, glowFilters: glow, neonHex, recolorable: /src="look\.js"/.test(t) });
}
const fired = Object.entries(found.tells).filter(([, v]) => v.length);
const motionUnfixed = motion.filter(m => !m.recolorable || found.look === 'noir');
const report = { html: path.relative(process.cwd(), html), look: found.look, tellsFired: fired.length, tells: Object.fromEntries(fired), motion, pageErrors: errors };
if (JSONOUT) console.log(JSON.stringify(report, null, 2));
else {
  console.log(`lint_look: ${report.html} · look=${found.look} · ${fired.length} generic tell(s)`);
  for (const [k, v] of fired) console.log(`  ✗ ${k}: ${v.slice(0, 4).join(', ')}${v.length > 4 ? ` (+${v.length - 4})` : ''}`);
  if (motion.length) console.log(`  motion: ${motion.length} graphic(s) use glow/neon; ${motionUnfixed.length ? motionUnfixed.length + ' shown unrecolored in this look' : 'all recolored by look.js in this look'}`);
  if (errors.length) console.log('  page errors: ' + errors.join(' | '));
  console.log(fired.length > MAX ? `FAIL (more than --max ${MAX})` : 'ok');
}
process.exit(fired.length > MAX || errors.length ? 1 : 0);
