"""Brand voice and design system tools."""

import json
from pathlib import Path
from typing import Optional


def register_brand_tools(mcp, server_instance):
    """Register brand-related MCP tools."""

    @mcp.tool()
    async def brand_voice_profile(
        doc_type: Optional[str] = None,
        audience: Optional[str] = None,
    ) -> str:
        """
        Get brand voice profile.

        Returns the brand voice guidelines including personality, tone,
        formality level, style targets, terminology preferences, and
        phrases to avoid.

        Args:
            doc_type: Get profile with document type overrides applied
            audience: Get profile with audience overrides applied
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...brand import load_brand_profile

        try:
            profile = load_brand_profile(server_instance.project.root)
            voice = profile.voice

            if not voice:
                return json.dumps(
                    {"warning": "No voice profile defined in brand.yaml"},
                    indent=2,
                )

            # Apply context if specified
            effective_voice = voice
            if doc_type or audience:
                effective_voice = voice.get_for_context(doc_type, audience)

            result = {
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

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def brand_voice_check(
        document: Optional[str] = None,
        check_all: bool = False,
    ) -> str:
        """
        Check document(s) against brand voice guidelines.

        Analyzes content for:
        - Active voice usage
        - Sentence length
        - Formality level
        - Person usage (first/second/third)
        - Terminology compliance
        - Avoided phrases

        Args:
            document: Specific document path to check (relative to project root)
            check_all: Check all documents in the project
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...brand import VoiceConsistencyChecker, load_brand_profile

        try:
            profile = load_brand_profile(server_instance.project.root)
            voice = profile.voice
            checker = VoiceConsistencyChecker(voice_profile=voice)

            results = []

            if check_all:
                for lang in server_instance.project.languages:
                    for chapter_path in server_instance.project.list_chapters(lang):
                        content = chapter_path.read_text()
                        result = checker.check_content(content, chapter_path)
                        results.append(result)
            elif document:
                doc_path = Path(document)
                if not doc_path.is_absolute():
                    doc_path = server_instance.project.root / doc_path
                if not doc_path.exists():
                    return json.dumps({"error": f"File not found: {document}"}, indent=2)
                content = doc_path.read_text()
                result = checker.check_content(content, doc_path)
                results.append(result)
            else:
                return json.dumps(
                    {"error": "Specify a document path or use check_all=true"},
                    indent=2,
                )

            # Build response
            passed_count = sum(1 for r in results if r.passed)
            total_issues = sum(len(r.issues) for r in results)

            response = {
                "summary": {
                    "documents_checked": len(results),
                    "documents_passed": passed_count,
                    "total_issues": total_issues,
                },
                "results": [r.to_dict() for r in results],
            }

            return json.dumps(response, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def brand_context(document: str) -> str:
        """
        Get effective brand context for a document.

        Shows the resolution chain that determines the document's effective
        voice profile, including:
        - Base brand.yaml settings
        - Document type overrides
        - Audience overrides
        - Ancestor document overrides (hierarchy inheritance)
        - Document's own brand frontmatter

        Args:
            document: Document path (relative to project root)
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...brand import BrandContextResolver

        try:
            resolver = BrandContextResolver(server_instance.project)
            doc_path = Path(document)

            if not doc_path.is_absolute():
                doc_path = server_instance.project.root / doc_path

            result = resolver.resolve_for_document(doc_path)

            return json.dumps(result.to_dict(), indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def brand_terminology_check() -> str:
        """
        Check terminology consistency across all documents.

        Scans all documents for usage of non-preferred terminology
        and phrases that should be avoided according to brand guidelines.

        Returns:
            Report of terminology issues organized by preference rule.
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...brand import VoiceConsistencyChecker, load_brand_profile

        try:
            profile = load_brand_profile(server_instance.project.root)
            voice = profile.voice

            if not voice or not voice.preferred_terms:
                return json.dumps(
                    {"warning": "No terminology preferences defined in brand.yaml"},
                    indent=2,
                )

            checker = VoiceConsistencyChecker(voice_profile=voice)
            term_issues = {}  # term -> list of files

            # Check all documents
            for lang in server_instance.project.languages:
                for chapter_path in server_instance.project.list_chapters(lang):
                    content = chapter_path.read_text()
                    result = checker.check_content(content, chapter_path)

                    for issue in result.issues:
                        if issue.type == "terminology":
                            if issue.message not in term_issues:
                                term_issues[issue.message] = []
                            term_issues[issue.message].append(str(chapter_path))

            response = {
                "preferred_terms": [
                    {"prefer": t.prefer, "avoid": t.avoid}
                    for t in voice.preferred_terms
                ],
                "avoid_phrases": voice.avoid_phrases,
                "issues": {
                    msg: paths for msg, paths in term_issues.items()
                },
                "summary": {
                    "total_issues": sum(len(paths) for paths in term_issues.values()),
                    "unique_issues": len(term_issues),
                },
            }

            return json.dumps(response, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def brand_status() -> str:
        """
        Get brand/design system status.

        Returns comprehensive brand profile information including:
        - Identity (name, logos, legal)
        - Colors (brand, semantic, text, background)
        - Typography (fonts, scale)
        - Voice profile summary
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        from ...brand import load_brand_profile

        try:
            profile = load_brand_profile(server_instance.project.root)

            response = {
                "name": profile.name,
                "identity": {
                    "logos": {
                        variant: {
                            "path": str(logo.path),
                            "exists": logo.exists(),
                        }
                        for variant, logo in [
                            ("primary", profile.logos.primary),
                            ("dark", profile.logos.dark),
                            ("square", profile.logos.square),
                            ("icon", profile.logos.icon),
                        ]
                        if logo.path
                    },
                    "legal": {
                        "copyright": profile.identity.legal.copyright if profile.identity else None,
                        "tagline": profile.identity.legal.tagline if profile.identity else None,
                    },
                },
                "colors": {
                    "brand": {
                        "primary": profile.colors.brand.primary,
                        "secondary": profile.colors.brand.secondary,
                        "accent": profile.colors.brand.accent,
                    },
                    "semantic": {
                        "success": profile.colors.semantic.success,
                        "warning": profile.colors.semantic.warning,
                        "error": profile.colors.semantic.error,
                        "info": profile.colors.semantic.info,
                    },
                },
                "typography": {
                    "heading": {
                        "family": profile.typography.heading.family,
                        "weights": profile.typography.heading.weights,
                        "source": profile.typography.heading.source,
                    },
                    "body": {
                        "family": profile.typography.body.family,
                        "weights": profile.typography.body.weights,
                        "source": profile.typography.body.source,
                    },
                    "code": {
                        "family": profile.typography.code.family,
                        "weights": profile.typography.code.weights,
                        "source": profile.typography.code.source,
                    },
                },
            }

            # Add voice summary if available
            if profile.voice:
                response["voice"] = {
                    "personality": profile.voice.personality,
                    "tone": profile.voice.tone,
                    "formality_level": profile.voice.formality_level,
                    "has_doc_type_overrides": bool(profile.voice.by_document_type),
                    "has_audience_overrides": bool(profile.voice.by_audience),
                    "preferred_terms_count": len(profile.voice.preferred_terms),
                    "avoid_phrases_count": len(profile.voice.avoid_phrases),
                }

            return json.dumps(response, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
