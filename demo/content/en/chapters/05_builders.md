---
title: "Output Builders"
version: "1.1.0"
status: "final"
last_modified: "2025-12-23"
freshness_days: 60
depends_on:
  - "chapters/02_content_management"
tags:
  - builders
  - html
  - pptx
  - xlsx
  - brand
  - dashboard

# Hierarchy metadata
doc_type: "implementation"
lifecycle: "living"
parent_document: "chapters/01_introduction.md"
sequence_order: 5
hierarchy_level: 1

# Derives from content management
derived_from:
  - path: "chapters/02_content_management.md"
    version: "1.0.0"
    relationship: "extends"

# Anchors - key facts defined here
anchors:
  supported_formats:
    value: "html, pdf, pptx, xlsx"
    type: string
    description: "List of output formats supported by Media Engine"
  default_output_dir:
    value: "dist"
    type: string
    description: "Default output directory for built files"

# References project name from introduction
anchor_refs:
  - source: "chapters/01_introduction.md"
    anchor: "project_name"
---

# Output Builders

Media Engine provides builders for generating multiple output formats from your content sources. For information on validating your content before building, see the [Validation chapter](08_validation.md).

## Available Builders

| Builder | Input | Output | Use Case |
|---------|-------|--------|----------|
| HTML | Markdown | `.html` | Web documents |
| PPTX | YAML/Markdown | `.pptx` | PowerPoint presentations |
| XLSX | YAML | `.xlsx` | Excel spreadsheets |

## HTML Builder

The HTML builder converts Markdown to styled HTML with theme support.

### Basic Usage

```python
from media_engine.builders.html import HTMLBuilder, HTMLConfig

builder = HTMLBuilder(theme=project.theme)

# Build from string
html = builder.build(markdown_content, title="My Document")

# Build from file
html = builder.build_from_file(Path("chapter.md"))

# Build combined document
html = builder.build_combined(
    [Path("ch1.md"), Path("ch2.md")],
    title="Full Document"
)

# Save to file
builder.save(html, Path("output.html"))
```

### Configuration Options

```python
config = HTMLConfig(
    include_toc=True,    # Generate table of contents
    footer="© 2025",     # Footer text
    lang="en",           # Document language
)

html = builder.build(content, "Title", config)
```

### Features

- **Theme integration**: CSS variables from your `theme.yaml`
- **Table of contents**: Auto-generated from headings
- **Code highlighting**: Syntax highlighting for code blocks
- **Dark mode**: Automatic via `prefers-color-scheme`
- **Print styles**: PDF-ready when printed from browser
- **Responsive**: Works on all screen sizes

## PPTX Builder

Generate PowerPoint presentations from structured YAML or Markdown.

### YAML Format

```yaml
# slides/pitch_deck.yaml
title: "My Presentation"
subtitle: "A great presentation"

slides:
  - type: title
    title: "Welcome"
    subtitle: "To our presentation"

  - type: content
    title: "Key Points"
    bullets:
      - "First point"
      - "Second point"
      - "Third point"

  - type: two_column
    title: "Comparison"
    left_title: "Before"
    left_bullets:
      - "Old way"
    right_title: "After"
    right_bullets:
      - "New way"

  - type: quote
    quote: "This is a quote."
    author: "Author Name"
```

### Slide Types

| Type | Description |
|------|-------------|
| `title` | Title slide with subtitle |
| `section` | Section divider |
| `content` | Bullet points |
| `two_column` | Side-by-side comparison |
| `quote` | Large quote with attribution |

### Building Presentations

```python
from media_engine.builders.pptx import PPTXBuilder

builder = PPTXBuilder(theme=project.theme)

# Build from YAML
builder.build_from_yaml(Path("slides/pitch_deck.yaml"))

# Build from Markdown (slides separated by ---)
builder.build_from_markdown(Path("slides/pitch_deck.md"))

# Save
output_path = builder.save(Path("output/pitch_deck.pptx"))
```

## XLSX Builder

Generate Excel spreadsheets from YAML data definitions.

### Data Format

```yaml
# data/calculator.yaml
title: "Project Calculator"

sheets:
  - name: "Summary"
    headers:
      - "Item"
      - "Quantity"
      - "Price"
      - "Total"
    rows:
      - ["Product A", 10, 100, "=B2*C2"]
      - ["Product B", 5, 200, "=B3*C3"]
    formulas:
      D5: "=SUM(D2:D4)"

  - name: "Details"
    headers:
      - "Category"
      - "Value"
    rows:
      - ["Category 1", 500]
      - ["Category 2", 750]
```

### Building Spreadsheets

```python
from media_engine.builders.xlsx import XLSXBuilder

builder = XLSXBuilder(theme=project.theme)
builder.build_from_yaml(Path("data/calculator.yaml"))
output_path = builder.save(Path("output/calculator.xlsx"))
```

### Features

- **Multiple sheets**: Define multiple worksheets
- **Formulas**: Excel formulas in cells
- **Styling**: Theme-based header colors
- **Auto-width**: Columns sized to content

## CLI Build Commands

Build all formats:

```bash
# Build all formats for all languages
media-engine build

# Build specific format
media-engine build --only html
media-engine build --only pptx

# Build specific language
media-engine build --lang en

# Force rebuild (ignore cache)
media-engine build --force
```

## Smart Caching

Builders track dependencies and only rebuild when sources change:

```python
# Check if rebuild needed
if project.should_rebuild("en/html", dependencies):
    html = builder.build(content)
    project.record_build("en/html", output_path, dependencies)
```

The build system computes hashes of source files to determine if outputs are stale.

## Brand Integration

All builders support brand-aware styling via `brand.yaml`:

```python
from media_engine.brand import BrandContext

# Create brand context
brand = BrandContext(profile=project.brand_profile)

# Use with builders
html_builder = HTMLBuilder(brand=brand)
pptx_builder = PPTXBuilder(brand=brand)
xlsx_builder = XLSXBuilder(brand=brand)
```

Brand integration provides:
- **Colors**: Primary, secondary, accent, semantic colors
- **Typography**: Font families for headings, body, and code
- **Logos**: Automatic format conversion (SVG to PNG for PPTX)
- **Dark mode**: Automatic dark variant styling

See the Brand chapter for detailed configuration.

## Dashboard Build Page

The web dashboard provides a visual build interface at `/build`:

| Feature | Description |
|---------|-------------|
| Format Selection | Choose HTML, PPTX, XLSX individually or all |
| Language Filtering | Build specific languages |
| Progress Indicators | Real-time build status via WebSocket |
| Output Preview | View and download built artifacts |
| Build History | Recent builds with timestamps |
| Error Display | Detailed error messages with file references |

Launch with `media-engine dashboard` and navigate to Build.
