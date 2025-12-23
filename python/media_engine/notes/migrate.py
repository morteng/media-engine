"""
Migrate existing scene notes to the general notes system.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from .types import NoteType

if TYPE_CHECKING:
    from ..core.project import Project


def migrate_scene_notes(project: "Project") -> Dict[str, Any]:
    """
    Migrate existing scene notes to the new notes system.

    Reads from .media-engine/scene-notes/*.json and converts to the
    new notes registry format.

    Returns migration report with counts and any errors.
    """
    from .registry import NotesRegistry

    old_notes_dir = project.root / ".media-engine" / "scene-notes"
    if not old_notes_dir.exists():
        return {"migrated": 0, "skipped": 0, "errors": [], "message": "No scene notes to migrate"}

    registry = NotesRegistry(project)
    migrated = 0
    skipped = 0
    errors: List[Dict[str, str]] = []

    for notes_file in old_notes_dir.glob("*.json"):
        try:
            with open(notes_file) as f:
                data = json.load(f)

            script_path = data.get("script_path", str(notes_file.stem))
            notes = data.get("notes", {})

            for scene_id, note_data in notes.items():
                # Check if this note already exists
                existing = registry.get_for_target(script_path, scene_id)
                scene_existing = [n for n in existing if n.note_type == NoteType.SCENE]

                if scene_existing:
                    skipped += 1
                    continue

                # Parse created date
                if note_data.get("created"):
                    try:
                        datetime.fromisoformat(note_data["created"])
                    except (ValueError, TypeError):
                        pass

                registry.add(
                    note_type=NoteType.SCENE,
                    target_path=script_path,
                    target_id=scene_id,
                    text=note_data.get("text", ""),
                    metadata={
                        "migrated_from": str(notes_file),
                        "migrated_at": datetime.now().isoformat(),
                        "original_created": note_data.get("created"),
                    },
                )
                migrated += 1

        except json.JSONDecodeError as e:
            errors.append({"file": str(notes_file), "error": f"Invalid JSON: {e}"})
        except Exception as e:
            errors.append({"file": str(notes_file), "error": str(e)})

    return {
        "migrated": migrated,
        "skipped": skipped,
        "errors": errors,
        "message": f"Migrated {migrated} notes, skipped {skipped} existing",
    }
