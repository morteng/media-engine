"""
Tests for the integrity module (asset checksums and terminology).
"""

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from media_engine.integrity import (
    AssetChecksum,
    AssetIntegrityChecker,
    GlossaryTerm,
    TerminologyChecker,
    generate_full_integrity_report,
)


class TestAssetChecksum:
    """Test AssetChecksum dataclass."""

    def test_create_checksum(self):
        """Test creating an asset checksum record."""
        cs = AssetChecksum(
            path="assets/logo.png",
            checksum="abc123def456",
            algorithm="sha256",
            size_bytes=1024,
            recorded_at="2024-01-15T10:00:00",
            recorded_by="admin",
        )

        assert cs.path == "assets/logo.png"
        assert cs.checksum == "abc123def456"
        assert cs.algorithm == "sha256"
        assert cs.size_bytes == 1024
        assert cs.recorded_by == "admin"

    def test_default_values(self):
        """Test default values for optional fields."""
        cs = AssetChecksum(
            path="assets/image.jpg",
            checksum="xyz789",
        )

        assert cs.algorithm == "sha256"
        assert cs.size_bytes == 0
        assert cs.recorded_at == ""
        assert cs.recorded_by is None


class TestAssetIntegrityChecker:
    """Test AssetIntegrityChecker class."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project for testing."""
        project = MagicMock()
        project.root = temp_dir
        project.assets_dir = temp_dir / "assets"
        project.assets_dir.mkdir(parents=True, exist_ok=True)
        return project

    @pytest.fixture
    def checker(self, mock_project):
        """Create an asset integrity checker."""
        return AssetIntegrityChecker(mock_project)

    def test_init_creates_data_dir(self, mock_project, temp_dir):
        """Test that checker initializes correctly."""
        checker = AssetIntegrityChecker(mock_project)
        assert checker.data_dir == temp_dir / ".media-engine"

    def test_compute_checksum(self, checker, temp_dir):
        """Test computing file checksum."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = checker.compute_checksum(test_file)

        # Verify it's a valid SHA256 hash
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

        # Verify it's deterministic
        checksum2 = checker.compute_checksum(test_file)
        assert checksum == checksum2

    def test_compute_checksum_binary(self, checker, temp_dir):
        """Test computing checksum for binary file."""
        test_file = temp_dir / "test.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

        checksum = checker.compute_checksum(test_file)
        assert len(checksum) == 64

    def test_record_asset(self, checker, mock_project, temp_dir):
        """Test recording an asset checksum."""
        # Create test asset
        asset = temp_dir / "assets" / "logo.png"
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"PNG image data")

        result = checker.record_asset(asset, recorded_by="tester")

        assert result is not None
        assert result.path == "assets/logo.png"
        assert result.recorded_by == "tester"
        assert result.size_bytes > 0

    def test_record_asset_nonexistent(self, checker, temp_dir):
        """Test recording a nonexistent asset returns None."""
        result = checker.record_asset(temp_dir / "nonexistent.png")
        assert result is None

    def test_record_asset_saves_to_disk(self, checker, mock_project, temp_dir):
        """Test that recorded assets are persisted."""
        asset = temp_dir / "assets" / "test.png"
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"test data")

        checker.record_asset(asset)

        # Check that data file exists
        data_path = temp_dir / ".media-engine" / "asset_checksums.json"
        assert data_path.exists()

        # Verify content
        data = json.loads(data_path.read_text())
        assert "assets/test.png" in data

    def test_verify_asset_valid(self, checker, temp_dir):
        """Test verifying an unchanged asset."""
        # Create and record asset
        asset = temp_dir / "assets" / "image.png"
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"image content")

        checker.record_asset(asset)

        # Verify
        result = checker.verify_asset(asset)
        assert result["status"] == "valid"
        assert "checksum" in result

    def test_verify_asset_modified(self, checker, temp_dir):
        """Test detecting modified asset."""
        # Create and record asset
        asset = temp_dir / "assets" / "doc.pdf"
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"original content")

        checker.record_asset(asset)

        # Modify asset
        asset.write_bytes(b"modified content")

        # Verify
        result = checker.verify_asset(asset)
        assert result["status"] == "modified"
        assert "expected_checksum" in result
        assert "current_checksum" in result
        assert result["expected_checksum"] != result["current_checksum"]

    def test_verify_asset_missing(self, checker, temp_dir):
        """Test detecting missing asset."""
        # Create and record asset
        asset = temp_dir / "assets" / "temp.png"
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"temporary")

        checker.record_asset(asset)

        # Delete asset
        asset.unlink()

        # Verify
        result = checker.verify_asset(asset)
        assert result["status"] == "missing"
        assert "expected_checksum" in result

    def test_verify_asset_untracked(self, checker, temp_dir):
        """Test detecting untracked asset."""
        asset = temp_dir / "assets" / "new.png"
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(b"new file")

        # Don't record it - verify as untracked
        result = checker.verify_asset(asset)
        assert result["status"] == "untracked"

    def test_verify_all(self, checker, temp_dir):
        """Test verifying all assets."""
        # Create multiple assets
        (temp_dir / "assets").mkdir(parents=True, exist_ok=True)

        valid_asset = temp_dir / "assets" / "valid.png"
        valid_asset.write_bytes(b"valid")
        checker.record_asset(valid_asset)

        modified_asset = temp_dir / "assets" / "modified.png"
        modified_asset.write_bytes(b"original")
        checker.record_asset(modified_asset)
        modified_asset.write_bytes(b"changed")

        # Verify all
        results = checker.verify_all()

        assert len(results["valid"]) == 1
        assert len(results["modified"]) == 1

    def test_record_all(self, checker, temp_dir):
        """Test recording all assets."""
        # Create multiple assets
        (temp_dir / "assets").mkdir(parents=True, exist_ok=True)

        for name in ["a.png", "b.jpg", "c.svg"]:
            (temp_dir / "assets" / name).write_bytes(b"content")

        count = checker.record_all(recorded_by="batch")
        assert count >= 3

    def test_generate_report(self, checker, temp_dir):
        """Test generating integrity report."""
        # Create and record an asset
        (temp_dir / "assets").mkdir(parents=True, exist_ok=True)
        asset = temp_dir / "assets" / "test.png"
        asset.write_bytes(b"test")
        checker.record_asset(asset)

        report = checker.generate_report()

        assert "summary" in report
        assert "issues" in report
        assert "total_tracked" in report["summary"]

    def test_load_existing_data(self, mock_project, temp_dir):
        """Test loading existing checksum data."""
        # Create data file
        data_dir = temp_dir / ".media-engine"
        data_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "assets/existing.png": {
                "checksum": "abc123",
                "algorithm": "sha256",
                "size_bytes": 1000,
                "recorded_at": "2024-01-01",
                "recorded_by": "user",
            }
        }
        (data_dir / "asset_checksums.json").write_text(json.dumps(data))

        # Create new checker - should load data
        checker = AssetIntegrityChecker(mock_project)

        assert "assets/existing.png" in checker._checksums


class TestGlossaryTerm:
    """Test GlossaryTerm dataclass."""

    def test_create_term(self):
        """Test creating a glossary term."""
        term = GlossaryTerm(
            term="API",
            definition="Application Programming Interface",
            preferred_forms=["API", "APIs"],
            avoid_forms=["api", "A.P.I."],
            context="technical",
            language="en",
        )

        assert term.term == "API"
        assert term.definition == "Application Programming Interface"
        assert "API" in term.preferred_forms
        assert "api" in term.avoid_forms
        assert term.language == "en"

    def test_default_values(self):
        """Test default values for glossary term."""
        term = GlossaryTerm(
            term="test",
            definition="A test term",
        )

        assert term.preferred_forms == []
        assert term.avoid_forms == []
        assert term.context is None
        assert term.language == "en"


class TestTerminologyChecker:
    """Test TerminologyChecker class."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project for testing."""
        project = MagicMock()
        project.root = temp_dir
        project.languages = ["en", "no"]
        project.list_chapters = MagicMock(return_value=[])
        return project

    @pytest.fixture
    def checker(self, mock_project):
        """Create a terminology checker."""
        return TerminologyChecker(mock_project)

    def test_init(self, checker, temp_dir):
        """Test checker initialization."""
        assert checker.glossary_path == temp_dir / ".media-engine" / "glossary.json"

    def test_add_term(self, checker):
        """Test adding a term to glossary."""
        checker.add_term(
            term="API",
            definition="Application Programming Interface",
            preferred_forms=["API"],
            avoid_forms=["api"],
            language="en",
        )

        terms = checker.get_glossary("en")
        assert len(terms) == 1
        assert terms[0].term == "API"

    def test_add_term_saves_to_disk(self, checker, temp_dir):
        """Test that adding term persists to disk."""
        checker.add_term(
            term="Test",
            definition="A test term",
        )

        glossary_path = temp_dir / ".media-engine" / "glossary.json"
        assert glossary_path.exists()

        data = json.loads(glossary_path.read_text())
        assert len(data["terms"]) == 1

    def test_get_glossary_by_language(self, checker):
        """Test getting glossary filtered by language."""
        checker.add_term("English term", "EN definition", language="en")
        checker.add_term("Norwegian term", "NO definition", language="no")

        en_terms = checker.get_glossary("en")
        no_terms = checker.get_glossary("no")

        assert len(en_terms) == 1
        assert len(no_terms) == 1
        assert en_terms[0].term == "English term"
        assert no_terms[0].term == "Norwegian term"

    def test_get_glossary_all(self, checker):
        """Test getting all glossary terms."""
        checker.add_term("Term 1", "Def 1", language="en")
        checker.add_term("Term 2", "Def 2", language="no")

        all_terms = checker.get_glossary()
        assert len(all_terms) == 2

    def test_check_document_finds_avoid_forms(self, checker, temp_dir):
        """Test checking document for terminology issues."""
        # Add term with avoid form
        checker.add_term(
            term="User Interface",
            definition="The visual interface",
            preferred_forms=["User Interface", "UI"],
            avoid_forms=["user-interface", "userinterface"],
            language="en",
        )

        # Create a test document
        doc_path = temp_dir / "test.md"
        doc_content = """---
title: Test Doc
language: en
---

# Test Document

This is a user-interface test.
"""
        doc_path.write_text(doc_content)

        # Mock Document.load at the point where it's imported in the integrity module
        with patch("media_engine.cms.document.Document") as mock_doc_class:
            mock_doc = MagicMock()
            mock_doc.content = "This is a user-interface test."
            mock_doc.metadata = {"language": "en"}
            mock_doc_class.load.return_value = mock_doc

            issues = checker.check_document(doc_path, "en")

        assert len(issues) >= 1
        assert issues[0]["type"] == "avoid_form"
        assert issues[0]["found"] == "user-interface"

    def test_export_glossary_markdown(self, checker, temp_dir):
        """Test exporting glossary to markdown."""
        checker.add_term(
            term="API",
            definition="Application Programming Interface",
            preferred_forms=["API"],
            avoid_forms=["api"],
        )

        output_path = temp_dir / "glossary.md"
        result = checker.export_glossary(output_path, format="markdown")

        assert result == output_path
        assert output_path.exists()

        content = output_path.read_text()
        assert "# Glossary" in content
        assert "API" in content
        assert "Application Programming Interface" in content

    def test_export_glossary_json(self, checker, temp_dir):
        """Test exporting glossary to JSON."""
        checker.add_term("Test", "Test definition")

        output_path = temp_dir / "glossary.json"
        checker.export_glossary(output_path, format="json")

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "terms" in data

    def test_generate_report(self, checker):
        """Test generating terminology report."""
        checker.add_term("Term 1", "Definition 1", language="en")
        checker.add_term("Term 2", "Definition 2", language="en")

        report = checker.generate_report()

        assert "summary" in report
        assert report["summary"]["total_terms"] == 2
        assert "en" in report["summary"]["languages"]

    def test_load_existing_glossary(self, mock_project, temp_dir):
        """Test loading existing glossary data."""
        # Create glossary file
        data_dir = temp_dir / ".media-engine"
        data_dir.mkdir(parents=True, exist_ok=True)

        glossary_data = {
            "terms": [
                {
                    "term": "Existing",
                    "definition": "Already exists",
                    "preferred_forms": ["Existing"],
                    "avoid_forms": [],
                    "language": "en",
                }
            ]
        }
        (data_dir / "glossary.json").write_text(json.dumps(glossary_data))

        # Create new checker - should load data
        checker = TerminologyChecker(mock_project)

        terms = checker.get_glossary("en")
        assert len(terms) == 1
        assert terms[0].term == "Existing"


