"""Tests for CLI commands."""

import pytest


@pytest.fixture
def sample_project(tmp_path):
    """Create a sample project for CLI testing."""
    import yaml

    # Create project structure
    content_dir = tmp_path / "content"
    (content_dir / "en" / "chapters").mkdir(parents=True)
    (content_dir / "no" / "chapters").mkdir(parents=True)
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()

    # Create project.yaml
    project_config = {
        "name": "Test CLI Project",
        "description": "A test project for CLI",
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


class TestCLIParser:
    """Test CLI argument parsing."""

    def test_status_parser(self):
        """Test status command parser."""

        from media_engine.cli import main

        # Just verify the module can be imported
        assert callable(main)

    def test_import_commands(self):
        """Test that all command modules can be imported."""
        from media_engine.cli.commands import (
            cmd_build,
            cmd_quality,
            cmd_status,
        )

        assert cmd_status is not None
        assert cmd_build is not None
        assert cmd_quality is not None


class TestStatusCommand:
    """Test status command."""

    def test_status_output(self, sample_project, monkeypatch):
        """Test status command output."""
        monkeypatch.chdir(sample_project)

        from media_engine.cli.commands.status import cmd_status

        # Create a namespace-like object for args
        class Args:
            view = None
            lang = None
            json = True  # Use JSON output for easier testing

        # This should not raise (cmd_status finds project internally)
        try:
            cmd_status(Args())
        except SystemExit:
            pass  # Some commands exit after running


class TestBuildCommand:
    """Test build command."""

    def test_build_imports(self):
        """Test build command imports."""
        from media_engine.cli.commands.build import cmd_build

        assert callable(cmd_build)


class TestQualityCommand:
    """Test quality command."""

    def test_quality_imports(self):
        """Test quality command imports."""
        from media_engine.cli.commands.quality import cmd_quality

        assert callable(cmd_quality)


class TestTranslationCommand:
    """Test translation command."""

    def test_translation_imports(self):
        """Test translation command imports."""
        from media_engine.cli.commands.translation import cmd_translation

        assert callable(cmd_translation)


class TestFreshnessCommand:
    """Test freshness command."""

    def test_freshness_imports(self):
        """Test freshness command imports."""
        from media_engine.cli.commands.freshness import cmd_freshness

        assert callable(cmd_freshness)


class TestHealthCommand:
    """Test health command."""

    def test_health_imports(self):
        """Test health command imports."""
        from media_engine.cli.commands.insights import cmd_health

        assert callable(cmd_health)


class TestStatsCommand:
    """Test stats command."""

    def test_stats_imports(self):
        """Test stats command imports."""
        from media_engine.cli.commands.insights import cmd_stats

        assert callable(cmd_stats)


class TestCacheCommand:
    """Test cache command."""

    def test_cache_imports(self):
        """Test cache command imports."""
        from media_engine.cli.commands.cache import cmd_cache

        assert callable(cmd_cache)


class TestValidateCommand:
    """Test validate command."""

    def test_validate_imports(self):
        """Test validate command imports."""
        from media_engine.cli.commands.validate import cmd_validate

        assert callable(cmd_validate)


class TestSecurityCommand:
    """Test security command."""

    def test_security_imports(self):
        """Test security command imports."""
        from media_engine.cli.commands.content import cmd_security

        assert callable(cmd_security)


class TestLinksCommand:
    """Test links command."""

    def test_links_imports(self):
        """Test links command imports."""
        from media_engine.cli.commands.content import cmd_links

        assert callable(cmd_links)


class TestReadabilityCommand:
    """Test readability command."""

    def test_readability_imports(self):
        """Test readability command imports."""
        from media_engine.cli.commands.content import cmd_readability

        assert callable(cmd_readability)


class TestGapsCommand:
    """Test gaps command."""

    def test_gaps_imports(self):
        """Test gaps command imports."""
        from media_engine.cli.commands.content import cmd_gaps

        assert callable(cmd_gaps)


class TestChangelogCommand:
    """Test changelog command."""

    def test_changelog_imports(self):
        """Test changelog command imports."""
        from media_engine.cli.commands.content import cmd_changelog

        assert callable(cmd_changelog)


class TestSearchCommand:
    """Test search command."""

    def test_search_imports(self):
        """Test search command imports."""
        from media_engine.cli.commands.search import cmd_search

        assert callable(cmd_search)


class TestInitCommand:
    """Test init command."""

    def test_init_imports(self):
        """Test init command imports."""
        from media_engine.cli.commands.init import cmd_init

        assert callable(cmd_init)


class TestPackCommand:
    """Test pack command."""

    def test_pack_imports(self):
        """Test pack command imports."""
        from media_engine.cli.commands.pack import cmd_pack

        assert callable(cmd_pack)


class TestPublishCommand:
    """Test publish command."""

    def test_publish_imports(self):
        """Test publish command imports."""
        from media_engine.cli.commands.publish import cmd_publish

        assert callable(cmd_publish)


class TestDemosCommand:
    """Test demos command."""

    def test_demos_imports(self):
        """Test demos command imports."""
        from media_engine.cli.commands.demos import cmd_demos

        assert callable(cmd_demos)


class TestIntegrityCommand:
    """Test integrity command."""

    def test_integrity_imports(self):
        """Test integrity command imports."""
        from media_engine.cli.commands.integrity import cmd_integrity

        assert callable(cmd_integrity)


class TestProvenanceCommand:
    """Test provenance command."""

    def test_provenance_imports(self):
        """Test provenance command imports."""
        from media_engine.cli.commands.provenance import cmd_provenance

        assert callable(cmd_provenance)


class TestNotesCommand:
    """Test notes command."""

    def test_notes_imports(self):
        """Test notes command imports."""
        from media_engine.cli.commands.notes import cmd_notes

        assert callable(cmd_notes)


class TestReleaseCommand:
    """Test release command."""

    def test_release_imports(self):
        """Test release command imports."""
        from media_engine.cli.commands.release import cmd_release

        assert callable(cmd_release)


class TestDashboardCommand:
    """Test dashboard command."""

    def test_dashboard_imports(self):
        """Test dashboard command imports."""
        from media_engine.cli.commands.dashboard import cmd_dashboard

        assert callable(cmd_dashboard)


class TestBrandCommand:
    """Test brand command."""

    def test_brand_imports(self):
        """Test brand command imports."""
        from media_engine.cli.commands.brand import cmd_brand

        assert callable(cmd_brand)


class TestAnalyzeCommand:
    """Test analyze command."""

    def test_analyze_imports(self):
        """Test analyze command imports."""
        from media_engine.cli.commands.analyze import cmd_analyze

        assert callable(cmd_analyze)


class TestInsightsCommand:
    """Test insights command."""

    def test_insights_imports(self):
        """Test insights command imports."""
        from media_engine.cli.commands.insights import (
            cmd_consistency,
            cmd_duplicates,
            cmd_graph,
            cmd_health,
            cmd_incomplete,
            cmd_parity,
            cmd_path,
            cmd_stats,
            cmd_terms,
            cmd_velocity,
        )

        assert callable(cmd_health)
        assert callable(cmd_stats)
        assert callable(cmd_consistency)
        assert callable(cmd_duplicates)
        assert callable(cmd_terms)
        assert callable(cmd_parity)
        assert callable(cmd_incomplete)
        assert callable(cmd_velocity)
        assert callable(cmd_graph)
        assert callable(cmd_path)


class TestContentCommand:
    """Test content command."""

    def test_content_imports(self):
        """Test content command imports."""
        from media_engine.cli.commands.content import (
            cmd_changelog,
            cmd_gaps,
            cmd_links,
            cmd_readability,
            cmd_security,
        )

        assert callable(cmd_security)
        assert callable(cmd_links)
        assert callable(cmd_readability)
        assert callable(cmd_gaps)
        assert callable(cmd_changelog)
