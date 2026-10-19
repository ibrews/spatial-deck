#!/usr/bin/env bash
# new_talk.sh — the ONE sanctioned way to start (or publish) a Spatial Deck talk.
# Convention (KB projects/spatial-deck/conventions.md): one public repo per talk, ibrews/<slug>, Pages-served,
# upstream = ibrews/spatial-deck. Talk content NEVER goes on a branch of ibrews/spatial-deck.
# Pre-authorized by Alex 2026-10-16 (KB intelligence/decisions/2026-10-16-preauthorize-spatial-deck-talk-repos.md).
#
#   tools/new_talk.sh <slug> --title "Talk title" [--description "..."] [--from <checkout>] [--dir <path>] [--dry-run]
#
#   --from <checkout>  publish an existing local checkout's current branch as the new repo's main
#                      (it must already contain README.md with a "## Things to Try" section)
#   (no --from)        seed a fresh talk: clone ibrews/spatial-deck main into --dir (default ~/GH/<slug>)
#                      and write a starter README; you then edit SECTIONS and push
# Steps: refuse if ibrews/<slug> exists → create public repo → push main → origin/upstream remotes →
#        enable GitHub Pages (main, /) → set homepage → print the Pages URL + KB follow-ups.
set -euo pipefail
OWNER=ibrews; UPSTREAM=https://github.com/ibrews/spatial-deck
die(){ echo "new_talk: $*" >&2; exit 1; }
[ $# -ge 1 ] || die "usage: new_talk.sh <slug> --title \"...\" [--description ...] [--from <checkout>] [--dir <path>] [--dry-run]"
SLUG=$1; shift; TITLE=""; DESC=""; FROM=""; DIR=""; DRY=0; RESUME=0
while [ $# -gt 0 ]; do case "$1" in
  --title) TITLE=$2; shift 2;; --description) DESC=$2; shift 2;; --from) FROM=$2; shift 2;;
  --dir) DIR=$2; shift 2;; --dry-run) DRY=1; shift;; --resume) RESUME=1; shift;; *) die "unknown arg $1";; esac; done
[[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]{2,60}$ ]] || die "slug must be lowercase kebab-case: $SLUG"
[ "$SLUG" != "spatial-deck" ] || die "refusing: talks never go in ibrews/spatial-deck itself"
[ -n "$TITLE" ] || die "--title is required"
[ -n "$DESC" ] || DESC="$TITLE — Alex Coulombe"
command -v gh >/dev/null || die "gh CLI required"
if gh repo view "$OWNER/$SLUG" >/dev/null 2>&1; then [ "$RESUME" = 1 ] || die "$OWNER/$SLUG already exists — not overwriting (use --resume to finish a half-done run)"; else RESUME=0; fi
run(){ echo "+ $*"; if [ "$DRY" = 0 ]; then "$@"; fi; }   # NOTE: `[..] || cmd` would disable set -e

if [ -n "$FROM" ]; then
  SRC=$(cd "$FROM" && pwd); git -C "$SRC" rev-parse --git-dir >/dev/null || die "--from is not a git checkout"
  [ -z "$(git -C "$SRC" status --porcelain)" ] || die "--from checkout has uncommitted changes; commit first"
  grep -q '^## Things to Try' "$SRC/README.md" 2>/dev/null || die "README.md with a '## Things to Try' section is required before publishing"
  BR=$(git -C "$SRC" branch --show-current); [ -n "$BR" ] || die "--from checkout is on a detached HEAD"
else
  SRC=${DIR:-$HOME/GH/$SLUG}; [ ! -e "$SRC" ] || die "$SRC already exists"
  run git clone -q "$UPSTREAM" "$SRC"; BR=main
  if [ $DRY = 0 ]; then
    cat > "$SRC/README.md" <<EOF
# $TITLE

$DESC

**▶ View the deck:** https://$OWNER.github.io/$SLUG/

Built on [Spatial Deck](https://github.com/ibrews/spatial-deck), the single-file HTML presentation framework.

## Quickstart

\`\`\`bash
git clone https://github.com/$OWNER/$SLUG && open $SLUG/index.html
\`\`\`

## Things to Try

1. Open \`index.html\` and press → to step through the talk.
2. Press **N** for presenter notes, or open \`index.html?notes\` on a phone.
3. Open \`index.html?edit\` and press **M** for move mode to reposition anything.

## Credits

**Alex Coulombe Presents** · framework: [Spatial Deck](https://github.com/ibrews/spatial-deck)
EOF
    git -C "$SRC" add README.md && git -C "$SRC" commit -q -m "docs: README for $SLUG talk"
  fi
fi

[ "$RESUME" = 1 ] || run gh repo create "$OWNER/$SLUG" --public --description "$DESC"
# remotes: the template becomes "upstream", the new talk repo becomes "origin"
O=$(git -C "$SRC" remote get-url origin 2>/dev/null || true)
if [ -n "$O" ]; then
  case "$O" in *ibrews/spatial-deck*) git -C "$SRC" remote get-url upstream >/dev/null 2>&1 && run git -C "$SRC" remote remove origin || run git -C "$SRC" remote rename origin upstream;;
               *"$OWNER/$SLUG"*) : ;;  # resume: origin already points at the talk repo
               *) die "--from checkout's origin is $O (expected ibrews/spatial-deck or none) — refusing to guess";; esac
fi
git -C "$SRC" remote get-url upstream >/dev/null 2>&1 || run git -C "$SRC" remote add upstream "$UPSTREAM"
git -C "$SRC" remote get-url origin >/dev/null 2>&1 || run git -C "$SRC" remote add origin "git@github.com:$OWNER/$SLUG.git"   # SSH: HTTPS 408s on the first media-heavy push
run git -C "$SRC" -c http.postBuffer=1048576000 push -q -u origin "$BR:main"   # big media packs 408 on the default buffer
[ "$BR" = main ] || run git -C "$SRC" checkout -q -B main "origin/main"
grep -qx 'notes-config.json' "$SRC/.gitignore" 2>/dev/null || echo "new_talk: warning — add notes-config.json to .gitignore" >&2
# No leading slash on gh api endpoints: Git Bash (MSYS) rewrites "/repos/..." into "C:/Program Files/Git/repos/..."
gh api "repos/$OWNER/$SLUG/pages" --silent 2>/dev/null || run gh api -X POST "repos/$OWNER/$SLUG/pages" -f 'source[branch]=main' -f 'source[path]=/' --silent
run gh repo edit "$OWNER/$SLUG" --homepage "https://$OWNER.github.io/$SLUG/"
echo
echo "new_talk: done → https://github.com/$OWNER/$SLUG  ·  Pages: https://$OWNER.github.io/$SLUG/ (first build takes ~1 min)"
echo "Follow-ups: KB projects/<talk>/overview.md with repo: link · social card (publish-repo skill) · talk-specific favicon."
