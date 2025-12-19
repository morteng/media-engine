"""
Tests for media_engine.core module.
"""

from media_engine.core.config import Config, load_config
from media_engine.core.theme import COPPER_AND_CREAM, Theme, load_theme


class TestConfig:
    """Tests for Config class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        assert config.name == "Untitled Project"
        assert config.voiceover.provider == "elevenlabs"
        assert config.video.width == 1920
        assert config.video.height == 1080
        assert config.video.fps == 60

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "project": {
                "name": "My Project",
                "description": "A description",
            },
            "voiceover": {
                "voice_id": "my-voice",
                "stability": 0.7,
            },
            "video": {
                "width": 3840,
                "height": 2160,
                "fps": 60,
            },
        }
        config = Config.from_dict(data)
        assert config.name == "My Project"
        assert config.description == "A description"
        assert config.voiceover.voice_id == "my-voice"
        assert config.voiceover.stability == 0.7
        assert config.video.width == 3840
        assert config.video.fps == 60

    def test_load_config_from_file(self, sample_config):
        """Test loading config from YAML file."""
        config = load_config(sample_config)
        assert config.name == "Test Project"
        assert config.voiceover.voice_id == "test-voice-id"
        assert config.video.width == 1920

    def test_load_config_missing_file(self, temp_dir):
        """Test loading config when file doesn't exist."""
        config = load_config(temp_dir / "nonexistent.yaml")
        assert config.name == "Untitled Project"  # Default


class TestTheme:
    """Tests for Theme class."""

    def test_default_theme(self):
        """Test default theme values."""
        theme = Theme()
        assert theme.name == "default"
        assert theme.colors.primary == "#000000"
        assert theme.typography.heading == "sans-serif"

    def test_theme_from_dict(self):
        """Test creating theme from dictionary."""
        data = {
            "name": "Custom Theme",
            "colors": {
                "primary": "#ff0000",
                "accent": "#00ff00",
                "dark": {
                    "background": "#111111",
                },
            },
            "typography": {
                "heading": "Georgia",
                "body": "Verdana",
            },
        }
        theme = Theme.from_dict(data)
        assert theme.name == "Custom Theme"
        assert theme.colors.primary == "#ff0000"
        assert theme.colors.accent == "#00ff00"
        assert theme.dark.background == "#111111"
        assert theme.typography.heading == "Georgia"

    def test_load_theme_from_file(self, sample_theme):
        """Test loading theme from YAML file."""
        theme = load_theme(sample_theme)
        assert theme.name == "Test Theme"
        assert theme.colors.primary == "#000000"
        assert theme.colors.accent == "#0066cc"

    def test_get_color_light_mode(self):
        """Test getting color in light mode."""
        theme = COPPER_AND_CREAM
        assert theme.get_color("accent", dark_mode=False) == "#c45c3c"
        assert theme.get_color("background", dark_mode=False) == "#fdfbf9"

    def test_get_color_dark_mode(self):
        """Test getting color in dark mode."""
        theme = COPPER_AND_CREAM
        assert theme.get_color("accent", dark_mode=True) == "#d4775a"
        assert theme.get_color("background", dark_mode=True) == "#1a1816"

    def test_copper_and_cream_preset(self):
        """Test the predefined Copper & Cream theme."""
        theme = COPPER_AND_CREAM
        assert theme.name == "Copper & Cream"
        assert theme.colors.accent == "#c45c3c"
        assert theme.typography.heading == "Fraunces"
        assert theme.typography.body == "Source Sans 3"
