// core/lane — one straight lane ("pick a lane, stay in it") splits into three strands that braid back into one wider
// path. A seekable iframe motion graphic (13 s, no clicks); every word is a prop.
SD.defineSlide({
  id: 'core/lane',
  frame: 'lane.html',
  steps: 0,
  duration: 13,
  props: { title: 'Pick a lane.', caption: 'STAY IN IT', strands: ['CRAFT ONE', 'CRAFT TWO', 'CRAFT THREE'], result: 'YOUR LANE', punch: '' },
  assets: ['lane.html'],
  provenance: ['ibrews/pmre-2026-xr-chitect media/motion/lane.html @310afba (PMRE 2026 cold open)'],
  notes: 'Let the first act play silently; the braid lands at about 10 s.',
});
