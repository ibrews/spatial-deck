// core/timeline — a winding road with milestones placed on it by arc length (labels alternate above/below). The road
// draws over 9 s and each milestone pops as the line reaches it. Props: nodes = [[year, headline, subline, color], …].
SD.defineSlide({
  id: 'core/timeline',
  frame: 'timeline.html',
  steps: 0,
  duration: 10.5,
  props: {
    label: 'Timeline',
    nodes: [['2016', 'First milestone', 'What happened', '#00d4ff'], ['2018', 'Second milestone', 'What happened', '#f43f5e'],
      ['2020', 'Third milestone', 'What happened', '#a78bfa'], ['2022', 'Fourth milestone', 'What happened', '#f59e0b'],
      ['2026', 'Today', 'Where this talk is', '#f0f4ff']],
  },
  assets: ['timeline.html'],
  provenance: ['ibrews/pmre-2026-xr-chitect media/motion/timeline.html @310afba (PMRE 2026 "The Winding Path")'],
  notes: 'Up to about nine milestones fit; colors should come from the noir palette (#00d4ff #f43f5e #a78bfa #f59e0b #f0f4ff) so every look recolors them.',
});
