---
name: quality-check
description: Run comprehensive quality checks across all guardians with unified GO/NO-GO report
---

# Quality Check - Full Guardian Orchestration

Run all quality gates in sequence and generate a unified GO/NO-GO report for release readiness.

## What This Command Does

```
+------------------------------------------------------------------+
|                    QUALITY GATE PIPELINE                          |
|                                                                   |
|   1. content-guardian   (quality, readability, translations)      |
|            |                                                      |
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
- [ ] Translations up to date

### Gate 2: Tests
- [ ] All tests passing
- [ ] Coverage >80%
- [ ] No linting errors (ruff)

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

echo "=== TRANSLATIONS ==="
media-engine translation outdated

echo "=== LINKS ==="
media-engine links --internal-only

# Step 2: Tests
echo "=== LINTING ==="
uv run ruff check python/

echo "=== TESTS ==="
uv run pytest --cov=media_engine --cov-fail-under=80

# Step 3: Security
echo "=== SECURITY ==="
media-engine security
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
| Tests | PASS/FAIL | Coverage: XX% |
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
