# Slide modules

A slide module is one slide's behavior in a folder you can copy: `slides/<namespace>/<id>/slide.js` plus whatever
assets it needs. A talk uses it as a case in `SECTIONS`, and overrides its text through props:

```js
cases: [
  { use: 'core/venn', props: { labels: ['Architecture', 'Theater', 'Realtime Tech'] }, notes: 'Let it orbit twice.' },
  { title: 'An ordinary slide', subtitle: 'still plain data', img: 'images/x.png', bullets: ['…'] },
]
```

Everything else about a case still works on a module slide: `notes`, `opt` / `keep` in talks that have an options
picker, the step indicator, the timing estimate, `?print`, `?shot=N`, `?notes`. The deck owns navigation and chrome
(`?chrome=full|quiet|none`); the module owns what is inside the slide.

## Library vs talk

- `slides/core/` in [ibrews/spatial-deck](https://github.com/ibrews/spatial-deck) is the shared library. Modules there
  hold **no talk text**: every word on screen is a prop with a neutral default. (A push hook refuses talk content on
  spatial-deck; keep it that way by construction.)
- A talk repo keeps its own modules under its own namespace (`slides/pmre/…`) and pulled copies of library modules
  under `slides/core/…`. A pulled copy carries `.pulled.json` (source repo, commit, file hashes), so a talk pins the
  version it rehearsed with and nothing changes under it when the library moves.

## The contract

```js
SD.defineSlide({
  id: 'core/venn',          // "<namespace>/<id>", the folder it lives in
  steps: 0,                 // clicks inside the slide; a number, or (props) => number. The deck asks for exactly this
  duration: 9,              // seconds of entry motion (enables seek-based MP4 rendering)
  props: { … },             // defaults; a case's props override them (shallow: an array prop is replaced whole)
  css: `…`,                 // optional; injected once. Scope it under .sd-mod-<namespace>-<id>
  assets: ['icon.png'],     // every file in the folder besides slide.js, so `slide.py pull <url>` can fetch them
  shared: ['kit/sprite.js'],// files under slides/ that several modules use; pull copies them along
  provenance: ['harvardxr-keynote@7c6fbf5 index.html buildVennSlide'],
  shows: ['avatar'],        // optional: what the slide already shows; a case can override with its own `shows`
  render(el, props, ctx) {  // build the slide's DOM into el; return the instance (all methods optional)
    return {
      enter() {},           // the slide became active: play the entry motion from t = 0 (state = step 0)
      step(n) {},           // click n of steps, called in order 1..steps
      leave() {},           // the slide stopped being active (ctx.clock is already stopped)
      seek(t) {},           // deterministic frame of the entry motion at t seconds: no timers, no Math.random
      staticFrame() {},     // final frame with every step applied (default: instant enter + every step)
    };
  },
});
```

`ctx` gives a module what it needs without reaching into the deck:

| field | what it is |
|---|---|
| `ctx.instant` | true for `?print`, `?shot=N`, `?static`, `?reduced` and prefers-reduced-motion: jump every beat to its final frame, start no timers, make no sound |
| `ctx.clock` | `after(ms,fn)`, `every(ms,fn)`, `raf(fn)`, `loop(fn(sec))`; the deck stops all of it on leave, so a slide never leaks timers |
| `ctx.audio()` | an AudioContext (or null in instant mode); recreated after the deck closes sound on slide change |
| `ctx.asset(p)` | URL of a file in the module's folder, wherever the module was pulled to |
| `ctx.svg(tag, attrs)` | the deck's SVG element helper |
| `ctx.look()` | current look id (`noir`, `sheet`, `house`, …) |
| `ctx.props`, `ctx.steps`, `ctx.slide`, `ctx.params` | resolved props, resolved step count, the slide element, URL params |

**Style from the look, not from the module.** Color a module with the deck's CSS variables (`var(--teal)`,
`var(--text)`, `var(--ink)` …) so every `styles/` look recolors it. Hard-coded hex is only for pixel art that is the
same in every look.

**Deck-level layers listen, they don't patch.** Every slide change (module or not) fires
`document.addEventListener('sd:slide', e => …)` with `e.detail = {index, slide, type, section, year, module, shows}`.
A persistent companion (a journey minimap, a walking sprite) reads the chapter from `section`/`year` and steps aside
when `shows` includes what it would draw (`'avatar'`). The event does not fire in `?print`/`?shot`.

**Never register `slideSteps` yourself.** The deck builds a module's clicks from `steps`; a module that adds its own is
exactly the "substeps came back by accident" failure, and the steps sweep fails it.

## iframe modules

A seekable HTML motion graphic is a module too: `SD.defineSlide({ id, frame: 'lane.html', steps, duration, props })`.
The deck puts `slides/<ns>/<id>/lane.html` in a full-bleed iframe and drives it over `postMessage`, so an iframe gets
the same slide-entered and next-click signals an inline module gets:

```
deck → frame  {sd:'spatial-deck', v:1, type:'enter' | 'step' | 'leave' | 'seek' | 'static', n?, t?, instant?}
frame → deck  {sd:'spatial-deck', v:1, type:'ready', steps, duration}
```

The frame loads `../../sd-frame.js`, builds its DOM synchronously from `SDFrame.props(defaults)` (the deck passes props
in the URL fragment, `#sdp=<json>`), then calls `SDFrame.init({ duration, steps, onStep })`. Steps are visible to CSS
as `html[data-step="2"]`. Off-screen the frame parks on its final frame; on enter it replays from 0 without a reload
(no white flash). It still works on its own: opened directly it plays, `?static` is the final frame, `?t=4` the
frame at 4 s, which is what `tools/render_motion.mjs` uses for MP4s. postMessage works from `file://`, so this needs
no server. Animate only with CSS animations or WAAPI (`document.getAnimations()` must see everything); the gotchas
are in the KB technique *seekable-html-motion-graphics-for-decks*.

## Tools

```bash
python3 tools/slide.py list ../pmre-2026-xr-chitect                 # modules, steps, durations, how often each is used
python3 tools/slide.py list https://ibrews.github.io/pmre-2026-xr-chitect/
python3 tools/slide.py pull ../spatial-deck core/venn --into ../my-talk      # copies files, writes .pulled.json, syncs
python3 tools/slide.py sync ../my-talk                               # rewrite index.html's module list from slides/
python3 tools/slide.py check ../my-talk                              # every use: resolves, every file declared
node tools/sweep_deck.mjs http://localhost:8000/ /tmp/sweep 1920 1080 steps --steps   # screenshot EVERY substep
bash tools/tests/test_steps.sh                                       # the steps lint must fail its broken fixtures
```

`sweep_deck.mjs --steps` presses the real ArrowRight key on every slide until the slide changes, screenshots each
substep into the contact sheets (captioned `12 · step 3`), and fails the run when declared steps differ from
reachable steps, when an iframe reports a different count than the deck asks for, or when a click changes nothing on
screen (a dead step).

## Why it is built this way

- **Classic scripts, not ES modules.** `import()` of a local file is blocked on `file://`, and a Spatial Deck has to
  open by double-click. `slide.js` calls `SD.defineSlide()` from an ordinary `<script src>`, listed between the
  `SD SLIDE MODULES` sentinels in `index.html` (`slide.py sync` keeps that list honest).
- **`render()` returns an instance.** The same module can appear twice in one talk (two lane variants) without the
  two slides sharing timers or state.
- **Steps go through `slideSteps`.** Every existing deck feature that knows about clicks (indicator, timing estimate,
  print step-completion, autoplay) works for modules with no extra code.
