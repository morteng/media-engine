#!/bin/bash
# Post-edit hook: Python syntax check + session tracking
# Silent unless there's a syntax error

# Get file path from input
[ -t 0 ] && exit 0
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# Python syntax check (only for .py files)
if [[ "$FILE_PATH" == *.py ]]; then
    if ! python3 -m py_compile "$FILE_PATH" 2>/dev/null; then
        echo "Syntax error in: $FILE_PATH"
        exit 1
    fi
fi

# Track session changes (silent)
if git rev-parse --git-dir &>/dev/null; then
    GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
    REL_PATH="${FILE_PATH#$GIT_ROOT/}"
    SESSION_FILE="${GIT_ROOT}/.claude/.session-changes"
    mkdir -p "$(dirname "$SESSION_FILE")" 2>/dev/null
    grep -qxF "$REL_PATH" "$SESSION_FILE" 2>/dev/null || echo "$REL_PATH" >> "$SESSION_FILE"
fi

exit 0
