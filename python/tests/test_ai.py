"""Tests for AI module."""


class TestAITypes:
    """Test AI type definitions."""

    def test_ai_operation_enum(self):
        """Test AIOperation enum."""
        from media_engine.ai import AIOperation

        assert AIOperation.IMPROVE is not None
        assert AIOperation.TRANSLATE is not None
        assert AIOperation.ANALYZE is not None
        assert AIOperation.SUMMARIZE is not None

    def test_ai_backend_enum(self):
        """Test AIBackend enum."""
        from media_engine.ai import AIBackend

        assert AIBackend.ANTHROPIC is not None
        assert AIBackend.CLAUDE_CODE is not None

    def test_content_selection(self):
        """Test ContentSelection dataclass."""
        from media_engine.ai import ContentSelection

        selection = ContentSelection(
            path="en/chapters/intro.md",
            content="Test content",
            title="Test Title",
        )

        assert selection.path == "en/chapters/intro.md"
        assert selection.content == "Test content"
        assert selection.title == "Test Title"

    def test_content_selection_with_metadata(self):
        """Test ContentSelection with metadata."""
        from media_engine.ai import ContentSelection

        selection = ContentSelection(
            path="en/chapters/intro.md",
            content="Test content",
            title="Test Title",
            content_type="document",
            metadata={"version": "1.0"},
        )

        assert selection.content_type == "document"
        assert selection.metadata["version"] == "1.0"

    def test_ai_process_request(self):
        """Test AIProcessRequest dataclass."""
        from media_engine.ai import AIOperation, AIProcessRequest, ContentSelection

        selection = ContentSelection(
            path="test.md",
            content="Test content",
            title="Test",
        )

        request = AIProcessRequest(
            operation=AIOperation.IMPROVE,
            selections=[selection],
            instructions="Improve clarity",
        )

        assert request.operation == AIOperation.IMPROVE
        assert request.instructions == "Improve clarity"
        assert len(request.selections) == 1


class TestAIConfig:
    """Test AI configuration."""

    def test_ai_config_creation(self):
        """Test AIConfig creation."""
        from media_engine.ai import AIBackend, AIConfig

        config = AIConfig(
            api_key="test-key",
            backend=AIBackend.ANTHROPIC,
        )

        assert config.api_key == "test-key"
        assert config.backend == AIBackend.ANTHROPIC

    def test_ai_config_defaults(self):
        """Test AIConfig defaults."""
        from media_engine.ai import AIBackend, AIConfig

        config = AIConfig()

        assert config.backend == AIBackend.CLAUDE_CODE
        assert config.max_tokens == 4096

    def test_get_ai_config_default(self, tmp_path, monkeypatch):
        """Test get_ai_config returns default when no config."""
        from media_engine.ai import get_ai_config

        config = get_ai_config()
        # Should return a config object (default or loaded)
        assert config is not None


class TestTaskQueue:
    """Test AI task queue."""

    def test_task_status_enum(self):
        """Test TaskStatus enum."""
        from media_engine.ai import TaskStatus

        assert TaskStatus.PENDING is not None
        assert TaskStatus.PROCESSING is not None
        assert TaskStatus.COMPLETED is not None
        assert TaskStatus.FAILED is not None

    def test_task_priority_enum(self):
        """Test TaskPriority enum."""
        from media_engine.ai import TaskPriority

        assert TaskPriority.LOW is not None
        assert TaskPriority.NORMAL is not None
        assert TaskPriority.HIGH is not None
        assert TaskPriority.URGENT is not None

    def test_task_queue_init(self, tmp_path):
        """Test TaskQueue initialization."""
        from media_engine.ai import TaskQueue

        # Create .media-engine directory
        (tmp_path / ".media-engine").mkdir()

        queue = TaskQueue(tmp_path)

        assert queue is not None
        assert queue.project_root == tmp_path

    def test_task_queue_submit_task(self, tmp_path):
        """Test submitting task to queue."""
        from media_engine.ai import TaskQueue

        # Create .media-engine directory
        (tmp_path / ".media-engine").mkdir()

        queue = TaskQueue(tmp_path)

        task = queue.submit(
            operation="improve",
            instructions="Make this better",
            selections=[
                {
                    "path": "test.md",
                    "title": "Test",
                    "content": "Test content",
                }
            ],
            priority="normal",
        )

        assert task is not None
        assert task.id is not None
        assert task.operation == "improve"

    def test_task_queue_list_tasks(self, tmp_path):
        """Test listing tasks in queue."""
        from media_engine.ai import TaskQueue

        # Create .media-engine directory
        (tmp_path / ".media-engine").mkdir()

        queue = TaskQueue(tmp_path)

        # Add a task
        queue.submit(
            operation="improve",
            instructions="Make this better",
            selections=[
                {
                    "path": "test1.md",
                    "title": "Test",
                    "content": "Test content",
                }
            ],
        )

        tasks = queue.list_tasks()
        assert len(tasks) >= 1

    def test_task_queue_stats(self, tmp_path):
        """Test queue statistics."""
        from media_engine.ai import TaskQueue

        # Create .media-engine directory
        (tmp_path / ".media-engine").mkdir()

        queue = TaskQueue(tmp_path)

        stats = queue.get_stats()
        assert "pending" in stats
        assert "processing" in stats
        assert "completed" in stats
        assert "failed" in stats
