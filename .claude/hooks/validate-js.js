// PostToolUse validator for index.html. Two checks:
//  1. JS syntax of every non-module inline <script> block (Function ctor parse).
//  2. Curly-quote HTML attribute delimiters anywhere in the file.
//
// The Edit tool sometimes silently converts ASCII " or ' to U+201C/D/18/19.
// JS parses the surrounding string fine, but the HTML attribute breaks at
// runtime (class isn't applied, etc.). The JS-only check misses this — hence
// check #2.
//
// Called by validate-js.sh with VALIDATE_FILE env var set.
const fs = require('fs');
const file = process.env.VALIDATE_FILE;
const content = fs.readFileSync(file, 'utf8');

const rx = /<script(?![^>]*type=["'](module|importmap))[^>]*>([\s\S]*?)<\/script>/g;
const scripts = [...content.matchAll(rx)];
let ok = true;

scripts.forEach((m, i) => {
  try { new Function(m[2]); }
  catch (e) {
    process.stderr.write(`Script block ${i}: ${e.message}\n`);
    ok = false;
  }
});

// Curly-quote HTML attribute delimiter check.
// Matches `<whitespace><attr-name>=<curly-quote>` — e.g. ` class="foo"`.
// One curly opener is enough to flag; the closer is whatever follows.
const curlyAttr = /\s[\w-]+=[“”‘’]/g;
for (const m of content.matchAll(curlyAttr)) {
  const idx = m.index;
  const line = content.slice(0, idx).split('\n').length;
  const ch = m[0][m[0].length - 1];
  const cp = 'U+' + ch.codePointAt(0).toString(16).toUpperCase().padStart(4, '0');
  const snippet = content.slice(idx, Math.min(idx + 90, content.length)).replace(/\n/g, ' ');
  process.stderr.write(`Line ${line}: HTML attribute delimited by curly quote (${cp}): ${snippet}\n`);
  ok = false;
}

process.exit(ok ? 0 : 1);
