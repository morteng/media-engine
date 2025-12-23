"""
Assets routes: diagrams, logos, images.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_assets_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register asset-related routes."""
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    @router.get("/api/assets")
    async def get_assets():
        """Get all project assets (diagrams, logos, images)."""
        project = get_project()
        assets = []

        # Diagrams
        diagram_dirs = [
            project.root / "docs" / "proposal" / "diagrams",
            project.root / "docs" / "system" / "diagrams",
            project.root / "docs" / "diagrams",
        ]
        for diagrams_dir in diagram_dirs:
            if diagrams_dir.exists():
                for ext in ["*.svg", "*.png", "*.jpg", "*.jpeg"]:
                    for f in diagrams_dir.glob(ext):
                        rel_path = f.relative_to(project.root)
                        assets.append(
                            {
                                "path": str(f),
                                "relative_path": str(rel_path),
                                "filename": f.name,
                                "type": "diagram",
                                "format": f.suffix.lstrip("."),
                                "size": f.stat().st_size,
                                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                            }
                        )

        # Logos
        logo_dirs = [
            project.root / "docs" / "brand" / "logo",
            project.root / "docs" / "brand" / "assets",
            project.root / "assets" / "logo",
        ]
        for logo_dir in logo_dirs:
            if logo_dir.exists():
                for ext in ["*.svg", "*.png"]:
                    for f in logo_dir.glob(ext):
                        rel_path = f.relative_to(project.root)
                        assets.append(
                            {
                                "path": str(f),
                                "relative_path": str(rel_path),
                                "filename": f.name,
                                "type": "logo",
                                "format": f.suffix.lstrip("."),
                                "size": f.stat().st_size,
                                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                            }
                        )

        # Video thumbnails
        video_assets_dir = project.root / "docs" / "deliverables" / "assets" / "videos"
        if video_assets_dir.exists():
            for f in video_assets_dir.rglob("*"):
                if f.is_file() and f.suffix in [".mp4", ".webm", ".png", ".jpg"]:
                    rel_path = f.relative_to(project.root)
                    assets.append(
                        {
                            "path": str(f),
                            "relative_path": str(rel_path),
                            "filename": f.name,
                            "type": "video_asset",
                            "format": f.suffix.lstrip("."),
                            "size": f.stat().st_size,
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        }
                    )

        by_type = {}
        for asset in assets:
            t = asset["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(asset)

        return {
            "total": len(assets),
            "by_type": {t: len(files) for t, files in by_type.items()},
            "assets": assets,
        }

    @router.get("/assets/{path:path}")
    async def serve_assets(path: str):
        """Serve asset files from project directory."""
        project = get_project()
        file_path = project.root / path
        if not file_path.exists():
            raise HTTPException(404, f"Asset file not found: {path}")
        suffix = file_path.suffix.lower()
        media_types = {
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
        }
        return FileResponse(file_path, media_type=media_types.get(suffix))
