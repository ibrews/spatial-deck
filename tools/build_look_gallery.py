#!/usr/bin/env python3
"""Write styles/index.html: a browsable gallery of every look in the style library.

One card per look, built from its look.json (name, summary, lineage, tokens) and its examples/ captures, with a link
that opens this deck in that look (../index.html?look=<id>). Re-run after adding or changing a look; apply_look.py
does not need it. Stdlib only.
    python3 tools/build_look_gallery.py [--styles styles]
"""
import argparse, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ("cover", "chapter", "case-two-pane", "close")

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Spatial Deck looks</title>
<style>
:root{--bg:#f4f2ec;--fg:#18181a;--dim:#5c5b57;--line:#d8d4c9}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eceae4;--dim:#a19e96;--line:#2e2d2a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1240px;margin:0 auto;padding:48px 16px 80px}
h1{font-size:2rem;margin:0 0 .3em}main>p{color:var(--dim);max-width:46em;margin:0 0 2.2em}
code{font-family:ui-monospace,Menlo,monospace;font-size:.9em}
.look{border-top:1px solid var(--line);padding:28px 0;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2.2fr);gap:28px}
@media (max-width:820px){.look{grid-template-columns:1fr}}
.look h2{margin:0 0 .2em;font-size:1.35rem}.id{color:var(--dim);font-size:.9rem}
.look p{margin:.6em 0;color:var(--dim)}.look .sum{color:var(--fg)}
.sw{display:flex;gap:4px;margin:.8em 0}.sw i{width:26px;height:26px;border:1px solid var(--line)}
.shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.shots img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;border:1px solid var(--line)}
a{color:inherit}.open{display:inline-block;margin-top:.6em;font-weight:600}
</style></head><body><main>
<h1>Spatial Deck looks</h1>
<p>Each look is a complete art direction from a real printed or built tradition: tokens, type, a frame, one motion
grammar and a motion-graphic palette. Pick one with <code>?look=&lt;id&gt;</code>, with
<code>tools/apply_look.py --default &lt;id&gt;</code>, or when starting a talk with <code>tools/new_talk.sh --look &lt;id&gt;</code>.
Rules are in <a href="README.md">styles/README.md</a>.</p>
@@CARDS@@
</main></body></html>
"""


def card(d, lid, j):
    ex = d / "examples"
    shots = "".join(f'<a href="looks/{lid}/examples/{s}.jpg"><img loading="lazy" src="looks/{lid}/examples/{s}.jpg" alt="{html.escape(j["name"])}: {s}"></a>'
                    for s in SHOTS if (ex / f"{s}.jpg").exists())
    tok = j.get("tokens", {})
    sw = "".join(f'<i style="background:{tok[k]}" title="{k} {tok[k]}"></i>' for k in ("paper", "ink", "acc-1", "acc-2", "acc-3") if k in tok)
    md = f'<a href="looks/{lid}/look.md">rules</a>' if (d / "look.md").exists() else ""
    return (f'<section class="look" id="{lid}"><div><h2>{html.escape(j["name"])}</h2><div class="id"><code>{lid}</code> · {md}</div>'
            f'<p class="sum">{html.escape(j.get("summary", ""))}</p><p>{html.escape(j.get("lineage", ""))}</p><div class="sw">{sw}</div>'
            f'<a class="open" href="../index.html?look={lid}">Open the sample deck in this look →</a></div><div class="shots">{shots}</div></section>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--styles", default=str(ROOT / "styles"))
    styles = Path(ap.parse_args().styles)
    cards = []
    for d in sorted((styles / "looks").iterdir()):
        if (d / "look.json").exists():
            cards.append(card(d, d.name, json.loads((d / "look.json").read_text(encoding="utf-8"))))
    noir = styles / "looks" / "noir"
    if noir.exists():  # the original has no look.json; list it last so a fresh reader meets the real looks first
        cards.append(card(noir, "noir", {"name": "Noir (original)", "summary": "The template's original look, kept so existing talks don't change. It trips 7 of the 8 generic tells in tools/lint_look.mjs.", "lineage": "", "tokens": {}}))
    out = styles / "index.html"
    out.write_text(PAGE.replace("@@CARDS@@", "\n".join(cards)), encoding="utf-8")
    print(f"build_look_gallery: {out} ({len(cards)} looks)")


if __name__ == "__main__":
    main()
