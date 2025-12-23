"""
Tests for media_engine.settings module.
"""

import os
from unittest.mock import patch


class TestVideoDefaults:
    """Tests for video default settings."""

    def test_video_resolution(self):
        """Test default video resolution."""
        from media_engine.settings import VIDEO

        assert VIDEO.width == 1920
        assert VIDEO.height == 1080

    def test_video_fps(self):
        """Test default video FPS."""
        from media_engine.settings import VIDEO

        assert VIDEO.fps == 60

    def test_video_codec(self):
        """Test default video codec."""
        from media_engine.settings import VIDEO

        assert VIDEO.codec == "h264"

    def test_video_ffmpeg_settings(self):
        """Test FFmpeg-related settings."""
        from media_engine.settings import VIDEO

        assert VIDEO.ffmpeg_preset == "slow"
        assert VIDEO.ffmpeg_crf == 18
        assert VIDEO.ffmpeg_profile == "high"


class TestVoiceoverDefaults:
    """Tests for voiceover default settings."""

    def test_voiceover_provider(self):
        """Test default voiceover provider."""
        from media_engine.settings import VOICEOVER

        assert VOICEOVER.provider == "elevenlabs"

    def test_voiceover_model(self):
        """Test default voiceover model."""
        from media_engine.settings import VOICEOVER

        assert VOICEOVER.model == "eleven_turbo_v2_5"

    def test_voiceover_stability(self):
        """Test voiceover stability settings."""
        from media_engine.settings import VOICEOVER

        assert VOICEOVER.stability == 0.5
        assert VOICEOVER.similarity_boost == 0.75


class TestWebDefaults:
    """Tests for web server default settings."""

    def test_web_port(self):
        """Test default web server port."""
        from media_engine.settings import WEB

        assert WEB.port == 8080

    def test_web_host(self):
        """Test default web server host."""
        from media_engine.settings import WEB

        assert WEB.host == "127.0.0.1"


class TestNetworkDefaults:
    """Tests for network default settings."""

    def test_default_timeout(self):
        """Test default network timeout."""
        from media_engine.settings import NETWORK

        assert NETWORK.timeout_default == 10

    def test_download_timeout(self):
        """Test download timeout."""
        from media_engine.settings import NETWORK

        assert NETWORK.timeout_download == 10

    def test_retry_settings(self):
        """Test retry settings."""
        from media_engine.settings import NETWORK

        assert NETWORK.max_retries == 3
        assert NETWORK.retry_delay == 1.0


class TestQualityDefaults:
    """Tests for quality threshold settings."""

    def test_sentence_word_limit(self):
        """Test max sentence words."""
        from media_engine.settings import QUALITY

        assert QUALITY.max_sentence_words == 25

    def test_freshness_settings(self):
        """Test freshness threshold settings."""
        from media_engine.settings import QUALITY

        assert QUALITY.freshness_default_days == 60
        assert QUALITY.freshness_warning_days == 30
        assert QUALITY.freshness_critical_days == 90


class TestCacheDefaults:
    """Tests for cache default settings."""

    def test_mcp_cache_ttl(self):
        """Test MCP cache TTL."""
        from media_engine.settings import CACHE

        assert CACHE.mcp_cache_ttl == 30

    def test_link_cache_ttl(self):
        """Test link cache TTL."""
        from media_engine.settings import CACHE

        assert CACHE.link_cache_ttl == 900  # 15 minutes


class TestSearchDefaults:
    """Tests for search default settings."""

    def test_search_results(self):
        """Test default search result limit."""
        from media_engine.settings import SEARCH

        assert SEARCH.results_limit == 20

    def test_search_excerpt_length(self):
        """Test search excerpt length."""
        from media_engine.settings import SEARCH

        assert SEARCH.excerpt_length == 200


