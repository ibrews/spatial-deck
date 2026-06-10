"""Export the current SECTIONS array as a single, self-contained, static
HTML outline — one page per case, readable in any browser with zero JS.

NOT the spatial-deck runtime: that's `index.html`. This is for handoff —
a collaborator who wants to skim the deck in email, a reviewer who doesn't
want to run the interactive version, or a print-to-PDF moment.

The outline is honest about what it can't carry: a fidelity report after
export lists, per slide, anything the linearization dropped or degraded
(advanced layouts flattened, media cyclers/iframes reduced to notes,
videos that won't play). Silence it with --no-report; machine-read it
with --json.

Usage:
    python3 tools/export_html.py --out /tmp/deck.html
    python3 tools/export_html.py --chapter 1 --out /tmp/ch1.html
    python3 tools/export_html.py --html other.html --out outline.html
"""
from __future__ import annotations
import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lint_deck import extract_sections  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HTML = REPO_ROOT / "index.html"

CSS = """
:root { color-scheme: light dark; --accent-teal:#0fb3a1; --accent-purple:#7c5cff;
        --accent-amber:#f5a524; --accent-rose:#f43f7d; }
* { box-sizing: border-box; }
body { margin:0; font: 16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
       background:#0b0b10; color:#e8e8f0; }
main { max-width: 920px; margin: 0 auto; padding: 40px 28px 120px; }
header.chapter { border-top: 4px solid var(--accent); padding: 28px 0 8px; margin-top: 48px; }
header.chapter:first-of-type { margin-top: 0; }
header.chapter .year { font: 700 12px/1 ui-monospace,monospace; letter-spacing: .12em;
                       color: var(--accent); text-transform: uppercase; }
header.chapter h1 { font: 700 34px/1.15 -apple-system,sans-serif; margin: 10px 0 8px; white-space: pre-line; }
header.chapter p.tagline { color:#b8b8c8; margin: 6px 0 0; }
header.chapter .meta { font-size: 13px; color:#8888a0; margin-top: 10px; }
article.case { border-top: 1px solid #24242e; padding: 28px 0; }
article.case h2 { font: 700 22px/1.25 -apple-system,sans-serif; margin: 0 0 6px; white-space: pre-line; }
article.case p.subtitle { color:#c8c8d8; margin: 4px 0 12px; }
article.case img { max-width: 100%; height: auto; border-radius: 10px; display:block; margin: 12px 0; }
article.case ul { margin: 12px 0 0; padding-left: 22px; }
article.case ul li { margin: 4px 0; }
article.case .notes { margin-top: 14px; padding: 10px 14px; border-left: 3px solid var(--accent);
                      background: rgba(255,255,255,.03); color:#b8b8c8; font-size: 14px; white-space: pre-line; }
.iframe-note { font-size: 13px; color:#8888a0; font-style: italic; }
.counter { font: 500 12px/1 ui-monospace,monospace; color:#6a6a80; letter-spacing: .1em; }
footer { text-align: center; color:#6a6a80; font-size: 12px; margin-top: 80px; }
"""

ACCENTS = {"teal": "var(--accent-teal)", "purple": "var(--accent-purple)",
           "amber": "var(--accent-amber)", "rose": "var(--accent-rose)"}


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def render_case(c: dict, idx: int) -> list[str]:
    out = ['<article class="case">']
    out.append(f'<div class="counter">Case {idx:02d}</div>')
    out.append(f'<h2>{esc(c.get("title") or "(untitled)")}</h2>')
    subtitle = (c.get("subtitle") or "").strip()
    if subtitle:
        out.append(f'<p class="subtitle">{esc(subtitle)}</p>')
    img = (c.get("img") or "").strip()
    if img.startswith("IFRAME:"):
        out.append(f'<p class="iframe-note">↗ embeds {esc(img[7:])}</p>')
    elif img and not img.startswith("MEDIA_CYCLER"):
        alt = esc(c.get("alt") or subtitle or c.get("title") or "")
        out.append(f'<img src="{esc(img)}" alt="{alt}" loading="lazy">')
    elif img.startswith("MEDIA_CYCLER"):
        out.append('<p class="iframe-note">↗ media cycler (see interactive deck)</p>')
    bullets = c.get("bullets") or []
    if bullets:
        out.append("<ul>")
        for b in bullets:
            if isinstance(b, str) and b.strip():
                out.append(f"<li>{esc(b)}</li>")
        out.append("</ul>")
    notes = (c.get("notes") or "").strip()
    if notes:
        out.append(f'<div class="notes">{esc(notes)}</div>')
    out.append("</article>")
    return out


def render_chapter(ch: dict, ch_idx: int) -> list[str]:
    accent = ACCENTS.get((ch.get("accent") or "").strip(), ACCENTS["teal"])
    lesson = ch.get("lesson") or {}
    year = esc(ch.get("year") or f"#{ch_idx}")
    title = esc(lesson.get("title") or "")
    tagline = esc(lesson.get("tagline") or "")
    short = esc(lesson.get("short") or "")
    tags = esc(lesson.get("tags") or "")
    out = [f'<header class="chapter" style="--accent:{accent}">']
    out.append(f'<div class="year">{year}{" · " + short if short and short != year else ""}</div>')
    if title:
        out.append(f"<h1>{title}</h1>")
    if tagline:
        out.append(f'<p class="tagline">{tagline}</p>')
    if tags:
        out.append(f'<div class="meta">{tags}</div>')
    out.append("</header>")
    for i, c in enumerate(ch.get("cases") or [], 1):
        out.extend(render_case(c, i))
    return out


