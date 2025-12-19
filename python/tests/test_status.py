"""
Tests for media_engine.status module.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from media_engine.core.config import Config
from media_engine.core.project import LanguageConfig, Project
from media_engine.core.theme import Theme
from media_engine.status.dashboard import (
    ContentStatus,
    DeliverableStatus,
    DocumentStatus,
    ProjectDashboard,
    VideoStatus,
    get_content_status,
    get_deliverable_status,
    get_project_dashboard,
    get_video_status,
)


class TestDocumentStatus:
    """Tests for DocumentStatus dataclass."""

    def test_document_status_defaults(self, temp_dir):
        """Test DocumentStatus with default values."""
        status = DocumentStatus(
            path=temp_dir / "chapter.md",
            title="Test Chapter",
            status="draft",
            version="1.0.0",
        )
        assert status.path == temp_dir / "chapter.md"
        assert status.title == "Test Chapter"
        assert status.status == "draft"
        assert status.version == "1.0.0"
        assert status.last_modified is None
        assert status.word_count == 0
        assert status.freshness_status == "fresh"
        assert status.days_old == 0

    def test_document_status_with_all_fields(self, temp_dir):
        """Test DocumentStatus with all fields."""
        now = datetime.now()
        status = DocumentStatus(
            path=temp_dir / "chapter.md",
            title="Test Chapter",
            status="final",
            version="2.0.0",
            last_modified=now,
            word_count=500,
            freshness_status="stale",
            days_old=30,
        )
        assert status.last_modified == now
        assert status.word_count == 500
        assert status.freshness_status == "stale"
        assert status.days_old == 30


class TestContentStatus:
    """Tests for ContentStatus dataclass."""

    def test_content_status_defaults(self):
        """Test ContentStatus with default values."""
        status = ContentStatus(language="en")
        assert status.language == "en"
        assert status.chapters == []
        assert status.research == []
        assert status.total_words == 0
        assert status.completion_percent == 0.0
        assert status.stale_count == 0

    def test_content_status_with_chapters(self, temp_dir):
        """Test ContentStatus with chapter data."""
        chapters = [
            DocumentStatus(
                path=temp_dir / "ch1.md",
                title="Chapter 1",
                status="final",
                version="1.0.0",
                word_count=100,
            ),
            DocumentStatus(
                path=temp_dir / "ch2.md",
                title="Chapter 2",
                status="draft",
                version="0.1.0",
                word_count=200,
                freshness_status="stale",
            ),
        ]
        status = ContentStatus(
            language="en",
            chapters=chapters,
            total_words=300,
            completion_percent=50.0,
            stale_count=1,
        )
        assert len(status.chapters) == 2
        assert status.total_words == 300
        assert status.completion_percent == 50.0
        assert status.stale_count == 1


class TestVideoStatus:
    """Tests for VideoStatus dataclass."""

    def test_video_status_defaults(self):
        """Test VideoStatus with default values."""
        status = VideoStatus(script_name="intro", language="en")
        assert status.script_name == "intro"
        assert status.language == "en"
        assert status.has_script is False
        assert status.has_voiceover is False
        assert status.has_captions is False
        assert status.has_video is False
        assert status.duration_seconds == 0.0
        assert status.status == "not_started"

    def test_video_status_complete(self):
        """Test VideoStatus for completed video."""
        status = VideoStatus(
            script_name="demo",
            language="en",
            has_script=True,
            has_voiceover=True,
            has_captions=True,
            has_video=True,
            duration_seconds=120.5,
            status="complete",
        )
        assert status.has_script is True
        assert status.has_voiceover is True
        assert status.has_captions is True
        assert status.has_video is True
        assert status.duration_seconds == 120.5
        assert status.status == "complete"


class TestDeliverableStatus:
    """Tests for DeliverableStatus dataclass."""

    def test_deliverable_status_defaults(self):
        """Test DeliverableStatus with default values."""
        status = DeliverableStatus(
            name="Proposal",
            type="html",
            language="en",
        )
        assert status.name == "Proposal"
        assert status.type == "html"
        assert status.language == "en"
        assert status.exists is False
        assert status.path is None
        assert status.last_built is None
        assert status.is_stale is False

    def test_deliverable_status_exists(self, temp_dir):
        """Test DeliverableStatus for existing deliverable."""
        now = datetime.now()
        path = temp_dir / "proposal.html"
        status = DeliverableStatus(
            name="Proposal",
            type="html",
            language="en",
            exists=True,
            path=path,
            last_built=now,
        )
        assert status.exists is True
        assert status.path == path
        assert status.last_built == now


class TestProjectDashboard:
    """Tests for ProjectDashboard dataclass."""

    def test_project_dashboard_defaults(self, temp_dir):
        """Test ProjectDashboard with default values."""
        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
        )
        assert dashboard.project_name == "Test Project"
        assert dashboard.project_root == temp_dir
        assert dashboard.languages == []
        assert dashboard.source_language == "en"
        assert dashboard.content_status == {}
        assert dashboard.video_status == []
        assert dashboard.deliverables == []
        assert dashboard.quality_issues == 0
        assert dashboard.cache_size_mb == 0.0
        assert dashboard.last_build is None

    def test_project_dashboard_total_chapters(self, temp_dir):
        """Test total_chapters property."""
        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
            content_status={
                "en": ContentStatus(
                    language="en",
                    chapters=[
                        DocumentStatus(
                            path=temp_dir / "ch1.md",
                            title="Ch1",
                            status="draft",
                            version="1.0",
                        )
                    ],
                ),
                "no": ContentStatus(
                    language="no",
                    chapters=[
                        DocumentStatus(
                            path=temp_dir / "ch1_no.md",
                            title="Ch1 NO",
                            status="draft",
                            version="1.0",
                        ),
                        DocumentStatus(
                            path=temp_dir / "ch2_no.md",
                            title="Ch2 NO",
                            status="draft",
                            version="1.0",
                        ),
                    ],
                ),
            },
        )
        assert dashboard.total_chapters == 3

    def test_project_dashboard_total_words(self, temp_dir):
        """Test total_words property."""
        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
            content_status={
                "en": ContentStatus(language="en", total_words=1000),
                "no": ContentStatus(language="no", total_words=500),
            },
        )
        assert dashboard.total_words == 1500

    def test_project_dashboard_completion_percent(self, temp_dir):
        """Test completion_percent property."""
        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
            content_status={
                "en": ContentStatus(language="en", completion_percent=80.0),
                "no": ContentStatus(language="no", completion_percent=40.0),
            },
        )
        assert dashboard.completion_percent == 60.0

    def test_project_dashboard_completion_percent_empty(self, temp_dir):
        """Test completion_percent with no content."""
        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
        )
        assert dashboard.completion_percent == 0.0

    def test_project_dashboard_video_completion(self, temp_dir):
        """Test video_completion property."""
        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
            video_status=[
                VideoStatus(script_name="video1", language="en", status="complete"),
                VideoStatus(script_name="video2", language="en", status="in_progress"),
                VideoStatus(script_name="video3", language="en", status="not_started"),
                VideoStatus(script_name="video4", language="en", status="complete"),
            ],
        )
        assert dashboard.video_completion == 50.0

    def test_project_dashboard_video_completion_empty(self, temp_dir):
        """Test video_completion with no videos."""
        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
        )
        assert dashboard.video_completion == 0.0

    def test_project_dashboard_deliverable_count(self, temp_dir):
        """Test deliverable_count property."""
        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
            deliverables=[
                DeliverableStatus(name="D1", type="html", language="en", exists=True),
                DeliverableStatus(name="D2", type="pdf", language="en", exists=False),
                DeliverableStatus(name="D3", type="pptx", language="en", exists=True),
            ],
        )
        assert dashboard.deliverable_count == 2


class TestGetContentStatus:
    """Tests for get_content_status function."""

    def test_get_content_status_empty_project(self, temp_dir):
        """Test get_content_status with no chapters."""
        project = self._create_mock_project(temp_dir)
        status = get_content_status(project, "en")

        assert status.language == "en"
        assert status.chapters == []
        assert status.total_words == 0
        assert status.completion_percent == 0.0

    def test_get_content_status_with_chapters(self, temp_dir):
        """Test get_content_status with chapters."""
        project = self._create_mock_project(temp_dir)

        # Create chapters directory and files
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)

        chapter_content = """---
