# AGENTS.md - AI Agent Instructions for Media Engine

This file provides instructions for AI agents working with media-engine projects.
Compatible with Claude Code, Cursor, Devin, GitHub Copilot, and other agent frameworks.

## Project Overview

Media Engine is an agent-based media production framework for automated content generation.
It manages documentation, presentations, spreadsheets, videos, and translations with
full version tracking, quality checks, and provenance verification.

## Available Tools

### Via MCP Server (Recommended)
If connected via MCP, use these tools directly:

| Tool | Purpose |
|------|---------|
| `project_status` | Get project health and content counts |
| `translation_status` | Check translation sync status |
| `outdated_translations` | List translations needing updates |
| `quality_check` | Run quality checks |
| `validate_project` | Validate against schema |
| `search_content` | Full-text search |
| `read_document` | Read document content |
| `build_html` | Build HTML from markdown |
| `build_pptx` | Build PowerPoint from YAML |

### Via CLI
```bash
media-engine status              # Project status
media-engine quality             # Run quality checks
media-engine validate            # Schema validation
media-engine translation status  # Translation sync
media-engine build html          # Build HTML output
media-engine dashboard           # Launch web dashboard
```

## Key Workflows

### 1. Before Making Changes
Always check project health first:
```
1. Run project_status or `media-engine status`
2. Check for quality issues with quality_check
3. Review translation status if multilingual
```

### 2. Editing Documents
Documents use frontmatter for metadata:
```yaml
---
title: "Document Title"
version: "1.0.0"
status: "draft"  # draft, in_review, approved, published
last_modified: "2025-12-16"
---
```

After editing:
1. Increment version appropriately (patch/minor/major)
2. Update `last_modified` date
3. If translation exists, it becomes outdated

### 3. Translation Workflow
Translations track their source:
```yaml
---
language: "no"
source_document: "en/chapters/01_intro.md"
source_version: "1.0.0"
---
```

When source changes:
1. Translation is marked outdated
2. Update translation content
3. Update `source_version` to match current source
4. Use `mark_translation_synced` tool or `media-engine translation sync`

### 4. Quality Standards
All content must pass:
- No placeholder text (TODO, TBD, FIXME, [PLACEHOLDER])
- Valid encoding (UTF-8)
- No stale content (modified within freshness_days)
- Valid frontmatter schema
- Working internal links

### 5. Approval Workflow
Document states: draft → in_review → approved → published

Request approval:
```python
from media_engine.provenance import ProvenanceTracker
tracker = ProvenanceTracker(project)
tracker.request_approval(doc_path, "requester_name")
```

## Content Structure

```
{project}/
├── project.yaml          # Project configuration
├── theme.yaml            # Design tokens
├── schema.yaml           # Frontmatter validation
├── content/
│   ├── {lang}/
│   │   ├── chapters/     # Markdown documentation
│   │   ├── scripts/      # Video scripts (YAML)
│   │   ├── slides/       # Presentation definitions
│   │   ├── data/         # Spreadsheet data
│   │   └── diagrams/     # Diagram definitions
├── assets/               # Images, logos, fonts
└── output/               # Generated files
```

## Language Configuration

Languages are configured in project.yaml:
```yaml
localization:
  source_language: "en"
  languages:
    "en":
      name: "English"
    "no":  # Must quote - YAML interprets bare 'no' as false
      name: "Norwegian"
```

## Provenance & Claims

For verified documentation, track claims:
```yaml
claims:
  - claim: "50% performance improvement"
    source: "benchmark_report_2024.pdf"
    verified_by: "john@example.com"
    verified_date: "2024-12-01"
    expires: "2025-12-01"
```

## Dependencies

Documents can declare dependencies:
```yaml
depends_on:
  - "chapters/02_setup.md"
  - "chapters/03_config.md"
```

When dependencies change, dependent documents need review.

## Best Practices for Agents

1. **Always verify before building**: Run quality_check before any build operation
2. **Preserve metadata**: When editing, keep existing frontmatter fields
3. **Use semantic versioning**: major.minor.patch for document versions
4. **Update translations**: After source changes, flag translations as needing update
5. **Log actions**: Use audit logging for important operations
6. **Check dependencies**: Before major changes, check what depends on the file
7. **Validate schemas**: Ensure frontmatter matches schema.yaml

## Error Handling

Common issues and solutions:

| Error | Solution |
|-------|----------|
| "Language 'no' not configured" | Quote "no" in YAML - it's parsed as boolean |
| "Document not found" | Check path is relative to content_dir |
| "Translation outdated" | Update source_version after translating |
| "Quality check failed" | Fix placeholders, encoding, or stale content |

## MCP Configuration

For Claude Desktop or other MCP clients:
```json
{
  "mcpServers": {
    "media-engine": {
      "command": "media-engine-mcp",
      "args": ["-p", "/path/to/project"]
    }
  }
}
```

## Web Dashboard

Launch for visual overview:
```bash
media-engine dashboard
# Opens http://localhost:8080
```

Features:
- Translation matrix view
- Quality issue tracking
- Build controls
- Real-time collaboration

## Contact

- Issues: https://github.com/anthropics/media-engine/issues
- Documentation: See demo/ folder for examples
