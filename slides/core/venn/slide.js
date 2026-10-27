// core/venn — three overlapping crafts with the HarvardXR pixel icons; a pixel avatar hops between them (each icon
// reacts), overlap labels light up as it crosses them, and it ends on the center pill. Seekable, 13.5 s, no clicks.
SD.defineSlide({
  id: 'core/venn',
  frame: 'venn.html',
  steps: 0,
  duration: 13.5,
  props: { labels: ['CRAFT ONE', 'CRAFT TWO', 'CRAFT THREE'], overlaps: ['', '', ''], center: 'YOU', caption: '', beard: false },
  assets: ['venn.html'],
  shared: ['kit/sprite.js'],
  provenance: [
    'harvardxr-keynote@7c6fbf5 index.html buildVennSlide (icons, reactions, pinball idea)',
    'ibrews/pmre-2026-xr-chitect media/motion/venn-sprite.html + sprite.js @310afba (seekable port)',
  ],
  notes: 'labels: the three circles (left, right, bottom). overlaps: left∩right, right∩bottom, left∩bottom. Use "" to leave one out.',
});
