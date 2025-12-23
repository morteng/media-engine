---
title: "Outputbyggere"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/05_builders.md"
source_content_hash: "93b5f2abb1241061"
depends_on:
  - "chapters/02_innholdsstyring"
tags:
  - byggere
  - html
  - pptx
  - xlsx
---

# Outputbyggere

Media Engine tilbyr byggere for å generere flere outputformater fra innholdskildene dine.

## Tilgjengelige byggere

| Bygger | Input | Output | Bruksområde |
|--------|-------|--------|-------------|
| HTML | Markdown | `.html` | Webdokumenter |
| PPTX | YAML/Markdown | `.pptx` | PowerPoint-presentasjoner |
| XLSX | YAML | `.xlsx` | Excel-regneark |

## HTML-bygger

HTML-byggeren konverterer Markdown til stilisert HTML med temastøtte.

### Grunnleggende bruk

```python
from media_engine.builders.html import HTMLBuilder, HTMLConfig

builder = HTMLBuilder(theme=project.theme)

# Bygg fra streng
html = builder.build(markdown_content, title="Mitt dokument")

# Bygg fra fil
html = builder.build_from_file(Path("chapter.md"))

# Lagre til fil
builder.save(html, Path("output.html"))
```

### Funksjoner

- **Temaintegrasjon**: CSS-variabler fra din `theme.yaml`
- **Innholdsfortegnelse**: Autogenerert fra overskrifter
- **Kodeutheving**: Syntaksutheving for kodeblokker
- **Mørk modus**: Automatisk via `prefers-color-scheme`
- **Utskriftsstiler**: PDF-klar ved utskrift fra nettleser

## PPTX-bygger

Generer PowerPoint-presentasjoner fra strukturert YAML.

### Slidetyper

| Type | Beskrivelse |
|------|-------------|
| `title` | Tittelslide med undertittel |
| `section` | Seksjonsdeler |
| `content` | Kulepunkter |
| `two_column` | Side-ved-side sammenligning |
| `quote` | Stort sitat med attribusjon |

## XLSX-bygger

Generer Excel-regneark fra YAML-datadefinisjoner.

### Funksjoner

- **Flere ark**: Definer flere regneark
- **Formler**: Excel-formler i celler
- **Stilisering**: Temabaserte overskriftfarger
- **Auto-bredde**: Kolonner tilpasset innhold

## CLI-byggkommandoer

```bash
# Bygg alle formater
media-engine build

# Bygg spesifikt format
media-engine build --only html

# Tving gjenoppbygging
media-engine build --force
```
