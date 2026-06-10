"""Import a PDF deck into Spatial Deck's SECTIONS array.

Pipeline:
  1. pdfplumber extracts per-page text (sorted top-to-bottom, left-to-right —
     PDFs from InDesign/Keynote often have wonky z-order in the raw stream).
  2. Each page is treated as one slide. The first non-empty line becomes
     the raw title; remaining lines become the body.
  3. llama3.1:8b@Sam normalizes each slide into {title, subtitle, bullets},
     single-pass, with qwen3-coder:30b@MBP as fallback.
  4. Embedded images are extracted via pdfplumber's image API to
     media/import-<pdf>-<hash>/ when possible. PDFs that only contain rastered
     pages (scanned decks) produce no images — that's expected.

Usage:
    python3 tools/import_pdf.py deck.pdf
    python3 tools/import_pdf.py deck.pdf --chapter "PDF DECK" --limit 3
    python3 tools/import_pdf.py deck.pdf --no-llm   # raw extraction only
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
from fleet_client import call_json, ENDPOINTS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_ROOT = REPO_ROOT / "media"
SAFE = re.compile(r"[^a-zA-Z0-9]+")

NORMALIZE_ROUTES = [
    ("llama3.1:8b", "sam"),
    ("qwen3-coder:30b", "mbp"),
]

PROMPT = """Normalize one PDF slide into a fixed JSON schema.

Slide title (first line): {title!r}
Remaining text (one line each):
---
{body}
---

Output a JSON object with EXACTLY these keys:
  title    — <= 60 chars, close to the first-line title.
  subtitle — optional one-line context, <= 80 chars. Empty if none fits.
  bullets  — array of 2-5 tight bullets (<=140 chars each). Rewrite bloated
             sentences into declarative lines. Preserve numbers and proper
             nouns EXACTLY.

Rules: No markdown, no emoji unless in original. Do not invent facts."""


def extract_page_text(page) -> tuple[str, list[str]]:
    """Return (title, body_lines) from a pdfplumber Page.

    Sorts text by (top, x0) so two-column layouts still read sensibly in
    most cases. Bails to stream order if we can't get word boxes."""
    try:
        words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    except Exception:
        txt = page.extract_text() or ""
        lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
        return (lines[0] if lines else ""), lines[1:]

    if not words:
        return "", []

    # Group words into lines by y (top) with a tolerance.
    TOL = 3.0
    lines: list[list[dict]] = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        placed = False
        for line in lines:
            if abs(line[0]["top"] - w["top"]) <= TOL:
                line.append(w)
                placed = True
                break
        if not placed:
            lines.append([w])
    # Sort each line left-to-right.
    line_texts: list[str] = []
    for line in sorted(lines, key=lambda ln: ln[0]["top"]):
        line_sorted = sorted(line, key=lambda w: w["x0"])
        text = " ".join(w["text"] for w in line_sorted).strip()
        if text:
            line_texts.append(text)
    if not line_texts:
        return "", []
    return line_texts[0], line_texts[1:]


def save_images(page, idx: int, out_dir: Path, pdf: pdfplumber.PDF) -> list[str]:
    """Extract raster images embedded on this page to out_dir."""
    saved: list[str] = []
    for pic_n, im in enumerate(page.images or []):
        try:
            # pdfplumber gives us image metadata; render the bbox from the
            # page to PNG as a robust fallback (handles compressed / masked
            # images more reliably than grabbing the stream directly).
            bbox = (im["x0"], im["top"], im["x1"], im["bottom"])
            cropped = page.crop(bbox).to_image(resolution=150)
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            blob = buf.getvalue()
        except Exception:
            continue
        digest = hashlib.sha1(blob).hexdigest()[:8]
        out = out_dir / f"slide{idx:02d}-{pic_n}-{digest}.png"
        if not out.exists():
            out.write_bytes(blob)
        saved.append(str(out.relative_to(REPO_ROOT)))
    return saved


def normalize_with_llm(title: str, body: list[str]) -> dict:
    body_str = "\n".join(body) or "(none)"
    prompt = PROMPT.format(title=title or "(untitled)", body=body_str)
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


BULLET_PREFIX_RE = re.compile(r"^\s*[-•*]\s+")


def fallback_entry(title: str, body: list[str]) -> dict:
    """Best-effort raw entry. Lines starting with -/•/* are bullets; a single
    leading non-bullet line becomes the subtitle."""
    subtitle = ""
    bullet_lines = []
    for ln in body:
        if BULLET_PREFIX_RE.match(ln):
            bullet_lines.append(BULLET_PREFIX_RE.sub("", ln).strip())
        elif not subtitle and not bullet_lines:
            subtitle = ln.strip()
        else:
            bullet_lines.append(ln.strip())
    return {
        "title": title or "Untitled",
        "subtitle": subtitle,
        "bullets": bullet_lines[:5],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--chapter", default="IMPORTED", help="year/chapter label")
    ap.add_argument("--accent", default="teal", choices=["teal", "purple", "amber", "rose"])
    ap.add_argument("--limit", type=int, default=0, help="max pages to process (0=all)")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--no-images", action="store_true", help="skip embedded-image extraction")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"ERROR: {args.pdf} not found", file=sys.stderr)
        return 2

    stem = SAFE.sub("-", args.pdf.stem).strip("-").lower() or "deck"
    digest = hashlib.sha1(args.pdf.read_bytes()).hexdigest()[:8]
    media_dir = MEDIA_ROOT / f"import-{stem}-{digest}"
    media_dir.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(str(args.pdf)) as pdf:
        pages = list(pdf.pages)
        if args.limit:
            pages = pages[:args.limit]
        print(f"[pdf] {len(pages)} pages. Media → {media_dir.relative_to(REPO_ROOT)}", file=sys.stderr)

        cases = []
        for i, page in enumerate(pages, 1):
            title, body = extract_page_text(page)

            img_path = ""
            if not args.no_images:
                imgs = save_images(page, i, media_dir, pdf)
                img_path = imgs[0] if imgs else ""

            if args.no_llm:
                entry = fallback_entry(title, body)
                tag = "raw"
            else:
                try:
                    entry = normalize_with_llm(title, body)
                    tag = "llm"
                except Exception as e:
                    print(f"  [page {i}] normalize failed ({e}); using raw fallback", file=sys.stderr)
                    entry = fallback_entry(title, body)
                    tag = "raw"
            entry["img"] = img_path
            cases.append(entry)
            print(f"  [page {i}/{len(pages)}] {tag}: {entry['title'][:50]}", file=sys.stderr)

    if not cases:
        print("ERROR: no pages extracted", file=sys.stderr)
        return 3

    chapter = {
        "year": args.chapter,
        "accent": args.accent,
        "lesson": {
            "title": f"Imported: {args.pdf.stem}",
            "short": args.chapter,
            "tagline": f"Imported from {args.pdf.name}. Edit this tagline and the cases below to match your narrative.",
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
