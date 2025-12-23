"""Tests for brand module."""

import pytest


class TestBrandColors:
    """Tests for brand color system."""

    def test_brand_colors_creation(self):
        """Test creating BrandColors."""
        from media_engine.brand import BrandColors

        colors = BrandColors(
            primary="#6366f1",
            secondary="#8b5cf6",
            accent="#06b6d4",
        )

        assert colors.primary == "#6366f1"
        assert colors.secondary == "#8b5cf6"
        assert colors.accent == "#06b6d4"

    def test_semantic_colors(self):
        """Test SemanticColors."""
        from media_engine.brand import SemanticColors

        colors = SemanticColors(
            success="#10b981",
            warning="#f59e0b",
            error="#ef4444",
            info="#3b82f6",
        )

        assert colors.success == "#10b981"
        assert colors.error == "#ef4444"

    def test_text_colors(self):
        """Test TextColors."""
        from media_engine.brand import TextColors

        colors = TextColors(
            primary="#1f2937",
            secondary="#4b5563",
            muted="#9ca3af",
        )

        assert colors.primary == "#1f2937"
        assert colors.muted == "#9ca3af"

    def test_background_colors(self):
        """Test BackgroundColors."""
        from media_engine.brand import BackgroundColors

        colors = BackgroundColors(
            primary="#ffffff",
            secondary="#f9fafb",
        )

        assert colors.primary == "#ffffff"
        assert colors.secondary == "#f9fafb"

    def test_surface_colors(self):
        """Test SurfaceColors."""
        from media_engine.brand import SurfaceColors

        colors = SurfaceColors()
        # Default values
        assert hasattr(colors, "default")

    def test_border_colors(self):
        """Test BorderColors."""
        from media_engine.brand import BorderColors

        colors = BorderColors()
        assert hasattr(colors, "default")

    def test_dark_mode_colors(self):
        """Test DarkModeColors."""
        from media_engine.brand import BackgroundColors, DarkModeColors, TextColors

        dark = DarkModeColors(
            text=TextColors(primary="#f9fafb", secondary="#e5e7eb", muted="#9ca3af"),
            background=BackgroundColors(primary="#111827", secondary="#1f2937"),
        )

        assert dark.text.primary == "#f9fafb"
        assert dark.background.primary == "#111827"

    def test_color_system(self):
        """Test ColorSystem."""
        from media_engine.brand import (
            BackgroundColors,
            BrandColors,
            ColorSystem,
            SemanticColors,
            TextColors,
        )

        system = ColorSystem(
            brand=BrandColors(primary="#6366f1", secondary="#8b5cf6", accent="#06b6d4"),
            semantic=SemanticColors(
                success="#10b981", warning="#f59e0b", error="#ef4444", info="#3b82f6"
            ),
            text=TextColors(primary="#1f2937", secondary="#4b5563", muted="#9ca3af"),
            background=BackgroundColors(primary="#ffffff", secondary="#f9fafb"),
        )

        assert system.brand.primary == "#6366f1"
        assert system.semantic.error == "#ef4444"


class TestTypography:
    """Tests for typography classes."""

    def test_font_asset(self):
        """Test FontAsset."""
        from media_engine.brand import FontAsset

        font = FontAsset(
            family="Inter",
            weights=[400, 500, 600, 700],
            source="google",
        )

        assert font.family == "Inter"
        assert 400 in font.weights
        assert font.source == "google"

    def test_font_scale(self):
        """Test FontScale."""
        from media_engine.brand import FontScale

        scale = FontScale()
        assert hasattr(scale, "base")
        assert hasattr(scale, "lg")
        assert hasattr(scale, "xl")

    def test_line_height(self):
        """Test LineHeight."""
        from media_engine.brand import LineHeight

        lh = LineHeight()
        assert hasattr(lh, "normal")
        assert hasattr(lh, "tight")

    def test_letter_spacing(self):
        """Test LetterSpacing."""
        from media_engine.brand import LetterSpacing

        ls = LetterSpacing()
        assert hasattr(ls, "normal")

    def test_typography_system(self):
        """Test Typography."""
        from media_engine.brand import FontAsset, Typography

        typo = Typography(
            heading=FontAsset(family="Inter", weights=[600, 700], source="google"),
            body=FontAsset(family="Inter", weights=[400, 500], source="google"),
        )

        assert typo.heading.family == "Inter"
        assert typo.body.family == "Inter"


