---
title: "Publisering"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/09_publishing.md"
source_content_hash: "a037318f08851c0d"
depends_on:
  - "chapters/05_byggere"
tags:
  - publisering
  - pakking
  - leveranser
---

# Publisering

Media Engine lager komplette, selvstendige leveransepakker klare for distribusjon.

## Oversikt

Publiseringssystemet:

- Samler alle outputs i en enkelt mappe
- Laster ned og bygger inn fonter for offline-bruk
- Genererer navigasjonsindekser
- Oppretter valgfritt ZIP-arkiver
- Kopierer til en forutsigbar plassering (Desktop/deliverables/)

## Publisering med CLI

```bash
# Publiser til standardplassering
media-engine publish

# Egendefinert outputmappe
media-engine publish -o ./dist

# Lag ZIP-arkiv
media-engine publish --zip

# Ekskluder komponenter
media-engine publish --no-fonts
```

## Publisering med Python

```python
from media_engine import publish_project, PublishConfig, find_project

project = find_project()

config = PublishConfig(
    output_dir=Path("./dist"),
    include_fonts=True,
    include_diagrams=True,
    generate_indexes=True,
    zip_output=True,
)

result = publish_project(project, config)
print(f"Publisert til: {result.output_dir}")
```

## Publisert struktur

```
deliverables/mitt-prosjekt/
├── en/
│   ├── proposal.html
│   ├── pitch_deck.pptx
│   └── diagrams/
├── no/
│   └── ...
├── assets/
│   └── fonts/
├── index.html
└── manifest.json
```

## Navigasjonsindeks

Når `generate_indexes=True`, opprettes en `index.html` med:

- Lenker til alle dokumenter etter språk
- Lenker til presentasjoner og regneark
- Miniatyrbilder av diagrammer

## Fontpakking

Publiseringssystemet laster ned fonter spesifisert i temaet ditt for offline-bruk.
