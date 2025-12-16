---
title: "Kvalitetssjekker"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/04_quality_checks.md"
source_version: "1.0.0"
depends_on:
  - "chapters/02_innholdsstyring"
tags:
  - kvalitet
  - validering
  - plassholdere
---

# Kvalitetssjekker

Media Engine inkluderer et omfattende kvalitetssikringssystem som skanner innhold for vanlige problemer før publisering.

## Oversikt

Kvalitetssjekkesystemet oppdager:

- **Plassholdermarkører**: TODO, TBD, FIXME og malvariabler
- **Tegnkodingsproblemer**: Mojibake og tegnkorrupsjon i norsk tekst
- **Terminologiinkonsistens**: Termer som bør bruke foretrukne alternativer
- **Tomme seksjoner**: Overskrifter uten innhold

## Kjøre kvalitetssjekker

Bruk CLI for å kjøre kvalitetssjekker på prosjektet:

```bash
# Kjør alle kvalitetssjekker
media-engine quality

# Output som JSON
media-engine quality --json
```

Eller bruk Python-API:

```python
from media_engine import run_quality_checks, find_project

project = find_project()
report = run_quality_checks(project)

print(f"Filer sjekket: {report.files_checked}")
print(f"Feil: {report.error_count}")
print(f"Advarsler: {report.warning_count}")
```

## Plassholderoppdaging

Systemet oppdager vanlige plassholdermønstre:

| Mønster | Beskrivelse |
|---------|-------------|
| `TODO` | Oppgavemarkører |
| `TBD` | Skal bestemmes |
| `FIXME` | Problemer å fikse |
| `[placeholder]` | Innholdsplassholder |

## Tegnkodingsvalidering

For norsk innhold oppdager systemet tegnkodingskorrupsjon (mojibake):

| Korrupt | Korrekt | Problem |
|---------|---------|---------|
| `Ã¦` | `æ` | UTF-8 lest som Latin-1 |
| `Ã¸` | `ø` | UTF-8 lest som Latin-1 |
| `Ã¥` | `å` | UTF-8 lest som Latin-1 |

## Alvorlighetsgrader

Problemer kategoriseres etter alvorlighet:

- **Error**: Må fikses før publisering (tegnkodingskorrupsjon)
- **Warning**: Bør håndteres (plassholdere, tomme seksjoner)
- **Info**: Forslag til forbedring (terminologi)
