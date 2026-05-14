#!/bin/bash
# PostToolUse hook: validates inline JS in index.html after any Edit or Write.
# Blocks Claude from continuing if a syntax error is introduced.

INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except:
    print('')
" 2>/dev/null)

[[ "$FILE" != *"index.html" ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

OUTPUT=$(VALIDATE_FILE="$FILE" node "$(dirname "$0")/validate-js.js" 2>&1)
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo "JS syntax error introduced in index.html — fix before continuing:" >&2
    echo "$OUTPUT" >&2
    exit 2
fi
