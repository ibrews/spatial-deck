// Headless behavioral sweep of the deck: walks every slide at a given viewport and
// records text that overflows the stage, images that never decoded, videos that
// won't play, lazy-iframe state, console errors and failed requests. Screenshots
// each slide and tiles them into 3x3 contact sheets you can actually look at.
//
// WHY THIS IS NODE AND EVERY OTHER TOOL HERE IS PYTHON: the rest of tools/ drives
// headless Chrome through its CLI (see capture_slides.py), which can screenshot and
// dump the DOM but cannot read layout geometry. Detecting clipped text needs
// getBoundingClientRect() per element at a real viewport, which needs a driver that
// can evaluate in-page. The alternative — teaching index.html an ?audit mode that
// computes the geometry itself and writes a manifest into the DOM, the way ?print
// already writes #sd-print-manifest — would keep this in Python, but it puts audit
// code in the page every viewer loads. A dev-only tool that ships nothing to
// viewers was the cheaper trade. Revisit if Playwright becomes a burden.
//
// Usage (needs: npm i playwright && npx playwright install chromium):
//   node tools/sweep_deck.mjs <url> <outDir> [width] [height] [tag]
//   node tools/sweep_deck.mjs http://localhost:8000/ /tmp/sweep 375 812 phone
//
// Exit code is 0 for PASS, 1 for FAIL, so CI can gate on it.
//
// --steps: also walk every SUBSTEP. On each slide it presses the real ArrowRight key until the slide index changes,
// screenshots every substep into the contact sheets (named NNN-sK), and checks the step contract:
//   declared  = what the deck promises (a module's resolved `steps`, else the slide's slideSteps length, else 0)
//   reachable = how many ArrowRight presses stayed on the slide
//   frame     = what an iframe module reported in its ready message
// declared != reachable, frame != declared, or a step whose screenshot is identical to the one before it (a dead
// step) fails the run. The sweep loads the deck with ?reduced so every beat jumps to its final frame and a step
// screenshot is deterministic, and hides the animated star background, the step indicator and the playing spinner
// (they would make every frame differ).
// --live keeps real-time motion instead (sheets show mid-animation frames; dead-step detection is then a weak signal).
//   node tools/sweep_deck.mjs http://localhost:8000/ /tmp/sweep 1920 1080 steps --steps
//
// ── On the verdict, and why it is not just "zero errors" ──────────────────────
// This tool's ancestor computed verdict = (errors==0 && failed==0 && problems==0).
// That verdict was structurally unreachable: the deck probes for an OPTIONAL,
// gitignored notes-config.json on every load (absent = local-only presenter mode,
// by design — HANDOFF_PROMPT.md), and a browser logs a 404 for it that no
// try/catch in page can suppress. So every run reported FAIL — including the runs
// that proved the 2026-10-08 small-screen clipping fix worked with 0 clipped
// slides. A red light that is always on carries no information and trains whoever
// reads it to ignore the tool.
//
// So: expected noise is declared, classified out of the verdict, and still printed.
// And an expected-noise entry that does NOT fire is reported too (expectedNoiseAbsent)
// — an allowlist nobody notices has gone stale is the next version of this same bug.
import { mkdirSync, rmSync, writeFileSync, existsSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import os from 'node:os';
import path from 'node:path';

// playwright if installed, else the playwright-core that tools/export_video.py caches, driving system Chrome.
async function loadChromium() {
  try { return { chromium: (await import('playwright')).chromium, exe: undefined }; } catch (e) { /* fall through */ }
  const req = createRequire(import.meta.url);
  const cands = [process.env.PLAYWRIGHT_CORE, path.join(os.homedir(), '.cache/spatial-deck/video-deps/node_modules/playwright-core')].filter(Boolean);
  const pw = cands.find((p) => existsSync(path.join(p, 'package.json')));
  if (!pw) { console.error('sweep_deck: needs playwright (npm i playwright) or PLAYWRIGHT_CORE=/abs/node_modules/playwright-core'); process.exit(2); }
  return { chromium: req(pw).chromium, exe: process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' };
}
const { chromium, exe: CHROME_EXE } = await loadChromium();

// Known-benign network noise. Keep this list SHORT and give every entry a reason:
// anything here is invisible to the verdict, so a wrong entry hides a real defect.
const EXPECTED_NOISE = [
  {
    id: 'notes-config-404',
    match: (s) => /notes-config\.json/.test(s),
    why: 'Optional presenter-sync config, gitignored by design. Absent => local-only notes mode (HANDOFF_PROMPT.md, tools/SETUP_NOTES_SYNC.md). The 404 is the feature detection.',
  },
];
// Third-party embeds whose request failures say nothing about this deck.
const THIRD_PARTY = /youtube|youtu\.be|google|doubleclick|ytimg|gstatic/;

const FLAGS = new Set(process.argv.slice(2).filter((a) => a.startsWith('--')));
const STEPS = FLAGS.has('--steps'), LIVE = FLAGS.has('--live');
const [url, outDir, wStr, hStr, tagArg] = process.argv.slice(2).filter((a) => !a.startsWith('--'));
if (!url || !outDir) {
  console.error('usage: node tools/sweep_deck.mjs <url> <outDir> [width] [height] [tag]');
  process.exit(2);
}
const W = +(wStr || 1920), H = +(hStr || 1080);
const tag = tagArg || `${W}x${H}`;
const frames = path.join(outDir, 'f-' + tag);
rmSync(frames, { recursive: true, force: true });
mkdirSync(frames, { recursive: true });

const b = await chromium.launch({ executablePath: CHROME_EXE, args: ['--hide-scrollbars', '--autoplay-policy=no-user-gesture-required'] });
const p = await b.newPage({ viewport: { width: W, height: H } });
const errs = [], failed = [];
p.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
p.on('console', (m) => {
  if (m.type() !== 'error') return;
  // A subresource 404 logs "Failed to load resource: ... 404" with NO url in the
  // text — the url is only in location(). Without it, an expected-noise rule can
  // classify the failed REQUEST and still be unable to classify the console error
  // the same 404 produced, which is precisely how the old verdict stayed stuck on
  // FAIL. Append the location so one rule covers both.
  const loc = m.location()?.url || '';
  errs.push('console: ' + m.text() + (loc ? ' @ ' + loc : ''));
});
p.on('requestfailed', (r) => {
  const u = r.url();
  if (!THIRD_PARTY.test(u)) failed.push(u + ' :: ' + (r.failure()?.errorText || '?'));
});
p.on('response', (r) => {
  if (r.status() >= 400 && !THIRD_PARTY.test(r.url())) failed.push(r.url() + ' :: HTTP ' + r.status());
});

const q = 'view' + (STEPS && !LIVE ? '&reduced' : '');
await p.goto(url + (url.includes('?') ? '&' : '?') + q, { waitUntil: 'load' });
// The step indicator and the 'playing' spinner change on every click; hidden so a dead step really looks identical.
if (STEPS) await p.addStyleTag({ content: '.bg,#stars,#step-indicator,#nav-playing{visibility:hidden!important}' });
await p.waitForTimeout(2500);
const total = await p.evaluate(() => document.querySelectorAll('.slide').length);
const shots = [], per = [];
const MAX_STEPS = 40;
// Press ArrowRight until the slide index changes; screenshot each substep; compare against what was declared.
async function walkSteps(i, firstShot) {
  const meta = await p.evaluate((n) => {
    const s = allSlides[n], ss = slideSteps.get(s);
    const mod = s.dataset.sdMod || null;
    return { mod, hidden: s.dataset.hidden === '1',
      declared: s.dataset.sdSteps != null ? +s.dataset.sdSteps : (ss ? ss.steps.length : 0),
      frame: s.dataset.sdFrameSteps != null ? +s.dataset.sdFrameSteps : null,
      arrowSubstep: window._arrowSubstep !== false };
  }, i);
  const r = { ...meta, reachable: 0, dead: [], shots: [] };
  if (meta.hidden) { r.skipped = 'hidden'; return r; }
  let prev = readFileSync(firstShot);
  for (let k = 1; k <= MAX_STEPS; k++) {
    await p.keyboard.press('ArrowRight');
    await p.waitForTimeout(LIVE ? 1500 : 650);
    const cur = await p.evaluate(() => current);
    if (cur !== i) break;
    r.reachable = k;
    const f = path.join(frames, String(i).padStart(3, '0') + '-s' + k + '.png');
    await p.screenshot({ path: f });
    shots.push(f); r.shots.push(path.basename(f));
    const buf = readFileSync(f);
    if (buf.equals(prev)) r.dead.push(k);
    prev = buf;
  }
  if (r.reachable === MAX_STEPS) r.runaway = true;
  const why = [];
  if (r.reachable !== r.declared) why.push(`declared ${r.declared} step(s), reachable ${r.reachable}`);
  if (r.frame !== null && r.frame !== r.declared) why.push(`frame reports ${r.frame} step(s), deck declares ${r.declared}`);
  if (r.dead.length) why.push(`dead step(s) ${r.dead.join(',')}: nothing on screen changed`);
  if (r.runaway) why.push(`still on the slide after ${MAX_STEPS} presses`);
  if (!r.arrowSubstep && r.declared) why.push('arrow substeps are switched off in Settings; steps cannot be reached');
  r.problems = why;
  return r;
}
for (let i = 0; i < total; i++) {
  await p.evaluate((n) => window.goTo && window.goTo(n), i);
  await p.waitForTimeout(900);
  // Wait (max 10 s) until the active slide's images have decoded and its videos can play,
  // so "broken image" means broken rather than "not finished yet".
  await p.waitForFunction(() => {
    const s = document.querySelector('.slide.active');
    if (!s) return true;
    const imgsOk = [...s.querySelectorAll('img')].every((im) => im.complete && im.naturalWidth > 0);
    const vidsOk = [...s.querySelectorAll('video')].every((v) => v.readyState >= 3);
    return imgsOk && vidsOk;
  }, null, { timeout: 10000, polling: 250 }).catch(() => {});
  await p.waitForTimeout(700);
  const info = await p.evaluate(async () => {
    const s = document.querySelector('.slide.active');
    if (!s) return { err: 'no active slide' };
    const r = {
      type: s.dataset.type, year: s.dataset.year,
      title: (s.querySelector('h1,h2,h3')?.textContent || '').trim().slice(0, 60),
      overflow: [], badImg: [], videos: [], iframes: [],
    };
    s.querySelectorAll('h1,h2,h3,p,li').forEach((e) => {
      const bb = e.getBoundingClientRect();
      if (bb.width && (bb.bottom > innerHeight + 2 || bb.right > innerWidth + 2 || bb.top < -2 || bb.left < -2)) {
        r.overflow.push(e.tagName + ':' + e.textContent.trim().slice(0, 40));
      }
    });
    s.querySelectorAll('img').forEach((im) => { if (!im.complete || !im.naturalWidth) r.badImg.push(im.getAttribute('src')); });
    const vs = [...s.querySelectorAll('video')];
    const t0 = vs.map((v) => v.currentTime);
    await new Promise((z) => setTimeout(z, 700));
    vs.forEach((v, k) => r.videos.push({
      src: v.getAttribute('src'), rs: v.readyState, dur: +(v.duration || 0).toFixed(1),
      w: v.videoWidth, adv: v.currentTime > t0[k],
    }));
    s.querySelectorAll('iframe').forEach((f) => r.iframes.push({ src: (f.getAttribute('src') || '').slice(0, 70), lazy: f.classList.contains('yt-lazy') }));
    return r;
  });
  info.i = i;
  per.push(info);
  const f = path.join(frames, String(i).padStart(3, '0') + '.png');
  await p.screenshot({ path: f });
  shots.push(f);
  if (STEPS) info.steps = await walkSteps(i, f);
}
const loadedYT = await p.evaluate(() => [...document.querySelectorAll('iframe.yt-lazy')].filter((f) => f.getAttribute('src')).length);

// Contact sheets, 9 shots each: the point is that a human can open one and look. Tiled by the browser rather than
// ffmpeg so every tile carries its caption (NNN = slide index, sK = substep K) without needing ffmpeg's drawtext.
const N = 9;
const sheet = await b.newPage({ viewport: { width: 1900, height: 1080 } });
for (let s = 0; s * N < shots.length; s++) {
  const tiles = shots.slice(s * N, s * N + N).map((f) => {
    const label = path.basename(f, '.png').replace(/^0+(?=\d)/, '').replace('-s', ' · step ');
    return `<figure><img src="data:image/png;base64,${readFileSync(f).toString('base64')}"><figcaption>${label}</figcaption></figure>`;
  }).join('');
  await sheet.setContent(`<style>body{margin:0;background:#14141f;display:grid;grid-template-columns:repeat(3,620px);gap:8px;padding:8px;width:max-content}
figure{margin:0;position:relative;outline:2px solid rgba(45,212,191,.5)}img{width:620px;display:block}
figcaption{position:absolute;left:8px;top:8px;background:rgba(0,0,0,.72);color:#fff;font:600 18px system-ui;padding:3px 9px;border-radius:4px}</style>${tiles}`);
  await sheet.screenshot({ path: path.join(outDir, `deck-${tag}-sheet${s}.png`), fullPage: true });
}
await b.close();

// ── Classify, then judge ─────────────────────────────────────────────────────
const firedIds = new Set();
const split = (list) => {
  const expected = [], unexpected = [];
  for (const line of list) {
    const hit = EXPECTED_NOISE.find((n) => n.match(line));
    if (hit) { firedIds.add(hit.id); expected.push({ line, expected: hit.id }); } else unexpected.push(line);
  }
  return { expected, unexpected };
};
const e = split(errs), f = split(failed);
const problemSlides = per.filter((x) => x.err || x.overflow?.length || x.badImg?.length
  || x.videos?.some((v) => v.rs < 2 || !v.dur || !v.adv));
const stepSlides = STEPS ? per.filter((x) => x.steps?.problems?.length) : [];

const failedBecause = [];
if (e.unexpected.length) failedBecause.push(`${e.unexpected.length} unexpected console/page error(s)`);
if (f.unexpected.length) failedBecause.push(`${f.unexpected.length} unexpected failed request(s)`);
if (problemSlides.length) failedBecause.push(`${problemSlides.length} problem slide(s)`);
if (stepSlides.length) failedBecause.push(`${stepSlides.length} slide(s) break the step contract`);

const rep = {
  url, viewport: `${W}x${H}`, slides: total,
  verdict: failedBecause.length === 0 ? 'PASS' : 'FAIL',
  failedBecause,
  problemSlides,
  unexpectedErrors: e.unexpected,
  unexpectedFailedRequests: f.unexpected,
  // Printed, never judged. Review these when the allowlist itself is in question.
  expectedNoise: [...e.expected, ...f.expected],
  // An expected-noise rule that did not fire is either stale or the cause moved.
  // Not a failure — but silence here is how an allowlist rots into a blindfold.
  expectedNoiseAbsent: EXPECTED_NOISE.filter((n) => !firedIds.has(n.id)).map((n) => ({ id: n.id, why: n.why })),
  ytLoadedAtEnd: loadedYT,
  ...(STEPS ? { steps: {
    slidesWithSteps: per.filter((x) => x.steps?.reachable).length,
    substepShots: per.reduce((n, x) => n + (x.steps?.shots.length || 0), 0),
    contract: per.filter((x) => x.steps && !x.steps.skipped).map((x) => ({ i: x.i, mod: x.steps.mod, declared: x.steps.declared, reachable: x.steps.reachable, frame: x.steps.frame })).filter((x) => x.declared || x.reachable || x.mod),
    broken: stepSlides.map((x) => ({ i: x.i, title: x.title, mod: x.steps.mod, problems: x.steps.problems })),
  } } : {}),
  videosChecked: per.reduce((a, x) => a + (x.videos?.length || 0), 0),
};
writeFileSync(path.join(outDir, `deck-${tag}-report.json`), JSON.stringify(rep, null, 2));
writeFileSync(path.join(outDir, `deck-${tag}-slides.json`), JSON.stringify(per, null, 1));
console.log(JSON.stringify({ ...rep, problemSlides: problemSlides.length }, null, 1));
for (const x of problemSlides) console.log(JSON.stringify(x));
for (const x of stepSlides) console.log('STEPS ' + JSON.stringify({ i: x.i, title: x.title, mod: x.steps.mod, problems: x.steps.problems }));
if (rep.expectedNoiseAbsent.length) {
  console.log(`\nNOTE: ${rep.expectedNoiseAbsent.length} expected-noise rule(s) did not fire this run — check tools/sweep_deck.mjs EXPECTED_NOISE is still accurate:`);
  for (const n of rep.expectedNoiseAbsent) console.log(`  - ${n.id}`);
}
process.exit(rep.verdict === 'PASS' ? 0 : 1);
