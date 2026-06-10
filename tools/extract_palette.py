"""Extract a Spatial Deck palette from a reference image.

Uses pure-Python KMeans on a downsampled version of the image to find N
dominant colors, then maps them into Spatial Deck's token schema (bg,
bg_dark, text, dim, primary, secondary, teal, purple, amber, rose) by
luminance and hue.

Optional --vibe flag asks gemma3:12b@Lenny to describe the mood in one
short phrase, which is emitted as a comment header in the output CSS.
Never mutates index.html directly — writes a CSS file that you then
pipe through tools/import_tokens.py.

Usage:
    python3 tools/extract_palette.py photo.jpg
    python3 tools/extract_palette.py photo.jpg --out my-palette.css
    python3 tools/extract_palette.py photo.jpg -k 8 --vibe
"""
from __future__ import annotations
import argparse
import base64
import colorsys
import json
import random
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from fleet_client import ENDPOINTS, call_vision  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def downsample(img: Image.Image, max_dim: int = 200) -> list[tuple[int, int, int]]:
    """Convert image to RGB, downsample so KMeans is fast, return pixel list."""
    img = img.convert("RGB")
    w, h = img.size
    scale = min(1.0, max_dim / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return list(img.getdata())


def kmeans(points: list[tuple[int, int, int]], k: int, *, max_iter: int = 20,
           seed: int = 0) -> list[tuple[int, int, int]]:
    """Classic k-means with random init. Returns centroids as 0-255 RGB tuples."""
    rng = random.Random(seed)
    # K-means++ style seeding for better spread — pick first at random, then
    # each subsequent pick weighted by squared distance to nearest existing.
    centroids = [points[rng.randrange(len(points))]]
    for _ in range(k - 1):
        dists = []
        for p in points:
            m = min((p[0]-c[0])**2 + (p[1]-c[1])**2 + (p[2]-c[2])**2 for c in centroids)
            dists.append(m)
        total = sum(dists) or 1
        pick = rng.random() * total
        acc = 0.0
        for p, d in zip(points, dists):
            acc += d
            if acc >= pick:
                centroids.append(p)
                break

    for _ in range(max_iter):
        buckets: list[list[tuple[int, int, int]]] = [[] for _ in range(k)]
        for p in points:
            best_i, best_d = 0, float("inf")
            for i, c in enumerate(centroids):
                d = (p[0]-c[0])**2 + (p[1]-c[1])**2 + (p[2]-c[2])**2
                if d < best_d:
                    best_d, best_i = d, i
            buckets[best_i].append(p)
        new_centroids = []
        for i, bucket in enumerate(buckets):
            if not bucket:
                new_centroids.append(centroids[i])
                continue
            r = sum(p[0] for p in bucket) / len(bucket)
            g = sum(p[1] for p in bucket) / len(bucket)
            b = sum(p[2] for p in bucket) / len(bucket)
            new_centroids.append((round(r), round(g), round(b)))
        if new_centroids == centroids:
            break
        centroids = new_centroids
    return centroids


def rgb_to_hex(c: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*c)


def luminance(c: tuple[int, int, int]) -> float:
    """Perceived luminance (ITU-R BT.601)."""
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def saturation(c: tuple[int, int, int]) -> float:
    h, s, v = colorsys.rgb_to_hsv(c[0]/255, c[1]/255, c[2]/255)
    return s


def hue_deg(c: tuple[int, int, int]) -> float:
    h, s, v = colorsys.rgb_to_hsv(c[0]/255, c[1]/255, c[2]/255)
    return h * 360


# Hue bucket centers (degrees) for the four accent tokens.
ACCENT_HUES = {"rose": 350, "amber": 40, "teal": 175, "purple": 280}


def _hue_dist(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def assign_tokens(centroids: list[tuple[int, int, int]]) -> dict[str, str]:
    """Map K centroids into Spatial Deck's token schema."""
    # Sort by luminance for bg/text picks.
    by_lum = sorted(centroids, key=luminance)
    tokens: dict[str, str] = {}
    tokens["bg_dark"] = rgb_to_hex(by_lum[0])
    # Pick a slightly lighter bg. If centroids are tightly clustered, nudge it.
    bg_candidate = by_lum[1] if len(by_lum) > 1 else by_lum[0]
    if luminance(bg_candidate) - luminance(by_lum[0]) < 20:
        # lift it 15 units
        r, g, b = bg_candidate
        bg_candidate = (min(255, r + 15), min(255, g + 15), min(255, b + 15))
    tokens["bg"] = rgb_to_hex(bg_candidate)

    # text is the lightest centroid; if it's too saturated, approximate with
    # a nearby neutral (keeps legibility).
    text_candidate = by_lum[-1]
    if saturation(text_candidate) > 0.25:
        # Desaturate toward a warm off-white.
        r, g, b = text_candidate
        avg = (r + g + b) // 3
        text_candidate = ((r + avg)//2, (g + avg)//2, (b + avg)//2)
    tokens["text"] = rgb_to_hex(text_candidate)

    # dim: a mid-luminance muted color.
    mids = [c for c in by_lum if 60 < luminance(c) < 200]
    dim_candidate = mids[len(mids)//2] if mids else by_lum[len(by_lum)//2]
    # Push toward neutral.
    r, g, b = dim_candidate
    avg = (r + g + b) // 3
    dim_candidate = ((r + avg)//2, (g + avg)//2, (b + avg)//2)
    tokens["dim"] = rgb_to_hex(dim_candidate)

    # Most saturated colors as primary / secondary.
    by_sat = sorted(centroids, key=saturation, reverse=True)
    saturated = [c for c in by_sat if saturation(c) > 0.15]
    if saturated:
        tokens["primary"] = rgb_to_hex(saturated[0])
        tokens["secondary"] = rgb_to_hex(saturated[1] if len(saturated) > 1 else saturated[0])
    else:
        tokens["primary"] = rgb_to_hex(by_sat[0])
        tokens["secondary"] = rgb_to_hex(by_sat[-1])

    # Assign the 4 accent tokens by hue distance to canonical centers.
    # Pick the saturated-enough centroid closest to each hue target. If the
    # nearest hit is too far off (no matching color in the image), synthesize
    # the accent from scratch at the target hue using the primary color's
    # saturation/value — keeps the accent palette visually coherent even for
    # monochrome-ish reference images.
    HUE_TOLERANCE_DEG = 35
    usable = [c for c in centroids if saturation(c) > 0.2] or centroids
    prim_rgb = tuple(int(tokens["primary"].lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    _, prim_s, prim_v = colorsys.rgb_to_hsv(prim_rgb[0]/255, prim_rgb[1]/255, prim_rgb[2]/255)
    # Ensure the synthesized accent is vivid enough to read as an accent.
    synth_s = max(prim_s, 0.5)
    synth_v = max(prim_v, 0.7)
    for name, target_hue in ACCENT_HUES.items():
        best = min(usable, key=lambda c: _hue_dist(hue_deg(c), target_hue))
        if _hue_dist(hue_deg(best), target_hue) <= HUE_TOLERANCE_DEG and saturation(best) > 0.2:
            tokens[name] = rgb_to_hex(best)
        else:
            r, g, b = colorsys.hsv_to_rgb(target_hue / 360, synth_s, synth_v)
            tokens[name] = rgb_to_hex((round(r*255), round(g*255), round(b*255)))

    return tokens


def vibe_phrase(img_path: Path, model: str = "gemma3:12b", host: str = "lenny") -> str | None:
    try:
        blob = img_path.read_bytes()
    except Exception:
        return None
    b64 = base64.b64encode(blob).decode()
    prompt = ("Describe the mood of this image in a single short phrase (3-6 words). "
              "Examples: 'warm dusk warehouse', 'cold neon diner', 'arctic minimalism'. "
              "No punctuation. No preamble.")
    try:
        raw = call_vision(prompt, b64, model=model, endpoint=ENDPOINTS.get(host),
                          timeout=60, temperature=0.3)
    except Exception as e:
        print(f"[vibe] call failed: {e}", file=sys.stderr)
        return None
    text = raw.strip().strip('."\'').split("\n", 1)[0]
    # Strip any leading preamble punctuation/quotes.
    return text[:60] if text else None


def emit_css(tokens: dict[str, str], vibe: str | None, source: str) -> str:
    header = [f"/* Palette extracted from {source}"]
    if vibe:
        header.append(f"   Vibe: {vibe}")
    header.append("*/")
    order = ["bg", "bg_dark", "text", "dim", "primary", "secondary",
             "teal", "purple", "amber", "rose"]
    body = ":root {"
    body_lines = []
    for key in order:
        if key in tokens:
            var = "--" + key.replace("_", "-")
            body_lines.append(f"  {var}: {tokens[key]};")
    return "\n".join(header) + "\n" + body + "\n" + "\n".join(body_lines) + "\n}\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("-k", "--clusters", type=int, default=8, help="k for kmeans")
    ap.add_argument("--out", type=Path, default=None, help="output CSS path")
    ap.add_argument("--vibe", action="store_true", help="ask Lenny for a mood phrase")
    ap.add_argument("--json", action="store_true", help="emit JSON tokens instead of CSS")
    args = ap.parse_args()

    if not args.image.exists():
        print(f"ERROR: {args.image} not found", file=sys.stderr)
        return 2

    img = Image.open(args.image)
    pixels = downsample(img)
    print(f"[palette] {len(pixels)} pixels → {args.clusters} centroids", file=sys.stderr)
    centroids = kmeans(pixels, args.clusters)
    print(f"[palette] centroids: {[rgb_to_hex(c) for c in centroids]}", file=sys.stderr)
    tokens = assign_tokens(centroids)

    vibe = None
    if args.vibe:
        vibe = vibe_phrase(args.image)
        if vibe:
            print(f"[vibe] {vibe}", file=sys.stderr)

    if args.json:
        sys.stdout.write(json.dumps({"tokens": tokens, "vibe": vibe}, indent=2) + "\n")
        return 0

    css = emit_css(tokens, vibe, args.image.name)
    out_path = args.out or (REPO_ROOT / "tools" / f"palette-{args.image.stem}.css")
    out_path.write_text(css)
    print(f"[done] Wrote {out_path.relative_to(REPO_ROOT)}", file=sys.stderr)
    print(f"[next] python3 tools/import_tokens.py {out_path.relative_to(REPO_ROOT)}", file=sys.stderr)
    sys.stdout.write(css)
    return 0


if __name__ == "__main__":
    sys.exit(main())
