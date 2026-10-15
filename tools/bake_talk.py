#!/usr/bin/env python3
"""Bake talk/sections.js (TALK + SECTIONS + BONUS) into index.html and apply the PMRE talk-branch runtime patches.

Idempotent: the content block lives between // ── TALK START ── / // ── TALK END ── sentinels; every runtime patch
checks for its own marker before applying, and fails loudly if its anchor text is missing (template drift).
    python3 tools/bake_talk.py
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML, SRC = ROOT / "index.html", ROOT / "talk" / "sections.js"
s = HTML.read_text(encoding="utf-8")
talk = SRC.read_text(encoding="utf-8").strip()

def patch(marker, anchor, new, count=1):
    """Replace anchor with new unless marker already present."""
    global s
    if marker in s:
        return
    if anchor not in s:
        sys.exit(f"bake_talk: anchor not found for {marker!r} — template changed? anchor starts: {anchor[:80]!r}")
    s = s.replace(anchor, new, count)

# 1. Content block: first bake replaces the template's SECTIONS..BONUS; later bakes replace between sentinels.
START, END = "// ── TALK START ──", "// ── TALK END ──"
block = f"{START}\n{talk}\n{END}"
if START in s:
    s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: block, s, count=1, flags=re.S)
else:
    m = re.search(r"const SECTIONS = \[.*?\nconst BONUS = \{.*?\};\n", s, flags=re.S)
    if not m:
        sys.exit("bake_talk: template SECTIONS/BONUS block not found")
    s = s[:m.start()] + block + "\n" + s[m.end():]

# 2. Head: title, description, social, favicon.
s = re.sub(r"<title>.*?</title>", "<title>Architect to XR-chitect — Alex Coulombe — PMRE 2026</title>", s, count=1)
s = re.sub(r'<meta name="description" content=".*?">', '<meta name="description" content="Architect to XR-chitect: The Best Career Advice I Ever Ignored. Alex Coulombe, PMRE 2026, Las Vegas.">', s, count=1)
s = re.sub(r'<meta property="og:title" content=".*?">', '<meta property="og:title" content="Architect to XR-chitect: The Best Career Advice I Ever Ignored">', s, count=1)
s = re.sub(r'<meta property="og:description" content=".*?">', '<meta property="og:description" content="Alex Coulombe at PMRE 2026: from architecture school to walkable VR real estate.">', s, count=1)
s = s.replace('<link rel="icon" type="image/svg+xml" href="favicon.svg">', '<link rel="icon" type="image/svg+xml" href="talk/favicon.svg">', 1)

# 3. Cover + close + map center text driven by TALK.
patch("TALK.coverTitle", "cov.innerHTML=`<div class=\"event-tag\">Spatial Deck &middot; Open-Source Presentation Framework</div><h1 class=\"talk-title\">Is XR Right<br>For Your Project?</h1><p class=\"talk-subtitle\">A framework for spatial decisions &mdash; before you pick a headset or a studio</p><div class=\"speaker-card\"><div><div class=\"speaker-name\">A Spatial Deck Presentation</div><div class=\"speaker-co\">github.com/spatial-deck</div></div></div>`;",
      "cov.innerHTML=`<div class=\"event-tag\">${TALK.coverEvent}</div><h1 class=\"talk-title\">${TALK.coverTitle}</h1><p class=\"talk-subtitle\">${TALK.coverSub}</p><div class=\"speaker-card\"><div><div class=\"speaker-name\">${TALK.speaker}</div><div class=\"speaker-co\">${TALK.speakerCo}</div></div></div>`;")
close_re = re.compile(r"cls\.innerHTML=`<div class=\"close-ey\">Thank You</div>.*?<div class=\"close-qr-row\">.*?</div></div></div>\n", re.S)
if "TALK.closeTitle" not in s:
    m = close_re.search(s)
    if not m:
        sys.exit("bake_talk: close slide anchor not found")
    s = s[:m.start()] + ("cls.innerHTML=`<div class=\"close-ey\">${TALK.closeEyebrow}</div><h2 class=\"close-title\">${TALK.closeTitle}</h2><p class=\"close-sub\">${TALK.closeSub}</p>\n"
        "<div class=\"contact-row\"><div class=\"contact-pill\"><span class=\"lbl\">Web</span>${TALK.web}</div></div>\n"
        "<div class=\"close-qr-row\"><div class=\"qr-card\"><img src=\"talk/qr.png\" alt=\"QR code: ${TALK.qr}\" onerror=\"this.parentNode.style.display='none'\"><div class=\"qr-label\">${TALK.qrLabel}</div><div class=\"qr-badge b-teal\">${TALK.web}</div></div></div>\n") + s[m.end():]
patch("TALK.mapCenter[0]", "ct.textContent='IS XR RIGHT'", "ct.textContent=TALK.mapCenter[0]")
patch("TALK.mapCenter[1]", "ct2.textContent='FOR YOUR PROJECT?'", "ct2.textContent=TALK.mapCenter[1]")

# 4. Presenter notes for cover/close/map/bonus come from TALK/BONUS.
patch("BONUS.notes||", "if(ty==='bonus')return'Bonus lesson:", "if(ty==='bonus'&&BONUS.notes)return BONUS.notes;\n  if(ty==='bonus')return'Bonus lesson:")
patch("TALK.coverNotes", "if(ty==='cover')return'Welcome", "if(ty==='cover'&&TALK.coverNotes)return TALK.coverNotes;\n  if(ty==='cover')return'Welcome")
patch("TALK.closeNotes", "if(ty==='close')return'Wrap up.", "if(ty==='close'&&TALK.closeNotes)return TALK.closeNotes;\n  if(ty==='close')return'Wrap up.")
patch("TALK.mapNotes", "if(ty==='map')return'The constellation", "if(ty==='map'&&TALK.mapNotes)return TALK.mapNotes;\n  if(ty==='map')return'The constellation")

# 5. No CDN 3D monocle on the bonus slide (offline-safe; not part of this talk).
patch("TALK_NO_MONOCLE", "// 3D Monocle on Bonus slide\n(function(){\n", "// 3D Monocle on Bonus slide\n(function(){if(window.TALK_NO_MONOCLE!==false)return; // TALK_NO_MONOCLE: disabled for PMRE talk\n")

# 6. Print/shot export: motion iframes become their rendered poster frame instead of a placeholder panel.
patch("sd-motion-poster", "querySelectorAll('#deck iframe').forEach(f=>{const src=f.src||'';",
      "querySelectorAll('#deck iframe').forEach(f=>{const src=f.src||'';const _mm=src.match(/media\\/motion\\/([\\w-]+)\\.html/);if(_mm){const im=document.createElement('img');im.className='full-media sd-motion-poster';im.src='media/motion/mp4/'+_mm[1]+'-poster.png';f.replaceWith(im);return;}")

# 7. Motion replay + reduced motion + talk CSS, appended before </body>.
EXTRA = """<!-- ── PMRE TALK RUNTIME ── -->
<style>
.talk-title .xr{background:linear-gradient(90deg,var(--teal),var(--purple),var(--rose));-webkit-background-clip:text;background-clip:text;color:transparent}
.layout-big .big-text.big-l2{font-size:calc(5.2*var(--vw))}
.layout-big .big-text.big-l3{font-size:calc(4.1*var(--vw))}
.layout-big .big-text.big-l4{font-size:calc(3.4*var(--vw));line-height:1.22}
@media (prefers-reduced-motion: reduce){.slide,.slide *{animation-duration:.001s!important;animation-delay:0s!important;transition:none!important}.bg *{animation:none!important}}
body.reduced-motion .slide,body.reduced-motion .slide *{animation-duration:.001s!important;animation-delay:0s!important;transition:none!important}
body.reduced-motion .bg *{animation:none!important}
</style>
<script>
// Long statements step down a size tier by their longest line so quotes never overflow the 16:9 stage.
document.querySelectorAll('#deck .big-text').forEach(b=>{const n=Math.max(...b.innerHTML.split(/<br\\s*\\/?>/i).map(l=>l.replace(/<[^>]+>/g,'').length));b.classList.add(n>34?'big-l4':n>27?'big-l3':n>20?'big-l2':'big-l1');});
// Motion graphics (media/motion/*.html) restart every time their slide becomes active; ?reduced forces final frames.
(function(){const reduced=new URLSearchParams(location.search).has('reduced');if(reduced)document.body.classList.add('reduced-motion');
const frames=[...document.querySelectorAll('#deck iframe.anim-frame')].filter(f=>/media\\/motion\\//.test(f.getAttribute('src')||''));
frames.forEach(f=>{const base=f.getAttribute('src').split('?')[0];f.dataset.motionBase=base;f.setAttribute('src',base+'?static');});
function arm(sl){if(!sl)return;sl.querySelectorAll('iframe[data-motion-base]').forEach(f=>{f.setAttribute('src',f.dataset.motionBase+(reduced?'?static':'?play='+Date.now()));});}
function rest(sl){if(!sl)return;sl.querySelectorAll('iframe[data-motion-base]').forEach(f=>{f.setAttribute('src',f.dataset.motionBase+'?static');});}
let last=null;new MutationObserver(()=>{const a=document.querySelector('#deck .slide.active');if(a!==last){rest(last);arm(a);last=a;}}).observe(document.getElementById('deck'),{subtree:true,attributes:true,attributeFilter:['class']});
const a0=document.querySelector('#deck .slide.active');if(a0){arm(a0);last=a0;}})();
</script>
"""
s = re.sub(r"<!-- ── PMRE TALK RUNTIME ── -->.*?(?=</body>)", "", s, flags=re.S)
if True:
    i = s.rfind("</body>")
    s = s[:i] + EXTRA + s[i:]

HTML.write_text(s, encoding="utf-8")
print("bake_talk: index.html updated")
