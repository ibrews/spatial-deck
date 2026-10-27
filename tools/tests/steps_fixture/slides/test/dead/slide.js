// Fixture (BROKEN on purpose): declares 3 steps but the third click changes nothing. The sweep must call step 3 dead.
SD.defineSlide({
  id: 'test/dead', steps: 3,
  render(el) {
    el.innerHTML = '<h2>Dead step</h2><p class="a" style="visibility:hidden;font-size:3rem">A</p><p class="b" style="visibility:hidden;font-size:3rem">B</p>';
    const a = el.querySelector('.a'), b = el.querySelector('.b');
    return {
      enter() { a.style.visibility = b.style.visibility = 'hidden'; },
      step(n) { if (n === 1) a.style.visibility = 'visible'; if (n === 2) b.style.visibility = 'visible'; },
    };
  },
});
