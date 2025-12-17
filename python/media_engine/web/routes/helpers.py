"""
Helper functions for route handlers.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ...core.project import Project


def find_source_script(project: "Project", media_file: Path) -> Optional[dict]:
    """Find the source script for a generated media file."""
    parts = media_file.parts

    # Try to find language in path
    lang = None
    for part in parts:
        if part in project.languages:
            lang = part
            break

    if not lang:
        return None

    # Get script name from filename (without extension)
    script_name = media_file.stem

    # Look for matching script in content directory
    script_path = project.content_dir / lang / "scripts" / f"{script_name}.yaml"
    if script_path.exists():
        return {
            "path": str(script_path),
            "name": script_name,
            "language": lang,
            "type": "script",
        }

    # Also check for scripts folder structure
    for i, part in enumerate(parts):
        if part == "scripts" and i + 1 < len(parts):
            folder_name = parts[i + 1]
            script_path = project.content_dir / lang / "scripts" / f"{folder_name}.yaml"
            if script_path.exists():
                return {
                    "path": str(script_path),
                    "name": folder_name,
                    "language": lang,
                    "type": "script",
                }

    return None


def find_source_demo(project: "Project", demo_file: Path) -> Optional[dict]:
    """Find the source demo config for a generated demo HTML."""
    demo_name = demo_file.stem
    parts = demo_file.parts
    for i, part in enumerate(parts):
        if part in project.languages:
            lang = part
            demo_path = project.content_dir / lang / "demos" / f"{demo_name}.yaml"
            if demo_path.exists():
                return {
                    "path": str(demo_path),
                    "name": demo_name,
                    "language": lang,
                    "type": "demo",
                }
    return None
