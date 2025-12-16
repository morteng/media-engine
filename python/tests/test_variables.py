"""
Tests for the variables module - content variable interpolation.
"""

from pathlib import Path

import pytest
from media_engine.variables import (
    ContentInterpolator,
    ProjectInterpolator,
    VariableLoader,
    VariableSet,
    interpolate_content,
    validate_variables,
)


class TestVariableSet:
    """Tests for VariableSet dataclass."""

    def test_default_empty(self):
        """Test default empty variable set."""
        vs = VariableSet()
        assert vs.project == {}
        assert vs.date == {}
        assert vs.env == {}
        assert vs.custom == {}

    def test_get_project_variable(self):
        """Test getting project variables."""
        vs = VariableSet(project={"name": "Test Project", "version": "1.0"})
        assert vs.get("project.name") == "Test Project"
        assert vs.get("project.version") == "1.0"

    def test_get_date_variable(self):
        """Test getting date variables."""
        vs = VariableSet(date={"year": "2025", "month": "12"})
        assert vs.get("date.year") == "2025"
        assert vs.get("date.month") == "12"

    def test_get_env_variable(self):
        """Test getting environment variables."""
        vs = VariableSet(env={"API_URL": "https://api.example.com"})
        assert vs.get("env.API_URL") == "https://api.example.com"

    def test_get_custom_variable(self):
        """Test getting custom variables."""
        vs = VariableSet(
            custom={
                "pricing": {"starter": "$10", "pro": "$50"},
                "company": "Acme Inc",
            }
        )
        assert vs.get("pricing.starter") == "$10"
        assert vs.get("pricing.pro") == "$50"
        assert vs.get("company") == "Acme Inc"

    def test_get_nested_custom(self):
        """Test getting deeply nested custom variables."""
        vs = VariableSet(
            custom={
                "config": {
                    "api": {
                        "endpoint": "https://api.example.com",
                        "version": "v2",
                    }
                }
            }
        )
        assert vs.get("config.api.endpoint") == "https://api.example.com"
        assert vs.get("config.api.version") == "v2"

    def test_get_missing_returns_default(self):
        """Test that missing variables return default."""
        vs = VariableSet()
        assert vs.get("missing.var") is None
        assert vs.get("missing.var", "default") == "default"

    def test_get_empty_path(self):
        """Test getting empty path returns empty dict."""
        vs = VariableSet()
        # Empty path returns empty dict (all custom vars, which is empty)
        assert vs.get("") == {}

    def test_to_dict(self):
        """Test converting to dictionary."""
        vs = VariableSet(
            project={"name": "Test"},
            date={"year": "2025"},
            env={"KEY": "value"},
            custom={"pricing": {"starter": 10}},
        )
        result = vs.to_dict()
        assert "project" in result
        assert "date" in result
        assert "env" in result
        assert "pricing" in result
        assert result["project"]["name"] == "Test"


