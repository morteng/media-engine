---
title: "Integrations"
version: "1.1.0"
status: "final"
last_modified: "2025-12-23"
freshness_days: 60
depends_on:
  - "chapters/01_introduction"
tags:
  - mcp
  - dashboard
  - cicd
  - integrations
---

# Integrations

Media Engine integrates with AI agents, web interfaces, and CI/CD pipelines.

See [Introduction](01_introduction.md) for an overview of the system.

## MCP Server

The Model Context Protocol (MCP) server exposes Media Engine functionality to AI agents like Claude.

### Installation

```bash
pip install media-engine[mcp]
```

### Running the Server

```bash
# Start MCP server for a project
media-engine-mcp --project /path/to/project

# Or use short flag
media-engine-mcp -p .
```

### Available Tools

The MCP server exposes 20+ tools for AI agents.

| Category | Tools |
|----------|-------|
| Project | `project_status`, `project_config`, `refresh_project` |
| Content | `list_chapters`, `read_document`, `update_document_metadata` |
| Translation | `translation_status`, `outdated_translations`, `mark_translation_synced` |
| Quality | `quality_check`, `validate_project` |
| Search | `search_content` |
| Build | `build_html`, `build_pptx`, `build_xlsx` |
| Cache | `cache_status`, `clear_cache` |

### Claude Desktop Configuration

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "media-engine": {
      "command": "media-engine-mcp",
      "args": ["-p", "/path/to/project"]
    }
  }
}
```

## Web Dashboard

A browser-based UI for project management with real-time collaboration features.

### Installation

```bash
pip install media-engine[web]
```

### Launching

```bash
# Start dashboard
media-engine dashboard

# Custom port
media-engine dashboard --port 3000
```

Opens `http://localhost:8080` by default.

### Features

The dashboard provides visual project management with a modern DaisyUI-based interface.

| View | Description |
|------|-------------|
| Overview | Project status, statistics, and health metrics |
| Content | Browse chapters with markdown preview and AI annotations |
| Translations | Matrix view of translation status |
| Quality | Issue tracking with semantic, readability, and freshness checks |
| Build | Trigger builds, view output, and download artifacts |
| Media | Media registry and asset management |
| Insights | Analytics, velocity metrics, and content health |
| Video | Video timeline and scene management |
| Brand | Brand profile with colors, typography, and logos |
| Settings | Theme preferences and dashboard configuration |

### Theme System

The dashboard supports multiple themes with automatic dark mode detection.

| Theme | Description |
|-------|-------------|
| Nord | Light theme with soft colors (default) |
| Sunset | Dark theme for low-light environments |

Switch themes via:
- Settings page (`/settings`)
- Theme toggle button in header
- Command palette (`Cmd+K` then search "theme")

Settings persist in localStorage across sessions.

### Command Palette

Press `Cmd+K` (Mac) or `Ctrl+K` (Windows/Linux) to open the command palette for quick navigation.

| Command | Action |
|---------|--------|
| Go to Dashboard | Navigate to overview |
| Go to Content | Navigate to documents |
| Go to Settings | Open settings page |
| Toggle Theme | Switch between light/dark |
| Search... | Search all content |

### AI Content Annotations

When viewing documents in the Content page, you can:

1. **Select text** - Highlight any text in the document preview
2. **Add comment** - Leave a comment or question for AI processing
3. **Submit to queue** - The annotation is queued for AI analysis
4. **Persistent highlights** - Annotations remain visible with yellow highlighting
5. **Click to edit** - Click any highlight to view or update the comment

Annotations are tracked per document and submitted to the AI task queue.

### Real-time Collaboration

The dashboard uses WebSocket connections for real-time updates.

| Event | Description |
|-------|-------------|
| Document changes | Auto-refresh when content updates |
| Build status | Live build progress indicators |
| AI task updates | Queue status notifications |
| User presence | See who else is viewing the dashboard |

Connection status is shown in the sidebar. The WebSocket automatically reconnects with exponential backoff if disconnected.

### GUI Launcher

For easier access, use the GUI launcher:

```bash
# Auto-detect project
media-engine-gui

# Specific project
media-engine-gui /path/to/project

# Open file browser to select
media-engine-gui --browse
```

## CI/CD Integration

Media Engine works with GitHub Actions and other CI systems.

### GitHub Actions Workflow

Create `.github/workflows/docs.yml`:

```yaml
name: Docs

on:
  push:
    branches: [main]
    paths:
      - 'content/**'
      - 'project.yaml'

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

      - name: Validate
        run: media-engine validate

      - name: Security scan
        run: media-engine security
```

### Exit Codes

Commands return appropriate exit codes for CI:

| Code | Meaning |
|------|---------|
| 0 | Success / No issues |
| 1 | Error / Issues found |

### JSON Output

All commands support `--json` for machine parsing:

```bash
media-engine quality --json | jq '.error_count'
media-engine validate --json | jq '.issues'
```

## Audit Logging

Track all operations for compliance and debugging.

### Automatic Logging

The system logs operations to `.media-engine/audit.log`:

```
2025-12-16T10:30:00 | document_updated | intro.md | user@example.com
2025-12-16T10:31:00 | build_completed | html | system
```

### Python API

```python
from media_engine.audit import log_action, get_recent_entries

# Log custom action
log_action(
    project,
    action="document_reviewed",
    details="Approved chapter 3",
    user="reviewer@example.com"
)

# Get recent entries
entries = get_recent_entries(project, limit=50)
for entry in entries:
    print(f"{entry.timestamp}: {entry.action}")
```

## Dependency Tracking

Track relationships between documents.

```python
from media_engine.dependencies import DependencyGraph

graph = DependencyGraph(project)
graph.refresh()  # Scan all documents

# Find what's affected by a change
affected = graph.get_impact("chapters/02_content.md")
print(f"Documents to review: {affected}")
```

Documents declare dependencies in frontmatter:

```yaml
depends_on:
  - "chapters/01_introduction"
  - "chapters/02_content_management"
```
