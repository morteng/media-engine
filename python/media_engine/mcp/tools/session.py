"""Session context and agent audit tools.

Provides tools for managing agent session state and maintaining
an audit trail of agent actions with reasoning.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import MediaEngineMCPServer

# In-memory session storage (persists for server lifetime)
_session_store: dict = {}
_agent_actions: list = []


def register_session_tools(mcp, server_instance: "MediaEngineMCPServer"):
    """Register session context and audit MCP tools."""

    @mcp.tool()
    async def set_session_context(key: str, value: str) -> str:
        """
        Store context for this agent session.

        Use this to remember information across tool calls:
        - Current task or goal
        - User preferences discovered during work
        - Important findings to reference later

        Args:
            key: Context key (e.g., "current_task", "user_preference")
            value: Context value (string or JSON string for complex data)

        Returns:
            Confirmation of stored context.
        """
        _session_store[key] = {
            "value": value,
            "set_at": datetime.now().isoformat(),
        }

        return json.dumps(
            {
                "status": "stored",
                "key": key,
                "timestamp": _session_store[key]["set_at"],
            },
            indent=2,
        )

    @mcp.tool()
    async def get_session_context(key: str = None) -> str:
        """
        Retrieve stored session context.

        Args:
            key: Specific key to retrieve, or None to get all context

        Returns:
            Stored context value(s).
        """
        if key:
            if key in _session_store:
                return json.dumps(
                    {
                        "key": key,
                        "value": _session_store[key]["value"],
                        "set_at": _session_store[key]["set_at"],
                    },
                    indent=2,
                )
            else:
                return json.dumps({"error": f"Key not found: {key}"}, indent=2)
        else:
            return json.dumps(
                {
                    "total_keys": len(_session_store),
                    "context": {
                        k: {"value": v["value"], "set_at": v["set_at"]}
                        for k, v in _session_store.items()
                    },
                },
                indent=2,
            )

    @mcp.tool()
    async def clear_session_context(key: str = None) -> str:
        """
        Clear session context.

        Args:
            key: Specific key to clear, or None to clear all context

        Returns:
            Confirmation of cleared context.
        """
        if key:
            if key in _session_store:
                del _session_store[key]
                return json.dumps({"status": "cleared", "key": key}, indent=2)
            else:
                return json.dumps({"error": f"Key not found: {key}"}, indent=2)
        else:
            count = len(_session_store)
            _session_store.clear()
            return json.dumps({"status": "cleared_all", "keys_cleared": count}, indent=2)

    @mcp.tool()
    async def log_agent_action(action: str, reasoning: str, result: str, target: str = None) -> str:
        """
        Log an agent action with reasoning for audit trail.

        Creates a record of what the agent did and why, enabling:
        - Review of agent decisions
        - Understanding of agent reasoning
        - Tracking of changes made

        Args:
            action: What action was taken (e.g., "updated_document", "ran_quality_check")
            reasoning: Why this action was taken
            result: What the outcome was
            target: Optional target of the action (document path, etc.)

        Returns:
            Confirmation with action ID.
        """
        action_record = {
            "id": len(_agent_actions) + 1,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "reasoning": reasoning,
            "result": result,
            "target": target,
        }

        _agent_actions.append(action_record)

        # Also log to project audit if available
        if server_instance.project:
            try:
                from ...audit import log_action

                log_action(
                    server_instance.project,
                    f"agent_{action}",
                    details=f"{reasoning} | Result: {result}",
                    document=Path(target) if target else None,
                    user="ai_agent",
                )
            except Exception:
                pass  # Audit logging is optional

        return json.dumps(
            {
                "status": "logged",
                "action_id": action_record["id"],
                "timestamp": action_record["timestamp"],
            },
            indent=2,
        )

    @mcp.tool()
    async def get_agent_actions(limit: int = 20) -> str:
        """
        Get recent agent actions from the audit trail.

        Args:
            limit: Maximum number of actions to return (default: 20)

        Returns:
            List of recent agent actions with reasoning.
        """
        recent = _agent_actions[-limit:] if _agent_actions else []
        recent.reverse()  # Most recent first

        return json.dumps(
            {
                "total_actions": len(_agent_actions),
                "showing": len(recent),
                "actions": recent,
            },
            indent=2,
        )

    @mcp.tool()
    async def get_action_summary() -> str:
        """
        Get a summary of agent actions in this session.

        Returns:
            Summary statistics and breakdown by action type.
        """
        if not _agent_actions:
            return json.dumps(
                {
                    "total_actions": 0,
                    "message": "No actions logged in this session",
                },
                indent=2,
            )

        # Group by action type
        by_type = {}
        for action in _agent_actions:
            action_type = action["action"]
            if action_type not in by_type:
                by_type[action_type] = 0
            by_type[action_type] += 1

        # Get time range
        first = _agent_actions[0]["timestamp"]
        last = _agent_actions[-1]["timestamp"]

        return json.dumps(
            {
                "total_actions": len(_agent_actions),
                "by_type": by_type,
                "first_action": first,
                "last_action": last,
                "unique_targets": len(
                    set(a["target"] for a in _agent_actions if a["target"])
                ),
            },
            indent=2,
        )

    @mcp.tool()
    async def export_session_report() -> str:
        """
        Export a complete report of this agent session.

        Includes:
        - Session context
        - All actions taken with reasoning
        - Summary statistics

        Useful for review or handoff to another agent/human.

        Returns:
            Complete session report.
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "session_context": {
                k: v["value"] for k, v in _session_store.items()
            },
            "actions": {
                "total": len(_agent_actions),
                "log": _agent_actions,
            },
            "summary": {
                "context_keys": list(_session_store.keys()),
                "action_types": list(set(a["action"] for a in _agent_actions)),
                "targets_modified": list(
                    set(a["target"] for a in _agent_actions if a["target"])
                ),
            },
        }

        return json.dumps(report, indent=2)


def reset_session():
    """Reset session state (for testing)."""
    global _session_store, _agent_actions
    _session_store = {}
    _agent_actions = []
