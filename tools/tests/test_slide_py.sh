#!/usr/bin/env bash
# slide.py's provenance and dependency checks have to fail on deliberately broken sources before a clean pull or a
# passing check means anything. Builds throwaway git repos (source + bare remote) and a host deck in a temp folder.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(dirname "$(dirname "$HERE")")"; SLIDE="python3 $REPO/tools/slide.py"
W="${OUT:-$(mktemp -d)}"; mkdir -p "$W"; fail=0
ok()  { echo "ok   $1"; }
bad() { echo "FAIL $1"; fail=1; }
expect() { # expect <0|1> <description> <grep-pattern> <command...>
  local want=$1 what=$2 pat=$3; shift 3
  out="$("$@" 2>&1)"; rc=$?
  if { [ "$want" = 0 ] && [ $rc -eq 0 ]; } || { [ "$want" = 1 ] && [ $rc -ne 0 ]; }; then
    if [ -z "$pat" ] || grep -qE "$pat" <<<"$out"; then ok "$what"; else bad "$what (exit $rc, output lacks /$pat/):"; echo "$out" | sed 's/^/     /'; fi
  else bad "$what (exit $rc, wanted $( [ "$want" = 0 ] && echo 0 || echo nonzero )):"; echo "$out" | sed 's/^/     /'; fi
}
deck() { mkdir -p "$1/slides"; cp "$REPO/index.html" "$1/"; cp "$REPO/slides/sd-frame.js" "$1/slides/"; $SLIDE sync "$1" >/dev/null; }
mod() { # mod <deck> <ns/id> <extra defineSlide fields> <render body>
  mkdir -p "$1/slides/$2"
  printf "SD.defineSlide({ id: '%s', steps: 0, %s render(el) { %s return {}; } });\n" "$2" "$3" "$4" > "$1/slides/$2/slide.js"
}

# ── source repo with a bare remote ──
SRC="$W/src"; git init -q --bare "$W/remote.git"; deck "$SRC"
git -C "$SRC" init -q -b main; git -C "$SRC" remote add origin "$W/remote.git"
mod "$SRC" t/clean "" "el.textContent='clean';"
git -C "$SRC" add -A; git -C "$SRC" -c user.name=t -c user.email=t@t commit -qm init; git -C "$SRC" push -q origin main 2>/dev/null
mod "$SRC" t/untracked "" "el.textContent='never committed';"

DST="$W/dst"; deck "$DST"
expect 0 "pull of a committed + pushed module succeeds"            "pulled t/clean"     $SLIDE pull "$SRC" t/clean --into "$DST"
grep -q '"dirty"' "$DST/slides/t/clean/.pulled.json" && bad "clean pull should not record dirty" || ok "clean pull records no dirty field"
expect 1 "pull of an untracked module is refused"                  "untracked: slides/t/untracked" $SLIDE pull "$SRC" t/untracked --into "$DST"
[ -e "$DST/slides/t/untracked" ] && bad "refused pull must copy nothing" || ok "refused pull copied nothing"
expect 0 "--dirty pulls it anyway"                                 "pulled with --dirty" $SLIDE pull "$SRC" t/untracked --into "$DST" --dirty
grep -q 'untracked: slides/t/untracked' "$DST/slides/t/untracked/.pulled.json" && ok "--dirty is recorded in .pulled.json" || bad "--dirty not recorded"

git -C "$SRC" add -A; git -C "$SRC" -c user.name=t -c user.email=t@t commit -qm local-only   # committed, never pushed
mod "$SRC" t/clean "" "el.textContent='clean v2';"; git -C "$SRC" add -A; git -C "$SRC" -c user.name=t -c user.email=t@t commit -qm v2
expect 1 "pull from a commit no remote holds is refused"           "not on any remote branch" $SLIDE pull "$SRC" t/clean --into "$DST" --force
echo "local only" >> "$SRC/slides/t/clean/slide.js"
expect 1 "pull of a modified (uncommitted) file is refused"        "uncommitted change: slides/t/clean/slide.js" $SLIDE pull "$SRC" t/clean --into "$DST" --force

# ── runtime dependencies (importmap) ──
H="$W/host"; deck "$H"
expect 0 "identity: an empty host deck passes check"                "0 problem"          $SLIDE check "$H"
mod "$H" t/undeclared "" "import('three').then(()=>{});"
$SLIDE sync "$H" >/dev/null
expect 1 "check fails a module that imports 'three' without declaring it" "t/undeclared: imports 'three' but does not declare it" $SLIDE check "$H"
rm -r "$H/slides/t/undeclared"
mod "$H" t/declared "requires: { importmap: ['three', 'three/addons/controls/OrbitControls.js'] }," "import('three').then(()=>{});"
$SLIDE sync "$H" >/dev/null
expect 0 "declared + mapped by the host importmap passes (prefix key three/addons/ included)" "0 problem" $SLIDE check "$H"
sed -i.bak '/^<script type="importmap">/d' "$H/index.html"
expect 1 "check fails when the host deck has no importmap entry"   "requires importmap entry 'three', which index.html does not map" $SLIDE check "$H"
mkdir -p "$H/slides/t/framed"
printf "SD.defineSlide({ id: 't/framed', frame: 'f.html', steps: 0 , requires: { importmap: ['three'] } });\n" > "$H/slides/t/framed/slide.js"
printf '<!doctype html><script src="../../sd-frame.js"></script><script type="module">import * as T from "three";</script>\n' > "$H/slides/t/framed/f.html"
$SLIDE sync "$H" >/dev/null
expect 1 "an iframe module is checked against its own document's importmap" "t/framed: requires importmap entry 'three', which slides/t/framed/f.html does not map" $SLIDE check "$H"

echo "work dir: $W"; exit $fail
