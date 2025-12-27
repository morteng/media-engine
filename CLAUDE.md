# Media Engine

Agent-based media production framework for automated content generation.

## Quick Reference

```bash
uv sync                              # Install dependencies
uv run pytest                        # Run tests
uv run ruff check python/            # Lint

# Core commands
media-engine status                  # Project overview
media-engine build                   # Build outputs
media-engine dashboard               # Launch web UI
media-engine quality                 # Quality checks
media-engine translation status      # Translation tracking
media-engine diagrams build          # Build diagrams
```

## Project Structure

```
python/media_engine/     # Main Python package
  core/                  # Config, Project, Theme, Hashing
  brand/                 # Brand/design system
  cms/                   # Document management
  builders/              # HTML, PPTX, XLSX, PDF generation
  diagrams/              # Multi-engine diagram generation (matplotlib, d2, excalidraw)
  video/                 # Timeline, capture, voiceover
  publications/          # Publication registry, builder, tracker
  ai/                    # AI context, sessions, research, notes, queue
  mcp/                   # MCP server (20+ tool modules)
  web/                   # FastAPI dashboard (17 tabs, 30+ routes)
  cli/                   # CLI (25+ command modules)
  relationships/         # Unified document relationships
  insights/              # Analytics (11 analyzers)
  freshness/             # Content freshness + predictive
  quality/               # Quality checks
  security/              # Secrets/PII detection
  semantic/              # Similarity, duplicates
  knowledge/             # Knowledge graph

python/tests/            # 54+ test files
dashboard/src/           # React dashboard (Vite + React 19)
remotion/src/            # Motion graphics components
demo/                    # Reference project
```

## Code Conventions

- Python 3.11+, type hints required, 100 char lines
- Dataclasses for data structures
- Google-style docstrings
- Imports sorted with ruff

## Key Patterns

```python
from media_engine import find_project
project = find_project()  # Searches up for project.yaml
```

**Config files**: `project.yaml`, `brand.yaml` (colors/fonts/logos), `schema.yaml` (validation)

## Unified Hashing

All modules use 16-char SHA256 via `core/hashing.py`:
```python
from media_engine.core import compute_content_hash, compute_document_hash, compute_file_hash
```

## CLI Commands

| Category | Commands |
|----------|----------|
| **Project** | `status`, `init`, `dashboard`, `release`, `brand status/init/validate` |
| **Content** | `insights`, `freshness`, `health`, `stats`, `gaps`, `stale`, `incomplete` |
| **Quality** | `quality`, `validate`, `security`, `links`, `readability` |
| **Translation** | `translation status/outdated/missing/sync` |
| **Build** | `build`, `publish`, `pack`, `demos list/build`, `diagrams build/list/engines` |
| **Publications** | `publications list/status/build/components/stale` |
| **Dependencies** | `graph`, `deps status/stale/check/sync`, `relationships status/graph` |
| **Workflow** | `provenance report/claims/queue`, `search`, `cache`, `changelog` |

## Diagram Generation

Multi-engine system with brand integration:

```bash
media-engine diagrams list           # List diagrams
media-engine diagrams engines        # Show available engines
media-engine diagrams build          # Build all (light + dark)
media-engine diagrams preview <file> --render
```

**Engines**: `matplotlib` (default), `d2` (sketch/animations), `excalidraw` (hand-drawn via Kroki.io)

```python
from media_engine.diagrams import DiagramGenerator, DiagramDefinition
generator = DiagramGenerator(brand=project.brand_context)
generator.generate(definition, "output.png", engine="d2")
```

**YAML schema**:
```yaml
config:
  engine: d2         # matplotlib, d2, excalidraw, auto
  engine_options: { sketch: true, layout: elk }
boxes:
  - id: api
    label: API
    color: "brand.primary"  # Brand tokens supported
    layer: frontend
arrows:
  - from: api
    to: db
    animated: true
layers:
  - id: frontend
    label: Frontend
```

## Translation Tracking

Hash-based change detection:
```yaml
language: "no"
source_document: "en/chapters/01_intro.md"
source_hash: "a1b2c3d4e5f67890"
```

## Brand System

Single source of truth in `brand.yaml`:
```python
from media_engine.brand import BrandContext
brand = BrandContext(profile=profile)
brand.get_color("brand.primary", dark_mode=True)
brand.get_system_font("heading")
```

## Publications System

Deliverable-centric architecture for composite documents:

