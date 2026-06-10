#!/usr/bin/env python3
"""Headless-Chrome capture layer for Spatial Deck export tooling.

The deck itself is the renderer: index.html?shot=N renders slide N (absolute
index, settings=0) full-viewport with chrome hidden, animations settled, media
cyclers frozen on their first item. index.html?print stacks all visible slides
and appends a JSON fidelity manifest (#sd-print-manifest) describing anything
that degraded (cycler -> first frame, iframe -> placeholder, video -> frozen).

This module finds Chrome, reads that manifest, and captures per-slide PNGs.
Used by export_pdf.py (PDF assembly) and export_pptx.py --visual. Stdlib only.

CLI:
    python3 tools/capture_slides.py                       # manifest summary
    python3 tools/capture_slides.py --out-dir /tmp/shots  # capture all visible
    python3 tools/capture_slides.py --slides 1,3-5 --out-dir shots
"""
import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]


def find_chrome():
    env = os.environ.get("CHROME_BIN")
    if env and (Path(env).exists() or shutil.which(env)):
        return env
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
        w = shutil.which(c)
        if w:
            return w
    sys.exit("error: no Chrome/Chromium found. Install Google Chrome or set CHROME_BIN=/path/to/chrome")


def _file_url(html_path, query):
    return Path(html_path).resolve().as_uri() + "?" + query


def _run_chrome(chrome, args, artifact, timeout=60, settle=0.7):
    """Launch headless Chrome and wait for `artifact` (a file path) to appear
    and stabilize, then kill the process tree.

    Chrome (observed on 149/macOS) reliably WRITES its --dump-dom/--screenshot
    output but often never exits afterwards, so waiting on the process hangs
    forever. The artifact, not the exit code, is the completion signal."""
    import os
    import signal
    import time
    artifact = Path(artifact)
    profile = tempfile.mkdtemp(prefix="sd-chrome-")
    cmd = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
           "--disable-extensions", "--mute-audio", "--use-mock-keychain",
           "--no-first-run", "--no-default-browser-check",
           f"--user-data-dir={profile}"] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        deadline = time.time() + timeout
        last_size, stable_since = -1, None
        while time.time() < deadline:
            if artifact.exists():
                size = artifact.stat().st_size
                if size > 0 and size == last_size:
                    if stable_since and time.time() - stable_since >= settle:
                        return True
                    stable_since = stable_since or time.time()
                else:
                    last_size, stable_since = size, None
            if proc.poll() is not None and artifact.exists() and artifact.stat().st_size > 0:
                return True
            time.sleep(0.15)
        return artifact.exists() and artifact.stat().st_size > 0
    finally:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass
        shutil.rmtree(profile, ignore_errors=True)


def read_manifest(html_path, chrome=None, wait_ms=4500):
    """Load ?print in headless Chrome and extract the fidelity manifest.

    --timeout makes Chrome dump the DOM after wait_ms of wall time, which is
    comfortably after the page appends the manifest (~1.2s post-load)."""
    chrome = chrome or find_chrome()
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
        dump_path = tf.name
    try:
        # --dump-dom writes to stdout; capture via shell redirect into the file
        # so the artifact poller has something to watch.
        ok = _run_chrome_dump(chrome, [f"--timeout={wait_ms}", "--dump-dom",
                                       _file_url(html_path, "print")], dump_path)
        dom = Path(dump_path).read_text() if ok else ""
    finally:
        Path(dump_path).unlink(missing_ok=True)
    m = re.search(r'<script type="application/json" id="sd-print-manifest">(.*?)</script>',
                  dom, re.S)
    if not m:
        sys.exit("error: no #sd-print-manifest in rendered DOM — does this index.html "
                 "have export modes? (needs the ?print/?shot feature, spatial-deck >= 2026-06)")
    return json.loads(m.group(1))


def _run_chrome_dump(chrome, args, out_path, timeout=60):
    """Variant of _run_chrome for --dump-dom: stdout is the artifact."""
    import os
    import signal
    import time
    profile = tempfile.mkdtemp(prefix="sd-chrome-")
    cmd = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
           "--disable-extensions", "--mute-audio", "--use-mock-keychain",
           "--no-first-run", "--no-default-browser-check",
           f"--user-data-dir={profile}"] + args
    with open(out_path, "wb") as fh:
        proc = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        try:
            deadline = time.time() + timeout
            target = Path(out_path)
            last_size, stable_since = -1, None
            while time.time() < deadline:
                size = target.stat().st_size if target.exists() else 0
                if size > 0 and b"</html>" in target.read_bytes()[-200:]:
                    return True
                if size == last_size and proc.poll() is not None:
                    return size > 0
                last_size = size
                time.sleep(0.15)
            return target.exists() and target.stat().st_size > 0
        finally:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
            shutil.rmtree(profile, ignore_errors=True)


def shoot(html_path, idx, out_png, width=1920, height=1080, chrome=None, wait_ms=3500):
    """Capture slide `idx` (absolute index) to out_png."""
    chrome = chrome or find_chrome()
    ok = _run_chrome(chrome, [f"--timeout={wait_ms}",
                              f"--window-size={width},{height}",
                              f"--screenshot={out_png}",
                              _file_url(html_path, f"shot={idx}")], out_png)
    if not ok or not Path(out_png).exists():
        raise RuntimeError(f"slide {idx}: screenshot failed (no artifact within timeout)")
    return out_png


def shoot_all(html_path, indices, out_dir, width=1920, height=1080, chrome=None,
              parallel=4, progress=True):
    """Capture many slides concurrently. Returns {idx: png_path}."""
    chrome = chrome or find_chrome()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as ex:
        futs = {ex.submit(shoot, html_path, i, str(out_dir / f"slide-{i:03d}.png"),
                          width, height, chrome): i for i in indices}
        for fut in concurrent.futures.as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
            if progress:
                print(f"  captured slide {i} ({len(results)}/{len(indices)})", file=sys.stderr)
    return results


def parse_slide_spec(spec, visible):
    """'1,3-5' -> [1,3,4,5]; None -> all visible indices."""
    if not spec:
        return list(visible)
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser(description="Capture Spatial Deck slides as PNGs via headless Chrome")
    ap.add_argument("--html", default=str(REPO / "index.html"))
    ap.add_argument("--out-dir", help="capture PNGs here (omit for manifest summary only)")
    ap.add_argument("--slides", help="absolute indices, e.g. '1,3-5' (default: all visible)")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--json", action="store_true", help="print manifest as JSON")
    args = ap.parse_args()

    chrome = find_chrome()
    man = read_manifest(args.html, chrome)
    if args.json:
        print(json.dumps(man, indent=2))
    else:
        print(f"{man['total']} slides, {len(man['visible'])} visible", file=sys.stderr)

    if args.out_dir:
        indices = parse_slide_spec(args.slides, man["visible"])
        shots = shoot_all(args.html, indices, args.out_dir, args.width, args.height,
                          chrome, args.parallel)
        print(f"wrote {len(shots)} PNGs to {args.out_dir}")


if __name__ == "__main__":
    main()
