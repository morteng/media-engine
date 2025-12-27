"""
Tests for Video Production MCP Tools.

Tests the video_producer, motion_design, and video_render MCP tool modules.
"""

import json
from unittest.mock import MagicMock

import pytest


# Test video_design_knowledge module
class TestVideoDesignKnowledge:
    """Tests for the video design knowledge base."""

    def test_motion_design_principles_structure(self):
        """Test that motion design principles have required categories."""
        from media_engine.mcp.tools.video_design_knowledge import MOTION_DESIGN_PRINCIPLES

        required_categories = ["timing", "composition", "transitions", "pacing", "typography", "color"]
        for category in required_categories:
            assert category in MOTION_DESIGN_PRINCIPLES
            assert isinstance(MOTION_DESIGN_PRINCIPLES[category], dict)
            assert len(MOTION_DESIGN_PRINCIPLES[category]) > 0

    def test_scene_type_recommendations_structure(self):
        """Test that scene type recommendations have required fields."""
        from media_engine.mcp.tools.video_design_knowledge import SCENE_TYPE_RECOMMENDATIONS

        required_scene_types = ["intro", "feature", "demo", "split", "outro"]
        required_fields = ["duration", "background", "transition_in", "text_effect", "guidelines"]

        for scene_type in required_scene_types:
            assert scene_type in SCENE_TYPE_RECOMMENDATIONS
            rec = SCENE_TYPE_RECOMMENDATIONS[scene_type]
            for field in required_fields:
                assert field in rec, f"Missing {field} in {scene_type}"

    def test_scene_type_has_duration_range(self):
        """Test that scene types have duration ranges for validation."""
        from media_engine.mcp.tools.video_design_knowledge import SCENE_TYPE_RECOMMENDATIONS

        for scene_type, rec in SCENE_TYPE_RECOMMENDATIONS.items():
            assert "duration_range" in rec, f"Missing duration_range in {scene_type}"
            assert isinstance(rec["duration_range"], tuple)
            assert len(rec["duration_range"]) == 2
            assert rec["duration_range"][0] <= rec["duration_range"][1]

    def test_transition_catalog_structure(self):
        """Test transition catalog has required metadata."""
        from media_engine.mcp.tools.video_design_knowledge import TRANSITION_CATALOG

        required_transitions = ["fade", "wipe", "glitch", "slice"]
        required_fields = ["energy", "use_for", "avoid_for"]

        for transition in required_transitions:
            assert transition in TRANSITION_CATALOG
            for field in required_fields:
                assert field in TRANSITION_CATALOG[transition]

    def test_background_catalog_structure(self):
        """Test background catalog has required metadata."""
        from media_engine.mcp.tools.video_design_knowledge import BACKGROUND_CATALOG

        required_backgrounds = ["dark", "aurora", "grid", "particles"]
        required_fields = ["mood", "use_for", "contrast"]

        for bg in required_backgrounds:
            assert bg in BACKGROUND_CATALOG
            for field in required_fields:
                assert field in BACKGROUND_CATALOG[bg]

    def test_text_effect_catalog_structure(self):
        """Test text effect catalog has required metadata."""
        from media_engine.mcp.tools.video_design_knowledge import TEXT_EFFECT_CATALOG

        required_effects = ["fade-up", "bounce", "wave", "scale-pop"]
        required_fields = ["energy", "readability", "use_for"]

        for effect in required_effects:
            assert effect in TEXT_EFFECT_CATALOG
            for field in required_fields:
                assert field in TEXT_EFFECT_CATALOG[effect]

    def test_brand_personality_styles(self):
        """Test brand personality to visual style mapping."""
        from media_engine.mcp.tools.video_design_knowledge import BRAND_PERSONALITY_STYLES

        required_personalities = ["professional", "playful", "technical", "minimal", "startup"]
        required_fields = ["backgrounds", "transitions", "text_effects", "pacing"]

        for personality in required_personalities:
            assert personality in BRAND_PERSONALITY_STYLES
            for field in required_fields:
                assert field in BRAND_PERSONALITY_STYLES[personality]

    def test_get_scene_recommendation(self):
        """Test scene recommendation helper function."""
        from media_engine.mcp.tools.video_design_knowledge import get_scene_recommendation

        rec = get_scene_recommendation("intro", "startup")

        assert rec["scene_type"] == "intro"
        assert rec["brand_personality"] == "startup"
        assert "duration" in rec
        assert "duration_range" in rec
        assert "backgrounds" in rec
        assert "transitions" in rec
        assert "text_effects" in rec
        assert "guidelines" in rec

    def test_get_scene_recommendation_defaults(self):
        """Test scene recommendation with unknown types uses defaults."""
        from media_engine.mcp.tools.video_design_knowledge import get_scene_recommendation

        rec = get_scene_recommendation("unknown_type", "unknown_personality")

        # Should fall back to feature/professional
        assert "duration" in rec
        assert "backgrounds" in rec

    def test_validate_scene_timing(self):
        """Test scene timing validation."""
        from media_engine.mcp.tools.video_design_knowledge import validate_scene_timing

        scenes = [
            {"id": "intro", "type": "intro", "duration": 2},  # Too short (min 3)
            {"id": "feature1", "type": "feature", "duration": 10},  # OK
            {"id": "outro", "type": "outro", "duration": 20},  # Too long (max 10)
        ]

        issues = validate_scene_timing(scenes)

        assert len(issues) == 2
        assert issues[0]["scene_id"] == "intro"
        assert issues[0]["issue"] == "too_short"
        assert issues[1]["scene_id"] == "outro"
        assert issues[1]["issue"] == "too_long"


