"""
Brand Voice Profile

Defines voice, tone, and writing style guidelines for consistent brand communication.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VoiceStyle:
    """Writing style preferences and targets."""

    active_voice_target: float = 0.8  # Target 80% active voice
    sentence_length_target: int = 18  # Average words per sentence
    paragraph_length_max: int = 5  # Max sentences per paragraph
    use_contractions: bool = True  # "don't" vs "do not"
    use_first_person: bool = False  # Avoid "I" and "we"
    use_second_person: bool = True  # Use "you" and "your"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceStyle":
        return cls(
            active_voice_target=data.get("active_voice_target", 0.8),
            sentence_length_target=data.get("sentence_length_target", 18),
            paragraph_length_max=data.get("paragraph_length_max", 5),
            use_contractions=data.get("use_contractions", True),
            use_first_person=data.get("use_first_person", False),
            use_second_person=data.get("use_second_person", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_voice_target": self.active_voice_target,
            "sentence_length_target": self.sentence_length_target,
            "paragraph_length_max": self.paragraph_length_max,
            "use_contractions": self.use_contractions,
            "use_first_person": self.use_first_person,
            "use_second_person": self.use_second_person,
        }

    def merge(self, override: "VoiceStyle") -> "VoiceStyle":
        """Merge with override, taking non-default values from override."""
        return VoiceStyle(
            active_voice_target=override.active_voice_target,
            sentence_length_target=override.sentence_length_target,
            paragraph_length_max=override.paragraph_length_max,
            use_contractions=override.use_contractions,
            use_first_person=override.use_first_person,
            use_second_person=override.use_second_person,
        )


@dataclass
class TermPreference:
    """Terminology preference: preferred term and alternatives to avoid."""

    prefer: str
    avoid: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TermPreference":
        avoid = data.get("avoid", [])
        if isinstance(avoid, str):
            avoid = [avoid]
        return cls(
            prefer=data.get("prefer", ""),
            avoid=avoid,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prefer": self.prefer,
            "avoid": self.avoid,
        }


@dataclass
class VoiceProfile:
    """
    Complete voice and tone profile for brand communication.

    Defines personality traits, tone settings, writing style preferences,
    terminology guidelines, and overrides for specific document types
    or audiences.
    """

    # Overall brand voice characteristics
    personality: List[str] = field(default_factory=lambda: ["professional", "approachable"])
    tone: str = "conversational"  # formal | conversational | technical | casual | procedural | persuasive
    formality_level: float = 0.6  # 0 = very casual, 1 = very formal

    # Writing style preferences
    style: VoiceStyle = field(default_factory=VoiceStyle)

    # Terminology preferences
    preferred_terms: List[TermPreference] = field(default_factory=list)

    # Phrases to avoid
    avoid_phrases: List[str] = field(default_factory=list)

    # Document-type-specific overrides (partial profiles)
    by_document_type: Dict[str, "VoiceProfileOverride"] = field(default_factory=dict)

    # Audience-specific overrides (partial profiles)
    by_audience: Dict[str, "VoiceProfileOverride"] = field(default_factory=dict)

    # Audio/voiceover voice profile
    audio: Optional["AudioVoiceProfile"] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceProfile":
        # Parse preferred terms
        preferred_terms = []
        for term_data in data.get("preferred_terms", []):
            preferred_terms.append(TermPreference.from_dict(term_data))

        # Parse document type overrides
        by_document_type = {}
        for doc_type, override_data in data.get("by_document_type", {}).items():
            by_document_type[doc_type] = VoiceProfileOverride.from_dict(override_data)

        # Parse audience overrides
        by_audience = {}
        for audience, override_data in data.get("by_audience", {}).items():
            by_audience[audience] = VoiceProfileOverride.from_dict(override_data)

        # Parse tone - can be a string or an object with default and formality_level
        tone_data = data.get("tone", "conversational")
        if isinstance(tone_data, dict):
            tone = tone_data.get("default", "conversational")
            formality_level = tone_data.get("formality_level", data.get("formality_level", 0.6))
        else:
            tone = tone_data
            formality_level = data.get("formality_level", 0.6)

        # Parse audio profile if present
        audio = None
        if "audio" in data:
            audio = AudioVoiceProfile.from_dict(data["audio"])

        return cls(
            personality=data.get("personality", ["professional", "approachable"]),
            tone=tone,
            formality_level=formality_level,
            style=VoiceStyle.from_dict(data.get("style", {})),
            preferred_terms=preferred_terms,
            avoid_phrases=data.get("avoid_phrases", []),
            by_document_type=by_document_type,
            by_audience=by_audience,
            audio=audio,
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "personality": self.personality,
            "tone": {
                "default": self.tone,
                "formality_level": self.formality_level,
            },
            "style": self.style.to_dict(),
            "preferred_terms": [t.to_dict() for t in self.preferred_terms],
            "avoid_phrases": self.avoid_phrases,
        }

        if self.by_document_type:
            result["by_document_type"] = {
                doc_type: override.to_dict() for doc_type, override in self.by_document_type.items()
            }

        if self.by_audience:
            result["by_audience"] = {audience: override.to_dict() for audience, override in self.by_audience.items()}

        if self.audio:
            result["audio"] = self.audio.to_dict()

        return result

    def get_for_document_type(self, doc_type: str) -> "VoiceProfile":
        """
        Get merged profile for a specific document type.

        Returns a new VoiceProfile with document-type-specific overrides applied.
        """
        if doc_type not in self.by_document_type:
            return self

        override = self.by_document_type[doc_type]
        return self._apply_override(override)

    def get_for_audience(self, audience: str) -> "VoiceProfile":
        """
        Get merged profile for a specific audience.

        Returns a new VoiceProfile with audience-specific overrides applied.
        """
        if audience not in self.by_audience:
            return self

        override = self.by_audience[audience]
        return self._apply_override(override)

    def get_for_context(self, doc_type: Optional[str] = None, audience: Optional[str] = None) -> "VoiceProfile":
        """
        Get merged profile for a specific context.

        Applies document type overrides first, then audience overrides.
        This allows audience to further refine document-type settings.
        """
        profile = self

        # Apply document type override if available
        if doc_type and doc_type in self.by_document_type:
            profile = profile._apply_override(self.by_document_type[doc_type])

        # Apply audience override if available (from original profile)
        if audience and audience in self.by_audience:
            profile = profile._apply_override(self.by_audience[audience])

        return profile

    def _apply_override(self, override: "VoiceProfileOverride") -> "VoiceProfile":
        """Apply an override to create a new merged profile."""
        return VoiceProfile(
            personality=override.personality if override.personality else self.personality,
            tone=override.tone if override.tone else self.tone,
            formality_level=override.formality_level if override.formality_level is not None else self.formality_level,
            style=self._merge_style(override.style) if override.style else self.style,
            preferred_terms=self.preferred_terms,  # Keep base terms
            avoid_phrases=self.avoid_phrases,  # Keep base phrases
            by_document_type={},  # Don't recurse
            by_audience={},  # Don't recurse
        )

    def _merge_style(self, override_style: VoiceStyle) -> VoiceStyle:
        """Merge style with override."""
        return VoiceStyle(
            active_voice_target=override_style.active_voice_target,
            sentence_length_target=override_style.sentence_length_target,
            paragraph_length_max=override_style.paragraph_length_max,
            use_contractions=override_style.use_contractions,
            use_first_person=override_style.use_first_person,
            use_second_person=override_style.use_second_person,
        )


@dataclass
class VoiceProfileOverride:
    """
    Partial voice profile for document-type or audience-specific overrides.

    Only specified fields will override the base profile.
    """

    personality: Optional[List[str]] = None
    tone: Optional[str] = None
    formality_level: Optional[float] = None
    style: Optional[VoiceStyle] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceProfileOverride":
        style = None
        if "style" in data:
            style = VoiceStyle.from_dict(data["style"])

        return cls(
            personality=data.get("personality"),
            tone=data.get("tone"),
            formality_level=data.get("formality_level"),
            style=style,
        )

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        if self.personality is not None:
            result["personality"] = self.personality
        if self.tone is not None:
            result["tone"] = self.tone
        if self.formality_level is not None:
            result["formality_level"] = self.formality_level
        if self.style is not None:
            result["style"] = self.style.to_dict()

        return result


# =============================================================================
# AUDIO VOICE PROFILE (for voiceovers)
# =============================================================================


@dataclass
class AudioVoiceSettings:
    """Settings for audio/voiceover voice generation."""

    stability: float = 0.5  # Voice stability (0-1)
    similarity_boost: float = 0.75  # Voice similarity (0-1)
    style: float = 0.0  # Speaking style (0-1, 0 = neutral)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioVoiceSettings":
        return cls(
            stability=data.get("stability", 0.5),
            similarity_boost=data.get("similarity_boost", 0.75),
            style=data.get("style", 0.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
        }

    def merge(self, override: "AudioVoiceSettings") -> "AudioVoiceSettings":
        """Merge with override settings."""
        return AudioVoiceSettings(
            stability=override.stability,
            similarity_boost=override.similarity_boost,
            style=override.style,
        )


@dataclass
class AudioVoice:
    """Audio voice configuration for a specific language."""

    voice_id: str
    name: str = ""
    description: str = ""
    settings: Optional[AudioVoiceSettings] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioVoice":
        # Handle simple string voice_id format
        if isinstance(data, str):
            return cls(voice_id=data)

        settings = None
        if "settings" in data:
            settings = AudioVoiceSettings.from_dict(data["settings"])

        return cls(
            voice_id=data.get("voice_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            settings=settings,
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "voice_id": self.voice_id,
            "name": self.name,
            "description": self.description,
        }
        if self.settings:
            result["settings"] = self.settings.to_dict()
        return result

    def with_settings(self, settings: AudioVoiceSettings) -> "AudioVoice":
        """Return a copy with merged settings."""
        base = self.settings or AudioVoiceSettings()
        return AudioVoice(
            voice_id=self.voice_id,
            name=self.name,
            description=self.description,
            settings=base.merge(settings),
        )


@dataclass
class AudioVoiceProfile:
    """
    Audio voice profile for voiceover generation.

    Manages voice IDs and settings for text-to-speech providers
    like ElevenLabs, Azure, Google, and Amazon.
    """

    provider: str = "elevenlabs"  # elevenlabs | azure | google | amazon
    default_settings: AudioVoiceSettings = field(default_factory=AudioVoiceSettings)
    voices: Dict[str, AudioVoice] = field(default_factory=dict)  # language -> voice
    by_document_type: Dict[str, AudioVoiceSettings] = field(default_factory=dict)
    by_audience: Dict[str, AudioVoiceSettings] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioVoiceProfile":
        # Parse default settings
        default_settings = AudioVoiceSettings.from_dict(data.get("default", {}))

        # Parse voices
        voices = {}
        for lang, voice_data in data.get("voices", {}).items():
            voices[lang] = AudioVoice.from_dict(voice_data)

        # Parse document type overrides
        by_document_type = {}
        for doc_type, settings_data in data.get("by_document_type", {}).items():
            by_document_type[doc_type] = AudioVoiceSettings.from_dict(settings_data)

        # Parse audience overrides
        by_audience = {}
        for audience, settings_data in data.get("by_audience", {}).items():
            by_audience[audience] = AudioVoiceSettings.from_dict(settings_data)

        return cls(
            provider=data.get("provider", "elevenlabs"),
            default_settings=default_settings,
            voices=voices,
            by_document_type=by_document_type,
            by_audience=by_audience,
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "provider": self.provider,
            "default": self.default_settings.to_dict(),
            "voices": {lang: voice.to_dict() for lang, voice in self.voices.items()},
        }

        if self.by_document_type:
            result["by_document_type"] = {
                doc_type: settings.to_dict() for doc_type, settings in self.by_document_type.items()
            }

        if self.by_audience:
            result["by_audience"] = {audience: settings.to_dict() for audience, settings in self.by_audience.items()}

        return result

    def get_voice(self, language: str) -> Optional[AudioVoice]:
        """Get voice for a specific language."""
        return self.voices.get(language)

    def get_settings(
        self, doc_type: Optional[str] = None, audience: Optional[str] = None
    ) -> AudioVoiceSettings:
        """
        Get merged settings for a specific context.

        Starts with default settings, then applies document type overrides,
        then audience overrides.
        """
        settings = self.default_settings

        if doc_type and doc_type in self.by_document_type:
            settings = settings.merge(self.by_document_type[doc_type])

        if audience and audience in self.by_audience:
            settings = settings.merge(self.by_audience[audience])

        return settings

    def get_voice_for_context(
        self, language: str, doc_type: Optional[str] = None, audience: Optional[str] = None
    ) -> Optional[AudioVoice]:
        """
        Get voice with context-appropriate settings.

        Returns the language voice with settings merged from document type
        and audience overrides.
        """
        voice = self.get_voice(language)
        if not voice:
            return None

        settings = self.get_settings(doc_type, audience)
        return voice.with_settings(settings)


# Default voice profile
DEFAULT_VOICE_PROFILE = VoiceProfile(
    personality=["professional", "approachable", "innovative"],
    tone="conversational",
    formality_level=0.6,
    style=VoiceStyle(),
    preferred_terms=[
        TermPreference(prefer="use", avoid=["utilize", "leverage"]),
        TermPreference(prefer="help", avoid=["assist", "facilitate"]),
        TermPreference(prefer="show", avoid=["demonstrate", "illustrate"]),
        TermPreference(prefer="start", avoid=["commence", "initiate"]),
        TermPreference(prefer="end", avoid=["terminate", "conclude"]),
        TermPreference(prefer="get", avoid=["obtain", "acquire"]),
        TermPreference(prefer="need", avoid=["require", "necessitate"]),
        TermPreference(prefer="make", avoid=["construct", "fabricate"]),
    ],
    avoid_phrases=[
        "please note that",
        "it should be noted",
        "in order to",
        "at this point in time",
        "for the purpose of",
        "with regard to",
        "in the event that",
        "due to the fact that",
        "in light of the fact that",
        "as a matter of fact",
    ],
)
