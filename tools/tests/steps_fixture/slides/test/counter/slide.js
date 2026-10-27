// Fixture: an inline module with two clicks. Each click adds a visible line.
SD.defineSlide({
  id: 'test/counter', steps: 2, props: { title: 'Counter', lines: ['one', 'two'] },
  render(el, props, ctx) {
    el.innerHTML = `<h2>${props.title}</h2><ul>${props.lines.map((l) => `<li style="visibility:hidden;font-size:3rem">${l}</li>`).join('')}</ul>`;
    const li = [...el.querySelectorAll('li')];
    return {
      enter() { li.forEach((x) => { x.style.visibility = 'hidden'; }); },
      step(n) { li[n - 1].style.visibility = 'visible'; },
    };
  },
});