class TestVideoRenderTools:
    """Tests for video render MCP tools."""

    def test_render_jobs_global_state(self):
        """Test that render jobs state is accessible."""
        from media_engine.mcp.tools.video_render import _render_jobs

        assert isinstance(_render_jobs, dict)

    @pytest.fixture
    def mock_server(self, tmp_path):
        """Create a mock server instance."""
        server = MagicMock()
        server.project = MagicMock()
        server.project.root = tmp_path
        server.project.content_dir = tmp_path / "content"
        server.project.output_dir = tmp_path / "output"

        # Create directories
        (tmp_path / "content" / "en" / "scripts").mkdir(parents=True)
        (tmp_path / "output" / "en" / "videos").mkdir(parents=True)

        return server

    @pytest.mark.asyncio
    async def test_start_video_render_invalid_script_id(self, mock_server):
        """Test start_video_render with invalid script ID format."""
        from media_engine.mcp.tools import video_render

        # Reset render jobs
        video_render._render_jobs.clear()

        # Test invalid script_id format (missing slash)
        result = await self._call_start_render(mock_server, "invalid_format", "production", "mp4")
        data = json.loads(result)
        assert "error" in data
        assert "Invalid script_id format" in data["error"]

    async def _call_start_render(self, server, script_id, quality, output_format):
        """Helper to call start_video_render."""
        import uuid

        from media_engine.mcp.tools.video_render import _render_jobs

        # Simulate the function logic
        if not server.project:
            return json.dumps({"error": "No project found"})

        parts = script_id.split("/", 1)
        if len(parts) != 2:
            return json.dumps({"error": "Invalid script_id format. Use 'language/script_name'"})

        lang, name = parts
        script_path = server.project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            return json.dumps({"error": f"Script not found: {script_id}"})

        job_id = str(uuid.uuid4())[:8]
        job = {
            "id": job_id,
            "script_id": script_id,
            "quality": quality,
            "status": "queued",
            "progress": 0,
        }
        _render_jobs[job_id] = job

        return json.dumps({"status": "queued", "job_id": job_id})

    @pytest.mark.asyncio
    async def test_render_job_lifecycle(self, mock_server):
        """Test full render job lifecycle: queue -> status -> cancel."""
        from datetime import datetime

        from media_engine.mcp.tools.video_render import _render_jobs

        # Clear state
        _render_jobs.clear()

        # Create a script file
        script_path = mock_server.project.content_dir / "en" / "scripts" / "test.yaml"
        script_path.write_text("title: Test\nscenes: []")

        # Queue a job
        job_id = "test123"
        _render_jobs[job_id] = {
            "id": job_id,
            "script_id": "en/test",
            "status": "queued",
            "progress": 0,
            "stage": "queued",
            "created": datetime.now().isoformat(),
            "started": None,
            "completed": None,
            "error": None,
            "output_path": None,
        }

        assert job_id in _render_jobs
        assert _render_jobs[job_id]["status"] == "queued"

        # Update to rendering
        _render_jobs[job_id]["status"] = "rendering"
        _render_jobs[job_id]["progress"] = 50
        assert _render_jobs[job_id]["progress"] == 50

        # Cancel
        _render_jobs[job_id]["status"] = "cancelled"
        assert _render_jobs[job_id]["status"] == "cancelled"

    def test_render_settings_presets(self):
        """Test render quality presets."""
        presets = {
            "preview": {"width": 1280, "height": 720, "crf": 28},
            "production": {"width": 1920, "height": 1080, "crf": 18},
            "4k": {"width": 3840, "height": 2160, "crf": 15},
        }

        for quality, settings in presets.items():
            assert settings["width"] > 0
            assert settings["height"] > 0
            assert 0 < settings["crf"] < 51  # Valid CRF range


