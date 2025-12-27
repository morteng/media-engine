"""
FastAPI API Routes for Media Engine Dashboard

This package contains modular route handlers organized by functionality.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from .helpers import find_source_demo, find_source_script

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

    from .ai import register_ai_routes
    from .assets import register_assets_routes
    from .brand import register_brand_routes
    from .build import register_build_routes
    from .core import register_core_routes, register_spa_catch_all
    from .dependencies import register_dependencies_routes
    from .diagrams import register_diagram_routes
    from .documents import register_document_routes
    from .freshness import register_freshness_routes
    from .hierarchy import register_hierarchy_routes
    from .insights import register_insights_routes
    from .media import register_media_routes
    from .notes import register_notes_routes
    from .provenance import register_provenance_routes
    from .publications import register_publications_routes
    from .quality import register_quality_routes
    from .registry import register_registry_routes
    from .scene_notes import register_scene_notes_routes
    from .search import register_search_routes
    from .settings import register_settings_routes
    from .translations import register_translation_routes
    from .websocket import register_websocket_routes

    # Create a single router for all routes
    router = APIRouter()

    # Register all route modules
    register_core_routes(router, get_project, manager, static_dir, set_project)
    register_settings_routes(router, get_project, manager)
    register_ai_routes(router, get_project, manager)
    register_brand_routes(router, get_project, manager)
    register_translation_routes(router, get_project, manager)
    register_quality_routes(router, get_project, manager)
    register_freshness_routes(router, get_project, manager)
    register_hierarchy_routes(router, get_project, manager)
    register_provenance_routes(router, get_project, manager)
    register_publications_routes(router, get_project, manager)
    register_build_routes(router, get_project, manager)
    register_diagram_routes(router, get_project, manager)
    register_search_routes(router, get_project, manager)
    register_dependencies_routes(router, get_project, manager)
    register_insights_routes(router, get_project, manager)
    register_document_routes(router, get_project, manager)
    register_registry_routes(router, get_project, manager)
    register_assets_routes(router, get_project, manager)
    register_media_routes(router, get_project, manager)
    register_notes_routes(router, get_project, manager)
    register_scene_notes_routes(router, get_project, manager)
    register_websocket_routes(router, get_project, manager)

    # IMPORTANT: SPA catch-all must be registered LAST
    # to avoid matching API routes before they can be handled
    register_spa_catch_all(router, static_dir)

    # Include the router in the app
    app.include_router(router)

    return router


__all__ = ["register_routes", "find_source_script", "find_source_demo"]
