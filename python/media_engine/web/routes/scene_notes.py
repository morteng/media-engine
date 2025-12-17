"""
Scene notes routes for video script annotation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_scene_notes_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
):
    """Register scene notes routes."""
    import yaml

    @router.get("/api/scene-notes/{script_path:path}")
    async def get_scene_notes(script_path: str):
        """Get notes for a script's scenes."""
        project = get_project()
        notes_dir = project.root / ".media-engine" / "scene-notes"

        # Create a safe filename from the script path
        safe_name = script_path.replace("/", "_").replace("\\", "_")
        notes_file = notes_dir / f"{safe_name}.json"

        if not notes_file.exists():
            return {"notes": {}}

        try:
            with open(notes_file) as f:
                data = json.load(f)
            return {"notes": data.get("notes", {})}
        except Exception:
            return {"notes": {}}

    @router.post("/api/scene-notes/{script_path:path}")
    async def save_scene_note(script_path: str, scene_id: str, note: str):
        """Save a note for a specific scene."""
        project = get_project()
        notes_dir = project.root / ".media-engine" / "scene-notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        safe_name = script_path.replace("/", "_").replace("\\", "_")
        notes_file = notes_dir / f"{safe_name}.json"

        # Load existing notes
        data = {"script_path": script_path, "notes": {}}
        if notes_file.exists():
            try:
                with open(notes_file) as f:
                    data = json.load(f)
            except Exception:
                pass

        # Update note
        if note.strip():
            data["notes"][scene_id] = {
                "text": note,
                "created": datetime.now().isoformat(),
                "scene_id": scene_id,
            }
        elif scene_id in data["notes"]:
            del data["notes"][scene_id]

        data["updated"] = datetime.now().isoformat()

        with open(notes_file, "w") as f:
            json.dump(data, f, indent=2)

        # Also update the consolidated todo file
        await _update_scene_notes_export(project)

        return {"status": "saved", "scene_id": scene_id}

    @router.delete("/api/scene-notes/{script_path:path}/{scene_id}")
    async def delete_scene_note(script_path: str, scene_id: str):
        """Delete a note for a specific scene."""
        project = get_project()
        notes_dir = project.root / ".media-engine" / "scene-notes"

        safe_name = script_path.replace("/", "_").replace("\\", "_")
        notes_file = notes_dir / f"{safe_name}.json"

        if notes_file.exists():
            try:
                with open(notes_file) as f:
                    data = json.load(f)
                if scene_id in data.get("notes", {}):
                    del data["notes"][scene_id]
                    data["updated"] = datetime.now().isoformat()
                    with open(notes_file, "w") as f:
                        json.dump(data, f, indent=2)
                    await _update_scene_notes_export(project)
            except Exception:
                pass

        return {"status": "deleted", "scene_id": scene_id}

    @router.get("/api/scene-notes-export")
    async def get_scene_notes_export():
        """Get all scene notes as a structured export for coding assistants."""
        project = get_project()
        return await _generate_scene_notes_export(project)

    async def _update_scene_notes_export(project: "Project"):
        """Update the consolidated scene notes export file."""
        export_data = await _generate_scene_notes_export(project)

        export_dir = project.root / ".media-engine"
        export_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON export
        export_file = export_dir / "scene-notes-todo.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f, indent=2)

        # Write markdown export for easy reading
        md_file = export_dir / "scene-notes-todo.md"
        with open(md_file, "w") as f:
            f.write("# Scene Notes & Suggestions\n\n")
            f.write(f"Generated: {export_data['generated']}\n\n")
            f.write(f"Total notes: {export_data['total_notes']}\n\n")

            for script in export_data["scripts"]:
                f.write(f"## {script['script_name']}\n\n")
                f.write(f"**Path:** `{script['script_path']}`\n\n")

                for note in script["notes"]:
                    f.write(f"### Scene: {note['scene_id']}\n\n")
                    if note.get("scene_name"):
                        f.write(f"**Scene Name:** {note['scene_name']}\n\n")
                    f.write(f"**Note:**\n{note['text']}\n\n")
                    f.write(f"*Created: {note['created']}*\n\n")
                    f.write("---\n\n")

    async def _generate_scene_notes_export(project: "Project") -> dict:
        """Generate the scene notes export data."""
        notes_dir = project.root / ".media-engine" / "scene-notes"

        export = {
            "generated": datetime.now().isoformat(),
            "project": project.config.name,
            "total_notes": 0,
            "scripts": [],
        }

        if not notes_dir.exists():
            return export

        for notes_file in notes_dir.glob("*.json"):
            try:
                with open(notes_file) as f:
                    data = json.load(f)

                script_path = data.get("script_path", "")
                notes = data.get("notes", {})

                if not notes:
                    continue

                # Try to load the script to get scene names
                script_data = {}
                try:
                    actual_path = Path(script_path)
                    if not actual_path.is_absolute():
                        actual_path = project.root / script_path
                    if actual_path.exists():
                        with open(actual_path) as f:
                            script_data = yaml.safe_load(f) or {}
                except Exception:
                    pass

                scenes_by_id = {}
                for scene in script_data.get("scenes", []):
                    if scene.get("id"):
                        scenes_by_id[scene["id"]] = scene

                script_notes = []
                for scene_id, note_data in notes.items():
                    scene_info = scenes_by_id.get(scene_id, {})
                    script_notes.append({
                        "scene_id": scene_id,
                        "scene_name": scene_info.get("name", ""),
                        "scene_type": scene_info.get("scene_type", ""),
                        "text": note_data.get("text", ""),
                        "created": note_data.get("created", ""),
                    })

                if script_notes:
                    export["scripts"].append({
                        "script_path": script_path,
                        "script_name": script_data.get("title", Path(script_path).stem),
                        "notes": script_notes,
                    })
                    export["total_notes"] += len(script_notes)

            except Exception:
                continue

        return export
