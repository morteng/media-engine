"""Tests for semantic module."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for semantic testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (tmp_path / ".media-engine").mkdir()

    # Create project.yaml
    project_config = {
        "name": "Semantic Test Project",
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
status: draft
---

# Introduction

This document introduces the main concepts of our system.
""")

    doc2 = content_dir / "en" / "chapters" / "02_api.md"
    doc2.write_text("""---
title: API Reference
status: draft
---

# API Reference

The API provides REST endpoints for authentication.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestSemanticMatch:
    """Tests for SemanticMatch dataclass."""

    def test_semantic_match_import(self):
        """Test SemanticMatch can be imported."""
        from media_engine.semantic import SemanticMatch

        assert SemanticMatch is not None

    def test_semantic_match_creation(self):
        """Test SemanticMatch creation."""
        from media_engine.semantic import SemanticMatch

        match = SemanticMatch(
            doc1=Path("doc1.md"),
            doc2=Path("doc2.md"),
            similarity=0.85,
            match_type="near_duplicate",
        )

        assert match.doc1 == Path("doc1.md")
        assert match.similarity == 0.85
        assert match.match_type == "near_duplicate"

    def test_semantic_match_to_dict(self):
        """Test SemanticMatch to_dict method."""
        from media_engine.semantic import SemanticMatch

        match = SemanticMatch(
            doc1=Path("doc1.md"),
            doc2=Path("doc2.md"),
            similarity=0.85,
            match_type="related",
        )

        d = match.to_dict()
        assert d["similarity"] == 0.85
        assert d["match_type"] == "related"


class TestTerminologyDrift:
    """Tests for TerminologyDrift dataclass."""

    def test_terminology_drift_import(self):
        """Test TerminologyDrift can be imported."""
        from media_engine.semantic import TerminologyDrift

        assert TerminologyDrift is not None


class TestSemanticAnalyzer:
    """Tests for SemanticAnalyzer."""

    def test_semantic_analyzer_import(self):
        """Test SemanticAnalyzer can be imported."""
        from media_engine.semantic import SemanticAnalyzer

        assert SemanticAnalyzer is not None

    def test_semantic_analyzer_init(self, project):
        """Test SemanticAnalyzer initialization."""
        from media_engine.semantic import SemanticAnalyzer

        analyzer = SemanticAnalyzer(project)
        assert analyzer is not None
        assert analyzer.project == project


class TestSemanticModule:
    """General tests for semantic module."""

    def test_semantic_exports(self):
        """Test semantic module exports."""
        from media_engine import semantic

        assert hasattr(semantic, "SemanticMatch")
        assert hasattr(semantic, "TerminologyDrift")
        assert hasattr(semantic, "SemanticAnalyzer")

    def test_text_similarity_calculation(self):
        """Test basic text similarity using Jaccard."""
        text1 = "the quick brown fox"
        text2 = "the quick brown dog"

        words1 = set(text1.split())
        words2 = set(text2.split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        similarity = intersection / union
        # "the", "quick", "brown" are shared (3 words)
        # Total unique words: the, quick, brown, fox, dog (5 words)
        # Similarity = 3/5 = 0.6
        assert 0.5 < similarity < 0.7
