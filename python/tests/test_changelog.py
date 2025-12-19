"""
Tests for the changelog generation module.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from media_engine.changelog import (
    ChangeEntry,
    ChangelogGenerator,
    ChangelogVersion,
    ChangeType,
    generate_changelog,
)


class TestChangeType:
    """Test ChangeType enum."""

    def test_change_types_exist(self):
        """Test all change types are defined."""
        assert ChangeType.ADDED.value == "added"
        assert ChangeType.CHANGED.value == "changed"
        assert ChangeType.DEPRECATED.value == "deprecated"
        assert ChangeType.REMOVED.value == "removed"
        assert ChangeType.FIXED.value == "fixed"
        assert ChangeType.SECURITY.value == "security"
        assert ChangeType.TRANSLATION.value == "translation"
        assert ChangeType.DOCUMENTATION.value == "documentation"


class TestChangeEntry:
    """Test ChangeEntry dataclass."""

    def test_create_entry(self):
        """Test creating a change entry."""
        entry = ChangeEntry(
            type=ChangeType.ADDED,
            description="Added new feature",
            date=datetime(2024, 1, 15),
            author="developer",
            commit="abc1234",
            files=["src/feature.py"],
            breaking=False,
        )

        assert entry.type == ChangeType.ADDED
        assert entry.description == "Added new feature"
        assert entry.author == "developer"
        assert entry.commit == "abc1234"
        assert entry.files == ["src/feature.py"]
        assert entry.breaking is False

    def test_create_breaking_change(self):
        """Test creating a breaking change entry."""
        entry = ChangeEntry(
            type=ChangeType.CHANGED,
            description="Changed API signature",
            date=datetime.now(),
            breaking=True,
        )

        assert entry.breaking is True

    def test_default_values(self):
        """Test default values for optional fields."""
        entry = ChangeEntry(
            type=ChangeType.FIXED,
            description="Fixed bug",
            date=datetime.now(),
        )

        assert entry.author is None
        assert entry.commit is None
        assert entry.files == []
        assert entry.breaking is False


class TestChangelogVersion:
    """Test ChangelogVersion dataclass."""

    def test_create_version(self):
        """Test creating a changelog version."""
        version = ChangelogVersion(
            version="1.0.0",
            date=datetime(2024, 1, 15),
            entries=[
                ChangeEntry(
                    type=ChangeType.ADDED,
                    description="Initial release",
                    date=datetime(2024, 1, 15),
                )
            ],
            summary="First release",
        )

        assert version.version == "1.0.0"
        assert len(version.entries) == 1
        assert version.summary == "First release"

    def test_default_entries_list(self):
        """Test default empty entries list."""
        version = ChangelogVersion(
            version="1.0.0",
            date=datetime.now(),
        )

        assert version.entries == []
        assert version.summary is None


class TestGitHistoryParser:
    """Test GitHistoryParser class."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project."""
        project = MagicMock()
        project.root = temp_dir
        return project

    def test_parse_commit_type_feat(self, mock_project):
        """Test parsing feat commit."""
        from media_engine.changelog import GitHistoryParser

        parser = GitHistoryParser(mock_project)
        change_type, desc, breaking = parser.parse_commit_type("feat: add new feature")

        assert change_type == ChangeType.ADDED
        assert desc == "add new feature"
        assert breaking is False

    def test_parse_commit_type_fix(self, mock_project):
        """Test parsing fix commit."""
        from media_engine.changelog import GitHistoryParser

        parser = GitHistoryParser(mock_project)
        change_type, desc, breaking = parser.parse_commit_type("fix: resolve issue")

        assert change_type == ChangeType.FIXED
        assert desc == "resolve issue"

    def test_parse_commit_type_docs(self, mock_project):
        """Test parsing docs commit."""
        from media_engine.changelog import GitHistoryParser

        parser = GitHistoryParser(mock_project)
        change_type, desc, breaking = parser.parse_commit_type("docs: update readme")

        assert change_type == ChangeType.DOCUMENTATION

    def test_parse_commit_type_breaking(self, mock_project):
        """Test parsing breaking change."""
        from media_engine.changelog import GitHistoryParser

        parser = GitHistoryParser(mock_project)
        change_type, desc, breaking = parser.parse_commit_type("! feat: breaking change")

        assert breaking is True

    def test_parse_commit_type_breaking_keyword(self, mock_project):
        """Test parsing BREAKING keyword."""
        from media_engine.changelog import GitHistoryParser

        parser = GitHistoryParser(mock_project)
        change_type, desc, breaking = parser.parse_commit_type(
            "refactor: BREAKING change to API"
        )

        assert breaking is True

    def test_parse_commit_type_unknown(self, mock_project):
        """Test parsing unknown commit type defaults to CHANGED."""
        from media_engine.changelog import GitHistoryParser

        parser = GitHistoryParser(mock_project)
        change_type, desc, breaking = parser.parse_commit_type(
            "Some commit message without type"
        )

        assert change_type == ChangeType.CHANGED

    def test_parse_commit_type_with_scope(self, mock_project):
        """Test parsing commit with scope."""
        from media_engine.changelog import GitHistoryParser

        parser = GitHistoryParser(mock_project)
        change_type, desc, breaking = parser.parse_commit_type("feat(api): add endpoint")

        assert change_type == ChangeType.ADDED


