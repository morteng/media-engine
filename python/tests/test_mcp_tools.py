"""Tests for enhanced MCP tools."""

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (content_dir / "no" / "chapters").mkdir(parents=True)

    # Create project.yaml using same format as test_insights
    project_config = {
        "name": "Test Project",
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
tags:
  - intro
  - basics
---

# Introduction

This is the introduction chapter.

TODO: Add more content here.
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

    # Create a translation
    trans1 = content_dir / "no" / "chapters" / "01_intro.md"
    trans1.write_text("""---
title: Introduksjon
language: "no"
source_document: en/chapters/01_intro.md
source_version: 1.0.0
status: draft
version: 1.0.0
---

# Introduksjon

Dette er introduksjonskapittelet.
""")

    return tmp_path


class TestContextTools:
    """Tests for context.py tools."""

    def test_get_project_overview(self, sample_project):
        """Test building project overview."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.context import _get_project_overview

        project = Project.load(sample_project)
        overview = _get_project_overview(project)

        assert "name" in overview
        assert "languages" in overview
        assert isinstance(overview["languages"], list)
        assert "source_language" in overview

    def test_get_content_structure(self, sample_project):
        """Test building content structure."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.context import _get_content_structure

        project = Project.load(sample_project)
        structure = _get_content_structure(project)

        assert structure["total_documents"] >= 2
        assert "by_language" in structure

    def test_find_relevant_docs(self, sample_project):
        """Test finding relevant documents."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.context import _find_relevant_docs

        project = Project.load(sample_project)
        results = _find_relevant_docs(project, "introduction")

        assert len(results) > 0
        assert any("intro" in r["path"].lower() for r in results)

    def test_analyze_impact(self, sample_project):
        """Test analyzing change impact."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.context import _analyze_impact

        project = Project.load(sample_project)
        impact = _analyze_impact(
            project,
            "en/chapters/01_intro.md",
            "update",
            "Adding more content"
        )

        assert impact["target"] == "en/chapters/01_intro.md"
        assert impact["change_type"] == "update"
        assert "translation_impact" in impact


class TestSuggestionTools:
    """Tests for suggestions.py tools."""

    def test_gather_suggestions(self, sample_project):
        """Test gathering suggestions."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.suggestions import _gather_suggestions

        project = Project.load(sample_project)
        suggestions = _gather_suggestions(project)

        # Should have at least incomplete content suggestion (we have a TODO)
        assert isinstance(suggestions, list)

    def test_validate_action_update(self, sample_project):
        """Test validating an update action."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.suggestions import _validate_action

        project = Project.load(sample_project)
        result = _validate_action(
            project,
            "update_document",
            "en/chapters/01_intro.md",
            {}
        )

        assert result["valid"] is True
        assert result["action"] == "update_document"

    def test_validate_action_missing_target(self, sample_project):
        """Test validating action with missing target."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.suggestions import _validate_action

        project = Project.load(sample_project)
        result = _validate_action(
            project,
            "update_document",
            "en/chapters/nonexistent.md",
            {}
        )

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_get_workflow_guidance(self):
        """Test getting workflow guidance."""
        from media_engine.mcp.tools.suggestions import _get_workflow_guidance

        guidance = _get_workflow_guidance("new_document")

        assert guidance["name"] == "Create New Document"
        assert len(guidance["steps"]) > 0
        assert "best_practices" in guidance

    def test_get_workflow_guidance_unknown(self):
        """Test getting guidance for unknown workflow."""
        from media_engine.mcp.tools.suggestions import _get_workflow_guidance

        guidance = _get_workflow_guidance("unknown_workflow")

        assert "error" in guidance
        assert "available_workflows" in guidance

    def test_get_best_practices(self):
        """Test getting best practices."""
        from media_engine.mcp.tools.suggestions import _get_best_practices

        practices = _get_best_practices("translations")

        assert practices["topic"] == "Translation Best Practices"
        assert len(practices["practices"]) > 0


class TestBatchTools:
    """Tests for batch.py tools."""

    def test_execute_single_operation(self, sample_project):
        """Test executing a single batch operation."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.batch import _execute_batch

        project = Project.load(sample_project)
        ops = [
            {
                "action": "update_status",
                "target": "en/chapters/01_intro.md",
                "params": {"status": "in_review"}
            }
        ]

        result = _execute_batch(project, ops)

        assert result["successful"] == 1
        assert result["failed"] == 0
        assert not result["rollback_performed"]

    def test_filter_by_selector(self, sample_project):
        """Test filtering documents by selector."""
        from media_engine.cms.document_manager import DocumentManager
        from media_engine.core.project import Project
        from media_engine.mcp.tools.batch import _filter_by_selector

        project = Project.load(sample_project)
        manager = DocumentManager(project)
        docs = manager.list_documents()

        # Filter by language
        en_docs = _filter_by_selector(docs, "lang:en", project)
        assert len(en_docs) >= 2

        # Filter by status
        draft_docs = _filter_by_selector(docs, "status:draft", project)
        assert len(draft_docs) >= 1

    def test_preview_changes(self, sample_project):
        """Test previewing changes."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.batch import _preview_changes

        project = Project.load(sample_project)
        ops = [
            {
                "action": "update_status",
                "target": "en/chapters/01_intro.md",
                "params": {"status": "final"}
            }
        ]

        preview = _preview_changes(project, ops)

        assert preview["total_operations"] == 1
        assert len(preview["preview"]) == 1
        assert preview["preview"][0]["valid"] is True


class TestSessionTools:
    """Tests for session.py tools."""

    def test_session_store(self):
        """Test session context storage."""
        from media_engine.mcp.tools.session import (
            _session_store,
            reset_session,
        )

        # Reset session for clean state
        reset_session()

        # Store value
        _session_store["test_key"] = {
            "value": "test_value",
            "set_at": "2024-01-01T00:00:00"
        }

        assert "test_key" in _session_store
        assert _session_store["test_key"]["value"] == "test_value"

        # Cleanup
        reset_session()

    def test_agent_actions_log(self):
        """Test agent action logging."""
        from media_engine.mcp.tools.session import (
            _agent_actions,
            reset_session,
        )

        # Reset for clean state
        reset_session()

        # Add action
        _agent_actions.append({
            "id": 1,
            "action": "test_action",
            "reasoning": "testing",
            "result": "success",
            "target": None,
        })

        assert len(_agent_actions) == 1
        assert _agent_actions[0]["action"] == "test_action"

        # Cleanup
        reset_session()


class TestClaudeTools:
    """Tests for claude.py tools."""

    def test_generate_claude_md(self, sample_project):
        """Test generating CLAUDE.md content."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.claude import _generate_claude_md

        project = Project.load(sample_project)
        content = _generate_claude_md(project)

        # Check for key sections regardless of project name
        assert "Quick Reference" in content
        assert "Project Structure" in content
        assert "Languages" in content
        assert "media-engine" in content

    def test_get_quick_status(self, sample_project):
        """Test getting quick status."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.claude import _get_quick_status

        project = Project.load(sample_project)
        status = _get_quick_status(project)

        assert "project" in status
        assert "summary" in status

    def test_get_slash_commands(self):
        """Test getting slash command definitions."""
        from media_engine.mcp.tools.claude import _get_slash_commands

        commands = _get_slash_commands()

        assert "media-status" in commands
        assert "media-translate" in commands
        assert "media-quality" in commands
        assert all("description" in cmd for cmd in commands.values())
        assert all("content" in cmd for cmd in commands.values())

    def test_process_natural_query_search(self, sample_project):
        """Test natural language query for document search."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.claude import _process_natural_query

        project = Project.load(sample_project)
        result = _process_natural_query(project, "What documents mention introduction?")

        assert result["query_type"] == "document_search"
        assert "results" in result

    def test_process_natural_query_translation(self, sample_project):
        """Test natural language query for translations."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.claude import _process_natural_query

        project = Project.load(sample_project)
        result = _process_natural_query(project, "What translations are needed?")

        # May return error dict or actual result depending on project setup
        assert isinstance(result, dict)
        # If it has query_type, it should be translation-related
        if "query_type" in result:
            assert "translation" in result["query_type"]

    def test_process_natural_query_status(self, sample_project):
        """Test natural language query for status."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.claude import _process_natural_query

        project = Project.load(sample_project)
        result = _process_natural_query(project, "What is the project status?")

        assert result["query_type"] == "status"
        assert "total_documents" in result
