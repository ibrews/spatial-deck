#!/usr/bin/env bash
# The steps lint has to fail on a deliberately broken module before its PASS on a real deck means anything.
# good.html must PASS the steps sweep; broken.html must FAIL on exactly its four broken slides, each for its own reason.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; TOOLS="$(dirname "$HERE")"; OUT="${OUT:-$(mktemp -d)}"; mkdir -p "$OUT"
python3 "$HERE/build_steps_fixture.py" || exit 2
fail=0
node "$TOOLS/sweep_deck.mjs" "file://$HERE/steps_fixture/good.html" "$OUT/good" 1280 720 good --steps > "$OUT/good.log" 2>&1
[ $? -eq 0 ] && echo "ok   good.html passes the steps sweep" || { echo "FAIL good.html should pass:"; grep -E 'STEPS|failedBecause' -A3 "$OUT/good.log" | head -20; fail=1; }
node "$TOOLS/sweep_deck.mjs" "file://$HERE/steps_fixture/broken.html" "$OUT/broken" 1280 720 broken --steps > "$OUT/broken.log" 2>&1
[ $? -ne 0 ] && echo "ok   broken.html fails the steps sweep" || { echo "FAIL broken.html should fail"; fail=1; }
check() { if grep -q "STEPS .*\"mod\":\"$1\".*$2" "$OUT/broken.log"; then echo "ok   $1: $2"; else echo "FAIL $1 should report: $2"; fail=1; fi; }
check test/dead 'dead step(s) 3'
check test/frame-liar 'frame reports 1 step(s), deck declares 2'
check test/sneaky 'declared 0 step(s), reachable 3'
check test/silent 'never reported ready'
n=$(grep -c '^STEPS ' "$OUT/broken.log"); [ "$n" -eq 4 ] && echo "ok   exactly 4 broken slides" || { echo "FAIL expected 4 broken slides, got $n"; grep '^STEPS ' "$OUT/broken.log"; fail=1; }
echo "logs + contact sheets: $OUT"; exit $fail
