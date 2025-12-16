#!/bin/bash
################################################################################
# Pre-Release Check - Media Engine
#
# Comprehensive checks before any release
# Runs all quality gates: content, tests, security
#
# Usage: .claude/hooks/pre-release-check.sh
################################################################################

set -euo pipefail

# Change to git root directory
GIT_ROOT=$(git rev-parse --show-toplevel)
cd "$GIT_ROOT" || exit 1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
declare -A results

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   MEDIA ENGINE PRE-RELEASE CHECK${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# -----------------------------------------------------------------------------
# Gate 1: Linting
# -----------------------------------------------------------------------------
echo -e "${BLUE}[1/5] Linting...${NC}"
if uv run ruff check python/ >/dev/null 2>&1; then
  echo -e "  ${GREEN}PASS${NC} - No linting errors"
  results["linting"]="PASS"
else
  echo -e "  ${RED}FAIL${NC} - Linting errors found"
  uv run ruff check python/
  results["linting"]="FAIL"
fi

# -----------------------------------------------------------------------------
# Gate 2: Tests with Coverage
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/5] Tests with coverage...${NC}"
if uv run pytest --cov=media_engine --cov-fail-under=80 -q >/dev/null 2>&1; then
  COVERAGE=$(uv run pytest --cov=media_engine --cov-report=term 2>/dev/null | grep "TOTAL" | awk '{print $NF}' || echo "??%")
  echo -e "  ${GREEN}PASS${NC} - All tests passing, coverage: $COVERAGE"
  results["tests"]="PASS"
else
  echo -e "  ${RED}FAIL${NC} - Tests failed or coverage below 80%"
  results["tests"]="FAIL"
fi

# -----------------------------------------------------------------------------
# Gate 3: Content Quality (if demo project exists)
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/5] Content quality...${NC}"
if [ -d "demo" ]; then
  cd demo
  if media-engine quality >/dev/null 2>&1; then
    echo -e "  ${GREEN}PASS${NC} - Content quality checks passed"
    results["content"]="PASS"
  else
    echo -e "  ${YELLOW}WARN${NC} - Content quality issues found"
    results["content"]="WARN"
  fi
  cd ..
else
  echo -e "  ${YELLOW}SKIP${NC} - No demo project found"
  results["content"]="SKIP"
fi

# -----------------------------------------------------------------------------
# Gate 4: Translation Status (if demo project exists)
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/5] Translation status...${NC}"
if [ -d "demo" ]; then
  cd demo
  OUTDATED=$(media-engine translation outdated 2>/dev/null | grep -c "outdated" || echo "0")
  if [ "$OUTDATED" = "0" ]; then
    echo -e "  ${GREEN}PASS${NC} - All translations current"
    results["translations"]="PASS"
  else
    echo -e "  ${YELLOW}WARN${NC} - $OUTDATED outdated translations"
    results["translations"]="WARN"
  fi
  cd ..
else
  echo -e "  ${YELLOW}SKIP${NC} - No demo project found"
  results["translations"]="SKIP"
fi

# -----------------------------------------------------------------------------
# Gate 5: Security Scan (if demo project exists)
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[5/5] Security scan...${NC}"
if [ -d "demo" ]; then
  cd demo
  if media-engine security >/dev/null 2>&1; then
    echo -e "  ${GREEN}PASS${NC} - No security issues"
    results["security"]="PASS"
  else
    echo -e "  ${RED}FAIL${NC} - Security issues found"
    results["security"]="FAIL"
  fi
  cd ..
else
  echo -e "  ${YELLOW}SKIP${NC} - No demo project found"
  results["security"]="SKIP"
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Determine overall status
overall="GO"
for gate in "${!results[@]}"; do
  status="${results[$gate]}"
  case $status in
    PASS) echo -e "  $gate: ${GREEN}$status${NC}" ;;
    WARN) echo -e "  $gate: ${YELLOW}$status${NC}" ;;
    FAIL) echo -e "  $gate: ${RED}$status${NC}"; overall="NO-GO" ;;
    SKIP) echo -e "  $gate: ${YELLOW}$status${NC}" ;;
  esac
done

echo ""
if [ "$overall" = "GO" ]; then
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}   DECISION: GO${NC}"
  echo -e "${GREEN}   Ready for release${NC}"
  echo -e "${GREEN}========================================${NC}"
  exit 0
else
  echo -e "${RED}========================================${NC}"
  echo -e "${RED}   DECISION: NO-GO${NC}"
  echo -e "${RED}   Fix blocking issues before release${NC}"
  echo -e "${RED}========================================${NC}"
  exit 1
fi
