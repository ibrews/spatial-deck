# PMRE 2026: options index ("Architect to XR-chitect")

Every option below is built into the deck. Press **O** in the deck for the picker, or add URL params, for example `index.html?open=question&thesis=b&cut=30&theme=stage`. The defaults reproduce the audited draft exactly. Picks are saved per browser, and **Reset to defaults** in the O panel clears them.

| Group (`?param=`) | Choice | One-line pitch |
|---|---|---|
| Opening `open` | `cold` *(default)* | The lane motion: one road splits into architecture, theater and technology, then braids into XR-chitect. Ends on "I didn't." |
| | `question` | Show of hands first: "Who here has a job title your parents can't explain?" Warms a post-lunch room. |
| | `story` | Skips the motion and goes straight to the "that job doesn't exist yet" quote. Fastest start. |
| Render questions `renders` | `quote` *(default)* | Three questions as a big typographic quote. |
| | `motion` | `questions-dissolve`: the questions orbit a flat render, a headset arrives, and they dissolve into the essay line. |
| One talk → one client `onetalk` | `photo` *(default)* | Two-pane slide with the Ed Sullivan lighting render. |
| | `motion` / `both` | `one-talk`: podium, ripple, audience member, client, twice (Late Show dome, then Waldorf Astoria). |
| Holodeck staging `spike` | `photo` *(default)* | Holodeck photo with the spike-tape bullets. |
| | `motion` / `both` | `spike-tape`: top-down plan over an empty room, spike marks laid, a guest walking mark to mark (illustrative). |
| Closing ask `ask` | `text` *(default)* | "What's your weird intersection?" as text. |
| | `motion` | `venn-you`: the audience's own Venn. PHOTOGRAPHY / VIDEO plus two blanks that cycle examples, then YOUR LANE. |
| Thesis `thesis` | `a` *(default)* | "The Advice Wasn't Wrong. It Just Assumed One Lane." |
| | `b` | "Specialize in the Overlap." Shortest and most quotable. |
| | `c` | "Pick a Lane. Then Build a Bridge." Kindest to the professors. |
| Close `close` | `talk` *(default)* | "Let's Talk." plus an intersection invite and the kids'-names bit. |
| | `kids` | "Ask Me About My Kids' Names." The bio's hook as the whole close. |
| | `question` | "What's Your Weird Intersection?" Ends on the audience. |
| Cover `cover` | `still` *(default)* / `motion` | Ambient strand background (`cover-ambient.html`, delivered 10:34 ET). Text-free; screen-blended so it works on every theme. |
| Length `cut` | `full` *(default)* | About 47 min, 35 slides. |
| | `30` | About 35 min (25 slides; lessons keep their full timing). |
| | `20` | About 25 min (17 slides). |
| Look `theme` | `noir` *(default)* / `blueprint` / `stage` | Dark XR noir; a navy drafting grid; or a warm spotlight with a red-curtain glow. |

All new copy is ✎ PROPOSED (connective). The quotes inside motion graphics are ✅ VERIFIED against Alex's 2017 essay, the KB speaking modules and the Four Seasons Lake Austin notes. The plans in the motion graphics are illustrative.

**Not done (out of time, 10:45 ET):** an "extended" cut beyond full, a side-by-side comparison page, and alternate cover lines. The official title is already on the PMRE agenda, so only the kicker line would change.

**MP4s for the alternates** (silent, 1080p30): `media/motion/mp4/{questions-dissolve,one-talk,spike-tape,venn-you}.mp4`. Copies are also in `~/Archives/pmre2026-2026-10/organizer-package-draft/videos/alternates/`.

**Exports:**
- Editable PPTX for any combination: `python3 tools/export_talk_pptx.py --pick thesis=b --pick cut=30 --out x.pptx`
- MP4s for the organizer: `node tools/render_motion.mjs <name>` writes to `media/motion/mp4/`
