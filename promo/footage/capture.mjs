// Record real Spatial Deck footage via system Chrome (playwright-core).
// Output: webm clips in /tmp/sd-capture/video/ — raw material for the
// README hero GIF and trailer beats.
import { chromium } from 'playwright-core';

const DECK = 'file:///Users/alex/spatial-deck/index.html';
const W = 1280, H = 720;

async function record(name, fn, ms) {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const ctx = await browser.newContext({
    viewport: { width: W, height: H },
    recordVideo: { dir: '/tmp/sd-capture/video', size: { width: W, height: H } },
  });
  const page = await ctx.newPage();
  await fn(page);
  const video = page.video();
  await ctx.close();
  await browser.close();
  const path = await video.path();
  const fs = await import('fs');
  fs.renameSync(path, `/tmp/sd-capture/video/${name}.webm`);
  console.log(`recorded ${name}.webm`);
}

// Clip 1: hero — cover, then advance through the first chapters so the GIF
// shows real slides, media reveals, and transitions.
await record('hero', async (page) => {
  await page.goto(DECK);
  await page.waitForTimeout(2800);            // cover settles, stars drift
  for (let i = 0; i < 7; i++) {
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(2100);          // whoosh + reveal per step
  }
});

// Clip 2: move mode — enter move mode, show the HUD/grid (trailer beat).
await record('movemode', async (page) => {
  await page.goto(DECK + '#3');
  await page.waitForTimeout(2000);
  await page.keyboard.press('m');
  await page.waitForTimeout(1200);
  await page.keyboard.press('g');             // layout grid overlay
  await page.waitForTimeout(2500);
  // drag the case title around
  const title = await page.$('.slide.active .case-title');
  if (title) {
    const box = await title.boundingBox();
    if (box) {
      const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
      await page.mouse.move(cx, cy);
      await page.mouse.down();
      for (let s = 1; s <= 20; s++) {
        await page.mouse.move(cx + s * 6, cy - s * 3);
        await page.waitForTimeout(40);
      }
      await page.mouse.up();
    }
  }
  await page.waitForTimeout(1800);
});

// Clip 3: constellation map — jump to the map slide, let it animate.
await record('map', async (page) => {
  await page.goto(DECK + '#16');
  await page.waitForTimeout(6000);
});

console.log('done');
