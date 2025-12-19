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
media-engine status              # Project status overview
media-engine build               # Build outputs
media-engine quality             # Quality checks
media-engine dashboard           # Launch web UI
media-engine translation status  # Translation tracking
media-engine insights            # Analytics insights
media-engine freshness           # Content freshness
media-engine health              # Project health score
media-engine provenance report   # Approval workflow
media-engine integrity verify    # Asset integrity
media-engine release             # Release management
```

## Project Structure

```
python/media_engine/     # Main Python package (38 modules, 172 files)
  core/                  # Config, Project, Theme (entry points)
  settings/              # Centralized configuration (env, paths, defaults)
  config/                # User-level configuration
  cms/                   # Document management (9 files)
  video/                 # Timeline, capture, voiceover, captions (8 files)
  builders/              # HTML, PPTX, XLSX, PDF generation
  templates/             # Jinja2 HTML templates and components
  slides/                # Slide generation
  diagrams/              # Matplotlib-based diagram generation
  assets/                # Font downloading, bundling
  quality/               # Content quality checks
  search/                # Full-text search indexing
  validation/            # Schema and reference validation
  packs/                 # Audience pack generators (investor, pilot)
  publish/               # Deliverable packaging
  insights/              # Comprehensive analytics (11 files)
  freshness/             # Content freshness tracking (3 files)
  mcp/                   # MCP server with 16 tool modules
  web/                   # FastAPI dashboard (16 tabs, 17 API routes)
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
  cli/                   # CLI with 20+ command modules

python/tests/            # Pytest test suite (19 test files)
remotion/src/            # TypeScript/React motion graphics (13 components)
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

Test files (19 total):
- `test_core.py`, `test_cms.py`, `test_video.py`, `test_builders.py`
- `test_web_unit.py`, `test_web_routes.py`, `test_web_integration.py`
- `test_mcp_tools.py`, `test_translation.py`, `test_security.py`
- `test_links.py`, `test_readability.py`, `test_gaps.py`
- `test_variables.py`, `test_diagrams.py`, `test_insights.py`
- `test_integration.py`, `test_user_config.py`

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

## CLI Commands

The CLI is organized into 20+ command modules in `cli/commands/`:

**Project Management:**
```bash
media-engine status              # Project status overview
media-engine init                # Initialize new project
media-engine dashboard           # Launch web UI
media-engine release             # Release management workflow
```

**Content Analysis:**
```bash
media-engine insights            # Analytics insights dashboard
media-engine freshness           # Content freshness status
media-engine health              # Project health score
media-engine stats               # Project statistics
media-engine velocity            # Production velocity metrics
media-engine parity              # Language parity analysis
media-engine consistency         # Content consistency checks
media-engine duplicates          # Duplicate content detection
media-engine incomplete          # Find incomplete content
media-engine gaps                # Content gap analysis
media-engine codesync            # Code synchronization checks
media-engine terms               # Terminology consistency
media-engine path                # Content path analysis
media-engine stale               # Find stale content
```

**Quality & Validation:**
```bash
media-engine quality             # Quality checks
media-engine validate            # Schema validation
media-engine security            # Security scanning (secrets, PII)
media-engine links               # Link validation
media-engine readability         # Readability analysis
media-engine integrity verify    # Asset integrity verification
```

**Translation:**
```bash
media-engine translation status    # All translation pairs
media-engine translation outdated  # Outdated translations
media-engine translation missing   # Missing translations
media-engine translation sync      # Sync translation status
```

**Building & Publishing:**
```bash
media-engine build               # Build outputs
media-engine publish             # Package deliverables
media-engine pack                # Generate audience packs
media-engine demos list          # List available demos
media-engine demos build         # Build interactive demos
```

**Workflow & Maintenance:**
```bash
media-engine provenance report   # Approval workflow status
media-engine provenance claims   # Claims needing verification
media-engine provenance queue    # Documents awaiting review
media-engine graph               # Dependency visualization
media-engine search              # Content search
media-engine cache               # Cache management
media-engine changelog           # Generate changelog
```

## Insights Module

Comprehensive analytics with 11 specialized analyzers in `insights/`:

```bash
media-engine insights            # Full insights dashboard
media-engine health              # Overall project health score
media-engine consistency         # Content consistency analysis
media-engine duplicates          # Duplicate content detection
media-engine terms               # Terminology consistency
media-engine parity              # Language parity across translations
media-engine stats               # Project statistics
media-engine incomplete          # Incomplete content detection
media-engine velocity            # Production velocity metrics
media-engine codesync            # Code synchronization status
media-engine graph               # Dependency graph visualization
```