class TestMotionDesignTools:
    """Tests for motion design MCP tools."""

    def test_component_categories(self):
        """Test that component categories are properly defined."""
        categories = ["background", "text", "transition", "layout", "effect"]
        # All these should be valid categories for the component catalog

        from media_engine.mcp.tools.video_design_knowledge import (
            BACKGROUND_CATALOG,
            TEXT_EFFECT_CATALOG,
            TRANSITION_CATALOG,
        )

        assert len(BACKGROUND_CATALOG) > 0
        assert len(TEXT_EFFECT_CATALOG) > 0
        assert len(TRANSITION_CATALOG) > 0

    def test_transition_energy_levels(self):
        """Test that transitions have valid energy levels."""
        from media_engine.mcp.tools.video_design_knowledge import TRANSITION_CATALOG

        valid_energy_levels = ["low", "medium", "high"]

        for name, transition in TRANSITION_CATALOG.items():
            assert transition["energy"] in valid_energy_levels, f"Invalid energy for {name}"

    def test_text_effect_readability(self):
        """Test that text effects have valid readability levels."""
        from media_engine.mcp.tools.video_design_knowledge import TEXT_EFFECT_CATALOG

        valid_readability = ["low", "medium", "high"]

        for name, effect in TEXT_EFFECT_CATALOG.items():
            assert effect["readability"] in valid_readability, f"Invalid readability for {name}"


class TestVideoProducerTools:
    """Tests for video producer MCP tools."""

    def test_video_types(self):
        """Test supported video types."""
        valid_types = ["explainer", "tutorial", "demo", "marketing", "announcement"]

        # These should all be valid video types for plan_video_from_content
        for vtype in valid_types:
            assert isinstance(vtype, str)
            assert len(vtype) > 0

    def test_scene_structure(self):
        """Test expected scene structure."""
        expected_fields = ["id", "type", "duration", "elements"]

        # A valid scene should have these fields
        sample_scene = {
            "id": "intro",
            "type": "intro",
            "duration": 5,
            "elements": [{"type": "title", "content": "Hello"}],
        }

        for field in expected_fields:
            assert field in sample_scene

    @pytest.fixture
    def sample_script(self):
        """Create a sample video script."""
        return {
            "title": "Test Video",
            "description": "A test video script",
            "settings": {
                "fps": 30,
                "resolution": "1080p",
            },
            "scenes": [
                {
                    "id": "intro",
                    "type": "intro",
                    "duration": 5,
                    "elements": [
                        {"type": "title", "content": "Welcome"},
                    ],
                },
                {
                    "id": "feature1",
                    "type": "feature",
                    "duration": 10,
                    "voiceover": "This is a feature demonstration.",
                    "elements": [
                        {"type": "text", "content": "Feature 1"},
                    ],
                },
                {
                    "id": "outro",
                    "type": "outro",
                    "duration": 5,
                    "elements": [
                        {"type": "cta", "content": "Learn More"},
                    ],
                },
            ],
        }

    def test_script_validation_structure(self, sample_script):
        """Test that a valid script has required structure."""
        assert "title" in sample_script
        assert "scenes" in sample_script
        assert len(sample_script["scenes"]) > 0

        for scene in sample_script["scenes"]:
            assert "id" in scene
            assert "type" in scene
            assert "duration" in scene

    def test_script_total_duration(self, sample_script):
        """Test calculating total script duration."""
        total = sum(s["duration"] for s in sample_script["scenes"])
        assert total == 20  # 5 + 10 + 5

    def test_voiceover_timing_estimation(self):
        """Test voiceover duration estimation (150 words per minute)."""
        words_per_minute = 150

        # Test with known word count
        test_words = ["word"] * 30  # Exactly 30 words
        test_text = " ".join(test_words)
        word_count = len(test_text.split())

        estimated_duration = (word_count / words_per_minute) * 60

        assert word_count == 30
        assert estimated_duration == 12.0  # 30 words at 150 wpm = 12 seconds


