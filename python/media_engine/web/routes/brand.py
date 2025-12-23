"""
Brand API Routes

Provides brand/design system configuration to the dashboard.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_brand_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
) -> None:
    """Register brand-related routes."""
    from fastapi import HTTPException, Query

    @router.get("/api/brand")
    async def get_brand() -> Dict[str, Any]:
        """Get brand configuration for the project."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        try:
            # Load brand profile
            from ...brand import load_brand_profile

            profile = load_brand_profile(project.root)

            # Determine source
            brand_yaml = project.root / "brand.yaml"
            source = "brand.yaml" if brand_yaml.exists() else "theme.yaml"

            # Build response
            return {
                "name": profile.name,
                "source": source,
                "colors": {
                    "primary": profile.colors.brand.primary,
                    "secondary": profile.colors.brand.secondary,
                    "accent": profile.colors.brand.accent,
                    "semantic": {
                        "success": profile.colors.semantic.success,
                        "warning": profile.colors.semantic.warning,
                        "error": profile.colors.semantic.error,
                        "info": profile.colors.semantic.info,
                    },
                },
                "typography": {
                    "heading": profile.typography.heading.family,
                    "body": profile.typography.body.family,
                    "code": profile.typography.code.family,
                },
                "logos": {
                    variant: {
                        "path": str(logo.path) if logo.path else None,
                        "exists": logo.exists(),
                    }
                    for variant, logo in [
                        ("primary", profile.logos.primary),
                        ("dark", profile.logos.dark),
                        ("square", profile.logos.square),
                        ("icon", profile.logos.icon),
                    ]
                    if logo
                },
            }
        except Exception as e:
            # Return basic fallback on error
            return {
                "name": project.name,
                "source": "fallback",
                "colors": {
                    "primary": "#1a365d",
                    "secondary": "#2a4a7f",
                    "accent": "#3182ce",
                },
                "typography": {
                    "heading": "Inter",
                    "body": "Inter",
                    "code": "JetBrains Mono",
                },
                "logos": {},
                "error": str(e),
            }

    @router.get("/api/brand/voice")
    async def get_brand_voice(
        doc_type: Optional[str] = Query(None, description="Document type for overrides"),
        audience: Optional[str] = Query(None, description="Audience for overrides"),
    ) -> Dict[str, Any]:
        """Get brand voice profile."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        try:
            from ...brand import load_brand_profile

            profile = load_brand_profile(project.root)
            voice = profile.voice

            if not voice:
                return {
                    "warning": "No voice profile defined in brand.yaml",
                    "has_voice": False,
                }

            # Apply context if specified
            effective_voice = voice
            if doc_type or audience:
                effective_voice = voice.get_for_context(doc_type, audience)

            result = {
                "has_voice": True,
                "personality": effective_voice.personality,
                "tone": effective_voice.tone,
                "formality_level": effective_voice.formality_level,
                "style": {
                    "active_voice_target": effective_voice.style.active_voice_target,
                    "sentence_length_target": effective_voice.style.sentence_length_target,
                    "paragraph_length_max": effective_voice.style.paragraph_length_max,
                    "use_contractions": effective_voice.style.use_contractions,
                    "use_first_person": effective_voice.style.use_first_person,
                    "use_second_person": effective_voice.style.use_second_person,
                },
            }

            if doc_type:
                result["applied_doc_type"] = doc_type
            if audience:
                result["applied_audience"] = audience

            # Include overrides info in base profile
            if not doc_type and not audience:
                if voice.by_document_type:
                    result["available_doc_types"] = list(voice.by_document_type.keys())
                if voice.by_audience:
                    result["available_audiences"] = list(voice.by_audience.keys())
                if voice.preferred_terms:
                    result["preferred_terms"] = [
                        {"prefer": t.prefer, "avoid": t.avoid}
                        for t in voice.preferred_terms
                    ]
                if voice.avoid_phrases:
                    result["avoid_phrases"] = voice.avoid_phrases

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/api/brand/voice/check")
    async def check_voice_all() -> Dict[str, Any]:
        """Check all documents against brand voice guidelines."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        try:
            from ...brand import VoiceConsistencyChecker, load_brand_profile

            profile = load_brand_profile(project.root)
            voice = profile.voice
            checker = VoiceConsistencyChecker(voice_profile=voice)

            results = []

            for lang in project.languages:
                for chapter_path in project.list_chapters(lang):
                    content = chapter_path.read_text()
                    result = checker.check_content(content, chapter_path)
                    results.append(result)

            passed_count = sum(1 for r in results if r.passed)
            total_issues = sum(len(r.issues) for r in results)

            return {
                "summary": {
                    "documents_checked": len(results),
                    "documents_passed": passed_count,
                    "total_issues": total_issues,
                    "pass_rate": round(passed_count / len(results) * 100, 1) if results else 0,
                },
                "results": [
                    {
                        "document": str(r.document),
                        "document_name": r.document.name,
                        "passed": r.passed,
                        "issues": [
                            {
                                "type": i.type,
                                "severity": i.severity,
                                "message": i.message,
                                "suggestion": i.suggestion,
                            }
                            for i in r.issues
                        ],
                        "metrics": r.metrics,
                    }
                    for r in results
                ],
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/api/brand/voice/check/{document_path:path}")
    async def check_voice_document(document_path: str) -> Dict[str, Any]:
        """Check specific document against brand voice guidelines."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        try:
            from ...brand import VoiceConsistencyChecker, load_brand_profile

            profile = load_brand_profile(project.root)
            voice = profile.voice
            checker = VoiceConsistencyChecker(voice_profile=voice)

            doc_path = Path(document_path)
            if not doc_path.is_absolute():
                doc_path = project.root / doc_path

            if not doc_path.exists():
                raise HTTPException(status_code=404, detail=f"Document not found: {document_path}")

            content = doc_path.read_text()
            result = checker.check_content(content, doc_path)

            return {
                "document": str(result.document),
                "document_name": result.document.name,
                "passed": result.passed,
                "issues": [
                    {
                        "type": i.type,
                        "severity": i.severity,
                        "message": i.message,
                        "suggestion": i.suggestion,
                    }
                    for i in result.issues
                ],
                "metrics": result.metrics,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/api/brand/voice/terminology")
    async def check_terminology() -> Dict[str, Any]:
        """Check terminology consistency across all documents."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        try:
            from ...brand import VoiceConsistencyChecker, load_brand_profile

            profile = load_brand_profile(project.root)
            voice = profile.voice

            if not voice or not voice.preferred_terms:
                return {
                    "warning": "No terminology preferences defined in brand.yaml",
                    "preferred_terms": [],
                    "avoid_phrases": [],
                    "issues": {},
                }

            checker = VoiceConsistencyChecker(voice_profile=voice)
            term_issues: Dict[str, List[str]] = {}

            for lang in project.languages:
                for chapter_path in project.list_chapters(lang):
                    content = chapter_path.read_text()
                    result = checker.check_content(content, chapter_path)

                    for issue in result.issues:
                        if issue.type == "terminology":
                            if issue.message not in term_issues:
                                term_issues[issue.message] = []
                            term_issues[issue.message].append(str(chapter_path))

            return {
                "preferred_terms": [
                    {"prefer": t.prefer, "avoid": t.avoid}
                    for t in voice.preferred_terms
                ],
                "avoid_phrases": voice.avoid_phrases,
                "issues": term_issues,
                "summary": {
                    "total_issues": sum(len(paths) for paths in term_issues.values()),
                    "unique_issues": len(term_issues),
                },
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/api/brand/voice/context/{document_path:path}")
    async def get_voice_context(document_path: str) -> Dict[str, Any]:
        """Get effective brand context for a document."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        try:
            from ...brand import BrandContextResolver

            resolver = BrandContextResolver(project)
            doc_path = Path(document_path)

            if not doc_path.is_absolute():
                doc_path = project.root / doc_path

            result = resolver.resolve_for_document(doc_path)

            return result.to_dict()

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
