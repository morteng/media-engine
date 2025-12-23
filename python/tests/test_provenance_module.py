"""Tests for provenance module."""

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for provenance testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (tmp_path / ".media-engine").mkdir()

    # Create project.yaml
    project_config = {
        "name": "Provenance Test Project",
        "languages": ["en"],
        "paths": {
            "content": "content",
            "assets": "assets",
            "output": "dist",
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(project_config))

    # Create sample document
    doc1 = content_dir / "en" / "chapters" / "01_intro.md"
    doc1.write_text("""---
title: Introduction
status: draft
version: 1.0.0
---

# Introduction

This is the introduction chapter.
""")

    return tmp_path


@pytest.fixture
def project(sample_project):
    """Load the sample project."""
    from media_engine.core.project import Project

    return Project.load(sample_project)


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_approval_status_import(self):
        """Test ApprovalStatus can be imported."""
        from media_engine.provenance import ApprovalStatus

        assert ApprovalStatus is not None

    def test_approval_status_values(self):
        """Test ApprovalStatus enum values."""
        from media_engine.provenance import ApprovalStatus

        assert ApprovalStatus.DRAFT is not None
        assert ApprovalStatus.IN_REVIEW is not None
        assert ApprovalStatus.APPROVED is not None
        assert ApprovalStatus.PUBLISHED is not None

    def test_approval_status_string_values(self):
        """Test ApprovalStatus string values."""
        from media_engine.provenance import ApprovalStatus

        assert ApprovalStatus.DRAFT.value == "draft"
        assert ApprovalStatus.IN_REVIEW.value == "in_review"


class TestClaimStatus:
    """Tests for ClaimStatus enum."""

    def test_claim_status_import(self):
        """Test ClaimStatus can be imported."""
        from media_engine.provenance import ClaimStatus

        assert ClaimStatus is not None

    def test_claim_status_values(self):
        """Test ClaimStatus enum values."""
        from media_engine.provenance import ClaimStatus

        assert ClaimStatus.UNVERIFIED is not None
        assert ClaimStatus.VERIFIED is not None
        assert ClaimStatus.EXPIRED is not None


class TestClaim:
    """Tests for Claim dataclass."""

    def test_claim_import(self):
        """Test Claim can be imported."""
        from media_engine.provenance import Claim

        assert Claim is not None

    def test_claim_creation(self):
        """Test Claim creation."""
        from media_engine.provenance import Claim

        claim = Claim(
            claim_id="claim-1",
            text="This is a factual claim.",
            source="Internal documentation",
            source_url="https://example.com/source",
        )

        assert claim.claim_id == "claim-1"
        assert claim.text == "This is a factual claim."
        assert claim.source == "Internal documentation"


class TestProvenanceTracker:
    """Tests for ProvenanceTracker."""

    def test_provenance_tracker_import(self):
        """Test ProvenanceTracker can be imported."""
        from media_engine.provenance import ProvenanceTracker

        assert ProvenanceTracker is not None

    def test_provenance_tracker_init(self, project):
        """Test ProvenanceTracker initialization."""
        from media_engine.provenance import ProvenanceTracker

        tracker = ProvenanceTracker(project)
        assert tracker is not None

    def test_tracker_methods(self, project):
        """Test ProvenanceTracker has expected methods."""
        from media_engine.provenance import ProvenanceTracker

        tracker = ProvenanceTracker(project)

        # Check it has expected attributes
        assert hasattr(tracker, "project")
        assert tracker.project == project


class TestProvenanceModule:
    """General tests for provenance module."""

    def test_provenance_exports(self):
        """Test provenance module exports."""
        from media_engine import provenance

        assert hasattr(provenance, "ApprovalStatus")
        assert hasattr(provenance, "ClaimStatus")
        assert hasattr(provenance, "Claim")
        assert hasattr(provenance, "ProvenanceTracker")
