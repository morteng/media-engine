---
name: project-manage
description: GitHub project management operations for Media Engine
version: 1.0.0
last_updated: 2025-12-27
---

# Project Management - GitHub Operations

Manage GitHub issues, milestones, releases, and project coordination.

## What This Command Does

```
+------------------------------------------------------------------+
|                   PROJECT MANAGEMENT                              |
|                                                                   |
|   Issues      -> Triage, label, assign, track                     |
|   Milestones  -> Create, track progress, close                    |
|   Releases    -> Prepare, validate, coordinate                    |
|   PRs         -> Review status, merge coordination                |
|   Boards      -> Project board updates                            |
+------------------------------------------------------------------+
```

## Usage

```bash
# General project management
/project-manage

# Specific operations
/project-manage issues          # Issue triage and status
/project-manage milestone       # Milestone management
/project-manage release         # Release preparation
/project-manage pr              # PR management
```

## Quick Operations

### Issue Management

```bash
# View open issues
gh issue list --state open

# Triage new issues (add labels, milestones)
gh issue edit <number> --add-label "bug,priority:high" --milestone "v1.1.0"

# Close completed issues
gh issue close <number> --comment "Fixed in PR #XYZ"
```

### Milestone Management

```bash
# Check milestone progress
gh api repos/{owner}/{repo}/milestones \
  --jq '.[] | select(.title == "v1.1.0") | {title, open_issues, closed_issues}'

# Create new milestone
gh api repos/{owner}/{repo}/milestones -X POST \
  -f title="v1.2.0" -f description="Next release"
```

### Release Preparation

```bash
# Check Release Please PR
gh pr list --label "autorelease: pending"

# View latest release
gh release view --latest

# Check if ready for release
/quality-check
```

### PR Management

```bash
# List open PRs
gh pr list --state open

# Check PR status
gh pr checks <number>

# List PRs awaiting review
gh pr list --search "review:required"
```

## Workflows

### Issue Triage Workflow

1. Review new issues: `gh issue list --state open --label ""` (unlabeled)
2. Classify: bug, enhancement, docs, question
3. Prioritize: critical, high, medium, low
4. Assign to milestone if applicable
5. Assign owner if clear

### Release Workflow

1. Verify milestone complete
2. Run `/quality-check` - all gates must pass
3. Review Release Please PR
4. Merge Release Please PR
5. Verify release created

### Hotfix Workflow

1. Create hotfix branch from main
2. Apply fix
3. Run quick quality check: `/quality-check quick`
4. Create PR and merge
5. Release Please auto-creates release PR

## Conventional Commits

All commits should follow conventional commit format for automatic changelog:

| Type | Use For | Version Bump |
|------|---------|--------------|
| `feat:` | New features | Minor |
| `fix:` | Bug fixes | Patch |
| `docs:` | Documentation | None |
| `refactor:` | Code refactoring | None |
| `test:` | Tests | None |
| `ci:` | CI/CD changes | None |
| `feat!:` or `BREAKING CHANGE` | Breaking changes | Major |

## Output Report Template

```markdown
## Project Status Report

**Date**: [timestamp]

### Issues
- Open: X
- Critical/High Priority: Y
- Unassigned: Z

### Current Milestone: v1.x.x
- Progress: X/Y issues (Z%)
- Due: YYYY-MM-DD

### Release Status
- Quality Gates: PASS/FAIL
- Release Please PR: #XXX (open/merged/none)
- Status: READY / NOT READY

### PRs Needing Attention
- #XXX - [title] (awaiting review)

### Recommended Actions
- [action items]
```

## Integration Points

### With Quality Guardians

```
/project-manage release
      |
      v
  Check milestone complete
      |
      v
  /quality-check  <- Runs all quality gates
      |
      v
  Merge Release PR
      |
      v
  Release created
```

### With Release Please

- Monitors `autorelease: pending` PRs
- Reviews auto-generated changelog
- Coordinates merge when quality gates pass

## Quick Reference

```bash
# Status overview
gh issue list --state open | head -20
gh pr list --state open
gh release list --limit 3

# Release readiness
gh pr list --label "autorelease: pending"
/quality-check

# Common triage
gh issue edit <num> --add-label "bug,priority:high"
gh issue edit <num> --milestone "v1.1.0"
```

## Related Commands

- `/quality-check` - Run all quality gates
- `/release-prep` - Full release preparation workflow
- `/test` - Run test suite
