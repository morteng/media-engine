---
title: "Videoproduksjon"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/03_video_production.md"
source_content_hash: "81dd41a16ae8b361"
depends_on:
  - "chapters/02_innholdsstyring"
tags:
  - video
  - produksjon
---

# Videoproduksjon

Media Engine integrerer med Remotion for programmatisk videogenerering og ElevenLabs for AI-voiceover.

## Videomanus

Videomanus er YAML-filer som definerer videostrukturen:

```yaml
metadata:
  title: "Demo Video"
  duration: 60  # sekunder

scenes:
  - type: "title"
    text: "Velkommen til Media Engine"
    duration: 5

  - type: "narration"
    text: "Media Engine hjelper deg med å lage innhold automatisk."
    duration: 10

  - type: "demo"
    screenshot: "feature_overview.png"
    duration: 15
```

## Voiceover-generering

Motoren genererer voiceovers med ElevenLabs:

1. Trekk ut fortellertekst fra manus
2. Sjekk cache for eksisterende lyd
3. Generer ny lyd om nødvendig
4. Cache resultat for fremtidige bygg

## Smart caching

Voiceover-lyd caches etter innholdshash:

```
.cache/voiceover/
├── abc123.mp3    # Cachet lydsegment
├── def456.mp3    # Et annet segment
└── manifest.json # Hash → filnavn-mapping
```

Hvis manusteksten ikke har endret seg, gjenbrukes cachet lyd.

## Remotion-integrasjon

Videokomposisjon håndteres av Remotion-komponenter:

- **TitleCard**: Animerte tittelslides
- **FeatureCard**: Funksjonshøydepunkter med ikoner
- **StatCounter**: Animert statistikk
- **Background**: Dynamiske bakgrunner
- **Transition**: Sceneoverganger