class TestChangelogGenerator:
    """Test ChangelogGenerator class."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project."""
        project = MagicMock()
        project.root = temp_dir
        project.languages = ["en"]
        project.list_chapters = MagicMock(return_value=[])
        return project

    @pytest.fixture
    def generator(self, mock_project):
        """Create a changelog generator."""
        return ChangelogGenerator(mock_project)

    def test_to_markdown_empty(self, generator):
        """Test markdown output with no entries."""
        result = generator.to_markdown([], title="Changelog")

        assert "# Changelog" in result
        assert "No changes recorded" in result

    def test_to_markdown_with_entries(self, generator):
        """Test markdown output with entries."""
        entries = [
            ChangeEntry(
                type=ChangeType.ADDED,
                description="New feature",
                date=datetime(2024, 1, 15),
            ),
            ChangeEntry(
                type=ChangeType.FIXED,
                description="Bug fix",
                date=datetime(2024, 1, 14),
            ),
        ]

        result = generator.to_markdown(entries)

        assert "## Added" in result
        assert "New feature" in result
        assert "## Fixed" in result
        assert "Bug fix" in result

    def test_to_markdown_breaking_change(self, generator):
        """Test markdown output with breaking change."""
        entries = [
            ChangeEntry(
                type=ChangeType.CHANGED,
                description="API change",
                date=datetime.now(),
                breaking=True,
            ),
        ]

        result = generator.to_markdown(entries)
        assert "**BREAKING**" in result

    def test_to_markdown_chronological(self, generator):
        """Test markdown output in chronological order."""
        entries = [
            ChangeEntry(
                type=ChangeType.ADDED,
                description="Feature 1",
                date=datetime(2024, 1, 15),
            ),
            ChangeEntry(
                type=ChangeType.ADDED,
                description="Feature 2",
                date=datetime(2024, 1, 14),
            ),
        ]

        result = generator.to_markdown(entries, group_by_type=False)

        assert "2024-01-15" in result
        assert "2024-01-14" in result

    def test_to_json(self, generator):
        """Test JSON output."""
        entries = [
            ChangeEntry(
                type=ChangeType.ADDED,
                description="New feature",
                date=datetime(2024, 1, 15),
                author="developer",
                commit="abc1234",
            ),
        ]

        result = generator.to_json(entries)

        assert len(result) == 1
        assert result[0]["type"] == "added"
        assert result[0]["description"] == "New feature"
        assert result[0]["author"] == "developer"

    @patch("media_engine.changelog.GitHistoryParser.get_commits")
    def test_generate_with_git(self, mock_get_commits, generator):
        """Test generating changelog from git."""
        mock_get_commits.return_value = []

        entries = generator.generate(include_git=True, include_docs=False)

        mock_get_commits.assert_called_once()

    def test_generate_removes_duplicates(self, generator):
        """Test that generate removes duplicate entries."""
        with patch.object(generator.git_parser, "get_commits", return_value=[]):
            with patch.object(generator.doc_tracker, "get_version_changes") as mock_docs:
                # Create duplicate entries
                now = datetime.now()
                mock_docs.return_value = [
                    ChangeEntry(
                        type=ChangeType.ADDED,
                        description="Same feature",
                        date=now,
                    ),
                    ChangeEntry(
                        type=ChangeType.ADDED,
                        description="Same feature",
                        date=now,
                    ),
                ]

                entries = generator.generate(include_git=False, include_docs=True)

                # Should deduplicate
                assert len(entries) == 1


class TestGenerateChangelogFunction:
    """Test the generate_changelog convenience function."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project."""
        project = MagicMock()
        project.root = temp_dir
        project.languages = ["en"]
        project.list_chapters = MagicMock(return_value=[])
        return project

    @patch("media_engine.changelog.ChangelogGenerator.generate")
    @patch("media_engine.changelog.ChangelogGenerator.to_markdown")
    def test_generate_markdown(self, mock_to_md, mock_generate, mock_project):
        """Test generating markdown changelog."""
        mock_generate.return_value = []
        mock_to_md.return_value = "# Changelog\n"

        result = generate_changelog(mock_project, format="markdown")

        assert "# Changelog" in result
        mock_to_md.assert_called_once()

    @patch("media_engine.changelog.ChangelogGenerator.generate")
    @patch("media_engine.changelog.ChangelogGenerator.to_json")
    def test_generate_json(self, mock_to_json, mock_generate, mock_project):
        """Test generating JSON changelog."""
        mock_generate.return_value = []
        mock_to_json.return_value = []

        result = generate_changelog(mock_project, format="json")

        assert result == "[]"
        mock_to_json.assert_called_once()