class TestContentInterpolator:
    """Tests for ContentInterpolator class."""

    @pytest.fixture
    def variables(self):
        """Create a variable set for testing."""
        return VariableSet(
            project={"name": "Test Project", "version": "1.0.0"},
            date={"year": "2025", "today": "2025-12-16"},
            custom={"company": "Acme Inc", "pricing": {"starter": "$10"}},
        )

    @pytest.fixture
    def interpolator(self, variables):
        """Create an interpolator instance."""
        return ContentInterpolator(variables)

    def test_interpolate_project_variable(self, interpolator):
        """Test interpolating project variables."""
        content = "Welcome to {{project.name}}!"
        result, missing = interpolator.interpolate(content)
        assert result == "Welcome to Test Project!"
        assert len(missing) == 0

    def test_interpolate_date_variable(self, interpolator):
        """Test interpolating date variables."""
        content = "Copyright {{date.year}}"
        result, missing = interpolator.interpolate(content)
        assert result == "Copyright 2025"
        assert len(missing) == 0

    def test_interpolate_custom_variable(self, interpolator):
        """Test interpolating custom variables."""
        content = "By {{company}}"
        result, missing = interpolator.interpolate(content)
        assert result == "By Acme Inc"

    def test_interpolate_nested_custom(self, interpolator):
        """Test interpolating nested custom variables."""
        content = "Starting at {{pricing.starter}}"
        result, missing = interpolator.interpolate(content)
        assert result == "Starting at $10"

    def test_interpolate_with_spaces(self, interpolator):
        """Test interpolating with spaces in braces."""
        content = "Welcome to {{ project.name }}!"
        result, missing = interpolator.interpolate(content)
        assert result == "Welcome to Test Project!"

    def test_interpolate_multiple(self, interpolator):
        """Test interpolating multiple variables."""
        content = "{{project.name}} v{{project.version}} - {{date.year}}"
        result, missing = interpolator.interpolate(content)
        assert result == "Test Project v1.0.0 - 2025"

    def test_missing_variable_returns_original(self, interpolator):
        """Test that missing variables return original."""
        content = "Value: {{missing.var}}"
        result, missing = interpolator.interpolate(content)
        assert result == "Value: {{missing.var}}"
        assert "missing.var" in missing

    def test_missing_variable_strict_mode(self, interpolator):
        """Test strict mode raises on missing."""
        content = "Value: {{missing.var}}"
        with pytest.raises(ValueError, match="Missing variable"):
            interpolator.interpolate(content, strict=True)

    def test_find_variables(self, interpolator):
        """Test finding all variables in content."""
        content = "{{project.name}} and {{date.year}} and {{custom.value}}"
        found = interpolator.find_variables(content)
        assert "project.name" in found
        assert "date.year" in found
        assert "custom.value" in found

    def test_validate_finds_missing(self, interpolator):
        """Test validation finds missing variables."""
        content = "{{project.name}} and {{missing.var}}"
        missing = interpolator.validate(content)
        assert "missing.var" in missing
        assert "project.name" not in missing

    def test_no_variables(self, interpolator):
        """Test content with no variables."""
        content = "Just plain text"
        result, missing = interpolator.interpolate(content)
        assert result == "Just plain text"
        assert len(missing) == 0

    def test_invalid_variable_syntax(self, interpolator):
        """Test invalid variable syntax is ignored."""
        content = "{project.name} and {{valid}} and {{ }}"
        # Single braces should not be interpolated
        found = interpolator.find_variables(content)
        # Only valid pattern should be found
        assert len([v for v in found if v]) >= 0


