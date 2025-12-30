---
title: "GitHub README Showcase"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 90
tags:
  - showcase
  - video
  - marketing
  - demo
---

# GitHub README Showcase

This chapter describes the showcase content we built for the Media Engine GitHub README. We designed this showcase to show all major features through video scripts, diagrams, interactive demos, presentations, and data spreadsheets.

See [Video Production](03_video_production.md) for how to build these videos.

## Overview

We assembled the showcase package with the following components. Each component serves a specific purpose in demonstrating Media Engine capabilities:

| Asset Type | File | Duration/Size | Purpose |
|------------|------|---------------|---------|
| Main Video Script | `scripts/github_readme_showcase.yaml` | ~3 minutes | Comprehensive feature demonstration |
| Teaser Video | `scripts/teaser_30s.yaml` | 30 seconds | Quick social media hook |
| Architecture Diagram | `diagrams/full_architecture.yaml` | - | System overview visualization |
| Pipeline Diagram | `diagrams/video_pipeline.yaml` | - | Video production flow |
| Feature Demo | `demos/feature_showcase.yaml` | - | Interactive feature comparison |
| CLI Playground | `demos/cli_playground.yaml` | - | Terminal command simulator |
| Slide Deck | `slides/github_showcase.yaml` | 25 slides | Presentation format |
| Feature Matrix | `data/feature_matrix.yaml` | 6 sheets | Complete feature documentation |

## Main Showcase Video (3 minutes)

The main showcase video (`github_readme_showcase.yaml`) follows five acts:

### Act 1: Introduction (0:00 - 0:25)
- **Opening Hook**: Problem statement about content creation overhead
- **Title Reveal**: Media Engine branding with copper-sweep transition
- **Tagline**: "Write Once, Publish Everywhere" with icon cascade

### Act 2: Core Features Demo (0:25 - 1:30)
- **Content Management**: CMS module, frontmatter, dependencies
- **Multi-Format Builders**: HTML, PDF, PPTX, XLSX, diagrams
- **Video Production**: Full pipeline from script to render
- **Browser Capture**: Playwright-based demo recording
- **Translation Tracking**: Multi-language status matrix

### Act 3: Quality & Security (1:30 - 2:00)
- **Quality Checks**: Readability, links, references, freshness
- **Security Scanning**: Secret detection, PII, audit trails
- **Provenance & Approval**: Document workflow states

### Act 4: Developer Experience (2:00 - 2:30)
- **CLI Interface**: Command demonstrations
- **MCP Server**: AI agent integration (20+ tools)
- **Web Dashboard**: Browser-based management UI

### Act 5: Closing (2:30 - 3:00)
- **Statistics**: Animated stat counters
- **Getting Started**: Installation and quick start
- **Call to Action**: GitHub star, community links

### Scene Types Used

```yaml
# Intro scenes with logo animation
- type: intro
  visual:
    show_logo: true
    animation: "copper-sweep"

# Feature cards with icons
- type: feature
  visual:
    feature_card:
      icon: "document"
      highlight: "copper"

# Screen recordings with overlays
- type: demo
  visual:
    screen_recording:
      description: "Terminal showing command"
    overlay:
      type: "callout"

# Statistics with count-up animation
- type: content
  visual:
    stat_grid:
      animation: "count_up"
```

## Teaser Video (30 seconds)

We designed the teaser (`teaser_30s.yaml`) for social media and quick README embeds:

1. **Hook** (4s): "What if your content could build itself?"
2. **Pain** (5s): Show manual content creation burden
3. **Solution** (3s): Media Engine logo punch-in
4. **Demo** (8s): One command, multiple outputs
5. **AI Angle** (4s): MCP server integration
6. **CTA** (6s): Install command, GitHub link

### Render Outputs
- MP4 video (1920x1080 @ 30fps)
- Animated GIF (for README embed)

## Architecture Diagrams

### Full Architecture (`full_architecture.yaml`)

Six-layer system diagram showing:

1. **Input Sources**: Markdown, YAML, Scripts, Assets, Config
2. **Core Processing**: CMS, Validation, Video Pipeline, Asset Manager
3. **Video Pipeline**: Voiceover, Captions, Remotion, Capture
4. **Builders**: HTML, PDF, PPTX, XLSX, Diagram, Video
5. **Quality & Security**: Checks, Scanner, Links, Readability, Translation
6. **Interfaces**: CLI, MCP Server, Web Dashboard, Python API
7. **Output Formats**: HTML, PDF, PPTX, XLSX, MP4, VTT

### Video Pipeline (`video_pipeline.yaml`)

Flow diagram showing:
- Script parsing
- Parallel generation (voiceover, captions, props)
- ElevenLabs API integration
- Audio caching system
- Remotion rendering
- Output files (MP4, VTT)

## Interactive Demos

### Feature Showcase (`feature_showcase.yaml`)

Comparison-type demo showing six capability categories:
- Content Management (7 features)
- Document Generation (7 features)
- Video Production (7 features)
- Quality Assurance (7 features)
- Security (7 features)
- Integration (7 features)

