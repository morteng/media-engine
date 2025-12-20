"""
Notes Export Utilities

Generate consolidated exports for agent consumption.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from .types import NoteStatus

if TYPE_CHECKING:
    from ..core.project import Project

    from .registry import NotesRegistry


def generate_export(registry: "NotesRegistry", project: "Project") -> Dict[str, Any]:
    """Generate structured export of pending notes for agent consumption."""
    pending = registry.get_by_status(NoteStatus.PENDING)

    # Group by target
    by_target: Dict[str, list] = {}
    for note in pending:
        key = note.target_path
        if key not in by_target:
            by_target[key] = []
        by_target[key].append(note.to_dict())

    # Group by type
    by_type: Dict[str, list] = {}
    for note in pending:
        key = note.note_type.value
        if key not in by_type:
            by_type[key] = []
        by_type[key].append(note.to_dict())

    return {
        "generated": datetime.now().isoformat(),
        "project": project.config.name,
        "total_pending": len(pending),
        "by_target": by_target,
        "by_type": by_type,
        "notes": [n.to_dict() for n in pending],
    }


def write_exports(project: "Project", export_data: Dict[str, Any]):
    """Write exports to disk (JSON and Markdown)."""
    export_dir = project.root / ".media-engine"
    export_dir.mkdir(parents=True, exist_ok=True)

    # JSON export
    json_path = export_dir / "notes-export.json"
    with open(json_path, "w") as f:
        json.dump(export_data, f, indent=2)

    # Markdown export
    md_path = export_dir / "notes-export.md"
    with open(md_path, "w") as f:
        f.write("# Notes Export\n\n")
        f.write(f"Generated: {export_data['generated']}\n")
        f.write(f"Project: {export_data['project']}\n")
        f.write(f"Total pending: {export_data['total_pending']}\n\n")

        if export_data["total_pending"] == 0:
            f.write("No pending notes.\n")
            return

        # By target
        f.write("## By Target\n\n")
        for target, notes in export_data["by_target"].items():
            f.write(f"### {target}\n\n")
            for note in notes:
                priority = note.get("priority", "medium")
                priority_marker = {
                    "critical": "!!!",
                    "high": "!!",
                    "medium": "!",
                    "low": "",
                }.get(priority, "")
                f.write(f"- [{priority.upper()}]{priority_marker} {note['text']}\n")
                if note.get("target_id"):
                    f.write(f"  - Target ID: {note['target_id']}\n")
                if note.get("tags"):
                    f.write(f"  - Tags: {', '.join(note['tags'])}\n")
                f.write(f"  - Note ID: `{note['note_id']}`\n")
            f.write("\n")

        # Summary by type
        f.write("## Summary by Type\n\n")
        for note_type, notes in export_data["by_type"].items():
            f.write(f"- **{note_type}**: {len(notes)} pending\n")
