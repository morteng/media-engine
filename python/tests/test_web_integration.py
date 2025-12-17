"""
Integration tests for Web Dashboard API endpoints.

Tests the FastAPI endpoints in media_engine.web.routes module,
with a focus on the scene notes feature and core API endpoints.
"""

import json
import shutil
from pathlib import Path

import pytest

# Check for FastAPI installation
try:
    from fastapi.testclient import TestClient

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

if HAS_FASTAPI:
    from media_engine.core.project import Project
    from media_engine.web.app import create_app

# Path to demo project
DEMO_PROJECT_PATH = Path(__file__).parent.parent.parent / "demo"


@pytest.fixture
def demo_project_web(temp_dir):
    """Create a copy of demo project for web tests."""
    if not HAS_FASTAPI:
        pytest.skip("FastAPI not installed - install with: pip install media-engine[web]")

    if not DEMO_PROJECT_PATH.exists():
        pytest.skip("Demo project not found")

    # Copy demo to temp
    dest = temp_dir / "demo"
    shutil.copytree(DEMO_PROJECT_PATH, dest)
    return dest


@pytest.fixture
def client(demo_project_web):
    """Create FastAPI test client with demo project."""
    app = create_app(demo_project_web)
    return TestClient(app)


@pytest.fixture
def sample_script_path(demo_project_web):
    """Return path to a sample script for testing scene notes."""
    # Use the showcase script from demo
    script_path = demo_project_web / "content" / "en" / "scripts" / "showcase.yaml"
    if not script_path.exists():
        pytest.skip("Sample script not found")
    return "content/en/scripts/showcase.yaml"


class TestProjectAPI:
    """Tests for core project API endpoints."""

    def test_get_project_info(self, client):
        """Test GET /api/project returns project configuration."""
        response = client.get("/api/project")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "description" in data
        assert "root" in data
        assert "languages" in data
        assert "source_language" in data
        assert "paths" in data

        # Check that languages are properly structured
        languages = data["languages"]
        assert isinstance(languages, dict)
        assert "en" in languages
        assert "name" in languages["en"]
        assert "locale" in languages["en"]

        # Check paths are present
        paths = data["paths"]
        assert "content" in paths
        assert "assets" in paths
        assert "output" in paths
        assert "publish" in paths

    def test_get_status(self, client):
        """Test GET /api/status returns project status."""
        response = client.get("/api/status")
        assert response.status_code == 200

        data = response.json()
        # Status response structure varies by project,
        # but should be a dict with at least some info
        assert isinstance(data, dict)


class TestDocumentAPI:
    """Tests for document listing and retrieval endpoints."""

    def test_list_documents_english(self, client):
        """Test GET /api/documents/{language} lists all documents."""
        response = client.get("/api/documents/en")
        assert response.status_code == 200

        data = response.json()
        assert "language" in data
        assert data["language"] == "en"
        assert "documents" in data

        documents = data["documents"]
        assert isinstance(documents, list)
        assert len(documents) > 0

        # Check document structure
        doc = documents[0]
        assert "path" in doc
        assert "filename" in doc
        assert "title" in doc
        assert "type" in doc

    def test_list_documents_invalid_language(self, client):
        """Test GET /api/documents/{language} with invalid language."""
        response = client.get("/api/documents/invalid")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_chapters(self, client):
        """Test GET /api/chapters/{language} returns chapters."""
        response = client.get("/api/chapters/en")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check chapter structure
        chapter = data[0]
        assert "path" in chapter
        assert "filename" in chapter
        assert "title" in chapter
        assert "metadata" in chapter


class TestTranslationAPI:
    """Tests for translation tracking endpoints."""

    def test_get_translations(self, client):
        """Test GET /api/translations returns translation status."""
        response = client.get("/api/translations")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "current" in data
        assert "outdated" in data
        assert "translations" in data

        translations = data["translations"]
        assert isinstance(translations, list)

        # If there are translations, check structure
        if len(translations) > 0:
            trans = translations[0]
            assert "source_path" in trans
            assert "translation_path" in trans
            assert "source_language" in trans
            assert "target_language" in trans
            assert "is_outdated" in trans
            assert "status" in trans

    def test_get_translation_matrix(self, client):
        """Test GET /api/translations/matrix returns translation matrix."""
        response = client.get("/api/translations/matrix")
        assert response.status_code == 200

        data = response.json()
        assert "languages" in data
        assert "source_language" in data
        assert "documents" in data

        languages = data["languages"]
        assert isinstance(languages, list)
        assert "en" in languages

        documents = data["documents"]
        assert isinstance(documents, list)

        # If there are documents, check structure
        if len(documents) > 0:
            doc = documents[0]
            assert "source_path" in doc
            assert "title" in doc
            assert "translations" in doc
            assert isinstance(doc["translations"], dict)


