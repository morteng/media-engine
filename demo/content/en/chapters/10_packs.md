---
title: "Audience Packs"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/09_publishing"
tags:
  - packs
  - audience
  - distribution
---

# Audience Packs

Media Engine can generate curated content packages tailored for specific audiences.

## Overview

Audience packs are subsets of your project content, bundled for a specific purpose:

- **Investor pack**: Financial highlights, pitch deck, key metrics
- **Pilot pack**: Technical documentation, setup guides, support materials

## Generating Packs

Generate audience-specific content packages using the CLI or Python API.

### CLI

```bash
# Generate investor materials
media-engine pack investor

# Generate pilot customer materials
media-engine pack pilot

# Custom output directory
media-engine pack investor -o ./investor-materials

# Don't create ZIP (directory only)
media-engine pack investor --no-zip
```

### Python API

```python
from media_engine import generate_investor_pack, generate_pilot_pack, find_project

project = find_project()

# Investor pack
result = generate_investor_pack(
    project,
    output_dir=Path("./dist"),
    create_zip=True,
    console_output=True,
)

print(f"Created: {result.output_path}")
print(f"Items: {result.items_included}")

# Pilot pack
result = generate_pilot_pack(project, output_dir=Path("./dist"))
```

## Pack Contents

Each pack type includes specific materials tailored for its audience.

### Investor Pack

| Item | Description |
|------|-------------|
| `pitch_deck.pptx` | Presentation slides |
| `executive_summary.pdf` | One-page overview |
| `calculator.xlsx` | Financial model |
| `diagrams/` | Architecture visuals |
| `README.txt` | Pack contents guide |

### Pilot Pack

| Item | Description |
|------|-------------|
| `documentation.pdf` | Full technical docs |
| `setup_guide.html` | Getting started guide |
| `api_reference.html` | API documentation |
| `videos/` | Demo videos and assets |
| `support.txt` | Contact information |

## Pack Result

```python
@dataclass
class PackResult:
    success: bool
    output_path: Path
    items_included: int
    items_missing: list[str]
    zip_path: Optional[Path]
```

## Missing Items

Packs report missing content:

```python
result = generate_investor_pack(project, output_dir)

if result.items_missing:
    print("Warning: Some items not found:")
    for item in result.items_missing:
        print(f"  - {item}")
```

Missing items don't cause failure—packs are generated with available content.

## Custom Pack Types

Define custom packs in your project:

```python
from media_engine.packs import PackGenerator, PackConfig

config = PackConfig(
    name="partner-pack",
    include_patterns=[
        "chapters/01_*.md",
        "chapters/02_*.md",
        "slides/partner_deck.yaml",
    ],
    exclude_patterns=[
        "**/internal/**",
        "**/*_draft.md",
    ],
)

generator = PackGenerator(project)
result = generator.generate(config, output_dir)
```

## Pack Manifest

Each pack includes a manifest:

```json
{
  "pack_type": "investor",
  "project": "My Project",
  "generated": "2025-12-16T10:30:00",
  "items": [
    {"name": "pitch_deck.pptx", "type": "presentation"},
    {"name": "calculator.xlsx", "type": "spreadsheet"}
  ],
  "missing": []
}
```

## Use Cases

Common scenarios for using audience packs in your workflow.

### Investor Outreach

```bash
# Generate and email to investors
media-engine pack investor
# Creates: investor-pack-2025-12-16.zip
```

### Customer Pilots

```bash
# Create pilot materials for each customer
media-engine pack pilot -o ./pilots/acme-corp
media-engine pack pilot -o ./pilots/globex-inc
```

### Automated Distribution

```python
import smtplib
from media_engine import generate_investor_pack

result = generate_investor_pack(project, output_dir)

if result.success and result.zip_path:
    # Attach ZIP to email
    send_email(
        to="investor@example.com",
        subject="Project Materials",
        attachment=result.zip_path,
    )
```

## Pack Naming

Output files follow this pattern:

- **Directory**: `{pack_type}-pack/`
- **ZIP file**: `{pack_type}-pack-{date}.zip`

Example: `investor-pack-2025-12-16.zip`

## Quality Checks

Before generating packs, consider running:

```bash
# Ensure content is complete
media-engine quality

# Build all outputs
media-engine build

# Then generate pack
media-engine pack investor
```

This ensures the pack contains final, validated content.
