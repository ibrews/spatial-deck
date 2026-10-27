/* Pixel-sprite kit for seekable slide modules (core/venn; PMRE's lane-sprite and lane-to-venn). Shared by modules that
   list it in `shared`; slide.py pull copies it along. Origin: ibrews/pmre-2026-xr-chitect media/motion/sprite.js @310afba.
   - avatar(): the exact 2010 pixel Alex from talk/intro.js tiAvatar (FMX/HXR buildAvatar), beard optional.
   - headset(): the intro's headset power-up (talk/intro.js tiHeadset).
   - temple() / theater() / monitor(): the HarvardXR 2026 Venn pixel icons (harvardxr-keynote buildVennSlide), recolored to
     the noir source palette so look.js can restyle them for house / sheet / folio.
   Everything moves through WAAPI keyframes sampled from pure functions of time, so document.getAnimations() + seek(sec)
   reproduce any frame exactly (no setTimeout / setInterval / rAF / runtime Math.random). Build synchronously, before the
   page's seek runtime and before look.js. */
(function () {
  const NS = 'http://www.w3.org/2000/svg', FPS = 30;
  function E(tag, attrs, parent) { const el = document.createElementNS(NS, tag); for (const k in attrs || {}) el.setAttribute(k, attrs[k]); if (parent) parent.appendChild(el); return el; }
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const ease = k => k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
  // Animate el over [0, END] with keyframes sampled from fn(t) at FPS. discrete=true holds each value until the next sample.
  function track(el, END, fn, discrete) {
    const N = Math.max(1, Math.round(END * FPS)), kf = [];
    let prev = null;
    for (let i = 0; i <= N; i++) {
      const v = fn(i / FPS), s = JSON.stringify(v);
      if (s === prev && i !== N) { const nx = i < N ? JSON.stringify(fn((i + 1) / FPS)) : null; if (nx === s) continue; }  // drop runs of identical frames
      prev = s; const k = Object.assign({}, v, { offset: i / N }); if (discrete) k.easing = 'steps(1,end)'; kf.push(k);
    }
    return el.animate(kf, { duration: END * 1000, fill: 'both', easing: 'linear' });
  }
  // Deterministic PRNG (mulberry32) for sparkle layouts.
  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  // ── The 2010 pixel Alex (verbatim pixel data from talk/intro.js tiAvatar) ──
  function avatar(parent, opts = {}) {
    const withBeard = !!opts.withBeard;
    const root = E('g', { class: 'avatar', 'shape-rendering': 'crispEdges' }, parent);
    const SKIN = '#f2c79b', SKIN_DARK = '#d9a77a', HAIR_LIGHT = '#a8602f', HAIR = '#8b4a2a', HAIR_DARK = '#5e2f1a', HAIR_SHADOW = '#3a1c08', BEARD = '#6e3a1e', BEARD_LIGHT = '#8a4f2a', SHIRT = '#6a8fd6', SHIRT_DARK = '#4a6fb8', PANTS = '#3f3025', BOOTS = '#1f150c', EYE = '#1a1a26';
    const px = (g, x, y, w, h, fill) => E('rect', { x, y, width: w, height: h, fill }, g);
    const body = E('g', { class: 'av-body' });
    px(body, -12, -34, 24, 22, SKIN); px(body, -12, -16, 24, 4, SKIN_DARK);
    px(body, -13, -40, 26, 2, HAIR_SHADOW); px(body, -15, -38, 30, 3, HAIR_SHADOW); px(body, -16, -36, 32, 4, HAIR_SHADOW); px(body, -9, -42, 5, 2, HAIR_SHADOW); px(body, 3, -42, 4, 2, HAIR_SHADOW); px(body, -2, -43, 5, 1, HAIR_SHADOW);
    px(body, -12, -40, 24, 2, HAIR_DARK); px(body, -14, -38, 28, 3, HAIR_DARK); px(body, -13, -34, 30, 3, HAIR_DARK); px(body, -8, -42, 4, 2, HAIR_DARK); px(body, 4, -42, 3, 2, HAIR_DARK); px(body, -1, -43, 3, 1, HAIR_DARK);
    px(body, -11, -41, 22, 1, HAIR); px(body, -13, -38, 26, 2, HAIR); px(body, -14, -36, 28, 2, HAIR); px(body, -8, -41, 4, 1, HAIR); px(body, 4, -41, 3, 1, HAIR);
    px(body, -13, -34, 2, 3, HAIR_DARK); px(body, 12, -33, 2, 3, HAIR_DARK); px(body, -14, -31, 2, 4, HAIR); px(body, 10, -31, 1, 2, HAIR);
    px(body, -8, -40, 3, 1, HAIR_LIGHT); px(body, 4, -40, 2, 1, HAIR_LIGHT); px(body, -10, -38, 2, 1, HAIR_LIGHT); px(body, -2, -42, 2, 1, HAIR_LIGHT); px(body, -7, -41, 2, 1, HAIR_LIGHT);
    px(body, -12, -34, 5, 3, HAIR_DARK); px(body, -11, -33, 4, 2, HAIR); px(body, -7, -34, 3, 2, HAIR_DARK); px(body, -7, -33, 2, 1, HAIR); px(body, -4, -34, 2, 4, HAIR_DARK); px(body, -4, -33, 1, 3, HAIR); px(body, -1, -34, 3, 2, HAIR_DARK); px(body, -1, -33, 2, 1, HAIR); px(body, 3, -34, 4, 3, HAIR_DARK); px(body, 3, -33, 3, 2, HAIR); px(body, 7, -34, 5, 4, HAIR_DARK); px(body, 10, -31, 3, 3, HAIR);
    px(body, -12, -31, 2, 1, HAIR_LIGHT); px(body, 8, -33, 2, 1, HAIR_LIGHT);
    px(body, -8, -27, 8, 3, HAIR_DARK); px(body, 3, -28, 9, 4, HAIR_DARK);
    px(body, -7, -24, 3, 4, EYE); px(body, 4, -24, 3, 4, EYE); px(body, -6, -23, 1, 2, '#fff'); px(body, 5, -23, 1, 2, '#fff');
    px(body, -3, -17, 6, 1, '#9c5040');
    if (withBeard) { px(body, -12, -22, 4, 5, BEARD); px(body, 8, -22, 4, 5, BEARD); px(body, -12, -20, 5, 3, BEARD); px(body, 7, -20, 5, 3, BEARD); px(body, -12, -17, 4, 1, BEARD); px(body, 8, -17, 4, 1, BEARD); px(body, -7, -19, 14, 2, BEARD); px(body, -6, -19, 12, 1, BEARD_LIGHT); px(body, -2, -16, 4, 1, BEARD); px(body, -12, -16, 24, 2, BEARD); px(body, -12, -14, 24, 2, BEARD); px(body, -10, -12, 20, 1, BEARD); }
    px(body, -4, -12, 8, 3, SKIN_DARK);
    px(body, -12, -9, 24, 18, SHIRT); px(body, -12, -9, 24, 3, SHIRT_DARK); px(body, -12, 6, 24, 3, SHIRT_DARK);
    px(body, -12, 9, 12, 14, PANTS); px(body, 0, 9, 12, 14, PANTS); px(body, -2, 9, 4, 14, '#2a1f18');
    px(body, -12, 23, 12, 5, BOOTS); px(body, 0, 23, 12, 5, BOOTS);
    root.appendChild(body);
    const armsDown = E('g', { class: 'av-arms-down' }, root); px(armsDown, -18, -8, 6, 14, SHIRT); px(armsDown, -18, 4, 6, 4, SKIN); px(armsDown, 12, -8, 6, 14, SHIRT); px(armsDown, 12, 4, 6, 4, SKIN);
    const armsUp = E('g', { class: 'av-arms-up' }, root); px(armsUp, -18, -22, 6, 14, SHIRT); px(armsUp, -18, -26, 6, 6, SKIN); px(armsUp, 12, -22, 6, 14, SHIRT); px(armsUp, 12, -26, 6, 6, SKIN);
    return { root, body, armsUp, armsDown };
  }
  // The intro's headset (talk/intro.js tiHeadset). #00d4ff lenses are a palette color, so they follow the look.
  function headset(body) {
    const hs = E('g', { class: 'worn-headset', 'shape-rendering': 'crispEdges' }, body);
    const px = (x, y, w, h, fill) => E('rect', { x, y, width: w, height: h, fill }, hs);
    px(-13, -27, 26, 1, '#0a0a14'); px(-13, -26, 26, 9, '#1a1a26'); px(-13, -17, 26, 1, '#0a0a14');
    px(-8, -24, 5, 5, '#00d4ff'); px(3, -24, 5, 5, '#00d4ff'); px(-7, -23, 1, 1, '#fff'); px(4, -23, 1, 1, '#fff');
    px(-13, -23, 1, 3, '#3a3a4e'); px(12, -23, 1, 3, '#3a3a4e');
    return hs;
  }

  // ── HXR Venn icons. Each returns { pos, g } where pos carries the placement (transform attr) and g is free for CSS motion. ──
  function iconShell(parent, x, y, S) {
    const pos = E('g', { transform: `translate(${x},${y})` }, parent), g = E('g', { 'shape-rendering': 'crispEdges' }, pos);
    const p = (x, y, w, h, f, o, into) => E('rect', Object.assign({ x: x * S, y: y * S, width: w * S, height: h * S, fill: f }, o == null ? {} : { 'fill-opacity': o }), into || g);
    return { pos, g, p };
  }
  // Architecture: Greek temple, pediment, four fluted columns, three steps. Marble = text color, trim = architecture teal.
  function temple(parent, x, y, S) {
    const I = iconShell(parent, x, y, S), p = I.p, M = '#f0f4ff', A = '#00d4ff';
    p(-1, -20, 2, 2, M); p(-3, -18, 6, 2, M); p(-6, -16, 12, 2, A); p(-9, -14, 18, 2, A); p(-12, -12, 24, 2, A, .75);
    p(-13, -10, 26, 2, A); p(-13, -8, 26, 1, A, .5);
    [-11, -5, 2, 8].forEach(cx => { p(cx, -7, 3, 18, M, .92); p(cx + 1, -7, 1, 18, A, .7); });
    p(-14, 11, 28, 2, A); p(-15, 13, 30, 2, A, .75); p(-16, 15, 32, 2, A, .5);
    I.cracks = E('g', { opacity: '0' }, I.g);
    [[-10, -2, 1, 6], [-9, 1, 1, 3], [-4, -4, 1, 8], [3, -1, 1, 5], [9, -3, 1, 7]].forEach(c => p(c[0], c[1], c[2], c[3], '#060810', .85, I.cracks));
    I.foot = 17 * S; return I;
  }
  // Theater: proscenium (amber) with draped curtains (rose), boards and a spotlight. shimmer = white overlays on the folds.
  function theater(parent, x, y, S) {
    const I = iconShell(parent, x, y, S), p = I.p, G = '#f59e0b', R = '#f43f5e', W = '#f0f4ff', D = '#060810';
    p(-16, -18, 32, 3, G); p(-16, -15, 3, 30, G); p(13, -15, 3, 30, G); p(-15, -17, 30, 1, W, .55);
    p(-13, -15, 26, 27, D);
    p(-13, -15, 4, 25, R, .85); p(-9, -15, 3, 23, R); p(-12, -15, 2, 25, R, .6); p(-7, -15, 2, 20, R, .85);
    p(9, -15, 4, 25, R, .85); p(6, -15, 3, 23, R); p(10, -15, 2, 25, R, .6); p(5, -15, 2, 20, R, .85);
    p(-9, -15, 18, 3, R, .85); p(-7, -13, 14, 2, R); p(-5, -11, 10, 1, R, .85);
    p(-13, 12, 26, 3, G, .55); p(-13, 12, 26, 1, G, .85);
    p(-1, -12, 2, 3, W, .3); p(-2, -9, 4, 4, W, .15); p(-4, -5, 8, 6, W, .08); p(-6, 1, 12, 6, W, .04);
    I.shimmer = [[-13, -15, 4, 25], [-9, -15, 3, 23], [-7, -15, 2, 20], [9, -15, 4, 25], [6, -15, 3, 23], [5, -15, 2, 20], [-9, -15, 18, 3]].map(r => { const e = p(r[0], r[1], r[2], r[3], W, .55); e.setAttribute('opacity', '0'); return e; });
    I.foot = 12 * S; return I;
  }
  // Realtime tech: monitor with a tiny platformer (player, coins, platform, clouds). player + coins animate on arrival.
  function monitor(parent, x, y, S) {
    const I = iconShell(parent, x, y, S), p = I.p, P = '#a78bfa', T = '#00d4ff', C = '#f59e0b', W = '#f0f4ff';
    p(-16, -16, 32, 24, P, .55); p(-14, -14, 28, 20, '#060810'); p(-14, -14, 28, 1, P, .4);
    p(-3, 8, 6, 4, P, .45); p(-8, 12, 16, 2, P, .45); p(-7, 12, 14, 1, P, .7);
    p(-12, 2, 24, 2, P); p(-12, 4, 24, 2, P, .45);
    I.player = E('g', {}, I.g); p(-6, -4, 2, 2, W, null, I.player); p(-7, -2, 4, 4, T, null, I.player); p(-7, 2, 2, 1, T, .6, I.player); p(-5, 2, 2, 1, T, .6, I.player);
    I.coins = [p(2, -6, 2, 2, C), p(7, -8, 2, 2, C)];
    p(4, -2, 8, 2, '#f43f5e', .7); p(4, -2, 8, 1, '#f43f5e');
    p(-10, -12, 6, 2, W, .15); p(5, -10, 4, 2, W, .1);
    I.foot = 14 * S; I.S = S; return I;
  }
  // ── Reactions (all in absolute seconds; pass the page END). HXR timings: shake 6 × 65 ms, cracks 600 ms, shimmer 9 × 70 ms, run 13 × 60 ms. ──
  const SHAKE = [[3, -2], [-4, 2], [2, 3], [-3, -1], [1, -2], [0, 0]];
  function shake(g, END, hits, amp) {
    amp = amp || 1.5;
    track(g, END, t => { for (const t0 of hits) { const i = Math.floor((t - t0) / .065); if (i >= 0 && i < SHAKE.length) return { transform: `translate(${SHAKE[i][0] * amp}px,${SHAKE[i][1] * amp}px)` }; } return { transform: 'translate(0px,0px)' }; }, true);
  }
  function reactArch(I, END, t0) { shake(I.g, END, [t0]); track(I.cracks, END, t => ({ opacity: t >= t0 && t < t0 + .6 ? 1 : 0 }), true); }
  function reactTheater(I, END, t0) {
    shake(I.g, END, [t0]);
    I.shimmer.forEach((r, i) => track(r, END, t => { const f = Math.floor((t - t0) / .07) + 1; return { opacity: f >= 1 && f <= 8 && (f + i) % 3 === 0 ? 1 : 0 }; }, true));
  }
  function reactTech(I, END, t0) {
    shake(I.g, END, [t0]);
    track(I.player, END, t => { const f = Math.floor((t - t0) / .06) + 1; return { transform: `translate(${f >= 1 && f <= 12 ? (Math.sin(f * .8) * 4 * I.S).toFixed(2) : 0}px,0px)` }; }, true);
    I.coins.forEach((c, i) => track(c, END, t => { const f = Math.floor((t - t0) / .06) + 1; return { opacity: f >= 1 && f <= 12 && (f + i) % 3 === 0 ? .3 : 1 }; }, true));
  }
  // Sparkle burst (intro power-up style): 24 dots fly out from (cx,cy) at t0. Seeded, so identical every run.
  function sparkles(parent, END, cx, cy, t0, seed, reach) {
    const R = rng(seed || 7), COLORS = ['#f59e0b', '#00d4ff', '#a78bfa', '#f43f5e', '#f0f4ff'], g = E('g', {}, parent); reach = reach || 1;
    for (let i = 0; i < 24; i++) {
      const a = (i / 24) * Math.PI * 2 + (R() - .5) * .4, d = (70 + R() * 60) * reach, c = E('circle', { cx, cy, r: (2 + R() * 3).toFixed(1), fill: COLORS[i % COLORS.length] }, g);
      track(c, END, t => { const k = (t - t0) / 1.1; if (k < 0 || k > 1) return { opacity: 0, transform: 'translate(0px,0px)' }; const e = 1 - Math.pow(1 - k, 3); return { opacity: +(1 - k).toFixed(3), transform: `translate(${(Math.cos(a) * d * e).toFixed(1)}px,${(Math.sin(a) * d * e).toFixed(1)}px)` }; });
    }
    return g;
  }
  // ── Routes: the sprite's position is a pure function of time. Segments: idle | walk | path | hop. ──
  // walk/path bob like steps; hop is a parabola with arms up. path rides an SVG path between two x positions.
  function lengthAtX(path, x) { const L = path.getTotalLength(); let lo = 0, hi = L; for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (path.getPointAtLength(m).x < x) lo = m; else hi = m; } return (lo + hi) / 2; }
  function route(segs) {
    segs.forEach(s => { if (s.type === 'path') { s.l0 = lengthAtX(s.path, s.x0); s.l1 = lengthAtX(s.path, s.x1); } });
    let last = { x: 0, y: 0, face: 1 };
    const at = t => {
      let s = segs[0]; for (const q of segs) if (t >= q.t0) s = q;
      const k = clamp((t - s.t0) / Math.max(.001, s.t1 - s.t0), 0, 1), stepBob = (dist) => -Math.abs(Math.sin(dist / 26 * Math.PI)) * 7;
      let x, y, up = false, bob = 0, face = s.face;
      if (s.type === 'idle' && face == null) face = last.face;
      if (s.type === 'idle') { x = s.a[0]; y = s.a[1]; up = !!s.cheer && k > 0 && k < 1 && Math.floor((t - s.t0) / .25) % 2 === 0; }
      else if (s.type === 'walk') { const e = s.linear ? k : ease(k); x = s.a[0] + (s.b[0] - s.a[0]) * e; y = s.a[1] + (s.b[1] - s.a[1]) * e; bob = k > 0 && k < 1 ? stepBob(Math.hypot(x - s.a[0], y - s.a[1])) : 0; if (face == null) face = Math.sign(s.b[0] - s.a[0]) || 1; }
      else if (s.type === 'path') { const e = s.linear ? k : ease(k), pt = s.path.getPointAtLength(s.l0 + (s.l1 - s.l0) * e); x = pt.x; y = pt.y; bob = k > 0 && k < 1 ? stepBob((s.l1 - s.l0) * e) : 0; if (face == null) face = Math.sign(s.x1 - s.x0) || 1; }
      else { x = s.a[0] + (s.b[0] - s.a[0]) * k; const h = s.h == null ? 90 : s.h; y = s.a[1] + (s.b[1] - s.a[1]) * k - 4 * h * k * (1 - k) - (s.extra ? s.extra(k) : 0); up = k > 0 && k < 1; if (face == null) face = Math.sign(s.b[0] - s.a[0]) || last.face; }
      last = { x, y, face: face || 1 }; return { x, y: y + bob, up, face: face || 1 };
    };
    return at;
  }
  // Drive a sprite: outer g translate+scale(face), arms swap while hopping/cheering, optional fade-in window.
  function drive(sp, END, at, scale, show) {
    track(sp.outer, END, t => { const s = at(t); return { transform: `translate(${s.x.toFixed(1)}px,${s.y.toFixed(1)}px) scale(${(s.face * scale).toFixed(3)},${scale})` }; });
    track(sp.av.armsUp, END, t => ({ opacity: at(t).up ? 1 : 0 }), true);
    track(sp.av.armsDown, END, t => ({ opacity: at(t).up ? 0 : 1 }), true);
    if (show) track(sp.outer.parentNode, END, t => ({ opacity: +clamp((t - show[0]) / (show[1] - show[0]), 0, 1).toFixed(3) }));
  }
  // A sprite whose local origin is at its feet. Returns { wrap, outer, av, body }.
  function sprite(parent, opts) {
    const wrap = E('g', {}, parent), outer = E('g', {}, wrap), feet = E('g', { transform: 'translate(0,-28)' }, outer), av = avatar(feet, opts);
    return { wrap, outer, av, body: av.body };
  }
  window.PX = { E, track, ease, clamp, rng, avatar, headset, temple, theater, monitor, shake, reactArch, reactTheater, reactTech, sparkles, route, drive, sprite, lengthAtX, FPS };
})();
