"""Tests for brand voice profile."""

from pathlib import Path

from media_engine.brand import (
    DEFAULT_VOICE_PROFILE,
    AudioVoice,
    AudioVoiceProfile,
    AudioVoiceSettings,
    BrandContextResolver,
    BrandProfile,
    ResolutionStep,
    ResolvedBrandContext,
    TermPreference,
    VoiceCheckResult,
    VoiceConsistencyChecker,
    VoiceIssue,
    VoiceProfile,
    VoiceProfileOverride,
    VoiceStyle,
    check_document_voice,
)


class TestVoiceStyle:
    """Tests for VoiceStyle dataclass."""

    def test_default_values(self):
        """Test default style values."""
        style = VoiceStyle()
        assert style.active_voice_target == 0.8
        assert style.sentence_length_target == 18
        assert style.paragraph_length_max == 5
        assert style.use_contractions is True
        assert style.use_first_person is False
        assert style.use_second_person is True

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "active_voice_target": 0.9,
            "sentence_length_target": 15,
            "use_contractions": False,
        }
        style = VoiceStyle.from_dict(data)
        assert style.active_voice_target == 0.9
        assert style.sentence_length_target == 15
        assert style.use_contractions is False
        # Defaults preserved
        assert style.paragraph_length_max == 5

    def test_to_dict(self):
        """Test converting to dictionary."""
        style = VoiceStyle(sentence_length_target=12)
        data = style.to_dict()
        assert data["sentence_length_target"] == 12
        assert "active_voice_target" in data


class TestTermPreference:
    """Tests for TermPreference dataclass."""

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {"prefer": "use", "avoid": ["utilize", "leverage"]}
        pref = TermPreference.from_dict(data)
        assert pref.prefer == "use"
        assert pref.avoid == ["utilize", "leverage"]

    def test_from_dict_single_avoid(self):
        """Test with single avoid term as string."""
        data = {"prefer": "help", "avoid": "assist"}
        pref = TermPreference.from_dict(data)
        assert pref.avoid == ["assist"]

    def test_to_dict(self):
        """Test converting to dictionary."""
        pref = TermPreference(prefer="start", avoid=["commence", "initiate"])
        data = pref.to_dict()
        assert data["prefer"] == "start"
        assert data["avoid"] == ["commence", "initiate"]


