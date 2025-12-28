"""
Integration tests for AI Queue API endpoints.

Tests the FastAPI endpoints for AI task queue management:
- POST /api/ai/tasks - Submit task
- GET /api/ai/tasks - List tasks
- GET /api/ai/tasks/{id} - Get task details
- POST /api/ai/tasks/{id}/cancel - Cancel task
- DELETE /api/ai/tasks/{id} - Delete task
- GET /api/ai/queue/stats - Queue statistics
"""

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
    from media_engine.web.app import create_app

# Path to demo project
DEMO_PROJECT_PATH = Path(__file__).parent.parent.parent / "demo"


@pytest.fixture
def demo_project_queue(temp_dir):
    """Create a copy of demo project for queue tests."""
    if not HAS_FASTAPI:
        pytest.skip("FastAPI not installed")

    if not DEMO_PROJECT_PATH.exists():
        pytest.skip("Demo project not found")

    # Copy demo to temp
    dest = temp_dir / "demo"
    shutil.copytree(DEMO_PROJECT_PATH, dest)

    # Clear any existing tasks
    tasks_file = dest / ".media-engine" / "ai_tasks.json"
    if tasks_file.exists():
        tasks_file.write_text("[]")

    return dest


@pytest.fixture
def client(demo_project_queue):
    """Create FastAPI test client with demo project."""
    app = create_app(demo_project_queue)
    return TestClient(app)


class TestTaskSubmission:
    """Tests for task submission endpoint."""

    def test_submit_task(self, client):
        """Test POST /api/ai/tasks creates a new task."""
        response = client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [
                    {
                        "path": "content/en/chapters/01_introduction.md",
                        "content": "Test content",
                        "title": "Test Doc",
                    }
                ],
                "instructions": "Make it better",
                "priority": "high",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["operation"] == "improve"
        assert data["priority"] == "high"
        assert data["selections_count"] == 1

    def test_submit_task_with_notes(self, client):
        """Test submitting task with attached notes."""
        response = client.post(
            "/api/ai/tasks",
            json={
                "operation": "analyze",
                "selections": [
                    {
                        "path": "content/en/chapters/01_introduction.md",
                        "content": "Content here",
                        "title": "Doc",
                        "notes": [{"text": "Check this part", "priority": "high"}],
                    }
                ],
                "instructions": "Review with notes",
            },
        )

        assert response.status_code == 200
        assert response.json()["task_id"] is not None

    def test_submit_translation_task(self, client):
        """Test submitting translation task with target language."""
        response = client.post(
            "/api/ai/tasks",
            json={
                "operation": "translate",
                "selections": [
                    {
                        "path": "content/en/chapters/01_introduction.md",
                        "content": "English content",
                        "title": "Intro",
                    }
                ],
                "instructions": "Translate to Norwegian",
                "target_language": "no",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["operation"] == "translate"


class TestTaskListing:
    """Tests for task listing endpoint."""

    def test_list_tasks_empty(self, client):
        """Test GET /api/ai/tasks with empty queue."""
        response = client.get("/api/ai/tasks")
        assert response.status_code == 200

        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert "stats" in data

    def test_list_tasks_with_tasks(self, client):
        """Test listing tasks after submission."""
        # Submit some tasks
        client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [{"path": "a.md", "content": "A", "title": "A"}],
                "instructions": "Task 1",
            },
        )
        client.post(
            "/api/ai/tasks",
            json={
                "operation": "analyze",
                "selections": [{"path": "b.md", "content": "B", "title": "B"}],
                "instructions": "Task 2",
            },
        )

        response = client.get("/api/ai/tasks")
        data = response.json()

        assert data["total"] == 2
        assert len(data["tasks"]) == 2

    def test_list_tasks_filter_by_status(self, client):
        """Test filtering tasks by status."""
        # Submit a task
        client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [{"path": "a.md", "content": "A", "title": "A"}],
                "instructions": "Task 1",
            },
        )

        # List pending only
        response = client.get("/api/ai/tasks?status=pending")
        data = response.json()

        assert data["total"] == 1
        assert data["tasks"][0]["status"] == "pending"

        # List completed (should be empty)
        response = client.get("/api/ai/tasks?status=completed")
        data = response.json()
        assert data["total"] == 0

    def test_list_tasks_with_limit(self, client):
        """Test limiting task list."""
        # Submit 5 tasks
        for i in range(5):
            client.post(
                "/api/ai/tasks",
                json={
                    "operation": "improve",
                    "selections": [{"path": f"{i}.md", "content": "X", "title": f"T{i}"}],
                    "instructions": f"Task {i}",
                },
            )

        # List with limit
        response = client.get("/api/ai/tasks?limit=3")
        data = response.json()

        assert len(data["tasks"]) == 3


