---
title: "Publishing"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/05_builders"
tags:
  - publishing
  - packaging
  - deliverables

# Hierarchy metadata
doc_type: "operations"
lifecycle: "living"
parent_document: "chapters/05_builders.md"
sequence_order: 9
hierarchy_level: 2

# Derives from builders (extends with publishing workflow)
derived_from:
  - path: "chapters/05_builders.md"
    version: "1.0.0"
    relationship: "extends"

# References output configuration
anchor_refs:
  - source: "chapters/05_builders.md"
    anchor: "supported_formats"
  - source: "chapters/05_builders.md"
    anchor: "default_output_dir"
---

# Publishing

Media Engine creates complete, self-contained packages ready for distribution.

See [Builders](05_builders.md) for how outputs are generated before publishing.

## Overview

The publish system:

- Bundles all outputs into a single directory
- Downloads and embeds fonts for offline use
- Generates navigation indexes
- Optionally creates ZIP archives
- Copies to a predictable location (Desktop/deliverables/)

## Publishing with CLI

```bash
# Publish to default location (Desktop/deliverables/{project})
media-engine publish

# Custom output directory
media-engine publish -o ./dist

# Create ZIP archive
media-engine publish --zip

# Exclude components
media-engine publish --no-fonts      # Skip font bundling
media-engine publish --no-diagrams   # Skip diagram copying
media-engine publish --no-videos     # Skip video assets
media-engine publish --no-index      # Skip navigation index
```

## Publishing with Python

```python
from media_engine import publish_project, PublishConfig, find_project

project = find_project()

config = PublishConfig(
    output_dir=Path("./dist"),
    include_fonts=True,
    include_diagrams=True,
    include_videos=True,
    generate_indexes=True,
    zip_output=True,
)

result = publish_project(project, config)

print(f"Published to: {result.output_dir}")
print(f"Documents: {result.documents_copied}")
print(f"Assets: {result.assets_copied}")
```

## Published Structure

```
deliverables/my-project/
├── en/
│   ├── proposal.html         # Combined HTML document
│   ├── pitch_deck.pptx       # PowerPoint presentation
│   ├── calculator.xlsx       # Excel spreadsheet
│   ├── diagrams/
│   │   ├── architecture_light.png
│   │   └── architecture_dark.png
│   └── videos/
│       ├── demo.props.json
│       └── demo.mp3
├── no/
│   └── ...                   # Norwegian versions
├── assets/
│   └── fonts/                # Downloaded fonts
├── index.html                # Navigation index
└── manifest.json             # Package manifest
```

## Navigation Index

When you set `generate_indexes=True`, the system creates an `index.html` with:

- Links to all documents by language
- Links to presentations and spreadsheets
- Thumbnail previews of diagrams
- Video asset listings

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `output_dir` | Desktop/deliverables | Output location |
| `include_fonts` | True | Bundle Google Fonts |
| `include_diagrams` | True | Copy diagram images |
| `include_videos` | True | Copy video assets |
| `generate_indexes` | True | Create index.html |
| `zip_output` | False | Create ZIP archive |
| `console_output` | True | Show progress |

## Publish Result

```python
@dataclass
class PublishResult:
    success: bool
    output_dir: Path
    zip_path: Optional[Path]
    documents_copied: int
    assets_copied: int
    fonts_downloaded: int
    errors: list[str]
```

## Font Bundling

The publish system downloads fonts specified in your theme:

```yaml
# theme.yaml
typography:
  heading: "Inter"
  body: "Source Sans 3"
  code: "JetBrains Mono"
```

The system downloads these fonts from Google Fonts and embeds them for offline use.

## Manifest File

The system generates a `manifest.json` with package metadata:

```json
{
  "project": "My Project",
  "version": "1.0.0",
  "published": "2025-12-16T10:30:00",
  "languages": ["en", "no"],
  "contents": {
    "documents": 5,
    "presentations": 1,
    "spreadsheets": 1,
    "diagrams": 4,
    "videos": 2
  }
}
```

## ZIP Archives

With `--zip`, the system creates a timestamped archive:

```
my-project-2025-12-16.zip
```

The ZIP contains the complete deliverable directory.

## Incremental Publishing

Publishing is always a full operation—it doesn't track incremental changes. Run it when you're ready to distribute:

```bash
# Build all outputs first
media-engine build

# Then publish
media-engine publish
```

## Error Handling

```python
result = publish_project(project, config)

if not result.success:
    for error in result.errors:
        print(f"Error: {error}")
```

Common errors:
- Missing build outputs (run `media-engine build` first)
- Font download failures (check network)
- Write permission issues (check output directory)

## Use Cases

1. **Client deliverables**: Self-contained package with all documentation
2. **Offline distribution**: Fonts and assets bundled for no-network use
3. **Archival**: ZIP with timestamp for version history
4. **Multi-language releases**: All languages in one package
