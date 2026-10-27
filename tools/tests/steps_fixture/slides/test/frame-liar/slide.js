// Fixture (BROKEN on purpose): the deck asks for 2 steps but the frame only implements (and reports) 1.
SD.defineSlide({ id: 'test/frame-liar', frame: 'liar.html', steps: 2, duration: 1, assets: ['liar.html'] });