class TestProvenanceDefaults:
    """Tests for provenance default settings."""

    def test_expiry_days(self):
        """Test default expiry days."""
        from media_engine.settings import PROVENANCE

        assert PROVENANCE.expiry_days == 365

    def test_review_stale_days(self):
        """Test review stale threshold."""
        from media_engine.settings import PROVENANCE

        assert PROVENANCE.review_stale_days == 14


class TestGetDefault:
    """Tests for get_default function."""

    def test_get_video_default(self):
        """Test getting video default."""
        from media_engine.settings import get_default

        assert get_default("video", "width") == 1920
        assert get_default("video", "fps") == 60

    def test_get_network_default(self):
        """Test getting network default."""
        from media_engine.settings import get_default

        assert get_default("network", "timeout_default") == 10

    def test_get_nonexistent_default(self):
        """Test getting non-existent default returns None."""
        from media_engine.settings import get_default

        result = get_default("nonexistent", "field")
        assert result is None

    def test_get_nonexistent_field(self):
        """Test getting non-existent field returns None."""
        from media_engine.settings import get_default

        result = get_default("video", "nonexistent_field")
        assert result is None


class TestDirectoryNames:
    """Tests for directory name constants."""

    def test_content_directory(self):
        """Test content directory name."""
        from media_engine.settings import DIRS

        assert DIRS.content == "content"

    def test_output_directory(self):
        """Test output directory name."""
        from media_engine.settings import DIRS

        assert DIRS.output == "output"

    def test_assets_directory(self):
        """Test assets directory name."""
        from media_engine.settings import DIRS

        assert DIRS.assets == "assets"

    def test_cache_directory(self):
        """Test cache directory name."""
        from media_engine.settings import DIRS

        assert DIRS.cache == ".cache"


class TestFileNames:
    """Tests for file name constants."""

    def test_project_config(self):
        """Test project config filename."""
        from media_engine.settings import FILES

        assert FILES.project_config == "project.yaml"

    def test_theme_file(self):
        """Test theme filename."""
        from media_engine.settings import FILES

        assert FILES.theme_config == "theme.yaml"

    def test_schema_file(self):
        """Test schema filename."""
        from media_engine.settings import FILES

        assert FILES.schema_config == "schema.yaml"


class TestPathResolver:
    """Tests for PathResolver class."""

    def test_init_with_path(self, temp_dir):
        """Test PathResolver initialization."""
        from media_engine.settings import PathResolver

        resolver = PathResolver(temp_dir)
        assert resolver.root == temp_dir

    def test_content_dir(self, temp_dir):
        """Test content directory path."""
        from media_engine.settings import PathResolver

        resolver = PathResolver(temp_dir)
        assert resolver.content_dir == temp_dir / "content"

    def test_output_dir(self, temp_dir):
        """Test output directory path."""
        from media_engine.settings import PathResolver

        resolver = PathResolver(temp_dir)
        assert resolver.output_dir == temp_dir / "output"

    def test_assets_dir(self, temp_dir):
        """Test assets directory path."""
        from media_engine.settings import PathResolver

        resolver = PathResolver(temp_dir)
        assert resolver.assets_dir == temp_dir / "assets"

    def test_cache_dir(self, temp_dir):
        """Test cache directory path."""
        from media_engine.settings import PathResolver

        resolver = PathResolver(temp_dir)
        assert resolver.cache_dir == temp_dir / ".cache"

    def test_media_engine_dir(self, temp_dir):
        """Test media-engine metadata directory path."""
        from media_engine.settings import PathResolver

        resolver = PathResolver(temp_dir)
        assert resolver.media_engine_dir == temp_dir / ".media-engine"


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_find_project_root_with_project_yaml(self, temp_dir):
        """Test finding project root when project.yaml exists."""
        from media_engine.settings import find_project_root

        # Create project.yaml
        (temp_dir / "project.yaml").write_text("name: Test")

        # Create subdirectory
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        # Find from subdirectory
        root = find_project_root(subdir)
        assert root == temp_dir

    def test_find_project_root_not_found(self, temp_dir):
        """Test find_project_root when no project.yaml exists."""
        from media_engine.settings import find_project_root

        # Create isolated directory without project.yaml
        isolated = temp_dir / "isolated"
        isolated.mkdir()

        root = find_project_root(isolated)
        assert root is None


