"""
WebSocket Connection Manager for Real-time Collaboration

Broadcasts:
- User presence (join/leave)
- Cursor positions
- File changes
- Registry updates (staleness, relationships)
"""

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration."""

    def __init__(self):
        self.active_connections: list["WebSocket"] = []
        self.user_cursors: dict[str, dict] = {}  # user_id -> {file, line, col}

    async def connect(self, websocket: "WebSocket", user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Notify others of new user
        await self.broadcast(
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            },
            exclude=websocket,
        )

    def disconnect(self, websocket: "WebSocket", user_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_cursors:
            del self.user_cursors[user_id]

    async def broadcast(self, message: dict, exclude: "WebSocket" = None):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def update_cursor(self, user_id: str, file: str, line: int, col: int):
        self.user_cursors[user_id] = {"file": file, "line": line, "col": col}
        await self.broadcast(
            {
                "type": "cursor_update",
                "user_id": user_id,
                "file": file,
                "line": line,
                "col": col,
            }
        )

    async def broadcast_registry_update(self, change_info: dict):
        """
        Broadcast a registry update to all connected clients.

        Args:
            change_info: Information about what changed, containing:
                - document: Path of changed document
                - change_type: created, modified, deleted
                - affected_documents: List of affected document paths
                - old_hash, new_hash: Content hashes
        """
        await self.broadcast({
            "type": "registry_update",
            "timestamp": datetime.now().isoformat(),
            "document": str(change_info.get("document", "")),
            "change_type": change_info.get("change_type", "modified"),
            "affected_count": len(change_info.get("affected_documents", [])),
            "affected_documents": [
                str(p) for p in change_info.get("affected_documents", [])[:20]
            ],
            "content_changed": change_info.get("old_hash") != change_info.get("new_hash"),
            "refresh": ["hierarchy", "dependencies", "translations", "quality"],
        })

    async def broadcast_staleness_update(self, stale_documents: list):
        """
        Broadcast staleness updates to all connected clients.

        Args:
            stale_documents: List of documents that are now stale
        """
        await self.broadcast({
            "type": "staleness_update",
            "timestamp": datetime.now().isoformat(),
            "stale_count": len(stale_documents),
            "stale_documents": [
                {
                    "path": str(doc.get("path", "")),
                    "title": doc.get("title", ""),
                    "reasons": doc.get("reasons", []),
                }
                for doc in stale_documents[:20]
            ],
            "refresh": ["hierarchy", "dependencies", "quality"],
        })

    def sync_broadcast(self, message: dict):
        """
        Synchronous broadcast for use in callbacks.

        Schedules async broadcast on event loop.
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(message))
        except RuntimeError:
            # No running loop, can't broadcast
            pass
