"""
Tests for media_engine.video.demo_registry module.
"""

import pytest
from media_engine.core.config import Config
from media_engine.core.project import LanguageConfig, Project
from media_engine.core.theme import Theme
from media_engine.video.demo_registry import (
    DemoDefinition,
    DemoRegistry,
    DemoState,
)


class TestDemoState:
    """Tests for DemoState dataclass."""

    def test_demo_state_defaults(self):
        """Test DemoState with default values."""
        state = DemoState(name="intro")
        assert state.name == "intro"
        assert state.description == ""
        assert state.setup is None
        assert state.wait_for is None

    def test_demo_state_with_all_fields(self):
        """Test DemoState with all fields."""
        state = DemoState(
            name="dashboard",
            description="Show the dashboard view",
            setup="document.querySelector('.nav-dashboard').click()",
            wait_for=".dashboard-panel",
        )
        assert state.name == "dashboard"
        assert state.description == "Show the dashboard view"
        assert "nav-dashboard" in state.setup
        assert state.wait_for == ".dashboard-panel"


class TestDemoDefinition:
    """Tests for DemoDefinition dataclass."""

    def test_demo_definition_defaults(self):
        """Test DemoDefinition with default values."""
        demo = DemoDefinition(name="test", url="http://localhost:3000")
        assert demo.name == "test"
        assert demo.url == "http://localhost:3000"
        assert demo.states == {}
        assert demo.viewport == {"width": 1920, "height": 1080}
        assert demo.metadata == {}

    def test_demo_definition_with_states(self):
        """Test DemoDefinition with states."""
        states = {
            "intro": DemoState(name="intro", description="Initial view"),
            "main": DemoState(name="main", description="Main content"),
        }
        demo = DemoDefinition(
            name="test-demo",
            url="http://example.com",
            states=states,
            viewport={"width": 1280, "height": 720},
            metadata={"author": "Test"},
        )
        assert demo.name == "test-demo"
        assert len(demo.states) == 2
        assert demo.viewport["width"] == 1280
        assert demo.metadata["author"] == "Test"

    def test_demo_definition_from_yaml(self, temp_dir):
        """Test loading DemoDefinition from YAML file."""
        yaml_content = """
name: platform-demo
url: "http://localhost:3000"
viewport:
  width: 1920
  height: 1080
metadata:
  version: "1.0"
states:
  intro:
    description: "Initial landing page"
    setup: "document.body.classList.add('ready')"
    wait_for: ".app-loaded"
  dashboard:
    description: "Dashboard view"
    setup: "window.router.push('/dashboard')"
    wait_for: ".dashboard"
  settings:
    description: "Settings panel"
"""
        yaml_path = temp_dir / "platform-demo.yaml"
        yaml_path.write_text(yaml_content)

        demo = DemoDefinition.from_yaml(yaml_path)

        assert demo.name == "platform-demo"
        assert demo.url == "http://localhost:3000"
        assert demo.viewport["width"] == 1920
        assert demo.metadata["version"] == "1.0"
        assert len(demo.states) == 3

        # Check full state
        intro = demo.states["intro"]
        assert intro.description == "Initial landing page"
        assert "classList.add" in intro.setup
        assert intro.wait_for == ".app-loaded"

        # Check simple state (description only)
        settings = demo.states["settings"]
        assert settings.description == "Settings panel"
        assert settings.setup is None
        assert settings.wait_for is None

    def test_demo_definition_from_yaml_minimal(self, temp_dir):
        """Test loading minimal DemoDefinition from YAML."""
        yaml_content = """
url: "http://example.com"
states:
  default: "Default view"
"""
        yaml_path = temp_dir / "minimal-demo.yaml"
        yaml_path.write_text(yaml_content)

        demo = DemoDefinition.from_yaml(yaml_path)

        assert demo.name == "minimal-demo"  # From filename
        assert demo.url == "http://example.com"
        assert "default" in demo.states
        assert demo.states["default"].description == "Default view"

    def test_demo_definition_get_state_exists(self, temp_dir):
        """Test get_state for existing state."""
        states = {"main": DemoState(name="main", description="Main view")}
        demo = DemoDefinition(name="test", url="http://example.com", states=states)

        state = demo.get_state("main")
        assert state.name == "main"
        assert state.description == "Main view"

    def test_demo_definition_get_state_not_found(self):
        """Test get_state raises KeyError for missing state."""
        demo = DemoDefinition(
            name="test",
            url="http://example.com",
            states={"one": DemoState(name="one", description="State one")},
        )

        with pytest.raises(KeyError) as exc_info:
            demo.get_state("missing")

        assert "missing" in str(exc_info.value)
        assert "one" in str(exc_info.value)  # Available states