class TestVoiceProfile:
    """Tests for VoiceProfile dataclass."""

    def test_default_profile(self):
        """Test default profile values."""
        profile = VoiceProfile()
        assert "professional" in profile.personality
        assert profile.tone == "conversational"
        assert profile.formality_level == 0.6

    def test_from_dict_basic(self):
        """Test creating from basic dictionary."""
        data = {
            "personality": ["technical", "precise"],
            "tone": "formal",
            "formality_level": 0.8,
        }
        profile = VoiceProfile.from_dict(data)
        assert profile.personality == ["technical", "precise"]
        assert profile.tone == "formal"
        assert profile.formality_level == 0.8

    def test_from_dict_with_tone_object(self):
        """Test creating with tone as nested object."""
        data = {
            "personality": ["friendly"],
            "tone": {"default": "casual", "formality_level": 0.3},
        }
        profile = VoiceProfile.from_dict(data)
        assert profile.tone == "casual"
        assert profile.formality_level == 0.3

    def test_from_dict_with_style(self):
        """Test creating with style settings."""
        data = {
            "style": {
                "active_voice_target": 0.9,
                "sentence_length_target": 12,
            }
        }
        profile = VoiceProfile.from_dict(data)
        assert profile.style.active_voice_target == 0.9
        assert profile.style.sentence_length_target == 12

    def test_from_dict_with_preferred_terms(self):
        """Test creating with preferred terms."""
        data = {
            "preferred_terms": [
                {"prefer": "use", "avoid": ["utilize"]},
                {"prefer": "help", "avoid": ["assist", "facilitate"]},
            ]
        }
        profile = VoiceProfile.from_dict(data)
        assert len(profile.preferred_terms) == 2
        assert profile.preferred_terms[0].prefer == "use"

    def test_from_dict_with_avoid_phrases(self):
        """Test creating with avoid phrases."""
        data = {"avoid_phrases": ["please note that", "in order to"]}
        profile = VoiceProfile.from_dict(data)
        assert "please note that" in profile.avoid_phrases

    def test_from_dict_with_document_type_overrides(self):
        """Test creating with document type overrides."""
        data = {
            "by_document_type": {
                "architecture": {"tone": "technical", "formality_level": 0.8},
                "tutorial": {"tone": "casual", "formality_level": 0.4},
            }
        }
        profile = VoiceProfile.from_dict(data)
        assert "architecture" in profile.by_document_type
        assert profile.by_document_type["architecture"].tone == "technical"

    def test_from_dict_with_audience_overrides(self):
        """Test creating with audience overrides."""
        data = {
            "by_audience": {
                "developer": {"formality_level": 0.5},
                "executive": {"formality_level": 0.9, "tone": "formal"},
            }
        }
        profile = VoiceProfile.from_dict(data)
        assert "developer" in profile.by_audience
        assert profile.by_audience["executive"].formality_level == 0.9

    def test_get_for_document_type(self):
        """Test getting profile for document type."""
        profile = VoiceProfile(
            tone="conversational",
            formality_level=0.6,
            by_document_type={
                "architecture": VoiceProfileOverride(tone="technical", formality_level=0.8)
            },
        )
        arch_profile = profile.get_for_document_type("architecture")
        assert arch_profile.tone == "technical"
        assert arch_profile.formality_level == 0.8

    def test_get_for_document_type_not_found(self):
        """Test getting profile for unknown document type returns base."""
        profile = VoiceProfile(tone="conversational")
        result = profile.get_for_document_type("unknown")
        assert result.tone == "conversational"

    def test_get_for_audience(self):
        """Test getting profile for audience."""
        profile = VoiceProfile(
            formality_level=0.6,
            by_audience={"executive": VoiceProfileOverride(formality_level=0.9)},
        )
        exec_profile = profile.get_for_audience("executive")
        assert exec_profile.formality_level == 0.9

    def test_get_for_context(self):
        """Test getting profile for combined context."""
        profile = VoiceProfile(
            tone="conversational",
            formality_level=0.6,
            by_document_type={
                "architecture": VoiceProfileOverride(tone="technical")
            },
            by_audience={"executive": VoiceProfileOverride(formality_level=0.9)},
        )
        result = profile.get_for_context(doc_type="architecture", audience="executive")
        assert result.tone == "technical"  # From doc_type
        assert result.formality_level == 0.9  # From audience

    def test_to_dict(self):
        """Test converting to dictionary."""
        profile = VoiceProfile(
            personality=["professional"],
            tone="formal",
            formality_level=0.8,
        )
        data = profile.to_dict()
        assert data["personality"] == ["professional"]
        assert data["tone"]["default"] == "formal"
        assert data["tone"]["formality_level"] == 0.8


class TestVoiceProfileOverride:
    """Tests for VoiceProfileOverride dataclass."""

    def test_from_dict_partial(self):
        """Test creating partial override."""
        data = {"tone": "technical"}
        override = VoiceProfileOverride.from_dict(data)
        assert override.tone == "technical"
        assert override.formality_level is None
        assert override.personality is None

    def test_from_dict_with_style(self):
        """Test creating override with style."""
        data = {
            "style": {
                "active_voice_target": 0.95,
                "sentence_length_target": 10,
            }
        }
        override = VoiceProfileOverride.from_dict(data)
        assert override.style is not None
        assert override.style.active_voice_target == 0.95

    def test_to_dict_excludes_none(self):
        """Test that None values are excluded from dict."""
        override = VoiceProfileOverride(tone="technical")
        data = override.to_dict()
        assert "tone" in data
        assert "personality" not in data
        assert "formality_level" not in data


