---
title: "Innholdsstyring"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/02_content_management.md"
source_version: "1.0.0"
depends_on:
  - "chapters/01_introduksjon"
tags:
  - innhold
  - cms
---

# Innholdsstyring

Media Engine bruker et filbasert innholdsstyringssystem. Dokumenter er Markdown-filer med YAML-frontmatter for metadata.

## Dokumentstruktur

Hvert dokument følger denne strukturen:

```markdown
---
title: "Dokumenttittel"
version: "1.0.0"
status: "draft"
last_modified: "2025-12-16"
---

# Overskrift

Innhold her...
```

## Frontmatter-felt

| Felt | Påkrevd | Beskrivelse |
|------|---------|-------------|
| `title` | Ja | Dokumenttittel |
| `version` | Ja | Semantisk versjon (major.minor.patch) |
| `status` | Ja | draft, review, eller final |
| `last_modified` | Ja | Dato for siste endring |
| `freshness_days` | Nei | Dager før innhold anses som foreldet |
| `depends_on` | Nei | Liste over avhengige dokumenter |
| `tags` | Nei | Liste med tagger for kategorisering |

## Foreldelsesporing

Dokumenter blir foreldede når:
- De ikke er endret på `freshness_days` dager
- Et dokument de avhenger av er oppdatert

Sjekk foreldet innhold med:

```bash
media-engine stale
```

## Mappestruktur

```
content/
├── en/                    # Engelsk innhold
│   ├── chapters/          # Dokumentkapitler
│   │   ├── 01_intro.md
│   │   └── 02_features.md
│   └── scripts/           # Videomanus
│       └── demo.yaml
└── no/                    # Norske oversettelser
    ├── chapters/
    └── scripts/
```