class TestTaskDetails:
    """Tests for task details endpoint."""

    def test_get_task(self, client):
        """Test GET /api/ai/tasks/{id}."""
        # Submit a task
        submit_response = client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [{"path": "doc.md", "content": "Content", "title": "Doc"}],
                "instructions": "Make it better",
            },
        )
        task_id = submit_response.json()["task_id"]

        # Get task details
        response = client.get(f"/api/ai/tasks/{task_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == task_id
        assert data["operation"] == "improve"
        assert data["instructions"] == "Make it better"
        assert len(data["selections"]) == 1

    def test_get_task_not_found(self, client):
        """Test getting non-existent task."""
        response = client.get("/api/ai/tasks/nonexistent")
        assert response.status_code == 404


class TestTaskCancellation:
    """Tests for task cancellation endpoint."""

    def test_cancel_task(self, client):
        """Test POST /api/ai/tasks/{id}/cancel."""
        # Submit a task
        submit_response = client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [{"path": "doc.md", "content": "X", "title": "Doc"}],
                "instructions": "Task",
            },
        )
        task_id = submit_response.json()["task_id"]

        # Cancel it
        response = client.post(f"/api/ai/tasks/{task_id}/cancel")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "cancelled"

        # Verify it's cancelled
        get_response = client.get(f"/api/ai/tasks/{task_id}")
        assert get_response.json()["status"] == "cancelled"

    def test_cancel_nonexistent_task(self, client):
        """Test cancelling non-existent task."""
        response = client.post("/api/ai/tasks/nonexistent/cancel")
        assert response.status_code == 400


class TestTaskDeletion:
    """Tests for task deletion endpoint."""

    def test_delete_cancelled_task(self, client):
        """Test DELETE /api/ai/tasks/{id} for cancelled task."""
        # Submit and cancel a task
        submit_response = client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [{"path": "doc.md", "content": "X", "title": "Doc"}],
                "instructions": "Task",
            },
        )
        task_id = submit_response.json()["task_id"]
        client.post(f"/api/ai/tasks/{task_id}/cancel")

        # Delete it
        response = client.delete(f"/api/ai/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify it's gone
        get_response = client.get(f"/api/ai/tasks/{task_id}")
        assert get_response.status_code == 404

    def test_delete_pending_task_fails(self, client):
        """Test that deleting pending task fails."""
        # Submit a task (stays pending)
        submit_response = client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [{"path": "doc.md", "content": "X", "title": "Doc"}],
                "instructions": "Task",
            },
        )
        task_id = submit_response.json()["task_id"]

        # Try to delete (should fail)
        response = client.delete(f"/api/ai/tasks/{task_id}")
        assert response.status_code == 400


class TestQueueStats:
    """Tests for queue statistics endpoint."""

    def test_get_queue_stats_empty(self, client):
        """Test GET /api/ai/queue/stats with empty queue."""
        response = client.get("/api/ai/queue/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_operation" in data
        assert data["total"] == 0

    def test_get_queue_stats_with_tasks(self, client):
        """Test queue stats with tasks."""
        # Submit tasks of different operations
        client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [{"path": "a.md", "content": "A", "title": "A"}],
                "instructions": "Improve",
            },
        )
        client.post(
            "/api/ai/tasks",
            json={
                "operation": "translate",
                "selections": [{"path": "b.md", "content": "B", "title": "B"}],
                "instructions": "Translate",
            },
        )
        client.post(
            "/api/ai/tasks",
            json={
                "operation": "improve",
                "selections": [{"path": "c.md", "content": "C", "title": "C"}],
                "instructions": "Improve 2",
            },
        )

        response = client.get("/api/ai/queue/stats")
        data = response.json()

        assert data["total"] == 3
        assert data["by_status"]["pending"] == 3
        assert data["by_operation"]["improve"] == 2
        assert data["by_operation"]["translate"] == 1


class TestAIContext:
    """Tests for AI context endpoints."""

    def test_get_ai_context(self, client):
        """Test GET /api/ai/context returns full context."""
        response = client.get("/api/ai/context")
        assert response.status_code == 200

        data = response.json()
        # Context should have various sections
        assert isinstance(data, dict)

    def test_get_document_context(self, client):
        """Test GET /api/ai/context/document/{path}."""
        response = client.get("/api/ai/context/document/content/en/chapters/01_introduction.md")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)


class TestAISessions:
    """Tests for AI session endpoints."""

    def test_list_sessions(self, client):
        """Test GET /api/ai/sessions."""
        response = client.get("/api/ai/sessions")
        assert response.status_code == 200

        data = response.json()
        assert "sessions" in data
        assert "total" in data


class TestAIOperations:
    """Tests for AI operations endpoint."""

    def test_list_operations(self, client):
        """Test GET /api/ai/operations."""
        response = client.get("/api/ai/operations")
        assert response.status_code == 200

        data = response.json()
        assert "operations" in data

        # Check expected operations exist
        op_ids = [op["id"] for op in data["operations"]]
        assert "improve" in op_ids
        assert "translate" in op_ids
        assert "analyze" in op_ids


class TestAIModels:
    """Tests for AI models endpoint."""

    def test_list_models(self, client):
        """Test GET /api/ai/models."""
        response = client.get("/api/ai/models")
        assert response.status_code == 200

        data = response.json()
        assert "models" in data
        assert len(data["models"]) > 0


class TestAIBackends:
    """Tests for AI backends endpoint."""

    def test_list_backends(self, client):
        """Test GET /api/ai/backends."""
        response = client.get("/api/ai/backends")
        assert response.status_code == 200

        data = response.json()
        assert "backends" in data
        assert len(data["backends"]) > 0

        # Check expected backends
        backend_ids = [b["id"] for b in data["backends"]]
        assert "anthropic" in backend_ids
        assert "claude_code" in backend_ids
