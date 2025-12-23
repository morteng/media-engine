---
title: "Ressurser og fonter"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/11_assets.md"
source_content_hash: "be98807030fd0945"
depends_on:
  - "chapters/05_byggere"
tags:
  - ressurser
  - fonter
  - pakking
---

# Ressurser og fonter

Media Engine administrerer prosjektressurser og kan laste ned fonter for offline-bruk.

## Ressursstruktur

Prosjekter organiserer ressurser i en dedikert mappe:

```
project/
├── assets/
│   ├── brand/
│   │   ├── logo.svg
│   │   └── icon.png
│   ├── images/
│   │   └── diagram.png
│   └── fonts/
│       └── (nedlastede fonter)
├── content/
└── project.yaml
```

## Konfigurasjon

Spesifiser ressursstien i `project.yaml`:

```yaml
paths:
  assets: "assets"
```

## Google Fonts

Last ned fonter fra Google Fonts for offline-bruk:

```python
from media_engine import download_google_fonts

fonts_downloaded = download_google_fonts(
    font_names=["Inter", "Source Sans 3", "JetBrains Mono"],
    output_dir=project.assets_dir / "fonts",
)
```

### Temabasert nedlasting

```python
from media_engine.assets import download_theme_fonts

# Last ned alle fonter referert i theme.yaml
fonts = download_theme_fonts(project.theme, project.assets_dir / "fonts")
```

## Ressurspakking

Pakk alle prosjektressurser i en enkelt mappe:

```python
from media_engine import bundle_project_assets

result = bundle_project_assets(
    project,
    output_dir=Path("./bundled"),
    include_fonts=True,
)

print(f"Pakket {result.files_copied} filer")
```

## Merkevareressurser

Lagre merkevareressurser for konsistent bruk:

```
assets/brand/
├── logo.svg           # Primærlogo
├── logo-dark.svg      # Mørk modus-variant
├── favicon.ico        # Nettleserfavikon
└── colors.json        # Merkefargedefinisjoner
```

## Beste praksis

1. **Organiser etter type**: Separer merkevare, bilder, fonter
2. **Bruk SVG**: Skalerbar grafikk for diagrammer og logoer
3. **Pakk fonter**: Sikre offline-kapabilitet
4. **Versjonér logoer**: Behold varianter (lys, mørk, kvadratisk)
