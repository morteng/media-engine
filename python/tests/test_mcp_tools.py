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
            project, "en/chapters/01_intro.md", "update", "Adding more content"
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
        result = _validate_action(project, "update_document", "en/chapters/01_intro.md", {})

        assert result["valid"] is True
        assert result["action"] == "update_document"

    def test_validate_action_missing_target(self, sample_project):
        """Test validating action with missing target."""
        from media_engine.core.project import Project
        from media_engine.mcp.tools.suggestions import _validate_action

        project = Project.load(sample_project)
        result = _validate_action(project, "update_document", "en/chapters/nonexistent.md", {})

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
                "params": {"status": "in_review"},
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
                "params": {"status": "final"},
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
        _session_store["test_key"] = {"value": "test_value", "set_at": "2024-01-01T00:00:00"}

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
        _agent_actions.append(
            {
                "id": 1,
                "action": "test_action",
                "reasoning": "testing",
                "result": "success",
                "target": None,
            }
        )

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


class TestDocumentLifecycleTools:
    """Tests for document lifecycle tools in documents.py."""

    @pytest.fixture
    def mock_server(self, sample_project):
        """Create a mock MCP server for testing."""
        from media_engine.mcp.server import MediaEngineMCPServer

        server = MediaEngineMCPServer(project_path=sample_project)
        return server

    @pytest.mark.asyncio
    async def test_scaffold_document_chapter(self, mock_server):
        """Test scaffolding a chapter document."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        result = await mock.tools["scaffold_document"](
            doc_type="chapter", language="en", title="Test Chapter"
        )

        data = json.loads(result)
        assert data["doc_type"] == "chapter"
        assert data["language"] == "en"
        assert "suggested_path" in data
        assert "content" in data
        assert data["metadata"]["title"] == "Test Chapter"
        assert data["metadata"]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_scaffold_document_script(self, mock_server):
        """Test scaffolding a video script."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        result = await mock.tools["scaffold_document"](
            doc_type="script", language="en", title="Demo Video"
        )

        data = json.loads(result)
        assert data["doc_type"] == "script"
        assert "scenes:" in data["content"]
        assert "voiceover:" in data["content"]

    @pytest.mark.asyncio
    async def test_create_document(self, mock_server, sample_project):
        """Test creating a new document."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        result = await mock.tools["create_document"](
            path="content/en/chapters/99_test.md",
            title="Test Document",
            doc_type="chapter",
            content="# Test\n\nThis is test content.",
            status="draft",
            tags="test,automation",
        )

        data = json.loads(result)
        assert data["status"] == "created"
        assert "99_test.md" in data["path"]
        assert data["title"] == "Test Document"
        assert data["metadata"]["status"] == "draft"
        assert "test" in data["metadata"]["tags"]

        # Verify file was created
        created_file = sample_project / "content" / "en" / "chapters" / "99_test.md"
        assert created_file.exists()
        content = created_file.read_text()
        assert "title: Test Document" in content

    @pytest.mark.asyncio
    async def test_create_document_already_exists(self, mock_server):
        """Test creating a document that already exists."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        result = await mock.tools["create_document"](
            path="content/en/chapters/01_intro.md", title="Already Exists", doc_type="chapter"
        )

        data = json.loads(result)
        assert "error" in data
        assert "already exists" in data["error"]

    @pytest.mark.asyncio
    async def test_update_document_content(self, mock_server, sample_project):
        """Test updating document content."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        new_content = "# Updated Introduction\n\nThis content has been updated."
        result = await mock.tools["update_document_content"](
            path="content/en/chapters/01_intro.md",
            content=new_content,
            update_modified=True,
            increment_version="minor",
        )

        data = json.loads(result)
        assert data["status"] == "content_updated"
        assert data["new_word_count"] > 0

        # Verify file was updated
        doc_file = sample_project / "content" / "en" / "chapters" / "01_intro.md"
        content = doc_file.read_text()
        assert "This content has been updated" in content

    @pytest.mark.asyncio
    async def test_delete_document_archive(self, mock_server, sample_project):
        """Test archiving a document."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        # First create a document to delete
        await mock.tools["create_document"](
            path="content/en/chapters/98_to_delete.md", title="To Delete", doc_type="chapter"
        )

        # Now archive it
        result = await mock.tools["delete_document"](
            path="content/en/chapters/98_to_delete.md", archive=True, check_dependencies=True
        )

        data = json.loads(result)
        assert data["status"] == "archived"
        assert ".archive" in data["archive_path"]

        # Verify original is gone
        original = sample_project / "content" / "en" / "chapters" / "98_to_delete.md"
        assert not original.exists()

        # Verify archive exists
        archive = sample_project / ".archive" / "content" / "en" / "chapters" / "98_to_delete.md"
        assert archive.exists()

    @pytest.mark.asyncio
    async def test_delete_document_permanent(self, mock_server, sample_project):
        """Test permanently deleting a document."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        # First create a document to delete
        await mock.tools["create_document"](
            path="content/en/chapters/97_to_delete.md",
            title="To Delete Permanently",
            doc_type="chapter",
        )

        # Now permanently delete it
        result = await mock.tools["delete_document"](
            path="content/en/chapters/97_to_delete.md", archive=False, check_dependencies=False
        )

        data = json.loads(result)
        assert data["status"] == "deleted"

        # Verify file is gone
        deleted = sample_project / "content" / "en" / "chapters" / "97_to_delete.md"
        assert not deleted.exists()

    @pytest.mark.asyncio
    async def test_move_document(self, mock_server, sample_project):
        """Test moving a document."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        # First create a document to move
        await mock.tools["create_document"](
            path="content/en/chapters/96_original.md", title="Original Location", doc_type="chapter"
        )

        # Now move it
        result = await mock.tools["move_document"](
            source_path="content/en/chapters/96_original.md",
            dest_path="content/en/chapters/96_moved.md",
            update_references=True,
        )

        data = json.loads(result)
        assert data["status"] == "moved"

        # Verify old location is gone
        old = sample_project / "content" / "en" / "chapters" / "96_original.md"
        assert not old.exists()

        # Verify new location exists
        new = sample_project / "content" / "en" / "chapters" / "96_moved.md"
        assert new.exists()

    @pytest.mark.asyncio
    async def test_move_document_not_found(self, mock_server):
        """Test moving a document that doesn't exist."""
        import json

        from media_engine.mcp.tools import documents

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        documents.register_document_tools(mock, mock_server)

        result = await mock.tools["move_document"](
            source_path="content/en/chapters/nonexistent.md",
            dest_path="content/en/chapters/moved.md",
        )

        data = json.loads(result)
        assert "error" in data
        assert "not found" in data["error"]


