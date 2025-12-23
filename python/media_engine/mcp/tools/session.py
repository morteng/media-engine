"""Session context and agent audit tools.

Provides tools for managing agent session state and maintaining
an audit trail of agent actions with reasoning.

Features:
- In-memory session storage for fast access
- Optional file-based persistence for cross-restart continuity
- Agent action audit trail with reasoning
- Session export for handoff or review
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..server import MediaEngineMCPServer

# In-memory session storage (persists for server lifetime)
_session_store: dict = {}
_agent_actions: list = []
_persistence_path: Optional[Path] = None


def _get_persistence_path(project_root: Path) -> Path:
    """Get the path for session persistence file."""
    return project_root / ".media-engine" / "agent_session.json"


def _load_persisted_session(project_root: Path) -> None:
    """Load session from persistence file if it exists."""
    global _session_store, _agent_actions, _persistence_path

    _persistence_path = _get_persistence_path(project_root)

    if _persistence_path.exists():
        try:
            with open(_persistence_path, "r") as f:
                data = json.load(f)
                _session_store = data.get("context", {})
                _agent_actions = data.get("actions", [])
        except Exception:
            pass  # Start fresh if file is corrupt


def _persist_session() -> None:
    """Save session to persistence file."""
    global _persistence_path

    if _persistence_path is None:
        return

    try:
        _persistence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_persistence_path, "w") as f:
            json.dump(
                {
                    "context": _session_store,
                    "actions": _agent_actions,
                    "last_saved": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )
    except Exception:
        pass  # Persistence is optional


def register_session_tools(mcp, server_instance: "MediaEngineMCPServer"):
    """Register session context and audit MCP tools."""

    # Load persisted session if project is available
    if server_instance.project:
        _load_persisted_session(server_instance.project.root)

    @mcp.tool()
    async def enable_session_persistence(enable: bool = True) -> str:
        """
        Enable or disable session persistence to disk.

        When enabled, session context and actions are saved to
        .media-engine/agent_session.json and restored on server restart.

        Args:
            enable: True to enable persistence, False to disable

        Returns:
            Confirmation of persistence status.
        """
        global _persistence_path

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        if enable:
            _persistence_path = _get_persistence_path(server_instance.project.root)
            _persist_session()
            return json.dumps(
                {
                    "status": "enabled",
                    "path": str(_persistence_path),
                    "note": "Session will persist across server restarts",
                },
                indent=2,
            )
        else:
            old_path = _persistence_path
            _persistence_path = None
            return json.dumps(
                {
                    "status": "disabled",
                    "previous_path": str(old_path) if old_path else None,
                    "note": "Session is now in-memory only",
                },
                indent=2,
            )

    @mcp.tool()
    async def load_previous_session() -> str:
        """
        Load a previously persisted session.

        Restores session context and action history from the last saved session.
        Useful for continuing work from a previous session.

        Returns:
            Loaded session info or error if no session found.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        path = _get_persistence_path(server_instance.project.root)

        if not path.exists():
            return json.dumps(
                {
                    "status": "not_found",
                    "path": str(path),
                    "note": "No previous session found",
                },
                indent=2,
            )

        _load_persisted_session(server_instance.project.root)

        return json.dumps(
            {
                "status": "loaded",
                "path": str(path),
                "context_keys": list(_session_store.keys()),
                "action_count": len(_agent_actions),
                "note": "Previous session restored",
            },
            indent=2,
        )

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

        # Persist to disk if enabled
        _persist_session()

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
                _persist_session()
                return json.dumps({"status": "cleared", "key": key}, indent=2)
            else:
                return json.dumps({"error": f"Key not found: {key}"}, indent=2)
        else:
            count = len(_session_store)
            _session_store.clear()
            _persist_session()
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

        # Persist to disk if enabled
        _persist_session()

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
                "unique_targets": len(set(a["target"] for a in _agent_actions if a["target"])),
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
            "session_context": {k: v["value"] for k, v in _session_store.items()},
            "actions": {
                "total": len(_agent_actions),
                "log": _agent_actions,
            },
            "summary": {
                "context_keys": list(_session_store.keys()),
                "action_types": list(set(a["action"] for a in _agent_actions)),
                "targets_modified": list(set(a["target"] for a in _agent_actions if a["target"])),
            },
        }

        return json.dumps(report, indent=2)


def reset_session():
    """Reset session state (for testing)."""
    global _session_store, _agent_actions
    _session_store = {}
    _agent_actions = []
