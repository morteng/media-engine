---
title: "Introduksjon til Media Engine"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/01_introduction.md"
source_version: "1.0.0"
tags:
  - introduksjon
  - oversikt
---

# Introduksjon til Media Engine

Media Engine er et agent-drevet rammeverk for medieproduksjon. Det hjelper AI-assistenter som Claude Code med å generere dokumenter, presentasjoner, videoer og andre mediefiler fra strukturert innhold.

## Hovedfunksjoner

- **Innholdsstyring**: Markdown-dokumenter med YAML-metadata for sporing
- **Flere formater**: Generer HTML, PDF, PPTX, XLSX og video fra samme kilde
- **Smart caching**: Bygg bare det som har endret seg
- **Flerspråklig støtte**: Innhold på flere språk med oversettelsesporing
- **Agent-vennlig**: CLI designet for at AI-assistenter kan operere

## Hvordan det fungerer

```
Innhold (Markdown) → Media Engine → Output (PDF, Video, osv.)
                          ↑
                    project.yaml
                    (konfigurasjon)
```

Media engine leser innholdet ditt, bruker ditt tema, og genererer output. Den sporer hva som er bygget og regenererer bare når kildinnhold endres.

## Kom i gang

1. Opprett et prosjekt med `media-engine init`
2. Legg til innhold i `content/{språk}/chapters/`
3. Bygg med `media-engine build`
4. Publiser til skrivebordet med `media-engine publish`
