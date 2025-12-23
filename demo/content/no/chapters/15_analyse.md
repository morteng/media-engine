---
title: "Innholdsanalyse"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/15_analysis.md"
source_content_hash: "6224ebc28194f87c"
depends_on:
  - "chapters/04_kvalitetssjekker"
tags:
  - lesbarhet
  - lenker
  - hull
  - analyse
---

# Innholdsanalyse

Media Engine tilbyr avanserte analyseverktøy for innholdskvalitet, lesbarhet og fullstendighet.

## Lenkevalidering

Sjekk alle interne og eksterne lenker i dokumentasjonen.

### CLI

```bash
# Sjekk alle lenker
media-engine links

# Kun interne lenker (raskere)
media-engine links --internal-only

# JSON-output
media-engine links --json
```

### Funksjoner

| Funksjon | Beskrivelse |
|----------|-------------|
| Parallell sjekking | Rask ekstern URL-validering |
| Resultatcaching | Unngå gjentatte sjekker (24t TTL) |
| Hopp over kodeblokker | Ignorerer eksempellenker i kode |
| Intern oppløsning | Validerer relative stier |

## Lesbarhetsanalyse

Mål hvor lett innholdet er å lese.

### CLI

```bash
# Analyser alle dokumenter
media-engine readability

# Sett mållesenivå
media-engine readability --target college

# JSON-output
media-engine readability --json
```

### Metrikker

Flere lesbarhetsformler beregnes.

| Metrikk | Område | Tolkning |
|---------|--------|----------|
| Flesch Reading Ease | 0-100 | Høyere = lettere |
| Flesch-Kincaid Grade | 1-12+ | Klassetrinn |
| Gunning Fog Index | 1-20+ | Utdanningsår |

### Målnivåer

| Nivå | Flesch | Målgruppe |
|------|--------|-----------|
| simple | 80-100 | Allmennheten |
| standard | 60-80 | Videregående |
| college | 30-60 | Høyere utdanning |
| technical | 0-30 | Spesialister |

## Innholdshullanalyse

Finn manglende eller ufullstendig innhold.

### CLI

```bash
# Finn alle hull
media-engine gaps

# Sjekk forventede emner
media-engine gaps --topics "installasjon,konfigurasjon,api"
```

### Hulltyper

| Hulltype | Beskrivelse |
|----------|-------------|
| Manglende oversettelser | Kildedokumenter uten oversettelser |
| Ødelagte referanser | `depends_on`-oppføringer som ikke eksisterer |
| Foreldreløse dokumenter | Dokumenter ikke lenket fra noe sted |

## Innholdsvariabler

Bruk dynamiske variabler i dokumentene.

### Syntaks

```markdown
Dette dokumentet ble publisert {{date.today}}.
Prosjektnavn: {{project.name}}
Versjon: {{project.version}}
```

### Tilgjengelige navnerom

| Navnerom | Variabler |
|----------|-----------|
| `project` | `name`, `version`, `description` |
| `date` | `today`, `year`, `month` |
| `env` | Miljøvariabler |

### Egendefinerte variabler

Definer egendefinerte variabler i `variables.yaml`:

```yaml
selskap:
  navn: "Acme AS"
  nettside: "https://acme.no"
```

## Endringslogggenerering

Generer endringslogger fra git-historikk.

```bash
# Full endringslogg
media-engine changelog

# Siste 30 dager
media-engine changelog --days 30

# Skriv til fil
media-engine changelog -o CHANGELOG.md
```
