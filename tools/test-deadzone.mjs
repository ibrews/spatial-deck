#!/usr/bin/env node

import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { homedir, tmpdir } from 'node:os';
import path from 'node:path';
import { readFile, mkdir, mkdtemp, writeFile } from 'node:fs/promises';

const ROOT = path.resolve(import.meta.dirname, '..');
const OUT = path.resolve(process.env.SD_DEADZONE_EVIDENCE || '/tmp/deck-deadzone-evidence');
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const require = createRequire(import.meta.url);

function loadChromium() {
  const roots = [
    process.env.SD_PLAYWRIGHT_DIR,
    path.join(homedir(), '.cache/spatial-deck/video-deps/node_modules'),
    path.join(homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'),
  ].filter(Boolean);
  for (const root of roots) {
    try { return require(path.join(root, 'playwright-core')).chromium; } catch (_) {}
  }
  throw new Error('playwright-core not found; set SD_PLAYWRIGHT_DIR to its node_modules directory');
}

function serveRepo() {
  const server = createServer(async (req, res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
      const requested = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
      const file = path.resolve(ROOT, requested);
      if (file !== ROOT && !file.startsWith(ROOT + path.sep)) throw new Error('outside repo');
      const body = await readFile(file);
      res.writeHead(200, { 'content-type': file.endsWith('.html') ? 'text/html; charset=utf-8' : 'application/octet-stream' });
      res.end(body);
    } catch (_) {
      res.writeHead(404).end('not found');
    }
  });
  return new Promise(resolve => server.listen(0, '127.0.0.1', () => {
    const { port } = server.address();
    resolve({ server, url: `http://127.0.0.1:${port}/?edit#1` });
  }));
}

let caseSequence = 0;
async function openCase(page, url, seed = true) {
  const caseUrl = url.replace('#', `&deadzoneCase=${++caseSequence}#`);
  await page.goto(caseUrl, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.slide.active .talk-title');
  await page.waitForTimeout(700);
  await page.evaluate(() => localStorage.clear());
  if (seed) {
    await page.evaluate(() => localStorage.setItem('sd-annos', JSON.stringify([
      { selector: '#seed', context: 'test', text: 'keep me', type: 'note' },
    ])));
  }
  await page.click('#move-toggle');
  assert.equal(await page.evaluate(() => window._moveMode), true, 'move mode did not enable');
  return page;
}

async function snapshot(page, selector = '.slide.active .talk-title') {
  return page.evaluate(sel => {
    const el = document.querySelector(sel);
    return {
      transform: el.style.transform,
      transformBox: el.style.transformBox,
      transformOrigin: el.style.transformOrigin,
      annotations: localStorage.getItem('sd-annos'),
      undoDisabled: document.querySelector('#move-undo').disabled,
      redoDisabled: document.querySelector('#move-redo').disabled,
    };
  }, selector);
}

async function drag(page, mode, amount, selector = '.slide.active .talk-title') {
  const box = await page.locator(selector).boundingBox();
  assert(box, `missing target ${selector}`);
  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;
  // Synthetic DOM events can use an off-viewport radius. The long baseline
  // avoids integer client-coordinate quantization around 0.02 and 1 degree.
  const radius = 5000;
  let start = { x: Math.round(cx), y: Math.round(cy) };
  let end = { x: start.x + amount, y: start.y };
  let shiftKey = false;
  let altKey = false;
  if (mode === 'scale') {
    start = { x: cx + radius, y: cy };
    end = { x: cx + radius * (1 + amount), y: cy };
    shiftKey = true;
  } else if (mode === 'rotate') {
    start = { x: cx + radius, y: cy };
    const angle = amount * Math.PI / 180;
    end = { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) };
    altKey = true;
  }
  return page.evaluate(({ selector, start, end, shiftKey, altKey }) => {
    const target = document.querySelector(selector);
    const init = (point, extra = {}) => ({ bubbles: true, cancelable: true, button: 0, buttons: 1, clientX: point.x, clientY: point.y, shiftKey, altKey, ...extra });
    target.dispatchEvent(new MouseEvent('mousedown', init(start)));
    document.dispatchEvent(new MouseEvent('mousemove', init(end)));
    const during = target.style.transform;
    document.dispatchEvent(new MouseEvent('mouseup', init(end, { buttons: 0 })));
    return during;
  }, { selector, start, end, shiftKey, altKey });
}

async function runThresholdCase(page, url, spec) {
  await openCase(page, url);
  const original = 'translate3d(7px, 9px, 0px) scale(1.1)';
  await page.evaluate(value => {
    const el = document.querySelector('.slide.active .talk-title');
    el.style.transform = value;
    el.style.transformBox = 'border-box';
    el.style.transformOrigin = '23% 41%';
  }, original);
  const before = await snapshot(page);
  const during = await drag(page, spec.mode, spec.amount);
  const after = await snapshot(page);
  if (spec.commits) {
    assert.notEqual(after.transform, before.transform, `${spec.name}: transform should commit (mousemove produced ${during})`);
    assert.equal(JSON.parse(after.annotations).length, 2, `${spec.name}: move annotation missing`);
    assert.equal(after.undoDisabled, false, `${spec.name}: undo history missing`);
    assert.equal(after.redoDisabled, true, `${spec.name}: redo should remain empty`);
  } else {
    assert.deepEqual(after, before, `${spec.name}: no-op changed DOM, history, redo, or annotations`);
  }
  return { name: spec.name, commits: spec.commits, transform: after.transform };
}

