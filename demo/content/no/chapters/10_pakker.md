---
title: "Målgruppepakker"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/10_packs.md"
source_version: "1.0.0"
depends_on:
  - "chapters/09_publisering"
tags:
  - pakker
  - malgruppe
  - distribusjon
---

# Målgruppepakker

Media Engine kan generere kuraterte innholdspakker skreddersydd for spesifikke målgrupper.

## Oversikt

Målgruppepakker er delmengder av prosjektinnholdet, pakket for et spesifikt formål:

- **Investorpakke**: Finansielle høydepunkter, pitch deck, nøkkeltall
- **Pilotpakke**: Teknisk dokumentasjon, oppsettguider, støttemateriale

## Generere pakker

### CLI

```bash
# Generer investormateriale
media-engine pack investor

# Generer pilotkundemateriale
media-engine pack pilot

# Egendefinert outputmappe
media-engine pack investor -o ./investor-materiale
```

### Python-API

```python
from media_engine import generate_investor_pack, find_project

project = find_project()

result = generate_investor_pack(
    project,
    output_dir=Path("./dist"),
    create_zip=True,
)

print(f"Opprettet: {result.output_path}")
print(f"Elementer: {result.items_included}")
```

## Pakkeinnhold

### Investorpakke

| Element | Beskrivelse |
|---------|-------------|
| `pitch_deck.pptx` | Presentasjonsslides |
| `executive_summary.pdf` | Ensidig oversikt |
| `calculator.xlsx` | Finansmodell |
| `diagrams/` | Arkitekturvisualiseringer |

### Pilotpakke

| Element | Beskrivelse |
|---------|-------------|
| `documentation.pdf` | Full teknisk dokumentasjon |
| `setup_guide.html` | Komme i gang-guide |
| `api_reference.html` | API-dokumentasjon |
| `videos/` | Demovideoer og ressurser |

## Manglende elementer

Pakker rapporterer manglende innhold uten å feile—pakker genereres med tilgjengelig innhold.
