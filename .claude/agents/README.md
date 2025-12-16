---
id: agents-readme
title: "Media Engine Agent Architecture"
version: "1.0.0"
created: 2025-12-16
last_updated: 2025-12-16
---

# Media Engine Agent Architecture

**Status**: Active

---

## Overview

Media Engine uses a **Guardian Pattern architecture** where specialized agents maintain project health, content quality, and release readiness for documentation and media production workflows.

**Architecture Pattern**: Focused agents handle specific domains (content quality, testing, security) and coordinate through quality gates.

---

## Core Agents

| Agent | Domain | Purpose |
|-------|--------|---------|
| **[content-guardian](./content-guardian.md)** | Content Quality | Readability, gap analysis, quality checks |
| **[test-guardian](./test-guardian.md)** | Test Quality | Coverage, test execution, validation |
| **[security-scanner](./security-scanner.md)** | Security | Secrets detection, PII scanning |

---

## Quick Reference: Which Agent Do I Use?

| Task | Agent | Command |
|------|-------|---------|
| Check content quality | content-guardian | `use content-guardian` |
| Find readability issues | content-guardian | `use content-guardian for readability analysis` |
| Find missing content | content-guardian | `use content-guardian for gap analysis` |
| Run tests | test-guardian | `use test-guardian` |
| Check coverage | test-guardian | `use test-guardian for coverage analysis` |
| Scan for secrets | security-scanner | `use security-scanner` |
| Pre-release security check | security-scanner | `use security-scanner for release validation` |

---

## Slash Commands

These commands orchestrate agents and CLI tools:

| Command | Purpose |
|---------|---------|
| `/quality-check` | Run all quality gates |
| `/release-prep` | Full release preparation workflow |
| `/test` | Run tests with coverage |

---

## Usage Patterns

### Pattern 1: Development Workflow

```bash
# Working on content
# 1. Make changes
# 2. Check quality
"use content-guardian to validate content quality"

# 3. Run tests
"use test-guardian to run tests"

# 4. Commit
```

### Pattern 2: Pre-Release Validation

```bash
# Preparing for release
/quality-check              # Run all quality gates
/release-prep               # Full release workflow
```

### Pattern 3: Content Review

```bash
# Review content quality
"use content-guardian for readability analysis"
"use content-guardian to find content gaps"
"use content-guardian to check translation status"
```

---

## Quality Gates

**Pre-Release Requirements**:
- Content quality checks passing
- Test coverage >80%
- No security issues (secrets/PII)
- Translations up to date

---

## CLI Integration

These agents leverage the built-in media-engine CLI:

```bash
media-engine quality        # Content quality checks
media-engine readability    # Readability scoring
media-engine gaps           # Content gap analysis
media-engine security       # Security scanning
media-engine translation status  # Translation tracking
uv run pytest              # Test execution
uv run ruff check          # Linting
```

---

**Status**: Active
**Next Review**: 2026-01-16
