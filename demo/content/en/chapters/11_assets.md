---
title: "Assets and Fonts"
version: "1.0.0"
status: "final"
last_modified: "2025-12-16"
freshness_days: 60
depends_on:
  - "chapters/05_builders"
tags:
  - assets
  - fonts
  - bundling
---

# Assets and Fonts

Media Engine manages project assets and can download fonts for offline use.

## Asset Structure

Projects organize assets in a dedicated directory:

```
project/
├── assets/
│   ├── brand/
│   │   ├── logo.svg
│   │   ├── logo-dark.svg
│   │   └── icon.png
│   ├── images/
│   │   ├── screenshot.png
│   │   └── diagram.png
│   └── fonts/
│       └── (downloaded fonts)
├── content/
└── project.yaml
```

## Configuration

Specify the assets path in `project.yaml`:

```yaml
paths:
  assets: "assets"
```

Access via the Project object:

```python
project = find_project()
assets_dir = project.assets_dir  # Path to assets/
```

## Google Fonts

Download fonts from Google Fonts for offline use:

```python
from media_engine import download_google_fonts

# Download fonts from theme
fonts_downloaded = download_google_fonts(
    font_names=["Inter", "Source Sans 3", "JetBrains Mono"],
    output_dir=project.assets_dir / "fonts",
)

print(f"Downloaded {fonts_downloaded} font files")
```

### Theme-Based Download

```python
from media_engine.assets import download_theme_fonts

# Download all fonts referenced in theme.yaml
fonts = download_theme_fonts(project.theme, project.assets_dir / "fonts")
```

This downloads:
- `typography.heading` font
- `typography.body` font
- `typography.code` font

### Font File Structure

```
assets/fonts/
├── Inter/
│   ├── Inter-Regular.woff2
│   ├── Inter-Medium.woff2
│   └── Inter-Bold.woff2
├── SourceSans3/
│   └── ...
└── JetBrainsMono/
    └── ...
```

## Asset Bundling

Bundle all project assets into a single directory:

```python
from media_engine import bundle_project_assets

result = bundle_project_assets(
    project,
    output_dir=Path("./bundled"),
    include_fonts=True,
    include_images=True,
)

print(f"Bundled {result.files_copied} files")
print(f"Total size: {result.total_size / 1024:.1f} KB")
```

### Bundle Result

```python
@dataclass
class BundleResult:
    output_dir: Path
    files_copied: int
    total_size: int  # bytes
    fonts_downloaded: int
    errors: list[str]
```

## Image References

Reference images in Markdown:

```markdown
![Architecture Diagram](../assets/images/architecture.png)
```

The validation system checks that referenced images exist.

## Brand Assets

Store brand assets for consistent use:

```
assets/brand/
├── logo.svg           # Primary logo
├── logo-dark.svg      # Dark mode variant
├── logo-square.svg    # Square format
├── favicon.ico        # Browser favicon
└── colors.json        # Brand color definitions
```

## Asset Paths in Code

```python
# Get brand directory
brand_dir = project.assets_dir / "brand"

# Get specific asset
logo = brand_dir / "logo.svg"
if logo.exists():
    # Use the logo
    pass
```

## CLI Asset Commands

Assets are bundled during publishing:

```bash
# Publish with fonts
media-engine publish

# Publish without fonts (faster, smaller)
media-engine publish --no-fonts
```

## Font Licensing

Media Engine downloads fonts from Google Fonts, which are open source. When bundling fonts:

1. Fonts are typically SIL Open Font License
2. They can be embedded in documents
3. They can be redistributed with your package

Check individual font licenses for specific terms.

## Offline Usage

For truly offline environments:

```python
# Pre-download all fonts
from media_engine.assets import download_google_fonts

download_google_fonts(
    font_names=["Inter", "Source Sans 3", "JetBrains Mono"],
    output_dir=Path("./offline-fonts"),
    formats=["woff2", "ttf"],  # Multiple formats
)
```

Then reference the local fonts in your CSS instead of Google Fonts CDN.

## Asset Optimization

For production, consider:

1. **Image compression**: Optimize PNGs and JPGs
2. **SVG minification**: Remove unnecessary metadata
3. **Font subsetting**: Include only used characters

```python
# Example: Copy and optimize
from media_engine.assets import bundle_project_assets

bundle_project_assets(
    project,
    output_dir,
    optimize_images=True,  # Future feature
)
```

## Best Practices

1. **Organize by type**: Separate brand, images, fonts
2. **Use SVG**: Scalable graphics for diagrams and logos
3. **Bundle fonts**: Ensure offline capability
4. **Version logos**: Keep variants (light, dark, square)
5. **Document assets**: Include a README in assets/
