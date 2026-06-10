"""Export the SECTIONS array as a Markdown file — the inverse of import_md.py.

Round-trips the convention used by the markdown importer:
  # Chapter title           (one per chapter)
  tagline paragraph
  ## Case title             (one per case)
  subtitle paragraph
  ![alt](media/foo.png)
  - bullet 1
  - bullet 2
  > speaker note

Useful for:
  - Editing a deck in your favorite Markdown editor, then re-importing.
  - Handing a static outline to a human reviewer or an AI collaborator.
  - Diffing deck content in a format `git diff` renders nicely.

Markdown can't carry everything the live deck does: a fidelity report
after export lists, per slide, what the round-trip loses (advanced
layouts flattened, media cyclers and iframes skipped entirely, videos
reduced to image references). Silence it with --no-report; machine-read
it with --json. When the document goes to stdout, the report goes to
stderr so the markdown stays clean.

Usage:
    python3 tools/export_md.py > my-deck.md
    python3 tools/export_md.py --html other.html --out outline.md
    python3 tools/export_md.py --chapter 1   # export one chapter only
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lint_deck import extract_sections  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HTML = REPO_ROOT / "index.html"


def emit_case(c: dict) -> list[str]:
    lines: list[str] = []
    title = (c.get("title") or "").replace("\n", " ").strip() or "(untitled)"
    lines.append(f"## {title}")
    lines.append("")
    subtitle = (c.get("subtitle") or "").strip()
    if subtitle:
        lines.append(subtitle)
        lines.append("")
    img = (c.get("img") or "").strip()
    # Skip pseudo-values that aren't real paths.
    if img and not img.startswith(("MEDIA_CYCLER", "IFRAME:")):
        alt = (c.get("alt") or subtitle or title or "image").strip()
        lines.append(f"![{alt}]({img})")
        lines.append("")
    bullets = c.get("bullets") or []
    for b in bullets:
        if isinstance(b, str) and b.strip():
            lines.append(f"- {b.strip()}")
    if bullets:
        lines.append("")
    notes = (c.get("notes") or "").strip()
    if notes:
        for ln in notes.splitlines():
            lines.append(f"> {ln}")
        lines.append("")
    return lines


def emit_chapter(ch: dict) -> list[str]:
    lines: list[str] = []
    lesson = ch.get("lesson") or {}
    ch_title = (lesson.get("title") or ch.get("year") or "Chapter").replace("\n", " / ").strip()
    lines.append(f"# {ch_title}")
    lines.append("")
    tagline = (lesson.get("tagline") or "").strip()
    if tagline:
        lines.append(tagline)
        lines.append("")
    # Surface lesson-level config as a YAML-ish HTML comment so re-imports round-trip.
    meta_pairs: list[tuple[str, str]] = []
    year = (ch.get("year") or "").strip()
    accent = (ch.get("accent") or "").strip()
    raw_title = (lesson.get("title") or "").strip()
    short = (lesson.get("short") or "").strip()
    tags = (lesson.get("tags") or "").strip()
    if year:     meta_pairs.append(("year", year))
    if accent:   meta_pairs.append(("accent", accent))
    if raw_title and "\n" in raw_title:
        meta_pairs.append(("title", raw_title.replace("\n", "\\n")))
    if short:    meta_pairs.append(("short", short))
    if tags:     meta_pairs.append(("tags", tags))
    if meta_pairs:
        lines.append("<!-- spatial-deck")
        for k, v in meta_pairs:
            lines.append(f"{k}: {v}")
        lines.append("-->")
        lines.append("")
    for c in ch.get("cases") or []:
        lines.extend(emit_case(c))
    return lines


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
    """Per-case degradations the markdown round-trip loses, plus deck-level
    notes. MEDIA_CYCLER and IFRAME: values are dropped from the .md entirely —
    a re-import will not restore them."""
    drops = []
    for si, ch in enumerate(sections):
        for ci, c in enumerate(ch.get("cases") or []):
            notes = []
            layout = (c.get("layout") or "").strip()
            if layout:
                notes.append(f"layout '{layout}' linearized to heading + bullets (field lost on re-import)")
            big_fields = [k for k in ("bigText", "bigCaption") if (c.get(k) or "").strip()]
            if big_fields:
                notes.append(f"fields dropped: {', '.join(big_fields)}")
            n_items, n_vids = _extra_media(c)
            if n_items:
                vid_note = f", {n_vids} of them video(s)" if n_vids else ""
                notes.append(f"{n_items} placed/belt item(s) dropped{vid_note}")
            img = (c.get("img") or "").strip()
            if img.startswith("MEDIA_CYCLER"):
                notes.append("media cycler -> skipped (not representable in markdown)")
            elif img.startswith("IFRAME:"):
                notes.append(f"iframe -> skipped, URL not exported ({img[7:]})")
            elif img.lower().endswith(VIDEO_EXTS):
                notes.append("video emitted as image reference — won't play")
            if notes:
                title = (c.get("title") or "(untitled)").replace("\n", " ").strip()
                drops.append({"slide": f"ch{si}.case{ci}", "title": title, "degraded": notes})
    deck_notes = ["cover/bonus/map/close slides not exported (SECTIONS chapters+cases only)"]
    return drops, deck_notes


def print_fidelity(drops: list[dict], n_slides: int, deck_notes: list[str],
                   as_json=False, stream=None):
    stream = stream or sys.stdout
    if as_json:
        print(json.dumps({"slides": n_slides, "degraded": drops,
                          "deck": deck_notes}, indent=2), file=stream)
        return
    print(f"\n── Fidelity report ── {n_slides} slides exported (markdown outline)", file=stream)
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
    ap.add_argument("--out", type=Path, default=None, help="write to file (default: stdout)")
    ap.add_argument("--chapter", type=int, default=None, help="index of single chapter to export")
    ap.add_argument("--json", action="store_true", help="fidelity report as JSON")
    ap.add_argument("--no-report", action="store_true", help="skip the fidelity report")
    args = ap.parse_args()

    sections = extract_sections(args.html)
    if args.chapter is not None:
        if args.chapter < 0 or args.chapter >= len(sections):
            print(f"ERROR: chapter index {args.chapter} out of range (0..{len(sections)-1})", file=sys.stderr)
            return 2
        chapters = [sections[args.chapter]]
    else:
        chapters = sections

    out_lines: list[str] = []
    for i, ch in enumerate(chapters):
        if i > 0:
            out_lines.append("---")
            out_lines.append("")
        out_lines.extend(emit_chapter(ch))

    text = "\n".join(out_lines).rstrip() + "\n"
    if args.out:
        args.out.write_text(text)
        print(f"[done] Wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    if not args.no_report:
        # When the document itself goes to stdout, the report moves to stderr
        # so the markdown stays clean.
        n_slides = len(chapters) + sum(len(ch.get("cases") or []) for ch in chapters)
        drops, deck_notes = structural_fidelity(chapters)
        print_fidelity(drops, n_slides, deck_notes, args.json,
                       stream=sys.stdout if args.out else sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
