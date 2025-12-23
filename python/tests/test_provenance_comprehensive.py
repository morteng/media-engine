"""Comprehensive tests for provenance module."""

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
        "name": "Provenance Test",
        "languages": ["en"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create sample document
    doc = content_dir / "en" / "chapters" / "01_intro.md"
    doc.write_text("""---
title: Introduction
status: draft
version: 1.0.0
---

# Introduction

This document makes some claims:
- According to research, users prefer simplicity [1].
- Studies show increased productivity.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_approval_status_values(self):
        """Test all status values exist."""
        from media_engine.provenance import ApprovalStatus

        assert ApprovalStatus.DRAFT is not None
        assert ApprovalStatus.IN_REVIEW is not None
        assert ApprovalStatus.APPROVED is not None
        assert ApprovalStatus.PUBLISHED is not None

    def test_approval_status_string_values(self):
        """Test status string values."""
        from media_engine.provenance import ApprovalStatus

        assert ApprovalStatus.DRAFT.value == "draft"
        assert ApprovalStatus.IN_REVIEW.value == "in_review"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.PUBLISHED.value == "published"


class TestClaimStatus:
    """Tests for ClaimStatus enum."""

    def test_claim_status_values(self):
        """Test all claim status values."""
        from media_engine.provenance import ClaimStatus

        assert ClaimStatus.UNVERIFIED is not None
        assert ClaimStatus.VERIFIED is not None
        assert ClaimStatus.EXPIRED is not None


class TestClaim:
    """Tests for Claim dataclass."""

    def test_claim_creation(self):
        """Test creating a claim."""
        from media_engine.provenance import Claim

        claim = Claim(
            claim_id="claim-001",
            text="Users prefer simplicity.",
            source="User research study 2024",
            source_url="https://example.com/study",
        )

        assert claim.claim_id == "claim-001"
        assert claim.text == "Users prefer simplicity."
        assert claim.source == "User research study 2024"

    def test_claim_with_defaults(self):
        """Test claim with default values."""
        from media_engine.provenance import Claim

        claim = Claim(
            claim_id="claim-002",
            text="A factual claim.",
            source="Documentation",
        )

        assert claim.claim_id == "claim-002"
        assert claim.source == "Documentation"
        assert claim.source_url is None  # defaults to None


class TestProvenanceTracker:
    """Tests for ProvenanceTracker."""

    def test_tracker_creation(self, project):
        """Test creating a tracker."""
        from media_engine.provenance import ProvenanceTracker

        tracker = ProvenanceTracker(project)
        assert tracker is not None
        assert tracker.project == project

    def test_tracker_has_methods(self, project):
        """Test tracker has expected methods."""
        from media_engine.provenance import ProvenanceTracker

        tracker = ProvenanceTracker(project)

        # Check it has core methods
        assert hasattr(tracker, "project")


class TestProvenanceModuleExports:
    """Tests for provenance module exports."""

    def test_module_exports(self):
        """Test all expected exports exist."""
        from media_engine import provenance

        assert hasattr(provenance, "ApprovalStatus")
        assert hasattr(provenance, "ClaimStatus")
        assert hasattr(provenance, "Claim")
        assert hasattr(provenance, "ProvenanceTracker")
