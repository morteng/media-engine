# Media Engine

**Agent-operated media production framework for automated content generation.**

Write content once in Markdown. Generate professional documents, presentations, videos, and interactive demos automatically.

[![CI](https://github.com/morteng/media-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/morteng/media-engine/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What It Does

Media Engine transforms your Markdown content into multiple output formats:

| Input | Outputs |
|-------|---------|
| Markdown chapters | HTML documents, PDF reports |
| YAML scripts | Voiceover audio, captions, video |
| YAML slide definitions | PowerPoint presentations |
| YAML data files | Excel spreadsheets with charts |
| YAML demo configs | Interactive HTML demos |
| YAML diagram specs | SVG/PNG diagrams |

All outputs are styled consistently using your theme configuration.

---

## Features

### Content Management
- **Markdown + YAML frontmatter** - Version tracking, status workflow, dependency graphs
- **Multi-language support** - Translation tracking with outdated detection
- **Full-text search** - Indexed search with relevance scoring

### Document Generation
- **HTML** - Responsive design, syntax highlighting, dark mode
- **PDF** - Print-ready documents
- **PowerPoint** - Slide decks from YAML definitions
- **Excel** - Spreadsheets with formulas and charts
- **Diagrams** - Matplotlib-based with theming

### Video Production
- **Voiceover** - ElevenLabs TTS with smart caching
- **Captions** - Auto-generated WebVTT
- **Motion graphics** - Remotion React components
- **Browser capture** - Playwright-based screen recording

### Quality Assurance
- **Readability scoring** - Flesch, Fog, SMOG indexes
- **Link validation** - Internal and external URL checking
- **Reference checking** - Cross-document reference validation
- **Schema validation** - Frontmatter structure enforcement
- **Security scanning** - API keys, PII, secrets detection

### Integrations
- **CLI** - Full command-line interface
- **MCP Server** - 20+ tools for AI agent integration
- **Web Dashboard** - Real-time project management UI
- **GitHub Actions** - CI/CD workflow templates
- **Python API** - Programmatic access to all features

---

## Quick Start

```bash
# Install
pip install media-engine

# Or with all optional features
pip install media-engine[all]

# Initialize project
media-engine init my-project
cd my-project

# Build all outputs
media-engine build

# Launch dashboard
media-engine dashboard
```

---

## CLI Reference

```bash
# Project status
media-engine status              # Full dashboard
media-engine status docs         # Document status
media-engine status videos       # Video production status

# Build outputs
media-engine build               # Build all formats
media-engine build --only html   # HTML only
media-engine build --force       # Force rebuild

# Quality & validation
media-engine quality             # Run quality checks
media-engine validate            # Schema + reference validation
media-engine security            # Scan for secrets/PII
media-engine links               # Validate all links

# Translation tracking
media-engine translation status    # All translation pairs
media-engine translation outdated  # Outdated translations
media-engine translation missing   # Missing translations

# Content analysis
media-engine readability         # Readability scores
media-engine gaps                # Content gap analysis
media-engine search "query"      # Full-text search

# Interactive demos
media-engine demos list          # List available demos
media-engine demos build         # Build to HTML

# Publishing
media-engine publish             # Self-contained package
media-engine pack investor       # Curated audience pack

# Dashboard
media-engine dashboard           # Launch web UI
```

---

## Project Structure

```
my-project/
├── project.yaml          # Project configuration
├── theme.yaml            # Design tokens
├── schema.yaml           # Frontmatter validation
├── content/
│   ├── en/
│   │   ├── chapters/     # Markdown documentation
│   │   ├── scripts/      # Video script YAML
│   │   ├── slides/       # Presentation YAML
│   │   ├── diagrams/     # Diagram definitions
│   │   ├── demos/        # Interactive demo configs
│   │   └── data/         # Spreadsheet data
│   └── no/               # Norwegian translations
├── assets/               # Images, fonts, media
└── output/               # Generated files
```

---

## Configuration

### project.yaml

```yaml
project:
  name: "My Project"
  description: "Project description"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"
      locale: "en-US"
      voice_id: "your-elevenlabs-voice-id"
    "no":  # Quote "no" - YAML interprets bare 'no' as false
      name: "Norwegian"
      locale: "nb-NO"

voiceover:
  provider: "elevenlabs"
  stability: 0.5
  similarity_boost: 0.75

video:
  width: 1920
  height: 1080
  fps: 30

paths:
  content: "content"
  assets: "assets"
  output: "output"
```

### theme.yaml

```yaml
name: "My Theme"

colors:
  primary: "#1a365d"
  accent: "#3182ce"
  background: "#ffffff"
  text: "#1a202c"

typography:
  heading: "Inter"
  body: "Source Sans 3"
  code: "JetBrains Mono"
```

---

## Python API

```python
from media_engine import find_project, run_quality_checks

# Load project
project = find_project()

# List documents
for doc in project.list_chapters("en"):
    print(f"{doc.stem}: v{doc.metadata.get('version', '?')}")

# Run quality checks
report = run_quality_checks(project)
print(f"Found {report.error_count} errors, {report.warning_count} warnings")

# Build outputs
from media_engine.builders import HTMLBuilder
builder = HTMLBuilder(project)
builder.build_all()
```

---

## MCP Server (AI Agent Integration)

Connect Claude Desktop or any MCP-compatible agent:

```bash
# Run MCP server
media-engine-mcp --project /path/to/project
```

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

**Available tools:** `project_status`, `list_chapters`, `read_document`, `update_document_metadata`, `translation_status`, `quality_check`, `build_html`, `search_content`, and 12 more.

---

## Web Dashboard

```bash
media-engine dashboard
# Opens http://localhost:8080
```

Features:
- **Overview** - Project stats, translation matrix, recent issues
- **Documents** - Browse and preview all content types
- **Media** - View generated audio, video, demos with source links
- **Translations** - Full translation status matrix
- **Quality** - Issue tracking with file navigation
- **Activity** - Audit log of all operations

---

## Video Production Pipeline

Define video scripts in YAML:

```yaml
id: product-demo
title: "Product Demo"
duration: 120
scenes:
  - type: title
    text: "Welcome to Our Product"
    duration: 5
  - type: demo
    action: "Show the dashboard"
    voiceover: "Let me show you the main dashboard."
    duration: 10
```

Build with voiceover and captions:

```bash
media-engine build --only video
```

Generates:
- `output/en/videos/product-demo.mp3` - Voiceover audio
- `output/en/videos/product-demo.vtt` - Captions
- `output/en/videos/product-demo/props.json` - Remotion render props

---

## Interactive Demos

Create calculator, playground, comparison, and quiz demos:

```yaml
# content/en/demos/pricing.yaml
id: pricing-calc
type: calculator
title: "Pricing Calculator"
data:
  formula: "(users * 10) + (storage * 0.05)"
  variables:
    - name: users
      label: "Number of Users"
      default: 100
    - name: storage
      label: "Storage (GB)"
      default: 500
```

Build demos:

```bash
media-engine demos build
# Creates interactive HTML in output/demos/
```

---

## Security Scanning

Detect sensitive content before publishing:

```bash
media-engine security
media-engine security --include-assets
```

Detects:
- API keys (AWS, GitHub, OpenAI, Anthropic, Stripe)
- PII (emails, phone numbers, SSN patterns)
- Internal URLs and private IPs
- Credentials and secrets

---

## Installation Options

```bash
# Core only
pip install media-engine

# With specific features
pip install media-engine[web]      # Dashboard
pip install media-engine[mcp]      # MCP server
pip install media-engine[pdf]      # PDF generation
pip install media-engine[all]      # Everything

# Development
git clone https://github.com/morteng/media-engine.git
cd media-engine
uv sync
```

---

## Repository Structure

```
media-engine/
├── python/
│   └── media_engine/        # Main Python package
│       ├── core/            # Config, Project, Theme
│       ├── cms/             # Document management
│       ├── video/           # Video production
│       ├── builders/        # Output generators
│       ├── quality/         # Quality checks
│       ├── security/        # Secret/PII detection
│       ├── web/             # Dashboard (FastAPI)
│       ├── mcp/             # MCP server
│       └── cli.py           # CLI interface
├── remotion/                # Motion graphics (React)
├── demo/                    # Reference project
└── pyproject.toml
```

---

## License

MIT

---

## Contributing

Contributions welcome! Please read our contributing guidelines and submit PRs.

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check python/
```
