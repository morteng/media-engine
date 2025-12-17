"""
FastAPI API Routes for Media Engine Dashboard

This package contains modular route handlers organized by functionality.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter, FastAPI

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_routes(
    app: "FastAPI",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
    static_dir: Path,
    set_project: Callable[[Path], "Project"] = None,
) -> "APIRouter":
    """
    Register all API routes on the FastAPI app.

    Routes are organized into modules:
    - core: Dashboard, project info, status, recent projects
    - translations: Translation routes
    - quality: Quality and validation routes
    - documents: Document listing, viewing, saving, chapters
    - registry: Document registry and packs routes
    - assets: Assets routes
    - media: Media files, serve routes
    - scene_notes: Scene notes routes
    - websocket: WebSocket endpoint

    Args:
        app: FastAPI application instance
        get_project: Function to get current project
        manager: WebSocket connection manager
        static_dir: Directory for static files
        set_project: Optional function to switch projects

    Returns:
        The configured APIRouter
    """
    from fastapi import APIRouter

    from .assets import register_assets_routes
    from .core import register_core_routes
    from .documents import register_document_routes
    from .media import register_media_routes
    from .quality import register_quality_routes
    from .registry import register_registry_routes
    from .scene_notes import register_scene_notes_routes
    from .translations import register_translation_routes
    from .websocket import register_websocket_routes

    # Create a single router for all routes
    router = APIRouter()

    # Register all route modules
    register_core_routes(router, get_project, manager, static_dir, set_project)
    register_translation_routes(router, get_project, manager)
    register_quality_routes(router, get_project, manager)
    register_document_routes(router, get_project, manager)
    register_registry_routes(router, get_project, manager)
    register_assets_routes(router, get_project, manager)
    register_media_routes(router, get_project, manager)
    register_scene_notes_routes(router, get_project, manager)
    register_websocket_routes(router, get_project, manager)

    # Include the router in the app
    app.include_router(router)

    return router


# Re-export for backwards compatibility and testing
from .helpers import find_source_demo, find_source_script

__all__ = ["register_routes", "find_source_script", "find_source_demo"]