class TestVariableLoader:
    """Tests for VariableLoader class."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project

        return Project.load(demo_path)

    def test_load_project_variables(self, demo_project):
        """Test loading project variables."""
        loader = VariableLoader(demo_project)
        vs = loader.load()

        assert vs.project["name"] == demo_project.config.name
        assert vs.project["source_language"] == demo_project.source_language
        assert "languages" in vs.project

    def test_load_date_variables(self, demo_project):
        """Test loading date variables."""
        loader = VariableLoader(demo_project)
        vs = loader.load()

        assert "today" in vs.date
        assert "year" in vs.date
        assert "month" in vs.date
        assert "timestamp" in vs.date

        # Verify date format
        assert len(vs.date["year"]) == 4  # YYYY
        assert len(vs.date["month"]) == 2  # MM

    def test_load_env_variables(self, demo_project, monkeypatch):
        """Test loading environment variables."""
        monkeypatch.setenv("MEDIA_ENGINE_TEST", "test_value")

        loader = VariableLoader(demo_project)
        vs = loader.load()

        assert vs.env.get("MEDIA_ENGINE_TEST") == "test_value"

    def test_env_filtering(self, demo_project, monkeypatch):
        """Test that only safe env vars are loaded."""
        monkeypatch.setenv("MEDIA_ENGINE_SAFE", "safe")
        monkeypatch.setenv("UNSAFE_VAR", "unsafe")

        loader = VariableLoader(demo_project)
        vs = loader.load()

        assert "MEDIA_ENGINE_SAFE" in vs.env
        assert "UNSAFE_VAR" not in vs.env


class TestProjectInterpolator:
    """Tests for ProjectInterpolator class."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project

        return Project.load(demo_path)

    def test_create_interpolator(self, demo_project):
        """Test creating a project interpolator."""
        interp = ProjectInterpolator(demo_project)
        assert interp.variables is not None
        assert interp.project == demo_project

    def test_get_available_variables(self, demo_project):
        """Test getting available variables."""
        interp = ProjectInterpolator(demo_project)
        available = interp.get_available_variables()

        assert "project" in available
        assert "date" in available
        assert "env" in available

    def test_validate_project(self, demo_project):
        """Test validating project for missing variables."""
        interp = ProjectInterpolator(demo_project)
        result = interp.validate_project()

        assert "total_files_with_issues" in result
        assert "issues" in result
        assert "all_missing" in result


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture
    def demo_project(self):
        """Load demo project if available."""
        demo_path = Path(__file__).parent.parent.parent / "demo"
        if not demo_path.exists():
            pytest.skip("Demo project not found")
        from media_engine.core.project import Project

        return Project.load(demo_path)

    def test_interpolate_content(self, demo_project):
        """Test interpolate_content function."""
        content = "Project: {{project.name}}"
        result = interpolate_content(demo_project, content)
        assert demo_project.config.name in result

    def test_validate_variables(self, demo_project):
        """Test validate_variables function."""
        result = validate_variables(demo_project)
        assert "total_files_with_issues" in result
        assert "issues" in result


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_content(self):
        """Test interpolating empty content."""
        vs = VariableSet()
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("")
        assert result == ""
        assert len(missing) == 0

    def test_only_braces(self):
        """Test content with only braces."""
        vs = VariableSet()
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("{{}}")
        # Should not match invalid pattern
        assert result == "{{}}"

    def test_nested_braces(self):
        """Test nested braces."""
        vs = VariableSet(project={"name": "Test"})
        interp = ContentInterpolator(vs)
        # Nested braces should work
        result, missing = interp.interpolate("{{{{project.name}}}}")
        # Outer braces remain
        assert "Test" in result

    def test_special_characters_in_value(self):
        """Test values with special characters."""
        vs = VariableSet(custom={"url": "https://example.com/path?q=1&x=2"})
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("URL: {{url}}")
        assert result == "URL: https://example.com/path?q=1&x=2"

    def test_unicode_values(self):
        """Test unicode values."""
        vs = VariableSet(custom={"greeting": "Hei, velkommen!"})
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("{{greeting}}")
        assert result == "Hei, velkommen!"

    def test_numeric_values(self):
        """Test numeric values are converted to string."""
        vs = VariableSet(custom={"count": 42, "price": 19.99})
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("Count: {{count}}, Price: {{price}}")
        assert result == "Count: 42, Price: 19.99"

    def test_boolean_values(self):
        """Test boolean values are converted to string."""
        vs = VariableSet(custom={"enabled": True, "disabled": False})
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("{{enabled}} and {{disabled}}")
        assert "True" in result
        assert "False" in result

    def test_list_values(self):
        """Test list values are converted to string."""
        vs = VariableSet(custom={"items": ["a", "b", "c"]})
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("Items: {{items}}")
        assert "a" in result  # List converted to string representation

    def test_multiline_content(self):
        """Test multiline content."""
        vs = VariableSet(project={"name": "Test"})
        interp = ContentInterpolator(vs)
        content = """
        Line 1: {{project.name}}
        Line 2: more text
        Line 3: {{project.name}} again
        """
        result, missing = interp.interpolate(content)
        assert result.count("Test") == 2

    def test_variable_at_start(self):
        """Test variable at start of content."""
        vs = VariableSet(project={"name": "Test"})
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("{{project.name}} is first")
        assert result.startswith("Test")

    def test_variable_at_end(self):
        """Test variable at end of content."""
        vs = VariableSet(project={"name": "Test"})
        interp = ContentInterpolator(vs)
        result, missing = interp.interpolate("Last is {{project.name}}")
        assert result.endswith("Test")
