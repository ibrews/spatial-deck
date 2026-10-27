#!/usr/bin/env python3
"""Slide modules: list what a deck has, pull one into another deck, keep the deck's module list in sync.

A slide module is slides/<namespace>/<id>/slide.js plus its assets (slides/README.md has the contract).
    python3 tools/slide.py list  <deck>                       # modules in a deck dir, index.html or https URL
    python3 tools/slide.py pull  <deck> <ns/id> --into <talk>  # copy a module (and its files) into another deck
    python3 tools/slide.py sync  [<talk>]                     # rewrite the deck's SD SLIDE MODULES block from disk
    python3 tools/slide.py check [<talk>]                     # static checks: every use: resolves, every file declared

<deck> is a folder (with index.html and slides/), a path to index.html, or a URL such as a GitHub Pages deck.
Metadata is read by running each slide.js under Node with a stub SD.defineSlide, so it is exactly what the deck
sees; nothing is rendered. Needs node on PATH.
"""
import argparse, datetime, hashlib, json, re, shutil, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

A, B = "<!-- ── SD SLIDE MODULES START ── -->", "<!-- ── SD SLIDE MODULES END ── -->"
FRAME_RUNTIME = "slides/sd-frame.js"
ROOT = Path(__file__).resolve().parent.parent

# Runs slide.js files in a sandbox where SD.defineSlide records the definition; functions are reported, not called,
# except a steps(props) function, which is resolved against the module's own default props.
META_JS = r"""
const vm=require('vm'),fs=require('fs');const out=[];
for(const f of process.argv.slice(1)){
  const defs=[];const sandbox={SD:{defineSlide:d=>{defs.push(d);return d;}},document:{currentScript:null},window:{},console};
  try{vm.runInNewContext(fs.readFileSync(f,'utf8'),sandbox,{filename:f,timeout:2000});}catch(e){out.push({file:f,error:String(e&&e.message||e)});continue;}
  for(const d of defs){let steps=d.steps;let dyn=false;if(typeof steps==='function'){dyn=true;try{steps=steps(d.props||{});}catch(e){steps=null;}}
    out.push({file:f,id:d.id,steps:steps==null?0:steps,dynamicSteps:dyn,duration:d.duration||null,frame:d.frame||null,
      seekable:typeof d.seek==='function'||!!d.frame||/\bseek\s*\(/.test(String(d.render||'')),
      props:Object.keys(d.props||{}),assets:d.assets||[],shared:d.shared||[],provenance:d.provenance||[],notes:d.notes||'',version:d.version||1});}
}
process.stdout.write(JSON.stringify(out));
"""


def node_meta(files):
    if not files:
        return []
    try:
        r = subprocess.run(["node", "-e", META_JS, *map(str, files)], capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        sys.exit("slide.py: node is not on PATH (it reads slide.js metadata)")
    if r.returncode:
        sys.exit("slide.py: reading slide.js failed:\n" + r.stderr)
    return json.loads(r.stdout)


def is_url(s):
    return bool(re.match(r"^https?://", s))


def deck_dir(arg):
    p = Path(arg).expanduser().resolve()
    return p.parent if p.is_file() else p


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()


def uses_in(html):
    """`use:` ids in a deck's SECTIONS (and any talk source spliced into it), with counts."""
    ids = re.findall(r"""\buse\s*:\s*['"]([\w-]+/[\w-]+)['"]""", html)
    return {i: ids.count(i) for i in dict.fromkeys(ids)}


def listed_in(html):
    m = re.search(re.escape(A) + r"(.*?)" + re.escape(B), html, re.S)
    return re.findall(r'src="([^"]+/slide\.js)"', m.group(1)) if m else None


def module_files(root):
    return sorted((root / "slides").glob("*/*/slide.js"))


def cmd_list(a):
    if is_url(a.deck):
        base = a.deck if a.deck.endswith("/") else a.deck.rsplit("/", 1)[0] + "/"
        html = fetch(a.deck if not a.deck.endswith("/") else a.deck + "index.html").decode("utf-8", "replace")
        srcs = listed_in(html) or []
        tmp = Path(subprocess.run(["mktemp", "-d"], capture_output=True, text=True).stdout.strip())
        files = []
        for src in srcs:
            dst = tmp / src
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(fetch(urllib.parse.urljoin(base, src)))
            files.append(dst)
        meta = node_meta(files)
        for m in meta:
            m["file"] = str(Path(m["file"]).relative_to(tmp))
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        root = deck_dir(a.deck)
        idx = root / "index.html"
        html = idx.read_text(encoding="utf-8") if idx.exists() else ""
        files = module_files(root)
        meta = node_meta(files)
        for m in meta:
            m["file"] = str(Path(m["file"]).relative_to(root))
    used = uses_in(html)
    if a.json:
        print(json.dumps({"modules": meta, "uses": used}, indent=1))
        return 0
    if not meta:
        print("no slide modules found")
    for m in meta:
        if "error" in m:
            print(f"  !! {m['file']}: {m['error']}")
            continue
        kind = "frame" if m["frame"] else "inline"
        dur = f"{m['duration']}s" if m["duration"] else "-"
        st = f"{m['steps']}{'*' if m['dynamicSteps'] else ''}"
        print(f"  {m['id']:<28} steps {st:<4} duration {dur:<6} {kind:<6} {'seekable' if m['seekable'] else 'not seekable':<13} used {used.get(m['id'], 0)}x   {m['file']}")
    missing = [u for u in used if u not in {m.get('id') for m in meta}]
    for u in missing:
        print(f"  ?? {u}: used by the deck but no module defines it")
    if any(m.get("dynamicSteps") for m in meta):
        print("  * steps depend on props; shown for the module's defaults (the deck resolves them per use)")
    return 1 if missing else 0


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_head(d):
    r = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True)
    r2 = subprocess.run(["git", "-C", str(d), "remote", "get-url", "origin"], capture_output=True, text=True)
    return (r.stdout.strip() or None), (r2.stdout.strip() or None)


