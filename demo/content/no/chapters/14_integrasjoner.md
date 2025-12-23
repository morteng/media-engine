---
title: "Integrasjoner"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
language: "no"
source_document: "en/chapters/14_integrations.md"
source_content_hash: "11af4172562869c6"
depends_on:
  - "chapters/01_introduksjon"
tags:
  - mcp
  - dashbord
  - cicd
  - integrasjoner
---

# Integrasjoner

Media Engine integrerer med AI-agenter, webgrensesnitt og CI/CD-pipelines.

## MCP-server

Model Context Protocol (MCP)-serveren eksponerer Media Engine-funksjonalitet til AI-agenter som Claude.

### Installasjon

```bash
pip install media-engine[mcp]
```

### Kjøre serveren

```bash
# Start MCP-server for et prosjekt
media-engine-mcp --project /sti/til/prosjekt

# Eller bruk kort flagg
media-engine-mcp -p .
```

### Tilgjengelige verktøy

MCP-serveren eksponerer 20+ verktøy for AI-agenter.

| Kategori | Verktøy |
|----------|---------|
| Prosjekt | `project_status`, `project_config`, `refresh_project` |
| Innhold | `list_chapters`, `read_document`, `update_document_metadata` |
| Oversettelse | `translation_status`, `outdated_translations` |
| Kvalitet | `quality_check`, `validate_project` |
| Søk | `search_content` |
| Bygg | `build_html`, `build_pptx`, `build_xlsx` |

### Claude Desktop-konfigurasjon

Legg til i `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "media-engine": {
      "command": "media-engine-mcp",
      "args": ["-p", "/sti/til/prosjekt"]
    }
  }
}
```

## Webdashbord

Et nettleserbasert brukergrensesnitt for prosjektstyring.

### Installasjon

```bash
pip install media-engine[web]
```

### Oppstart

```bash
# Start dashbord
media-engine dashboard

# Egendefinert port
media-engine dashboard --port 3000
```

Åpner `http://localhost:8080` som standard.

### Funksjoner

| Visning | Beskrivelse |
|---------|-------------|
| Oversikt | Prosjektstatus og statistikk |
| Dokumenter | Bla gjennom og les alle kapitler |
| Oversettelser | Matriseoversikt over oversettelsesstatus |
| Kvalitet | Problemsporing og løsning |
| Bygg | Utløs bygg og vis output |

## CI/CD-integrasjon

Media Engine fungerer med GitHub Actions og andre CI-systemer.

### GitHub Actions arbeidsflyt

```yaml
name: Docs

on:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install
        run: pip install media-engine

      - name: Quality check
        run: media-engine quality
```

## Revisjonslogging

Spor alle operasjoner for samsvar og feilsøking.

```python
from media_engine.audit import log_action, get_recent_entries

log_action(project, "document_reviewed", details="Godkjent kapittel 3")
entries = get_recent_entries(project, limit=50)
```