def render(sections: list[dict], title: str) -> str:
    body: list[str] = []
    for i, ch in enumerate(sections):
        body.extend(render_chapter(ch, i))
    total_cases = sum(len(ch.get("cases") or []) for ch in sections)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<main>
{chr(10).join(body)}
<footer>Exported outline · {len(sections)} chapters · {total_cases} cases</footer>
</main>
</body>
</html>
"""


# ── Fidelity report (derived from SECTIONS — no Chrome needed) ──────────────

VIDEO_EXTS = (".mp4", ".webm", ".mov", ".m4v")


def _extra_media(c: dict) -> tuple[int, int]:
    """(item_count, video_count) across placedImages/placedItems/beltItems."""
    srcs: list[str] = []
    for it in c.get("placedImages") or []:
        if isinstance(it, (list, tuple)) and it:
            srcs.append(str(it[0]))
    for it in (c.get("placedItems") or []) + (c.get("beltItems") or []):
        if isinstance(it, dict):
            srcs.append(str(it.get("src") or it.get("type") or ""))
    vids = sum(1 for s in srcs if s.lower().endswith(VIDEO_EXTS) or s == "mp4")
    return len(srcs), vids


def structural_fidelity(sections: list[dict]) -> tuple[list[dict], list[str]]:
    """Per-case degradations the linearized outline introduces, plus
    deck-level notes."""
    drops = []
    any_relative_img = False
    for si, ch in enumerate(sections):
        for ci, c in enumerate(ch.get("cases") or []):
            notes = []
            layout = (c.get("layout") or "").strip()
            if layout:
                notes.append(f"layout '{layout}' linearized to heading + bullets")
            big_fields = [k for k in ("bigText", "bigCaption") if (c.get(k) or "").strip()]
            if big_fields:
                notes.append(f"fields dropped: {', '.join(big_fields)}")
            n_items, n_vids = _extra_media(c)
            if n_items:
                vid_note = f", {n_vids} of them video(s)" if n_vids else ""
                notes.append(f"{n_items} placed/belt item(s) dropped{vid_note}")
            img = (c.get("img") or "").strip()
            if img.startswith("MEDIA_CYCLER"):
                notes.append("media cycler -> placeholder note (no media embedded)")
            elif img.startswith("IFRAME:"):
                notes.append(f"iframe -> URL note, content not embedded ({img[7:]})")
            elif img.lower().endswith(VIDEO_EXTS):
                notes.append("video referenced via <img> tag — will not play in the outline")
            elif img and not img.startswith(("http://", "https://", "data:", "/")):
                any_relative_img = True
            if notes:
                title = (c.get("title") or "(untitled)").replace("\n", " ").strip()
                drops.append({"slide": f"ch{si}.case{ci}", "title": title, "degraded": notes})
    deck_notes = ["cover/bonus/map/close slides not exported (SECTIONS chapters+cases only)"]
    if any_relative_img:
        deck_notes.append("image paths are repo-relative — keep the outline inside the repo (or copy media/) for images to resolve")
    return drops, deck_notes


def print_fidelity(drops: list[dict], n_slides: int, deck_notes: list[str],
                   as_json=False, stream=None):
    stream = stream or sys.stdout
    if as_json:
        print(json.dumps({"slides": n_slides, "degraded": drops,
                          "deck": deck_notes}, indent=2), file=stream)
        return
    print(f"\n── Fidelity report ── {n_slides} slides exported (HTML outline)", file=stream)
    if not drops:
        print("  nothing degraded per-slide — no advanced layouts/cyclers/iframes/videos in these chapters",
              file=stream)
    for d in drops:
        print(f"  {d['slide']:>10}  {d['title'][:48]}", file=stream)
        for n in d["degraded"]:
            print(f"            · {n}", file=stream)
    for n in deck_notes:
        print(f"  ({n})", file=stream)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", type=Path, default=DEFAULT_HTML)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--chapter", type=int, default=None)
    ap.add_argument("--title", default="Spatial Deck — Outline")
    ap.add_argument("--json", action="store_true", help="fidelity report as JSON")
    ap.add_argument("--no-report", action="store_true", help="skip the fidelity report")
    args = ap.parse_args()

    sections = extract_sections(args.html)
    if args.chapter is not None:
        if not (0 <= args.chapter < len(sections)):
            print(f"ERROR: chapter index out of range (0..{len(sections)-1})", file=sys.stderr)
            return 2
        sections = [sections[args.chapter]]

    out = render(sections, args.title)
    if args.out:
        args.out.write_text(out)
        print(f"[done] Wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(out)
    if not args.no_report:
        # When the document itself goes to stdout, the report moves to stderr
        # so the outline stays well-formed.
        n_slides = len(sections) + sum(len(ch.get("cases") or []) for ch in sections)
        drops, deck_notes = structural_fidelity(sections)
        print_fidelity(drops, n_slides, deck_notes, args.json,
                       stream=sys.stdout if args.out else sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
