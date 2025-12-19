---
title: "CLI Reference"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/01_introduction"
tags:
  - cli
  - reference
  - commands
---

# CLI Reference

Complete reference for the `media-engine` command line interface.

## Global Usage

```bash
media-engine <command> [options]
```

## Commands

Available commands for managing your Media Engine project.

### status

Show project status and dashboard.

```bash
media-engine status [view] [--lang LANG] [--json]
```

| Argument | Description |
|----------|-------------|
| `view` | Optional view: `docs`, `videos`, `quality`, `deliverables`, `tree`, `cache` |
| `--lang` | Filter by language code |
| `--json` | Output as JSON |

Examples:
```bash
media-engine status              # Full dashboard
media-engine status docs         # Document status only
media-engine status --json       # JSON output
```

### build

Build media outputs from sources.

```bash
media-engine build [--only FORMAT] [--force] [--lang LANG] [--json]
```

| Option | Description |
|--------|-------------|
| `--only` | Build specific formats (comma-separated): html, pdf, pptx, xlsx, diagrams, video |
| `--force` | Force rebuild (ignore cache) |
| `--lang` | Build specific languages (comma-separated) |
| `--json` | Output results as JSON |

Examples:
```bash
media-engine build               # Build all
media-engine build --only html   # HTML only
media-engine build --lang en,no  # Specific languages
media-engine build --force       # Ignore cache
```

### publish

Create complete deliverable package.

```bash
media-engine publish [-o DIR] [--zip] [options]
```

| Option | Description |
|--------|-------------|
| `-o`, `--output` | Output directory |
| `--zip` | Create ZIP archive |
| `--no-fonts` | Skip font bundling |
| `--no-diagrams` | Skip diagram copying |
| `--no-videos` | Skip video assets |
| `--no-index` | Skip navigation index |

Examples:
```bash
media-engine publish             # Default location
media-engine publish -o ./dist   # Custom directory
media-engine publish --zip       # With ZIP archive
```

### quality

Run quality checks on content.

```bash
media-engine quality [--json]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

Exit code: 0 if passed, 1 if errors found.

### stale

List stale content that needs updating.

```bash
media-engine stale [--json]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |

### search

Search project documents.

```bash
media-engine search QUERY [--limit N] [--rebuild] [--json]
```

| Option | Description |
|--------|-------------|
| `QUERY` | Search query (required) |
| `--limit` | Maximum results (default: 20) |
| `--rebuild` | Rebuild index before searching |
| `--json` | Output as JSON |

Examples:
```bash
media-engine search "authentication"
media-engine search "api" --limit 5
media-engine search "query" --rebuild
```

### index

Build or update search index.

```bash
media-engine index [-o PATH]
```

| Option | Description |
|--------|-------------|
| `-o`, `--output` | Output path for index file |

### validate

Validate project content against schema.

```bash
media-engine validate [--schema PATH] [--refs-only] [--json]
```

| Option | Description |
|--------|-------------|
| `--schema` | Path to custom schema file |
| `--refs-only` | Only check references |
| `--json` | Output as JSON |

Exit code: 0 if passed, 1 if errors found.

### pack

Generate audience-specific content packs.

```bash
media-engine pack TYPE [-o DIR] [--no-zip]
```

| Argument | Description |
|----------|-------------|
| `TYPE` | Pack type: `investor` or `pilot` |
| `-o`, `--output` | Output directory |
| `--no-zip` | Don't create ZIP archive |

Examples:
```bash
media-engine pack investor
media-engine pack pilot -o ./customer-materials
```

### cache

Manage build cache.

```bash
media-engine cache status
media-engine cache clear [--voiceover] [--builds]
```

Subcommands:
- `status`: Show cache status and size
- `clear`: Clear cached data

| Option | Description |
|--------|-------------|
| `--voiceover` | Clear voiceover cache only |
| `--builds` | Clear builds cache only |

### init

Initialize a new project.

```bash
media-engine init [DIRECTORY] [--name NAME]
```

| Argument | Description |
|----------|-------------|
| `DIRECTORY` | Project directory (default: current) |
| `--name` | Project name (default: directory name) |

Creates:
- `project.yaml` - Project configuration
- `theme.yaml` - Design system
- `content/en/chapters/` - Content directory
- Sample chapter

### release

Copy production videos to deliverables folder.

```bash
media-engine release [--json]
```

