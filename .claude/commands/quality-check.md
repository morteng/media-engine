---
name: quality-check
description: Run comprehensive quality checks across all guardians with unified GO/NO-GO report
version: 2.0.0
last_updated: 2025-12-23
---

# Quality Check - Full Guardian Orchestration

Run all quality gates in sequence and generate a unified GO/NO-GO report for release readiness.

## What This Command Does

```
+------------------------------------------------------------------+
|                    QUALITY GATE PIPELINE                          |
|                                                                   |
|   1. content-guardian   (quality, readability, translations)      |
|            |            + hash-based change detection             |
|   2. test-guardian      (coverage >80%, all tests pass)           |
|            |                                                      |
|   3. security-scanner   (secrets, PII detection)                  |
|            |                                                      |
|            v                                                      |
|               -> UNIFIED GO/NO-GO REPORT <-                       |
+------------------------------------------------------------------+
```

## Usage

```bash
# Full quality check
/quality-check

# Quick mode (tests + security only)
/quality-check quick
```

## Quality Gates (Must Pass)

### Gate 1: Content Quality
- [ ] Quality checks passing (media-engine quality)
- [ ] Readability scores acceptable (Flesch >50)
- [ ] No broken links
- [ ] Translations up to date (hash-based detection)
- [ ] All translations using hash tracking mode

### Gate 2: Tests
- [ ] Python tests passing (pytest)
- [ ] Python coverage >80%
- [ ] Dashboard unit tests passing (vitest)
- [ ] E2E tests passing (playwright)
- [ ] No linting errors (ruff, eslint)

### Gate 3: Security
- [ ] No secrets detected
- [ ] No PII in content
- [ ] No exposed credentials

## Execution Sequence

Run these checks in order:

```bash
# Step 1: Content Quality
echo "=== CONTENT QUALITY ==="
cd demo && media-engine quality

echo "=== TRANSLATION STATUS (Hash-Based) ==="
media-engine translation status
# Check tracking_stats in output - all should be hash_tracked

echo "=== OUTDATED TRANSLATIONS ==="
media-engine translation outdated
# Shows content_changed: true for automatic detection

echo "=== LINKS ==="
media-engine links --internal-only

# Step 2: Tests
echo "=== PYTHON LINTING ==="
uv run ruff check python/

echo "=== PYTHON TESTS ==="
uv run pytest --cov=media_engine --cov-fail-under=80

echo "=== DASHBOARD LINTING ==="
cd dashboard && npm run lint

echo "=== DASHBOARD UNIT TESTS ==="
npm run test:run

echo "=== E2E TESTS ==="
npm run test:e2e

# Step 3: Security
echo "=== SECURITY ==="
media-engine security
```

## Translation Tracking Setup

If translations are using version-based tracking (legacy), upgrade to hash-based:

```bash
# Check current tracking mode
media-engine translation status --json | jq '.tracking_stats'

# Enable hash-based tracking for all current translations
# MCP tool: sync_all_translations(dry_run=True) to preview
# MCP tool: sync_all_translations() to execute

# After sync, any source content change is automatically detected
```

## Output Report Template

```markdown
# Quality Check Report

**Timestamp**: [DATE TIME]
**Project**: media-engine

## Gate Results

| Gate | Status | Details |
|------|--------|---------|
| Content Quality | PASS/FAIL | [summary] |
| Translations | PASS/WARN | X outdated |
| Python Tests | PASS/FAIL | Coverage: XX% |
| Dashboard Tests | PASS/FAIL | XX passed |
| E2E Tests | PASS/FAIL | XX/44 passed |
| Linting | PASS/FAIL | X errors |
| Security | PASS/FAIL | X issues |

## Overall Decision

**STATUS**: GO / NO-GO

### Blocking Issues (if NO-GO)
- [List of blocking issues]

### Warnings (non-blocking)
- [List of warnings]

## Next Steps

If GO:
- Proceed with `/release-prep`

If NO-GO:
- Fix blocking issues
- Re-run `/quality-check`
```

## Quick Mode

Skip content checks for faster iteration:

```bash
/quality-check quick
```

Gates in quick mode:
1. test-guardian (essential)
2. security-scanner (essential)
3. ~~content-guardian~~ (skipped)

## Related Commands

- `/test` - Run tests only
- `/release-prep` - Full release preparation
