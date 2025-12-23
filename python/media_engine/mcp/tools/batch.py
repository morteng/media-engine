"""Batch operation tools for AI agents.

Provides tools for executing multiple operations atomically and
applying transformations across multiple documents efficiently.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import MediaEngineMCPServer


def register_batch_tools(mcp, server_instance: "MediaEngineMCPServer"):
    """Register batch operation MCP tools."""

    @mcp.tool()
    async def batch_update(operations: str) -> str:
        """
        Execute multiple operations atomically.

        Performs a series of document operations with all-or-nothing semantics.
        If any operation fails, all changes are rolled back.

        Args:
            operations: JSON array of operations, each with:
                - action: "update_metadata", "update_status", "increment_version"
                - target: Document path
                - params: Action-specific parameters

        Example operations:
        [
            {"action": "update_status", "target": "en/chapters/01.md", "params": {"status": "final"}},
            {"action": "increment_version", "target": "en/chapters/01.md", "params": {"bump": "minor"}}
        ]

        Returns:
            Results of all operations with success/failure status.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            ops = json.loads(operations)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {e}"}, indent=2)

        if not isinstance(ops, list):
            return json.dumps({"error": "Operations must be an array"}, indent=2)

        project = server_instance.project
        result = _execute_batch(project, ops)

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def apply_transformation(selector: str, transformation: str, dry_run: bool = True) -> str:
        """
        Apply a transformation to multiple documents matching a selector.

        Selectors:
        - "status:draft" - all draft documents
        - "lang:en" or "language:en" - all English documents
        - "type:chapter" - all chapters
        - "all" - all documents (use with caution)

        Transformations:
        - "update_status:final" - set status to final
        - "add_tag:reviewed" - add a tag
        - "remove_tag:draft" - remove a tag
        - "set_metadata:key=value" - set arbitrary metadata

        Args:
            selector: Document selector expression
            transformation: Transformation to apply
            dry_run: If True, just report what would change (default: True)

        Returns:
            List of affected documents and changes applied/to be applied.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        project = server_instance.project
        result = _apply_transformation(project, selector, transformation, dry_run)

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def preview_changes(changes: str) -> str:
        """
        Preview what a set of changes would do without applying them.

        Takes the same format as batch_update but only reports what would happen.

        Args:
            changes: JSON array of operations to preview

        Returns:
            Preview of changes including affected documents and estimated impact.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            ops = json.loads(changes)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {e}"}, indent=2)

        project = server_instance.project
        preview = _preview_changes(project, ops)

        return json.dumps(preview, indent=2)


def _execute_batch(project, operations: list) -> dict:
    """Execute a batch of operations atomically."""
    from ...cms.document_manager import DocumentManager

    manager = DocumentManager(project)
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_operations": len(operations),
        "successful": 0,
        "failed": 0,
        "results": [],
        "rollback_performed": False,
    }

    # Store original states for rollback
    original_states = {}
    applied_ops = []

    try:
        for i, op in enumerate(operations):
            action = op.get("action")
            target = op.get("target")
            params = op.get("params", {})

            if not action or not target:
                raise ValueError(f"Operation {i}: missing action or target")

            # Store original state
            original = _get_document_state(project, target)
            if original:
                original_states[target] = original

            # Execute operation
            op_result = _execute_operation(project, manager, action, target, params)
            op_result["operation_index"] = i

            if op_result.get("success"):
                results["successful"] += 1
                applied_ops.append((target, action, params))
            else:
                results["failed"] += 1
                # Rollback all previous operations
                _rollback_operations(project, manager, original_states, applied_ops)
                results["rollback_performed"] = True
                results["results"].append(op_result)
                raise ValueError(f"Operation {i} failed: {op_result.get('error')}")

            results["results"].append(op_result)

    except ValueError as e:
        results["error"] = str(e)
    except Exception as e:
        results["error"] = f"Unexpected error: {e}"
        # Attempt rollback
        _rollback_operations(project, manager, original_states, applied_ops)
        results["rollback_performed"] = True

    return results


