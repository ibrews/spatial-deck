/* core/intro-lens: a studio monocle with client names orbiting it (auto, with a low hum), then up to five clicks:
   1 the names fade, 2 a year counter runs backward, 3 a younger avatar appears in the lens, 4 it shrinks into the eyepiece,
   5 chiptune: it dashes around the lens and the landing year appears.
   `sequence: false` makes the slide ONE beat (0 clicks): just the orbit, with no countdown, avatar or shrink; the final
   frame is the orbit itself. Props: name, tagline, est, city, footer (the heading block inside the ring), year (the landing
   label), countFrom (first number of the counter), clientsFixed (4 names pinned at 12/3/6/9 o'clock), clientsOthers (up to
   8 more, two per gap), monocle (URL of a white-on-transparent ring image; the default is a generic monocle that keeps the
   same geometry: ring centered at 407,432 r 374 and an eyelet at 775,788 in an 852x877 box), sequence.
   Ported from the PMRE deck's talk/intro.js (tiBuildLens): same SVG, timings and sounds. Differences: the counter's tick/fade
   thresholds are relative to countFrom (identical for 2026), and with reduced motion step 2 shows the first counter value
   (the live counter's last frame is empty, which made the click a dead step). */
SD.defineSlide({
  id: 'core/intro-lens',
  shows: ['avatar'],
  steps: (props) => (props.sequence === false ? 0 : 5),
  props: {
    sequence: true,
    name: 'YOUR STUDIO',
    tagline: 'WHAT YOU DO',
    est: 'EST. 2016',
    city: 'CITY',
    footer: 'YOUR FOOTER LINE',
    year: '2016',
    countFrom: 2026,
    clientsFixed: ['Client A', 'Client B', 'Client C', 'Client D'],
    clientsOthers: ['Client E', 'Client F', 'Client G', 'Client H', 'Client I', 'Client J', 'Client K', 'Client L'],
    monocle: null,
  },
  assets: ['monocle.svg'],
  provenance: [
    'harvardxr-keynote@7c6fbf5 (the 5-step monocle slide)',
    'git/fmx-2026-spatial-storytelling@b035b8c (pixel avatar)',
    'git/nxtbld-2026-productizing-xr@9736254 (config-driven text, mobile CSS)',
    'ibrews/pmre-2026-xr-chitect talk/intro.js @a8a98de (tiBuildLens)',
  ],
  css: `
.slide.sd-mod-core-intro-lens{padding:0;overflow:hidden}
.sd-mod-core-intro-lens .lens-svg{position:absolute;inset:0;width:100%;height:100%}
.sd-mod-core-intro-lens .avatar .av-arms-up{visibility:hidden}
.sd-mod-core-intro-lens .avatar.arm-up .av-arms-down{visibility:hidden}
.sd-mod-core-intro-lens .avatar.arm-up .av-arms-up{visibility:visible}
@media(max-width:900px){
  body:not(.stage-on) .slide.sd-mod-core-intro-lens{min-height:56vw}
}
`,
  render(el, props, ctx) {
    const svgE = ctx.svg;
    const L = props;
    const sequence = L.sequence !== false;

    // ── synthesized sound (Web Audio); ctx.audio() is null in instant mode ──
    function tone(freq, start, dur, type, vol) {
      if (ctx.instant) return; const c = ctx.audio(); if (!c) return;
      try { const now = c.currentTime, o = c.createOscillator(), g = c.createGain(); o.type = type || 'square'; o.frequency.value = freq; o.connect(g); g.connect(c.destination); g.gain.setValueAtTime(vol, now + start); g.gain.exponentialRampToValueAtTime(0.001, now + start + dur); o.start(now + start); o.stop(now + start + dur + 0.01); } catch (e) {}
    }
    const sfx = {
      year() { [[523, 0], [659, .10], [784, .20]].forEach(([f, t]) => tone(f, t, .5, 'sine', .12)); },
      spawn() { [[523, 0], [659, .07], [784, .14], [1047, .22], [1319, .30]].forEach(([f, t]) => tone(f, t, .18, 'sine', .07)); },
      shrink() { [[880, 0], [587, .09], [392, .18]].forEach(([f, t]) => tone(f, t, .12, 'sine', .08)); },
      countTick() { tone(1200 + Math.random() * 200, 0, .04, 'square', .04); },
      chiptune() { [262, 294, 330, 349, 392, 349, 330, 294, 262, 330, 392, 440].forEach((f, i) => tone(f, i * .22, .2, 'square', .04)); },
    };

    // ── pixel avatar (the younger speaker: no beard, headset on) ──
    function avatar(parent) {
      const root = svgE('g', { class: 'avatar' }); root.style.shapeRendering = 'crispEdges'; parent.appendChild(root);
      const SKIN = '#f2c79b', SKIN_DARK = '#d9a77a', HAIR_LIGHT = '#a8602f', HAIR = '#8b4a2a', HAIR_DARK = '#5e2f1a', HAIR_SHADOW = '#3a1c08', SHIRT = '#6a8fd6', SHIRT_DARK = '#4a6fb8', PANTS = '#3f3025', BOOTS = '#1f150c', EYE = '#1a1a26';
      const px = (g, x, y, w, h, fill) => g.appendChild(svgE('rect', { x, y, width: w, height: h, fill }));
      const body = svgE('g', { class: 'av-body' });
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
      px(body, -4, -12, 8, 3, SKIN_DARK);
      px(body, -12, -9, 24, 18, SHIRT); px(body, -12, -9, 24, 3, SHIRT_DARK); px(body, -12, 6, 24, 3, SHIRT_DARK);
      px(body, -12, 9, 12, 14, PANTS); px(body, 0, 9, 12, 14, PANTS); px(body, -2, 9, 4, 14, '#2a1f18');
      px(body, -12, 23, 12, 5, BOOTS); px(body, 0, 23, 12, 5, BOOTS);
      root.appendChild(body);
      const armsDown = svgE('g', { class: 'av-arms-down' }); px(armsDown, -18, -8, 6, 14, SHIRT); px(armsDown, -18, 4, 6, 4, SKIN); px(armsDown, 12, -8, 6, 14, SHIRT); px(armsDown, 12, 4, 6, 4, SKIN); root.appendChild(armsDown);
      const armsUp = svgE('g', { class: 'av-arms-up' }); px(armsUp, -18, -22, 6, 14, SHIRT); px(armsUp, -18, -26, 6, 6, SKIN); px(armsUp, 12, -22, 6, 14, SHIRT); px(armsUp, 12, -26, 6, 6, SKIN); root.appendChild(armsUp);
      return root;
    }
    function headset(body) {
      body.querySelector('.worn-headset')?.remove();
      const hs = svgE('g', { class: 'worn-headset' }); hs.style.shapeRendering = 'crispEdges';
      const px = (x, y, w, h, fill) => hs.appendChild(svgE('rect', { x, y, width: w, height: h, fill }));
      px(-13, -27, 26, 1, '#0a0a14'); px(-13, -26, 26, 9, '#1a1a26'); px(-13, -17, 26, 1, '#0a0a14');
      px(-8, -24, 5, 5, '#00d4ff'); px(3, -24, 5, 5, '#00d4ff'); px(-7, -23, 1, 1, '#fff'); px(4, -23, 1, 1, '#fff');
      px(-13, -23, 1, 3, '#3a3a4e'); px(12, -23, 1, 3, '#3a3a4e');
      body.appendChild(hs);
    }

    const label = String(L.name || '').replace(/[<>&"]/g, '');
    el.innerHTML = `<svg class="lens-svg" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid meet" aria-label="${label}: client orbit"></svg>`;
    const svg = el.querySelector('svg'), CX = 800, CY = 420, R = 200;
    const ringCX = 407, ringCY = 432, ringR = 374, mS = R / ringR, mW = 852 * mS, mH = 877 * mS, mX = CX - ringCX * mS, mY = CY - ringCY * mS;
    svg.appendChild(svgE('circle', { cx: CX, cy: CY, r: R, fill: 'none', stroke: 'rgba(255,255,255,.12)', 'stroke-width': '28' }));
    svg.appendChild(svgE('circle', { cx: CX, cy: CY, r: R, fill: 'none', stroke: 'rgba(255,255,255,.06)', 'stroke-width': '34' }));
    [-1.41, -0.2].forEach(a => svg.appendChild(svgE('circle', { cx: CX + (R + 16) * Math.cos(a), cy: CY + (R + 16) * Math.sin(a), r: '8', fill: 'none', stroke: 'rgba(255,255,255,.1)', 'stroke-width': '5' })));
    const ex = CX + (775 - 407) * mS, ey = CY + (788 - 432) * mS, eyeA = Math.atan2(ey - CY, ex - CX);
    const cs = { x: CX + R * Math.cos(eyeA), y: CY + R * Math.sin(eyeA) }, ctl = { x: (cs.x + ex) / 2 + 15 * Math.cos(eyeA + Math.PI / 2), y: (cs.y + ey) / 2 + 15 * Math.sin(eyeA + Math.PI / 2) };
    svg.appendChild(svgE('path', { d: `M${cs.x} ${cs.y} Q${ctl.x} ${ctl.y} ${ex} ${ey}`, fill: 'none', stroke: 'rgba(255,255,255,.08)', 'stroke-width': '4', 'stroke-linecap': 'round' }));
    svg.appendChild(svgE('circle', { cx: ex, cy: ey, r: '18', fill: 'none', stroke: 'rgba(255,255,255,.1)', 'stroke-width': '5' }));
    const pulseImg = svgE('image', { href: L.monocle || ctx.asset('monocle.svg'), x: mX + 1, y: mY - 4, width: mW, height: mH, opacity: '0' }); svg.appendChild(pulseImg);
    const txt = (str, x, y, size, weight, ls, fill) => { const t = svgE('text', { x, y, 'text-anchor': 'middle', 'dominant-baseline': 'middle', fill, 'font-family': 'Space Grotesk,sans-serif', 'font-size': size, 'font-weight': weight, 'letter-spacing': ls }); t.textContent = str; svg.appendChild(t); return t; };
    const heads = [txt(L.name || '', CX + 2, CY - 16, 42, 700, 6, 'rgba(255,255,255,.85)'), txt(L.tagline || '', CX, CY + 18, 16, 400, 4, 'rgba(255,255,255,.35)'), txt(L.est || '', CX, CY + 42, 14, 400, 5, 'rgba(255,255,255,.30)'), txt(L.city || '', CX, CY + 64, 13, 400, 6, 'rgba(255,255,255,.20)')];
    const foot = svgE('text', { x: CX, y: 830, 'text-anchor': 'middle', fill: 'rgba(255,255,255,.25)', 'font-family': 'Space Grotesk,sans-serif', 'font-size': '14', 'letter-spacing': '2' }); foot.textContent = L.footer || ''; svg.appendChild(foot);
    // Four anchors at 12/3/6/9 o'clock, the rest two per gap
    const fixed = (L.clientsFixed || []).slice(0, 4).map((name, i) => ({ name, angle: -Math.PI / 2 + i * Math.PI / 2 }));
    const all = [...fixed, ...(L.clientsOthers || []).map((name, i) => { const from = -Math.PI / 2 + (i % 4) * Math.PI / 2; return { name, angle: from + (Math.PI / 2) * (i < 4 ? 1 / 3 : 2 / 3) }; })].sort((a, b) => a.angle - b.angle);
    const oR = R + 110, clients = all.map(({ name, angle }) => { const t = txt(String(name).toUpperCase(), CX + Math.cos(angle) * oR, CY + Math.sin(angle) * oR, 18, 600, 2.5, 'rgba(255,255,255,.6)'); t.dataset.a = angle; return t; });
    const texts = [...heads, foot, ...clients];
    const C = ctx.clock; let hum = null, ang = 0, tt = 0, av = null;
    function place() { clients.forEach(c => { const a = +c.dataset.a + ang; c.setAttribute('x', CX + Math.cos(a) * oR); c.setAttribute('y', CY + Math.sin(a) * oR); c.setAttribute('fill', `rgba(255,255,255,${(0.3 + 0.5 * (1 - (Math.sin(a) + 1) / 2)).toFixed(2)})`); }); }
    function startHum() { if (ctx.instant) return; const c = ctx.audio(); if (!c) return; try { const g = c.createGain(); g.gain.value = 0; g.connect(c.destination); const oscs = [[68, 1], [136, .55], [204, .25]].map(([f, rel]) => { const o = c.createOscillator(), og = c.createGain(); o.type = 'sine'; o.frequency.value = f; og.gain.value = rel; o.connect(og); og.connect(g); o.start(); return o; }); g.gain.setValueAtTime(0, c.currentTime); g.gain.linearRampToValueAtTime(.091, c.currentTime + 1.2); hum = { c, g, oscs }; } catch (e) {} }
    // The hum's fade-out must finish after the clock is stopped on leave, so these two timers are deliberately plain setTimeout.
    function stopHum() { const h = hum; hum = null; if (!h) return; try { if (h.c.state !== 'closed') { h.g.gain.setValueAtTime(h.g.gain.value, h.c.currentTime); h.g.gain.linearRampToValueAtTime(0, h.c.currentTime + .6); setTimeout(() => h.oscs.forEach(o => { try { o.stop(); } catch (e) {} }), 700); } } catch (e) {} }
    function orbit() { ang += .003; tt += .02; place(); pulseImg.setAttribute('opacity', (.06 + .06 * Math.sin(tt)).toFixed(3)); if (hum && hum.c.state !== 'closed') hum.g.gain.setTargetAtTime(.056 + .07 * ((Math.sin(tt) + 1) / 2), hum.c.currentTime, .08); C.raf(orbit); }
    function clear() { svg.querySelectorAll('.ti-lens-x').forEach(n => n.remove()); av = null; }

    function enter() {
      clear(); stopHum(); ang = 0; tt = 0; place();
      texts.forEach(t => { t.style.transition = 'none'; t.style.opacity = ''; });
      if (ctx.instant) { pulseImg.setAttribute('opacity', '.1'); return; }
      pulseImg.setAttribute('opacity', '.06');
      C.after(400, () => { startHum(); C.raf(orbit); });
    }
    function leave() { stopHum(); }

    function fadeNames() { texts.forEach(t => { t.style.transition = ctx.instant ? 'none' : 'opacity .8s ease-out'; t.style.opacity = '0'; }); stopHum(); }

    function countdown() {
      const from = +L.countFrom || 2026;
      const y = svgE('text', { x: CX, y: CY, 'text-anchor': 'middle', 'dominant-baseline': 'middle', fill: 'rgba(255,255,255,.85)', 'font-family': 'Space Grotesk,sans-serif', 'font-size': '72', 'font-weight': '700', 'letter-spacing': '4', class: 'ti-lens-x ti-lens-count' });
      y.style.transformBox = 'fill-box'; y.style.transformOrigin = 'center'; y.textContent = String(from); svg.appendChild(y);
      // Reduced motion: the live counter's last frame is empty, so show its first value instead (spawn() removes it).
      if (ctx.instant) return;
      y.style.opacity = '0';
      C.after(50, () => { y.style.transition = 'opacity .4s'; y.style.opacity = '1'; });
      C.after(500, () => {
        y.style.transition = ''; const t0 = performance.now(); let last = -1;
        const frame = now => { const k = Math.min(1, (now - t0) / 3000), cur = Math.round(from - k * 126); y.textContent = String(cur); if (cur !== last) { if (cur > from - 51) sfx.countTick(); last = cur; }
          const ct = Math.min(1, Math.max(0, (from - cur) / 16)); y.setAttribute('fill', `rgb(${Math.round(255 * (1 - ct))},${Math.round(255 - 43 * ct)},255)`);
          if (cur <= from - 56) { const f = Math.min(1, (from - 56 - cur) / 20); y.style.opacity = (1 - f).toFixed(3); y.style.transform = `scale(${(1 - .15 * f).toFixed(3)})`; }
          if (k < 1) C.raf(frame); else y.style.opacity = '0'; };
        C.raf(frame);
      });
    }

    const tf = (x, y, k) => av.setAttribute('transform', `translate(${x.toFixed(1)},${y.toFixed(1)}) scale(${k.toFixed(3)})`);
    const ease = k => k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
    function spawn() {
      svg.querySelectorAll('.ti-lens-av').forEach(n => n.remove());
      if (ctx.instant) svg.querySelectorAll('.ti-lens-count').forEach(n => n.remove());
      av = svgE('g', { class: 'ti-lens-x ti-lens-av', transform: `translate(${CX},${CY}) scale(1.2)` });
      const root = avatar(av); headset(root.querySelector('.av-body')); svg.appendChild(av);
      if (ctx.instant) return;
      root.classList.add('arm-up'); av.style.opacity = '0'; av.style.transition = 'opacity .5s';
      C.after(50, () => { av.style.opacity = '1'; sfx.spawn(); });
      C.after(1500, () => root.classList.remove('arm-up'));
    }
    function shrink() {
      if (!av) spawn();
      if (ctx.instant) { tf(ex, ey, .4); return; }
      sfx.shrink(); const t0 = performance.now();
      const frame = now => { const k = Math.min(1, (now - t0) / 1500), e = ease(k); tf(CX + (ex - CX) * e, CY + (ey - CY) * e, 1.2 - .8 * e); if (k < 1) C.raf(frame); };
      C.raf(frame);
    }
    function dash() {
      if (!av) spawn();
      const rx = CX + R * Math.cos(eyeA), ry = CY + R * Math.sin(eyeA), SIX = Math.PI / 2;
      const trail = () => { const p = svgE('path', { d: '', fill: 'none', stroke: 'rgba(0,212,255,.4)', 'stroke-width': '2', 'stroke-dasharray': '6 4', 'stroke-linecap': 'round', class: 'ti-lens-x' }); svg.insertBefore(p, av); return p; };
      const yearLabel = () => { const l = svgE('text', { x: CX, y: CY + R + 52, 'text-anchor': 'middle', fill: 'rgba(0,212,255,.8)', 'font-family': 'Space Grotesk,sans-serif', 'font-size': '18', 'font-weight': '600', 'letter-spacing': '2', class: 'ti-lens-x' }); l.textContent = L.year || ''; svg.appendChild(l); return l; };
      const arcPts = n => Array.from({ length: n + 1 }, (_, i) => { const a = eyeA + (SIX - eyeA) * (i / n); return `${(CX + R * Math.cos(a)).toFixed(1)},${(CY + R * Math.sin(a)).toFixed(1)}`; });
      if (ctx.instant) { trail().setAttribute('d', `M${ex.toFixed(1)},${ey.toFixed(1)} L${rx.toFixed(1)},${ry.toFixed(1)}`); trail().setAttribute('d', 'M' + arcPts(24).join(' L')); tf(CX, CY + R, .4); yearLabel(); return; }
      sfx.chiptune();
      const tA = trail(), pA = [], t0 = performance.now();
      const phaseA = now => { const e = ease(Math.min(1, (now - t0) / 700)), x = ex + (rx - ex) * e, y = ey + (ry - ey) * e; tf(x, y, .4); pA.push(`${x.toFixed(1)},${y.toFixed(1)}`); if (pA.length > 1) tA.setAttribute('d', 'M' + pA.join(' L')); if (e < 1) { C.raf(phaseA); return; }
        const tB = trail(), pB = [], t1 = performance.now();
        const phaseB = n2 => { const k = Math.min(1, (n2 - t1) / 1940), a = eyeA + (SIX - eyeA) * ease(k), x2 = CX + R * Math.cos(a), y2 = CY + R * Math.sin(a); tf(x2, y2, .4); pB.push(`${x2.toFixed(1)},${y2.toFixed(1)}`); if (pB.length > 1) tB.setAttribute('d', 'M' + pB.join(' L')); if (k < 1) { C.raf(phaseB); return; }
          const l = yearLabel(); l.style.opacity = '0'; C.after(50, () => { l.style.transition = 'opacity .5s'; l.style.opacity = '1'; sfx.year(); }); };
        C.raf(phaseB); };
      C.raf(phaseA);
    }

    const clicks = [fadeNames, countdown, spawn, shrink, dash];
    return { enter, leave, step(n) { if (sequence) clicks[n - 1](); } };
  },
});
