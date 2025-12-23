#!/bin/bash
# Post-tool health report - runs quick checks after file edits

# Get the file that was edited from environment or stdin
FILE_PATH="${CLAUDE_FILE_PATH:-}"

# If no file path, try to read from tool input
if [ -z "$FILE_PATH" ]; then
    # Read tool input JSON if available
    if [ -t 0 ]; then
        exit 0  # No input, skip
    fi
    INPUT=$(cat)
    FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
fi

# Skip if no file or file doesn't exist
[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# Only check Python files
if [[ "$FILE_PATH" == *.py ]]; then
    # Quick ruff check (non-blocking)
    if command -v ruff &> /dev/null; then
        ERRORS=$(ruff check "$FILE_PATH" --select=E,F --quiet 2>/dev/null | head -5)
        if [ -n "$ERRORS" ]; then
            echo "⚠️  Lint issues in $(basename "$FILE_PATH"):"
            echo "$ERRORS"
        fi
    fi
fi

exit 0
