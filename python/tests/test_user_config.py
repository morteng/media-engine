"""
Unit tests for user configuration module.

Tests the recent projects tracking functionality in ~/.media-engine/
"""

from pathlib import Path

import pytest


@pytest.fixture
def temp_home(temp_dir, monkeypatch):
    """Create a temporary home directory for tests."""
    fake_home = temp_dir / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    # Also patch Path.home() for macOS/Linux
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    return fake_home


@pytest.fixture
def user_config_module(temp_home):
    """Import user_config module with mocked home directory."""
    from media_engine.config import user_config
    return user_config


class TestGetUserConfigDir:
    """Tests for get_user_config_dir function."""

    def test_creates_directory(self, user_config_module, temp_home):
        """Test that config directory is created if it doesn't exist."""
        config_dir = user_config_module.get_user_config_dir()
        assert config_dir.exists()
        assert config_dir == temp_home / ".media-engine"

    def test_returns_existing_directory(self, user_config_module, temp_home):
        """Test that existing config directory is returned."""
        # Create directory first
        expected_dir = temp_home / ".media-engine"
        expected_dir.mkdir(parents=True, exist_ok=True)

        config_dir = user_config_module.get_user_config_dir()
        assert config_dir == expected_dir


class TestRecentProjects:
    """Tests for recent projects tracking."""

    def test_empty_recent_projects(self, user_config_module):
        """Test that empty list is returned when no config exists."""
        projects = user_config_module.get_recent_projects(include_temp=True)
        assert projects == []

    def test_add_recent_project(self, user_config_module, temp_dir):
        """Test adding a project to recent list."""
        project_path = str(temp_dir / "test_project")
        # Resolve to handle macOS /var -> /private/var symlink
        resolved_path = str(Path(project_path).resolve())

        project = user_config_module.add_recent_project(project_path, "Test Project", allow_temp=True)

        assert project.path == resolved_path
        assert project.name == "Test Project"
        assert project.last_accessed is not None

        # Verify it's in the list
        projects = user_config_module.get_recent_projects(include_temp=True)
        assert len(projects) == 1
        assert projects[0].path == resolved_path

    def test_add_multiple_projects(self, user_config_module, temp_dir):
        """Test adding multiple projects."""
        paths = [
            str(temp_dir / "project1"),
            str(temp_dir / "project2"),
            str(temp_dir / "project3"),
        ]

        for i, path in enumerate(paths):
            user_config_module.add_recent_project(path, f"Project {i+1}", allow_temp=True)

        projects = user_config_module.get_recent_projects(include_temp=True)
        assert len(projects) == 3

    def test_most_recent_first(self, user_config_module, temp_dir):
        """Test that most recently accessed project is first."""
        import time

        path1 = str(temp_dir / "project1")
        path2 = str(temp_dir / "project2")

        user_config_module.add_recent_project(path1, "First Project", allow_temp=True)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        user_config_module.add_recent_project(path2, "Second Project", allow_temp=True)

        projects = user_config_module.get_recent_projects(include_temp=True)
        assert projects[0].name == "Second Project"
        assert projects[1].name == "First Project"

    def test_update_existing_project(self, user_config_module, temp_dir):
        """Test that adding existing project updates it."""
        import time

        path = str(temp_dir / "project")

        user_config_module.add_recent_project(path, "Original Name", allow_temp=True)
        time.sleep(0.01)
        user_config_module.add_recent_project(path, "Updated Name", allow_temp=True)

        projects = user_config_module.get_recent_projects(include_temp=True)
        # Should only have one entry
        assert len(projects) == 1
        assert projects[0].name == "Updated Name"

    def test_remove_recent_project(self, user_config_module, temp_dir):
        """Test removing a project from recent list."""
        path1 = str(temp_dir / "project1")
        path2 = str(temp_dir / "project2")
        # Resolve to handle macOS /var -> /private/var symlink
        resolved_path2 = str(Path(path2).resolve())

        user_config_module.add_recent_project(path1, "Project 1", allow_temp=True)
        user_config_module.add_recent_project(path2, "Project 2", allow_temp=True)

        # Remove first project
        result = user_config_module.remove_recent_project(path1)
        assert result is True

        projects = user_config_module.get_recent_projects(include_temp=True)
        assert len(projects) == 1
        assert projects[0].path == resolved_path2

    def test_remove_nonexistent_project(self, user_config_module):
        """Test removing a project that doesn't exist."""
        result = user_config_module.remove_recent_project("/nonexistent/path")
        assert result is False

    def test_max_recent_projects(self, user_config_module, temp_dir):
        """Test that max_recent_projects limit is enforced."""
        # Add 15 projects (more than default max of 10)
        for i in range(15):
            path = str(temp_dir / f"project{i}")
            user_config_module.add_recent_project(path, f"Project {i}", allow_temp=True)

        projects = user_config_module.get_recent_projects(include_temp=True)
        assert len(projects) <= 10

    def test_project_exists(self, user_config_module, temp_dir):
        """Test project_exists function."""
        # Create a valid project directory
        project_dir = temp_dir / "valid_project"
        project_dir.mkdir()
        (project_dir / "project.yaml").write_text("name: Test")

        assert user_config_module.project_exists(str(project_dir)) is True

        # Non-existent path
        assert user_config_module.project_exists("/nonexistent/path") is False

        # Directory without project.yaml
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        assert user_config_module.project_exists(str(empty_dir)) is False

    def test_path_normalization(self, user_config_module, temp_dir):
        """Test that paths are normalized."""
        # Add with relative path notation
        path = str(temp_dir / "project" / ".." / "project")
        user_config_module.add_recent_project(path, "Test", allow_temp=True)

        projects = user_config_module.get_recent_projects(include_temp=True)
        assert len(projects) == 1
        # Path should be normalized (no ..)
        assert ".." not in projects[0].path


class TestRecentProjectDataclass:
    """Tests for RecentProject dataclass."""

    def test_to_dict(self, user_config_module):
        """Test converting RecentProject to dict."""
        project = user_config_module.RecentProject(
            path="/test/path",
            name="Test Project",
            last_accessed="2024-01-15T10:00:00",
        )

        data = project.to_dict()
        assert data["path"] == "/test/path"
        assert data["name"] == "Test Project"
        assert data["last_accessed"] == "2024-01-15T10:00:00"

    def test_from_dict(self, user_config_module):
        """Test creating RecentProject from dict."""
        data = {
            "path": "/test/path",
            "name": "Test Project",
            "last_accessed": "2024-01-15T10:00:00",
        }

        project = user_config_module.RecentProject.from_dict(data)
        assert project.path == "/test/path"
        assert project.name == "Test Project"
        assert project.last_accessed == "2024-01-15T10:00:00"

    def test_from_dict_defaults(self, user_config_module):
        """Test that from_dict provides default values."""
        data = {"path": "/test/path"}

        project = user_config_module.RecentProject.from_dict(data)
        assert project.path == "/test/path"
        assert project.name == "path"  # Defaults to directory name
        assert project.last_accessed is not None
