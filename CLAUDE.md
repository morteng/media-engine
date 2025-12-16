# Media Engine

Agent-based media production framework for automated content generation.

## Quick Reference

```bash
# Install dependencies
uv sync

# Install with all optional features
pip install media-engine[all]

# Run tests
uv run pytest

# Run specific test file
uv run pytest python/tests/test_core.py

# Lint
uv run ruff check python/

# CLI (after install)
media-engine status
media-engine build
media-engine quality
media-engine dashboard       # Launch web UI
media-engine translation status
media-engine provenance report
media-engine integrity verify
```

## Project Structure

```
python/media_engine/     # Main Python package
  core/                  # Config, Project, Theme (entry points)
  cms/                   # Document management, frontmatter parsing
  video/                 # Timeline, capture, voiceover, captions
  builders/              # HTML, PPTX, XLSX, PDF generation
  templates/             # Jinja2 HTML templates
  assets/                # Font downloading, bundling
  quality/               # Content quality checks
  search/                # Full-text search indexing
  validation/            # Schema and reference validation
  packs/                 # Audience pack generators (investor, pilot)
  publish/               # Deliverable packaging
  status/                # Dashboard views
  mcp/                   # MCP server for AI agent integration
  web/                   # FastAPI web dashboard
  gui/                   # Easy GUI launcher
  audit/                 # Audit logging system
  provenance/            # Claim tracking and approval workflows
  dependencies/          # Document dependency graph
  integrity/             # Asset checksums and terminology
  security/              # Sensitive content detection (secrets, PII)
  links/                 # External and internal link validation
  variables/             # Content variable interpolation
  changelog/             # Changelog generation from git/docs
  readability/           # Readability scoring (Flesch, Fog, etc.)
  gaps/                  # Content gap analysis
  demos/                 # Interactive HTML demo generation
  cli.py                 # argparse-based CLI

python/tests/            # Pytest test suite
remotion/src/            # TypeScript/React motion graphics components
```

## Code Conventions

- **Python 3.11+** required
- **Type hints** on all function signatures
- **Dataclasses** for data structures (see `core/project.py`, `core/config.py`)
- **Line length**: 100 characters (ruff configured)
- **Docstrings**: Module and class level, Google style
- **Imports**: sorted with ruff (isort rules)

## Testing

Tests use pytest with fixtures defined in `conftest.py`:
- `temp_dir` - temporary directory cleanup
- `sample_markdown` - markdown with frontmatter
- `sample_config`, `sample_theme` - YAML config fixtures

Test classes follow `Test{ClassName}` naming with `test_{method}` methods.

## Key Patterns

**Project loading**: Always start from `Project.load()` or `find_project()`:
```python
from media_engine import find_project
project = find_project()  # searches up directory tree for project.yaml
```

**Configuration files**:
- `project.yaml` - project config, paths, localization
- `theme.yaml` - colors, typography, design tokens
- `schema.yaml` - frontmatter validation schema

**Module exports**: Public API defined in each module's `__init__.py` and re-exported from top-level `__init__.py`.

## Translation Tracking

Multilingual documents use frontmatter to track translation status:

```yaml
language: "no"
source_document: "en/chapters/01_introduction.md"
source_version: "1.0.0"  # version of source when translated
```

Translation commands:
```bash
media-engine translation status    # Show all translation pairs
media-engine translation outdated  # Show only outdated translations
media-engine translation missing   # Show missing translations
```

## Demo Project

The `demo/` directory is a fully-functional reference project that documents media-engine itself:
- 12 English chapters covering all features
- 12 Norwegian translations
- Scripts, diagrams, slides, and data files in both languages
- Used for integration testing

## MCP Server (Agent Integration)

Media Engine provides a comprehensive MCP server for agent-agnostic integration:

```bash
# Install MCP support
pip install media-engine[mcp]

# Run MCP server
media-engine-mcp --project /path/to/project
```

**20+ Tools exposed via MCP:**
- Project: `project_status`, `project_config`, `refresh_project`
- Content: `list_chapters`, `read_document`, `update_document_metadata`, `increment_document_version`
- Translation: `translation_status`, `outdated_translations`, `missing_translations`, `mark_translation_synced`
- Quality: `quality_check`, `validate_project`
- Search: `search_content`
- Build: `build_html`, `build_pptx`, `build_xlsx`
- Cache: `cache_status`, `clear_cache`
- Audit: `log_action`, `get_audit_log`

**Claude Desktop config** (`~/.claude/claude_desktop_config.json`):
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

