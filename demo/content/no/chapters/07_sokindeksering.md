---
title: "Søkeindeksering"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/07_search_indexing.md"
source_version: "1.0.0"
depends_on:
  - "chapters/02_innholdsstyring"
tags:
  - sok
  - indeksering
  - fulltekst
---

# Søkeindeksering

Media Engine gir fulltekstsøkefunksjoner for prosjektinnhold med relevansskåring.

## Oversikt

Søkesystemet:

- Indekserer alle Markdown-dokumenter
- Støtter fulltekstspørringer
- Rangerer resultater etter relevans
- Lagrer indekser for raske søk
- Integrerer med CLI

## Bygge en søkeindeks

Opprett og oppdater søkeindekser med CLI eller Python API.

### CLI

```bash
# Bygg/oppdater søkeindeks
media-engine index

# Søk i dokumenter
media-engine search "autentisering"

# Begrens resultater
media-engine search "api" --limit 10
```

### Python-API

```python
from media_engine import build_search_index, find_project

project = find_project()

# Bygg indeks
index = build_search_index(project)

# Lagre for senere bruk
index.save(Path(".cache/search_index.json"))
```

## Søke

```python
results = index.search("autentisering", limit=10)

for result in results:
    print(f"{result.score:.0f} - {result.entry.title}")
```

## Søkeresultatets egenskaper

| Egenskap | Beskrivelse |
|----------|-------------|
| `score` | Relevansskår (høyere = bedre) |
| `entry.title` | Dokumenttittel |
| `entry.path` | Filsti |
| `entry.excerpt` | Innholdsforhåndsvisning |

## Relevansskåring

Søkealgoritmen vurderer:

1. **Titteltreff**: Høyest vekt
2. **Taggtreff**: Høy vekt
3. **Innholdstreff**: Standard vekt
4. **Termfrekvens**: Flere forekomster = høyere skår

## Flerspråklig støtte

Søkesystemet indekserer alle språk:

```python
# Søk på tvers av alle språk
results = index.search("autentisering")

# Filtrer etter språk
no_results = [r for r in results if r.entry.language == "no"]
```
