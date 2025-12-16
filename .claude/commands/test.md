---
name: test
description: Run tests with coverage reporting
---

# Test Command

Run the Media Engine test suite with coverage reporting.

## Usage

```bash
# Run all tests
/test

# Run with coverage
/test coverage

# Run specific module
/test core
/test cms
/test builders
```

## Quick Test Run

```bash
uv run pytest -x -q
```

## Full Test Suite with Coverage

```bash
uv run pytest --cov=media_engine --cov-report=term-missing
```

## Test Specific Module

```bash
# Core module
uv run pytest python/tests/test_core.py -v

# CMS module
uv run pytest python/tests/test_cms.py -v

# Builders
uv run pytest python/tests/test_builders.py -v
```

## Coverage Report

```bash
# Terminal report with missing lines
uv run pytest --cov=media_engine --cov-report=term-missing

# HTML report
uv run pytest --cov=media_engine --cov-report=html
# Open htmlcov/index.html in browser
```

## Pre-Release Test Validation

```bash
# Fail if coverage below 80%
uv run pytest --cov=media_engine --cov-fail-under=80
```

## Linting

```bash
# Check for issues
uv run ruff check python/

# Auto-fix issues
uv run ruff check --fix python/
```

## Output Template

```markdown
## Test Results

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | XXX | - |
| Passed | XXX | PASS |
| Failed | X | PASS/FAIL |
| Coverage | XX% | PASS/FAIL |

### Coverage by Module
| Module | Coverage |
|--------|----------|
| core/ | XX% |
| cms/ | XX% |
| builders/ | XX% |

### Next Steps
- If tests pass: Proceed with security check
- If tests fail: Fix failures and re-run
```

## Related Commands

- `/quality-check` - Full quality pipeline
- `/release-prep` - Release preparation