def _execute_operation(project, manager, action: str, target: str, params: dict) -> dict:
    """Execute a single batch operation."""
    result = {"action": action, "target": target, "success": False}

    try:
        doc_path = project.content_dir / target
        if not doc_path.exists():
            doc_path = project.content_dir / target.lstrip("/")

        if not doc_path.exists():
            result["error"] = f"Document not found: {target}"
            return result

        if action == "update_status":
            new_status = params.get("status")
            if not new_status:
                result["error"] = "Missing 'status' parameter"
                return result

            _update_frontmatter(doc_path, {"status": new_status})
            result["success"] = True
            result["new_status"] = new_status

        elif action == "update_metadata":
            metadata = params.get("metadata", params)
            if not metadata:
                result["error"] = "Missing metadata to update"
                return result

            _update_frontmatter(doc_path, metadata)
            result["success"] = True
            result["updated_fields"] = list(metadata.keys())

        elif action == "increment_version":
            bump = params.get("bump", "patch")
            new_version = _increment_version(doc_path, bump)
            result["success"] = True
            result["new_version"] = new_version

        elif action == "add_tag":
            tag = params.get("tag")
            if not tag:
                result["error"] = "Missing 'tag' parameter"
                return result

            _add_tag(doc_path, tag)
            result["success"] = True
            result["added_tag"] = tag

        elif action == "remove_tag":
            tag = params.get("tag")
            if not tag:
                result["error"] = "Missing 'tag' parameter"
                return result

            _remove_tag(doc_path, tag)
            result["success"] = True
            result["removed_tag"] = tag

        else:
            result["error"] = f"Unknown action: {action}"

    except Exception as e:
        result["error"] = str(e)

    return result


def _get_document_state(project, target: str) -> dict | None:
    """Get the current state of a document for potential rollback."""
    try:
        doc_path = project.content_dir / target
        if not doc_path.exists():
            doc_path = project.content_dir / target.lstrip("/")

        if not doc_path.exists():
            return None

        content = doc_path.read_text(encoding="utf-8")
        return {"path": str(doc_path), "content": content}
    except Exception:
        return None


def _rollback_operations(project, manager, original_states: dict, applied_ops: list):
    """Rollback applied operations by restoring original states."""
    for target, _, _ in reversed(applied_ops):
        if target in original_states:
            original = original_states[target]
            try:
                Path(original["path"]).write_text(original["content"], encoding="utf-8")
            except Exception:
                pass  # Best effort rollback


def _update_frontmatter(doc_path: Path, updates: dict):
    """Update frontmatter fields in a document."""
    from ...cms.document import Document

    doc = Document.load(doc_path)
    doc.metadata.update(updates)
    doc.save()


def _increment_version(doc_path: Path, bump: str) -> str:
    """Increment the version of a document."""
    from ...cms.document import Document

    doc = Document.load(doc_path)

    current = doc.metadata.get("version", "1.0.0")
    parts = current.split(".")
    if len(parts) != 3:
        parts = ["1", "0", "0"]

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    doc.metadata["version"] = new_version
    doc.save()

    return new_version


def _add_tag(doc_path: Path, tag: str):
    """Add a tag to a document."""
    from ...cms.document import Document

    doc = Document.load(doc_path)

    tags = doc.metadata.get("tags", [])
    if not isinstance(tags, list):
        tags = [tags] if tags else []

    if tag not in tags:
        tags.append(tag)

    doc.metadata["tags"] = tags
    doc.save()


def _remove_tag(doc_path: Path, tag: str):
    """Remove a tag from a document."""
    from ...cms.document import Document

    doc = Document.load(doc_path)

    tags = doc.metadata.get("tags", [])
    if not isinstance(tags, list):
        tags = [tags] if tags else []

    if tag in tags:
        tags.remove(tag)

    doc.metadata["tags"] = tags
    doc.save()


def _apply_transformation(project, selector: str, transformation: str, dry_run: bool) -> dict:
    """Apply a transformation to matching documents."""
    from ...cms.document_manager import DocumentManager

    manager = DocumentManager(project)
    docs = manager.list_documents()

    # Filter by selector
    matching = _filter_by_selector(docs, selector, project)

    result = {
        "selector": selector,
        "transformation": transformation,
        "dry_run": dry_run,
        "total_matched": len(matching),
        "affected_documents": [],
    }

    # Parse transformation
    trans_parts = transformation.split(":", 1)
    trans_action = trans_parts[0]
    trans_value = trans_parts[1] if len(trans_parts) > 1 else None

    for doc in matching:
        doc_path = project.content_dir / doc["path"]
        change = {
            "path": doc["path"],
            "transformation": transformation,
            "applied": False,
        }

        if dry_run:
            change["would_apply"] = True
            change["current_value"] = _get_current_value(doc, trans_action)
            change["new_value"] = trans_value
        else:
            try:
                if trans_action == "update_status":
                    _update_frontmatter(doc_path, {"status": trans_value})
                    change["applied"] = True
                elif trans_action == "add_tag":
                    _add_tag(doc_path, trans_value)
                    change["applied"] = True
                elif trans_action == "remove_tag":
                    _remove_tag(doc_path, trans_value)
                    change["applied"] = True
                elif trans_action == "set_metadata":
                    if "=" in trans_value:
                        key, val = trans_value.split("=", 1)
                        _update_frontmatter(doc_path, {key: val})
                        change["applied"] = True
                else:
                    change["error"] = f"Unknown transformation: {trans_action}"
            except Exception as e:
                change["error"] = str(e)

        result["affected_documents"].append(change)

    result["applied_count"] = sum(1 for d in result["affected_documents"] if d.get("applied"))

    return result


