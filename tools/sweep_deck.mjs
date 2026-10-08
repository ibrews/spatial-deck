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
import { chromium } from 'playwright';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

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

const [, , url, outDir, wStr, hStr, tagArg] = process.argv;
if (!url || !outDir) {
  console.error('usage: node tools/sweep_deck.mjs <url> <outDir> [width] [height] [tag]');
  process.exit(2);
}
const W = +(wStr || 1920), H = +(hStr || 1080);
const tag = tagArg || `${W}x${H}`;
const frames = path.join(outDir, 'f-' + tag);
rmSync(frames, { recursive: true, force: true });
mkdirSync(frames, { recursive: true });

const b = await chromium.launch({ args: ['--hide-scrollbars', '--autoplay-policy=no-user-gesture-required'] });
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

await p.goto(url + (url.includes('?') ? '&' : '?') + 'view', { waitUntil: 'load' });
await p.waitForTimeout(2500);
const total = await p.evaluate(() => document.querySelectorAll('.slide').length);
const shots = [], per = [];
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
}
const loadedYT = await p.evaluate(() => [...document.querySelectorAll('iframe.yt-lazy')].filter((f) => f.getAttribute('src')).length);
await b.close();

// Contact sheets, 9 slides each — the point is that a human can open one and look.
const N = 9;
for (let s = 0; s * N < total; s++) {
  const sel = shots.slice(s * N, s * N + N);
  const d2 = path.join(frames, 'g' + s);
  mkdirSync(d2, { recursive: true });
  sel.forEach((f, i) => execFileSync('cp', [f, path.join(d2, String(i).padStart(3, '0') + '.png')]));
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-i', path.join(d2, '%03d.png'), '-vf',
    'scale=620:-2,drawbox=c=0x2dd4bf@0.5:t=2,tile=3x3:padding=8:color=0x14141f',
    '-frames:v', '1', path.join(outDir, `deck-${tag}-sheet${s}.png`)]);
}

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

const failedBecause = [];
if (e.unexpected.length) failedBecause.push(`${e.unexpected.length} unexpected console/page error(s)`);
if (f.unexpected.length) failedBecause.push(`${f.unexpected.length} unexpected failed request(s)`);
if (problemSlides.length) failedBecause.push(`${problemSlides.length} problem slide(s)`);

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
  videosChecked: per.reduce((a, x) => a + (x.videos?.length || 0), 0),
};
writeFileSync(path.join(outDir, `deck-${tag}-report.json`), JSON.stringify(rep, null, 2));
writeFileSync(path.join(outDir, `deck-${tag}-slides.json`), JSON.stringify(per, null, 1));
console.log(JSON.stringify({ ...rep, problemSlides: problemSlides.length }, null, 1));
for (const x of problemSlides) console.log(JSON.stringify(x));
if (rep.expectedNoiseAbsent.length) {
  console.log(`\nNOTE: ${rep.expectedNoiseAbsent.length} expected-noise rule(s) did not fire this run — check tools/sweep_deck.mjs EXPECTED_NOISE is still accurate:`);
  for (const n of rep.expectedNoiseAbsent) console.log(`  - ${n.id}`);
}
process.exit(rep.verdict === 'PASS' ? 0 : 1);
