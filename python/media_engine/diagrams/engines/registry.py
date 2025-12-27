"""
Engine Registry Module

Manages registration and discovery of diagram engines.
"""

from typing import Optional, Type

from .base import DiagramEngine, EngineCapability, EngineInfo

# Global engine registry
_ENGINES: dict[str, Type[DiagramEngine]] = {}


def register_engine(name: str, engine_class: Type[DiagramEngine]) -> None:
    """
    Register a diagram engine.

    Args:
        name: Engine name (lowercase identifier)
        engine_class: Engine class (must inherit from DiagramEngine)
    """
    if not issubclass(engine_class, DiagramEngine):
        raise TypeError(f"{engine_class} must inherit from DiagramEngine")
    _ENGINES[name.lower()] = engine_class


def unregister_engine(name: str) -> bool:
    """
    Unregister a diagram engine.

    Args:
        name: Engine name

    Returns:
        True if engine was removed, False if not found
    """
    return _ENGINES.pop(name.lower(), None) is not None


def get_engine(name: str) -> Optional[Type[DiagramEngine]]:
    """
    Get engine class by name.

    Args:
        name: Engine name (case-insensitive)

    Returns:
        Engine class or None if not found
    """
    return _ENGINES.get(name.lower())


def get_available_engines() -> list[EngineInfo]:
    """
    Get list of all registered engines with their info.

    Returns:
        List of EngineInfo for all registered engines
    """
    engines = []
    for name, engine_class in _ENGINES.items():
        info = engine_class.get_info()
        # Update installed status based on actual availability
        info.installed = engine_class.is_available()
        engines.append(info)
    return engines


def get_installed_engines() -> list[EngineInfo]:
    """
    Get list of engines that are installed and ready to use.

    Returns:
        List of EngineInfo for available engines only
    """
    return [e for e in get_available_engines() if e.installed]


def get_engine_names() -> list[str]:
    """
    Get list of all registered engine names.

    Returns:
        List of engine names
    """
    return list(_ENGINES.keys())


def get_best_engine(
    capabilities: Optional[list[EngineCapability]] = None,
    output_format: str = "png",
    prefer_installed: bool = True,
) -> Optional[Type[DiagramEngine]]:
    """
    Select best available engine for requirements.

    Args:
        capabilities: Required capabilities
        output_format: Output format needed
        prefer_installed: If True, prefer installed engines

    Returns:
        Best matching engine class or None
    """
    candidates = []

    for name, engine_class in _ENGINES.items():
        info = engine_class.get_info()
        is_installed = engine_class.is_available()

        # Skip if prefer_installed and not available
        if prefer_installed and not is_installed:
            continue

        # Check format support
        if not info.supports_format(output_format):
            continue

        # Check capabilities
        if capabilities:
            missing = [c for c in capabilities if not info.has_capability(c)]
            if missing:
                continue

        # Calculate score
        score = len(info.capabilities)
        if is_installed:
            score += 100  # Strongly prefer installed engines

        candidates.append((score, name, engine_class))

    if not candidates:
        return None

    # Sort by score descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][2]


def get_engine_for_format(output_format: str) -> Optional[Type[DiagramEngine]]:
    """
    Get first available engine that supports an output format.

    Args:
        output_format: Desired output format (png, svg, pdf, etc.)

    Returns:
        Engine class or None
    """
    for engine_class in _ENGINES.values():
        if not engine_class.is_available():
            continue
        info = engine_class.get_info()
        if info.supports_format(output_format):
            return engine_class
    return None


def get_install_hints() -> dict[str, str]:
    """
    Get installation hints for all non-installed engines.

    Returns:
        Dict of engine name to installation instructions
    """
    hints = {}
    for name, engine_class in _ENGINES.items():
        if not engine_class.is_available():
            hints[name] = engine_class.get_install_hint()
    return hints


def engine_summary() -> str:
    """
    Get a summary of all engines and their status.

    Returns:
        Multi-line string summary
    """
    lines = ["Diagram Engines:"]
    for info in get_available_engines():
        status = "installed" if info.installed else "not installed"
        caps = ", ".join(c.value for c in info.capabilities[:3])
        if len(info.capabilities) > 3:
            caps += f" (+{len(info.capabilities) - 3} more)"
        lines.append(f"  {info.name}: {status}")
        lines.append(f"    Formats: {', '.join(info.formats)}")
        lines.append(f"    Capabilities: {caps}")
    return "\n".join(lines)
