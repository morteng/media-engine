"""
FastAPI API Routes for Media Engine Dashboard

This is a backwards-compatibility wrapper that imports from the routes package.
The actual route implementations are in python/media_engine/web/routes/*.py
"""

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import FastAPI

    from ..core.project import Project
    from .websocket import ConnectionManager


def register_routes(
    app: "FastAPI",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
    static_dir: Path,
    set_project: Callable[[Path], "Project"] = None,
):
    """
    Register all API routes on the FastAPI app.

    This is a backwards-compatibility wrapper. The actual implementation
    is in the routes package (python/media_engine/web/routes/).

    Args:
        app: FastAPI application instance
        get_project: Function to get current project
        manager: WebSocket connection manager
        static_dir: Directory for static files
        set_project: Optional function to switch projects
    """
    from .routes import register_routes as _register_routes

    return _register_routes(app, get_project, manager, static_dir, set_project)
