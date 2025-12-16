# Media Engine

Agent-based media production framework for automated content generation.

## Features

- **CMS** - Document management with frontmatter, versioning, and freshness tracking
- **Video** - Timeline sequencing, screen capture, voiceover generation, captions
- **Diagrams** - Matplotlib-based diagram generation with light/dark theming
- **Builders** - HTML, PowerPoint, and Excel generation with theming
- **Templates** - Professional HTML templates with sidebar, theme toggle, progress bar
- **Assets** - Google Fonts downloading, asset bundling for offline use
- **Quality** - Placeholder detection, terminology consistency, encoding validation
- **Search** - Full-text search index with relevance scoring
- **Validation** - Schema validation for frontmatter, reference and link checking
- **Packs** - Curated ZIP bundles for specific audiences (investor, pilot)
- **Publish** - Self-contained deliverable packages with navigation indexes
- **Remotion** - React-based motion graphics components

## Installation

```bash
# Clone the repository
git clone https://github.com/morteng/media-engine.git
cd media-engine

# Install Python dependencies
uv sync

# Install Remotion dependencies (optional)
cd remotion && npm install
```

## CLI Usage

```bash
# Initialize a new project
media-engine init my-project

# Show project status
media-engine status              # Full dashboard
media-engine status docs         # Document status
media-engine status videos       # Video production status
media-engine status quality      # Quality check summary

# Build outputs
media-engine build               # Build all formats
media-engine build --only html   # Build HTML only
media-engine build --force       # Force rebuild

# Quality checks
media-engine quality             # Run quality checks
media-engine quality --json      # JSON output

# Search documents
media-engine search "query"      # Search project content
media-engine search "api" --limit 10  # Limit results
media-engine index               # Build/update search index

# Validate content
media-engine validate            # Full schema + reference validation
media-engine validate --refs-only  # Only check references
media-engine validate --schema custom.yaml  # Custom schema

# Generate audience packs
media-engine pack investor       # Investor materials ZIP
media-engine pack pilot          # Pilot customer materials ZIP
media-engine pack investor -o ./dist  # Custom output

# Publish deliverables
media-engine publish             # Full self-contained package
media-engine publish --zip       # Create ZIP archive
media-engine publish -o ./dist   # Custom output directory
```

## Quick Start

### Document Management

```python
from media_engine import Document, DocumentCollection, find_project

# Find and load project
project = find_project()

# Load documents
for doc in project.list_chapters("en"):
    print(f"{doc.title}: v{doc.version} - {doc.freshness_status}")
```

### Video Timeline

```python
from media_engine.video import Timeline, TimelineClip

# Create timeline
timeline = Timeline(fps=30)
timeline.add_clip(TimelineClip(
    source="demo.mp4",
    start_frame=0,
    duration_frames=300
))

# Export FFmpeg command
ffmpeg_cmd = timeline.export_ffmpeg("output.mp4")
```

### Quality Checks

```python
from media_engine import run_quality_checks, find_project

project = find_project()
report = run_quality_checks(project)

print(f"Checked {report.files_checked} files")
print(f"Found {report.error_count} errors, {report.warning_count} warnings")
```

### Publishing

```python
from media_engine import publish_project, PublishConfig, find_project

project = find_project()
config = PublishConfig(
    output_dir=Path("./dist"),
    include_fonts=True,
    generate_indexes=True,
    zip_output=True,
)

result = publish_project(project, config)
print(f"Published {result.documents_copied} documents")
```

### Search Index

```python
from media_engine import build_search_index, find_project

project = find_project()
index = build_search_index(project)

# Search with relevance scoring
results = index.search("authentication", limit=10)
for result in results:
    print(f"{result.score:.0f} - {result.entry.title}")

# Save/load index
index.save("search_index.json")
```

### Validation

```python
from media_engine import validate_project, find_project

project = find_project()
report = validate_project(project, schema_path=Path("schema.yaml"))

print(f"Files: {report.files_checked}")
print(f"Errors: {report.error_count}, Warnings: {report.warning_count}")

for issue in report.issues:
    print(f"  {issue.severity}: {issue.file_path.name} - {issue.message}")
```

### Audience Packs

```python
from media_engine import generate_investor_pack, generate_pilot_pack, find_project

project = find_project()

# Generate investor materials ZIP
result = generate_investor_pack(project, output_dir=Path("./dist"))
print(f"Created {result.output_path} ({result.items_included} items)")

# Generate pilot customer pack
result = generate_pilot_pack(project, create_zip=True)
```

### Remotion Components

```tsx
import { TitleCard, StatCounter, Background } from '@media-engine/remotion';

export const MyVideo = () => (
  <>
    <Background variant="gradient" />
    <TitleCard title="My Title" tagline="Subtitle here" />
    <StatCounter value={100} suffix="%" label="Completion" />
  </>
);
```

## Project Structure

```
media-engine/
├── python/
│   ├── media_engine/
│   │   ├── cms/          # Document management
│   │   ├── video/        # Video production pipeline
│   │   ├── diagrams/     # Diagram generation
│   │   ├── builders/     # HTML, PPTX, XLSX builders
│   │   ├── templates/    # Professional HTML templates
│   │   ├── assets/       # Font downloading, bundling
│   │   ├── quality/      # Quality checks
│   │   ├── search/       # Full-text search indexing
│   │   ├── validation/   # Schema and reference validation
│   │   ├── packs/        # Audience pack generators
│   │   ├── publish/      # Deliverable packaging
│   │   ├── status/       # Project dashboards
│   │   ├── core/         # Config, theme, project
│   │   └── cli.py        # Command-line interface
│   └── tests/            # Test suite
├── remotion/
│   └── src/
│       ├── components/   # Motion graphics
│       └── lib/          # Animation utilities
├── demo/                 # Demo project
└── pyproject.toml
```

## Configuration

Create a `project.yaml` in your project root:

```yaml
project:
  name: "My Project"
  description: "Project description"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"
      voice_id: "your-elevenlabs-voice-id"

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

Create a `theme.yaml` for design tokens:

```yaml
name: "My Theme"

colors:
  primary: "#2c2522"
  secondary: "#4a4340"
  accent: "#c45c3c"
  background: "#fdfbf9"
  text: "#2c2522"

  dark:
    background: "#1a1816"
    text: "#f5f2ef"
    accent: "#d4775a"

typography:
  heading: "Fraunces"
  body: "Source Sans 3"
  code: "JetBrains Mono"
  base_size: 16
  scale: 1.25
```

## License

MIT
