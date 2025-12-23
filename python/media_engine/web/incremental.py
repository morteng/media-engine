"""
Incremental Registry Updates

Updates content registries incrementally when files change,
avoiding full rescans for better performance.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Set

if TYPE_CHECKING:
    from ..core.project import Project

logger = logging.getLogger(__name__)


class IncrementalUpdater:
    """
    Handles incremental updates to project registries.

    When files change:
    - Updates freshness registry for changed files
    - Updates translation status for changed translations
    - Updates dependency hashes for changed dependencies
    - Marks affected documents as potentially stale
    """

    def __init__(self, project: "Project"):
        self.project = project
        self._pending_updates: Set[str] = set()

    def on_file_change(self, changes: list[dict]) -> dict:
        """
        Process file changes and update registries incrementally.

        Args:
            changes: List of change events from file watcher
                Each has: path, type (created/modified/deleted), timestamp

        Returns:
            Summary of updates performed
        """
        result = {
            "freshness_updated": 0,
            "translations_updated": 0,
            "dependencies_updated": 0,
            "documents_marked_stale": 0,
            "errors": [],
        }

        # Group changes by type for efficient processing
        created = []
        modified = []
        deleted = []

        for change in changes:
            path = Path(change["path"])
            event_type = change.get("type", "modified")

            if event_type == "created":
                created.append(path)
            elif event_type == "deleted":
                deleted.append(path)
            else:
                modified.append(path)

        # Process deletions first
        for path in deleted:
            try:
                self._handle_deletion(path, result)
            except Exception as e:
                result["errors"].append(f"Delete {path}: {e}")

        # Process creations (new files)
        for path in created:
            try:
                self._handle_creation(path, result)
            except Exception as e:
                result["errors"].append(f"Create {path}: {e}")

        # Process modifications
        for path in modified:
            try:
                self._handle_modification(path, result)
            except Exception as e:
                result["errors"].append(f"Modify {path}: {e}")

        logger.debug(
            f"Incremental update: {result['freshness_updated']} freshness, "
            f"{result['translations_updated']} translations, "
            f"{result['dependencies_updated']} dependencies"
        )

        return result

    def _handle_deletion(self, path: Path, result: dict) -> None:
        """Handle a deleted file."""
        # Update freshness registry
        try:
            from ..freshness import FreshnessRegistry

            registry = FreshnessRegistry(self.project)
            rel_path = str(self._get_relative_path(path))

            if rel_path in registry.items:
                del registry.items[rel_path]
                registry.save()
                result["freshness_updated"] += 1
        except Exception as e:
            logger.debug(f"Could not update freshness for deletion: {e}")

        # Update dependency hashes
        try:
            from ..dependencies.hashes import DependencyHashTracker

            tracker = DependencyHashTracker(self.project)
            tracker.remove_document(path)
            result["dependencies_updated"] += 1
        except Exception as e:
            logger.debug(f"Could not update dependencies for deletion: {e}")

    def _handle_creation(self, path: Path, result: dict) -> None:
        """Handle a newly created file."""
        # Determine content type
        content_type = self._classify_path(path)
        if not content_type:
            return

        # Register in freshness
        try:
            from ..freshness import FreshnessRegistry
            from ..freshness.types import ContentType

            registry = FreshnessRegistry(self.project)
            registry.register(
                path=path,
                content_type=ContentType(content_type),
            )
            registry.save()
            result["freshness_updated"] += 1
        except Exception as e:
            logger.debug(f"Could not register in freshness: {e}")

        # Register dependencies if it's a document
        if path.suffix == ".md":
            try:
                from ..dependencies.hashes import DependencyHashTracker

                tracker = DependencyHashTracker(self.project)
                tracker.register_document(path)
                result["dependencies_updated"] += 1
            except Exception as e:
                logger.debug(f"Could not register dependencies: {e}")

    def _handle_modification(self, path: Path, result: dict) -> None:
        """Handle a modified file."""
        # Update freshness registry
        try:
            from ..freshness import FreshnessRegistry

            registry = FreshnessRegistry(self.project)
            rel_path = str(self._get_relative_path(path))

            if rel_path in registry.items:
                item = registry.items[rel_path]
                # Update hash and timestamp
                item.content_hash = registry._compute_hash(path)
                item.last_modified = datetime.fromtimestamp(path.stat().st_mtime)
                item.last_checked = datetime.now()
                item.freshness_status = registry._compute_freshness(item)
                registry.save()
                result["freshness_updated"] += 1
        except Exception as e:
            logger.debug(f"Could not update freshness: {e}")

        # Update translation status if it's a translation
        try:
            if self._is_translation(path):
                from ..cms.translation import TranslationTracker

                tracker = TranslationTracker(self.project)
                status = tracker.get_status_for_file(path)
                if status:
                    result["translations_updated"] += 1
        except Exception as e:
            logger.debug(f"Could not update translation status: {e}")

        # Update dependency hashes
        try:
            from ..dependencies.hashes import DependencyHashTracker

            tracker = DependencyHashTracker(self.project)

            # Update the document's own hash
            tracker.update_document_hash(path)

            # Check if any documents that depend on this one are now stale
            stale_dependents = tracker.check_dependents(path)
            result["documents_marked_stale"] += len(stale_dependents)
            result["dependencies_updated"] += 1
        except Exception as e:
            logger.debug(f"Could not update dependencies: {e}")

    def _get_relative_path(self, path: Path) -> Path:
        """Get path relative to project root."""
        try:
            if path.is_absolute():
                return path.relative_to(self.project.root)
            return path
        except ValueError:
            return path

    def _classify_path(self, path: Path) -> Optional[str]:
        """Classify a file path into a content type."""
        rel_path = str(self._get_relative_path(path))

        # Check if under content directory
        if not rel_path.startswith("content/"):
            return None

        suffix = path.suffix.lower()

        if suffix == ".md":
            if "/scripts/" in rel_path:
                return "video_script"
            return "source_document"
        elif suffix in (".yaml", ".yml"):
            if "/scripts/" in rel_path:
                return "video_script"
            return "source_document"
        elif suffix in (".mp4", ".webm"):
            return "video_render"
        elif suffix in (".mp3", ".wav"):
            return "voiceover_audio"
        elif suffix in (".png", ".jpg", ".jpeg", ".svg"):
            return "image_asset"

        return None

    def _is_translation(self, path: Path) -> bool:
        """Check if a file is a translation document."""
        if path.suffix != ".md":
            return False

        rel_path = str(self._get_relative_path(path))

        # Get source language from project
        source_lang = getattr(self.project, "source_language", "en")

        # If it's not in the source language directory, it might be a translation
        return f"/content/{source_lang}/" not in f"/{rel_path}/"


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
