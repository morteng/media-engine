"""
Media Engine Assets Module

Asset management for projects:
- Font downloading and embedding
- Asset bundling for self-contained packages
"""

from .bundler import (
    AssetBundle,
    bundle_project_assets,
)
from .fonts import (
    FontConfig,
    download_google_fonts,
    generate_font_faces,
)

__all__ = [
    "download_google_fonts",
    "generate_font_faces",
    "FontConfig",
    "bundle_project_assets",
    "AssetBundle",
]