async function runUndoRedo(page, url) {
  await openCase(page, url);
  const before = await snapshot(page);
  await drag(page, 'translate', 6);
  const moved = await snapshot(page);
  assert.equal(JSON.parse(moved.annotations).filter(a => a.type === 'move').length, 1);
  assert.equal(moved.undoDisabled, false);
  await page.screenshot({ path: path.join(OUT, 'meaningful-drag.png') });

  await drag(page, 'translate', 4);
  const afterNoop = await snapshot(page);
  assert.deepEqual(afterNoop, moved, 'no-op after a committed drag changed transform, history, or annotation state');

  await page.click('#move-undo');
  const undone = await snapshot(page);
  assert.notEqual(undone.transform, moved.transform, 'undo did not restore the prior transform state');
  assert.equal(undone.redoDisabled, false, 'undo did not populate redo');
  assert.equal(undone.annotations, moved.annotations, 'undo corrupted serialized annotations');

  await page.click('#move-redo');
  const redone = await snapshot(page);
  assert.equal(redone.transform, moved.transform, 'redo did not restore the committed transform');
  assert.equal(redone.annotations, moved.annotations, 'redo corrupted serialized annotations');
  assert.equal(redone.redoDisabled, true);
  await page.screenshot({ path: path.join(OUT, 'meaningful-redo.png') });
  return { before, moved, afterNoop, undone, redone };
}

async function runCropScaleGuard(page, url) {
  await openCase(page, url);
  const selector = '#deadzone-synthetic-media';
  await page.evaluate(() => {
    const img = document.createElement('img');
    img.id = 'deadzone-synthetic-media';
    img.alt = 'synthetic crop-scale fixture';
    img.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect width="400" height="300" fill="%2300d4ff"/></svg>';
    img.style.cssText = 'position:absolute;left:35%;top:30%;width:400px;height:300px;object-fit:cover;object-position:37% 63%;transform:scale(1.25);transform-origin:17% 29%;z-index:20';
    document.querySelector('.slide.active').appendChild(img);
  });
  const before = await snapshot(page, selector);
  const box = await page.locator(selector).boundingBox();
  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;
  const radius = 100;
  await page.keyboard.down('Shift');
  await page.keyboard.down('c');
  await page.mouse.move(cx + radius, cy);
  await page.mouse.down();
  await page.mouse.move(cx + radius * 1.007, cy, { steps: 2 });
  await page.mouse.up();
  await page.keyboard.up('c');
  await page.keyboard.up('Shift');
  const after = await snapshot(page, selector);
  assert.deepEqual(after, before, 'sub-threshold crop-scale changed transform or serialized state');
  await page.screenshot({ path: path.join(OUT, 'synthetic-crop-scale-noop.png') });
  return after;
}

const cases = [
  { name: 'translate-below-4px', mode: 'translate', amount: 4, commits: false },
  { name: 'translate-at-5px', mode: 'translate', amount: 5, commits: true },
  { name: 'translate-above-6px', mode: 'translate', amount: 6, commits: true },
  { name: 'scale-below-0.019', mode: 'scale', amount: 0.019, commits: false },
  { name: 'scale-at-0.02', mode: 'scale', amount: 0.02, commits: true },
  { name: 'scale-above-0.021', mode: 'scale', amount: 0.021, commits: true },
  { name: 'rotate-below-0.9deg', mode: 'rotate', amount: 0.9, commits: false },
  { name: 'rotate-at-1deg', mode: 'rotate', amount: 1.01, commits: true },
  { name: 'rotate-above-1.1deg', mode: 'rotate', amount: 1.1, commits: true },
];

await mkdir(OUT, { recursive: true });
const { server, url } = await serveRepo();
const chromium = loadChromium();
const profile = await mkdtemp(path.join(tmpdir(), 'deck-deadzone-profile-'));
const context = await chromium.launchPersistentContext(profile, {
  headless: true,
  executablePath: CHROME,
  viewport: { width: 1280, height: 720 },
  // Keeps macOS headless runs viable inside restricted CI/agent sandboxes where
  // Chromium's child-process Mach rendezvous registration is denied.
  args: ['--single-process', '--no-zygote'],
});
const page = context.pages()[0] || await context.newPage();
const results = [];
try {
  for (const spec of cases) results.push(await runThresholdCase(page, url, spec));
  results.push({ name: 'meaningful-drag-annotation-undo-redo', state: await runUndoRedo(page, url) });
  results.push({ name: 'synthetic-crop-scale-noop', state: await runCropScaleGuard(page, url) });
  const report = { passed: results.length, thresholdCases: cases.length, url, results };
  await writeFile(path.join(OUT, 'results.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(`PASS ${results.length} dead-zone browser scenarios`);
  console.log(`evidence: ${OUT}`);
} finally {
  await context.close();
  await new Promise(resolve => server.close(resolve));
}