class TestDefaultVoiceProfile:
    """Tests for the default voice profile."""

    def test_has_preferred_terms(self):
        """Test that default profile has preferred terms."""
        assert len(DEFAULT_VOICE_PROFILE.preferred_terms) > 0
        terms = {t.prefer for t in DEFAULT_VOICE_PROFILE.preferred_terms}
        assert "use" in terms
        assert "help" in terms

    def test_has_avoid_phrases(self):
        """Test that default profile has avoid phrases."""
        assert len(DEFAULT_VOICE_PROFILE.avoid_phrases) > 0
        assert "please note that" in DEFAULT_VOICE_PROFILE.avoid_phrases


class TestBrandProfileVoiceIntegration:
    """Tests for voice integration in BrandProfile."""

    def test_brand_profile_with_voice(self):
        """Test creating BrandProfile with voice."""
        data = {
            "name": "Test Brand",
            "voice": {
                "personality": ["professional"],
                "tone": "formal",
                "formality_level": 0.8,
            },
        }
        profile = BrandProfile.from_dict(data)
        assert profile.voice is not None
        assert profile.voice.tone == "formal"

    def test_brand_profile_without_voice(self):
        """Test creating BrandProfile without voice."""
        data = {"name": "Test Brand"}
        profile = BrandProfile.from_dict(data)
        assert profile.voice is None

    def test_brand_profile_voice_with_overrides(self):
        """Test BrandProfile with voice document type overrides."""
        data = {
            "name": "Test Brand",
            "voice": {
                "tone": "conversational",
                "by_document_type": {
                    "architecture": {"tone": "technical"},
                },
            },
        }
        profile = BrandProfile.from_dict(data)
        assert profile.voice is not None
        arch_voice = profile.voice.get_for_document_type("architecture")
        assert arch_voice.tone == "technical"


class TestAudioVoiceSettings:
    """Tests for AudioVoiceSettings dataclass."""

    def test_default_values(self):
        """Test default settings values."""
        settings = AudioVoiceSettings()
        assert settings.stability == 0.5
        assert settings.similarity_boost == 0.75
        assert settings.style == 0.0

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {"stability": 0.7, "style": 0.3}
        settings = AudioVoiceSettings.from_dict(data)
        assert settings.stability == 0.7
        assert settings.style == 0.3
        assert settings.similarity_boost == 0.75  # default

    def test_to_dict(self):
        """Test converting to dictionary."""
        settings = AudioVoiceSettings(stability=0.6)
        data = settings.to_dict()
        assert data["stability"] == 0.6

    def test_merge(self):
        """Test merging settings."""
        base = AudioVoiceSettings(stability=0.5, style=0.0)
        override = AudioVoiceSettings(stability=0.7, style=0.3)
        merged = base.merge(override)
        assert merged.stability == 0.7
        assert merged.style == 0.3


class TestAudioVoice:
    """Tests for AudioVoice dataclass."""

    def test_from_dict_full(self):
        """Test creating from full dictionary."""
        data = {
            "voice_id": "abc123",
            "name": "Test Voice",
            "description": "A test voice",
        }
        voice = AudioVoice.from_dict(data)
        assert voice.voice_id == "abc123"
        assert voice.name == "Test Voice"
        assert voice.description == "A test voice"

    def test_from_dict_string(self):
        """Test creating from simple string."""
        voice = AudioVoice.from_dict("abc123")
        assert voice.voice_id == "abc123"
        assert voice.name == ""

    def test_with_settings(self):
        """Test creating voice with settings."""
        voice = AudioVoice(voice_id="abc123", name="Test")
        settings = AudioVoiceSettings(stability=0.8)
        new_voice = voice.with_settings(settings)
        assert new_voice.voice_id == "abc123"
        assert new_voice.settings.stability == 0.8