def _filter_by_selector(docs: list, selector: str, project) -> list:
    """Filter documents by selector."""
    if selector == "all":
        return docs

    matching = []

    # Parse selector (format: key:value)
    if ":" in selector:
        key, value = selector.split(":", 1)
        key = key.lower()
        value = value.lower()

        for doc in docs:
            # Handle language specially
            if key in ["lang", "language"]:
                if doc.get("language", "").lower() == value:
                    matching.append(doc)
            elif key == "type":
                # Infer type from path
                path = doc.get("path", "")
                if value in path.lower():
                    matching.append(doc)
            else:
                # Generic field match
                if str(doc.get(key, "")).lower() == value:
                    matching.append(doc)

    return matching


def _get_current_value(doc: dict, trans_action: str) -> str | None:
    """Get the current value for a transformation type."""
    if trans_action == "update_status":
        return doc.get("status")
    elif trans_action in ["add_tag", "remove_tag"]:
        return doc.get("tags", [])
    return None


def _preview_changes(project, operations: list) -> dict:
    """Preview a set of changes without applying them."""
    preview = {
        "total_operations": len(operations),
        "preview": [],
        "estimated_impact": {
            "documents_modified": 0,
            "translations_affected": 0,
        },
    }

    seen_docs = set()

    for op in operations:
        action = op.get("action")
        target = op.get("target")
        params = op.get("params", {})

        op_preview = {
            "action": action,
            "target": target,
            "params": params,
            "valid": True,
            "warnings": [],
        }

        # Check if target exists
        doc_path = project.content_dir / target
        if not doc_path.exists():
            doc_path = project.content_dir / target.lstrip("/")

        if not doc_path.exists():
            op_preview["valid"] = False
            op_preview["error"] = f"Document not found: {target}"
        else:
            op_preview["current_state"] = _describe_current_state(doc_path, action)
            op_preview["expected_outcome"] = _describe_expected_outcome(action, params)

            if target not in seen_docs:
                seen_docs.add(target)
                preview["estimated_impact"]["documents_modified"] += 1

            # Check translation impact
            if action in ["update_metadata", "update_status"]:
                try:
                    from ...translation.tracker import TranslationTracker

                    tracker = TranslationTracker(project)
                    translations = tracker.get_translations_for_source(Path(target))
                    if translations:
                        preview["estimated_impact"]["translations_affected"] += len(translations)
                        op_preview["warnings"].append(
                            f"{len(translations)} translations may need updating"
                        )
                except Exception:
                    pass

        preview["preview"].append(op_preview)

    return preview


def _describe_current_state(doc_path: Path, action: str) -> str:
    """Describe the current state relevant to an action."""
    try:
        from ...cms.document import Document

        doc = Document.load(doc_path)
        metadata = doc.metadata

        if action == "update_status":
            return f"status: {metadata.get('status', 'unknown')}"
        elif action == "increment_version":
            return f"version: {metadata.get('version', '1.0.0')}"
        elif action in ["add_tag", "remove_tag"]:
            tags = metadata.get("tags", [])
            return f"tags: {tags}"
        elif action == "update_metadata":
            return f"metadata keys: {list(metadata.keys())}"
        else:
            return "unknown state"
    except Exception:
        return "could not read state"


def _describe_expected_outcome(action: str, params: dict) -> str:
    """Describe the expected outcome of an action."""
    if action == "update_status":
        return f"status will be: {params.get('status')}"
    elif action == "increment_version":
        return f"version will be bumped ({params.get('bump', 'patch')})"
    elif action == "add_tag":
        return f"tag '{params.get('tag')}' will be added"
    elif action == "remove_tag":
        return f"tag '{params.get('tag')}' will be removed"
    elif action == "update_metadata":
        return f"fields will be updated: {list(params.get('metadata', params).keys())}"
    else:
        return "unknown outcome"