def cmd_pull(a):
    mid = a.id
    if not re.match(r"^[\w-]+/[\w-]+$", mid):
        sys.exit(f"slide.py: module id must be <namespace>/<id>, got {mid!r}")
    into = deck_dir(a.into)
    if not (into / "index.html").exists():
        sys.exit(f"slide.py: {into} has no index.html")
    dst = into / "slides" / mid
    tmp = None
    if is_url(a.deck):
        base = a.deck if a.deck.endswith("/") else a.deck.rsplit("/", 1)[0] + "/"
        tmp = Path(subprocess.run(["mktemp", "-d"], capture_output=True, text=True).stdout.strip())
        src = tmp / "slides" / mid
        src.mkdir(parents=True)
        (src / "slide.js").write_bytes(fetch(urllib.parse.urljoin(base, f"slides/{mid}/slide.js")))
        meta = node_meta([src / "slide.js"])[0]
        for f in [meta["frame"], *meta["assets"]]:
            if f:
                (src / f).parent.mkdir(parents=True, exist_ok=True)
                (src / f).write_bytes(fetch(urllib.parse.urljoin(base, f"slides/{mid}/{f}")))
        if meta["frame"]:
            (tmp / FRAME_RUNTIME).write_bytes(fetch(urllib.parse.urljoin(base, FRAME_RUNTIME)))
        for sh in meta["shared"]:
            (tmp / "slides" / sh).parent.mkdir(parents=True, exist_ok=True)
            (tmp / "slides" / sh).write_bytes(fetch(urllib.parse.urljoin(base, f"slides/{sh}")))
        origin, commit, root = a.deck, None, tmp
    else:
        root = deck_dir(a.deck)
        src = root / "slides" / mid
        if not (src / "slide.js").exists():
            have = ", ".join(m["id"] for m in node_meta(module_files(root)) if "id" in m) or "none"
            sys.exit(f"slide.py: {root} has no module {mid} (it has: {have})")
        meta = node_meta([src / "slide.js"])[0]
        commit, origin = git_head(root)
        origin = origin or str(root)
    if "error" in meta:
        sys.exit(f"slide.py: {mid}/slide.js does not load: {meta['error']}")
    undeclared = [p for p in src.rglob("*") if p.is_file() and p.name not in ("slide.js", ".pulled.json")
                  and str(p.relative_to(src)) not in set(meta["assets"]) | {meta["frame"]}]
    if undeclared and not is_url(a.deck):
        print(f"slide.py: note: {len(undeclared)} file(s) in {mid}/ are not in its assets list and will be copied anyway: "
              + ", ".join(str(p.relative_to(src)) for p in undeclared[:5]))
    if dst.exists() and not a.force:
        same = all((dst / p.relative_to(src)).exists() and sha256(dst / p.relative_to(src)) == sha256(p)
                   for p in src.rglob("*") if p.is_file() and p.name != ".pulled.json")
        if same:
            print(f"slide.py: {mid} is already in {into} and identical; nothing to do")
            return cmd_sync(argparse.Namespace(talk=str(into), quiet=True))
        sys.exit(f"slide.py: {dst} exists and differs; pass --force to replace it (your copy is overwritten)")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".pulled.json"))
    if meta["frame"]:
        rt_src, rt_dst = root / FRAME_RUNTIME, into / FRAME_RUNTIME
        if rt_src.exists() and (not rt_dst.exists() or sha256(rt_src) != sha256(rt_dst)):
            if rt_dst.exists():
                print(f"slide.py: updating {FRAME_RUNTIME} in {into} (frame protocol runtime)")
            shutil.copyfile(rt_src, rt_dst)
    # Files shared by several modules (slides/kit/…) come along; a differing local copy is kept unless --force.
    for sh in meta["shared"]:
        s_src, s_dst = root / "slides" / sh, into / "slides" / sh
        if not s_src.exists():
            sys.exit(f"slide.py: {mid} needs slides/{sh} but the source deck does not have it")
        if s_dst.exists() and sha256(s_dst) != sha256(s_src) and not a.force:
            print(f"slide.py: keeping your slides/{sh} (differs from the source's; --force replaces it)")
            continue
        s_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(s_src, s_dst)
    rec = {"id": mid, "pulled_from": origin, "commit": commit, "pulled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "files": {str(p.relative_to(dst)): sha256(p) for p in sorted(dst.rglob("*")) if p.is_file()},
           "provenance": meta["provenance"]}
    (dst / ".pulled.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    cmd_sync(argparse.Namespace(talk=str(into), quiet=True))
    print(f"slide.py: pulled {mid} ({meta['steps']} step(s){', ' + str(meta['duration']) + 's' if meta['duration'] else ''}) into {dst.relative_to(into)}")
    print("  add it to SECTIONS as a case, overriding any of its props:")
    print(f"    {{ use: '{mid}', props: {{ {', '.join(p + ': …' for p in meta['props'])} }}, notes: '' }},")
    return 0


def cmd_sync(a):
    root = deck_dir(a.talk)
    idx = root / "index.html"
    s = idx.read_text(encoding="utf-8")
    if A not in s or B not in s:
        sys.exit(f"slide.py: {idx} has no SD SLIDE MODULES block; re-seed it from ibrews/spatial-deck index.html (module loader)")
    files = module_files(root)
    tags = "".join(f'<script src="{p.relative_to(root).as_posix()}"></script>\n' for p in files)
    new = re.sub(re.escape(A) + r".*?" + re.escape(B), lambda m: A + "\n" + tags + B, s, count=1, flags=re.S)
    if new != s:
        idx.write_text(new, encoding="utf-8")
    if not getattr(a, "quiet", False):
        print(f"slide.py: {idx.name} lists {len(files)} module(s)" + ("" if new != s else " (unchanged)"))
    return 0


def cmd_check(a):
    """Static half of the steps lint; the behavioral half is tools/sweep_deck.mjs --steps."""
    root = deck_dir(a.talk)
    html = (root / "index.html").read_text(encoding="utf-8")
    meta = node_meta(module_files(root))
    by_id = {m["id"]: m for m in meta if "id" in m}
    errs = [f"{m['file']}: does not load: {m['error']}" for m in meta if "error" in m]
    listed = listed_in(html)
    if listed is None:
        errs.append("index.html has no SD SLIDE MODULES block")
    else:
        disk = [p.relative_to(root).as_posix() for p in module_files(root)]
        if sorted(listed) != sorted(disk):
            errs.append(f"modules block is stale (lists {len(listed)}, slides/ has {len(disk)}): run tools/slide.py sync")
    for u in uses_in(html):
        if u not in by_id:
            errs.append(f"use: '{u}' has no module in slides/")
    for m in by_id.values():
        d = root / "slides" / m["id"]
        if Path(m["file"]).resolve().parent != d.resolve():
            errs.append(f"{m['file']}: defines {m['id']} but lives in {Path(m['file']).parent}; the folder must match the id")
        declared = set(m["assets"]) | ({m["frame"]} if m["frame"] else set())
        for f in declared:
            if not (d / f).exists():
                errs.append(f"{m['id']}: declares {f} but the file is missing")
        for p in d.rglob("*"):
            if p.is_file() and p.name not in ("slide.js", ".pulled.json", "README.md") and p.relative_to(d).as_posix() not in declared:
                errs.append(f"{m['id']}: {p.relative_to(d)} is not in assets (slide.py pull from a URL would miss it)")
        for sh in m.get("shared", []):
            if not (root / "slides" / sh).exists():
                errs.append(f"{m['id']}: needs shared file slides/{sh}, which is missing")
        if m["frame"] and not (root / FRAME_RUNTIME).exists():
            errs.append(f"{m['id']}: is an iframe module but {FRAME_RUNTIME} is missing")
    for e in errs:
        print("  FAIL " + e)
    print(f"slide.py check: {len(by_id)} module(s), {len(uses_in(html))} used id(s), {len(errs)} problem(s)")
    return 1 if errs else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("deck"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("pull"); p.add_argument("deck"); p.add_argument("id"); p.add_argument("--into", required=True); p.add_argument("--force", action="store_true")
    p = sub.add_parser("sync"); p.add_argument("talk", nargs="?", default=str(ROOT))
    p = sub.add_parser("check"); p.add_argument("talk", nargs="?", default=str(ROOT))
    a = ap.parse_args()
    return {"list": cmd_list, "pull": cmd_pull, "sync": cmd_sync, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
