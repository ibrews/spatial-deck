/* core/intro-avatar: the 8-bit speaker intro. A pixel avatar walks in, jumps, punches a "?" block and puts on a headset (auto
   on arrival), then three clicks: 1 name + bio, 2 a second power-up (hits the badge block, doubles in size, runs back and forth
   throwing badge fireballs), 3 the stat cards tally up. Every visible string is a prop; the defaults are neutral placeholders.
   Props: eyebrow, name (HTML allowed, e.g. "First<br>Last"), role, bio, ue5 (the second power-up's text, "\n" = line break;
   `power2` is accepted as an alias), withBeard, stats [{n,l}] (a numeric n like "100+" tallies up), img {badge, logo}
   (badge = the block you hit; logo = the other fireball sprite, defaults to the badge). Ported from the PMRE deck's
   talk/intro.js (tiBuildAlex): same SVG, timings, sounds and CSS; the lifecycle now comes from the deck runtime, the timers
   from ctx.clock and nothing is global, so two copies on one deck do not interfere. */
SD.defineSlide({
  id: 'core/intro-avatar',
  steps: 3,
  props: {
    eyebrow: 'Your Speaker',
    name: 'Your Name',
    role: 'Your Role',
    bio: 'One or two sentences about who you are and what you build.',
    ue5: 'A second credential, certification or superpower.\nA second line if you need one.',
    withBeard: false,
    stats: [{ n: '10', l: 'Years' }, { n: '20', l: 'Projects' }, { n: '30', l: 'Talks' }, { n: '100+', l: 'Things built' }],
    img: {},
  },
  assets: ['badge.svg', 'logo.svg'],
  provenance: [
    'git/fmx-2026-spatial-storytelling@b035b8c (walker, power-up, fireballs, tallies)',
    'git/nxtbld-2026-productizing-xr@9736254 (config-driven text, mobile CSS)',
    'harvardxr-keynote@7c6fbf5 (pixel avatar)',
    'ibrews/pmre-2026-xr-chitect talk/intro.js @a8a98de (tiBuildAlex)',
  ],
  css: `
.slide.sd-mod-core-intro-avatar{padding:0;align-items:center;justify-content:center}
.sd-mod-core-intro-avatar .intro-grid{display:flex;align-items:center;gap:clamp(40px,calc(5*var(--vw)),90px);width:100%;max-width:1500px;padding:clamp(50px,calc(5*var(--vw)),90px) clamp(60px,calc(7*var(--vw)),140px)}
.sd-mod-core-intro-avatar .intro-stage{flex:0 0 42%;max-width:560px;aspect-ratio:1/1;position:relative}
.sd-mod-core-intro-avatar .intro-stage svg{width:100%;height:100%;overflow:visible}
.sd-mod-core-intro-avatar .intro-content{flex:1;text-align:left;min-width:0}
.sd-mod-core-intro-avatar .intro-eyebrow{font-size:clamp(.78rem,calc(1.1*var(--vw)),1rem);font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:var(--teal);margin-bottom:18px}
.sd-mod-core-intro-avatar .intro-title{font-size:clamp(2.6rem,calc(5.5*var(--vw)),5.2rem);font-weight:700;line-height:1.02;letter-spacing:-.02em;margin-bottom:14px;background:linear-gradient(130deg,#fff 20%,#a5d8ff 55%,#c5b6ff 90%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.sd-mod-core-intro-avatar .intro-role{font-size:clamp(1rem,calc(1.45*var(--vw)),1.35rem);font-weight:600;color:var(--text);letter-spacing:.04em;margin:0 0 20px}
.sd-mod-core-intro-avatar .intro-sub{font-size:clamp(1rem,calc(1.5*var(--vw)),1.3rem);color:var(--dim);line-height:1.55;margin-bottom:24px;max-width:640px}
.sd-mod-core-intro-avatar .intro-stats{display:flex;gap:14px;flex-wrap:nowrap}
.sd-mod-core-intro-avatar .intro-stat{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:12px;padding:16px 18px;flex:1;min-width:0}
.sd-mod-core-intro-avatar .intro-stat .num{display:block;font-size:clamp(1.4rem,calc(2.2*var(--vw)),2rem);font-weight:700;color:var(--teal);letter-spacing:-.02em;margin-bottom:6px;transform-origin:left bottom}
.sd-mod-core-intro-avatar .intro-stat .lbl{display:block;font-size:clamp(.6rem,calc(.82*var(--vw)),.76rem);font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.55);line-height:1.3}
.sd-mod-core-intro-avatar .intro-stage .stage-floor{fill:rgba(0,212,255,.10);stroke:rgba(0,212,255,.28);stroke-width:1}
.sd-mod-core-intro-avatar .intro-stage .ti-anim{transform-box:fill-box;transform-origin:center bottom}
.sd-mod-core-intro-avatar .intro-stage .ti-block{transform-box:fill-box;transform-origin:center}
.sd-mod-core-intro-avatar .ti-fade{opacity:0;transition:opacity .6s}
.sd-mod-core-intro-avatar .ti-fade.on{opacity:1}
.sd-mod-core-intro-avatar.ti-now .ti-fade{transition:none}
.sd-mod-core-intro-avatar .avatar .av-arms-up{visibility:hidden}
.sd-mod-core-intro-avatar .avatar.arm-up .av-arms-down{visibility:hidden}
.sd-mod-core-intro-avatar .avatar.arm-up .av-arms-up{visibility:visible}
@keyframes introWalk{0%{transform:translate(-200px,0)}100%{transform:translate(160px,0)}}
@keyframes introJumpUp{0%{transform:translate(160px,0) scale(1,1)}30%{transform:translate(160px,-16px) scale(.95,1.05)}100%{transform:translate(160px,-80px) scale(1,1)}}
@keyframes introFallDown{0%{transform:translate(160px,-80px) scale(1.4)}100%{transform:translate(160px,0) scale(1.4)}}
@keyframes introPowerUp{0%{transform:translate(160px,-80px) scale(1);filter:brightness(1)}35%{transform:translate(160px,-80px) scale(1.2);filter:brightness(1.8)}60%{transform:translate(160px,-80px) scale(1.1);filter:brightness(1.3)}100%{transform:translate(160px,-80px) scale(1.4);filter:brightness(1)}}
@keyframes introHeadsetBob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@keyframes introHeadsetGrab{0%{opacity:1;transform:scale(1)}50%{opacity:1;transform:scale(1.3) translateY(-8px)}100%{opacity:0;transform:scale(0) translateY(-24px)}}
@keyframes introSparkle{0%{opacity:0;transform:translate(0,0) scale(.3)}12%{opacity:1;transform:translate(calc(var(--tx)*.15),calc(var(--ty)*.15)) scale(1.5)}55%{opacity:1;transform:translate(calc(var(--tx)*.6),calc(var(--ty)*.6)) scale(1)}100%{opacity:0;transform:translate(var(--tx),var(--ty)) scale(.3)}}
@keyframes introFlash{0%{opacity:0}8%{opacity:.7}100%{opacity:0}}
@keyframes ue5JumpUp{0%{transform:translate(0,0) scale(1.5)}25%{transform:translate(0,-20px) scale(1.4,1.6)}100%{transform:translate(0,-130px) scale(1.5)}}
@keyframes ue5PowerUp{0%{transform:translate(0,-130px) scale(1.5);filter:brightness(1)}30%{transform:translate(0,-130px) scale(1.8);filter:brightness(1.7)}55%{transform:translate(0,-130px) scale(1.4);filter:brightness(1.3)}100%{transform:translate(0,-130px) scale(2);filter:brightness(1)}}
@keyframes ue5FallDown{0%{transform:translate(0,-130px) scale(2)}100%{transform:translate(0,0) scale(2)}}
@media(max-width:900px){
  body:not(.stage-on) .sd-mod-core-intro-avatar .intro-grid{flex-direction:column;text-align:center;padding:24px 16px;gap:12px}
  body:not(.stage-on) .sd-mod-core-intro-avatar .intro-stage{flex:none;width:70%;max-width:280px}
  body:not(.stage-on) .sd-mod-core-intro-avatar .intro-content{text-align:center}
  body:not(.stage-on) .sd-mod-core-intro-avatar .intro-sub{margin-left:auto;margin-right:auto}
  body:not(.stage-on) .sd-mod-core-intro-avatar .intro-stats{flex-wrap:wrap}
  body:not(.stage-on) .sd-mod-core-intro-avatar .intro-stat{flex:1 1 40%}
}
/* Non-noir looks: the same overrides PMRE kept in its bake step. :not(#_) lifts specificity above the module rules. */
body:where([data-look]:not([data-look="noir"])):not(#_) .sd-mod-core-intro-avatar .intro-title{background:none;-webkit-text-fill-color:currentColor;color:var(--ink);font-family:var(--font-display)}
body:where([data-look]:not([data-look="noir"])):not(#_) .sd-mod-core-intro-avatar .intro-eyebrow,body:where([data-look]:not([data-look="noir"])):not(#_) .sd-mod-core-intro-avatar .intro-stat .num{color:var(--acc-1)}
body:where([data-look]:not([data-look="noir"])):not(#_) .sd-mod-core-intro-avatar .intro-role{color:var(--ink)}
body:where([data-look]:not([data-look="noir"])):not(#_) .sd-mod-core-intro-avatar .intro-sub{color:var(--ink-2)}
body:where([data-look]:not([data-look="noir"])):not(#_) .sd-mod-core-intro-avatar .intro-stat{background:transparent;border:1px solid var(--rule);border-radius:0}
body:where([data-look]:not([data-look="noir"])):not(#_) .sd-mod-core-intro-avatar .intro-stat .lbl{color:var(--ink-2)}
`,
  render(el, props, ctx) {
    const svgE = ctx.svg;
    const IMG = props.img || {};
    const badgeSrc = IMG.badge || ctx.asset('badge.svg');
    const logoSrc = IMG.logo || (IMG.badge ? IMG.badge : ctx.asset('logo.svg'));
    const ue5 = props.power2 != null ? props.power2 : props.ue5;

    // ── synthesized sound (Web Audio); ctx.audio() is null in instant mode ──
    function tone(freq, start, dur, type, vol) {
      if (ctx.instant) return; const c = ctx.audio(); if (!c) return;
      try { const now = c.currentTime, o = c.createOscillator(), g = c.createGain(); o.type = type || 'square'; o.frequency.value = freq; o.connect(g); g.connect(c.destination); g.gain.setValueAtTime(vol, now + start); g.gain.exponentialRampToValueAtTime(0.001, now + start + dur); o.start(now + start); o.stop(now + start + dur + 0.01); } catch (e) {}
    }
    const sfx = {
      powerUp() { [[130, 0, .09], [196, .08, .09], [262, .16, .09], [349, .24, .09], [523, .32, .09], [698, .40, .09], [1047, .48, .12], [784, .61, .18, 'sine', .08], [1047, .80, .25, 'sine', .1]].forEach(([f, s, d, t, v]) => tone(f, s, d, t || 'square', v || .12)); },
      zap() { if (ctx.instant) return; const c = ctx.audio(); if (!c) return; try { const now = c.currentTime, o = c.createOscillator(), g = c.createGain(); o.type = 'sawtooth'; o.frequency.setValueAtTime(600, now); o.frequency.exponentialRampToValueAtTime(200, now + .15); o.connect(g); g.connect(c.destination); g.gain.setValueAtTime(.06, now); g.gain.exponentialRampToValueAtTime(.001, now + .15); o.start(now); o.stop(now + .15); } catch (e) {} },
      tick() { tone(880, 0, .06, 'sine', .04); },
      ching() { [[1047, 0, .18], [1319, .05, .18], [1568, .1, .25]].forEach(([f, s, d]) => tone(f, s, d, 'sine', .06)); },
    };

    // ── pixel avatar ──
    function avatar(parent, opts = {}) {
      const withBeard = !!opts.withBeard;
      const root = svgE('g', { class: 'avatar' }); root.style.shapeRendering = 'crispEdges'; parent.appendChild(root);
      const SKIN = '#f2c79b', SKIN_DARK = '#d9a77a', HAIR_LIGHT = '#a8602f', HAIR = '#8b4a2a', HAIR_DARK = '#5e2f1a', HAIR_SHADOW = '#3a1c08', BEARD = '#6e3a1e', BEARD_LIGHT = '#8a4f2a', SHIRT = '#6a8fd6', SHIRT_DARK = '#4a6fb8', PANTS = '#3f3025', BOOTS = '#1f150c', EYE = '#1a1a26';
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
      if (withBeard) { px(body, -12, -22, 4, 5, BEARD); px(body, 8, -22, 4, 5, BEARD); px(body, -12, -20, 5, 3, BEARD); px(body, 7, -20, 5, 3, BEARD); px(body, -12, -17, 4, 1, BEARD); px(body, 8, -17, 4, 1, BEARD); px(body, -7, -19, 14, 2, BEARD); px(body, -6, -19, 12, 1, BEARD_LIGHT); px(body, -2, -16, 4, 1, BEARD); px(body, -12, -16, 24, 2, BEARD); px(body, -12, -14, 24, 2, BEARD); px(body, -10, -12, 20, 1, BEARD); }
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

    const stats = (props.stats || []).map(x => `<div class="intro-stat"><span class="num" data-tally="${x.n}">${x.n}</span><span class="lbl">${x.l}</span></div>`).join('');
    el.innerHTML = `<div class="intro-grid"><div class="intro-stage"><svg viewBox="0 0 400 400" aria-hidden="true"></svg></div><div class="intro-content"><div class="intro-eyebrow ti-fade">${props.eyebrow || ''}</div><h1 class="intro-title ti-fade">${props.name || ''}</h1>${props.role ? `<p class="intro-role ti-fade">${props.role}</p>` : ''}<p class="intro-sub ti-fade">${props.bio || ''}</p><p class="intro-sub intro-sub-ue5 ti-fade">${(ue5 || '').replace(/\n/g, '<br>')}</p><div class="intro-stats ti-fade">${stats}</div></div></div>`;
    const svg = el.querySelector('svg'), q = sel => el.querySelector(sel);
    const bioEls = [q('.intro-eyebrow'), q('.intro-title'), q('.intro-role'), q('.intro-sub:not(.intro-sub-ue5)')].filter(Boolean);
    const ue5Text = q('.intro-sub-ue5'), statsRow = q('.intro-stats');
    svg.appendChild(svgE('rect', { x: 30, y: 300, width: 340, height: 6, class: 'stage-floor', rx: '2' }));
    // "?" block holding a headset at (240,200)
    const bPos = svgE('g', { transform: 'translate(240,200)' }), bAnim = svgE('g', { class: 'ti-block' }); bPos.appendChild(bAnim);
    bAnim.appendChild(svgE('rect', { x: -22, y: -22, width: 44, height: 44, fill: '#f59e0b', stroke: '#b45309', 'stroke-width': '2', rx: '3' }));
    bAnim.appendChild(svgE('rect', { x: -18, y: -18, width: 36, height: 36, fill: 'none', stroke: '#fde68a', 'stroke-width': '1', rx: '1' }));
    bAnim.appendChild(svgE('rect', { x: -13, y: -7, width: 26, height: 14, rx: '5', fill: '#1a1a26' }));
    bAnim.appendChild(svgE('circle', { cx: -6, cy: 0, r: '3', fill: '#00d4ff' })); bAnim.appendChild(svgE('circle', { cx: 6, cy: 0, r: '3', fill: '#00d4ff' }));
    bAnim.appendChild(svgE('rect', { x: -13, y: -9, width: 26, height: 2, fill: '#0a0a14' }));
    svg.appendChild(bPos);
    // badge block at (80,140), hit by the second power-up
    const uPos = svgE('g', { transform: 'translate(80,140)' }), uAnim = svgE('g', { class: 'ti-block' }); uPos.appendChild(uAnim);
    uAnim.appendChild(svgE('image', { href: badgeSrc, x: -22, y: -22, width: 44, height: 44 }));
    svg.appendChild(uPos);
    // Walker
    const walker = svgE('g', { class: 'stage-walker', transform: 'translate(80,270)' }), anim = svgE('g', { class: 'ti-anim' });
    walker.appendChild(anim); svg.appendChild(walker);
    const avBody = avatar(anim, { withBeard: !!props.withBeard }).querySelector('.av-body');
    // 24 sparkles + flash
    const sparkles = svgE('g', { opacity: '0' }), COLORS = ['#fde68a', '#00d4ff', '#a78bfa', '#f59e0b', '#fff', '#fb7185'];
    for (let i = 0; i < 24; i++) { const a = (i / 24) * Math.PI * 2 + (Math.random() - .5) * .4, d = 55 + Math.random() * 45; const sp = svgE('circle', { cx: 240, cy: 200, r: (1.2 + Math.random() * 2.2).toFixed(1), fill: COLORS[i % COLORS.length] }); sp.style.setProperty('--tx', (Math.cos(a) * d).toFixed(1) + 'px'); sp.style.setProperty('--ty', (Math.sin(a) * d).toFixed(1) + 'px'); sp.style.transformOrigin = '240px 200px'; sparkles.appendChild(sp); }
    svg.appendChild(sparkles);
    const flash = svgE('rect', { x: 0, y: 0, width: 400, height: 400, fill: '#fff', opacity: '0', 'pointer-events': 'none' }); svg.appendChild(flash);
    const nums = [...el.querySelectorAll('.num')];

    // Two independent timer groups on top of ctx.clock: E = the entrance (a click mid-walk cancels it), S = the clicks.
    // ctx.clock.stop() on leave still kills both, because they schedule through it.
    const group = () => { let gen = 0; return { after(ms, fn) { const g = gen; ctx.clock.after(ms, () => { if (g === gen) fn(); }); }, raf(fn) { const g = gen; ctx.clock.raf(t => { if (g === gen) fn(t); }); }, stop() { gen++; } }; };
    const E = group(), S = group();

    // Show/hide with .on; instant (or hiding) skips the CSS transition, otherwise stagger via the clock.
    function fade(els, on, instant, stagger) {
      els.forEach((e, i) => { if (!e) return; if (instant || !on) { e.style.transition = 'none'; e.classList.toggle('on', on); void e.offsetWidth; e.style.transition = ''; } else ctx.clock.after((stagger || 0) * i, () => e.classList.add('on')); });
    }
    const setAnim = (v, tf) => { anim.style.animation = v; if (tf !== undefined) anim.style.transform = tf; };
    const pulse = (e, a) => { e.style.animation = 'none'; void e.getBoundingClientRect(); e.style.animation = a; };
    function entranceFinal() { E.stop(); setAnim('none', 'translate(160px,0) scale(1.5)'); anim.style.opacity = '1'; bAnim.style.animation = 'none'; bAnim.style.opacity = '0'; sparkles.setAttribute('opacity', '0'); flash.style.animation = 'none'; headset(avBody); }
    function stop() { E.stop(); S.stop(); svg.querySelectorAll('.ti-fb').forEach(f => f.remove()); }

    function enter() {
      stop(); el.classList.toggle('ti-now', ctx.instant);
      fade([...bioEls, ue5Text, statsRow], false, true);
      nums.forEach(n => { n.textContent = ctx.instant ? n.dataset.tally : (/^\d+\+?$/.test(n.dataset.tally) ? '0' : n.dataset.tally); n.style.transform = ''; });
      uPos.style.opacity = '0'; uAnim.style.opacity = '1'; uAnim.style.animation = 'none'; anim.style.transition = 'none'; anim.style.filter = '';
      if (ctx.instant) { entranceFinal(); return; }
      avBody.querySelector('.worn-headset')?.remove();
      setAnim('none', ''); anim.style.opacity = '0'; bAnim.style.opacity = '1'; bAnim.style.animation = 'introHeadsetBob 1.6s ease-in-out infinite';
      sparkles.setAttribute('opacity', '0'); sparkles.querySelectorAll('circle').forEach(p => p.style.animation = 'none'); flash.style.animation = 'none';
      const D = 300;
      E.after(D, () => { anim.style.opacity = '1'; setAnim('introWalk 2s linear 0s 1 normal both'); });
      E.after(D + 2000, () => setAnim('introJumpUp .4s cubic-bezier(.3,.7,.4,1) 0s 1 normal both'));
      E.after(D + 2400, () => { pulse(flash, 'introFlash .45s ease-out forwards'); bAnim.style.animation = 'introHeadsetGrab .5s ease-out forwards'; sparkles.setAttribute('opacity', '1'); sparkles.querySelectorAll('circle').forEach(p => pulse(p, 'introSparkle 1.1s ease-out forwards')); sfx.powerUp(); setAnim('introPowerUp .8s ease-out forwards'); });
      E.after(D + 2900, () => headset(avBody));
      E.after(D + 3200, () => setAnim('introFallDown .55s cubic-bezier(.55,0,.8,1) forwards'));
      E.after(D + 3780, () => setAnim('none', 'translate(160px,0) scale(1.5)'));
    }

    function showBio() { fade(bioEls, true, ctx.instant, 200); }

    function shootFireball(x, y, dir) {
      const fb = svgE('g', { class: 'ti-fb', transform: `translate(${x},${y})` });
      fb.appendChild(svgE('image', { href: Math.random() < .5 ? badgeSrc : logoSrc, x: -20, y: -20, width: 40, height: 40 }));
      svg.appendChild(fb); sfx.zap();
      let f = 0; const sp = dir * 5.5;
      const spin = () => { f++; const cx = x + sp * f, b = -Math.abs(Math.sin(f * .12)) * 18 * Math.max(0, 1 - f / 40); fb.setAttribute('transform', `translate(${cx},${y + b}) rotate(${f * 12})`); if (f < 55 && cx > 5 && cx < 395) S.raf(spin); else fb.remove(); };
      S.raf(spin);
    }

    function secondPowerUp() {
      entranceFinal(); // pressing → mid-walk lands the entrance first
      fade([ue5Text], false, true); uPos.style.opacity = '1';
      if (ctx.instant) { uAnim.style.opacity = '0'; setAnim('none', 'translate(90px,0) scale(2)'); fade([ue5Text], true, true); return; }
      setAnim('none', 'translate(160px,0) scale(1.5)'); void anim.getBoundingClientRect(); anim.style.transition = 'transform 1.5s linear'; anim.style.transform = 'translate(0,0) scale(1.5)';
      S.after(1500, () => { anim.style.transition = 'none'; void anim.getBoundingClientRect(); setAnim('ue5JumpUp .4s cubic-bezier(.3,.7,.4,1) forwards'); });
      S.after(1900, () => { pulse(flash, 'introFlash .45s ease-out forwards'); uAnim.style.animation = 'introHeadsetGrab .5s ease-out forwards'; sfx.powerUp(); setAnim('ue5PowerUp .8s ease-out forwards'); });
      S.after(2700, () => setAnim('ue5FallDown .55s cubic-bezier(.55,0,.8,1) forwards'));
      S.after(3300, () => {
        fade([ue5Text], true, false); setAnim('none', 'translate(0,0) scale(2)');
        const run = (startX, hop, done) => { let dir = 1, x = startX, fbt = 0, n = 0; const loop = () => { if (n > 180) { done(x); return; } n++; x += dir * 2.8; if (x > 200) dir = -1; if (x < -20) dir = 1; const hy = hop ? -Math.abs(Math.sin(n * .15)) * 8 : 0; anim.style.transform = `translate(${x}px,${hy}px) scale(2)`; if (++fbt > 18 && Math.random() < .18) { shootFireball(80 + x + (dir > 0 ? 25 : -25), 270 + hy, dir); fbt = 0; } S.raf(loop); }; S.raf(loop); };
        run(0, false, () => { anim.style.transform = 'translate(90px,0) scale(2)'; S.after(5000, () => run(90, true, x2 => { anim.style.transform = `translate(${x2}px,0) scale(2)`; })); });
      });
    }

    function showTallies() {
      fade([statsRow], true, ctx.instant);
      if (ctx.instant) { nums.forEach(n => n.textContent = n.dataset.tally); return; }
      S.after(300, () => nums.forEach(e => {
        const m = e.dataset.tally.match(/^(\d+)(\+?)$/); if (!m) return;
        const target = +m[1], suf = m[2] || '', t0 = performance.now(); let last = -1; e.style.display = 'inline-block';
        const frame = t => { const k = Math.min(1, (t - t0) / 1000), cur = Math.round((1 - Math.pow(1 - k, 3)) * target); e.textContent = cur + (k >= 1 ? suf : ''); if (cur !== last && k < 1) { sfx.tick(); last = cur; }
          let y = 0, sx = 1, sy = 1; if (k < .85) y = -Math.sin((k / .85) * Math.PI) * 14; else { const lk = (k - .85) / .15; sy = 1 - .12 * Math.sin(lk * Math.PI); sx = 1 + .12 * Math.sin(lk * Math.PI); }
          e.style.transform = `translateY(${y.toFixed(2)}px) scale(${sx.toFixed(3)},${sy.toFixed(3)})`; if (k < 1) S.raf(frame); else { e.style.transform = ''; sfx.ching(); } };
        S.raf(frame);
      }));
    }

    const clicks = [showBio, secondPowerUp, showTallies];
    return { enter, step(n) { clicks[n - 1](); }, leave: stop };
  },
});
