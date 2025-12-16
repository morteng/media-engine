---
title: "Validering"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/08_validation.md"
source_version: "1.0.0"
depends_on:
  - "chapters/02_innholdsstyring"
  - "chapters/04_kvalitetssjekker"
tags:
  - validering
  - skjema
  - referanser
---

# Validering

Media Engine tilbyr skjemavalidering for frontmatter og referansesjekking for lenker.

## Oversikt

Valideringssystemet sjekker:

- **Skjemavalidering**: Frontmatter-felt mot JSON Schema
- **Referansevalidering**: Interne lenker og sitater
- **Påkrevde felt**: Manglende obligatorisk metadata
- **Verdibegrensninger**: Enums, mønstre og typer

## Kjøre validering

### CLI

```bash
# Full validering (skjema + referanser)
media-engine validate

# Kun sjekk referanser
media-engine validate --refs-only

# Bruk tilpasset skjema
media-engine validate --schema custom_schema.yaml
```

### Python-API

```python
from media_engine import validate_project, find_project

project = find_project()
report = validate_project(project)

print(f"Filer: {report.files_checked}")
print(f"Feil: {report.error_count}")
```

## Skjemadefinisjon

Skjemaer bruker JSON Schema-format i YAML:

```yaml
type: object
required:
  - title
  - version
  - status

properties:
  title:
    type: string

  version:
    type: string
    pattern: "^\\d+\\.\\d+\\.\\d+$"

  status:
    type: string
    enum:
      - draft
      - review
      - final
```

## Referansevalidering

Systemet sjekker:

1. **Interne lenker**: `[tekst](../chapter.md)` løses opp
2. **Bildereferanser**: `![alt](image.png)` filer eksisterer
3. **Dokumentavhengigheter**: `depends_on` oppføringer er gyldige

## Feileksempler

```
ERROR: document.md - Mangler påkrevd felt 'title'
ERROR: document.md:15 - Ødelagt lenke: ../missing.md
ERROR: document.md - depends_on 'chapters/nonexistent' ikke funnet
```