### dashboard

Launch web dashboard for project management.

```bash
media-engine dashboard [--port PORT]
```

| Option | Description |
|--------|-------------|
| `--port` | Port number (default: 8080) |

### translation

Translation tracking and management.

```bash
media-engine translation <subcommand> [--json]
```

Subcommands:
- `status`: Show all translation pairs
- `outdated`: Show outdated translations
- `missing`: Show missing translations
- `sync`: Mark translation as synced

### provenance

Provenance and approval workflow tracking.

```bash
media-engine provenance <subcommand> [--json]
```

Subcommands:
- `report`: Full provenance report
- `claims`: Claims needing verification
- `queue`: Documents awaiting review

### integrity

Asset and terminology integrity checking.

```bash
media-engine integrity <subcommand> [--json]
```

Subcommands:
- `record`: Record asset checksums
- `verify`: Verify no unauthorized changes

### freshness

Content freshness tracking.

```bash
media-engine freshness [--json]
```

Shows content freshness status and identifies stale documents.

### health

Show project health score.

```bash
media-engine health [--json]
```

Returns 0-100 health score with component breakdown.

### stats

Show project statistics.

```bash
media-engine stats [--json]
```

### incomplete

Find incomplete content markers.

```bash
media-engine incomplete [--json]
```

Detects TODO, TBD, FIXME, and other incomplete markers.

### consistency

Check status consistency across documents.

```bash
media-engine consistency [--json]
```

### parity

Translation parity matrix.

```bash
media-engine parity [--json]
```

Shows translation coverage across all language pairs.

### terms

Check terminology consistency.

```bash
media-engine terms [--json]
```

Validates consistent use of defined terminology.

### duplicates

Find duplicate content.

```bash
media-engine duplicates [--json]
```

### velocity

Content velocity metrics.

```bash
media-engine velocity [--json]
```

Shows production rate and trend analysis.

### graph

Knowledge graph and dependency visualization.

```bash
media-engine graph [--json]
```

### path

Reading paths through content.

```bash
media-engine path [--json]
```

### readability

Readability analysis.

```bash
media-engine readability [--target LEVEL] [--json]
```

| Option | Description |
|--------|-------------|
| `--target` | Target level: simple, standard, college, technical |

### gaps

Content gap analysis.

```bash
media-engine gaps [--topics TOPICS] [--json]
```

| Option | Description |
|--------|-------------|
| `--topics` | Expected topics (comma-separated) |

### links

Link validation.

```bash
media-engine links [--internal-only] [--json]
```

| Option | Description |
|--------|-------------|
| `--internal-only` | Skip external URL checking |

### security

Security scan for sensitive content.

```bash
media-engine security [--include-assets] [--json]
```

| Option | Description |
|--------|-------------|
| `--include-assets` | Also scan YAML/JSON files |

Detects: API keys, PII, internal URLs, credentials.

### changelog

Generate changelog from git history.

```bash
media-engine changelog [--days N] [-o FILE] [--json]
```

| Option | Description |
|--------|-------------|
| `--days` | Limit to last N days |
| `-o` | Write to file |

### demos

Interactive HTML demos.

```bash
media-engine demos <subcommand>
```

Subcommands:
- `list`: List available demos
- `build`: Build demos to HTML

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (validation failed, missing project, etc.) |

## Environment

The CLI looks for `project.yaml` in:
1. Current directory
2. Parent directories (up to root)

## JSON Output

All commands support `--json` for machine-readable output:

```bash
media-engine status --json | jq '.languages'
media-engine quality --json | jq '.error_count'
```

## Common Workflows

Typical command sequences for common tasks.

### Initial Setup

```bash
media-engine init my-project
cd my-project
# Edit content/en/chapters/01_introduction.md
media-engine build
media-engine status
```

### Content Update Cycle

```bash
# Check what needs updating
media-engine stale

# Edit content...

# Validate and build
media-engine quality
media-engine validate
media-engine build

# Publish when ready
media-engine publish
```

### Search and Discovery

```bash
# Build search index
media-engine index

# Find content
media-engine search "authentication"
media-engine search "api endpoint" --limit 5
```

### Release Preparation

```bash
# Full validation
media-engine validate
media-engine quality

# Build all outputs
media-engine build --force

# Create deliverables
media-engine publish --zip
media-engine pack investor
media-engine pack pilot
```
