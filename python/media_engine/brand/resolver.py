"""
Brand Context Resolver

Resolves effective brand context for documents by cascading settings
through the document hierarchy.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .context import BrandContext
from .profile import BrandProfile
from .voice import VoiceProfile, VoiceProfileOverride, VoiceStyle

if TYPE_CHECKING:
    from ..core.project import Project


@dataclass
class ResolutionStep:
    """A step in the brand context resolution chain."""

    source: str  # "base", "doc_type:xxx", "audience:xxx", "ancestor:path", "document"
    path: Optional[Path] = None
    overrides: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedBrandContext:
    """Resolved brand context with resolution chain for debugging."""

    context: BrandContext
    effective_voice: VoiceProfile
    resolution_chain: List[ResolutionStep] = field(default_factory=list)
    doc_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "document": str(self.doc_path) if self.doc_path else None,
            "resolution_chain": [
                {
                    "source": step.source,
                    "path": str(step.path) if step.path else None,
                    "overrides": step.overrides,
                }
                for step in self.resolution_chain
            ],
            "effective_voice": {
                "tone": self.effective_voice.tone,
                "formality_level": self.effective_voice.formality_level,
                "personality": self.effective_voice.personality,
                "style": self.effective_voice.style.to_dict() if self.effective_voice.style else {},
            },
        }


class BrandContextResolver:
    """
    Resolves effective brand context for documents.

    Resolution order (later overrides earlier):
    1. Project brand.yaml defaults
    2. doc_type overrides from brand.yaml
    3. audience overrides from brand.yaml
    4. Ancestor document overrides (root → parent)
    5. Document's own overrides
    """

    def __init__(self, project: "Project"):
        """
        Initialize resolver.

        Args:
            project: Project to resolve context for
        """
        self.project = project
        self._base_profile: Optional[BrandProfile] = None
        self._cache: Dict[Path, ResolvedBrandContext] = {}

    @property
    def base_profile(self) -> Optional[BrandProfile]:
        """Lazy-load base brand profile."""
        if self._base_profile is None:
            try:
                from .loader import load_brand_profile

                self._base_profile = load_brand_profile(self.project.root)
            except Exception:
                pass
        return self._base_profile

    def clear_cache(self):
        """Clear the resolution cache."""
        self._cache.clear()

    def resolve_for_document(
        self,
        doc_path: Path,
        use_cache: bool = True,
    ) -> ResolvedBrandContext:
        """
        Resolve effective brand context for a document.

        Args:
            doc_path: Path to document (relative or absolute)
            use_cache: Whether to use cached results

        Returns:
            ResolvedBrandContext with effective settings and resolution chain
        """
        # Normalize path
        if doc_path.is_absolute():
            try:
                doc_path = doc_path.relative_to(self.project.root)
            except ValueError:
                pass  # Keep absolute if not under project root

        # Check cache
        if use_cache and doc_path in self._cache:
            return self._cache[doc_path]

        resolution_chain: List[ResolutionStep] = []

        # Start with base profile
        base_voice = self._get_base_voice()
        resolution_chain.append(
            ResolutionStep(source="base", overrides={"voice": "from brand.yaml"})
        )

        current_voice = base_voice

        # Get document metadata
        doc_metadata = self._get_document_metadata(doc_path)
        doc_type = doc_metadata.get("type") or doc_metadata.get("doc_type")
        audience = doc_metadata.get("audience")

        # Apply doc_type overrides
        if doc_type and base_voice:
            if doc_type in base_voice.by_document_type:
                override = base_voice.by_document_type[doc_type]
                current_voice = self._apply_voice_override(current_voice, override)
                resolution_chain.append(
                    ResolutionStep(
                        source=f"doc_type:{doc_type}",
                        overrides=override.to_dict() if override else {},
                    )
                )

        # Apply audience overrides
        if audience and base_voice:
            if audience in base_voice.by_audience:
                override = base_voice.by_audience[audience]
                current_voice = self._apply_voice_override(current_voice, override)
                resolution_chain.append(
                    ResolutionStep(
                        source=f"audience:{audience}",
                        overrides=override.to_dict() if override else {},
                    )
                )

        # Apply hierarchy overrides (ancestors first)
        ancestors = self._get_ancestors(doc_path)
        for ancestor_path in reversed(ancestors):  # Root first
            ancestor_meta = self._get_document_metadata(ancestor_path)
            if "brand" in ancestor_meta:
                brand_overrides = ancestor_meta["brand"]
                current_voice = self._apply_dict_override(current_voice, brand_overrides)
                resolution_chain.append(
                    ResolutionStep(
                        source="ancestor",
                        path=ancestor_path,
                        overrides=brand_overrides,
                    )
                )

        # Apply document's own overrides
        if "brand" in doc_metadata:
            brand_overrides = doc_metadata["brand"]
            current_voice = self._apply_dict_override(current_voice, brand_overrides)
            resolution_chain.append(
                ResolutionStep(
                    source="document",
                    path=doc_path,
                    overrides=brand_overrides,
                )
            )

        # Build context
        context = BrandContext(profile=self.base_profile) if self.base_profile else BrandContext()

        result = ResolvedBrandContext(
            context=context,
            effective_voice=current_voice or VoiceProfile(),
            resolution_chain=resolution_chain,
            doc_path=doc_path,
        )

        # Cache result
        if use_cache:
            self._cache[doc_path] = result

        return result

    def _get_base_voice(self) -> Optional[VoiceProfile]:
        """Get base voice profile from brand.yaml."""
        if self.base_profile and self.base_profile.voice:
            return self.base_profile.voice
        return VoiceProfile()

    def _get_document_metadata(self, doc_path: Path) -> Dict[str, Any]:
        """Get document frontmatter metadata."""
        import yaml

        full_path = doc_path
        if not full_path.is_absolute():
            full_path = self.project.root / doc_path

        if not full_path.exists():
            return {}

        try:
            content = full_path.read_text()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end > 0:
                    frontmatter = yaml.safe_load(content[3:end])
                    if isinstance(frontmatter, dict):
                        return frontmatter
        except Exception:
            pass

        return {}

    def _get_ancestors(self, doc_path: Path) -> List[Path]:
        """Get ancestor documents in hierarchy order (closest first)."""
        ancestors = []

        try:
            from ..hierarchy import HierarchyGraph

            graph = HierarchyGraph(self.project)

            # Get parent chain
            current = doc_path
            while True:
                parent = graph.get_parent(current)
                if parent is None:
                    break
                ancestors.append(parent)
                current = parent
        except Exception:
            pass  # Hierarchy not available

        return ancestors

    def _apply_voice_override(
        self,
        base: Optional[VoiceProfile],
        override: VoiceProfileOverride,
    ) -> VoiceProfile:
        """Apply VoiceProfileOverride to a VoiceProfile."""
        if base is None:
            base = VoiceProfile()

        return VoiceProfile(
            personality=override.personality if override.personality else base.personality,
            tone=override.tone if override.tone else base.tone,
            formality_level=override.formality_level if override.formality_level is not None else base.formality_level,
            style=self._merge_style(base.style, override.style) if override.style else base.style,
            preferred_terms=base.preferred_terms,
            avoid_phrases=base.avoid_phrases,
            by_document_type={},  # Don't recurse
            by_audience={},  # Don't recurse
            audio=base.audio,
        )

    def _apply_dict_override(
        self,
        base: Optional[VoiceProfile],
        overrides: Dict[str, Any],
    ) -> VoiceProfile:
        """Apply dictionary overrides to a VoiceProfile."""
        if base is None:
            base = VoiceProfile()

        # Extract voice-specific overrides
        voice_overrides = overrides.get("voice", {})

        personality = voice_overrides.get("personality", base.personality)
        tone = voice_overrides.get("tone", base.tone)
        formality_level = voice_overrides.get("formality_level", base.formality_level)

        # Handle style overrides
        style = base.style
        if "style" in voice_overrides:
            style = self._merge_style_dict(base.style, voice_overrides["style"])

        return VoiceProfile(
            personality=personality,
            tone=tone,
            formality_level=formality_level,
            style=style,
            preferred_terms=base.preferred_terms,
            avoid_phrases=base.avoid_phrases,
            by_document_type={},
            by_audience={},
            audio=base.audio,
        )

    def _merge_style(
        self,
        base: VoiceStyle,
        override: Optional[VoiceStyle],
    ) -> VoiceStyle:
        """Merge two VoiceStyle objects."""
        if override is None:
            return base

        return VoiceStyle(
            active_voice_target=override.active_voice_target,
            sentence_length_target=override.sentence_length_target,
            paragraph_length_max=override.paragraph_length_max,
            use_contractions=override.use_contractions,
            use_first_person=override.use_first_person,
            use_second_person=override.use_second_person,
        )

    def _merge_style_dict(
        self,
        base: VoiceStyle,
        overrides: Dict[str, Any],
    ) -> VoiceStyle:
        """Merge style with dictionary overrides."""
        return VoiceStyle(
            active_voice_target=overrides.get("active_voice_target", base.active_voice_target),
            sentence_length_target=overrides.get("sentence_length_target", base.sentence_length_target),
            paragraph_length_max=overrides.get("paragraph_length_max", base.paragraph_length_max),
            use_contractions=overrides.get("use_contractions", base.use_contractions),
            use_first_person=overrides.get("use_first_person", base.use_first_person),
            use_second_person=overrides.get("use_second_person", base.use_second_person),
        )


def resolve_brand_context(
    project: "Project",
    doc_path: Path,
) -> ResolvedBrandContext:
    """
    Convenience function to resolve brand context for a document.

    Args:
        project: Project
        doc_path: Path to document

    Returns:
        ResolvedBrandContext with effective settings
    """
    resolver = BrandContextResolver(project)
    return resolver.resolve_for_document(doc_path)
