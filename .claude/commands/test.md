---
name: test
description: Run tests with coverage reporting (Python, Dashboard, E2E)
---

# Test Command

Run the Media Engine test suite across Python backend, React dashboard, and E2E tests.

## Usage

```bash
# Run all Python tests
/test

# Run with coverage
/test coverage

# Run specific test type
/test python        # Python tests only
/test dashboard     # Dashboard unit tests only
/test e2e           # E2E Playwright tests only

# Run specific module
/test core
/test mcp
/test insights
```

---

## Python Tests

```bash
# Quick test run
uv run pytest -x -q

# Full suite with coverage
uv run pytest --cov=media_engine --cov-report=term-missing

# Specific module
uv run pytest python/tests/test_core.py -v
uv run pytest python/tests/test_mcp_tools.py -v
uv run pytest python/tests/test_insights.py -v

# HTML coverage report
uv run pytest --cov=media_engine --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Dashboard Unit Tests

```bash
cd dashboard

# Interactive watch mode
npm run test

# Single run
npm run test:run

# With coverage
npm run test:coverage
```

---

## E2E Tests (Playwright)

```bash
cd dashboard

# Run all E2E tests
npm run test:e2e

# Interactive UI mode (recommended for debugging)
npm run test:e2e:ui

# Watch tests in browser
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test dashboard.spec.ts
npx playwright test navigation.spec.ts

# Run by grep pattern
npx playwright test -g "header"
npx playwright test -g "navigation"

# List all available tests
npx playwright test --list
```

---

## Pre-Release Validation

```bash
# Fail if coverage below 80%
uv run pytest --cov=media_engine --cov-fail-under=80

# Run dashboard tests
cd dashboard && npm run test:run

# Run E2E tests
npm run test:e2e
```

---

## Linting

```bash
# Python - check for issues
uv run ruff check python/

# Python - auto-fix issues
uv run ruff check --fix python/

# Dashboard
cd dashboard && npm run lint
```

---

## Test Structure

### Python Tests (19 files)
```
python/tests/
├── test_core.py          # Core module
├── test_cms.py           # CMS/documents
├── test_mcp_tools.py     # MCP tools (37 tests)
├── test_insights.py      # Insights (42 tests)
├── test_web_*.py         # Web API tests
└── ...
```

### Dashboard Unit Tests (13 files)
```
dashboard/src/
├── components/**/*.test.tsx
├── pages/*.test.tsx
└── contexts/*.test.tsx
```

### E2E Tests (5 files, 44 tests)
```
dashboard/e2e/
├── dashboard.spec.ts     # 8 tests
├── content.spec.ts       # 6 tests
├── quality.spec.ts       # 13 tests
├── build.spec.ts         # 7 tests
└── navigation.spec.ts    # 10 tests
```

---

## Output Template

```markdown
## Test Results

### Python
| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | XXX | - |
| Passed | XXX | PASS |
| Failed | X | PASS/FAIL |
| Coverage | XX% | PASS/FAIL |

### Dashboard Unit
| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | XX | - |
| Passed | XX | PASS/FAIL |

### E2E (Playwright)
| Metric | Value | Status |
|--------|-------|--------|
| Total Tests | 44 | - |
| Passed | XX | - |
| Failed | X | PASS/FAIL |

### Coverage by Module
| Module | Coverage |
|--------|----------|
| core/ | XX% |
| mcp/tools/ | XX% |
| insights/ | XX% |

### Next Steps
- If tests pass: Proceed with security check
- If tests fail: Fix failures and re-run
```

---

## Related Commands

- `/quality-check` - Full quality pipeline
- `/release-prep` - Release preparation
