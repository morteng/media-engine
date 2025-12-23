"""
File system watcher for real-time content updates.

Monitors the project content directory and broadcasts changes
to connected dashboard clients via WebSocket.
"""

import asyncio
import logging
import threading
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .websocket import ConnectionManager


class FileWatcher:
    """
    Watches project files for changes and broadcasts updates.

    Uses watchdog for efficient file system monitoring with
    debouncing to prevent rapid-fire updates.
    """

    def __init__(
        self,
        project_root: Path,
        connection_manager: "ConnectionManager",
        debounce_seconds: float = 1.0,
    ):
        self.project_root = project_root
        self.content_dir = project_root / "content"
        self.connection_manager = connection_manager
        self.debounce_seconds = debounce_seconds

        self._observer = None
        self._pending_events: dict[str, dict] = {}
        self._debounce_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False

        # Track what types of changes occurred
        self._change_types: dict[str, set] = defaultdict(set)

    def start(self, loop: asyncio.AbstractEventLoop):
        """Start watching for file changes."""
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            logger.warning("watchdog not installed, file watching disabled")
            return

        self._loop = loop
        self._running = True

        class Handler(FileSystemEventHandler):
            def __init__(handler_self, watcher: "FileWatcher"):
                handler_self.watcher = watcher

            def on_any_event(handler_self, event):
                if event.is_directory:
                    return

                # Filter to relevant file types
                path = Path(event.src_path)
                if path.suffix.lower() not in (".md", ".yaml", ".yml", ".json"):
                    return

                # Skip hidden files and .media-engine directory
                if any(part.startswith(".") for part in path.parts):
                    return

                handler_self.watcher._queue_event(event)

        self._observer = Observer()
        self._observer.schedule(
            Handler(self),
            str(self.project_root),
            recursive=True,
        )
        self._observer.start()
        logger.info(f"File watcher started for {self.project_root}")

    def stop(self):
        """Stop watching for file changes."""
        self._running = False
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        if self._debounce_task:
            self._debounce_task.cancel()
        logger.info("File watcher stopped")

    def _queue_event(self, event):
        """Queue a file event for debounced processing."""
        path = event.src_path
        event_type = event.event_type  # created, modified, deleted, moved

        # Track the change
        self._pending_events[path] = {
            "path": path,
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
        }
        self._change_types[self._categorize_path(path)].add(event_type)

        # Schedule debounced broadcast
        if self._loop:
            self._loop.call_soon_threadsafe(self._schedule_broadcast)

    def _categorize_path(self, path: str) -> str:
        """Categorize a file path for change grouping."""
        p = Path(path)

        # Check if in content directory
        try:
            rel = p.relative_to(self.content_dir)
            parts = rel.parts

            if len(parts) >= 2:
                # content/<lang>/chapters, scripts, etc.
                return f"{parts[0]}_{parts[1]}"
            return "content"
        except ValueError:
            pass

        # Check for other project files
        if p.name == "project.yaml":
            return "config"
        if p.name == "brand.yaml" or p.name == "theme.yaml":
            return "brand"
        if p.suffix == ".json" and ".media-engine" in str(p):
            return "registry"

        return "other"

    def _schedule_broadcast(self):
        """Schedule a debounced broadcast."""
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        self._debounce_task = asyncio.create_task(self._debounced_broadcast())

    async def _debounced_broadcast(self):
        """Wait for debounce period then broadcast changes."""
        await asyncio.sleep(self.debounce_seconds)

        if not self._pending_events:
            return

        # Collect changes
        events = list(self._pending_events.values())
        categories = dict(self._change_types)

        # Clear pending
        self._pending_events.clear()
        self._change_types.clear()

        # Determine what data needs refreshing
        refresh_types = set()
        for category, _ in categories.items():
            if category.endswith("_chapters"):
                refresh_types.add("documents")
                refresh_types.add("translations")
                refresh_types.add("quality")
            elif category.endswith("_scripts"):
                refresh_types.add("documents")
                refresh_types.add("media")
            elif category == "config":
                refresh_types.add("project")
                refresh_types.add("all")
            elif category == "brand":
                refresh_types.add("brand")
            elif category == "registry":
                refresh_types.add("freshness")
            else:
                refresh_types.add("documents")

        # Broadcast to all connected clients
        await self.connection_manager.broadcast({
            "type": "file_change",
            "timestamp": datetime.now().isoformat(),
            "changes": events,
            "categories": {k: list(v) for k, v in categories.items()},
            "refresh": list(refresh_types),
        })

        logger.debug(f"Broadcast file changes: {len(events)} files, refresh: {refresh_types}")


# Global instance for the application
_watcher: Optional[FileWatcher] = None


def get_watcher() -> Optional[FileWatcher]:
    """Get the global file watcher instance."""
    return _watcher


def start_watcher(
    project_root: Path,
    connection_manager: "ConnectionManager",
    loop: asyncio.AbstractEventLoop,
) -> FileWatcher:
    """Start the global file watcher."""
    global _watcher
    if _watcher:
        _watcher.stop()

    _watcher = FileWatcher(project_root, connection_manager)
    _watcher.start(loop)
    return _watcher


def stop_watcher():
    """Stop the global file watcher."""
    global _watcher
    if _watcher:
        _watcher.stop()
        _watcher = None
