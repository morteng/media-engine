---
title: "Diagramgenerering"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/06_diagrams.md"
source_version: "1.0.0"
depends_on:
  - "chapters/05_byggere"
tags:
  - diagrammer
  - matplotlib
  - visualisering
---

# Diagramgenerering

Media Engine inkluderer en diagramgenerator som lager profesjonelle visualiseringer fra YAML-definisjoner.

## Oversikt

Diagramsystemet bruker Matplotlib for å tegne boks-og-pil-diagrammer vanlig brukt i teknisk dokumentasjon:

- Arkitekturdiagrammer
- Flytskjemaer
- Systemoversikter
- Komponentrelasjoner

## YAML-definisjonsformat

Diagrammer defineres i YAML-filer:

```yaml
title: "Systemarkitektur"
description: "Høynivå systemoversikt"

config:
  width: 14
  height: 10
  dpi: 150
  format: png

boxes:
  - id: frontend
    label: "Frontend\nReact App"
    x: 0
    y: 4
    width: 2
    height: 1

  - id: api
    label: "API Server"
    x: 3
    y: 4
    width: 2
    height: 1

arrows:
  - from: frontend
    to: api
    label: "REST"
```

## Boksegenskaper

| Egenskap | Type | Beskrivelse |
|----------|------|-------------|
| `id` | streng | Unik identifikator |
| `label` | streng | Visningstekst (støtter `\n`) |
| `x`, `y` | tall | Posisjon |
| `width`, `height` | tall | Dimensjoner |
| `color` | streng | Fyllfarge (hex) |

## Temaintegrasjon

Diagramgeneratoren bruker dine temafarger:

- **Lys modus**: Bruker `theme.colors.background`, `theme.colors.text`
- **Mørk modus**: Bruker `theme.dark.background`, `theme.dark.text`

Både lyse og mørke versjoner genereres automatisk for hvert diagram.

## Generere diagrammer

```bash
# Bygg alle diagrammer
media-engine build --only diagrams

# Diagrammer genereres i output/{lang}/diagrams/
```
