"""
WebSocket Connection Manager for Real-time Collaboration
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
