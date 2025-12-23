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
media-engine brand status        # Brand/design system status
```

## Project Structure

```
python/media_engine/     # Main Python package (45+ modules, 200+ files)
  core/                  # Config, Project, Theme, Hashing (entry points)
  brand/                 # Brand/design system (8 files)
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
  freshness/             # Content freshness tracking + predictive (4 files)
  mcp/                   # MCP server with 18 tool modules
  web/                   # FastAPI dashboard (16 tabs, 25 API routes, file watcher)
  hierarchy/             # Document hierarchy and staleness propagation
  gui/                   # Easy GUI launcher
  audit/                 # Audit logging system
  provenance/            # Claim tracking and approval workflows
  dependencies/          # Document dependency graph
  integrity/             # Asset checksums and terminology
  security/              # Sensitive content detection (secrets, PII)
  links/                 # External and internal link validation
  variables/             # Content variable interpolation
  changelog/             # Changelog generation from git/docs
  readability/           # Readability scoring (Flesch, Fog, LIX for Norwegian)
  gaps/                  # Content gap analysis
  demos/                 # Interactive HTML demo generation
  cli/                   # CLI with 20+ command modules
  # Advanced Analysis Modules
  semantic/              # Semantic similarity, duplicate detection, terminology
  knowledge/             # Knowledge graph, concept mapping, prerequisites
  codesync/              # Code-documentation synchronization
  advanced/              # Audience analysis, style checking, engagement
  llm_quality/           # LLM-ready quality reporting (for MCP integration)

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

## Unified Hashing

All modules use consistent SHA256 hashes (16 characters) via `core/hashing.py`:

```python
from media_engine.core import (
    compute_content_hash,   # Text content (normalized whitespace)
    compute_document_hash,  # Markdown (content only, no frontmatter)
    compute_file_hash,      # Binary files (chunked reading)
    compute_raw_hash,       # Raw bytes
    compute_short_hash,     # Configurable length (default 8)
    verify_hash,            # Verify content matches hash
    verify_file_hash,       # Verify file matches hash
)

# All hashes are 16-char SHA256 by default
hash = compute_content_hash("Hello world")  # "b94d27b9934d3e08"
```

Used by: translation tracking, dependency detection, freshness registry, provenance, scene notes.

## Key Patterns

**Project loading**: Always start from `Project.load()` or `find_project()`:
```python
from media_engine import find_project
project = find_project()  # searches up directory tree for project.yaml
```

**Configuration files**:
- `project.yaml` - project config, paths, localization
- `brand.yaml` - unified brand system (colors, typography, logos, tokens)
- `theme.yaml` - legacy colors/typography (deprecated, use brand.yaml)
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
media-engine brand status        # Show brand profile (colors, fonts, logos)
media-engine brand init          # Create brand.yaml from template
media-engine brand migrate       # Migrate theme.yaml to brand.yaml
media-engine brand validate      # Validate brand.yaml configuration
media-engine brand export-css    # Export CSS variables from brand
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

**Dependencies:**
```bash
media-engine graph               # Dependency visualization
media-engine deps status         # Dependency hash status
media-engine deps stale          # Documents with stale dependencies
media-engine deps check <path>   # Check specific document
media-engine deps sync           # Sync hashes from graph
media-engine deps refresh        # Refresh all hashes
```

**Workflow & Maintenance:**
```bash
media-engine provenance report   # Approval workflow status
media-engine provenance claims   # Claims needing verification
media-engine provenance queue    # Documents awaiting review
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

## Advanced Analysis Modules

Media Engine includes advanced analysis capabilities for deep content quality assessment:

### Semantic Analysis (`semantic/`)

Detect content similarity and terminology consistency:

```python
from media_engine.semantic import SemanticAnalyzer

analyzer = SemanticAnalyzer(project)

# Find near-duplicate documents (>85% similarity)
duplicates = analyzer.find_near_duplicates(threshold=0.85)

# Detect terminology inconsistencies
drift = analyzer.detect_terminology_drift()

# Cluster content by topic
clusters = analyzer.cluster_content()

# Find similar documents to a specific one
similar = analyzer.find_similar_documents(doc_path, top_k=5)
```

### Knowledge Graph (`knowledge/`)

Map concepts and relationships across documentation:

```python
from media_engine.knowledge import KnowledgeGraph

kg = KnowledgeGraph(project)
kg.build()

# Get concept statistics
stats = kg.get_statistics()  # total_concepts, relationships, coverage_score

# Find orphan concepts (mentioned but never explained)
orphans = kg.find_orphan_concepts()

# Get document prerequisites
prereqs = kg.get_prerequisites(doc_path)