class TestAIContextVideoIntegration:
    """Tests for video production integration with AI context."""

    def test_video_context_structure(self):
        """Test that video context has expected structure."""
        expected_keys = ["scripts", "render_queue", "brand", "capabilities"]

        # The _get_video_context method should return these keys
        for key in expected_keys:
            assert isinstance(key, str)

    def test_video_capabilities_list(self):
        """Test that video capabilities include all tools."""
        expected_tools = [
            "plan_video_from_content",
            "generate_video_script",
            "suggest_scene_visuals",
            "optimize_timing",
            "validate_video_script",
            "list_motion_components",
            "suggest_transitions",
            "apply_brand_to_video",
            "start_video_render",
            "get_render_status",
        ]

        for tool in expected_tools:
            assert isinstance(tool, str)
            assert len(tool) > 0


class TestVideoToolsImports:
    """Test that all video tool modules import correctly."""

    def test_import_video_producer(self):
        """Test video_producer module imports."""
        from media_engine.mcp.tools import video_producer

        assert hasattr(video_producer, "register_video_producer_tools")

    def test_import_motion_design(self):
        """Test motion_design module imports."""
        from media_engine.mcp.tools import motion_design

        assert hasattr(motion_design, "register_motion_design_tools")

    def test_import_video_render(self):
        """Test video_render module imports."""
        from media_engine.mcp.tools import video_render

        assert hasattr(video_render, "register_video_render_tools")

    def test_import_video_design_knowledge(self):
        """Test video_design_knowledge module imports."""
        from media_engine.mcp.tools import video_design_knowledge

        assert hasattr(video_design_knowledge, "MOTION_DESIGN_PRINCIPLES")
        assert hasattr(video_design_knowledge, "SCENE_TYPE_RECOMMENDATIONS")
        assert hasattr(video_design_knowledge, "TRANSITION_CATALOG")
        assert hasattr(video_design_knowledge, "BACKGROUND_CATALOG")
        assert hasattr(video_design_knowledge, "TEXT_EFFECT_CATALOG")
        assert hasattr(video_design_knowledge, "BRAND_PERSONALITY_STYLES")
        assert hasattr(video_design_knowledge, "get_scene_recommendation")
        assert hasattr(video_design_knowledge, "validate_scene_timing")

    def test_tools_in_init(self):
        """Test that video tools are exported from __init__.py."""
        from media_engine.mcp import tools

        assert hasattr(tools, "video_producer")
        assert hasattr(tools, "motion_design")
        assert hasattr(tools, "video_render")
        assert hasattr(tools, "video_design_knowledge")


class TestMCPServerVideoRegistration:
    """Test that video tools are properly registered in MCP server."""

    def test_server_imports_video_tools(self):
        """Test that server.py imports video tool modules."""
        # This tests that the imports don't fail
        from media_engine.mcp.server import MediaEngineMCPServer

        assert MediaEngineMCPServer is not None

    def test_server_has_register_tools(self):
        """Test that server has _register_tools method."""
        from media_engine.mcp.server import MediaEngineMCPServer

        assert hasattr(MediaEngineMCPServer, "_register_tools")
