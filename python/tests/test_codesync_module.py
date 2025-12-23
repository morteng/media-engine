"""Tests for codesync module."""

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (tmp_path / ".media-engine").mkdir()

    # Create project.yaml
    project_config = {
        "name": "CodeSync Test",
        "languages": ["en"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create sample document with code example
    doc = content_dir / "en" / "chapters" / "01_api.md"
    doc.write_text("""---
title: API Examples
status: final
---

# API Examples

```python
def authenticate(api_key):
    '''Authenticate with API key.'''
    return validate_key(api_key)
```

Use the `authenticate()` function to log in.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestEnhancedCodeSyncChecker:
    """Tests for EnhancedCodeSyncChecker."""

    def test_checker_import(self):
        """Test checker can be imported."""
        from media_engine.codesync import EnhancedCodeSyncChecker

        assert EnhancedCodeSyncChecker is not None

    def test_checker_creation(self, project):
        """Test creating checker."""
        from media_engine.codesync import EnhancedCodeSyncChecker

        checker = EnhancedCodeSyncChecker(project)
        assert checker is not None


class TestCodeBlock:
    """Tests for CodeBlock."""

    def test_code_block_import(self):
        """Test CodeBlock can be imported."""
        from media_engine.codesync import CodeBlock

        assert CodeBlock is not None


class TestSyncIssue:
    """Tests for SyncIssue."""

    def test_sync_issue_import(self):
        """Test SyncIssue can be imported."""
        from media_engine.codesync import SyncIssue

        assert SyncIssue is not None


class TestCodeBlockExtractor:
    """Tests for CodeBlockExtractor."""

    def test_extractor_import(self):
        """Test extractor can be imported."""
        from media_engine.codesync import CodeBlockExtractor

        assert CodeBlockExtractor is not None


class TestCheckCodeSync:
    """Tests for check_code_sync function."""

    def test_check_function_import(self):
        """Test function can be imported."""
        from media_engine.codesync import check_code_sync

        assert check_code_sync is not None


class TestCodeSyncModuleExports:
    """Tests for codesync module exports."""

    def test_module_exports(self):
        """Test all expected exports exist."""
        from media_engine import codesync

        assert hasattr(codesync, "EnhancedCodeSyncChecker")
        assert hasattr(codesync, "CodeBlock")
        assert hasattr(codesync, "SyncIssue")
        assert hasattr(codesync, "check_code_sync")
