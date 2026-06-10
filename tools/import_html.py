"""Import a standalone HTML deck (e.g. Claude Design export) into Spatial Deck.

Pipeline:
  1. BeautifulSoup parses the HTML and chunks it into slide-sized regions,
     using whichever signal is present:
       - <section>, <article>, <slide>, [data-slide], .slide, [role=slide]
       - failing that, each <h1>/<h2> plus its following siblings until the
         next heading
  2. For each chunk, deterministic extraction pulls out the heading, any text
     blocks, list items, blockquotes, and <img> src/alt.
  3. qwen2.5-coder:14b@Archie normalizes each slide into
     {title, subtitle, bullets[]} — single-pass, with a fallback to
     qwen3-coder:30b@MBP if Archie is flaky.
  4. Images referenced with relative or data: URLs are copied/decoded into
     media/import-<hash>/ and rewritten as repo-relative paths.
  5. Output JSON is SECTIONS-compatible, ready for tools/merge_sections.py.

Usage:
    python3 tools/import_html.py claude-design-export.html
    python3 tools/import_html.py deck.html --chapter "DESIGN" --limit 5
    python3 tools/import_html.py deck.html --no-llm   # raw extraction only

Writes nothing to index.html directly — run merge_sections.py after review.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import mimetypes
import re
import sys
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup, Tag

sys.path.insert(0, str(Path(__file__).parent))
from fleet_client import call_json, ENDPOINTS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_ROOT = REPO_ROOT / "media"
SAFE = re.compile(r"[^a-zA-Z0-9]+")

SLIDE_SELECTORS = [
    "section", "article", "slide",
    "[data-slide]", ".slide", "[role=slide]",
]

# (model, host) pairs for slide normalization. Archie's coder is strong on
# messy DOM; MBP's qwen3-coder:30b is the offline fallback.
NORMALIZE_ROUTES = [
    ("qwen2.5-coder:14b", "archie"),
    ("qwen3-coder:30b",   "mbp"),
]

PROMPT = """You are normalizing one slide extracted from an HTML deck into a fixed JSON schema.

Raw heading: {title!r}
Extracted text blocks (one per line):
---
{body}
---
List items already found on this slide (may overlap with text):
---
{items}
---

Output a JSON object with EXACTLY these keys:
  title    — short punchy headline, <= 60 chars. Keep close to the raw heading.
  subtitle — optional one-line context, <= 80 chars. Empty string if nothing fits.
  bullets  — array of 2-5 short punchy bullet strings, each <= 140 chars.
             If list items were given, prefer those (tightened). Otherwise
             derive from the text blocks. Preserve numbers and proper nouns.

Rules:
- No markdown, no emoji unless present in original.
- Do not invent facts.
- If the slide is clearly a section divider with only a title, return bullets:[].
"""

IMG_EXT = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg",
    "image/gif": ".gif", "image/svg+xml": ".svg", "image/webp": ".webp",
}


def find_slides(soup: BeautifulSoup) -> list[Tag]:
    """Return the list of slide-level Tags. Tries structural selectors first,
    falls back to heading-based chunking."""
    for sel in SLIDE_SELECTORS:
        hits = soup.select(sel)
        # Filter out empties / navigations / scripts.
        hits = [h for h in hits if h.get_text(strip=True)]
        if len(hits) >= 2:
            return hits
    # Heading-based fallback.
    body = soup.body or soup
    headings = body.find_all(["h1", "h2"])
    if not headings:
        return []
    slides = []
    for i, h in enumerate(headings):
        wrapper = soup.new_tag("section")
        wrapper.append(h.__copy__())
        for sib in h.next_siblings:
            if isinstance(sib, Tag) and sib.name in ("h1", "h2"):
                break
            if isinstance(sib, Tag):
                wrapper.append(sib.__copy__())
        slides.append(wrapper)
    return slides


def extract_slide(tag: Tag) -> dict:
    """Deterministic pull of heading, body text, list items, images."""
    title = ""
    for h in tag.find_all(["h1", "h2", "h3"], limit=1):
        title = h.get_text(" ", strip=True)
        break

    items: list[str] = []
    for li in tag.find_all("li"):
        t = li.get_text(" ", strip=True)
        if t:
            items.append(t)

    body_blocks: list[str] = []
    for el in tag.find_all(["p", "blockquote", "figcaption", "div"]):
        # Skip divs that wrap our list/heading/image content.
        if el.find(["ul", "ol", "li", "h1", "h2", "h3"]):
            continue
        t = el.get_text(" ", strip=True)
        if t and t not in body_blocks and t != title:
            body_blocks.append(t)

    images: list[tuple[str, str]] = []  # (src, alt)
    for img in tag.find_all("img"):
        src = img.get("src") or ""
        alt = img.get("alt") or ""
        if src:
            images.append((src.strip(), alt.strip()))

    return {"title": title, "body": body_blocks, "items": items, "images": images}


def copy_image(src: str, source_html_path: Path, out_dir: Path, idx: int, pic_n: int) -> str:
    """Resolve src (data URI / relative / abs) into a copied media path.
    Returns the repo-relative path or '' if we can't materialize it."""
    if src.startswith("data:"):
        m = re.match(r"data:([^;]+);base64,(.+)", src)
        if not m:
            return ""
        mime, b64 = m.group(1), m.group(2)
        ext = IMG_EXT.get(mime, mimetypes.guess_extension(mime) or ".bin")
        try:
            blob = base64.b64decode(b64)
        except Exception:
            return ""
        digest = hashlib.sha1(blob).hexdigest()[:8]
        out = out_dir / f"slide{idx:02d}-{pic_n}-{digest}{ext}"
        if not out.exists():
            out.write_bytes(blob)
        return str(out.relative_to(REPO_ROOT))

    if src.startswith(("http://", "https://")):
        # Remote URL — let the HTML reference it directly; Spatial Deck can load it.
        return src

    # Relative path — resolve against the source HTML's directory.
    src_unquoted = urllib.parse.unquote(src)
    candidate = (source_html_path.parent / src_unquoted).resolve()
    if not candidate.exists() or not candidate.is_file():
        return ""
    try:
        blob = candidate.read_bytes()
    except Exception:
        return ""
    digest = hashlib.sha1(blob).hexdigest()[:8]
    ext = candidate.suffix or ".bin"
    out = out_dir / f"slide{idx:02d}-{pic_n}-{digest}{ext}"
    if not out.exists():
        out.write_bytes(blob)
    return str(out.relative_to(REPO_ROOT))


