"""
Media files routes: videos, audio, captions, demos.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_media_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register media file routes."""
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    from .helpers import find_source_demo, find_source_script

    @router.get("/api/media")
    async def get_media_files():
        """Get all generated media files with source document info."""
        project = get_project()
        media_files = []

        output_dir = project.output_dir
        if output_dir.exists():
            # Audio files (voiceovers)
            for mp3 in output_dir.rglob("*.mp3"):
                rel_path = mp3.relative_to(output_dir)
                source_script = find_source_script(project, mp3)
                media_files.append(
                    {
                        "path": str(mp3),
                        "relative_path": str(rel_path),
                        "filename": mp3.name,
                        "type": "audio",
                        "format": "mp3",
                        "size": mp3.stat().st_size,
                        "modified": datetime.fromtimestamp(mp3.stat().st_mtime).isoformat(),
                        "source": source_script,
                        "url": f"/media/{rel_path}",
                    }
                )

            # Caption files (VTT)
            for vtt in output_dir.rglob("*.vtt"):
                rel_path = vtt.relative_to(output_dir)
                source_script = find_source_script(project, vtt)
                media_files.append(
                    {
                        "path": str(vtt),
                        "relative_path": str(rel_path),
                        "filename": vtt.name,
                        "type": "captions",
                        "format": "vtt",
                        "size": vtt.stat().st_size,
                        "modified": datetime.fromtimestamp(vtt.stat().st_mtime).isoformat(),
                        "source": source_script,
                        "url": f"/media/{rel_path}",
                    }
                )

            # Video props files
            for props in output_dir.rglob("props.json"):
                rel_path = props.relative_to(output_dir)
                source_script = find_source_script(project, props)
                media_files.append(
                    {
                        "path": str(props),
                        "relative_path": str(rel_path),
                        "filename": props.name,
                        "type": "video_props",
                        "format": "json",
                        "size": props.stat().st_size,
                        "modified": datetime.fromtimestamp(props.stat().st_mtime).isoformat(),
                        "source": source_script,
                        "url": f"/media/{rel_path}",
                    }
                )

            # Demo HTML files
            demos_dir = output_dir / "demos"
            if demos_dir.exists():
                for html in demos_dir.rglob("*.html"):
                    rel_path = html.relative_to(output_dir)
                    source_demo = find_source_demo(project, html)
                    media_files.append(
                        {
                            "path": str(html),
                            "relative_path": str(rel_path),
                            "filename": html.name,
                            "type": "demo",
                            "format": "html",
                            "size": html.stat().st_size,
                            "modified": datetime.fromtimestamp(html.stat().st_mtime).isoformat(),
                            "source": source_demo,
                            "url": f"/media/{rel_path}",
                        }
                    )

            # Video files (MP4)
            for mp4 in output_dir.rglob("*.mp4"):
                rel_path = mp4.relative_to(output_dir)
                source_script = find_source_script(project, mp4)
                media_files.append(
                    {
                        "path": str(mp4),
                        "relative_path": str(rel_path),
                        "filename": mp4.name,
                        "type": "video",
                        "format": "mp4",
                        "size": mp4.stat().st_size,
                        "modified": datetime.fromtimestamp(mp4.stat().st_mtime).isoformat(),
                        "source": source_script,
                        "url": f"/media/{rel_path}",
                    }
                )

            # HTML documents
            for html in output_dir.rglob("*.html"):
                if "demos" in str(html):
                    continue
                rel_path = html.relative_to(output_dir)
                media_files.append(
                    {
                        "path": str(html),
                        "relative_path": str(rel_path),
                        "filename": html.name,
                        "type": "document",
                        "format": "html",
                        "size": html.stat().st_size,
                        "modified": datetime.fromtimestamp(html.stat().st_mtime).isoformat(),
                        "source": None,
                        "url": f"/media/{rel_path}",
                    }
                )

            # PDF files
            for pdf in output_dir.rglob("*.pdf"):
                rel_path = pdf.relative_to(output_dir)
                media_files.append(
                    {
                        "path": str(pdf),
                        "relative_path": str(rel_path),
                        "filename": pdf.name,
                        "type": "document",
                        "format": "pdf",
                        "size": pdf.stat().st_size,
                        "modified": datetime.fromtimestamp(pdf.stat().st_mtime).isoformat(),
                        "source": None,
                        "url": f"/media/{rel_path}",
                    }
                )

        by_type = {}
        for f in media_files:
            t = f["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(f)

        return {
            "total": len(media_files),
            "by_type": {t: len(files) for t, files in by_type.items()},
            "files": media_files,
            "output_dir": str(output_dir),
        }

    @router.get("/media/{path:path}")
    async def serve_media(path: str):
        """Serve media files from output directory."""
        project = get_project()
        file_path = project.output_dir / path
        if not file_path.exists():
            raise HTTPException(404, f"Media file not found: {path}")
        return FileResponse(file_path)
