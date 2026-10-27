// Fixture (BROKEN on purpose): an iframe module whose html never loads sd-frame.js, so it never reports ready and the
// deck can never send it enter. The sweep must fail it ("never reported ready").
SD.defineSlide({ id: 'test/silent', frame: 'silent.html', steps: 0, duration: 1, assets: ['silent.html'] });
