"""
WebSocket endpoint for real-time collaboration.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_websocket_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register WebSocket endpoint."""
    from fastapi import WebSocket, WebSocketDisconnect

    @router.websocket("/ws/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, user_id: str):
        """WebSocket for real-time collaboration."""
        await manager.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_json()

                if data.get("type") == "cursor":
                    await manager.update_cursor(
                        user_id,
                        data.get("file", ""),
                        data.get("line", 0),
                        data.get("col", 0),
                    )
                elif data.get("type") == "edit":
                    await manager.broadcast(
                        {
                            "type": "edit",
                            "user_id": user_id,
                            "file": data.get("file"),
                            "changes": data.get("changes"),
                            "timestamp": datetime.now().isoformat(),
                        },
                        exclude=websocket,
                    )

        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            await manager.broadcast(
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
