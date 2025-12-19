"""Webhook and event notification system for AI agents.

Allows agents to subscribe to and receive notifications about project changes,
build events, document updates, and quality issues.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class WebhookEvent:
    """A webhook event to be delivered."""

    event_type: str  # "document.updated", "build.completed", "quality.issue", etc.
    timestamp: str
    project_path: str
    data: dict
    correlation_id: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class WebhookSubscription:
    """A webhook subscription."""

    id: str
    url: str
    event_types: list[str]  # ["document.*", "build.completed"]
    active: bool = True
    created_at: str = ""
    last_triggered: Optional[str] = None


def register_webhook_tools(mcp, server_instance):
    """Register webhook management tools."""

    # In-memory webhook storage (can be persisted to file/db in production)
    server_instance._webhooks = getattr(server_instance, "_webhooks", {})
    server_instance._webhook_events = getattr(server_instance, "_webhook_events", [])

    @mcp.tool()
    async def register_webhook(url: str, event_types: str) -> str:
        """
        Register a webhook for notifications.

        Args:
            url: Webhook URL to call (should accept POST requests)
            event_types: Comma-separated event types to subscribe to
                        Examples: "document.*", "build.completed", "quality.issue"

        Returns:
            Webhook subscription details
        """
        import uuid

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        webhook_id = str(uuid.uuid4())[:8]
        events = [e.strip() for e in event_types.split(",")]

        subscription = WebhookSubscription(
            id=webhook_id,
            url=url,
            event_types=events,
            created_at=datetime.now().isoformat(),
        )

        server_instance._webhooks[webhook_id] = subscription

        return json.dumps(
            {
                "status": "registered",
                "webhook_id": webhook_id,
                "url": url,
                "event_types": events,
                "created_at": subscription.created_at,
            },
            indent=2,
        )

    @mcp.tool()
    async def list_webhooks() -> str:
        """
        List all registered webhooks.

        Returns:
            List of webhook subscriptions
        """
        webhooks = list(server_instance._webhooks.values())

        return json.dumps(
            {
                "count": len(webhooks),
                "webhooks": [
                    {
                        "id": w.id,
                        "url": w.url,
                        "event_types": w.event_types,
                        "active": w.active,
                        "created_at": w.created_at,
                        "last_triggered": w.last_triggered,
                    }
                    for w in webhooks
                ],
            },
            indent=2,
        )

    @mcp.tool()
    async def unregister_webhook(webhook_id: str) -> str:
        """
        Unregister a webhook.

        Args:
            webhook_id: ID of webhook to remove

        Returns:
            Confirmation of removal
        """
        if webhook_id in server_instance._webhooks:
            del server_instance._webhooks[webhook_id]
            return json.dumps({"status": "unregistered", "webhook_id": webhook_id}, indent=2)

        return json.dumps({"error": f"Webhook {webhook_id} not found"}, indent=2)

    @mcp.tool()
    async def get_webhook_history(webhook_id: str = None, limit: int = 10) -> str:
        """
        Get history of webhook events.

        Args:
            webhook_id: Optional webhook ID to filter by
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        events = server_instance._webhook_events

        if webhook_id:
            # Events would need to track webhook_id - for now show all
            pass

        recent = sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

        return json.dumps(
            {
                "total": len(events),
                "returned": len(recent),
                "events": [e.to_dict() for e in recent],
            },
            indent=2,
        )

    @mcp.tool()
    async def emit_event(event_type: str, data: str = "{}") -> str:
        """
        Emit a webhook event (primarily for testing).

        Args:
            event_type: Type of event (e.g., "document.updated")
            data: JSON string with event data

        Returns:
            Event details and delivery status
        """
        import uuid

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            event_data = json.loads(data) if data != "{}" else {}
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in data parameter"}, indent=2)

        event = WebhookEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            project_path=str(server_instance.project.root),
            data=event_data,
            correlation_id=str(uuid.uuid4())[:8],
        )

        server_instance._webhook_events.append(event)

        # In production, would deliver to registered webhooks here
        matched_hooks = _get_matching_webhooks(
            server_instance._webhooks, event_type
        )

        return json.dumps(
            {
                "event_emitted": True,
                "event_type": event_type,
                "correlation_id": event.correlation_id,
                "timestamp": event.timestamp,
                "matched_webhooks": len(matched_hooks),
                "webhook_ids": [w.id for w in matched_hooks],
            },
            indent=2,
        )

    @mcp.tool()
    async def on_event_notification(event_json: str) -> str:
        """
        Receive notification of a project event (called by webhooks).

        This is typically called by the webhook system when events occur.
        Agents can register to receive these notifications.

        Args:
            event_json: JSON event data

        Returns:
            Acknowledgment and next steps
        """
        try:
            event_data = json.loads(event_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON event"}, indent=2)

        event_type = event_data.get("event_type", "unknown")

        # Provide intelligent responses based on event type
        if event_type.startswith("quality."):
            response = _handle_quality_event(event_data, server_instance.project)
        elif event_type.startswith("document."):
            response = _handle_document_event(event_data, server_instance.project)
        elif event_type.startswith("build."):
            response = _handle_build_event(event_data, server_instance.project)
        else:
            response = {
                "acknowledged": True,
                "event_type": event_type,
                "message": f"Received {event_type} event",
            }

        return json.dumps(response, indent=2)


def _get_matching_webhooks(webhooks: dict, event_type: str) -> list:
    """Find webhooks that match an event type."""
    matching = []

    for webhook in webhooks.values():
        if not webhook.active:
            continue

        for pattern in webhook.event_types:
            # Simple wildcard matching (e.g., "document.*" matches "document.updated")
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if event_type.startswith(prefix):
                    matching.append(webhook)
                    break
            elif pattern == event_type:
                matching.append(webhook)
                break

    return matching


def _handle_quality_event(event_data: dict, project) -> dict:
    """Handle quality-related events."""
    return {
        "acknowledged": True,
        "event_type": event_data.get("event_type"),
        "action": "quality_issue_detected",
        "message": f"Quality issue detected: {event_data.get('issue', 'unknown')}",
        "next_steps": [
            "Review the quality report",
            "Address critical issues first",
            "Run quality checks again to verify fixes",
        ],
    }


def _handle_document_event(event_data: dict, project) -> dict:
    """Handle document-related events."""
    return {
        "acknowledged": True,
        "event_type": event_data.get("event_type"),
        "action": "document_changed",
        "document": event_data.get("document_path"),
        "message": f"Document updated: {event_data.get('document_path')}",
        "next_steps": [
            "Verify changes are correct",
            "Check for broken references",
            "Update translations if needed",
        ],
    }


def _handle_build_event(event_data: dict, project) -> dict:
    """Handle build-related events."""
    return {
        "acknowledged": True,
        "event_type": event_data.get("event_type"),
        "action": "build_event",
        "status": event_data.get("status", "unknown"),
        "message": f"Build {event_data.get('status', 'unknown')}: {event_data.get('format', 'unknown')}",
        "next_steps": [
            "Check build output",
            "Verify output files",
            "Deploy if build was successful",
        ],
    }
