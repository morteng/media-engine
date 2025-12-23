---
title: "Video Production"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
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
    type: integer
    description: "Default video width in pixels"
  default_video_height:
    value: 1080
    type: integer
    description: "Default video height in pixels"
  default_video_fps:
    value: 30
    type: integer
    description: "Default frames per second"
---

# Video Production

Media Engine provides a complete video production pipeline, integrating Remotion for programmatic video rendering and ElevenLabs for high-quality AI voiceovers. This allows you to generate professional videos directly from YAML script definitions—no video editing software required.

## Video Scripts

Video scripts are YAML files that define the video structure:

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

Voiceover audio is cached by content hash:

```
.cache/voiceover/
├── abc123.mp3    # Cached audio segment
├── def456.mp3    # Another segment
└── manifest.json # Hash → filename mapping
```

If the script text hasn't changed, the cached audio is reused.

## Remotion Integration

Video composition is handled by Remotion components:

- **TitleCard**: Animated title slides
- **FeatureCard**: Feature highlights with icons
- **StatCounter**: Animated statistics
- **Background**: Dynamic backgrounds
- **Transition**: Scene transitions

## Quick Reference

| Component | Purpose | Example Use |
|-----------|---------|-------------|
| Script YAML | Define video structure | `content/en/scripts/demo.yaml` |
| Voiceover | AI narration | Auto-generated from script text |
| Cache | Avoid regeneration | `.cache/voiceover/` |
| Remotion | Video rendering | TypeScript components in `remotion/` |