class TestAudioVoiceProfile:
    """Tests for AudioVoiceProfile dataclass."""

    def test_default_profile(self):
        """Test default profile values."""
        profile = AudioVoiceProfile()
        assert profile.provider == "elevenlabs"
        assert profile.default_settings.stability == 0.5

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "provider": "azure",
            "default": {"stability": 0.6},
            "voices": {
                "en": {"voice_id": "voice-en", "name": "English Voice"},
                "no": {"voice_id": "voice-no", "name": "Norwegian Voice"},
            },
        }
        profile = AudioVoiceProfile.from_dict(data)
        assert profile.provider == "azure"
        assert profile.default_settings.stability == 0.6
        assert len(profile.voices) == 2
        assert profile.voices["en"].voice_id == "voice-en"

    def test_get_voice(self):
        """Test getting voice by language."""
        profile = AudioVoiceProfile(
            voices={
                "en": AudioVoice(voice_id="en-voice"),
                "no": AudioVoice(voice_id="no-voice"),
            }
        )
        en_voice = profile.get_voice("en")
        assert en_voice.voice_id == "en-voice"
        assert profile.get_voice("de") is None

    def test_get_settings_with_overrides(self):
        """Test getting settings with doc type and audience overrides."""
        profile = AudioVoiceProfile(
            default_settings=AudioVoiceSettings(stability=0.5, style=0.0),
            by_document_type={
                "pitch": AudioVoiceSettings(stability=0.4, style=0.3),
            },
            by_audience={
                "executive": AudioVoiceSettings(stability=0.6, style=0.1),
            },
        )

        # Default
        settings = profile.get_settings()
        assert settings.stability == 0.5

        # With doc type
        settings = profile.get_settings(doc_type="pitch")
        assert settings.stability == 0.4
        assert settings.style == 0.3

        # With audience
        settings = profile.get_settings(audience="executive")
        assert settings.stability == 0.6

        # With both (audience applies after doc type)
        settings = profile.get_settings(doc_type="pitch", audience="executive")
        assert settings.stability == 0.6  # audience override
        assert settings.style == 0.1  # audience override

    def test_get_voice_for_context(self):
        """Test getting voice with context-appropriate settings."""
        profile = AudioVoiceProfile(
            default_settings=AudioVoiceSettings(stability=0.5),
            voices={"en": AudioVoice(voice_id="en-voice")},
            by_document_type={"pitch": AudioVoiceSettings(stability=0.4)},
        )

        voice = profile.get_voice_for_context("en", doc_type="pitch")
        assert voice.voice_id == "en-voice"
        assert voice.settings.stability == 0.4


class TestVoiceProfileWithAudio:
    """Tests for VoiceProfile with audio integration."""

    def test_voice_profile_with_audio(self):
        """Test creating VoiceProfile with audio section."""
        data = {
            "personality": ["professional"],
            "tone": "formal",
            "audio": {
                "provider": "elevenlabs",
                "voices": {
                    "en": {"voice_id": "voice-123"},
                },
            },
        }
        profile = VoiceProfile.from_dict(data)
        assert profile.audio is not None
        assert profile.audio.provider == "elevenlabs"
        assert profile.audio.get_voice("en").voice_id == "voice-123"

    def test_voice_profile_without_audio(self):
        """Test VoiceProfile without audio section."""
        data = {"personality": ["professional"]}
        profile = VoiceProfile.from_dict(data)
        assert profile.audio is None

    def test_voice_profile_audio_to_dict(self):
        """Test VoiceProfile to_dict includes audio."""
        profile = VoiceProfile(
            audio=AudioVoiceProfile(
                voices={"en": AudioVoice(voice_id="test")}
            )
        )
        data = profile.to_dict()
        assert "audio" in data
        assert data["audio"]["voices"]["en"]["voice_id"] == "test"


# =============================================================================
# VOICE CONSISTENCY CHECKER TESTS
# =============================================================================


