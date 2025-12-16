"""
Media Engine Assets Module

Asset management for projects:
- Font downloading and embedding
- Asset bundling for self-contained packages
"""

from .fonts import (
    download_google_fonts,
    generate_font_faces,
    FontConfig,
)
from .bundler import (
    bundle_project_assets,
    AssetBundle,
)

__all__ = [
    "download_google_fonts",
    "generate_font_faces",
    "FontConfig",
    "bundle_project_assets",
    "AssetBundle",
]
