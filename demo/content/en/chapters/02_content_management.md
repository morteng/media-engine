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
---

# Content Management

Media Engine uses a file-based content management system. Documents are Markdown files with YAML frontmatter for metadata.

## Document Structure

Every document follows this structure:

```markdown
---
title: "Document Title"
version: "1.0.0"
status: "draft"
last_modified: "2025-12-16"
---

# Heading

Your content is written here in standard Markdown format.
```

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Document title |
| `version` | Yes | Semantic version (major.minor.patch) |
| `status` | Yes | draft, review, or final |
| `last_modified` | Yes | Date of last edit |
| `freshness_days` | No | Days before content is considered stale |
| `depends_on` | No | List of documents this depends on |
| `tags` | No | List of tags for categorization |

## Staleness Tracking

Documents become stale when:
- They haven't been modified in `freshness_days`
- A document they depend on has been updated

Check stale content with:

```bash
media-engine stale
```

## Directory Structure

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
