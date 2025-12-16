---
title: "CLI-referanse"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/12_cli_reference.md"
source_version: "1.0.0"
depends_on:
  - "chapters/01_introduksjon"
tags:
  - cli
  - referanse
  - kommandoer
---

# CLI-referanse

Komplett referanse for `media-engine` kommandolinjegrensesnittet.

## Global bruk

```bash
media-engine <kommando> [alternativer]
```

## Kommandoer

Tilgjengelige kommandoer for å administrere Media Engine-prosjektet ditt.

### status

Vis prosjektstatus og dashbord.

```bash
media-engine status [visning] [--lang LANG] [--json]
```

Eksempler:
```bash
media-engine status              # Full dashbord
media-engine status docs         # Kun dokumentstatus
media-engine status --json       # JSON-output
```

### build

Bygg medieutdata fra kilder.

```bash
media-engine build [--only FORMAT] [--force] [--lang LANG]
```

| Alternativ | Beskrivelse |
|------------|-------------|
| `--only` | Bygg spesifikke formater: html, pdf, pptx, xlsx |
| `--force` | Tving gjenoppbygging (ignorer cache) |
| `--lang` | Bygg spesifikke språk |

### publish

Lag komplett leveransepakke.

```bash
media-engine publish [-o DIR] [--zip]
```

### quality

Kjør kvalitetssjekker på innhold.

```bash
media-engine quality [--json]
```

### search

Søk i prosjektdokumenter.

```bash
media-engine search SPØRRING [--limit N]
```

### validate

Valider prosjektinnhold mot skjema.

```bash
media-engine validate [--schema STI] [--refs-only]
```

### pack

Generer målgruppespesifikke innholdspakker.

```bash
media-engine pack TYPE [-o DIR]
```

### init

Initialiser et nytt prosjekt.

```bash
media-engine init [MAPPE] [--name NAVN]
```

## Exitkoder

| Kode | Betydning |
|------|-----------|
| 0 | Suksess |
| 1 | Feil |

## Vanlige arbeidsflyter

Typiske kommandosekvenser for vanlige oppgaver.

### Innholdsoppdateringssyklus

```bash
# Sjekk hva som må oppdateres
media-engine stale

# Rediger innhold...

# Valider og bygg
media-engine quality
media-engine validate
media-engine build

# Publiser når klar
media-engine publish
```
