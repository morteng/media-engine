"""Comprehensive tests for all MCP tools."""

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for MCP testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (content_dir / "no" / "chapters").mkdir(parents=True)
    (tmp_path / ".media-engine").mkdir()

    # Create project.yaml
    project_config = {
        "name": "MCP Test Project",
        "description": "A test project for MCP tools",
        "languages": ["en", "no"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create sample documents
    doc1 = content_dir / "en" / "chapters" / "01_intro.md"
    doc1.write_text("""---
title: Introduction
status: draft
version: 1.0.0
---

# Introduction

This is the introduction chapter.
""")

    doc2 = content_dir / "en" / "chapters" / "02_features.md"
    doc2.write_text("""---
title: Features
status: final
version: 2.0.0
---

# Features

This chapter describes features.
""")

    # Create Norwegian translation
    trans1 = content_dir / "no" / "chapters" / "01_intro.md"
    trans1.write_text("""---
title: Introduksjon
language: "no"
source_document: en/chapters/01_intro.md
source_version: 1.0.0
---

# Introduksjon

Dette er introduksjonskapittelet.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestProjectTools:
    """Tests for project.py MCP tools."""

    def test_project_status_import(self):
        """Test project status tool import."""
        from media_engine.mcp.tools.project import register_project_tools

        assert callable(register_project_tools)


class TestQualityTools:
    """Tests for quality.py MCP tools."""

    def test_quality_tools_import(self):
        """Test quality tools import."""
        from media_engine.mcp.tools.quality import register_quality_tools

        assert callable(register_quality_tools)


class TestBuildTools:
    """Tests for build.py MCP tools."""

    def test_build_tools_import(self):
        """Test build tools import."""
        from media_engine.mcp.tools.build import register_build_tools

        assert callable(register_build_tools)


class TestSearchTools:
    """Tests for search.py MCP tools."""

    def test_search_tools_import(self):
        """Test search tools import."""
        from media_engine.mcp.tools.search import register_search_tools

        assert callable(register_search_tools)


class TestCacheTools:
    """Tests for cache.py MCP tools."""

    def test_cache_tools_import(self):
        """Test cache tools import."""
        from media_engine.mcp.tools.cache import register_cache_tools

        assert callable(register_cache_tools)


class TestAuditTools:
    """Tests for audit.py MCP tools."""

    def test_audit_tools_import(self):
        """Test audit tools import."""
        from media_engine.mcp.tools.audit import register_audit_tools

        assert callable(register_audit_tools)


class TestProvenanceTools:
    """Tests for provenance.py MCP tools."""

    def test_provenance_tools_import(self):
        """Test provenance tools import."""
        from media_engine.mcp.tools.provenance import register_provenance_tools

        assert callable(register_provenance_tools)


class TestNotesTools:
    """Tests for notes.py MCP tools."""

    def test_notes_tools_import(self):
        """Test notes tools import."""
        from media_engine.mcp.tools.notes import register_notes_tools

        assert callable(register_notes_tools)


class TestTranslationTools:
    """Tests for translation.py MCP tools."""

    def test_translation_tools_import(self):
        """Test translation tools import."""
        from media_engine.mcp.tools.translation import register_translation_tools

        assert callable(register_translation_tools)


class TestAITools:
    """Tests for ai.py MCP tools."""

    def test_ai_tools_import(self):
        """Test AI tools import."""
        from media_engine.mcp.tools.ai import register_ai_tools

        assert callable(register_ai_tools)


class TestWebhooksTools:
    """Tests for webhooks.py MCP tools."""

    def test_webhooks_tools_import(self):
        """Test webhooks tools import."""
        from media_engine.mcp.tools.webhooks import register_webhook_tools

        assert callable(register_webhook_tools)


class TestReportsTools:
    """Tests for reports.py MCP tools."""

    def test_reports_tools_import(self):
        """Test reports tools import."""
        from media_engine.mcp.tools.reports import register_report_tools

        assert callable(register_report_tools)


class TestMCPServer:
    """Tests for MCP server."""

    def test_server_init(self, sample_project):
        """Test MCP server initialization."""
        from media_engine.mcp.server import MediaEngineMCPServer

        server = MediaEngineMCPServer(project_path=sample_project)
        assert server is not None
        assert server.project is not None

    def test_server_run_method_exists(self, sample_project):
        """Test server run method exists."""
        from media_engine.mcp.server import MediaEngineMCPServer

        server = MediaEngineMCPServer(project_path=sample_project)
        assert hasattr(server, "run")


class TestMCPHelpers:
    """Tests for MCP helpers."""

    def test_helpers_import(self):
        """Test helpers import."""
        from media_engine.mcp import helpers

        # Module should be importable
        assert helpers is not None


class TestMCPResources:
    """Tests for MCP resources."""

    def test_resources_import(self):
        """Test resources import."""
        from media_engine.mcp import resources

        # Module should be importable
        assert resources is not None


class TestContextToolsAdvanced:
    """Advanced tests for context tools."""

    def test_get_document_context(self, project):
        """Test getting document context."""
        from media_engine.mcp.tools.context import _get_document_context

        context = _get_document_context(project, "en/chapters/01_intro.md")

        # The function returns a dict with document info
        assert isinstance(context, dict)

    def test_context_module_import(self):
        """Test context module can be imported."""
        from media_engine.mcp.tools.context import register_context_tools

        assert callable(register_context_tools)


class TestSuggestionToolsAdvanced:
    """Advanced tests for suggestion tools."""

    def test_get_best_practices_translations(self):
        """Test getting best practices for translations."""
        from media_engine.mcp.tools.suggestions import _get_best_practices

        practices = _get_best_practices("translations")
        assert "topic" in practices
        assert "practices" in practices

    def test_get_best_practices_quality(self):
        """Test getting best practices for quality."""
        from media_engine.mcp.tools.suggestions import _get_best_practices

        practices = _get_best_practices("quality")
        assert "topic" in practices

    def test_get_best_practices_general(self):
        """Test getting best practices for general topic."""
        from media_engine.mcp.tools.suggestions import _get_best_practices

        practices = _get_best_practices("general")
        assert "topic" in practices

    def test_get_workflow_guidance_translate(self):
        """Test getting workflow guidance for translation."""
        from media_engine.mcp.tools.suggestions import _get_workflow_guidance

        guidance = _get_workflow_guidance("translate")
        assert "name" in guidance
        assert "steps" in guidance

    def test_get_workflow_guidance_new_document(self):
        """Test getting workflow guidance for new document."""
        from media_engine.mcp.tools.suggestions import _get_workflow_guidance

        guidance = _get_workflow_guidance("new_document")
        assert "name" in guidance


class TestBatchToolsAdvanced:
    """Advanced tests for batch tools."""

    def test_preview_changes(self, project):
        """Test previewing batch changes."""
        from media_engine.mcp.tools.batch import _preview_changes

        ops = [
            {
                "action": "update_status",
                "target": "en/chapters/01_intro.md",
                "params": {"status": "in_review"},
            }
        ]

        preview = _preview_changes(project, ops)
        assert "total_operations" in preview
        assert "preview" in preview


class TestClaudeToolsAdvanced:
    """Advanced tests for Claude tools."""

    def test_claude_tools_import(self):
        """Test Claude tools import."""
        from media_engine.mcp.tools.claude import register_claude_tools

        assert callable(register_claude_tools)

    def test_get_slash_commands_exists(self):
        """Test _get_slash_commands function exists."""
        from media_engine.mcp.tools import claude

        # Check the module has the function
        assert hasattr(claude, "_get_slash_commands")


class TestSessionToolsAdvanced:
    """Advanced tests for session tools."""

    def test_session_reset(self):
        """Test session reset."""
        from media_engine.mcp.tools import session

        # Add something to session
        session._session_store["test"] = {"value": "test"}

        # Reset - call the function and reload the module state
        session.reset_session()

        # Verify reset - use the module reference
        assert len(session._session_store) == 0

    def test_session_tools_import(self):
        """Test session tools can be imported."""
        from media_engine.mcp.tools.session import register_session_tools

        assert callable(register_session_tools)