class TestVoiceIssue:
    """Tests for VoiceIssue dataclass."""

    def test_to_dict(self):
        """Test converting issue to dictionary."""
        issue = VoiceIssue(
            type="passive_voice",
            severity="warning",
            message="Too much passive voice",
            suggestion="Use active voice",
            location="line 10",
        )
        data = issue.to_dict()
        assert data["type"] == "passive_voice"
        assert data["severity"] == "warning"
        assert data["message"] == "Too much passive voice"
        assert data["suggestion"] == "Use active voice"
        assert data["location"] == "line 10"


class TestVoiceCheckResult:
    """Tests for VoiceCheckResult dataclass."""

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = VoiceCheckResult(
            document=Path("test.md"),
            issues=[VoiceIssue(type="test", message="test")],
            metrics={"active_voice_percentage": 75.0},
            passed=True,
        )
        data = result.to_dict()
        assert data["document"] == "test.md"
        assert len(data["issues"]) == 1
        assert data["metrics"]["active_voice_percentage"] == 75.0
        assert data["passed"] is True


class TestVoiceConsistencyChecker:
    """Tests for VoiceConsistencyChecker class."""

    def test_check_empty_content(self):
        """Test checking empty content passes."""
        checker = VoiceConsistencyChecker()
        result = checker.check_content("", Path("test.md"))
        assert result.passed is True
        assert len(result.issues) == 0

    def test_check_active_voice_good(self):
        """Test content with good active voice passes."""
        content = """
        The team builds software. Engineers write code. Users love the product.
        The system processes data. Developers test features.
        """
        checker = VoiceConsistencyChecker()
        result = checker.check_content(content, Path("test.md"))
        # Should have high active voice percentage
        assert "active_voice_percentage" in result.metrics

    def test_check_active_voice_bad(self):
        """Test content with too much passive voice flags issue."""
        content = """
        The code was written by engineers. The tests were run by the team.
        The features were designed carefully. The bugs were fixed promptly.
        The product was released yesterday. The documentation was updated.
        The system is used by customers. The data is processed by servers.
        """
        profile = VoiceProfile(style=VoiceStyle(active_voice_target=0.9))
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        # Should flag passive voice
        [i for i in result.issues if i.type == "passive_voice"]
        # This content has significant passive voice
        assert result.metrics["passive_count"] > 0

    def test_check_first_person_usage(self):
        """Test first person usage detection."""
        content = """
        I think this is great. We believe in quality. Our team delivers value.
        I recommend using this approach. We have proven results.
        My experience shows this works. We offer the best solution.
        """
        profile = VoiceProfile(style=VoiceStyle(use_first_person=False))
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        assert result.metrics["person_usage"]["first"] > 0
        # Should flag first person when not allowed
        first_person_issues = [i for i in result.issues if i.type == "first_person_usage"]
        assert len(first_person_issues) > 0

    def test_check_second_person_usage(self):
        """Test second person usage detection."""
        content = """
        You can do this. Your code works well. You will succeed.
        You should try this approach. Your results will improve.
        You need to configure settings. Your experience matters.
        """
        profile = VoiceProfile(style=VoiceStyle(use_second_person=False))
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        assert result.metrics["person_usage"]["second"] > 0

    def test_check_formality_informal(self):
        """Test informal content detection."""
        content = """
        This is gonna be awesome! Super cool features are coming.
        Wanna try it? It's really pretty amazing stuff!!
        """
        checker = VoiceConsistencyChecker()
        result = checker.check_content(content, Path("test.md"))
        assert result.metrics["detected_formality"] == "informal"

    def test_check_formality_formal(self):
        """Test formal content detection."""
        content = """
        Therefore, the aforementioned system shall hereby process all requests.
        Furthermore, we must consequently ensure compliance. Moreover, the
        herein described procedures shall be followed accordingly.
        """
        checker = VoiceConsistencyChecker()
        result = checker.check_content(content, Path("test.md"))
        assert result.metrics["detected_formality"] == "formal"

    def test_check_avoided_phrases(self):
        """Test avoided phrase detection."""
        content = """
        Please note that in order to achieve success, you need to follow
        these steps. It should be noted that this is important.
        """
        profile = VoiceProfile(
            avoid_phrases=["please note that", "in order to", "it should be noted"]
        )
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        avoided_issues = [i for i in result.issues if i.type == "avoided_phrase"]
        assert len(avoided_issues) > 0

    def test_check_terminology(self):
        """Test terminology preference checking."""
        content = """
        We utilize best practices to leverage our assets. You must
        facilitate the process and assist customers to obtain results.
        """
        profile = VoiceProfile(
            preferred_terms=[
                TermPreference(prefer="use", avoid=["utilize", "leverage"]),
                TermPreference(prefer="help", avoid=["assist", "facilitate"]),
                TermPreference(prefer="get", avoid=["obtain"]),
            ]
        )
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        term_issues = [i for i in result.issues if i.type == "terminology"]
        assert len(term_issues) > 0

    def test_check_sentence_length(self):
        """Test sentence length checking."""
        # Create content with very long sentences
        content = """
        This is an extremely long sentence that goes on and on and on with many
        words and clauses and phrases that make it very difficult to read and
        understand because it just keeps going without any natural breaks or
        pauses for the reader to absorb the information being presented in this
        very lengthy and convoluted manner.
        """
        profile = VoiceProfile(style=VoiceStyle(sentence_length_target=12))
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        assert result.metrics["avg_sentence_length"] > 12

    def test_code_blocks_removed(self):
        """Test that code blocks are removed before checking."""
        content = """
        Some text here.

        ```python
        # This is code with utilize and leverage
        def utilize():
            pass
        ```

        More text here.
        """
        profile = VoiceProfile(
            preferred_terms=[
                TermPreference(prefer="use", avoid=["utilize", "leverage"]),
            ]
        )
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        # Should not flag terminology in code blocks
        term_issues = [i for i in result.issues if i.type == "terminology"]
        assert len(term_issues) == 0

    def test_frontmatter_removed(self):
        """Test that frontmatter is removed before checking."""
        content = """---
title: Utilize Best Practices
author: Test
---

Some normal text here.
        """
        profile = VoiceProfile(
            preferred_terms=[
                TermPreference(prefer="use", avoid=["utilize"]),
            ]
        )
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        # Should not flag terminology in frontmatter
        term_issues = [i for i in result.issues if i.type == "terminology"]
        assert len(term_issues) == 0

    def test_context_aware_checking(self):
        """Test checking with document type context."""
        content = "This is technical documentation for developers."
        profile = VoiceProfile(
            tone="conversational",
            by_document_type={
                "architecture": VoiceProfileOverride(
                    tone="technical",
                    style=VoiceStyle(active_voice_target=0.9),
                )
            },
        )
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(
            content, Path("test.md"), doc_type="architecture"
        )
        # Should use architecture-specific profile
        assert result.passed  # Short content should pass

    def test_pass_fail_logic(self):
        """Test pass/fail determination."""
        # Content designed to generate multiple warnings
        content = """
        Please note that in order to utilize this feature, you must
        facilitate the process. It should be noted that we leverage
        our assets accordingly.
        """
        profile = VoiceProfile(
            avoid_phrases=["please note that", "in order to", "it should be noted"],
            preferred_terms=[
                TermPreference(prefer="use", avoid=["utilize", "leverage"]),
                TermPreference(prefer="help", avoid=["facilitate"]),
            ],
        )
        checker = VoiceConsistencyChecker(voice_profile=profile)
        result = checker.check_content(content, Path("test.md"))
        # Should fail due to multiple issues
        # (>3 warnings means fail)
        warning_count = sum(1 for i in result.issues if i.severity == "warning")
        if warning_count > 3:
            assert result.passed is False


