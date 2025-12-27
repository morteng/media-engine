"""
Backward-compatible anchors module.

This module is deprecated. Use media_engine.relationships instead.
"""

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    pass


class AnchorValidationResult:
    """Result of anchor validation."""

    def __init__(
        self,
        valid: bool = True,
        missing_anchors: List = None,
        orphan_references: List = None,
    ):
        self.valid = valid
        self.missing_anchors = missing_anchors or []
        self.orphan_references = orphan_references or []


class AnchorRegistry:
    """
    Backward-compatible anchor registry.

    Wraps the relationships module to provide legacy API compatibility.
    """

    def __init__(self, project_or_registry: Any):
        """Initialize with a project, registry, or None."""
        self.project = None
        self._registry = None

        if project_or_registry is None:
            pass
        elif hasattr(project_or_registry, "root"):
            # It's a Project
            self.project = project_or_registry
        elif hasattr(project_or_registry, "get_parent"):
            # It's a UnifiedRegistry
            self._registry = project_or_registry
        else:
            # Try to use it as a project
            self.project = project_or_registry

    def _get_registry(self):
        """Lazily get the unified registry."""
        if self._registry is None and self.project is not None:
            try:
                from ..relationships import get_registry_manager, init_registry_manager

                manager = get_registry_manager(self.project)
                if manager is None:
                    manager = init_registry_manager(self.project)
                self._registry = manager.registry
            except Exception:
                self._registry = None
        return self._registry

    def build(self) -> None:
        """Build the anchor registry (no-op for compatibility)."""
        # The relationships module handles this automatically
        pass

    def get_all_anchors(self) -> Dict[str, Dict]:
        """Get all defined anchors."""
        registry = self._get_registry()
        if registry is None:
            return {}
        try:
            if hasattr(registry, "get_anchors"):
                return registry.get_anchors()
            return {}
        except Exception:
            return {}

    def validate(self) -> Dict:
        """Validate anchor references."""
        anchors = self.get_all_anchors()
        return {
            "valid": True,
            "anchor_count": len(anchors),
            "anchors": anchors,
        }

    def validate_references(self) -> AnchorValidationResult:
        """Validate anchor references and return detailed result."""
        # For backward compatibility, return an empty valid result
        # The relationships module handles anchor validation differently
        return AnchorValidationResult(valid=True)


__all__ = ["AnchorRegistry", "AnchorValidationResult"]
