---
title: "Content Analysis"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/04_quality_checks"
tags:
  - readability
  - links
  - gaps
  - analysis
---

# Content Analysis

Media Engine provides advanced analysis tools for content quality, readability, and completeness. These tools help you maintain high-quality documentation.

See [Quality Checks](04_quality_checks.md) for the related quality system.

## Link Validation

Check all internal and external links in your documentation:

### CLI

```bash
# Check all links
media-engine links

# Internal links only (faster)
media-engine links --internal-only

# JSON output
media-engine links --json
```

### Python API

```python
from media_engine.links import LinkChecker

checker = LinkChecker(project)
results = checker.check_all()

print(f"Total links: {results['total']}")
print(f"Broken: {results['broken']}")

for broken in results['broken_links']:
    print(f"  {broken.source_file}:{broken.source_line}")
    print(f"    -> {broken.url}")
```

### Features

The link checker provides comprehensive validation:

| Feature | Description |
|---------|-------------|
| Parallel checking | Validates external URLs quickly |
| Result caching | Avoids repeated checks (24h TTL) |
| Code block skipping | Ignores example links in code |
| Internal resolution | Validates relative paths |

## Readability Analysis

Measure how easy your content is to read.

### CLI

```bash
# Analyze all documents
media-engine readability

# Set target reading level
media-engine readability --target college

# JSON output
media-engine readability --json
```

### Metrics

The analyzer calculates multiple readability formulas:

| Metric | Range | Interpretation |
|--------|-------|----------------|
| Flesch Reading Ease | 0-100 | Higher = easier |
| Flesch-Kincaid Grade | 1-12+ | US grade level |
| Gunning Fog Index | 1-20+ | Years of education |
| SMOG Index | 1-20+ | Years of education |

### Target Levels

| Level | Flesch | Audience |
|-------|--------|----------|
| simple | 80-100 | General public |
| standard | 60-80 | High school |
| college | 30-60 | College educated |
| technical | 0-30 | Specialists |

### Python API

```python
from media_engine.readability import analyze_readability

results = analyze_readability(project)

for doc_path, scores in results.items():
    print(f"{doc_path}:")
    print(f"  Flesch: {scores['flesch_reading_ease']:.1f}")
    print(f"  Grade: {scores['flesch_kincaid_grade']:.1f}")
```

## Content Gap Analysis

Find missing or incomplete content.

### CLI

```bash
# Find all gaps
media-engine gaps

# Check for expected topics
media-engine gaps --topics "installation,configuration,api"

# JSON output
media-engine gaps --json
```

### Gap Types

The analyzer detects various content issues.

| Gap Type | Description |
|----------|-------------|
| Missing translations | Source documents without translations |
| Broken references | `depends_on` entries that don't exist |
| Orphan documents | Documents not linked from anywhere |
| Missing topics | Expected topics not covered |

### Python API

```python
from media_engine.gaps import GapAnalyzer

analyzer = GapAnalyzer(project)
report = analyzer.analyze()

print(f"Missing translations: {len(report.missing_translations)}")
print(f"Orphan documents: {len(report.orphans)}")

for gap in report.gaps:
    print(f"  {gap.type}: {gap.description}")
```

## Content Variables

Use dynamic variables in your documents.

### Syntax

```markdown
This document was published on {{date.today}}.
Project name: {{project.name}}
Version: {{project.version}}
```

### Available Namespaces

| Namespace | Variables |
|-----------|-----------|
| `project` | `name`, `version`, `description` |
| `date` | `today`, `year`, `month` |
| `env` | Environment variables |

### Custom Variables

Define custom variables in `variables.yaml`:

```yaml
company:
  name: "Acme Corp"
  website: "https://acme.com"

product:
  version: "2.0"
  release_date: "2025-01-15"
```

Use in documents:

```markdown
Welcome to {{company.name}}!
Download {{product.name}} v{{product.version}}.
```

### Python API

```python
from media_engine.variables import VariableResolver

resolver = VariableResolver(project)
content = resolver.resolve(document_content)
```

## Changelog Generation

Generate changelogs from git history and document changes.

### CLI

```bash
# Full changelog
media-engine changelog

# Last 30 days
media-engine changelog --days 30

# Write to file
media-engine changelog -o CHANGELOG.md
```

### Python API

```python
from media_engine.changelog import generate_changelog

changelog = generate_changelog(
    project,
    days=30,
    include_commits=True
)

print(changelog)
```

## Best Practices

1. **Run link checks regularly**: External links can break anytime
2. **Target appropriate readability**: Match your audience
3. **Track gaps systematically**: Review gap reports before releases
4. **Use variables for consistency**: Avoid hardcoded values
5. **Generate changelogs automatically**: Keep users informed

See [Validation](08_validation.md) for document schema validation and [Security](13_security.md) for security scanning.