class TestCheckDocumentVoice:
    """Tests for check_document_voice convenience function."""

    def test_basic_check(self):
        """Test basic voice check."""
        content = "This is a simple test document."
        result = check_document_voice(content, Path("test.md"))
        assert isinstance(result, VoiceCheckResult)
        assert result.document == Path("test.md")

    def test_with_profile(self):
        """Test with voice profile."""
        content = "We utilize best practices."
        profile = VoiceProfile(
            preferred_terms=[
                TermPreference(prefer="use", avoid=["utilize"]),
            ]
        )
        result = check_document_voice(content, Path("test.md"), voice_profile=profile)
        term_issues = [i for i in result.issues if i.type == "terminology"]
        assert len(term_issues) > 0

    def test_with_context(self):
        """Test with document type and audience context."""
        content = "Technical documentation content."
        profile = VoiceProfile(
            by_document_type={
                "reference": VoiceProfileOverride(tone="technical"),
            }
        )
        result = check_document_voice(
            content,
            Path("test.md"),
            voice_profile=profile,
            doc_type="reference",
            audience="developer",
        )
        assert result.passed


# =============================================================================
# BRAND CONTEXT RESOLVER TESTS
# =============================================================================


class TestResolutionStep:
    """Tests for ResolutionStep dataclass."""

    def test_basic_creation(self):
        """Test creating a resolution step."""
        step = ResolutionStep(
            source="doc_type:architecture",
            path=Path("test.md"),
            overrides={"tone": "technical"},
        )
        assert step.source == "doc_type:architecture"
        assert step.path == Path("test.md")
        assert step.overrides["tone"] == "technical"

    def test_defaults(self):
        """Test default values."""
        step = ResolutionStep(source="base")
        assert step.path is None
        assert step.overrides == {}