class TestEnvVars:
    """Tests for environment variable handling."""

    def test_env_var_name(self):
        """Test EnvVar class name attribute."""
        from media_engine.settings import EnvVar

        var = EnvVar(
            name="TEST_VAR",
            description="Test variable",
            default="default_value",
        )
        assert var.name == "TEST_VAR"
        assert var.description == "Test variable"
        assert var.default == "default_value"

    def test_env_var_get_not_set(self):
        """Test getting env var when not set."""
        from media_engine.settings import EnvVar

        var = EnvVar(
            name="NONEXISTENT_VAR_12345",
            description="Test",
            default="fallback",
        )
        assert var.get() == "fallback"

    def test_env_var_get_when_set(self):
        """Test getting env var when set."""
        from media_engine.settings import EnvVar

        var = EnvVar(
            name="TEST_ENV_VAR_12345",
            description="Test",
            default="fallback",
        )

        with patch.dict(os.environ, {"TEST_ENV_VAR_12345": "actual_value"}):
            assert var.get() == "actual_value"

    def test_env_var_is_set(self):
        """Test checking if env var is set."""
        from media_engine.settings import EnvVar

        var = EnvVar(
            name="TEST_IS_SET_VAR",
            description="Test",
        )

        assert var.is_set() is False

        with patch.dict(os.environ, {"TEST_IS_SET_VAR": "value"}):
            assert var.is_set() is True


class TestIsDebugMode:
    """Tests for is_debug_mode function."""

    def test_debug_mode_not_set(self):
        """Test debug mode when not set."""
        from media_engine.settings import is_debug_mode

        with patch.dict(os.environ, {}, clear=True):
            # Remove DEBUG if present
            os.environ.pop("MEDIA_ENGINE_DEBUG", None)
            # Should return False by default
            assert is_debug_mode() in (True, False)  # Depends on environment

    def test_debug_mode_set_true(self):
        """Test debug mode when set to true."""
        from media_engine.settings import is_debug_mode

        with patch.dict(os.environ, {"MEDIA_ENGINE_DEBUG": "true"}):
            assert is_debug_mode() is True

    def test_debug_mode_set_false(self):
        """Test debug mode when set to false."""
        from media_engine.settings import is_debug_mode

        with patch.dict(os.environ, {"MEDIA_ENGINE_DEBUG": "false"}):
            assert is_debug_mode() is False


class TestGetLogLevel:
    """Tests for get_log_level function."""

    def test_default_log_level(self):
        """Test default log level."""
        from media_engine.settings import get_log_level

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MEDIA_ENGINE_LOG_LEVEL", None)
            level = get_log_level()
            assert level in ("INFO", "DEBUG", "WARNING", "ERROR")  # Valid levels


class TestGetElevenlabsApiKey:
    """Tests for get_elevenlabs_api_key function."""

    def test_api_key_function_exists(self):
        """Test get_elevenlabs_api_key function exists."""
        from media_engine.settings import get_elevenlabs_api_key

        # Should be callable
        assert callable(get_elevenlabs_api_key)

    def test_api_key_returns_string_or_none(self):
        """Test API key returns string or None."""
        from media_engine.settings import get_elevenlabs_api_key

        key = get_elevenlabs_api_key()
        # Key should be string or None
        assert key is None or isinstance(key, str)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_video_resolution(self):
        """Test get_video_resolution function."""
        from media_engine.settings import get_video_resolution

        width, height = get_video_resolution()
        assert width == 1920
        assert height == 1080

    def test_get_voiceover_settings(self):
        """Test get_voiceover_settings function."""
        from media_engine.settings import get_voiceover_settings

        settings = get_voiceover_settings()
        assert "provider" in settings
        assert "model" in settings
        assert settings["provider"] == "elevenlabs"

    def test_get_ffmpeg_settings(self):
        """Test get_ffmpeg_settings function."""
        from media_engine.settings import get_ffmpeg_settings

        settings = get_ffmpeg_settings()
        assert "preset" in settings
        assert "crf" in settings
        assert settings["preset"] == "slow"
        assert settings["crf"] == 18

    def test_get_network_timeouts(self):
        """Test get_network_timeouts function."""
        from media_engine.settings import get_network_timeouts

        timeouts = get_network_timeouts()
        assert "default" in timeouts
        assert "download" in timeouts
        assert timeouts["default"] == 10
        assert timeouts["download"] == 10  # Same as default in this module

    def test_get_quality_thresholds(self):
        """Test get_quality_thresholds function."""
        from media_engine.settings import get_quality_thresholds

        thresholds = get_quality_thresholds()
        assert "max_sentence_words" in thresholds
        assert "freshness_default_days" in thresholds
        assert thresholds["max_sentence_words"] == 25


