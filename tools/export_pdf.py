#!/usr/bin/env python3
"""SECTIONS-faithful PDF export — pixel-perfect, rendered by the deck itself.

Pipeline: headless Chrome captures every visible slide via index.html?shot=N
(the deck's own renderer, so layouts/themes/placed media are exact), PNGs are
converted to JPEG (sips on macOS, Pillow elsewhere), and a PDF is assembled
with a small stdlib writer (one 16:9 page per slide, 960x540pt).

A fidelity report is printed after export: anything that degraded (media
cycler -> first item, iframe -> placeholder panel, video -> frozen frame)
is listed per slide, so loss is informed, never silent.

    python3 tools/export_pdf.py                              # deck.pdf
    python3 tools/export_pdf.py --out talk.pdf --quality 90
    python3 tools/export_pdf.py --slides 1-12 --keep-shots /tmp/shots
    python3 tools/export_pdf.py --print-css --out talk.pdf   # vector text via
                                                             # Chrome print-to-pdf
                                                             # (selectable text,
                                                             # but page size is
                                                             # at Chrome's mercy)

Requires: Google Chrome (or CHROME_BIN). No Python deps on macOS; Pillow is
used for PNG->JPEG only when sips is unavailable.
"""
import argparse
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture_slides import (REPO, find_chrome, read_manifest, shoot_all,
                            parse_slide_spec, _run_chrome, _file_url)

PAGE_W, PAGE_H = 960, 540  # points: 13.333in x 7.5in @72dpi = 16:9


# ── PNG -> JPEG ─────────────────────────────────────────────────────────────

def png_to_jpeg(png_path, jpg_path, quality=85):
    if shutil.which("sips"):
        r = subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions",
                            str(quality), str(png_path), "--out", str(jpg_path)],
                           capture_output=True, text=True)
        if r.returncode == 0 and Path(jpg_path).exists():
            return jpg_path
    try:
        from PIL import Image
        Image.open(png_path).convert("RGB").save(jpg_path, "JPEG", quality=quality)
        return jpg_path
    except ImportError:
        sys.exit("error: need `sips` (macOS) or Pillow (`pip3 install Pillow`) for PNG->JPEG")


def jpeg_dimensions(path):
    """Width/height from JPEG SOF marker — no image libs needed."""
    data = Path(path).read_bytes()
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + seg_len
    raise ValueError(f"no SOF marker in {path}")


# ── Minimal PDF writer (JPEG pages via DCTDecode) ───────────────────────────