Each category includes feature checkmarks and descriptions.

### CLI Playground (`cli_playground.yaml`)

Terminal simulator with pre-configured commands:
- `help` - Command overview
- `status` - Project status
- `build` - Build outputs
- `quality` - Quality checks
- `translation status` - Translation matrix
- `security` - Security scan
- `dashboard` - Web UI launch

Users can type commands or click quick-access buttons.

## Slide Deck

The presentation (`github_showcase.yaml`) contains 25 slides:

1. Title slide
2. Problem statement
3. Philosophy quote
4-6. Core capabilities (CMS, transforms, builders)
7-9. Video production (pipeline, components, scripts)
10-12. Quality & security
13-16. Developer experience (CLI, MCP, dashboard, API)
17-19. Getting started (install, quick start, structure)
20-21. Benefits comparison
22. Use cases
23. Philosophy quote
24. Next steps
25. Closing

### Slide Types

```yaml
# Title slides
- type: title

# Section dividers
- type: section

# Bullet content
- type: content
  bullets: [...]

# Side-by-side comparison
- type: two_column
  left_bullets: [...]
  right_bullets: [...]

# Large quote
- type: quote
  quote: "..."
  author: "..."
```

## Data Spreadsheet

The feature matrix (`feature_matrix.yaml`) contains six sheets:

### Sheet 1: Feature Matrix
Complete feature listing with:
- Feature name
- Category
- Stability status
- CLI command
- MCP tool name

### Sheet 2: Output Formats
All supported output formats with:
- Format name and extension
- Builder class
- Theming support
- Multi-language support
- Use case description

### Sheet 3: MCP Tools
All 20+ MCP tools with:
- Tool name
- Category
- Description

### Sheet 4: CLI Commands
Complete CLI reference with:
- Command syntax
- Description
- Common options

### Sheet 5: Productivity Metrics
Time savings analysis with:
- Task description
- Manual time (hours)
- Automated time (hours)
- Percentage saved

### Sheet 6: Language Support
Supported languages with:
- Language name and code
- TTS voice availability
- Translation support
- Notes

## Building the Showcase

To generate all showcase outputs:

```bash
# Build all outputs
media-engine build

# Build specific components
media-engine build --video    # Video scripts → MP4
media-engine build --pptx     # Slides → PowerPoint
media-engine build --xlsx     # Data → Excel
media-engine build --diagrams # Diagrams → PNG/SVG
media-engine demos build      # Demos → HTML
```

## Rendering Videos

The video scripts work with the Remotion renderer:

```bash
# Generate voiceover and props
media-engine build --video

# Render with Remotion (if installed)
cd remotion
npx remotion render src/index.tsx \
  --props ../output/github_readme_showcase_props.json \
  --output ../output/github_readme_showcase.mp4
```

## Motion Graphics Components Used

The showcase scripts reference these Remotion components:

| Component | Usage |
|-----------|-------|
| `TitleCard` | Logo reveals, section titles |
| `TextReveal` | Word-by-word text animations |
| `StatCounter` | Animated statistics |
| `FeatureCard` | Feature showcase cards |
| `Transition` | Scene transitions (copper-sweep, fade, wipe) |
| `Background` | Dark, gradient, grid, particles |
| `Overlay` | Callouts, stats, lower thirds |

## Voiceover Notes

Both video scripts use ElevenLabs TTS with:
- Professional voice style
- Medium pace (main showcase)
- Fast/energetic pace (teaser)
- Smart pause calculation based on punctuation

We wrote the voiceover text for:
- Clear pronunciation
- Natural rhythm
- Emphasis on key terms (Media Engine, automatically, powerful)

Voiceover settings are configured in `project.yaml` and script YAML files.

## Design System

All showcase content uses the "Copper & Cream" design system:

```yaml
colors:
  primary: "#2c2522"   # Warm espresso
  accent: "#c45c3c"    # Copper terracotta
  background: "#fdfbf9" # Warm cream

typography:
  heading: "Fraunces"
  body: "Source Sans 3"
  code: "JetBrains Mono"
```

Design systems are configured in `brand.yaml` at the project root.

## Customization

Adapt the showcase for your own project:

1. **Branding**: Update `theme.yaml` colors and fonts
2. **Voice**: Set `voice_id` in project configuration
3. **Content**: Change scene text and visuals
4. **Statistics**: Update stat values in closing scenes
5. **Links**: Change GitHub and documentation URLs

## File Locations

```
demo/content/en/
├── scripts/
│   ├── github_readme_showcase.yaml  # Main 3-minute video
│   └── teaser_30s.yaml              # 30-second teaser
├── diagrams/
│   ├── full_architecture.yaml       # System architecture
│   └── video_pipeline.yaml          # Video production flow
├── demos/
│   ├── feature_showcase.yaml        # Feature comparison
│   └── cli_playground.yaml          # Terminal simulator
├── slides/
│   └── github_showcase.yaml         # 25-slide presentation
├── data/
│   └── feature_matrix.yaml          # 6-sheet spreadsheet
└── chapters/
    └── 16_github_showcase.md        # This documentation
```