class TestGenerateFullIntegrityReport:
    """Test the combined integrity report function."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project."""
        project = MagicMock()
        project.root = temp_dir
        project.assets_dir = temp_dir / "assets"
        project.assets_dir.mkdir(parents=True, exist_ok=True)
        project.languages = ["en"]
        project.list_chapters = MagicMock(return_value=[])
        return project

    def test_generate_full_report(self, mock_project):
        """Test generating full integrity report."""
        report = generate_full_integrity_report(mock_project)

        assert "assets" in report
        assert "terminology" in report
        assert "generated_at" in report

    def test_report_structure(self, mock_project):
        """Test report structure contains expected sections."""
        report = generate_full_integrity_report(mock_project)

        # Assets section
        assert "summary" in report["assets"]
        assert "issues" in report["assets"]

        # Terminology section
        assert "summary" in report["terminology"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def mock_project(self, temp_dir):
        """Create a mock project."""
        project = MagicMock()
        project.root = temp_dir
        project.assets_dir = temp_dir / "assets"
        return project

    def test_large_file_checksum(self, mock_project, temp_dir):
        """Test computing checksum for larger files."""
        checker = AssetIntegrityChecker(mock_project)

        # Create a larger file (100KB)
        large_file = temp_dir / "large.bin"
        large_file.write_bytes(b"x" * 100000)

        checksum = checker.compute_checksum(large_file)
        assert len(checksum) == 64

    def test_special_characters_in_path(self, mock_project, temp_dir):
        """Test handling paths with special characters."""
        (temp_dir / "assets").mkdir(parents=True, exist_ok=True)

        # Create file with spaces in name
        special_file = temp_dir / "assets" / "my file (1).png"
        special_file.write_bytes(b"content")

        checker = AssetIntegrityChecker(mock_project)
        result = checker.record_asset(special_file)

        assert result is not None
        assert "my file (1).png" in result.path

    def test_empty_glossary(self, mock_project):
        """Test terminology checker with empty glossary."""
        checker = TerminologyChecker(mock_project)

        report = checker.generate_report()
        assert report["summary"]["total_terms"] == 0
        assert report["summary"]["total_issues"] == 0

    def test_unicode_in_glossary(self, mock_project, temp_dir):
        """Test glossary with unicode characters."""
        checker = TerminologyChecker(mock_project)

        checker.add_term(
            term="Brukernavn",
            definition="Norwegian for username",
            language="no",
        )

        terms = checker.get_glossary("no")
        assert terms[0].term == "Brukernavn"

        # Export to markdown (JSON export uses default serializer)
        output_path = temp_dir / "unicode_glossary.md"
        checker.export_glossary(output_path, format="markdown")

        content = output_path.read_text()
        assert "Brukernavn" in content