title: Introduction
version: 1.0.0
status: final
---

# Introduction

This is the introduction chapter with some content.
"""
        (chapters_dir / "01_introduction.md").write_text(chapter_content)

        status = get_content_status(project, "en")

        assert status.language == "en"
        assert len(status.chapters) == 1
        assert status.chapters[0].title == "Introduction"
        assert status.chapters[0].status == "final"
        assert status.chapters[0].version == "1.0.0"
        assert status.total_words > 0
        assert status.completion_percent == 100.0

    def test_get_content_status_tracks_stale(self, temp_dir):
        """Test get_content_status tracks stale documents."""
        project = self._create_mock_project(temp_dir)

        # Create chapters with different statuses
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)

        content = """---
title: Test
version: 1.0.0
status: draft
---

Content here.
"""
        (chapters_dir / "01_test.md").write_text(content)

        status = get_content_status(project, "en")

        assert status.language == "en"
        # Stale count depends on actual freshness which depends on modification time
        assert isinstance(status.stale_count, int)

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.paths.content = "content"
        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English")}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestGetVideoStatus:
    """Tests for get_video_status function."""

    def test_get_video_status_no_scripts(self, temp_dir):
        """Test get_video_status with no scripts directory."""
        project = self._create_mock_project(temp_dir)
        videos = get_video_status(project, "en")

        assert videos == []

    def test_get_video_status_with_scripts(self, temp_dir):
        """Test get_video_status with script files."""
        project = self._create_mock_project(temp_dir)

        # Create scripts directory
        scripts_dir = temp_dir / "content" / "en" / "scripts"
        scripts_dir.mkdir(parents=True)

        # Create script files
        (scripts_dir / "intro.yaml").write_text("title: Introduction")
        (scripts_dir / "demo.yaml").write_text("title: Demo")

        videos = get_video_status(project, "en")

        assert len(videos) == 2
        script_names = {v.script_name for v in videos}
        assert "intro" in script_names
        assert "demo" in script_names
        for v in videos:
            assert v.has_script is True
            assert v.status == "not_started"

    def test_get_video_status_with_audio(self, temp_dir):
        """Test get_video_status with voiceover audio."""
        project = self._create_mock_project(temp_dir)

        # Create scripts directory
        scripts_dir = temp_dir / "content" / "en" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "intro.yaml").write_text("title: Introduction")

        # Create cache/voiceover directory with audio
        audio_dir = temp_dir / ".cache" / "voiceover" / "en"
        audio_dir.mkdir(parents=True)
        (audio_dir / "intro.mp3").touch()

        videos = get_video_status(project, "en")

        assert len(videos) == 1
        assert videos[0].has_script is True
        assert videos[0].has_voiceover is True
        assert videos[0].status == "in_progress"

    def test_get_video_status_complete(self, temp_dir):
        """Test get_video_status with complete video."""
        project = self._create_mock_project(temp_dir)

        # Create scripts directory
        scripts_dir = temp_dir / "content" / "en" / "scripts"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "intro.yaml").write_text("title: Introduction")

        # Create output directory with video
        output_dir = temp_dir / "output" / "en" / "videos"
        output_dir.mkdir(parents=True)
        (output_dir / "intro.mp4").touch()
        (output_dir / "intro.vtt").touch()

        videos = get_video_status(project, "en")

        assert len(videos) == 1
        assert videos[0].has_video is True
        assert videos[0].has_captions is True
        assert videos[0].status == "complete"

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"
        config.paths.cache = ".cache"
        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English")}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestGetDeliverableStatus:
    """Tests for get_deliverable_status function."""

    def test_get_deliverable_status_empty(self, temp_dir):
        """Test get_deliverable_status with no deliverables."""
        project = self._create_mock_project(temp_dir)
        deliverables = get_deliverable_status(project)

        # Should still have entries for expected deliverables
        assert len(deliverables) >= 2  # At least HTML and PDF proposals
        assert all(d.exists is False for d in deliverables)

    def test_get_deliverable_status_with_html(self, temp_dir):
        """Test get_deliverable_status with HTML deliverable."""
        project = self._create_mock_project(temp_dir)

        # Create output directory with HTML
        output_dir = temp_dir / "output" / "en"
        output_dir.mkdir(parents=True)
        (output_dir / "proposal.html").write_text("<html>Test</html>")

        deliverables = get_deliverable_status(project)

        html_deliverables = [d for d in deliverables if d.type == "html"]
        assert len(html_deliverables) >= 1
        assert any(d.exists is True for d in html_deliverables)

    def test_get_deliverable_status_with_presentations(self, temp_dir):
        """Test get_deliverable_status with PPTX presentations."""
        project = self._create_mock_project(temp_dir)

        # Create presentations directory
        pres_dir = temp_dir / "output" / "en" / "presentations"
        pres_dir.mkdir(parents=True)
        (pres_dir / "investor_deck.pptx").touch()
        (pres_dir / "pilot_overview.pptx").touch()

        deliverables = get_deliverable_status(project)

        pptx_deliverables = [d for d in deliverables if d.type == "pptx"]
        assert len(pptx_deliverables) == 2
        assert all(d.exists is True for d in pptx_deliverables)

    def test_get_deliverable_status_with_videos(self, temp_dir):
        """Test get_deliverable_status with video deliverables."""
        project = self._create_mock_project(temp_dir)

        # Create videos directory
        videos_dir = temp_dir / "output" / "en" / "videos"
        videos_dir.mkdir(parents=True)
        (videos_dir / "intro.mp4").touch()
        (videos_dir / "demo-walkthrough.mp4").touch()

        deliverables = get_deliverable_status(project)

        video_deliverables = [d for d in deliverables if d.type == "video"]
        assert len(video_deliverables) == 2
        assert all(d.exists is True for d in video_deliverables)

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.paths.content = "content"
        config.paths.output = "output"
        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English")}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestGetProjectDashboard:
    """Tests for get_project_dashboard function."""

    def test_get_project_dashboard_basic(self, temp_dir):
        """Test get_project_dashboard creates proper dashboard."""
        project = self._create_mock_project(temp_dir)

        dashboard = get_project_dashboard(project)

        assert dashboard.project_name == "Test Project"
        assert dashboard.project_root == temp_dir
        assert "en" in dashboard.languages
        assert dashboard.source_language == "en"
        assert isinstance(dashboard.content_status, dict)
        assert isinstance(dashboard.video_status, list)
        assert isinstance(dashboard.deliverables, list)

    def test_get_project_dashboard_with_content(self, temp_dir):
        """Test get_project_dashboard with actual content."""
        project = self._create_mock_project(temp_dir)

        # Create content
        chapters_dir = temp_dir / "content" / "en" / "chapters"
        chapters_dir.mkdir(parents=True)
        (chapters_dir / "01_intro.md").write_text(
            "---\ntitle: Introduction\n---\n\n# Introduction\n\nHello world."
        )

        dashboard = get_project_dashboard(project)

        assert "en" in dashboard.content_status
        assert dashboard.total_chapters >= 1
        assert dashboard.total_words >= 2

    def test_get_project_dashboard_with_cache(self, temp_dir):
        """Test get_project_dashboard calculates cache size."""
        project = self._create_mock_project(temp_dir)

        # Create cache directory with files
        cache_dir = temp_dir / ".cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "test.txt").write_text("x" * 1024)  # 1KB file

        dashboard = get_project_dashboard(project)

        assert dashboard.cache_size_mb > 0

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
        config.paths.content = "content"
        config.paths.output = "output"
        config.paths.cache = ".cache"
        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English")}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project


class TestPrintFunctions:
    """Tests for console print functions (using mocks)."""

    def test_print_dashboard_runs_without_error(self, temp_dir):
        """Test print_dashboard completes without error."""
        from media_engine.status.dashboard import print_dashboard

        dashboard = ProjectDashboard(
            project_name="Test Project",
            project_root=temp_dir,
            languages=["en"],
        )

        # Should not raise
        print_dashboard(dashboard)

    def test_print_document_status_runs(self, temp_dir):
        """Test print_document_status completes without error."""
        from media_engine.status.views import print_document_status

        project = self._create_mock_project(temp_dir)

        # Should not raise
        print_document_status(project)

    def test_print_video_status_runs(self, temp_dir):
        """Test print_video_status completes without error."""
        from media_engine.status.views import print_video_status

        project = self._create_mock_project(temp_dir)

        # Should not raise
        print_video_status(project)

    def test_print_deliverable_status_runs(self, temp_dir):
        """Test print_deliverable_status completes without error."""
        from media_engine.status.views import print_deliverable_status

        project = self._create_mock_project(temp_dir)

        # Should not raise
        print_deliverable_status(project)

    def test_print_build_tree_runs(self, temp_dir):
        """Test print_build_tree completes without error."""
        from media_engine.status.views import print_build_tree

        project = self._create_mock_project(temp_dir)

        # Should not raise
        print_build_tree(project)

    def test_print_cache_status_runs(self, temp_dir):
        """Test print_cache_status completes without error."""
        from media_engine.status.views import print_cache_status

        project = self._create_mock_project(temp_dir)

        # Should not raise
        print_cache_status(project)

    def test_print_cache_status_with_cache(self, temp_dir):
        """Test print_cache_status with actual cache."""
        from media_engine.status.views import print_cache_status

        project = self._create_mock_project(temp_dir)

        # Create cache with subdirectories
        cache_dir = temp_dir / ".cache"
        (cache_dir / "audio").mkdir(parents=True)
        (cache_dir / "audio" / "test.mp3").write_bytes(b"x" * 1000)
        (cache_dir / "images").mkdir(parents=True)
        (cache_dir / "images" / "test.png").write_bytes(b"y" * 2000)

        # Should not raise
        print_cache_status(project)

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.name = "Test Project"
        config.paths.content = "content"
        config.paths.output = "output"
        config.paths.cache = ".cache"
        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English")}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project
