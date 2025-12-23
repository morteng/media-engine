"""
FastAPI Application for Media Engine Dashboard

Provides REST API and WebSocket endpoints for:
- Project status and configuration
- Translation tracking and management
- Quality checks and validation
- Real-time collaboration
- Build operations
- Scene notes and suggestions
- Project switching and recent projects

Uses centralized settings from media_engine.settings for defaults.
"""

import webbrowser
from pathlib import Path
from typing import Optional

# FastAPI imports - graceful fallback
try:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None

import asyncio

from ..config.user_config import add_recent_project
from ..core.project import Project, find_project
from ..settings import WEB
from .routes import register_routes
from .watcher import start_watcher, stop_watcher
from .websocket import ConnectionManager


def create_app(project_path: Optional[Path] = None) -> "FastAPI":
    """
    Create FastAPI application for the dashboard.

    Args:
        project_path: Path to project root. If None, searches from cwd.

    Returns:
        FastAPI application instance
    """
    if not HAS_FASTAPI:
        raise RuntimeError("FastAPI not installed. Install with: pip install media-engine[web]")

    app = FastAPI(
        title="Media Engine Dashboard",
        description="Web interface for media-engine project management",
        version="1.0.0",
    )

    # CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # State
    manager = ConnectionManager()
    _project: Optional[Project] = None

    def get_project() -> Project:
        nonlocal _project
        if _project is None:
            if project_path:
                _project = Project.load(project_path)
            else:
                _project = find_project()
            if _project is None:
                raise HTTPException(404, "No project found")
            # Track in recent projects
            add_recent_project(str(_project.root), _project.config.name)
        return _project

    def set_project(path: Path) -> Project:
        """Switch to a different project."""
        nonlocal _project
        new_project = Project.load(path)
        if new_project is None:
            raise HTTPException(404, f"No project found at {path}")
        _project = new_project
        # Track in recent projects
        add_recent_project(str(_project.root), _project.config.name)
        return _project

    # Static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        # Also mount assets directory for Vite builds
        assets_dir = static_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Register all routes
    register_routes(app, get_project, manager, static_dir, set_project)

    # File watcher for live updates
    @app.on_event("startup")
    async def startup_watcher():
        """Start file watcher on server startup."""
        try:
            project = get_project()
            loop = asyncio.get_event_loop()
            start_watcher(project.root, manager, loop)
        except Exception:
            pass  # Watcher is optional

    @app.on_event("shutdown")
    async def shutdown_watcher():
        """Stop file watcher on server shutdown."""
        stop_watcher()

    return app


def run_dashboard(
    project_path: Optional[Path] = None,
    host: str = None,
    port: int = None,
    open_browser: bool = None,
):
    """
    Run the dashboard server.

    Args:
        project_path: Path to project root
        host: Host to bind to (default from settings)
        port: Port to bind to (default from settings)
        open_browser: Whether to open browser automatically (default from settings)
    """
    if not HAS_FASTAPI:
        raise RuntimeError("FastAPI not installed. Install with: pip install media-engine[web]")

    # Use settings defaults if not specified
    host = host or WEB.host
    port = port or WEB.port
    open_browser = open_browser if open_browser is not None else WEB.auto_open_browser

    app = create_app(project_path)

    if open_browser:
        import threading

        def open_browser_delayed():
            import time

            time.sleep(WEB.browser_open_delay)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=open_browser_delayed, daemon=True).start()

    uvicorn.run(app, host=host, port=port)
