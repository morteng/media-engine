---
title: "Content Management"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/01_introduction"
tags:
  - content
  - cms

# Hierarchy metadata
doc_type: "implementation"
lifecycle: "living"
parent_document: "chapters/01_introduction.md"
sequence_order: 2
hierarchy_level: 1

# Derives from introduction
derived_from:
  - path: "chapters/01_introduction.md"
    version: "1.0.0"
    relationship: "implements"
---

# Content Management

Media Engine stores all content as Markdown files with YAML frontmatter. You organize documents in a simple folder structure and track changes through version metadata.

## Document Structure

Write every document with this structure:

```markdown
---
title: "Document Title"
version: "1.0.0"
status: "draft"
last_modified: "2025-12-16"
---

# Heading

Write your content here in standard Markdown.
```

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Document title |
| `version` | Yes | Semantic version (major.minor.patch) |
| `status` | Yes | draft, review, or final |
| `last_modified` | Yes | Date of last edit |
| `freshness_days` | No | Days before the system marks content stale |
| `depends_on` | No | List of documents this one requires |
| `tags` | No | List of tags for categorization |

See [Validation](08_validation.md) for details on how Media Engine checks these fields.

## Staleness Tracking

Media Engine marks documents as stale when:
- You haven't modified them within `freshness_days`
- You updated a document they depend on

Check stale content:

```bash
media-engine stale
```

See [Quality Checks](04_quality_checks.md) for more freshness monitoring options.

## Directory Structure

Organize your content by language and type:

```
content/
├── en/                    # English content
│   ├── chapters/          # Document chapters
│   │   ├── 01_intro.md
│   │   └── 02_features.md
│   └── scripts/           # Video scripts
│       └── demo.yaml
└── no/                    # Norwegian translations
    ├── chapters/
    └── scripts/
```

See [Publishing](09_publishing.md) to learn how Media Engine builds these files into outputs.
