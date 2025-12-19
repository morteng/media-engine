---
title: "Media Engine Documentation"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 90
tags:
  - index
  - documentation
  - landing
---

# Media Engine

**Agent-Operated Media Production Framework**

Write content once in Markdown. Generate HTML documents, PDF reports, PowerPoint presentations, Excel spreadsheets, and full video productions—automatically.

---

## Quick Start

```bash
# Install
pip install media-engine[all]

# Initialize a new project
media-engine init

# Build all outputs
media-engine build

# Check quality
media-engine quality

# Launch dashboard
media-engine dashboard
```

---

## Documentation

### Getting Started

| Chapter | Description |
|---------|-------------|
| [Introduction](chapters/01_introduction.md) | Overview of Media Engine and its capabilities |
| [Content Management](chapters/02_content_management.md) | Markdown content, frontmatter, and document organization |
| [Video Production](chapters/03_video_production.md) | Scripts, voiceovers, captions, and motion graphics |

### Core Features

| Chapter | Description |
|---------|-------------|
| [Quality Checks](chapters/04_quality_checks.md) | Readability, links, freshness, and validation |
| [Builders](chapters/05_builders.md) | HTML, PDF, PPTX, XLSX generation |
| [Diagrams](chapters/06_diagrams.md) | Technical diagram generation |
| [Search Indexing](chapters/07_search_indexing.md) | Full-text search capabilities |
| [Validation](chapters/08_validation.md) | Schema and content validation |

### Publishing & Deployment

| Chapter | Description |
|---------|-------------|
| [Publishing](chapters/09_publishing.md) | Packaging deliverables |
| [Audience Packs](chapters/10_packs.md) | Investor, pilot, and custom packs |
| [Assets](chapters/11_assets.md) | Font downloading and bundling |

### Reference

| Chapter | Description |
|---------|-------------|
| [CLI Reference](chapters/12_cli_reference.md) | Complete command-line documentation |
| [Security](chapters/13_security.md) | Secret detection and PII scanning |
| [Integrations](chapters/14_integrations.md) | MCP server, web dashboard, APIs |
| [Analysis](chapters/15_analysis.md) | Readability, gaps, and reporting |

### Showcase

| Chapter | Description |
|---------|-------------|
| [GitHub Showcase](chapters/16_github_showcase.md) | Comprehensive demo content documentation |

---

## Additional Content

### Video Scripts

| Script | Duration | Description |
|--------|----------|-------------|
| [Walkthrough](scripts/walkthrough.yaml) | 90 sec | Complete feature walkthrough with scenes |

### Presentations

| Deck | Slides | Description |
|------|--------|-------------|
| [GitHub Showcase](slides/github_showcase.yaml) | 25 | Complete feature presentation |
| [Pitch Deck](slides/pitch_deck.yaml) | 12 | Investor-style overview |

### Diagrams

| Diagram | Description |
|---------|-------------|
| [Full Architecture](diagrams/full_architecture.yaml) | Complete system architecture |
| [Video Pipeline](diagrams/video_pipeline.yaml) | Video production workflow |
| [Architecture](diagrams/architecture.yaml) | High-level system overview |

### Interactive Demos

| Demo | Type | Description |
|------|------|-------------|
| [Feature Showcase](demos/feature_showcase.yaml) | Comparison | All features by category |
| [CLI Playground](demos/cli_playground.yaml) | Code Playground | Interactive terminal |
| [Pricing Calculator](demos/pricing_calculator.yaml) | Calculator | Project cost estimator |
| [Feature Comparison](demos/feature_comparison.yaml) | Comparison | Plan comparison table |
| [Code Playground](demos/code_playground.yaml) | Code Playground | Live HTML/CSS/JS editor |
| [Dashboard Demo](demos/dashboard-demo.yaml) | Scene Capture | Dashboard UI state definitions |
| [Project Timeline](demos/project_timeline.yaml) | Timeline | Development milestones |
| [Feature Quiz](demos/feature_quiz.yaml) | Quiz | Knowledge check questions |
| [Health Metrics](demos/health_metrics.yaml) | Data Viz | Project health radar chart |
| [Project Form](demos/project_form.yaml) | Form Demo | Configuration with validation |
| [API Explorer](demos/api_explorer.yaml) | API Explorer | Dashboard API endpoints |
| [Architecture](demos/architecture_diagram.yaml) | Interactive Diagram | Clickable system components |

### Data Files

| File | Sheets | Description |
|------|--------|-------------|
| [Feature Matrix](data/feature_matrix.yaml) | 6 | Complete feature documentation |
| [ROI Calculator](data/calculator.yaml) | 3 | Productivity metrics |

---

## Output Formats

Media Engine generates:

| Format | Extension | Builder | Use Case |
|--------|-----------|---------|----------|
| HTML | `.html` | HTMLBuilder | Web documentation |
| PDF | `.pdf` | PDFBuilder | Print-ready reports |
| PowerPoint | `.pptx` | PPTXBuilder | Presentations |
| Excel | `.xlsx` | XLSXBuilder | Data exports |
| Video | `.mp4` | VideoBuilder | Product demos |
| Captions | `.vtt` | CaptionBuilder | Accessibility |
| Diagrams | `.png`/`.svg` | DiagramBuilder | Technical illustrations |

---

## Languages

This documentation is available in:

- **English** (current)
- [Norwegian](../no/index.md)

---

## Links

- **GitHub**: [github.com/example/media-engine](https://github.com/example/media-engine)
- **PyPI**: [pypi.org/project/media-engine](https://pypi.org/project/media-engine)
- **Documentation**: [media-engine.dev](https://media-engine.dev)

---

## Philosophy

> "AI handles the busywork. You make the calls."

Media Engine automates the tedious parts of content production—formatting, rendering, translation tracking, quality checks—so you can focus on what matters: the content itself.

---

*Built with Media Engine v1.0.0*
