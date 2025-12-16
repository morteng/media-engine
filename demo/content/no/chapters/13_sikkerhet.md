---
title: "Sikkerhetsskanning"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/13_security.md"
source_version: "1.0.0"
depends_on:
  - "chapters/04_kvalitetssjekker"
tags:
  - sikkerhet
  - hemmeligheter
  - personvern
---

# Sikkerhetsskanning

Media Engine inkluderer omfattende sikkerhetsskanning for å oppdage sensitivt innhold før publisering.

## Oversikt

Sikkerhetsskanneren oppdager:

- **API-nøkler**: AWS, GitHub, OpenAI, Anthropic, Stripe og flere
- **Personopplysninger**: E-postadresser, telefonnumre, personnummer
- **Interne URLer**: Private nettverksadresser og localhost-referanser
- **Legitimasjon**: Passord, tokens og autentiseringshemmeligheter

## Kjøre sikkerhetsskanning

Bruk CLI for å skanne prosjektet for sensitivt innhold.

### CLI

```bash
# Skann alle dokumenter
media-engine security

# Inkluder ressursfiler (YAML, JSON)
media-engine security --include-assets

# JSON-output
media-engine security --json
```

### Python-API

```python
from media_engine.security import scan_for_secrets, SensitiveContentScanner

# Rask skanning
report = scan_for_secrets(project)

print(f"Filer skannet: {report['files_scanned']}")
print(f"Funn: {report['total_findings']}")
```

## Oppdagede mønstre

Skanneren gjenkjenner vanlige hemmelighetsmønstre.

### API-nøkler

| Mønster | Eksempel | Alvorlighet |
|---------|----------|-------------|
| AWS Access Key | `AKIA...` | Kritisk |
| GitHub Token | `ghp_...` | Kritisk |
| OpenAI API Key | `sk-...` | Kritisk |
| Anthropic Key | `sk-ant-...` | Kritisk |

### Personopplysninger

| Mønster | Eksempel | Alvorlighet |
|---------|----------|-------------|
| E-postadresse | `bruker@example.com` | Høy |
| Telefonnummer | `+47 XXX XX XXX` | Høy |

## Alvorlighetsnivåer

Funn kategoriseres etter alvorlighet:

- **Kritisk**: Må fjernes før publisering
- **Høy**: Bør gjennomgås
- **Medium**: Kan være tilsiktet
- **Lav**: Informasjon

## CI/CD-integrasjon

Blokker publisering ved kritiske funn:

```bash
media-engine security || exit 1
```