# Find prerequisite issues
issues = kg.find_prerequisite_issues()
```

### Predictive Freshness (`freshness/predictive.py`)

Predict which documents will become stale:

```python
from media_engine.freshness.predictive import PredictiveFreshnessModel

model = PredictiveFreshnessModel(project)

# Get staleness predictions for all documents
predictions = model.predict_staleness()

# Each prediction contains:
# - document: Path to document
# - risk_score: 0-1 probability of becoming stale
# - days_until_stale: Predicted days before review needed
# - risk_factors: Why document is at risk

high_risk = [p for p in predictions if p.risk_score > 0.7]
```

### Code-Doc Sync (`codesync/`)

Detect mismatches between code references and documentation:

```python
from media_engine.codesync import CodeDocSyncChecker

checker = CodeDocSyncChecker(project)

# Check all documents
issues = checker.check_all()

# Check specific document
doc_issues = checker.check_document(doc_path)

# Issues include:
# - Syntax errors in code examples
# - Deprecated API references
# - Version mismatches
```

### Norwegian Readability (`readability/norwegian.py`)

LIX-based readability analysis for Norwegian content:

```python
from media_engine.readability.norwegian import NorwegianReadabilityAnalyzer

analyzer = NorwegianReadabilityAnalyzer(project)

# Analyze all Norwegian documents
results = analyzer.analyze_all()

# Each result contains:
# - lix: LIX score (lower = easier)
# - difficulty_level: "easy", "medium", "difficult", "very_difficult"
# - word_count, sentence_count, long_word_count

# LIX interpretation:
# < 25: Very easy (children's books)
# 25-35: Easy (simple text)
# 35-45: Medium (newspapers)
# 45-55: Difficult (official documents)
# > 55: Very difficult (academic)
```

### MCP Integration

All advanced analysis is available through MCP tools for AI agents:

```python
# Get comprehensive quality report
quality_report_comprehensive()

# Get report for specific module
quality_report_module("semantic")  # or "knowledge", "freshness", "codesync", "readability"

# Get document-specific analysis
quality_report_document("chapters/api.md")

# Get prioritized issues
quality_report_issues(priority="high")
```

See `mcp/AGENT_DEVELOPER_GUIDE.md` for detailed tool documentation.

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

Multilingual documents use frontmatter to track translation status with **hash-based change detection**:

```yaml
language: "no"
source_document: "en/chapters/01_introduction.md"
source_hash: "a1b2c3d4e5f67890"  # Content hash of source when translated
```

The system uses SHA256 content hashes (16 characters) to detect when source documents change, automatically flagging translations for review.

Translation commands:
```bash
media-engine translation status    # Show all translation pairs
media-engine translation outdated  # Show only outdated translations
media-engine translation missing   # Missing translations
media-engine translation sync      # Sync translation status registry
```

```python
from media_engine.cms.translation import TranslationTracker

tracker = TranslationTracker(project)
status = tracker.get_all_status()  # All translation pairs with hash status
outdated = tracker.get_outdated()  # Translations with stale source hashes
```

## Demo Project

The `demo/` directory is a fully-functional reference project that documents media-engine itself:
- 12 English chapters covering all features
- 12 Norwegian translations
- Scripts, diagrams, slides, and data files in both languages
- Used for integration testing

## Brand/Design System

Unified visual identity system for consistent styling across all output formats.

**Project structure:**
```
project_root/
├── brand.yaml          # Single source of truth for brand
├── brand/
│   ├── logos/          # Logo variants (SVG, PNG)
│   │   ├── logo.svg
│   │   ├── logo-dark.svg
│   │   └── icon.png
│   └── fonts/          # Local fonts (if source: local)
└── theme.yaml          # Legacy (deprecated)
```

**CLI commands:**
```bash
media-engine brand status       # View colors, typography, logos
media-engine brand init         # Create brand.yaml template
media-engine brand migrate      # Convert theme.yaml to brand.yaml
media-engine brand validate     # Validate configuration
media-engine brand export-css   # Export CSS variables
```

**brand.yaml schema:**
```yaml
name: "Project Name"

identity:
  logos:
    primary: { path: "brand/logos/logo.svg", alt: "Logo" }
    dark: { path: "brand/logos/logo-dark.svg" }
    icon: { path: "brand/logos/icon.png", sizes: [16, 32, 64] }
  legal:
    copyright: "2024 Company"
    tagline: "Your tagline"

