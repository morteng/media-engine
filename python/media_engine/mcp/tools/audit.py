"""Audit logging tools."""

import json
from datetime import datetime


def register_audit_tools(mcp, server_instance):
    """Register audit-related MCP tools."""

    @mcp.tool()
    async def log_action(action: str, details: str = None, user: str = None) -> str:
        """
        Log an action to the audit trail.

        Args:
            action: Action description (e.g., "document_updated")
            details: Additional details (optional)
            user: User identifier (optional)
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...audit import log_action as do_log

        do_log(server_instance.project, action, details, user)

        return json.dumps(
            {
                "status": "logged",
                "action": action,
                "timestamp": datetime.now().isoformat(),
            },
            indent=2,
        )

    @mcp.tool()
    async def get_audit_log(limit: int = 50) -> str:
        """
        Get recent audit log entries.

        Args:
            limit: Maximum entries to return (default: 50)
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...audit import get_recent_entries

        entries = get_recent_entries(server_instance.project, limit)

        return json.dumps(
            {
                "count": len(entries),
                "entries": entries,
            },
            indent=2,
        )
