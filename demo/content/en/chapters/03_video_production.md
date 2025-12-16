---
title: "Video Production"
version: "1.0.0"
status: "draft"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/02_content_management"
tags:
  - video
  - production
---

# Video Production

Media Engine integrates with Remotion for programmatic video generation and ElevenLabs for AI voiceovers.

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
