---
name: release-prep
description: Full release preparation workflow with quality gates and version management
---

# Release Preparation - Complete Pre-Release Workflow

Comprehensive release preparation that runs all quality gates, validates milestones, and generates release artifacts.

## What This Command Does

```
+--------------------------------------------------------------------+
|                     RELEASE PREPARATION                             |
|                                                                     |
|  Phase 1: Validation                                                |
|  +-- Check milestone completion (GitHub)                            |
|  +-- Run /quality-check (all guardians)                             |
|  +-- Verify version in pyproject.toml                               |
|                                                                     |
|  Phase 2: Artifacts                                                 |
|  +-- Generate CHANGELOG entries                                     |
|  +-- Create release notes                                           |
|  +-- Update version badges                                          |
|                                                                     |
|  Phase 3: Final Checks                                              |
|  +-- Security scan                                                  |
|  +-- All tests pass                                                 |
|  +-- Documentation current                                          |
|                                                                     |
|  Phase 4: Decision                                                  |
|  +-- GO / NO-GO recommendation                                      |
+--------------------------------------------------------------------+
```

## Usage

```bash
# Standard release preparation
/release-prep

# For specific version
/release-prep v1.0.0

# Dry run (validation only)
/release-prep --dry-run
```

## Pre-Release Checklist

### Phase 1: Validation (Must Pass)

```markdown
## Milestone Validation
- [ ] All milestone issues are CLOSED
- [ ] No blocking issues remain open
- [ ] Version in pyproject.toml matches release

## Quality Gates (/quality-check)
- [ ] content-guardian: PASS
- [ ] test-guardian: PASS (coverage >80%)
- [ ] security-scanner: PASS (0 critical)

## Version Check
- [ ] pyproject.toml version correct
- [ ] No skipped versions
```

### Phase 2: Artifact Generation

```markdown
## CHANGELOG
- [ ] All features documented
- [ ] Bug fixes listed
- [ ] Breaking changes highlighted

## Release Notes
- [ ] User-friendly language
- [ ] Upgrade instructions if needed

## Documentation
- [ ] README updated
- [ ] API docs current
```

### Phase 3: Final Security

```markdown
## Security
- [ ] No secrets in content
- [ ] No PII exposed
- [ ] Dependencies secure

## Tests
- [ ] All tests passing
- [ ] Coverage >80%
```

## Execution Commands

```bash
# Phase 1: Milestone Check
gh api repos/{owner}/{repo}/milestones \
  --jq '.[] | select(.title | contains("v1.0")) | {title, open_issues, closed_issues}'

# Phase 1: Version Check
grep -E "^version" pyproject.toml

# Phase 1: Quality Check
/quality-check

# Phase 2: Analyze commits for changelog
git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~20)..HEAD

# Phase 3: Final validation
uv run pytest --cov=media_engine --cov-fail-under=80
media-engine security
```

## Release Decision Matrix

| Condition | Decision |
|-----------|----------|
| All gates pass, milestone complete | GO - Proceed |
| Quality gates fail | NO-GO - Fix first |
| Milestone incomplete | NO-GO - Close issues |
| Security issues found | NO-GO - Fix vulnerabilities |

## Output Report

```markdown
# Release Preparation Report

**Version**: vX.Y.Z
**Timestamp**: [DATE TIME]

## Phase 1: Validation

### Milestone Status
- **Milestone**: vX.Y.Z
- **Open Issues**: X
- **Closed Issues**: Y
- **Status**: Complete / Incomplete

### Quality Gate Results
| Gate | Status | Details |
|------|--------|---------|
| Content | PASS/FAIL | [summary] |
| Tests | PASS/FAIL | Coverage: XX% |
| Security | PASS/FAIL | Issues: X |

### Version Check
- pyproject.toml: X.Y.Z
- Expected: X.Y.Z

## Phase 2: Artifacts

### CHANGELOG Preview
## [X.Y.Z] - YYYY-MM-DD

### Added
- Feature 1
- Feature 2

### Fixed
- Bug fix 1

## Decision

**RELEASE STATUS**: GO / NO-GO

### Blocking Issues (if NO-GO)
- [Issue 1]

## Next Steps

If GO:
1. Create tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
2. Push tag: `git push origin vX.Y.Z`
3. Create GitHub release
4. Publish to PyPI (if applicable)

If NO-GO:
1. Fix blocking issues
2. Re-run `/release-prep`
```

## Version Management Rules

**NEVER VIOLATE:**

```markdown
- NO TAGS WITHOUT MILESTONE COMPLETION
- NO VERSION BUMPS WITHOUT QUALITY CHECK
- NO SKIPPING VERSIONS (0.1.0 -> 0.2.0 -> 1.0.0)
- NO RELEASES WITHOUT SECURITY SCAN
```

## Related Commands

- `/quality-check` - Run quality gates only
- `/test` - Run tests only