Launch browser-based UI for project management:

```bash
# Install web support
pip install media-engine[web]

# Launch dashboard
media-engine dashboard
# Opens http://localhost:8080
```

Features:
- Translation matrix view
- Quality issue tracking
- Build controls
- Real-time collaboration via WebSocket

## Provenance & Approval Workflow

Track claims and manage document approval:

```bash
media-engine provenance report   # Full provenance report
media-engine provenance claims   # Claims needing verification
media-engine provenance queue    # Documents awaiting review
```

Document states: `draft` → `in_review` → `approved` → `published`

```python
from media_engine.provenance import ProvenanceTracker

tracker = ProvenanceTracker(project)
tracker.request_approval(doc_path, "author@example.com")
tracker.approve_document(doc_path, "reviewer@example.com")
```

## Asset Integrity & Terminology

```bash
media-engine integrity record   # Record asset checksums
media-engine integrity verify   # Verify no unauthorized changes
media-engine integrity terms    # Check terminology consistency
```

## Audit Logging

All operations are logged to `.media-engine/audit.log`:

```python
from media_engine.audit import log_action, get_recent_entries

log_action(project, "document_updated", details="Updated intro", user="author")
entries = get_recent_entries(project, limit=50)
```

## Dependency Tracking

Track relationships between documents:

```python
from media_engine.dependencies import DependencyGraph

graph = DependencyGraph(project)
graph.refresh()  # Scan all documents
affected = graph.get_impact(changed_doc)  # What needs review?
```

## Platform Independence

Publish directory resolution priority:
1. Environment variable: `MEDIA_ENGINE_PUBLISH_DIR`
2. Config in project.yaml: `paths.publish`
3. Default: `{project_root}/dist/{project-name}`

## Security Scanning

Detect sensitive content before publishing:

```bash
media-engine security               # Scan for secrets/PII
media-engine security --include-assets  # Also scan YAML/JSON files
```

Detects: API keys (AWS, GitHub, OpenAI, Anthropic, Stripe), PII (emails, phone, SSN), internal URLs, private IPs.

## Link Validation

```bash
media-engine links                 # Check all links
media-engine links --internal-only # Skip external URLs
```

Features: parallel checking, result caching, broken link detection.

## Content Variables

Use `{{variable.path}}` syntax for dynamic content:

```markdown
Published: {{date.today}}
Project: {{project.name}}
```

Available namespaces: `project`, `date`, `env`, plus custom from `variables.yaml`.

## Readability Analysis

```bash
media-engine readability                    # Analyze all docs
media-engine readability --target college   # Set target level
```

Metrics: Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog, SMOG Index.

## Content Gap Analysis

```bash
media-engine gaps                              # Find missing content
media-engine gaps --topics "installation,api"  # Check expected topics
```

Detects: missing translations, broken references, orphan documents.

## Changelog Generation

```bash
media-engine changelog                # Full changelog
media-engine changelog --days 30      # Last 30 days
media-engine changelog -o CHANGELOG.md  # Write to file
```

## PDF Generation

```bash
pip install media-engine[pdf]
```

```python
from media_engine.builders.pdf import PDFBuilder

builder = PDFBuilder(theme=project.theme)
builder.build_from_markdown(content, title, output_path)
```

## Interactive Demos

Create interactive HTML demos (calculators, code playgrounds, comparisons):

```bash
media-engine demos list   # List available demos
media-engine demos build  # Build to HTML
```

Demo types: `code_playground`, `calculator`, `comparison`, `timeline`, `quiz`, `data_viz`, `form_demo`, `api_explorer`.

Demo config (`content/en/demos/example.yaml`):
```yaml
id: pricing-calc
type: calculator
title: Pricing Calculator
data:
  formula: "chapters * 100 + videos * 500"
  variables:
    - name: chapters
      label: Chapters
      default: 10
```

## Easy GUI Launch

```bash
# From anywhere
media-engine-gui                    # Auto-detect project
media-engine-gui /path/to/project   # Specific project
media-engine-gui --browse           # Open file browser

# Or via CLI
media-engine dashboard
```

## GitHub Actions CI/CD

Workflow at `.github/workflows/docs.yml`:
- Validates content quality
- Checks translations
- Security scans
- Builds documentation
- Deploys to GitHub Pages

## YAML Gotcha

When configuring Norwegian language, always quote "no":
```yaml
languages:
  "no":  # Must quote - YAML interprets bare 'no' as boolean False
    name: "Norwegian"
```
