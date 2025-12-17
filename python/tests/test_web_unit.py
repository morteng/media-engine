"""
Unit tests for media_engine.web module.

Tests websocket connection management and dashboard HTML generation.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from media_engine.web.dashboard_html import generate_dashboard_html
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


class TestDashboardHTML:
    """Tests for dashboard HTML generation functions."""

    def test_generate_dashboard_html_returns_string(self):
        """Test generate_dashboard_html returns a string."""
        html = generate_dashboard_html()
        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_dashboard_html_is_valid_html(self):
        """Test generated HTML has proper structure."""
        html = generate_dashboard_html()

        # Check for essential HTML structure
        assert html.startswith("<!DOCTYPE html>")
        assert "<html" in html
        assert "<head>" in html
        assert "</head>" in html
        assert "<body>" in html
        assert "</body>" in html
        assert html.endswith("</html>")

    def test_dashboard_html_contains_title(self):
        """Test dashboard HTML contains title element."""
        html = generate_dashboard_html()
        assert "<title>Media Engine Dashboard</title>" in html

    def test_dashboard_html_contains_styles(self):
        """Test dashboard HTML contains CSS styles."""
        html = generate_dashboard_html()
        assert "<style>" in html
        assert "</style>" in html
        assert ":root" in html
        assert "var(--" in html  # CSS variables

    def test_dashboard_html_contains_javascript(self):
        """Test dashboard HTML contains JavaScript."""
        html = generate_dashboard_html()
        assert "<script>" in html
        assert "</script>" in html

    def test_dashboard_html_contains_tabs(self):
        """Test dashboard HTML contains navigation tabs."""
        html = generate_dashboard_html()

        # Check for tab elements
        assert 'class="tab' in html or 'class=\\"tab' in html

        # Check for expected tab names/IDs
        assert "overview" in html.lower()
        assert "documents" in html.lower()
        assert "translations" in html.lower()
        assert "quality" in html.lower()

    def test_dashboard_html_contains_cards(self):
        """Test dashboard HTML contains card components."""
        html = generate_dashboard_html()

        # Check for card elements
        assert 'class="card' in html

    def test_dashboard_html_contains_overview_tab(self):
        """Test dashboard HTML contains overview tab content."""
        html = generate_dashboard_html()
        assert "overview" in html.lower()

    def test_dashboard_html_contains_documents_tab(self):
        """Test dashboard HTML contains documents tab content."""
        html = generate_dashboard_html()
        assert "documents" in html.lower()

    def test_dashboard_html_contains_media_tab(self):
        """Test dashboard HTML contains media tab content."""
        html = generate_dashboard_html()
        assert "media" in html.lower()

    def test_dashboard_html_contains_packs_tab(self):
        """Test dashboard HTML contains packs tab content."""
        html = generate_dashboard_html()
        assert "packs" in html.lower()

    def test_dashboard_html_contains_assets_tab(self):
        """Test dashboard HTML contains assets tab content."""
        html = generate_dashboard_html()
        assert "assets" in html.lower()

    def test_dashboard_html_contains_translations_tab(self):
        """Test dashboard HTML contains translations tab content."""
        html = generate_dashboard_html()
        assert "translations" in html.lower()

    def test_dashboard_html_contains_quality_tab(self):
        """Test dashboard HTML contains quality tab content."""
        html = generate_dashboard_html()
        assert "quality" in html.lower()

    def test_dashboard_html_contains_activity_tab(self):
        """Test dashboard HTML contains activity tab content."""
        html = generate_dashboard_html()
        assert "activity" in html.lower()

    def test_dashboard_html_responsive_design(self):
        """Test dashboard HTML includes responsive design elements."""
        html = generate_dashboard_html()

        # Check for viewport meta tag
        assert "viewport" in html

        # Check for media queries
        assert "@media" in html

    def test_dashboard_html_dark_theme(self):
        """Test dashboard HTML includes dark theme styling."""
        html = generate_dashboard_html()

        # Check for dark theme color variables
        assert "--bg:" in html
        assert "--bg-card:" in html
        assert "0f172a" in html or "#0f172a" in html  # Dark background color

    def test_dashboard_html_contains_status_badges(self):
        """Test dashboard HTML includes status badge styles."""
        html = generate_dashboard_html()
        assert "status-badge" in html or "status-ok" in html or "status-warn" in html

    def test_dashboard_html_contains_grid_layouts(self):
        """Test dashboard HTML includes grid layout classes."""
        html = generate_dashboard_html()
        assert "grid" in html
        assert "grid-template-columns" in html

    def test_dashboard_html_contains_websocket_connection(self):
        """Test dashboard HTML includes WebSocket connection code."""
        html = generate_dashboard_html()
        assert "WebSocket" in html or "websocket" in html.lower()

    def test_dashboard_html_contains_api_endpoints(self):
        """Test dashboard HTML references API endpoints."""
        html = generate_dashboard_html()
        # Should contain API endpoint references
        assert "/api/" in html

    def test_dashboard_html_no_script_injection(self):
        """Test dashboard HTML doesn't contain obvious script injection."""
        html = generate_dashboard_html()

        # Should not contain dangerous patterns
        assert "<script>alert(" not in html
        assert "javascript:void" not in html
        assert "onerror=" not in html.lower()

    def test_dashboard_html_consistent_structure(self):
        """Test dashboard HTML structure is consistent across calls."""
        html1 = generate_dashboard_html()
        html2 = generate_dashboard_html()

        # Should generate identical HTML (no random elements)
        assert html1 == html2

    def test_dashboard_html_contains_document_browser(self):
        """Test dashboard HTML includes document browser interface."""
        html = generate_dashboard_html()
        assert "doc-browser" in html or "document" in html.lower()

    def test_dashboard_html_contains_translation_matrix(self):
        """Test dashboard HTML includes translation matrix view."""
        html = generate_dashboard_html()
        assert "matrix" in html.lower() or "translation" in html.lower()

    def test_dashboard_html_contains_quality_issues(self):
        """Test dashboard HTML includes quality issue tracking."""
        html = generate_dashboard_html()
        assert "quality" in html.lower() or "issue" in html.lower()

    def test_dashboard_html_no_inline_user_data(self):
        """Test dashboard HTML doesn't contain hardcoded user data."""
        html = generate_dashboard_html()

        # Should not contain hardcoded user names, emails, etc.
        # (data should be loaded dynamically via API)
        assert "@example.com" not in html
        assert "John Doe" not in html

    def test_dashboard_html_contains_loading_states(self):
        """Test dashboard HTML includes loading state indicators."""
        html = generate_dashboard_html()
        assert "loading" in html.lower() or "loader" in html.lower()

    def test_dashboard_html_contains_empty_states(self):
        """Test dashboard HTML includes empty state messaging."""
        html = generate_dashboard_html()
        assert "empty" in html.lower() or "no data" in html.lower() or "empty-state" in html

    def test_dashboard_html_reasonable_size(self):
        """Test dashboard HTML is a reasonable size."""
        html = generate_dashboard_html()

        # Should be substantial but not excessively large
        # Reasonable range: 10KB to 500KB for embedded HTML
        size_kb = len(html) / 1024
        assert 10 < size_kb < 500, f"HTML size {size_kb:.2f}KB is outside reasonable range"

    def test_dashboard_html_uses_semantic_html(self):
        """Test dashboard HTML uses semantic HTML elements."""
        html = generate_dashboard_html()

        # Check for semantic elements
        assert "<header>" in html or "<nav>" in html or "<main>" in html or "<section>" in html

    def test_dashboard_html_contains_metadata(self):
        """Test dashboard HTML contains proper metadata."""
        html = generate_dashboard_html()

        # Check for charset and viewport
        assert 'charset="UTF-8"' in html
        assert "viewport" in html

    def test_dashboard_html_color_variables_defined(self):
        """Test dashboard HTML defines color CSS variables."""
        html = generate_dashboard_html()

        # Check for essential color variables
        assert "--primary:" in html
        assert "--bg:" in html
        assert "--text:" in html

    def test_dashboard_html_contains_fetch_calls(self):
        """Test dashboard HTML includes fetch API calls for data loading."""
        html = generate_dashboard_html()
        assert "fetch(" in html

    def test_dashboard_html_contains_event_listeners(self):
        """Test dashboard HTML includes event listeners for interactivity."""
        html = generate_dashboard_html()
        assert "addEventListener" in html or "onclick" in html.lower()
