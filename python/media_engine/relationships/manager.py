"""
Registry Manager - Singleton for Unified Registry Access

Provides:
- Thread-safe singleton access to UnifiedRegistry
- In-memory caching with disk persistence
- File locking for concurrent access
- Event emission for change notifications
- Incremental update support
"""

import fcntl
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional, Set

from .registry import UnifiedRegistry
from .scanner import RelationshipScanner
from .staleness import StalenessTracker
from .types import ChangeInfo, DocumentNode, EdgeType, RelationshipEdge

if TYPE_CHECKING:
    from ..core.project import Project

logger = logging.getLogger(__name__)


class RegistryManager:
    """
    Singleton manager for the Unified Registry.

    Features:
    - Thread-safe access to a single registry instance
    - Lazy loading from disk
    - Incremental updates on file changes
    - Change event callbacks for WebSocket notifications
    - File locking for multi-process safety
    """

    _instance: Optional["RegistryManager"] = None
    _lock = threading.RLock()

    def __new__(cls, project: "Project" = None):
        """Singleton pattern with lazy initialization."""
        with cls._lock:
            if cls._instance is None:
                if project is None:
                    raise ValueError("Project required for first initialization")
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, project: "Project" = None):
        """Initialize the manager if not already done."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self.project = project
            self._registry: Optional[UnifiedRegistry] = None
            self._scanner: Optional[RelationshipScanner] = None
            self._staleness: Optional[StalenessTracker] = None

            # Change event callbacks
            self._callbacks: list[Callable[[ChangeInfo], None]] = []

            # Lock file for multi-process coordination
            self._lock_file = project.root / ".media-engine" / ".registry.lock"
            self._file_lock_handle = None

            # Track last scan time
            self._last_full_scan: Optional[datetime] = None

            self._initialized = True

    @classmethod
    def get_instance(cls, project: "Project" = None) -> "RegistryManager":
        """Get or create the singleton instance."""
        return cls(project)

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            if cls._instance:
                cls._instance._release_file_lock()
            cls._instance = None

    # =========================================================================
    # Registry Access
    # =========================================================================

    @property
    def registry(self) -> UnifiedRegistry:
        """Get the cached registry, loading if necessary."""
        with self._lock:
            if self._registry is None:
                self._registry = UnifiedRegistry(self.project)
                # If registry is empty, do initial scan
                if len(self._registry._nodes) == 0:
                    self.refresh()
            return self._registry

    @property
    def scanner(self) -> RelationshipScanner:
        """Get the relationship scanner."""
        if self._scanner is None:
            self._scanner = RelationshipScanner(self.project, self.registry)
        return self._scanner

    @property
    def staleness_tracker(self) -> StalenessTracker:
        """Get the staleness tracker."""
        if self._staleness is None:
            self._staleness = StalenessTracker(self.registry)
        return self._staleness

    # =========================================================================
    # Core Operations
    # =========================================================================

    def refresh(self) -> dict:
        """
        Full refresh of the registry from disk.

        Returns summary of the refresh operation.
        """
        with self._lock:
            self._acquire_file_lock()
            try:
                logger.info("Starting full registry refresh")
                start_time = datetime.now()

                # Clear and rescan
                self.registry._nodes.clear()
                self.registry._forward.clear()
                self.registry._reverse.clear()
                self.registry._anchors.clear()

                self.scanner.full_scan()
                self.registry.save()

                self._last_full_scan = datetime.now()
                elapsed = (datetime.now() - start_time).total_seconds()

                summary = {
                    "status": "refreshed",
                    "documents": len(self.registry._nodes),
                    "relationships": sum(len(e) for e in self.registry._forward.values()),
                    "elapsed_seconds": elapsed,
                }

                logger.info(f"Registry refresh complete: {summary}")
                return summary

            finally:
                self._release_file_lock()

    def reload(self):
        """Reload registry from disk (after external changes)."""
        with self._lock:
            self._registry = None  # Force reload on next access

    # =========================================================================
    # Incremental Updates
    # =========================================================================

    def on_file_change(self, path: Path, change_type: str) -> Optional[ChangeInfo]:
        """
        Handle a file change event.

        Args:
            path: Path to the changed file
            change_type: "created", "modified", or "deleted"

        Returns:
            ChangeInfo describing the impact of the change
        """
        with self._lock:
            self._acquire_file_lock()
            try:
                # Get existing node state
                old_node = self.registry.get_node(path)
                old_hash = old_node.content_hash if old_node else None

                if change_type == "deleted":
                    return self._handle_deletion(path, old_hash)
                elif change_type == "created":
                    return self._handle_creation(path)
                else:
                    return self._handle_modification(path, old_hash)

            finally:
                self._release_file_lock()

    def _handle_deletion(self, path: Path, old_hash: str) -> ChangeInfo:
        """Handle a deleted file."""
        # Find affected documents before removing
        affected = list(self.registry.get_impact(path))

        # Remove node and edges
        self.registry.remove_node(path)
        self.registry.save()

        change_info = ChangeInfo(
            document=path,
            change_type="deleted",
            old_hash=old_hash,
            new_hash=None,
            affected_documents=affected,
        )

        self._emit_change(change_info)
        return change_info

    def _handle_creation(self, path: Path) -> ChangeInfo:
        """Handle a created file."""
        # Scan the new document
        self.scanner.scan_document(path)
        self.registry.save()

        new_node = self.registry.get_node(path)
        new_hash = new_node.content_hash if new_node else None

        change_info = ChangeInfo(
            document=path,
            change_type="created",
            old_hash=None,
            new_hash=new_hash,
            affected_documents=[],
        )

        self._emit_change(change_info)
        return change_info

    def _handle_modification(self, path: Path, old_hash: str) -> ChangeInfo:
        """Handle a modified file."""
        # Rescan the document
        self.scanner.scan_document(path)

        # Get new state
        new_node = self.registry.get_node(path)
        new_hash = new_node.content_hash if new_node else None

        # Propagate staleness if content actually changed
        affected = []
        if old_hash != new_hash:
            affected = list(self.staleness_tracker.propagate_staleness(path))

        self.registry.save()

        change_info = ChangeInfo(
            document=path,
            change_type="modified",
            old_hash=old_hash,
            new_hash=new_hash,
            affected_documents=affected,
        )

        self._emit_change(change_info)
        return change_info

    def on_files_changed(self, changes: list[dict]) -> list[ChangeInfo]:
        """
        Handle multiple file changes.

        Args:
            changes: List of {"path": str, "type": str} dicts

        Returns:
            List of ChangeInfo for each changed file
        """
        results = []

        with self._lock:
            self._acquire_file_lock()
            try:
                for change in changes:
                    path = Path(change["path"])
                    change_type = change.get("type", "modified")

                    # Only process content files
                    if path.suffix.lower() not in (".md", ".yaml", ".yml"):
                        continue

                    result = self._process_single_change(path, change_type)
                    if result:
                        results.append(result)

                # Save once after all changes
                if results:
                    self.registry.save()

            finally:
                self._release_file_lock()

        return results

    def _process_single_change(
        self, path: Path, change_type: str
    ) -> Optional[ChangeInfo]:
        """Process a single file change without saving."""
        old_node = self.registry.get_node(path)
        old_hash = old_node.content_hash if old_node else None

        if change_type == "deleted":
            affected = list(self.registry.get_impact(path))
            self.registry.remove_node(path)

            return ChangeInfo(
                document=path,
                change_type="deleted",
                old_hash=old_hash,
                new_hash=None,
                affected_documents=affected,
            )

        elif change_type == "created":
            if path.exists():
                self.scanner.scan_document(path)
                new_node = self.registry.get_node(path)
                return ChangeInfo(
                    document=path,
                    change_type="created",
                    old_hash=None,
                    new_hash=new_node.content_hash if new_node else None,
                    affected_documents=[],
                )

        else:  # modified
            if path.exists():
                self.scanner.scan_document(path)
                new_node = self.registry.get_node(path)
                new_hash = new_node.content_hash if new_node else None

                affected = []
                if old_hash != new_hash:
                    affected = list(self.staleness_tracker.propagate_staleness(path))

                return ChangeInfo(
                    document=path,
                    change_type="modified",
                    old_hash=old_hash,
                    new_hash=new_hash,
                    affected_documents=affected,
                )

        return None

    # =========================================================================
    # Staleness Operations
    # =========================================================================

    def mark_fresh(self, doc_path: Path):
        """Mark a document and its relationships as fresh."""
        with self._lock:
            self._acquire_file_lock()
            try:
                self.staleness_tracker.mark_fresh(doc_path)
                self.registry.save()
            finally:
                self._release_file_lock()

    def mark_all_fresh(self):
        """Mark all documents as fresh."""
        with self._lock:
            self._acquire_file_lock()
            try:
                for node in self.registry.all_nodes():
                    self.staleness_tracker.mark_fresh(node.path)
                self.registry.save()
            finally:
                self._release_file_lock()

    def get_stale_documents(self) -> list[DocumentNode]:
        """Get all documents with stale relationships."""
        return self.registry.get_stale_documents()

    def check_staleness(self, doc_path: Path = None):
        """Check staleness for a document or all documents."""
        if doc_path:
            return self.staleness_tracker.check_document(doc_path)
        return self.staleness_tracker.check_all()

    # =========================================================================
    # Change Callbacks
    # =========================================================================

    def on_change(self, callback: Callable[[ChangeInfo], None]):
        """Register a callback for change events."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ChangeInfo], None]):
        """Remove a change callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _emit_change(self, change_info: ChangeInfo):
        """Emit a change event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(change_info)
            except Exception as e:
                logger.warning(f"Change callback error: {e}")

    # =========================================================================
    # File Locking
    # =========================================================================

    def _acquire_file_lock(self):
        """Acquire exclusive file lock for multi-process safety."""
        try:
            self._lock_file.parent.mkdir(parents=True, exist_ok=True)
            self._file_lock_handle = open(self._lock_file, "w")
            fcntl.flock(self._file_lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError):
            # Lock not available - wait for it
            if self._file_lock_handle:
                fcntl.flock(self._file_lock_handle.fileno(), fcntl.LOCK_EX)

    def _release_file_lock(self):
        """Release the file lock."""
        if self._file_lock_handle:
            try:
                fcntl.flock(self._file_lock_handle.fileno(), fcntl.LOCK_UN)
                self._file_lock_handle.close()
            except Exception:
                pass
            self._file_lock_handle = None

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def get_node(self, path: Path) -> Optional[DocumentNode]:
        """Get a document node."""
        return self.registry.get_node(path)

    def get_outgoing_edges(
        self, path: Path, edge_type: EdgeType = None
    ) -> list[RelationshipEdge]:
        """Get outgoing edges from a document."""
        return self.registry.get_outgoing_edges(path, edge_type)

    def get_incoming_edges(
        self, path: Path, edge_type: EdgeType = None
    ) -> list[RelationshipEdge]:
        """Get incoming edges to a document."""
        return self.registry.get_incoming_edges(path, edge_type)

    def get_impact(self, path: Path) -> Set[Path]:
        """Get all documents affected by a change to path."""
        return self.registry.get_impact(path)

    def get_translations(self, source: Path) -> list[RelationshipEdge]:
        """Get translations of a source document."""
        return self.registry.get_translations(source)

    def get_parent(self, path: Path) -> Optional[Path]:
        """Get parent document."""
        return self.registry.get_parent(path)

    def get_children(self, path: Path) -> list[Path]:
        """Get child documents."""
        return self.registry.get_children(path)

    def generate_report(self) -> dict:
        """Generate a comprehensive relationship report."""
        return self.registry.generate_report()


# =========================================================================
# Module-level convenience functions
# =========================================================================

_manager: Optional[RegistryManager] = None


def get_registry_manager(project: "Project" = None) -> Optional[RegistryManager]:
    """Get the global registry manager instance."""
    global _manager
    if _manager is None and project is not None:
        _manager = RegistryManager(project)
    return _manager


def init_registry_manager(project: "Project") -> RegistryManager:
    """Initialize the global registry manager."""
    global _manager
    RegistryManager.reset_instance()
    _manager = RegistryManager(project)
    return _manager


def reset_registry_manager():
    """Reset the global registry manager."""
    global _manager
    RegistryManager.reset_instance()
    _manager = None


__all__ = [
    "RegistryManager",
    "get_registry_manager",
    "init_registry_manager",
    "reset_registry_manager",
]