class TestTokens:
    """Tests for design tokens."""

    def test_spacing_scale(self):
        """Test SpacingScale."""
        from media_engine.brand import SpacingScale

        spacing = SpacingScale()
        assert hasattr(spacing, "unit")
        assert hasattr(spacing, "scale")

    def test_border_tokens(self):
        """Test BorderTokens."""
        from media_engine.brand import BorderTokens

        tokens = BorderTokens()
        assert hasattr(tokens, "radius")

    def test_shadow_tokens(self):
        """Test ShadowTokens."""
        from media_engine.brand import ShadowTokens

        tokens = ShadowTokens()
        assert hasattr(tokens, "sm")
        assert hasattr(tokens, "md")

    def test_transition_tokens(self):
        """Test TransitionTokens."""
        from media_engine.brand import TransitionTokens

        tokens = TransitionTokens()
        assert hasattr(tokens, "duration")

    def test_z_index_scale(self):
        """Test ZIndexScale."""
        from media_engine.brand import ZIndexScale

        scale = ZIndexScale()
        assert hasattr(scale, "modal")
        assert hasattr(scale, "dropdown")

    def test_breakpoints(self):
        """Test Breakpoints."""
        from media_engine.brand import Breakpoints

        bp = Breakpoints()
        assert hasattr(bp, "sm")
        assert hasattr(bp, "md")
        assert hasattr(bp, "lg")

    def test_component_tokens(self):
        """Test ComponentTokens."""
        from media_engine.brand import ComponentTokens

        tokens = ComponentTokens()
        assert hasattr(tokens, "button")


class TestLogos:
    """Tests for logo assets."""

    def test_logo_asset(self):
        """Test LogoAsset."""
        from media_engine.brand import LogoAsset

        logo = LogoAsset(
            path="brand/logos/logo.svg",
            alt="Company Logo",
        )

        assert logo.path == "brand/logos/logo.svg"
        assert logo.alt == "Company Logo"

    def test_logo_assets(self):
        """Test LogoAssets."""
        from media_engine.brand import LogoAsset, LogoAssets

        logos = LogoAssets(
            primary=LogoAsset(path="brand/logos/logo.svg", alt="Logo"),
        )

        assert logos.primary.path == "brand/logos/logo.svg"


class TestFonts:
    """Tests for font registry."""

    def test_font_config(self):
        """Test FontConfig."""
        from media_engine.brand import FontConfig

        config = FontConfig(
            name="Inter",
            weights=[400, 500, 600],
        )

        assert config.name == "Inter"
        assert 400 in config.weights

    def test_font_registry(self):
        """Test FontRegistry."""
        from media_engine.brand import FontAsset, FontRegistry

        registry = FontRegistry(
            heading=FontAsset(family="Inter", weights=[600, 700]),
            body=FontAsset(family="Inter", weights=[400, 500]),
            code=FontAsset(family="JetBrains Mono", weights=[400]),
        )

        assert registry.heading.family == "Inter"
        assert registry.body.family == "Inter"
        assert registry.code.family == "JetBrains Mono"

    def test_font_registry_unique_families(self):
        """Test getting unique font families."""
        from media_engine.brand import FontAsset, FontRegistry

        registry = FontRegistry(
            heading=FontAsset(family="Inter", weights=[600, 700]),
            body=FontAsset(family="Inter", weights=[400, 500]),
            code=FontAsset(family="JetBrains Mono", weights=[400]),
        )

        families = registry.get_unique_families()
        assert "Inter" in families
        assert "JetBrains Mono" in families
        assert len(families) == 2  # Inter and JetBrains Mono


