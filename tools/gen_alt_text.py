"""Generate alt-text for every image referenced in SECTIONS.

Walks the SECTIONS array, finds case.img paths that point to local files,
and asks gemma3:12b@Lenny (vision-capable) to draft a short description.
Outputs a JSON patch you can merge by hand (or pipe through the merger).
Never mutates index.html.

Also: --scan-media walks media/ and lists images that aren't referenced
anywhere in SECTIONS. Useful for spotting orphans.

Why this tool is a cautious one:
  - Fleet vision models are mediocre. Expect Sol ~5/10 accuracy. Set
    expectations accordingly — this is first-pass copy, not final.
  - ~30-60 seconds per image on 12b; multiply by deck size before running.

Usage:
    python3 tools/gen_alt_text.py                  # draft alt for all imgs
    python3 tools/gen_alt_text.py --limit 3        # smoke-test on 3 images
    python3 tools/gen_alt_text.py --model gemma3:27b  # bigger model, slower
    python3 tools/gen_alt_text.py --scan-media     # orphan report only
    python3 tools/gen_alt_text.py --force          # regenerate even if alt exists
"""
from __future__ import annotations
import argparse
import base64
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fleet_client import ENDPOINTS, call_vision as _provider_vision  # noqa: E402
from lint_deck import extract_sections  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HTML = REPO_ROOT / "index.html"

VISION_ROUTES = [
    ("gemma3:12b", "lenny"),   # faster
    ("gemma3:27b", "lenny"),   # only if caller overrides
]

PROMPT = """Write ONE short alt-text sentence for this image, suitable for a slide deck.

Requirements:
- 10-20 words.
- Describe what is visible: people, objects, setting, mood.
- No leading phrases like "This image shows" or "Here is".
- No markdown, no emoji, no quotes.
- Plain prose only.
- Do not speculate about context you cannot see."""


def call_vision(model: str, host: str, image_b64: str, timeout: int = 120) -> str:
    """Send image + prompt through the provider chain (Anthropic/OpenAI/Ollama).
    model/host are hints for the Ollama/fleet tier."""
    text = _provider_vision(PROMPT, image_b64, model=model,
                            endpoint=ENDPOINTS.get(host), timeout=timeout,
                            temperature=0.2).strip()
    text = text.replace("**", "").strip()

    # Drop any leading preamble line that ends with ":" (e.g. "Here's a short
    # alt-text sentence:" or "Alt text:") — real description never does that.
    while "\n" in text:
        first, rest = text.split("\n", 1)
        first = first.strip()
        if first.endswith(":") and rest.strip():
            text = rest.strip()
            continue
        break

    # If the model volunteered a one-line preamble ending with ":" followed
    # by the actual text on the same line (rare), split at the colon.
    if text.count(":") == 1 and text.lower().startswith(("here", "this", "alt", "description", "the image")):
        before, after = text.split(":", 1)
        if after.strip():
            text = after.strip()

    # Strip specific phrasings that sneak through.
    for lead in ("This image shows ", "The image shows ", "This is ",
                 "The picture shows ", "In this image, "):
        if text.lower().startswith(lead.lower()):
            text = text[len(lead):]
            text = text[:1].upper() + text[1:] if text else text

    text = text.split("\n\n", 1)[0].split("\n", 1)[0].strip(' "\'')
    if "." in text:
        text = text.split(".")[0].strip() + "."
    return text


def collect_img_entries(sections: list[dict]) -> list[dict]:
    """Return [{chapter, case, title, img, existing_alt}] for every case
    with a local image path."""
    out = []
    for ch_idx, ch in enumerate(sections):
        for ci, c in enumerate(ch.get("cases") or []):
            img = (c.get("img") or "").strip()
            if not img:
                continue
            if img.startswith(("IFRAME:", "MEDIA_CYCLER", "http://", "https://", "data:")):
                continue
            out.append({
                "chapter": ch_idx,
                "case": ci,
                "title": (c.get("title") or "").replace("\n", " ")[:60],
                "img": img,
                # Only an explicit `alt` field counts — subtitle is a visible
                # caption and serves a different purpose than accessibility alt.
                "existing_alt": (c.get("alt") or "").strip(),
            })
    return out


