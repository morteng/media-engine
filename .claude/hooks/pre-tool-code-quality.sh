#!/bin/bash
# Pre-tool code quality check - validates before making changes

# Get the file path from tool input
if [ -t 0 ]; then
    exit 0  # No stdin, allow
fi

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

[ -z "$FILE_PATH" ] && exit 0

# For new files (Write tool), just allow
if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# Check if file is writable
if [ ! -w "$FILE_PATH" ]; then
    echo "❌ File is not writable: $FILE_PATH"
    exit 1
fi

# Warn about editing test files without running tests
if [[ "$FILE_PATH" == *test*.py ]] || [[ "$FILE_PATH" == *_test.py ]]; then
    echo "ℹ️  Editing test file - remember to run tests after"
fi

# Warn about editing config files
if [[ "$FILE_PATH" == *.yaml ]] || [[ "$FILE_PATH" == *.yml ]] || [[ "$FILE_PATH" == *.json ]]; then
    if [[ "$FILE_PATH" == *config* ]] || [[ "$FILE_PATH" == *settings* ]]; then
        echo "ℹ️  Editing config file - changes may affect runtime behavior"
    fi
fi

exit 0
