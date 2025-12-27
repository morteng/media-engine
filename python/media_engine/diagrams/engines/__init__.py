"""
Diagram Engines Package

Provides pluggable diagram rendering engines.
"""

from .base import DiagramEngine, EngineCapability, EngineInfo
from .registry import (
    engine_summary,
    get_available_engines,
    get_best_engine,
    get_engine,
    get_engine_for_format,
    get_engine_names,
    get_install_hints,
    get_installed_engines,
    register_engine,
    unregister_engine,
)


# Auto-register built-in engines
def _auto_register() -> None:
    """Auto-register available engines."""
    # Matplotlib engine (always available)
    from .matplotlib_engine import MatplotlibEngine

    register_engine("matplotlib", MatplotlibEngine)

    # D2 engine (requires D2 CLI for rendering)
    from .d2_engine import D2Engine
    register_engine("d2", D2Engine)

    # Excalidraw engine (uses Kroki.io API)
    from .excalidraw_engine import ExcalidrawEngine
    register_engine("excalidraw", ExcalidrawEngine)


# Run auto-registration on import
_auto_register()


__all__ = [
    # Base classes
    "DiagramEngine",
    "EngineCapability",
    "EngineInfo",
    # Registry functions
    "register_engine",
    "unregister_engine",
    "get_engine",
    "get_available_engines",
    "get_installed_engines",
    "get_engine_names",
    "get_best_engine",
    "get_engine_for_format",
    "get_install_hints",
    "engine_summary",
]
