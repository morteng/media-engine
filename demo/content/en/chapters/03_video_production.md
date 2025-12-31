---
title: "Video Production"
version: "1.0.0"
status: "final"
last_modified: "2025-12-31"
freshness_days: 60
depends_on:
  - "chapters/02_content_management"
tags:
  - video
  - production

# Hierarchy metadata
doc_type: "implementation"
lifecycle: "living"
parent_document: "chapters/01_introduction.md"
sequence_order: 3
hierarchy_level: 1

# Derives from content management
derived_from:
  - path: "chapters/02_content_management.md"
    version: "1.0.0"
    relationship: "extends"

# Anchors - video configuration facts
anchors:
  default_video_width:
    value: 1920
    type: number
    description: "Default video width in pixels"
  default_video_height:
    value: 1080
    type: number
    description: "Default video height in pixels"
  default_video_fps:
    value: 30
    type: number
    description: "Default frames per second"
---

# Video Production

Media Engine provides a complete video production pipeline. It integrates Remotion for programmatic video rendering and ElevenLabs for AI voiceovers. You generate professional videos directly from YAML script definitions—no video editing software required.

See [Content Management](02_content_management.md) for how scripts fit into the content structure.

## Video Scripts

Write video scripts as YAML files that define your video structure:

```yaml
metadata:
  title: "Demo Video"
  duration: 60  # seconds

scenes:
  - type: "title"
    text: "Welcome to Media Engine"
    duration: 5

  - type: "narration"
    text: "Media Engine helps you create content automatically."
    duration: 10

  - type: "demo"
    screenshot: "feature_overview.png"
    duration: 15
```

## Voiceover Generation

The engine generates voiceovers using ElevenLabs:

1. Extract narration text from script
2. Check cache for existing audio
3. Generate new audio if needed
4. Cache result for future builds

## Smart Caching

The system caches voiceover audio by content hash:

```
.cache/voiceover/
├── abc123.mp3    # Cached audio segment
├── def456.mp3    # Another segment
└── manifest.json # Hash → filename mapping
```

If the script text hasn't changed, Media Engine reuses the cached audio.

## Remotion Integration

Remotion components handle video composition:

- **TitleCard**: Animated title slides
- **FeatureCard**: Feature highlights with icons
- **StatCounter**: Animated statistics
- **Background**: Dynamic backgrounds
- **Transition**: Scene transitions

## Video Projects

The dashboard provides project-based video management with component tracking:

1. **Create Project**: Name and language for a new video project
2. **Track Components**: Script, demo clips, voiceover, props, captions, render
3. **Component Dependencies**: Cascading regeneration when source changes
4. **Review Comments**: Add comments at specific timestamps for team review

### Component Workflow

```
Script → Demo Definition → Demo Clip
                              ↓
Script → Voiceover → Captions
                        ↓
        Props ← Demo Clip + Captions
           ↓
        Render (final output)
```

### Dashboard Features

| Feature | Description |
|---------|-------------|
| Project List | Filter by status: Draft, In Review, Approved, Rendering, Published |
| Progress Tracking | Visual progress bar based on component completion |
| Stale Detection | Automatic marking when dependencies change |
| Cascade Regenerate | Mark downstream components as stale |

## MCP Video Tools

AI agents can use MCP tools for video production automation:

| Tool | Purpose |
|------|---------|
| `list_video_scripts` | List all scripts with metadata |
| `get_video_script` | Get single script with full details |
| `get_video_props` | Get computed props.json for rendering |
| `get_video_assets` | List assets by type (demo clips, audio, etc.) |
| `generate_voiceover` | Prepare voiceover generation |
| `start_video_render` | Queue a render job |
| `get_render_status` | Check render progress |

See [Integrations](14_integrations.md) for the full MCP tools reference.

## Quick Reference

| Component | Purpose | Example Use |
|-----------|---------|-------------|
| Script YAML | Define video structure | `content/en/scripts/demo.yaml` |
| Voiceover | AI narration | Auto-generated from script text |
| Cache | Avoid regeneration | `.cache/voiceover/` |
| Remotion | Video rendering | TypeScript components in `remotion/` |

See [GitHub Showcase](16_github_showcase.md) for a complete video example with voiceover configuration.
