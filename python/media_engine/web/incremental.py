"""
Incremental Registry Updates

Updates the unified registry when files change, avoiding full rescans.
Integrates with the RegistryManager singleton for thread-safe updates.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..core.project import Project

logger = logging.getLogger(__name__)


class IncrementalUpdater:
    """
    Handles incremental updates to the unified registry.

    When files change:
    - Updates document nodes and relationships
    - Propagates staleness to affected documents
    - Emits change events for WebSocket notifications
    """

    def __init__(self, project: "Project"):
        self.project = project
        self._manager = None

    @property
    def manager(self):
        """Lazy-load the registry manager."""
        if self._manager is None:
            from ..relationships import get_registry_manager, init_registry_manager

            self._manager = get_registry_manager(self.project)
            if self._manager is None:
                self._manager = init_registry_manager(self.project)
        return self._manager

    def on_file_change(self, changes: list[dict]) -> dict:
        """
        Process file changes and update the unified registry.

        Args:
            changes: List of change events from file watcher
                Each has: path, type (created/modified/deleted), timestamp

        Returns:
            Summary of updates performed
        """
        result = {
            "documents_updated": 0,
            "documents_deleted": 0,
            "documents_created": 0,
            "documents_affected": 0,
            "errors": [],
        }

        # Filter to content files only
        content_changes = []
        for change in changes:
            path = Path(change["path"])

            # Only process content files
            if not self._is_content_file(path):
                continue

            content_changes.append(change)

        if not content_changes:
            return result

        # Process changes through the manager
        try:
            change_infos = self.manager.on_files_changed(content_changes)

            for info in change_infos:
                if info.change_type == "deleted":
                    result["documents_deleted"] += 1
                elif info.change_type == "created":
                    result["documents_created"] += 1
                else:
                    result["documents_updated"] += 1

                result["documents_affected"] += len(info.affected_documents)

        except Exception as e:
            logger.error(f"Failed to process changes: {e}")
            result["errors"].append(str(e))

        logger.debug(
            f"Incremental update: {result['documents_updated']} updated, "
            f"{result['documents_created']} created, "
            f"{result['documents_deleted']} deleted, "
            f"{result['documents_affected']} affected"
        )

        return result

    def _is_content_file(self, path: Path) -> bool:
        """Check if a file is a content file we should track."""
        # Check suffix
        if path.suffix.lower() not in (".md", ".yaml", ".yml"):
            return False

        # Check if under content directory
        try:
            rel_path = path.relative_to(self.project.root)
            return str(rel_path).startswith("content/")
        except ValueError:
            return False

    def refresh_all(self) -> dict:
        """Force a full refresh of the registry."""
        return self.manager.refresh()


# Global instance
_updater: Optional[IncrementalUpdater] = None


def get_incremental_updater(project: "Project" = None) -> Optional[IncrementalUpdater]:
    """Get or create the global incremental updater."""
    global _updater

    if _updater is None and project is not None:
        _updater = IncrementalUpdater(project)

    return _updater


def process_file_changes(changes: list[dict], project: "Project") -> dict:
    """Process file changes incrementally."""
    updater = get_incremental_updater(project)
    if updater:
        return updater.on_file_change(changes)
    return {"error": "No updater available"}


def reset_updater():
    """Reset the global updater (for testing)."""
    global _updater
    _updater = None