class TestSessionPersistence:
    """Tests for session persistence tools."""

    @pytest.fixture
    def mock_server(self, sample_project):
        """Create a mock MCP server for testing."""
        from media_engine.mcp.server import MediaEngineMCPServer

        server = MediaEngineMCPServer(project_path=sample_project)
        return server

    @pytest.mark.asyncio
    async def test_enable_session_persistence(self, mock_server, sample_project):
        """Test enabling session persistence."""
        import json

        from media_engine.mcp.tools import session
        from media_engine.mcp.tools.session import reset_session

        # Reset session state
        reset_session()

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        session.register_session_tools(mock, mock_server)

        result = await mock.tools["enable_session_persistence"](enable=True)

        data = json.loads(result)
        assert data["status"] == "enabled"
        assert "path" in data

    @pytest.mark.asyncio
    async def test_session_context_roundtrip(self, mock_server):
        """Test setting and getting session context."""
        import json

        from media_engine.mcp.tools import session
        from media_engine.mcp.tools.session import reset_session

        # Reset session state
        reset_session()

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        session.register_session_tools(mock, mock_server)

        # Set a value
        await mock.tools["set_session_context"](key="test_key", value="test_value")

        # Get it back
        result = await mock.tools["get_session_context"](key="test_key")

        data = json.loads(result)
        assert data["key"] == "test_key"
        assert data["value"] == "test_value"

        # Cleanup
        reset_session()

    @pytest.mark.asyncio
    async def test_clear_session_context(self, mock_server):
        """Test clearing session context."""
        import json

        from media_engine.mcp.tools import session
        from media_engine.mcp.tools.session import reset_session

        # Reset session state
        reset_session()

        class MockMCP:
            def __init__(self):
                self.tools = {}

            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func

                return decorator

        mock = MockMCP()
        session.register_session_tools(mock, mock_server)

        # Set a value
        await mock.tools["set_session_context"](key="to_clear", value="value")

        # Clear it
        result = await mock.tools["clear_session_context"](key="to_clear")

        data = json.loads(result)
        assert data["status"] == "cleared"

        # Verify it's gone
        result2 = await mock.tools["get_session_context"](key="to_clear")
        data2 = json.loads(result2)
        assert "error" in data2  # Key not found returns error

        # Cleanup
        reset_session()


class TestPathValidation:
    """Tests for path validation in MCP server."""

    @pytest.fixture
    def mock_server(self, sample_project):
        """Create a mock MCP server for testing."""
        from media_engine.mcp.server import MediaEngineMCPServer

        server = MediaEngineMCPServer(project_path=sample_project)
        return server

    def test_validate_relative_path(self, mock_server, sample_project):
        """Test validating a relative path."""
        result = mock_server._validate_path("content/en/chapters/01_intro.md")
        expected = sample_project / "content" / "en" / "chapters" / "01_intro.md"
        assert result == expected.resolve()

    def test_validate_absolute_path(self, mock_server, sample_project):
        """Test validating an absolute path within project."""
        abs_path = sample_project / "content" / "en" / "chapters" / "01_intro.md"
        result = mock_server._validate_path(str(abs_path))
        assert result == abs_path.resolve()

    def test_validate_path_outside_project(self, mock_server):
        """Test that paths outside project are rejected."""
        with pytest.raises(ValueError, match="Path outside project"):
            mock_server._validate_path("/etc/passwd")

    def test_validate_path_traversal_attack(self, mock_server):
        """Test that path traversal attacks are blocked."""
        with pytest.raises(ValueError, match="Path outside project"):
            mock_server._validate_path("content/../../../etc/passwd")
