"""
Unit tests for media_engine.web module.

Tests websocket connection management.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from media_engine.web.websocket import ConnectionManager


class TestConnectionManager:
    """Tests for WebSocket ConnectionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager instance."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket object."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    def test_initialization(self, manager):
        """Test ConnectionManager initializes with empty state."""
        assert manager.active_connections == []
        assert manager.user_cursors == {}

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager, mock_websocket):
        """Test connect accepts the websocket connection."""
        await manager.connect(mock_websocket, "user1")
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_adds_to_active_connections(self, manager, mock_websocket):
        """Test connect adds websocket to active connections list."""
        await manager.connect(mock_websocket, "user1")
        assert mock_websocket in manager.active_connections
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_connect_broadcasts_user_joined(self, manager, mock_websocket):
        """Test connect broadcasts user_joined message."""
        # First connection doesn't broadcast (no one to send to)
        await manager.connect(mock_websocket, "user1")

        # Second connection should broadcast to first
        mock_websocket2 = MagicMock()
        mock_websocket2.accept = AsyncMock()
        mock_websocket2.send_json = AsyncMock()

        await manager.connect(mock_websocket2, "user2")

        # First websocket should receive user_joined message
        assert mock_websocket.send_json.called
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "user_joined"
        assert call_args["user_id"] == "user2"
        assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_active_connections(self, manager, mock_websocket):
        """Test disconnect removes websocket from active connections."""
        await manager.connect(mock_websocket, "user1")
        assert mock_websocket in manager.active_connections

        manager.disconnect(mock_websocket, "user1")
        assert mock_websocket not in manager.active_connections
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_disconnect_removes_user_cursor(self, manager, mock_websocket):
        """Test disconnect removes user cursor data."""
        await manager.connect(mock_websocket, "user1")
        manager.user_cursors["user1"] = {"file": "test.md", "line": 10, "col": 5}

        manager.disconnect(mock_websocket, "user1")
        assert "user1" not in manager.user_cursors

    def test_disconnect_nonexistent_websocket(self, manager):
        """Test disconnect handles websocket not in active connections."""
        mock_ws = MagicMock()
        # Should not raise exception
        manager.disconnect(mock_ws, "user1")
        assert len(manager.active_connections) == 0

    def test_disconnect_nonexistent_user_cursor(self, manager, mock_websocket):
        """Test disconnect handles user without cursor data."""
        manager.active_connections.append(mock_websocket)
        # Should not raise exception
        manager.disconnect(mock_websocket, "user1")
        assert len(manager.user_cursors) == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_all_connections(self, manager):
        """Test broadcast sends message to all active connections."""
        # Create three mock websockets
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        ws3 = MagicMock()
        ws3.accept = AsyncMock()
        ws3.send_json = AsyncMock()

        await manager.connect(ws1, "user1")
        await manager.connect(ws2, "user2")
        await manager.connect(ws3, "user3")

        # Broadcast a message
        test_message = {"type": "test", "data": "hello"}
        await manager.broadcast(test_message)

        # All websockets should receive the message
        ws1.send_json.assert_called_with(test_message)
        ws2.send_json.assert_called_with(test_message)
        ws3.send_json.assert_called_with(test_message)

    @pytest.mark.asyncio
    async def test_broadcast_excludes_specific_connection(self, manager):
        """Test broadcast can exclude a specific connection."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect(ws1, "user1")
        await manager.connect(ws2, "user2")

        # Reset send_json calls from connect broadcasts
        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()

        # Broadcast excluding ws1
        test_message = {"type": "test", "data": "hello"}
        await manager.broadcast(test_message, exclude=ws1)

        # Only ws2 should receive the message
        ws1.send_json.assert_not_called()
        ws2.send_json.assert_called_once_with(test_message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_exceptions(self, manager):
        """Test broadcast continues if send_json raises exception."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect(ws1, "user1")
        await manager.connect(ws2, "user2")

        ws1.send_json.reset_mock()
        ws2.send_json.reset_mock()

        # Should not raise exception
        test_message = {"type": "test", "data": "hello"}
        await manager.broadcast(test_message)

        # ws2 should still receive the message
        assert ws2.send_json.called

    @pytest.mark.asyncio
    async def test_update_cursor_stores_cursor_data(self, manager):
        """Test update_cursor stores cursor data in user_cursors dict."""
        await manager.update_cursor("user1", "test.md", 10, 5)

        assert "user1" in manager.user_cursors
        assert manager.user_cursors["user1"]["file"] == "test.md"
        assert manager.user_cursors["user1"]["line"] == 10
        assert manager.user_cursors["user1"]["col"] == 5

    @pytest.mark.asyncio
    async def test_update_cursor_overwrites_previous_data(self, manager):
        """Test update_cursor overwrites previous cursor position."""
        await manager.update_cursor("user1", "test.md", 10, 5)
        await manager.update_cursor("user1", "test.md", 20, 15)

        assert manager.user_cursors["user1"]["line"] == 20
        assert manager.user_cursors["user1"]["col"] == 15

    @pytest.mark.asyncio
    async def test_update_cursor_broadcasts_cursor_update(self, manager):
        """Test update_cursor broadcasts cursor_update message."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        await manager.connect(ws1, "user1")
        ws1.send_json.reset_mock()

        await manager.update_cursor("user2", "test.md", 10, 5)

        # Should broadcast cursor_update message
        assert ws1.send_json.called
        call_args = ws1.send_json.call_args[0][0]
        assert call_args["type"] == "cursor_update"
        assert call_args["user_id"] == "user2"
        assert call_args["file"] == "test.md"
        assert call_args["line"] == 10
        assert call_args["col"] == 5

    @pytest.mark.asyncio
    async def test_multiple_users_independent_cursors(self, manager):
        """Test multiple users maintain independent cursor positions."""
        await manager.update_cursor("user1", "file1.md", 10, 5)
        await manager.update_cursor("user2", "file2.md", 20, 15)
        await manager.update_cursor("user3", "file3.md", 30, 25)

        assert len(manager.user_cursors) == 3
        assert manager.user_cursors["user1"]["file"] == "file1.md"
        assert manager.user_cursors["user2"]["file"] == "file2.md"
        assert manager.user_cursors["user3"]["file"] == "file3.md"