class TestDemoRegistry:
    """Tests for DemoRegistry class."""

    def test_demo_registry_init(self):
        """Test DemoRegistry initialization."""
        registry = DemoRegistry()
        assert registry.project is None
        assert registry._cache == {}

    def test_demo_registry_with_project(self, temp_dir):
        """Test DemoRegistry with project."""
        project = self._create_mock_project(temp_dir)
        registry = DemoRegistry(project)
        assert registry.project is project

    def test_demo_registry_load(self, temp_dir):
        """Test loading a demo from registry."""
        project = self._create_mock_project(temp_dir)

        # Create demo file
        demos_dir = temp_dir / "content" / "en" / "demos"
        demos_dir.mkdir(parents=True)
        demo_path = demos_dir / "test-demo.yaml"
        demo_path.write_text("""
name: Test Demo
url: "http://localhost:3000"
states:
  intro: "Introduction"
""")

        registry = DemoRegistry(project)
        demo = registry.load("test-demo", language="en")

        assert demo.name == "Test Demo"
        assert demo.url == "http://localhost:3000"
        assert "intro" in demo.states

    def test_demo_registry_load_cached(self, temp_dir):
        """Test registry caches loaded demos."""
        project = self._create_mock_project(temp_dir)

        # Create demo file
        demos_dir = temp_dir / "content" / "en" / "demos"
        demos_dir.mkdir(parents=True)
        demo_path = demos_dir / "cached-demo.yaml"
        demo_path.write_text("name: Cached\nurl: http://test.com\nstates: {}")

        registry = DemoRegistry(project)

        # Load twice
        demo1 = registry.load("cached-demo", "en")
        demo2 = registry.load("cached-demo", "en")

        # Should be the same object (cached)
        assert demo1 is demo2
        assert "en/cached-demo" in registry._cache

    def test_demo_registry_load_not_found(self, temp_dir):
        """Test loading non-existent demo raises error."""
        project = self._create_mock_project(temp_dir)
        registry = DemoRegistry(project)

        with pytest.raises(FileNotFoundError) as exc_info:
            registry.load("nonexistent", "en")

        assert "nonexistent" in str(exc_info.value)

    def test_demo_registry_list_demos(self, temp_dir):
        """Test listing available demos."""
        project = self._create_mock_project(temp_dir)

        # Create demo files
        demos_dir = temp_dir / "content" / "en" / "demos"
        demos_dir.mkdir(parents=True)
        (demos_dir / "demo-a.yaml").write_text("name: A\nurl: http://a.com")
        (demos_dir / "demo-b.yaml").write_text("name: B\nurl: http://b.com")

        # Shared demos
        shared_dir = temp_dir / "demos"
        shared_dir.mkdir(parents=True)
        (shared_dir / "shared-demo.yaml").write_text("name: Shared\nurl: http://shared.com")

        registry = DemoRegistry(project)
        demos = registry.list_demos("en")

        assert "demo-a" in demos
        assert "demo-b" in demos
        assert "shared-demo" in demos
        assert len(demos) == 3

    def test_demo_registry_list_demos_empty(self, temp_dir):
        """Test listing demos when none exist."""
        project = self._create_mock_project(temp_dir)
        registry = DemoRegistry(project)

        demos = registry.list_demos("en")
        assert demos == []

    def test_demo_registry_clear_cache(self, temp_dir):
        """Test clearing demo cache."""
        project = self._create_mock_project(temp_dir)

        # Create demo file
        demos_dir = temp_dir / "content" / "en" / "demos"
        demos_dir.mkdir(parents=True)
        demo_path = demos_dir / "cache-test.yaml"
        demo_path.write_text("name: Cache Test\nurl: http://test.com")

        registry = DemoRegistry(project)
        registry.load("cache-test", "en")

        assert len(registry._cache) == 1

        registry.clear_cache()

        assert len(registry._cache) == 0

    def test_demo_registry_load_shared_demos(self, temp_dir):
        """Test loading from shared demos directory."""
        project = self._create_mock_project(temp_dir)

        # Create only shared demo (not language-specific)
        shared_dir = temp_dir / "demos"
        shared_dir.mkdir(parents=True)
        (shared_dir / "shared-only.yaml").write_text("name: Shared Only\nurl: http://shared.com")

        registry = DemoRegistry(project)
        demo = registry.load("shared-only", "en")

        assert demo.name == "Shared Only"

    def test_demo_registry_language_priority(self, temp_dir):
        """Test language-specific demos take priority over shared."""
        project = self._create_mock_project(temp_dir)

        # Create both language-specific and shared
        lang_dir = temp_dir / "content" / "en" / "demos"
        lang_dir.mkdir(parents=True)
        (lang_dir / "priority.yaml").write_text("name: English Version\nurl: http://en.com")

        shared_dir = temp_dir / "demos"
        shared_dir.mkdir(parents=True)
        (shared_dir / "priority.yaml").write_text("name: Shared Version\nurl: http://shared.com")

        registry = DemoRegistry(project)
        demo = registry.load("priority", "en")

        # Should load language-specific version
        assert demo.name == "English Version"

    def _create_mock_project(self, root_dir):
        """Helper to create a mock project."""
        config = Config()
        config.paths.content = "content"
        theme = Theme()

        lang_configs = {"en": LanguageConfig(code="en", name="English")}

        project = Project(
            root=root_dir,
            config=config,
            theme=theme,
            languages=lang_configs,
            source_language="en",
        )

        return project
