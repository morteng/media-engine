# Media Engine

Agent-based media production framework for automated content generation.

## Features

- **CMS** - Document management with frontmatter, versioning, and quality checks
- **Video** - Timeline sequencing, screen capture, voiceover generation, captions
- **Diagrams** - Matplotlib-based diagram generation with theming
- **Slides** - PowerPoint and PDF generation
- **Remotion** - React-based motion graphics components

## Installation

```bash
# Python package
uv add media-engine --path ../media-engine/python

# Remotion components
npm install @media-engine/remotion --registry file:../media-engine/remotion
```

## Quick Start

### Document Management

```python
from media_engine.cms import Document, DocumentCollection

# Load documents
collection = DocumentCollection(Path("docs"))
collection.load_all()

# Quality checks
for doc in collection.all_documents:
    print(f"{doc.title}: v{doc.version}")
```

### Video Timeline

```python
from media_engine.video import Timeline, TimelineClip

# Create timeline
timeline = Timeline(fps=30)
timeline.add_clip(TimelineClip(
    source="demo.mp4",
    start_frame=0,
    duration_frames=300
))

# Export FFmpeg command
ffmpeg_cmd = timeline.export_ffmpeg("output.mp4")
```

### Voiceover Generation

```python
from media_engine.video import VoiceoverConfig, generate_voiceover

config = VoiceoverConfig(
    voice_id="your-voice-id",
    provider="elevenlabs"
)

audio_path = await generate_voiceover(
    text="Your script here",
    config=config,
    output_path=Path("voiceover.mp3")
)
```

### Remotion Components

```tsx
import { TitleCard, StatCounter, Background } from '@media-engine/remotion';

export const MyVideo = () => (
  <>
    <Background variant="gradient" />
    <TitleCard title="My Title" tagline="Subtitle here" />
    <StatCounter value={100} suffix="%" label="Completion" />
  </>
);
```

## Project Structure

```
media-engine/
├── python/
│   ├── media_engine/
│   │   ├── cms/          # Document management
│   │   ├── video/        # Video production
│   │   ├── diagrams/     # Diagram generation
│   │   ├── slides/       # Slide generation
│   │   └── core/         # Shared utilities
│   └── tests/            # Test suite
├── remotion/
│   └── src/
│       ├── components/   # Motion graphics
│       └── lib/          # Animation utilities
└── pyproject.toml
```

## Configuration

Create a `config.yaml` in your project:

```yaml
project:
  name: "My Project"

voiceover:
  provider: "elevenlabs"
  voice_id: "your-voice-id"

video:
  width: 1920
  height: 1080
  fps: 30

theme:
  colors:
    primary: "#2c2522"
    accent: "#c45c3c"
```

## License

MIT