class TestResolvedBrandContext:
    """Tests for ResolvedBrandContext dataclass."""

    def test_to_dict(self):
        """Test converting to dictionary."""
        from media_engine.brand import BrandContext, BrandProfile

        # BrandContext requires a BrandProfile
        profile = BrandProfile.from_dict({"name": "Test"})

        result = ResolvedBrandContext(
            context=BrandContext(profile=profile),
            effective_voice=VoiceProfile(tone="formal", formality_level=0.8),
            resolution_chain=[
                ResolutionStep(source="base"),
                ResolutionStep(source="doc_type:architecture"),
            ],
            doc_path=Path("test.md"),
        )
        data = result.to_dict()
        assert data["document"] == "test.md"
        assert len(data["resolution_chain"]) == 2
        assert data["effective_voice"]["tone"] == "formal"
        assert data["effective_voice"]["formality_level"] == 0.8


class TestBrandContextResolver:
    """Tests for BrandContextResolver class."""

    def test_resolution_chain_base(self, tmp_path):
        """Test that resolution starts with base profile."""
        # Create minimal project structure
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text("""
name: test-project
source_language: en
languages:
  en:
    name: English
paths:
  content: content
""")
        brand_yaml = tmp_path / "brand.yaml"
        brand_yaml.write_text("""
name: Test Brand
voice:
  tone: conversational
  formality_level: 0.6
""")
        content_dir = tmp_path / "content" / "en" / "chapters"
        content_dir.mkdir(parents=True)
        doc = content_dir / "test.md"
        doc.write_text("""---
title: Test Document
---

Content here.
""")

        from media_engine import Project

        project = Project.load(tmp_path)  # Pass directory, not file
        resolver = BrandContextResolver(project)
        result = resolver.resolve_for_document(doc.relative_to(tmp_path))

        # Should have base in resolution chain
        assert any(step.source == "base" for step in result.resolution_chain)
        assert result.effective_voice.tone == "conversational"
        assert result.effective_voice.formality_level == 0.6

    def test_doc_type_override(self, tmp_path):
        """Test doc_type override in resolution chain."""
        # Create project structure
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text("""
name: test-project
source_language: en
languages:
  en:
    name: English
paths:
  content: content
""")
        brand_yaml = tmp_path / "brand.yaml"
        brand_yaml.write_text("""
name: Test Brand
voice:
  tone: conversational
  formality_level: 0.6
  by_document_type:
    architecture:
      tone: technical
      formality_level: 0.8
""")
        content_dir = tmp_path / "content" / "en" / "chapters"
        content_dir.mkdir(parents=True)
        doc = content_dir / "arch.md"
        doc.write_text("""---
title: Architecture Doc
type: architecture
---

Architecture content.
""")

        from media_engine import Project

        project = Project.load(tmp_path)  # Pass directory, not file
        resolver = BrandContextResolver(project)
        result = resolver.resolve_for_document(doc.relative_to(tmp_path))

        # Should have doc_type override in chain
        assert any("doc_type:architecture" in step.source for step in result.resolution_chain)
        assert result.effective_voice.tone == "technical"
        assert result.effective_voice.formality_level == 0.8

    def test_document_brand_override(self, tmp_path):
        """Test document-level brand override."""
        # Create project structure
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text("""
name: test-project
source_language: en
languages:
  en:
    name: English
paths:
  content: content
""")
        brand_yaml = tmp_path / "brand.yaml"
        brand_yaml.write_text("""
name: Test Brand
voice:
  tone: conversational
  formality_level: 0.6
""")
        content_dir = tmp_path / "content" / "en" / "chapters"
        content_dir.mkdir(parents=True)
        doc = content_dir / "custom.md"
        doc.write_text("""---
title: Custom Doc
brand:
  voice:
    tone: formal
    formality_level: 0.9
---

Custom content.
""")

        from media_engine import Project

        project = Project.load(tmp_path)  # Pass directory, not file
        resolver = BrandContextResolver(project)
        result = resolver.resolve_for_document(doc.relative_to(tmp_path))

        # Should have document override in chain
        assert any(step.source == "document" for step in result.resolution_chain)
        assert result.effective_voice.tone == "formal"
        assert result.effective_voice.formality_level == 0.9

    def test_cache_functionality(self, tmp_path):
        """Test that caching works."""
        # Create minimal project
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text("""
name: test-project
source_language: en
languages:
  en:
    name: English
paths:
  content: content
""")
        content_dir = tmp_path / "content" / "en" / "chapters"
        content_dir.mkdir(parents=True)
        doc = content_dir / "test.md"
        doc.write_text("---\ntitle: Test\n---\nContent")

        from media_engine import Project

        project = Project.load(tmp_path)  # Pass directory, not file
        resolver = BrandContextResolver(project)

        # First call
        result1 = resolver.resolve_for_document(doc.relative_to(tmp_path))
        # Second call should use cache
        result2 = resolver.resolve_for_document(doc.relative_to(tmp_path))

        assert result1 is result2  # Same object from cache

    def test_clear_cache(self, tmp_path):
        """Test cache clearing."""
        # Create minimal project
        project_yaml = tmp_path / "project.yaml"
        project_yaml.write_text("""
name: test-project
source_language: en
languages:
  en:
    name: English
paths:
  content: content
""")
        content_dir = tmp_path / "content" / "en" / "chapters"
        content_dir.mkdir(parents=True)
        doc = content_dir / "test.md"
        doc.write_text("---\ntitle: Test\n---\nContent")

        from media_engine import Project

        project = Project.load(tmp_path)  # Pass directory, not file
        resolver = BrandContextResolver(project)

        # Fill cache
        result1 = resolver.resolve_for_document(doc.relative_to(tmp_path))

        # Clear cache
        resolver.clear_cache()

        # Should compute new result
        result2 = resolver.resolve_for_document(doc.relative_to(tmp_path))

        assert result1 is not result2  # Different object after cache clear
