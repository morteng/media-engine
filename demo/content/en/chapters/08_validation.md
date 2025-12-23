---
title: "Validation"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/02_content_management"
  - "chapters/04_quality_checks"
tags:
  - validation
  - schema
  - references

# Hierarchy metadata
doc_type: "operations"
lifecycle: "living"
parent_document: "chapters/04_quality_checks.md"
sequence_order: 8
hierarchy_level: 2

# Derives from quality checks (extends with schema validation)
derived_from:
  - path: "chapters/04_quality_checks.md"
    version: "1.0.0"
    relationship: "extends"
  - path: "chapters/02_content_management.md"
    version: "1.0.0"
    relationship: "implements"
---

# Validation

Media Engine provides schema validation for frontmatter and reference checking for links.

## Overview

The validation system checks:

- **Schema validation**: Frontmatter fields against JSON Schema
- **Reference validation**: Internal links and citations
- **Required fields**: Missing mandatory metadata
- **Value constraints**: Enums, patterns, and types

## Running Validation

Run validation checks using the CLI or Python API.

### CLI

```bash
# Full validation (schema + references)
media-engine validate

# Only check references
media-engine validate --refs-only

# Use custom schema
media-engine validate --schema custom_schema.yaml

# JSON output
media-engine validate --json
```

### Python API

```python
from media_engine import validate_project, find_project

project = find_project()
report = validate_project(project, schema_path=Path("schema.yaml"))

print(f"Files: {report.files_checked}")
print(f"Errors: {report.error_count}")
print(f"Warnings: {report.warning_count}")

for issue in report.issues:
    print(f"{issue.severity}: {issue.file_path.name}")
    print(f"  {issue.message}")
```

## Schema Definition

Schemas use JSON Schema format in YAML:

```yaml
# schema.yaml
type: object
required:
  - title
  - version
  - status
  - last_modified

properties:
  title:
    type: string
    minLength: 1

  version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"

  status:
    type: string
    enum:
      - draft
      - review
      - final
      - archived

  last_modified:
    type: string
    pattern: "^\\d{4}-\\d{2}-\\d{2}$"

  freshness_days:
    type: integer
    minimum: 1

  tags:
    type: array
    items:
      type: string

  depends_on:
    type: array
    items:
      type: string
```

## Default Schema

If no schema is provided, a default schema is used:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Document title |
| `version` | string | No | Semantic version |
| `status` | enum | No | draft, review, final, archived |
| `last_modified` | string | No | Date (YYYY-MM-DD) |
| `freshness_days` | integer | No | Days until stale |
| `tags` | array | No | List of tags |
| `depends_on` | array | No | Document dependencies |

## Reference Validation

The system checks:

1. **Internal links**: Markdown links to other documents resolve correctly
2. **Image references**: Image embeds reference files that exist
3. **Document dependencies**: `depends_on` entries are valid
4. **Citations**: Numbered references like `[1]` have matching entries

### Checking References

```python
from media_engine.validation import validate_references

errors = validate_references(project, console_output=True)
# Returns list of broken references
```

## Validation Report

```python
@dataclass
class ValidationIssue:
    type: str        # schema, reference, missing
    severity: str    # error, warning
    file_path: Path
    line: int        # 0 if not applicable
    message: str
    field: str       # For schema errors

@dataclass
class ValidationReport:
    issues: list[ValidationIssue]
    files_checked: int
    passed: bool

    @property
    def error_count(self) -> int
    @property
    def warning_count(self) -> int
```

## Schema Error Examples

```yaml
# Missing required field
ERROR: document.md - Missing required field 'title'

# Invalid type
ERROR: document.md - version: Expected string, got integer

# Invalid enum value
ERROR: document.md - status: Value 'wip' not in [draft, review, final]

# Pattern mismatch
ERROR: document.md - version: '1.0' does not match ^\d+\.\d+\.\d+$
```

## Reference Error Examples

```
ERROR: chapter.md:15 - Broken link: ../missing.md
ERROR: chapter.md:28 - Image not found: images/diagram.png
ERROR: chapter.md - depends_on 'chapters/nonexistent' not found
```

## CI/CD Integration

```bash
# Fail build on validation errors
media-engine validate || exit 1

# Parse JSON output
RESULT=$(media-engine validate --json)
ERRORS=$(echo $RESULT | jq '.error_count')
```

## Custom Validation

Extend validation with custom checks:

```python
from media_engine.validation import SchemaValidator

validator = SchemaValidator()
validator.load_schema_file(Path("my_schema.yaml"))

errors = validator.validate(
    frontmatter=doc.metadata,
    schema_name="my_schema",
    file_path=doc.path
)
```

## Translation Field Validation

For translated documents, validate translation metadata:

```yaml
# Additional fields for translations
properties:
  language:
    type: string
    pattern: "^[a-z]{2}(-[A-Z]{2})?$"

  source_document:
    type: string

  source_version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"
```

This ensures translations properly reference their source documents.
