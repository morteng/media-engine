"""
Core routes: dashboard, project info, status, recent projects.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_core_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
    static_dir: Path,
    set_project: Callable[[Path], "Project"] = None,
):
    """Register core dashboard and project routes."""
    from fastapi import HTTPException
    from fastapi.responses import FileResponse, HTMLResponse

    from ...config.user_config import (
        get_recent_projects,
        project_exists,
        remove_recent_project,
    )

    # === Dashboard Page ===

    @router.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve the main dashboard page."""
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        # React SPA not built - return simple message
        return HTMLResponse(
            """<!DOCTYPE html>
<html><head><title>Media Engine Dashboard</title></head>
<body style="font-family: system-ui; background: #0f172a; color: #e2e8f0; padding: 2rem;">
<h1>Dashboard Not Built</h1>
<p>The React SPA dashboard needs to be built. Run:</p>
<pre style="background: #1e293b; padding: 1rem; border-radius: 0.5rem;">
cd dashboard && npm install && npm run build
</pre>
<p>Then restart the server.</p>
</body></html>"""
        )

    # === Project API ===

    @router.get("/api/project")
    async def get_project_info():
        """Get project configuration and status."""
        project = get_project()
        return {
            "name": project.config.name,
            "description": project.config.description,
            "root": str(project.root),
            "languages": {
                code: {"name": lang.name, "locale": lang.locale}
                for code, lang in project.languages.items()
            },
            "source_language": project.source_language,
            "paths": {
                "content": str(project.content_dir),
                "assets": str(project.assets_dir),
                "output": str(project.output_dir),
                "publish": str(project.publish_dir),
            },
        }

    @router.get("/api/status")
    async def get_status():
        """Get comprehensive project status."""
        project = get_project()
        return project.get_status()

    # === Project Switching API ===

    @router.get("/api/recent-projects")
    async def list_recent_projects():
        """Get list of recently accessed projects."""
        projects = get_recent_projects()

        # Check which projects still exist
        result = []
        for p in projects:
            result.append(
                {
                    "path": p.path,
                    "name": p.name,
                    "last_accessed": p.last_accessed,
                    "exists": project_exists(p.path),
                }
            )

        # Get current project info
        current = None
        try:
            proj = get_project()
            current = {
                "path": str(proj.root),
                "name": proj.config.name,
            }
        except Exception:
            pass

        return {
            "current": current,
            "recent": result,
        }

    @router.post("/api/open-project")
    async def open_project(path: str):
        """Switch to a different project."""
        if not set_project:
            raise HTTPException(500, "Project switching not supported")

        project_path = Path(path)
        if not project_path.exists():
            raise HTTPException(404, f"Project path does not exist: {path}")

        if not (project_path / "project.yaml").exists():
            raise HTTPException(400, f"No project.yaml found at: {path}")

        try:
            new_project = set_project(project_path)

            # Notify connected clients of project switch
            await manager.broadcast(
                {
                    "type": "project_switched",
                    "project": {
                        "path": str(new_project.root),
                        "name": new_project.config.name,
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "status": "switched",
                "project": {
                    "path": str(new_project.root),
                    "name": new_project.config.name,
                },
            }
        except Exception as e:
            raise HTTPException(500, f"Failed to open project: {e}")

    @router.delete("/api/recent-projects")
    async def remove_from_recent(path: str):
        """Remove a project from the recent projects list."""
        removed = remove_recent_project(path)
        return {
            "status": "removed" if removed else "not_found",
            "path": path,
        }

    @router.post("/api/browse-project")
    async def browse_for_project():
        """Open a native file selection dialog to choose a project.yaml file."""
        import subprocess
        import sys

        file_path = None

        # Try AppleScript on macOS for reliable file picker
        if sys.platform == "darwin":
            try:
                script_lines = [
                    'tell application "System Events" to activate',
                    (
                        "set projectFile to POSIX path of (choose file with prompt "
                        '"Select project.yaml" of type {"yaml", "public.yaml"} '
                        "default location (path to home folder))"
                    ),
                    "return projectFile",
                ]
                result = subprocess.run(
                    ["osascript"] + [arg for line in script_lines for arg in ["-e", line]],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0 and result.stdout.strip():
                    file_path = result.stdout.strip()
            except Exception:
                pass

        # Fallback: return a prompt request
        if not file_path:
            return {"status": "prompt", "path": None, "message": "Enter project path manually"}

        # Validate that it's a project.yaml file
        selected_file = Path(file_path)
        if selected_file.name != "project.yaml":
            return {
                "status": "invalid",
                "path": file_path,
                "error": f"Please select a project.yaml file, not {selected_file.name}",
            }

        # Return the project directory (parent of project.yaml)
        project_dir = selected_file.parent
        return {"status": "selected", "path": str(project_dir)}

    # === Audit Log API ===

    @router.get("/api/audit-log")
    async def get_audit_log(limit: int = 100):
        """Get recent audit log entries."""
        import json

        project = get_project()
        log_path = project.root / ".media-engine" / "audit.log"

        if not log_path.exists():
            return {"entries": []}

        entries = []
        with open(log_path) as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        return {"entries": entries[-limit:]}

    # NOTE: SPA catch-all route is registered separately via register_spa_catch_all
    # to ensure it's registered LAST after all API routes


def register_spa_catch_all(
    router: "APIRouter",
    static_dir: Path,
):
    """
    Register the SPA catch-all route.

    IMPORTANT: This must be called LAST after all other routes are registered,
    otherwise it will match API routes before they can be handled.
    """
    from fastapi import HTTPException
    from fastapi.responses import FileResponse, HTMLResponse

    @router.get("/{full_path:path}", response_class=HTMLResponse)
    async def spa_catch_all(full_path: str):
        """
        Catch-all route for SPA frontend.

        Serves index.html for any route that doesn't match an API endpoint,
        allowing React Router to handle client-side routing.
        """
        # Don't serve index.html for API routes or static assets
        if full_path.startswith("api/") or full_path.startswith("static/"):
            raise HTTPException(404, "Not Found")

        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        return HTMLResponse(
            """<!DOCTYPE html>
<html><head><title>Media Engine Dashboard</title></head>
<body style="font-family: system-ui; background: #0f172a; color: #e2e8f0; padding: 2rem;">
<h1>Dashboard Not Built</h1>
<p>Build the React SPA: <code>cd dashboard && npm run build</code></p>
</body></html>"""
        )
