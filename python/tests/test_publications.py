"""
Tests for publications functionality.
"""


import pytest


@pytest.fixture
def publication_project(temp_dir):
    """Create a project with publication definitions."""
    # Create project structure
    (temp_dir / "content/en/chapters").mkdir(parents=True)
    (temp_dir / "content/en/publications").mkdir(parents=True)
    (temp_dir / "content/no/chapters").mkdir(parents=True)
    (temp_dir / "content/no/publications").mkdir(parents=True)

    # Create project.yaml
    project_yaml = temp_dir / "project.yaml"
    project_yaml.write_text("""
project:
  name: "Publications Test"

localization:
  source_language: "en"
  languages:
    en:
      name: "English"
    "no":
      name: "Norwegian"

paths:
  content: "content"
""")

    # Create English chapters
    (temp_dir / "content/en/chapters/01_intro.md").write_text("""---
title: "Introduction"
---
# Introduction
""")

    (temp_dir / "content/en/chapters/02_features.md").write_text("""---
title: "Features"
---
# Features
""")

    # Create English publication
    (temp_dir / "content/en/publications/documentation.yaml").write_text("""
title: "Complete Documentation"
subtitle: "All Chapters"
description: "Full documentation package"
language: en

metadata:
  version: "1.0.0"
  status: "draft"

outputs:
  - type: pdf
    filename: "documentation-en.pdf"
  - type: pptx
    filename: "documentation-en.pptx"

chapters:
  - path: "en/chapters/01_intro.md"
  - path: "en/chapters/02_features.md"
""")

    # Create Norwegian publication (translation)
    (temp_dir / "content/no/publications/dokumentasjon.yaml").write_text("""
title: "Komplett Dokumentasjon"
subtitle: "Alle Kapitler"
description: "Full dokumentasjonspakke"
language: "no"
source_document: "en/publications/documentation.yaml"
source_hash: "oldhash12345678"

metadata:
  version: "1.0.0"
  status: "draft"

outputs:
  - type: pdf
    filename: "dokumentasjon-no.pdf"

chapters:
  - path: "no/chapters/01_intro.md"
  - path: "no/chapters/02_features.md"
""")

    from media_engine.core.project import Project
    return Project.load(temp_dir)


class TestPublicationRegistry:
    """Tests for PublicationRegistry."""

    def test_load_publications(self, publication_project):
        """Test loading publications from project."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        pubs = registry.list_publications()

        assert len(pubs) >= 2

    def test_filter_by_language(self, publication_project):
        """Test filtering publications by language."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)

        en_pubs = registry.list_publications(language="en")
        assert len(en_pubs) >= 1
        assert all(p.language == "en" for p in en_pubs)

        no_pubs = registry.list_publications(language="no")
        assert len(no_pubs) >= 1
        assert all(p.language == "no" for p in no_pubs)

    def test_get_publication_by_path(self, publication_project):
        """Test getting a publication by path."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        pubs = registry.list_publications()

        # Find the English documentation
        en_doc = next((p for p in pubs if p.language == "en"), None)
        assert en_doc is not None
        assert en_doc.title == "Complete Documentation"

    def test_publication_status(self, publication_project):
        """Test getting publication status."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        pubs = registry.list_publications()

        for pub in pubs:
            status = registry.get_status(pub)
            assert status is not None
            assert hasattr(status, "missing_chapters")

    def test_translation_pairs(self, publication_project):
        """Test getting translation pairs for publications."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        pairs = registry.get_translation_pairs()

        # Should have at least one pair
        assert len(pairs) >= 1


class TestPublicationDataclass:
    """Tests for Publication dataclass."""

    def test_publication_fields(self, publication_project):
        """Test Publication dataclass fields."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        pubs = registry.list_publications(language="en")

        en_pub = pubs[0]
        assert en_pub.title == "Complete Documentation"
        assert en_pub.language == "en"
        assert len(en_pub.outputs) >= 1
        assert len(en_pub.chapters) >= 1

    def test_output_config(self, publication_project):
        """Test OutputConfig in publications."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        pubs = registry.list_publications(language="en")

        en_pub = pubs[0]
        output = en_pub.outputs[0]

        assert output.format in ["pdf", "pptx", "html", "xlsx"]
        assert output.filename


class TestPublicationStatus:
    """Tests for PublicationStatus."""

    def test_status_fields(self, publication_project):
        """Test PublicationStatus fields."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        pubs = registry.list_publications()

        for pub in pubs:
            status = registry.get_status(pub)
            assert hasattr(status, "publication")
            assert hasattr(status, "chapter_count")
            assert hasattr(status, "missing_chapters")
            assert hasattr(status, "is_valid")


class TestPublicationTranslation:
    """Tests for publication translation tracking."""

    def test_translation_reference(self, publication_project):
        """Test that Norwegian publication has translation reference."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        no_pubs = registry.list_publications(language="no")

        no_pub = no_pubs[0]
        assert no_pub.source_document is not None
        assert "documentation.yaml" in no_pub.source_document

    def test_translation_hash(self, publication_project):
        """Test that translation has source hash."""
        from media_engine.cms.publication import PublicationRegistry

        registry = PublicationRegistry(publication_project)
        no_pubs = registry.list_publications(language="no")

        no_pub = no_pubs[0]
        assert no_pub.source_hash is not None
