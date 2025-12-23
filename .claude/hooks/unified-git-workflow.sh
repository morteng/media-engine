#!/bin/bash
# Unified git workflow - tracks changes for better commit awareness

# Get the file that was edited
FILE_PATH="${CLAUDE_FILE_PATH:-}"

if [ -z "$FILE_PATH" ]; then
    if [ -t 0 ]; then
        exit 0
    fi
    INPUT=$(cat)
    FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
fi

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# Check if we're in a git repo
if ! git rev-parse --git-dir &> /dev/null; then
    exit 0
fi

# Get relative path from git root
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
REL_PATH="${FILE_PATH#$GIT_ROOT/}"

# Track modified files in a session file
SESSION_FILE="${GIT_ROOT}/.claude/.session-changes"
mkdir -p "$(dirname "$SESSION_FILE")"

# Add to session tracking (deduped)
if [ -f "$SESSION_FILE" ]; then
    if ! grep -qxF "$REL_PATH" "$SESSION_FILE" 2>/dev/null; then
        echo "$REL_PATH" >> "$SESSION_FILE"
    fi
else
    echo "$REL_PATH" > "$SESSION_FILE"
fi

# Count uncommitted changes periodically
CHANGE_COUNT=$(wc -l < "$SESSION_FILE" 2>/dev/null | tr -d ' ')
if [ "$CHANGE_COUNT" -ge 10 ]; then
    echo "📝 $CHANGE_COUNT files modified this session - consider committing"
fi

exit 0