colors:
  brand:
    primary: "#6366f1"
    secondary: "#8b5cf6"
    accent: "#06b6d4"
  semantic:
    success: "#10b981"
    warning: "#f59e0b"
    error: "#ef4444"
    info: "#3b82f6"
  text: { primary: "#1f2937", secondary: "#4b5563", muted: "#9ca3af" }
  background: { primary: "#ffffff", secondary: "#f9fafb" }
  dark:  # Dark mode overrides
    text: { primary: "#f9fafb", muted: "#9ca3af" }
    background: { primary: "#111827", secondary: "#1f2937" }

typography:
  fonts:
    heading: { family: "Inter", weights: [500, 600, 700], source: "google" }
    body: { family: "Inter", weights: [400, 500], source: "google" }
    code: { family: "JetBrains Mono", weights: [400], source: "google" }
  scale: { xs: 12, sm: 14, base: 16, lg: 18, xl: 20, 2xl: 24, display: 72 }

spacing: { unit: 4, scale: { 1: 4, 2: 8, 4: 16, 6: 24, 8: 32 } }
borders: { radius: { sm: 2, md: 4, lg: 8, full: 9999 } }
shadows:
  sm: "0 1px 2px rgba(0,0,0,0.05)"
  md: "0 4px 6px rgba(0,0,0,0.1)"
```

**Python API:**
```python
from media_engine.brand import BrandContext, load_brand_profile

# Load brand profile
profile = load_brand_profile(project.root)

# Create context for builders
brand = BrandContext(profile=profile)

# Access colors (supports dot notation)
primary = brand.get_color("brand.primary")
error = brand.get_color("semantic.error")
dark_bg = brand.get_color("background.primary", dark_mode=True)

# Get logo with format conversion (SVG→PNG for PPTX)
logo = brand.get_logo("primary", format="png", size=256)

# Get system font (maps web fonts to Office-compatible)
font = brand.get_system_font("heading")  # "Arial" for Inter

# Generate CSS
css = brand.generate_complete_css(include_fonts=True)
```

**Builder integration:**
```python
from media_engine.builders import HTMLBuilder, PPTXBuilder, XLSXBuilder

# All builders accept brand parameter
html = HTMLBuilder(brand=project.brand_context)
pptx = PPTXBuilder(brand=project.brand_context)
xlsx = XLSXBuilder(brand=project.brand_context)

# Legacy theme parameter still works (converted internally)
html = HTMLBuilder(theme=project.theme)
```

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
| `reports.py` | Comprehensive quality reports (semantic, knowledge, freshness, codesync) |
| `search.py` | Content search |
| `build.py` | HTML, PPTX, XLSX generation |
| `cache.py` | Cache status, clearing |
| `audit.py` | Audit logging |
| `provenance.py` | Approval workflows |
| `notes.py` | Scene notes and annotations |
| `batch.py` | Batch operations |
| `session.py` | Session management |
| `suggestions.py` | AI-powered suggestions with advanced analysis |
| `claude.py` | Claude-specific integration |
| `context.py` | Context management with advanced analysis |
| `ai.py` | AI task queue management |
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
- **File watching** with automatic UI refresh on content changes
- **Background preprocessing** for fast API responses
- **Incremental registry updates** on file changes
- Responsive design (~195KB JavaScript, ~49KB CSS)
- RESTful API for all operations

**Real-time Updates:**

The dashboard monitors project files and broadcasts changes to connected clients:

```python
from media_engine.web.watcher import FileWatcher, start_watcher
from media_engine.web.preprocessor import BackgroundPreprocessor
from media_engine.web.incremental import IncrementalUpdater

# File watching detects changes and triggers:
# 1. WebSocket broadcast to all dashboard clients
# 2. Background preprocessor cache invalidation
# 3. Incremental registry updates (freshness, translations, dependencies)
```

Cache stats endpoint: `GET /api/cache-stats`

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

Track relationships between documents with **hash-based change detection**:

```python
from media_engine.dependencies import DependencyGraph, DependencyHashTracker

# Graph-based dependency analysis
graph = DependencyGraph(project)
graph.refresh()  # Scan all documents
affected = graph.get_impact(changed_doc)  # What needs review?

# Hash-based staleness detection
tracker = DependencyHashTracker(project)
status = tracker.check_document(doc_path)  # Check if dependencies changed
stale = tracker.get_all_stale()  # All documents with stale dependencies
tracker.mark_current(doc_path)  # Acknowledge dependency changes
```

CLI commands:
```bash
media-engine graph               # Visualize dependencies
media-engine deps status         # Dependency hash status
media-engine deps stale          # Documents with stale dependencies
media-engine deps check <path>   # Check specific document
media-engine deps sync           # Sync hashes from dependency graph
media-engine deps refresh        # Refresh all dependency hashes
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
