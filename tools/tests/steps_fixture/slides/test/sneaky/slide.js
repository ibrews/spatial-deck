// Fixture (BROKEN on purpose): declares no steps but registers three substeps of its own, the way hand-written slide
// code did before modules (the intro-lens countdown that "came back by accident"). declared 0 vs reachable 3.
SD.defineSlide({
  id: 'test/sneaky', steps: 0,
  render(el) {
    el.innerHTML = '<h2>Sneaky</h2><p class="n" style="font-size:3rem">0</p>';
    const n = el.querySelector('.n');
    slideSteps.set(el, { current: 0, steps: [1, 2, 3].map((k) => () => { n.textContent = String(k); }) });
    return {};
  },
});
