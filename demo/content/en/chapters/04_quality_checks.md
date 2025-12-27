---
title: "Quality Checks"
version: "1.1.0"
status: "final"
last_modified: "2025-12-23"
freshness_days: 60
depends_on:
  - "chapters/02_content_management"
tags:
  - quality
  - validation
  - placeholders

# Hierarchy metadata
doc_type: "operations"
lifecycle: "living"
parent_document: "chapters/01_introduction.md"
sequence_order: 4
hierarchy_level: 1

# Derives from content management (implements quality aspects)
derived_from:
  - path: "chapters/02_content_management.md"
    version: "1.0.0"
    relationship: "implements"

# References anchors from introduction
anchor_refs:
  - source: "chapters/01_introduction.md"
    anchor: "project_name"
---

# Quality Checks

Media Engine includes a comprehensive quality assurance system that scans content for common issues before publication.

## Overview

The quality checking system detects:

- **Placeholder markers**: TO​DO, TB​D, FIX​ME, and template variables
- **Encoding issues**: Mojibake and character corruption in Norwegian text
- **Terminology inconsistencies**: Terms that should use preferred alternatives
- **Empty sections**: Headers with no content

## Running Quality Checks

Use the CLI to run quality checks on your project:

```bash
# Run all quality checks
media-engine quality

# Output results as JSON
media-engine quality --json
```

Or use the Python API:

```python
from media_engine import run_quality_checks, find_project

project = find_project()
report = run_quality_checks(project)

print(f"Files checked: {report.files_checked}")
print(f"Errors: {report.error_count}")
print(f"Warnings: {report.warning_count}")

for issue in report.issues:
    print(f"{issue.severity}: {issue.file_path.name}:{issue.line} - {issue.message}")
```

## Placeholder Detection

The system detects common placeholder patterns:

| Pattern | Description |
|---------|-------------|
| `TO​DO` | Task markers |
| `TB​D` | To be determined |
| `FIX​ME` | Issues to fix |
| `X​XX` | Attention needed |
| `[place​holder]` | Content placeholder |
| `${...}` | Template variables |
| `{{...}}` | Template variables |

These are flagged as warnings since they indicate incomplete content.

## Encoding Validation

For Norwegian content, the system detects encoding corruption (mojibake):

| Corrupted | Correct | Issue |
|-----------|---------|-------|
| `Ã¦` | `æ` | UTF-8 read as Latin-1 |
| `Ã¸` | `ø` | UTF-8 read as Latin-1 |
| `Ã¥` | `å` | UTF-8 read as Latin-1 |

It also catches common workarounds like `aa` instead of `å`.

## Terminology Consistency

Create a `glossary.yaml` file to enforce consistent terminology:

```yaml
terms:
  - preferred: "API endpoint"
    avoid:
      - "api endpoint"
      - "API Endpoint"
      - "endpoint"

  - preferred: "machine learning"
    avoid:
      - "ML"
      - "Machine Learning"
```

The quality checker will flag uses of non-preferred terms.

## Empty Section Detection

Headers followed by no content trigger warnings:

```markdown
## This Section Has Content

Here is some content.

## This Section Is Empty

## Next Section

More content here.
```

The "This Section Is Empty" header would be flagged.

## Issue Severity Levels

Issues are categorized by severity:

- **Error**: Must be fixed before publishing (encoding corruption)
- **Warning**: Should be addressed (placeholders, empty sections)
- **Info**: Suggestions for improvement (terminology)

## Quality Report

The `QualityReport` object provides:

```python
report = run_quality_checks(project)

# Summary
report.passed          # True if no errors
report.files_checked   # Number of files scanned
report.error_count     # Critical issues
report.warning_count   # Non-critical issues

# Details
for issue in report.issues:
    issue.type       # placeholder, encoding, terminology, empty
    issue.severity   # error, warning, info
    issue.file_path  # Path to file
    issue.line       # Line number
    issue.message    # Human-readable description
    issue.context    # Surrounding text
```

## Dashboard Quality Views

The web dashboard provides comprehensive quality analysis across multiple specialized tabs.

### Quality Tab Structure

| Tab | Analysis |
|-----|----------|
| Quality | Overview of issues, coverage, and health score |
| Semantic | Semantic similarity, duplicate detection, terminology drift |
| Knowledge | Knowledge graph, concept mapping, prerequisite tracking |
| Readability | Flesch-Kincaid, Gunning Fog, LIX (Norwegian) scoring |
| Freshness | Content age tracking and staleness prediction |
| Code Sync | Code-documentation synchronization status |
| Advanced | Audience analysis, style checking, engagement metrics |
| Activity | Recent changes, review queue, audit log |

### Using the Dashboard

```bash
# Launch dashboard
media-engine dashboard

# Navigate to /quality for quality analysis
```

The Quality page displays:
- Overall health score (0-100)
- Issue counts by severity
- Sub-tab navigation for specialized analysis
- Filtering by document, language, and severity

### AI-Assisted Review

Select text in any document preview to:
1. Add comments for AI review
2. Queue issues for automated analysis
3. Track annotation history

## Integration with CI/CD

Quality checks return a non-zero exit code when errors are found:

```bash
# In CI pipeline
media-engine quality || exit 1
```

Use the `--json` flag for machine-readable output that can be parsed by other tools.