def normalize_with_llm(title: str, body: list[str], items: list[str]) -> dict:
    body_str = "\n".join(body) or "(none)"
    items_str = "\n".join(f"- {x}" for x in items) if items else "(none)"
    prompt = PROMPT.format(title=title or "(untitled)", body=body_str, items=items_str)
    last_err: Exception | None = None
    for model, host in NORMALIZE_ROUTES:
        try:
            data = call_json(
                model, prompt,
                endpoint=ENDPOINTS[host],
                required_keys=["title", "subtitle", "bullets"],
            )
            t = data.get("title")
            if not isinstance(t, str) or not t.strip():
                raise ValueError(f"bad title: {t!r}")
            s = data.get("subtitle", "")
            if not isinstance(s, str):
                s = ""
            b = data.get("bullets", [])
            if not isinstance(b, list) or not all(isinstance(x, str) for x in b):
                raise ValueError(f"bad bullets: {b!r}")
            return {
                "title": t.strip(),
                "subtitle": s.strip(),
                "bullets": [x.strip() for x in b if x.strip()],
            }
        except Exception as e:
            last_err = e
            print(f"    [normalize] {model}@{host} failed: {e}", file=sys.stderr)
    raise RuntimeError(f"all normalize routes failed; last error: {last_err}")


def fallback_entry(title: str, body: list[str], items: list[str]) -> dict:
    bullets = items[:5] if items else body[:4]
    return {
        "title": title or "Untitled",
        "subtitle": "",
        "bullets": bullets,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--chapter", default="IMPORTED", help="year/chapter label")
    ap.add_argument("--accent", default="teal", choices=["teal", "purple", "amber", "rose"])
    ap.add_argument("--limit", type=int, default=0, help="max slides to process (0=all)")
    ap.add_argument("--no-llm", action="store_true", help="use raw extraction only")
    args = ap.parse_args()

    if not args.html.exists():
        print(f"ERROR: {args.html} not found", file=sys.stderr)
        return 2

    raw = args.html.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")

    for bad in soup(["script", "style", "nav", "header", "footer", "aside"]):
        bad.decompose()

    slides = find_slides(soup)
    if args.limit:
        slides = slides[:args.limit]
    if not slides:
        print("ERROR: could not identify any slides in this HTML.", file=sys.stderr)
        return 3

    stem = SAFE.sub("-", args.html.stem).strip("-").lower() or "deck"
    digest = hashlib.sha1(args.html.read_bytes()).hexdigest()[:8]
    media_dir = MEDIA_ROOT / f"import-{stem}-{digest}"
    media_dir.mkdir(parents=True, exist_ok=True)
    print(f"[html] {len(slides)} slide chunks. Media → {media_dir.relative_to(REPO_ROOT)}", file=sys.stderr)

    cases = []
    for i, s in enumerate(slides, 1):
        raw_slide = extract_slide(s)

        # Copy/decode images.
        img_path = ""
        for pic_n, (src, alt) in enumerate(raw_slide["images"]):
            resolved = copy_image(src, args.html.resolve(), media_dir, i, pic_n)
            if resolved:
                img_path = resolved
                break
        # Prefer alt text of chosen image as a subtitle candidate.
        alt_fallback = ""
        if raw_slide["images"]:
            alt_fallback = raw_slide["images"][0][1]

        if args.no_llm:
            entry = fallback_entry(raw_slide["title"], raw_slide["body"], raw_slide["items"])
            tag = "raw"
        else:
            try:
                entry = normalize_with_llm(raw_slide["title"], raw_slide["body"], raw_slide["items"])
                tag = "llm"
            except Exception as e:
                print(f"  [slide {i}] normalize failed ({e}); using raw fallback", file=sys.stderr)
                entry = fallback_entry(raw_slide["title"], raw_slide["body"], raw_slide["items"])
                tag = "raw"

        if not entry.get("subtitle") and alt_fallback:
            entry["subtitle"] = alt_fallback
        entry["img"] = img_path
        cases.append(entry)
        print(f"  [slide {i}/{len(slides)}] {tag}: {entry['title'][:50]}", file=sys.stderr)

    chapter = {
        "year": args.chapter,
        "accent": args.accent,
        "lesson": {
            "title": f"Imported: {args.html.stem}",
            "short": args.chapter,
            "tagline": f"Imported from {args.html.name}. Edit this tagline and the cases below to match your narrative.",
            "tags": "",
        },
        "cases": cases,
    }

    out_path = args.out or (REPO_ROOT / "tools" / f"imported-{stem}-{digest}.json")
    out_path.write_text(json.dumps(chapter, indent=2, ensure_ascii=False))
    try:
        rel = str(out_path.relative_to(REPO_ROOT))
    except ValueError:
        rel = str(out_path)
    print(f"[done] Wrote {rel} ({len(cases)} cases)", file=sys.stderr)
    print(f"[next] python3 tools/merge_sections.py {rel}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