class TestSceneNotesAPI:
    """Tests for scene notes API endpoints."""

    def test_get_scene_notes_empty(self, client, sample_script_path):
        """Test GET /api/scene-notes/{script_path} returns empty notes initially."""
        response = client.get(f"/api/scene-notes/{sample_script_path}")
        assert response.status_code == 200

        data = response.json()
        assert "notes" in data
        assert isinstance(data["notes"], dict)
        # Should be empty initially
        assert len(data["notes"]) == 0

    def test_save_scene_note(self, client, sample_script_path):
        """Test POST /api/scene-notes/{script_path} saves a note."""
        # Save a note for the "hook" scene
        response = client.post(
            f"/api/scene-notes/{sample_script_path}",
            params={
                "scene_id": "hook",
                "note": "Consider adding more visual emphasis on the problem statement.",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "saved"
        assert data["scene_id"] == "hook"

    def test_get_scene_notes_after_save(self, client, sample_script_path):
        """Test GET /api/scene-notes/{script_path} retrieves saved notes."""
        # First, save a note
        note_text = "Test note for solution scene"
        client.post(
            f"/api/scene-notes/{sample_script_path}",
            params={"scene_id": "solution", "note": note_text},
        )

        # Then retrieve it
        response = client.get(f"/api/scene-notes/{sample_script_path}")
        assert response.status_code == 200

        data = response.json()
        notes = data["notes"]
        assert "solution" in notes
        assert notes["solution"]["text"] == note_text
        assert "created" in notes["solution"]
        assert "scene_id" in notes["solution"]

    def test_save_multiple_scene_notes(self, client, sample_script_path):
        """Test saving notes for multiple scenes."""
        scenes = [
            ("hook", "Improve opening hook"),
            ("solution", "Add company logo here"),
            ("core_concept", "Need better animation for this part"),
        ]

        # Save multiple notes
        for scene_id, note_text in scenes:
            response = client.post(
                f"/api/scene-notes/{sample_script_path}",
                params={"scene_id": scene_id, "note": note_text},
            )
            assert response.status_code == 200

        # Retrieve all notes
        response = client.get(f"/api/scene-notes/{sample_script_path}")
        assert response.status_code == 200

        data = response.json()
        notes = data["notes"]
        assert len(notes) == 3

        for scene_id, note_text in scenes:
            assert scene_id in notes
            assert notes[scene_id]["text"] == note_text

    def test_update_scene_note(self, client, sample_script_path):
        """Test updating an existing scene note."""
        scene_id = "feature_video"
        original_note = "Original note"
        updated_note = "Updated note with more details"

        # Save original note
        client.post(
            f"/api/scene-notes/{sample_script_path}",
            params={"scene_id": scene_id, "note": original_note},
        )

        # Update the note
        response = client.post(
            f"/api/scene-notes/{sample_script_path}",
            params={"scene_id": scene_id, "note": updated_note},
        )
        assert response.status_code == 200

        # Verify update
        response = client.get(f"/api/scene-notes/{sample_script_path}")
        data = response.json()
        assert data["notes"][scene_id]["text"] == updated_note

    def test_delete_scene_note(self, client, sample_script_path):
        """Test DELETE /api/scene-notes/{script_path}/{scene_id} deletes a note."""
        scene_id = "feature_quality"

        # First, save a note
        client.post(
            f"/api/scene-notes/{sample_script_path}",
            params={"scene_id": scene_id, "note": "This will be deleted"},
        )

        # Verify it was saved
        response = client.get(f"/api/scene-notes/{sample_script_path}")
        assert scene_id in response.json()["notes"]

        # Delete the note
        response = client.delete(f"/api/scene-notes/{sample_script_path}/{scene_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify deletion
        response = client.get(f"/api/scene-notes/{sample_script_path}")
        assert scene_id not in response.json()["notes"]

    def test_delete_nonexistent_note(self, client, sample_script_path):
        """Test deleting a note that doesn't exist."""
        response = client.delete(f"/api/scene-notes/{sample_script_path}/nonexistent_scene")
        # Should succeed silently
        assert response.status_code == 200

    def test_save_empty_note_deletes(self, client, sample_script_path):
        """Test that saving an empty note deletes it."""
        scene_id = "feature_ai"

        # Save a note
        client.post(
            f"/api/scene-notes/{sample_script_path}",
            params={"scene_id": scene_id, "note": "To be deleted"},
        )

        # Save empty note (should delete)
        response = client.post(
            f"/api/scene-notes/{sample_script_path}",
            params={"scene_id": scene_id, "note": "   "},  # Whitespace only
        )
        assert response.status_code == 200

        # Verify deletion
        response = client.get(f"/api/scene-notes/{sample_script_path}")
        assert scene_id not in response.json()["notes"]

    def test_get_scene_notes_export(self, client, sample_script_path):
        """Test GET /api/scene-notes-export returns all notes."""
        # Save some notes first
        notes = [
            ("hook", "Improve visual impact"),
            ("solution", "Add brand colors"),
        ]

        for scene_id, note_text in notes:
            client.post(
                f"/api/scene-notes/{sample_script_path}",
                params={"scene_id": scene_id, "note": note_text},
            )

        # Get export
        response = client.get("/api/scene-notes-export")
        assert response.status_code == 200

        data = response.json()
        assert "generated" in data
        assert "project" in data
        assert "total_notes" in data
        assert "scripts" in data

        # Check that our notes are in the export
        scripts = data["scripts"]
        assert len(scripts) > 0

        # Find our script in the export
        our_script = None
        for script in scripts:
            if sample_script_path in script["script_path"]:
                our_script = script
                break

        assert our_script is not None
        assert "script_name" in our_script
        assert "notes" in our_script
        assert len(our_script["notes"]) == 2

    def test_scene_notes_export_includes_scene_metadata(self, client, sample_script_path):
        """Test that scene notes export includes scene metadata from YAML."""
        # Save a note
        client.post(
            f"/api/scene-notes/{sample_script_path}",
            params={"scene_id": "hook", "note": "Test metadata"},
        )

        # Get export
        response = client.get("/api/scene-notes-export")
        data = response.json()

        # Find our note
        for script in data["scripts"]:
            if sample_script_path in script["script_path"]:
                notes = script["notes"]
                hook_note = next((n for n in notes if n["scene_id"] == "hook"), None)
                assert hook_note is not None
                # Should include scene metadata if available
                assert "scene_id" in hook_note
                assert "text" in hook_note
                assert "created" in hook_note

    def test_scene_notes_with_special_characters_in_path(self, client):
        """Test scene notes with special characters in script path."""
        # Use a path with spaces and special chars
        script_path = "content/en/scripts/test-script_name.yaml"

        response = client.get(f"/api/scene-notes/{script_path}")
        assert response.status_code == 200

        # Save a note
        response = client.post(
            f"/api/scene-notes/{script_path}",
            params={"scene_id": "test", "note": "Test note"},
        )
        assert response.status_code == 200

        # Retrieve it
        response = client.get(f"/api/scene-notes/{script_path}")
        assert response.status_code == 200
        assert "test" in response.json()["notes"]


class TestQualityAPI:
    """Tests for quality and validation endpoints."""

    def test_get_quality(self, client):
        """Test GET /api/quality runs quality checks."""
        response = client.get("/api/quality")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "errors" in data
        assert "warnings" in data
        assert "info" in data
        assert "issues" in data

        issues = data["issues"]
        assert isinstance(issues, list)

        # If there are issues, check structure
        if len(issues) > 0:
            issue = issues[0]
            assert "severity" in issue
            assert "category" in issue
            assert "message" in issue

    def test_get_validation(self, client):
        """Test GET /api/validation validates project."""
        response = client.get("/api/validation")
        assert response.status_code == 200

        data = response.json()
        assert "valid" in data
        assert "total" in data
        assert "errors" in data
        assert "warnings" in data
        assert "issues" in data

        assert isinstance(data["valid"], bool)
        assert isinstance(data["total"], int)
        assert isinstance(data["errors"], int)
        assert isinstance(data["warnings"], int)
        assert isinstance(data["issues"], list)


class TestMediaAPI:
    """Tests for media files and assets endpoints."""

    def test_get_media_files(self, client):
        """Test GET /api/media returns media files."""
        response = client.get("/api/media")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "by_type" in data
        assert "files" in data
        assert "output_dir" in data

        assert isinstance(data["files"], list)
        assert isinstance(data["by_type"], dict)

    def test_get_assets(self, client):
        """Test GET /api/assets returns project assets."""
        response = client.get("/api/assets")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "by_type" in data
        assert "assets" in data

        assert isinstance(data["assets"], list)


class TestAuditLogAPI:
    """Tests for audit log endpoint."""

    def test_get_audit_log(self, client):
        """Test GET /api/audit-log returns log entries."""
        response = client.get("/api/audit-log")
        assert response.status_code == 200

        data = response.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)

    def test_get_audit_log_with_limit(self, client):
        """Test GET /api/audit-log with limit parameter."""
        response = client.get("/api/audit-log?limit=10")
        assert response.status_code == 200

        data = response.json()
        entries = data["entries"]
        assert len(entries) <= 10


class TestPacksAPI:
    """Tests for packs API endpoint."""

    def test_get_packs(self, client):
        """Test GET /api/packs returns available packs."""
        response = client.get("/api/packs")
        assert response.status_code == 200

        data = response.json()
        assert "packs" in data

        packs = data["packs"]
        assert isinstance(packs, dict)
        assert "investor" in packs
        assert "pilot" in packs

        # Check pack structure
        investor = packs["investor"]
        assert "name" in investor
        assert "description" in investor
        assert "contents" in investor
        assert "audience" in investor


class TestRegistryAPI:
    """Tests for document registry endpoint."""

    def test_get_registry(self, client):
        """Test GET /api/registry returns document registry."""
        response = client.get("/api/registry")
        assert response.status_code == 200

        data = response.json()
        assert "found" in data

        # Registry may or may not exist
        if data["found"]:
            assert "categories" in data
            assert "status_counts" in data


class TestProjectSwitcherAPI:
    """Tests for project switcher API endpoints."""

    def test_get_recent_projects(self, client):
        """Test GET /api/recent-projects returns project list."""
        response = client.get("/api/recent-projects")
        assert response.status_code == 200

        data = response.json()
        assert "current" in data
        assert "recent" in data
        assert isinstance(data["recent"], list)

        # Current project should be set
        assert data["current"] is not None
        assert "path" in data["current"]
        assert "name" in data["current"]

    def test_recent_projects_structure(self, client):
        """Test that recent projects have correct structure."""
        response = client.get("/api/recent-projects")
        data = response.json()

        # After accessing the dashboard, there should be at least one recent project
        if len(data["recent"]) > 0:
            proj = data["recent"][0]
            assert "path" in proj
            assert "name" in proj
            assert "last_accessed" in proj
            assert "exists" in proj

    def test_open_project_nonexistent(self, client):
        """Test POST /api/open-project with nonexistent path."""
        response = client.post(
            "/api/open-project",
            params={"path": "/nonexistent/path/to/project"}
        )
        assert response.status_code == 404
        assert "not exist" in response.json()["detail"].lower()

    def test_open_project_no_project_yaml(self, client, temp_dir):
        """Test POST /api/open-project with directory but no project.yaml."""
        # Create an empty directory
        empty_dir = temp_dir / "empty_project"
        empty_dir.mkdir()

        response = client.post(
            "/api/open-project",
            params={"path": str(empty_dir)}
        )
        assert response.status_code == 400
        assert "project.yaml" in response.json()["detail"].lower()

    def test_open_project_valid(self, client, demo_project_web):
        """Test POST /api/open-project with valid project path."""
        response = client.post(
            "/api/open-project",
            params={"path": str(demo_project_web)}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "switched"
        assert "project" in data
        assert "path" in data["project"]
        assert "name" in data["project"]

    def test_remove_recent_project(self, client):
        """Test DELETE /api/recent-projects removes a project."""
        # First, get current recent projects
        response = client.get("/api/recent-projects")
        initial_recent = response.json()["recent"]

        # Try to remove a nonexistent project
        response = client.delete(
            "/api/recent-projects",
            params={"path": "/some/fake/path/that/doesnt/exist"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"

    def test_open_and_verify_recent(self, client, demo_project_web):
        """Test that opening a project works (temp dirs not added to recent)."""
        # Open the project first
        response = client.post(
            "/api/open-project",
            params={"path": str(demo_project_web)}
        )
        assert response.status_code == 200

        # Now check recent projects
        response = client.get("/api/recent-projects")
        data = response.json()

        # Temp directory projects are intentionally not added to recent list
        # to avoid polluting the list with test/temporary projects
        recent_paths = [p["path"] for p in data["recent"]]
        demo_path_resolved = str(Path(demo_project_web).resolve())

        # Verify the API works, but temp paths are filtered from recent
        assert "recent" in data
        # Temp directory should NOT appear in recent (by design)
        assert demo_path_resolved not in recent_paths or not any(
            indicator in demo_path_resolved.lower()
            for indicator in ["/tmp/", "/var/folders/", "/private/var/folders/"]
        )