def scan_media_orphans(sections: list[dict], media_root: Path) -> list[str]:
    """Return media paths that exist on disk but aren't referenced in SECTIONS."""
    referenced: set[str] = set()
    for ch in sections:
        for c in ch.get("cases") or []:
            img = (c.get("img") or "").strip()
            if img and not img.startswith(("IFRAME:", "MEDIA_CYCLER", "http", "data:")):
                referenced.add(img)
    found: list[str] = []
    for p in media_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            rel = str(p.relative_to(REPO_ROOT))
            if rel not in referenced:
                found.append(rel)
    return sorted(found)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", type=Path, default=DEFAULT_HTML)
    ap.add_argument("--model", default="gemma3:12b", help="vision model (gemma3:12b|gemma3:27b)")
    ap.add_argument("--host", default="lenny", choices=list(ENDPOINTS.keys()))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="regenerate even if existing alt/subtitle")
    ap.add_argument("--scan-media", action="store_true", help="list orphan media files, don't gen")
    args = ap.parse_args()

    sections = extract_sections(args.html)

    if args.scan_media:
        orphans = scan_media_orphans(sections, REPO_ROOT / "media")
        if not orphans:
            print("No orphan images found.", file=sys.stderr)
            return 0
        print(f"# Orphan images ({len(orphans)})", file=sys.stderr)
        for p in orphans:
            print(p)
        return 0

    entries = collect_img_entries(sections)
    if not args.force:
        entries = [e for e in entries if not e["existing_alt"]]
    if args.limit:
        entries = entries[:args.limit]

    if not entries:
        print("No images need alt-text. Use --force to regenerate.", file=sys.stderr)
        return 0

    print(f"[alt] {len(entries)} images to describe via {args.model}@{args.host} "
          f"(~{len(entries)*45}s estimated)", file=sys.stderr)

    patch = []
    skipped: list[dict] = []
    for i, e in enumerate(entries, 1):
        img_path = REPO_ROOT / e["img"]
        if img_path.suffix.lower() == ".svg":
            # Vision models can't consume SVG. Skip cleanly.
            skipped.append({"reason": "svg-unsupported", **e})
            print(f"  [{i}] SKIP (SVG): {e['img']}", file=sys.stderr)
            continue
        if not img_path.exists():
            print(f"  [{i}] MISSING FILE: {e['img']}", file=sys.stderr)
            skipped.append({"reason": "file-missing", **e})
            continue
        try:
            blob = img_path.read_bytes()
        except Exception as err:
            print(f"  [{i}] read failed: {err}", file=sys.stderr)
            skipped.append({"reason": f"read-{err}", **e})
            continue

        b64 = base64.b64encode(blob).decode()
        t0 = time.time()
        try:
            alt = call_vision(args.model, args.host, b64)
        except Exception as err:
            print(f"  [{i}] vision call failed: {err}", file=sys.stderr)
            skipped.append({"reason": f"vision-{err}", **e})
            continue
        dt = time.time() - t0
        if not alt or len(alt) < 5:
            print(f"  [{i}] empty alt returned", file=sys.stderr)
            skipped.append({"reason": "empty", **e})
            continue
        patch.append({
            "chapter": e["chapter"],
            "case": e["case"],
            "img": e["img"],
            "alt": alt,
        })
        print(f"  [{i}/{len(entries)} {dt:.0f}s] {e['img']}: {alt[:80]}", file=sys.stderr)

    out = {"model": f"{args.model}@{args.host}", "patch": patch, "skipped": skipped}
    sys.stdout.write(json.dumps(out, indent=2))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
