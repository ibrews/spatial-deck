#!/usr/bin/env python3
"""Fail if a talk fork still ships Spatial Deck's template branding.

Rule (Alex, 2026-10-22): every Spatial Deck talk gets its own social card and favicon; never the template defaults.
Generalized from ibrews/mia-2026-collective-pitch tools/check_branding.py. Checks, for the deck's index.html:
  - og:image and twitter:image exist, point at THIS repo's Pages site (not spatial-deck/), resolve to a file in the
    repo, are 1200x630, and are not byte-identical to the template's social.png;
  - every <link rel=icon|apple-touch-icon> resolves to a file that is not the template's favicon;
  - <title>, meta tags and the corner #brand label do not say "Spatial Deck".
In ibrews/spatial-deck itself (the template) it exits 0 without checking. Stdlib only.
    python3 tools/check_branding.py [--html index.html]
"""
import argparse, hashlib, re, struct, subprocess, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_MD5 = {"social.png": {"5599df306a11e9e8f54abebaa894f7d1"}, "favicon.svg": {"d58951081dfd95ec7ce14890cbcb81ec"}}
TEMPLATE_REPO = Path.home() / "GH" / "spatial-deck"


def md5(b):
    return hashlib.md5(b).hexdigest()


def template_hashes(name):
    known = set(TEMPLATE_MD5.get(name, ()))
    for repo in (TEMPLATE_REPO, ROOT):  # the template checkout, and the fork's own upstream history
        for ref in ("HEAD", "upstream/main", "origin/main"):
            r = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{name}"], capture_output=True)
            if r.returncode == 0 and (repo != ROOT or ref == "upstream/main"):
                known.add(md5(r.stdout))
    return known


def origin_slug():
    r = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True)
    m = re.search(r"github\.com[:/]([^/]+)/([^/.\s]+)", r.stdout)
    return (m.group(1).lower(), m.group(2)) if m else (None, None)


def image_size(p):
    b = p.read_bytes()[:64 * 1024]
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", b[16:24])
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b) - 9:
            if b[i] == 0xFF and b[i + 1] in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", b[i + 5:i + 9]); return w, h
            i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None


def local_path(url, owner, repo):
    """Map a Pages URL (or a relative path) to a file in this repo; None if it points somewhere else."""
    u = urlparse(url)
    if not u.scheme:
        return ROOT / url.lstrip("./")
    if owner and u.netloc.lower() == f"{owner}.github.io" and u.path.startswith(f"/{repo}/"):
        return ROOT / u.path[len(repo) + 2:]
    return None


def check(html_path):
    owner, repo = origin_slug()
    if repo == "spatial-deck":
        return None
    errs = []
    html = html_path.read_text(encoding="utf-8")
    head = html[: html.find("</head>")] if "</head>" in html else html[:20000]
    for tag in re.findall(r"<title>.*?</title>|<meta[^>]+>", head, re.S):
        if re.search(r"spatial[ -]?deck", tag, re.I):
            errs.append(f"head still says Spatial Deck: {tag[:120]}")
    social_known = template_hashes("social.png")
    for prop in ("og:image", "twitter:image"):
        m = re.search(rf'<meta (?:property|name)="{re.escape(prop)}" content="([^"]+)"', head)
        if not m:
            errs.append(f"no {prop} meta tag"); continue
        url = m.group(1)
        if "spatial-deck/" in url:
            errs.append(f"{prop} points at the template: {url}"); continue
        p = local_path(url, owner, repo)
        if p is None:
            errs.append(f"{prop} is not on this repo's Pages site ({owner}.github.io/{repo}/): {url}")
        elif not p.exists():
            errs.append(f"{prop} file missing in repo: {p.relative_to(ROOT)}")
        else:
            if md5(p.read_bytes()) in social_known:
                errs.append(f"{prop} is the template's social.png: make a card for this talk")
            if image_size(p) != (1200, 630):
                errs.append(f"{prop} is {image_size(p)}, expected (1200, 630)")
    icons = re.findall(r'<link rel="(?:icon|alternate icon|apple-touch-icon)"[^>]*href="([^"]+)"', head)
    if not icons:
        errs.append("no favicon <link> in head")
    fav_known = template_hashes("favicon.svg")
    for href in icons:
        p = local_path(href, owner, repo)
        if p is None or not p.exists():
            errs.append(f"favicon missing: {href}")
        elif md5(p.read_bytes()) in fav_known:
            errs.append(f"favicon {href} is the template's favicon")
    if re.search(r'<div id="brand">\s*Spatial Deck', html, re.I):
        errs.append('corner #brand label still says "Spatial Deck"')
    return errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--html", default=str(ROOT / "index.html"))
    e = check(Path(ap.parse_args().html))
    if e is None:
        print("check_branding: template repo (ibrews/spatial-deck), nothing to check"); sys.exit(0)
    for x in e:
        print(f"BRANDING: {x}", file=sys.stderr)
    print("branding OK" if not e else f"{len(e)} branding problem(s)")
    sys.exit(1 if e else 0)
