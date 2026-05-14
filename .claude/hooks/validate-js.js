// PostToolUse validator: checks all non-module inline <script> blocks in index.html
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

process.exit(ok ? 0 : 1);
