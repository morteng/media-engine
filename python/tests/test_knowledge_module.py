"""Tests for knowledge module."""

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
        "name": "Knowledge Test",
        "languages": ["en"],
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
status: final
---

# Introduction

This chapter introduces the core concepts of the API.
""")

    doc2 = content_dir / "en" / "chapters" / "02_auth.md"
    doc2.write_text("""---
title: Authentication
status: final
---

# Authentication

This covers OAuth flows.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph."""

    def test_knowledge_graph_import(self):
        """Test KnowledgeGraph can be imported."""
        from media_engine.knowledge import KnowledgeGraph

        assert KnowledgeGraph is not None


class TestGraphNode:
    """Tests for GraphNode."""

    def test_graph_node_import(self):
        """Test GraphNode can be imported."""
        from media_engine.knowledge import GraphNode

        assert GraphNode is not None


class TestGraphEdge:
    """Tests for GraphEdge."""

    def test_graph_edge_import(self):
        """Test GraphEdge can be imported."""
        from media_engine.knowledge import GraphEdge

        assert GraphEdge is not None


class TestPrerequisiteIssue:
    """Tests for PrerequisiteIssue."""

    def test_prerequisite_issue_import(self):
        """Test PrerequisiteIssue can be imported."""
        from media_engine.knowledge import PrerequisiteIssue

        assert PrerequisiteIssue is not None


class TestConceptExtractor:
    """Tests for ConceptExtractor."""

    def test_extractor_import(self):
        """Test extractor can be imported."""
        from media_engine.knowledge import ConceptExtractor

        assert ConceptExtractor is not None


class TestBuildKnowledgeGraph:
    """Tests for build_knowledge_graph function."""

    def test_function_import(self):
        """Test function can be imported."""
        from media_engine.knowledge import build_knowledge_graph

        assert build_knowledge_graph is not None


class TestKnowledgeModuleExports:
    """Tests for knowledge module exports."""

    def test_module_exports(self):
        """Test all expected exports exist."""
        from media_engine import knowledge

        assert hasattr(knowledge, "KnowledgeGraph")
        assert hasattr(knowledge, "GraphNode")
        assert hasattr(knowledge, "GraphEdge")
        assert hasattr(knowledge, "PrerequisiteIssue")
        assert hasattr(knowledge, "build_knowledge_graph")