def build_pdf(jpeg_paths, out_path, title="Spatial Deck"):
    objs = []  # list of bytes; object number = index+1

    def ref(n):
        return f"{n} 0 R".encode()

    # obj 1: catalog, obj 2: pages — placeholders, filled after pages exist
    objs.append(None)
    objs.append(None)
    page_refs = []
    for jp in jpeg_paths:
        w, h = jpeg_dimensions(jp)
        img_data = Path(jp).read_bytes()
        img_n = len(objs) + 1
        objs.append(b"<< /Type /XObject /Subtype /Image /Width %d /Height %d "
                    b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode "
                    b"/Length %d >>\nstream\n" % (w, h, len(img_data))
                    + img_data + b"\nendstream")
        content = b"q %d 0 0 %d 0 0 cm /Im0 Do Q" % (PAGE_W, PAGE_H)
        cont_n = len(objs) + 1
        objs.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        page_n = len(objs) + 1
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
                    b"/Resources << /XObject << /Im0 %s >> >> /Contents %s >>"
                    % (PAGE_W, PAGE_H, ref(img_n), ref(cont_n)))
        page_refs.append(page_n)

    kids = b"[" + b" ".join(ref(n) for n in page_refs) + b"]"
    objs[1] = b"<< /Type /Pages /Kids %s /Count %d >>" % (kids, len(page_refs))
    objs[0] = b"<< /Type /Catalog /Pages 2 0 R >>"

    info_n = len(objs) + 1
    t = title.encode("latin-1", "replace").replace(b"(", b"\\(").replace(b")", b"\\)")
    objs.append(b"<< /Title (%s) /Producer (spatial-deck export_pdf.py) >>" % t)

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % (i + 1) + body + b"\nendobj\n"
    xref_at = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += (b"trailer\n<< /Size %d /Root 1 0 R /Info %s >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objs) + 1, ref(info_n), xref_at))
    Path(out_path).write_bytes(out)
    return len(page_refs)


# ── Fidelity report ─────────────────────────────────────────────────────────

def fidelity_report(manifest, exported_indices, as_json=False):
    drops = []
    for s in manifest["slides"]:
        if s["i"] not in exported_indices:
            continue
        notes = []
        if s.get("cycler", 0) > 1:
            notes.append(f"media cycler: first of {s['cycler']} items shown")
        if s.get("iframes"):
            notes.append(f"{s['iframes']} iframe(s) -> placeholder panel with URL")
        if s.get("videos"):
            notes.append(f"{s['videos']} video(s) frozen on an early frame")
        if s["type"] == "map":
            notes.append("constellation map: 3D/animated content captured as-rendered")
        if notes:
            drops.append({"slide": s["i"], "title": s["title"], "degraded": notes})
    if as_json:
        print(json.dumps({"pages": len(exported_indices), "degraded": drops}, indent=2))
        return
    print(f"\n── Fidelity report ── {len(exported_indices)} pages exported")
    if not drops:
        print("  nothing degraded — interactive-only features were not used on these slides")
    for d in drops:
        print(f"  slide {d['slide']:>3}  {d['title'][:48]}")
        for n in d["degraded"]:
            print(f"            · {n}")
    hidden = [s for s in manifest["slides"] if s["hidden"] and s["type"] != "settings"]
    if hidden:
        print(f"  ({len(hidden)} hidden slide(s) excluded, as in the live deck)")


# ── Alternate path: Chrome print-to-pdf on ?print (vector text) ─────────────

def print_css_export(html, out, chrome, wait_ms=6000):
    ok = _run_chrome(chrome, [f"--timeout={wait_ms}",
                              "--no-pdf-header-footer",
                              f"--print-to-pdf={out}",
                              _file_url(html, "print")], out, timeout=120)
    if not ok or not Path(out).exists():
        sys.exit("error: print-to-pdf produced no output within timeout")


def main():
    ap = argparse.ArgumentParser(description="Export the deck as a visually-faithful PDF")
    ap.add_argument("--html", default=str(REPO / "index.html"))
    ap.add_argument("--out", default="deck.pdf")
    ap.add_argument("--slides", help="absolute indices, e.g. '1,3-5' (default: all visible)")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--quality", type=int, default=85, help="JPEG quality (default 85)")
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--keep-shots", metavar="DIR", help="keep per-slide PNGs here")
    ap.add_argument("--print-css", action="store_true",
                    help="use Chrome print-to-pdf on ?print instead of screenshots "
                         "(vector/selectable text; page size depends on Chrome's @page support)")
    ap.add_argument("--json", action="store_true", help="fidelity report as JSON")
    ap.add_argument("--no-report", action="store_true")
    args = ap.parse_args()

    chrome = find_chrome()
    print("reading deck manifest…", file=sys.stderr)
    man = read_manifest(args.html, chrome)
    indices = sorted(parse_slide_spec(args.slides, man["visible"]))

    if args.print_css:
        print_css_export(args.html, args.out, chrome)
        print(f"wrote {args.out} (print-css path)")
        if not args.no_report:
            fidelity_report(man, indices, args.json)
        return

    shot_dir = args.keep_shots or tempfile.mkdtemp(prefix="sd-shots-")
    print(f"capturing {len(indices)} slides at {args.width}x{args.height}…", file=sys.stderr)
    shots = shoot_all(args.html, indices, shot_dir, args.width, args.height,
                      chrome, args.parallel)

    jpegs = []
    for i in indices:
        jp = str(Path(shot_dir) / f"slide-{i:03d}.jpg")
        png_to_jpeg(shots[i], jp, args.quality)
        jpegs.append(jp)

    title = Path(args.html).stem if Path(args.html).stem != "index" else "Spatial Deck"
    pages = build_pdf(jpegs, args.out, title)
    size_mb = Path(args.out).stat().st_size / 1e6
    print(f"wrote {args.out} — {pages} pages, {size_mb:.1f} MB")
    if not args.keep_shots:
        shutil.rmtree(shot_dir, ignore_errors=True)
    if not args.no_report:
        fidelity_report(man, indices, args.json)


if __name__ == "__main__":
    main()