```python
from media_engine.insights import (
    HealthAnalyzer,
    ConsistencyChecker,
    DuplicateDetector,
    TerminologyAnalyzer,
    ParityChecker,
    StatisticsCollector,
    IncompleteDetector,
    VelocityTracker,
    CodeSyncChecker,
)

health = HealthAnalyzer(project)
score = health.calculate_score()  # 0-100 health score
```

## Freshness Tracking

Track content freshness with persistent registry in `freshness/`:

```bash
media-engine freshness           # Content freshness status
media-engine stale               # Find stale content
```

```python
from media_engine.freshness import FreshnessRegistry, FreshnessScanner

registry = FreshnessRegistry(project)
scanner = FreshnessScanner(project)
stale_docs = scanner.find_stale(days=30)
```

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

Media Engine provides a comprehensive MCP server with 16 specialized tool modules:

```bash
# Install MCP support
pip install media-engine[mcp]

# Run MCP server
media-engine-mcp --project /path/to/project
```

**Tool Modules in `mcp/tools/`:**

| Module | Purpose |
|--------|---------|
| `project.py` | Project status, config, refresh |
| `documents.py` | List, read, update documents |
| `translation.py` | Translation status, sync, outdated |
| `quality.py` | Quality checks, validation |
| `search.py` | Content search |
| `build.py` | HTML, PPTX, XLSX generation |
| `cache.py` | Cache status, clearing |
| `audit.py` | Audit logging |
| `provenance.py` | Approval workflows |
| `batch.py` | Batch operations |
| `session.py` | Session management |
| `suggestions.py` | AI-powered suggestions |
| `claude.py` | Claude-specific integration |
| `context.py` | Context management |
| `webhooks.py` | Webhook integrations |

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

See `mcp/AGENT_DEVELOPER_GUIDE.md` and `mcp/CLAUDE_CODE_EXAMPLES.md` for integration guides.

## Web Dashboard

Launch browser-based UI for project management:

```bash
# Install web support
pip install media-engine[web]

# Launch dashboard
media-engine dashboard
# Opens http://localhost:8080
```

**16 Dashboard Tabs** (`web/dashboard/tabs/`):

| Tab | Purpose |
|-----|---------|
| Overview | Project status at a glance |
| Documents | Document management |
| Translations | Translation matrix view |
| Freshness | Content freshness tracking |
| Insights | Analytics and metrics |
| Assets | Asset management |
| Build | Build controls |
| Quality | Quality issue tracking |
| Provenance | Approval workflow |
| Media | Media registry |
| Search | Content search |
| Activity | Activity log |
| Packs | Pack generation |
| Dependencies | Dependency graph |

**17 API Routes** (`web/routes/`):
- Core, Documents, Translations, Freshness, Insights
- Assets, Build, Quality, Provenance, Media
- Search, Registry, Dependencies, Scene Notes
- WebSocket handlers for real-time updates

**Features:**
- Real-time collaboration via WebSocket
- Responsive design (~195KB JavaScript, ~49KB CSS)
- RESTful API for all operations

## Remotion (Motion Graphics)

TypeScript/React components for video generation in `remotion/`:

**Components** (`remotion/src/components/`):
- `TitleCard.tsx` - Title cards
- `FeatureCard.tsx` - Feature display
- `TextReveal.tsx` - Text animation
- `StatCounter.tsx` - Number counter animation
- `Background.tsx` - Background rendering
- `Transition.tsx` - Scene transitions
- `Overlay.tsx` - Overlay elements

**Utilities** (`remotion/src/lib/`):
- `theme.ts` - Theme utilities
- `animations.ts` - Animation helpers

**Main files:**
- `Video.tsx` - Main video composition (~19KB)
- `Root.tsx` - Root component
- `remotion.config.ts` - Remotion configuration

## Diagram Generation

Generate diagrams with Matplotlib in `diagrams/`:

```python
from media_engine.diagrams import DiagramGenerator

generator = DiagramGenerator(project)
generator.generate("workflow", output_path)
```

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
media-engine terms              # Check terminology consistency
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

```bash
media-engine graph               # Visualize dependencies
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

## User Configuration

User-level settings in `config/user_config.py`:

```python
from media_engine.config import UserConfig

config = UserConfig.load()
config.set("editor", "code")
config.save()
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
