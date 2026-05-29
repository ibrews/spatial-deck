# Animations

Spatial Deck has three animation layers: slide transitions, per-slide multi-step sequences, and keyframe WAAPI animations on individual elements.

---

## Slide Transitions

Set in the Settings slide. Options: Slide, Fade, Zoom, None. See [Theme & Settings](05-theme-settings.md#transition-style).

---

## Multi-Step Slides (`slideSteps`)

A multi-step slide is one where clicking `→` runs through a sequence of animations before advancing to the next slide. Think: bullet points appearing one at a time, or elements flying in on cue.

### Basic Pattern

```javascript
// Must be inside a setTimeout to defer past the slideSteps declaration
setTimeout(() => {
  const mySlide = allSlides.find(s =>
    s.querySelector?.('.case-title')?.textContent.includes('My Slide Title'));
  if (!mySlide) return;

  slideSteps.set(mySlide, {
    current: 0,
    steps: [
      () => {
        // Step 1: fade in a bullet
        mySlide.querySelectorAll('.case-bullet')[0].style.opacity = '1';
      },
      () => {
        // Step 2: fade in second bullet
        mySlide.querySelectorAll('.case-bullet')[1].style.opacity = '1';
      },
      () => {
        // Step 3: play a sound
        playBing();
      }
    ]
  });
}, 0);
```

### How It Plays

1. Arriving at the slide runs nothing — it shows the initial state.
2. First `→` click calls `steps[0]`.
3. Second `→` calls `steps[1]`.
4. After all steps: `→` advances to the next slide.

The pacing estimator adds +5 seconds per step to the slide's estimated duration.

### Tips

- **Start elements hidden**: set `opacity:0` on elements you want to reveal, then set `opacity:1` in a step.
- **Use CSS transitions**: add `transition: opacity 0.5s ease` so the reveal is smooth, not instant.
- **Undo substep**: pressing `←` while on a stepped slide goes backward through steps before going to the previous slide (controlled by `arrowSubstep` setting).

---

## SFX (Web Audio)

All audio uses the Web Audio API — no external audio files needed.

### Built-in Sounds

```javascript
playWhoosh()   // White-noise bandpass — soft slide transition whoosh
playBing()     // Soft bell — for media cycler transitions or drawing attention
```

Both functions are defined in the main script block and available globally.

### AudioContext Policy

Browsers require user interaction before any `AudioContext` can start. The first time sound plays after a page load, it may be silently blocked. After the user has clicked/pressed anything, audio works fine.

Wrap all audio calls in try/catch:
```javascript
try { playWhoosh(); } catch(e) {}
```

### SFX Cleanup

All `AudioContext` instances are tracked automatically (the constructor is monkey-patched). When `goTo()` navigates to any slide, `window._killAllSfx()` closes all active contexts — no lingering audio from the previous slide's animations.

To register a custom cleanup hook for an animation (e.g., to stop a looping oscillator on slide exit):
```javascript
window._sfxKillHooks = window._sfxKillHooks || [];
window._sfxKillHooks.push(() => { oscillator.stop(); });
```

---

## Keyframe Animations (WAAPI)

The Web Animations API (WAAPI) keyframe system is described in [Move Mode & Layout — Keyframe Animations](04-move-mode.md#keyframe-animations). This section covers the programmatic side.

### Programmatic WAAPI Animation

If you want to animate elements without using the scrubber UI:

```javascript
const el = mySlide.querySelector('.case-title');
el.animate([
  { transform: 'translateX(-40px)', opacity: 0 },
  { transform: 'translateX(0)',     opacity: 1 }
], {
  duration: 600,
  easing: 'ease-out',
  fill: 'forwards'
});
```

WAAPI animations in steps work well — start with the element in its initial state, then trigger `.animate()` in a `slideSteps` step function.

### Lifecycle Management

For animations tied to a slide's presence, use the slide's enter/exit hooks:

```javascript
// Re-usable pattern: init animation on enter, stop on exit
function initMyAnimation(slide) {
  let running = true;
  function frame() {
    if (!running) return;
    // ... your animation logic
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  // Clean up when leaving this slide
  slide._cleanup = () => { running = false; };
}

// Wire it up
initMyAnimation(mySlide);

// In goTo() — the engine calls slide._cleanup?.() when leaving
// (Check your version of the engine; if it doesn't, call cleanup in goTo's observer)
```

The bonus slide's 3D monocle IIFE demonstrates the full pattern.

---

## CSS Animations

You can use plain CSS `@keyframes` animations too. The SECTIONS config controls content — for layout-level animations, add rules to the `<style>` block or via inline `style` attributes set in step functions.

```javascript
// In a step function:
el.style.animation = 'slideIn 0.5s ease-out forwards';
```

Make sure any `@keyframes` rules you reference exist in the `<style>` block.