```bash
media-engine publications list          # List all publications
media-engine publications status        # Status overview
media-engine publications build <id>    # Build a publication
media-engine publications components <id>  # Show components
```

**YAML configuration** (`project.yaml`):
```yaml
publications:
  - id: docs-book
    title: Documentation
    type: book        # book, deck, video, report, website, package
    formats: [pdf, html]
    languages: [en, 'no']
    parts:
      - id: intro
        title: Getting Started
        components:
          - source: content/en/chapters/01_intro.md
            type: chapter
```

```python
from media_engine.publications import PublicationRegistry, PublicationBuilder, PublicationTracker

registry = PublicationRegistry(project)
for pub in registry.list():
    print(f"{pub.id}: {len(pub.get_all_components())} components")
```

## AI Context & Session Management

Full AI-native integration for Claude Code and other agents:

```bash
# Work queue for AI tasks
media-engine ai queue           # View pending tasks

# Via MCP tools (Claude Code)
get_ai_context()               # Full project context
start_ai_session(task_id)      # Track session
record_session_change(...)     # Track changes
complete_ai_session(...)       # Complete with summary
```

**AI module components**:
- `AIContext` - Comprehensive context provider
- `SessionManager` - Session tracking for continuity
- `TaskQueue` - Work queue with priorities
- `ResearchStore` - Persistent research storage
- `NotesManager` - AI-human collaboration notes

```python
from media_engine.ai import AIContext, SessionManager, NotesManager, ResearchStore

context = AIContext(project)
full_context = context.get_full_context()  # Everything needed to work

sessions = SessionManager(project.root)
session = sessions.start(task_id="update-docs")
sessions.add_step(session.id, "Reviewing chapters")
sessions.add_change(session.id, "chapters/01.md", "modified")
```

**MCP Tools for AI**:
| Tool | Purpose |
|------|---------|
| `get_ai_context` | Full project context for starting work |
| `get_document_context` | Context for specific document |
| `start_ai_session` | Begin tracked session |
| `record_session_progress` | Track work steps |
| `record_decision` | Record decisions with reasoning |
| `add_ai_note` | Notes for humans/future AI |
| `store_research` | Persist research findings |
| `get_work_queue` | View pending tasks |

## MCP Server

```bash
media-engine-mcp --project /path/to/project
```

**Tool modules**: `project`, `documents`, `translation`, `quality`, `build`, `diagrams`, `search`, `cache`, `audit`, `provenance`, `notes`, `suggestions`, `context`, `ai`, `ai_context`, `publications`, `relationships`

**Claude Desktop** (`~/.claude/claude_desktop_config.json`):
```json
{"mcpServers": {"media-engine": {"command": "media-engine-mcp", "args": ["-p", "/path"]}}}
```

## Web Dashboard

```bash
media-engine dashboard  # http://localhost:8080
```

**Features**: Real-time WebSocket updates, file watching, background preprocessing, Reagraph visualizations

**API routes**: `/api/status`, `/api/documents`, `/api/diagrams`, `/api/translations`, `/api/quality`, `/api/build`, etc.

## Testing

```bash
uv run pytest                                    # All tests
uv run pytest --cov=media_engine --cov-fail-under=80
cd dashboard && npm run test:run                 # Unit tests
npm run test:e2e                                 # Playwright E2E
```

Key test files: `test_core.py`, `test_mcp_tools.py`, `test_diagram_engines.py`, `test_web_*.py`

## Advanced Analysis

| Module | Purpose |
|--------|---------|
| `semantic/` | Duplicate detection, terminology drift |
| `knowledge/` | Knowledge graph, orphan concepts |
| `freshness/predictive.py` | Staleness prediction |
| `codesync/` | Code-doc sync validation |
| `readability/` | Flesch, Fog, LIX (Norwegian) |

## Relationships Registry

```python
from media_engine.relationships import get_registry_manager
manager = get_registry_manager(project)
manager.get_stale_documents()
manager.mark_fresh(doc_path)
```

**Edge types**: `PARENT`, `TRANSLATES`, `REFERENCES`, `USES_ASSET`, `DEPENDS_ON`

## Security & Quality

```bash
media-engine security      # Scan for secrets, PII, API keys
media-engine links         # Validate internal/external links
media-engine integrity verify
```

## Content Variables

`{{project.name}}`, `{{date.today}}`, `{{env.VAR}}` in markdown

## YAML Gotcha

```yaml
languages:
  "no":  # Must quote - YAML interprets bare 'no' as boolean False
```
