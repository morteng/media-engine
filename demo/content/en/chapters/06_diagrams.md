---
title: "Diagram Generation"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/05_builders"
tags:
  - diagrams
  - matplotlib
  - visualization
---

# Diagram Generation

Media Engine includes a diagram generator that creates professional visualizations from YAML definitions.

## Overview

The diagram system uses Matplotlib to render box-and-arrow diagrams commonly used in technical documentation:

- Architecture diagrams
- Flow charts
- System overviews
- Component relationships

## YAML Definition Format

Diagrams are defined in YAML files:

```yaml
# diagrams/architecture.yaml
title: "System Architecture"
description: "High-level system overview"

config:
  width: 14        # Figure width in inches
  height: 10       # Figure height
  dpi: 150         # Resolution
  format: png      # Output format
  font_scale: 1.0  # Text size multiplier

boxes:
  - id: frontend
    label: "Frontend\nReact App"
    x: 0
    y: 4
    width: 2
    height: 1
    color: "#e8f4f8"

  - id: api
    label: "API Server"
    x: 3
    y: 4
    width: 2
    height: 1

  - id: database
    label: "Database"
    x: 6
    y: 4
    width: 2
    height: 1

arrows:
  - from: frontend
    to: api
    label: "REST"

  - from: api
    to: database
    label: "SQL"
```

## Box Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier |
| `label` | string | Display text (supports `\n`) |
| `x` | float | X position |
| `y` | float | Y position |
| `width` | float | Box width |
| `height` | float | Box height |
| `color` | string | Fill color (hex) |

## Arrow Properties

| Property | Type | Description |
|----------|------|-------------|
| `from` | string | Source box ID |
| `to` | string | Target box ID |
| `label` | string | Arrow label |
| `style` | string | `->` or `<->` |

## Generating Diagrams

Generate diagrams from YAML definitions using either the CLI or Python API.

### Python API

```python
from media_engine.diagrams import DiagramGenerator, DiagramDefinition

# Load definition
definition = DiagramDefinition.from_yaml(Path("diagrams/architecture.yaml"))

# Create generator with theme
generator = DiagramGenerator(theme=project.theme)

# Generate both themes
light_path, dark_path = generator.generate_both_themes(
    definition,
    output_dir=Path("output/diagrams"),
    base_name="architecture"
)
# Creates: architecture_light.png, architecture_dark.png
```

### CLI

```bash
# Build all diagrams
media-engine build --only diagrams

# Diagrams are generated in output/{lang}/diagrams/
```

## Theme Integration

The diagram generator uses your theme colors:

- **Light mode**: Uses `theme.colors.background`, `theme.colors.text`
- **Dark mode**: Uses `theme.dark.background`, `theme.dark.text`
- **Accent colors**: Arrow heads and highlights

Both light and dark versions are generated automatically for each diagram.

## Styling Options

Customize diagram appearance with colors, fonts, and spacing.

### Custom Box Colors

```yaml
boxes:
  - id: highlight
    label: "Important"
    color: "#ffcc00"    # Yellow highlight
```

### Multi-line Labels

```yaml
boxes:
  - id: service
    label: "Auth Service\n(OAuth 2.0)"
```

### Bidirectional Arrows

```yaml
arrows:
  - from: a
    to: b
    style: "<->"
    label: "sync"
```

## Output Formats

The generator supports multiple output formats:

| Format | Use Case |
|--------|----------|
| `png` | Web and documents |
| `svg` | Scalable graphics |
| `pdf` | Print and LaTeX |

Configure in the YAML:

```yaml
config:
  format: svg
```

## Best Practices

1. **Consistent positioning**: Use a grid system for alignment
2. **Readable labels**: Keep labels short, use `\n` for multi-line
3. **Color meaning**: Use consistent colors for component types
4. **Both themes**: Always generate light and dark versions

## Example: Architecture Diagram

```yaml
title: "Media Engine Architecture"

boxes:
  # Input Layer
  - id: markdown
    label: "Markdown"
    x: 0
    y: 3
    width: 1.5
    height: 0.8

  - id: yaml
    label: "YAML"
    x: 2
    y: 3
    width: 1.5
    height: 0.8

  # Processing Layer
  - id: engine
    label: "Media Engine"
    x: 1
    y: 1.5
    width: 2.5
    height: 1
    color: "#e8f4f8"

  # Output Layer
  - id: html
    label: "HTML"
    x: 0
    y: 0
    width: 1
    height: 0.6

  - id: pptx
    label: "PPTX"
    x: 1.2
    y: 0
    width: 1
    height: 0.6

  - id: video
    label: "Video"
    x: 2.4
    y: 0
    width: 1
    height: 0.6

arrows:
  - from: markdown
    to: engine
  - from: yaml
    to: engine
  - from: engine
    to: html
  - from: engine
    to: pptx
  - from: engine
    to: video
```

This creates a clear visual showing the transformation from inputs to outputs.