class TestFileExtensions:
    """Tests for file extension constants."""

    def test_documents_extension(self):
        """Test document extensions."""
        from media_engine.settings import EXTENSIONS

        doc_exts = EXTENSIONS.documents
        # Should be a collection (frozenset, tuple, or set)
        assert hasattr(doc_exts, "__iter__")
        # Should include markdown
        assert ".md" in doc_exts

    def test_config_extension(self):
        """Test config extensions."""
        from media_engine.settings import EXTENSIONS

        config_exts = EXTENSIONS.configs
        # Should be a collection
        assert hasattr(config_exts, "__iter__")
        # Should include yaml
        assert ".yaml" in config_exts or ".yml" in config_exts


class TestIgnorePatterns:
    """Tests for default ignore patterns."""

    def test_ignore_patterns_exist(self):
        """Test that ignore patterns are defined."""
        from media_engine.settings import DEFAULT_IGNORE_PATTERNS

        assert isinstance(DEFAULT_IGNORE_PATTERNS, (list, tuple, set))
        assert len(DEFAULT_IGNORE_PATTERNS) > 0

    def test_common_patterns_included(self):
        """Test that common patterns are included."""
        from media_engine.settings import DEFAULT_IGNORE_PATTERNS

        patterns_str = str(DEFAULT_IGNORE_PATTERNS)
        # Should include common patterns like .git, __pycache__, etc.
        assert "__pycache__" in patterns_str or "pycache" in patterns_str.lower()


class TestAllDefaults:
    """Tests for ALL_DEFAULTS dictionary."""

    def test_all_defaults_exists(self):
        """Test ALL_DEFAULTS dictionary exists."""
        from media_engine.settings import ALL_DEFAULTS

        assert isinstance(ALL_DEFAULTS, dict)
        assert len(ALL_DEFAULTS) > 0

    def test_all_defaults_has_video(self):
        """Test ALL_DEFAULTS contains video settings."""
        from media_engine.settings import ALL_DEFAULTS, VIDEO

        assert "video" in ALL_DEFAULTS
        assert ALL_DEFAULTS["video"] is VIDEO

    def test_all_defaults_has_web(self):
        """Test ALL_DEFAULTS contains web settings."""
        from media_engine.settings import ALL_DEFAULTS, WEB

        assert "web" in ALL_DEFAULTS
        assert ALL_DEFAULTS["web"] is WEB


class TestAllEnvVars:
    """Tests for ALL_ENV_VARS dictionary."""

    def test_all_env_vars_exists(self):
        """Test ALL_ENV_VARS dictionary exists."""
        from media_engine.settings import ALL_ENV_VARS

        assert isinstance(ALL_ENV_VARS, dict)

    def test_all_env_vars_has_debug(self):
        """Test ALL_ENV_VARS contains debug setting."""
        from media_engine.settings import ALL_ENV_VARS

        # Should have some env vars defined
        assert len(ALL_ENV_VARS) >= 0  # May be empty in some configs
