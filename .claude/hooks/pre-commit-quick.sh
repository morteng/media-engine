#!/bin/bash
################################################################################
# Pre-Commit Quick Check - Media Engine
#
# Lightweight checks for every commit (fast execution)
# Checks: linting (ruff), formatting (ruff), quick tests
#
# For comprehensive checks before release, use /quality-check command
################################################################################

set -euo pipefail

# Change to git root directory
GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT" || exit 1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall success
all_checks_passed=true

echo "Running pre-commit checks..."

# 1. Ruff formatting check (fast)
echo -n "Checking formatting... "
if ! uv run ruff format --check python/ >/dev/null 2>&1; then
  echo -e "${YELLOW}fixing${NC}"
  uv run ruff format python/ --quiet
  git add -u  # Re-stage formatted files
  echo -e "${GREEN}Code formatted and re-staged${NC}"
else
  echo -e "${GREEN}ok${NC}"
fi

# 2. Ruff linting (fast)
echo -n "Checking linting... "
if ! uv run ruff check python/ >/dev/null 2>&1; then
  echo -e "${RED}failed${NC}"
  echo ""
  uv run ruff check python/
  echo ""
  echo -e "${YELLOW}Tip: Run 'uv run ruff check --fix python/' to auto-fix${NC}"
  all_checks_passed=false
else
  echo -e "${GREEN}ok${NC}"
fi

# 3. Quick tests (only if linting passed)
if [ "$all_checks_passed" = true ]; then
  echo -n "Running quick tests... "
  if ! uv run pytest -x -q --tb=no >/dev/null 2>&1; then
    echo -e "${RED}failed${NC}"
    echo ""
    uv run pytest -x --tb=short
    all_checks_passed=false
  else
    echo -e "${GREEN}ok${NC}"
  fi
fi

# Exit with error if checks failed
if [ "$all_checks_passed" = false ]; then
  echo ""
  echo -e "${RED}Pre-commit checks failed${NC}"
  exit 1
fi

echo -e "${GREEN}All pre-commit checks passed${NC}"
exit 0