class TestProfile:
    """Tests for brand profile."""

    def test_identity(self):
        """Test Identity."""
        from media_engine.brand import Identity, LogoAsset, LogoAssets

        identity = Identity(
            logos=LogoAssets(primary=LogoAsset(path="logo.svg", alt="Logo")),
        )

        assert identity.logos.primary.path == "logo.svg"

    def test_legal_info(self):
        """Test LegalInfo."""
        from media_engine.brand import LegalInfo

        legal = LegalInfo(
            copyright="2024 Company Inc.",
            tagline="Building the future",
        )

        assert legal.copyright == "2024 Company Inc."
        assert legal.tagline == "Building the future"

    def test_brand_profile(self):
        """Test BrandProfile."""
        from media_engine.brand import (
            BackgroundColors,
            BrandColors,
            BrandProfile,
            ColorSystem,
            FontAsset,
            Identity,
            LogoAsset,
            LogoAssets,
            SemanticColors,
            TextColors,
            Typography,
        )

        profile = BrandProfile(
            name="Test Brand",
            identity=Identity(logos=LogoAssets(primary=LogoAsset(path="logo.svg", alt="Logo"))),
            colors=ColorSystem(
                brand=BrandColors(primary="#6366f1", secondary="#8b5cf6", accent="#06b6d4"),
                semantic=SemanticColors(
                    success="#10b981", warning="#f59e0b", error="#ef4444", info="#3b82f6"
                ),
                text=TextColors(primary="#1f2937", secondary="#4b5563", muted="#9ca3af"),
                background=BackgroundColors(primary="#ffffff", secondary="#f9fafb"),
            ),
            typography=Typography(
                heading=FontAsset(family="Inter", weights=[600, 700], source="google"),
                body=FontAsset(family="Inter", weights=[400], source="google"),
            ),
        )

        assert profile.name == "Test Brand"
        assert profile.colors.brand.primary == "#6366f1"


class TestBrandContext:
    """Tests for brand context builder interface."""

    def test_brand_context_creation(self):
        """Test creating BrandContext."""
        from media_engine.brand import (
            BackgroundColors,
            BrandColors,
            BrandContext,
            BrandProfile,
            ColorSystem,
            FontAsset,
            Identity,
            LogoAsset,
            LogoAssets,
            SemanticColors,
            TextColors,
            Typography,
        )

        profile = BrandProfile(
            name="Test",
            identity=Identity(logos=LogoAssets(primary=LogoAsset(path="logo.svg", alt="Logo"))),
            colors=ColorSystem(
                brand=BrandColors(primary="#6366f1", secondary="#8b5cf6", accent="#06b6d4"),
                semantic=SemanticColors(
                    success="#10b981", warning="#f59e0b", error="#ef4444", info="#3b82f6"
                ),
                text=TextColors(primary="#1f2937", secondary="#4b5563", muted="#9ca3af"),
                background=BackgroundColors(primary="#ffffff", secondary="#f9fafb"),
            ),
            typography=Typography(
                body=FontAsset(family="Inter", weights=[400], source="google"),
            ),
        )

        context = BrandContext(profile=profile)
        assert context.profile == profile


class TestBrandLoader:
    """Tests for brand loading."""

    def test_load_brand_missing_file(self, tmp_path):
        """Test loading brand when file doesn't exist."""
        from media_engine.brand import load_brand_profile

        profile = load_brand_profile(tmp_path)
        # Should return default brand when file doesn't exist
        assert profile is not None
        assert profile.name == "Default Brand"


class TestInsightsRoutes:
    """Tests for insights API routes."""

    @pytest.fixture
    def sample_project(self, tmp_path):
        """Create a sample project for testing insights."""
        import yaml

        # Create project structure
        content_dir = tmp_path / "content"
        (content_dir / "en" / "chapters").mkdir(parents=True)
        (content_dir / "no" / "chapters").mkdir(parents=True)

        # Create project.yaml
        project_config = {
            "name": "Test Project",
            "description": "A test project",
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

This is the introduction.
""")

        doc2 = content_dir / "no" / "chapters" / "01_intro.md"
        doc2.write_text("""---
title: Introduksjon
language: "no"
source_document: en/chapters/01_intro.md
source_version: 1.0.0
---

# Introduksjon

Dette er introduksjonen.
""")

        return tmp_path

    def test_insights_api_exists(self, sample_project):
        """Test that insights API routes exist."""
        from media_engine.web.routes import insights

        assert hasattr(insights, "register_insights_routes")
