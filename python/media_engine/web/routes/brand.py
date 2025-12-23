"""
Brand API Routes

Provides brand/design system configuration to the dashboard.
Includes visual identity, voice guidelines, templates, and brand notes for AI processing.
"""

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def _get_brand_notes_path(project_root: Path) -> Path:
    """Get path to brand notes file."""
    return project_root / ".media-engine" / "brand_notes.json"


def _load_brand_notes(project_root: Path) -> Dict[str, Any]:
    """Load brand notes from file."""
    notes_path = _get_brand_notes_path(project_root)
    if notes_path.exists():
        return json.loads(notes_path.read_text())
    return {"notes": [], "categories": ["voice", "visual", "template", "general"]}


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

    # ==================== BRAND ASSETS ====================

    @router.get("/api/brand/assets")
    async def get_brand_assets() -> Dict[str, Any]:
        """Get comprehensive brand assets including colors, typography, spacing."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        try:
            from ...brand import load_brand_profile

            profile = load_brand_profile(project.root)

            # Build comprehensive assets response
            assets = {
                "name": profile.name,
                "version": getattr(profile, "version", "1.0.0"),
                "identity": {
                    "taglines": getattr(profile.identity, "taglines", None) if profile.identity else None,
                    "legal": {
                        "copyright": profile.identity.legal.copyright if profile.identity and profile.identity.legal else None,
                        "license": getattr(profile.identity.legal, "license", None) if profile.identity and profile.identity.legal else None,
                    } if profile.identity else None,
                },
                "colors": {
                    "brand": {
                        "primary": profile.colors.brand.primary,
                        "secondary": profile.colors.brand.secondary,
                        "accent": profile.colors.brand.accent,
                        "muted": getattr(profile.colors.brand, "muted", None),
                    },
                    "semantic": {
                        "success": profile.colors.semantic.success,
                        "warning": profile.colors.semantic.warning,
                        "error": profile.colors.semantic.error,
                        "info": profile.colors.semantic.info,
                    },
                    "text": {
                        "primary": getattr(profile.colors.text, "primary", "#1f2937"),
                        "secondary": getattr(profile.colors.text, "secondary", "#4b5563"),
                        "muted": getattr(profile.colors.text, "muted", "#9ca3af"),
                    } if profile.colors.text else {},
                    "background": {
                        "primary": getattr(profile.colors.background, "primary", "#ffffff"),
                        "secondary": getattr(profile.colors.background, "secondary", "#f9fafb"),
                    } if profile.colors.background else {},
                    "dark": {
                        "text": {
                            "primary": getattr(profile.colors.dark.text, "primary", "#f9fafb"),
                            "secondary": getattr(profile.colors.dark.text, "secondary", "#e5e7eb"),
                            "muted": getattr(profile.colors.dark.text, "muted", "#9ca3af"),
                        } if profile.colors.dark and profile.colors.dark.text else {},
                        "background": {
                            "primary": getattr(profile.colors.dark.background, "primary", "#111827"),
                            "secondary": getattr(profile.colors.dark.background, "secondary", "#1f2937"),
                        } if profile.colors.dark and profile.colors.dark.background else {},
                    } if hasattr(profile.colors, "dark") and profile.colors.dark else None,
                },
                "typography": {
                    "fonts": {
                        "heading": {
                            "family": profile.typography.heading.family,
                            "fallback": getattr(profile.typography.heading, "fallback", None),
                            "weights": profile.typography.heading.weights,
                            "source": profile.typography.heading.source,
                        },
                        "body": {
                            "family": profile.typography.body.family,
                            "fallback": getattr(profile.typography.body, "fallback", None),
                            "weights": profile.typography.body.weights,
                            "source": profile.typography.body.source,
                        },
                        "code": {
                            "family": profile.typography.code.family,
                            "fallback": getattr(profile.typography.code, "fallback", None),
                            "weights": profile.typography.code.weights,
                            "source": profile.typography.code.source,
                        },
                    },
                    "scale": getattr(profile.typography, "scale", None),
                },
                "logos": {},
                "spacing": getattr(profile, "spacing", None),
                "borders": getattr(profile, "borders", None),
                "shadows": getattr(profile, "shadows", None),
            }

            # Add logos with existence check
            for variant, logo in [
                ("primary", profile.logos.primary),
                ("dark", profile.logos.dark),
                ("square", profile.logos.square),
                ("icon", profile.logos.icon),
            ]:
                if logo:
                    logo_path = project.root / logo.path if logo.path else None
                    assets["logos"][variant] = {
                        "path": str(logo.path) if logo.path else None,
                        "alt": logo.alt,
                        "exists": logo_path.exists() if logo_path else False,
                        "url": f"/api/brand/file/{logo.path}" if logo.path else None,
                    }

            return assets

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ==================== BRAND FILES ====================

    @router.get("/api/brand/files")
    async def list_brand_files() -> Dict[str, Any]:
        """List all brand-related files in the project."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        files: List[Dict[str, Any]] = []

        # Check for brand.yaml
        brand_yaml = project.root / "brand.yaml"
        if brand_yaml.exists():
            stat = brand_yaml.stat()
            files.append({
                "path": "brand.yaml",
                "type": "config",
                "category": "configuration",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        # Check for theme.yaml (legacy)
        theme_yaml = project.root / "theme.yaml"
        if theme_yaml.exists():
            stat = theme_yaml.stat()
            files.append({
                "path": "theme.yaml",
                "type": "config",
                "category": "configuration",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "legacy": True,
            })

        # Check brand directory for logos and assets
        brand_dir = project.root / "brand"
        if brand_dir.exists():
            for item in brand_dir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(project.root)
                    stat = item.stat()

                    # Determine category
                    category = "asset"
                    if "logo" in item.name.lower():
                        category = "logo"
                    elif item.suffix in [".ttf", ".otf", ".woff", ".woff2"]:
                        category = "font"
                    elif item.suffix in [".svg", ".png", ".jpg", ".jpeg"]:
                        category = "image"

                    files.append({
                        "path": str(rel_path),
                        "type": item.suffix[1:] if item.suffix else "unknown",
                        "category": category,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })

        # Check for PPTX templates
        templates_dir = project.root / "templates"
        if templates_dir.exists():
            for item in templates_dir.rglob("*.pptx"):
                rel_path = item.relative_to(project.root)
                stat = item.stat()
                files.append({
                    "path": str(rel_path),
                    "type": "pptx",
                    "category": "template",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })

        # Check assets directory for brand-related files
        assets_dir = project.assets_dir
        if assets_dir.exists():
            for item in assets_dir.rglob("*"):
                if item.is_file() and any(x in item.name.lower() for x in ["logo", "brand", "icon"]):
                    rel_path = item.relative_to(project.root)
                    stat = item.stat()
                    files.append({
                        "path": str(rel_path),
                        "type": item.suffix[1:] if item.suffix else "unknown",
                        "category": "asset",
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })

        return {
            "files": files,
            "total": len(files),
            "categories": {
                "configuration": len([f for f in files if f["category"] == "configuration"]),
                "logo": len([f for f in files if f["category"] == "logo"]),
                "image": len([f for f in files if f["category"] == "image"]),
                "font": len([f for f in files if f["category"] == "font"]),
                "template": len([f for f in files if f["category"] == "template"]),
                "asset": len([f for f in files if f["category"] == "asset"]),
            },
        }

    @router.get("/api/brand/file/{file_path:path}")
    async def get_brand_file(file_path: str) -> Dict[str, Any]:
        """Get a specific brand file with content (base64 for binary)."""
        from fastapi.responses import Response

        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        full_path = project.root / file_path

        # Security check - ensure path is within project
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(project.root.resolve())):
                raise HTTPException(status_code=403, detail="Access denied")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid path")

        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        stat = full_path.stat()
        suffix = full_path.suffix.lower()

        # Determine content type and handling
        binary_types = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".pptx", ".ttf", ".otf", ".woff", ".woff2"}
        text_types = {".yaml", ".yml", ".json", ".css", ".md", ".txt"}

        if suffix in binary_types:
            content = base64.b64encode(full_path.read_bytes()).decode("utf-8")
            encoding = "base64"
        elif suffix in text_types:
            content = full_path.read_text()
            encoding = "text"
        else:
            content = base64.b64encode(full_path.read_bytes()).decode("utf-8")
            encoding = "base64"

        # Determine MIME type
        mime_types = {
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".ico": "image/x-icon",
            ".webp": "image/webp",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
            ".json": "application/json",
            ".css": "text/css",
            ".md": "text/markdown",
            ".txt": "text/plain",
        }

        return {
            "path": file_path,
            "name": full_path.name,
            "type": suffix[1:] if suffix else "unknown",
            "mime_type": mime_types.get(suffix, "application/octet-stream"),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "content": content,
            "encoding": encoding,
        }

    # ==================== BRAND NOTES ====================

    @router.get("/api/brand/notes")
    async def get_brand_notes() -> Dict[str, Any]:
        """Get all brand notes for AI processing."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        return _load_brand_notes(project.root)

    @router.post("/api/brand/notes")
    async def add_brand_note(
        category: str = Query(..., description="Note category: voice, visual, template, general"),
        target: Optional[str] = Query(None, description="Target file or element"),
        text: str = Query(..., description="Note text"),
        priority: str = Query("medium", description="Priority: low, medium, high, critical"),
    ) -> Dict[str, Any]:
        """Add a brand note for AI processing."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        notes_data = _load_brand_notes(project.root)

        # Create new note
        note = {
            "id": f"bn_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(notes_data['notes'])}",
            "category": category,
            "target": target,
            "text": text,
            "priority": priority,
            "status": "pending",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }

        notes_data["notes"].append(note)

        # Save notes
        notes_path = _get_brand_notes_path(project.root)
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        notes_path.write_text(json.dumps(notes_data, indent=2))

        return {"status": "created", "note": note}

    @router.put("/api/brand/notes/{note_id}")
    async def update_brand_note(
        note_id: str,
        text: Optional[str] = Query(None),
        status: Optional[str] = Query(None, description="Status: pending, in_progress, completed, archived"),
        priority: Optional[str] = Query(None),
    ) -> Dict[str, Any]:
        """Update a brand note."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        notes_data = _load_brand_notes(project.root)

        # Find note
        note = None
        for n in notes_data["notes"]:
            if n["id"] == note_id:
                note = n
                break

        if not note:
            raise HTTPException(status_code=404, detail=f"Note not found: {note_id}")

        # Update fields
        if text is not None:
            note["text"] = text
        if status is not None:
            note["status"] = status
        if priority is not None:
            note["priority"] = priority
        note["updated"] = datetime.now().isoformat()

        # Save notes
        notes_path = _get_brand_notes_path(project.root)
        notes_path.write_text(json.dumps(notes_data, indent=2))

        return {"status": "updated", "note": note}

    @router.delete("/api/brand/notes/{note_id}")
    async def delete_brand_note(note_id: str) -> Dict[str, Any]:
        """Delete a brand note."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        notes_data = _load_brand_notes(project.root)

        # Find and remove note
        original_count = len(notes_data["notes"])
        notes_data["notes"] = [n for n in notes_data["notes"] if n["id"] != note_id]

        if len(notes_data["notes"]) == original_count:
            raise HTTPException(status_code=404, detail=f"Note not found: {note_id}")

        # Save notes
        notes_path = _get_brand_notes_path(project.root)
        notes_path.write_text(json.dumps(notes_data, indent=2))

        return {"status": "deleted", "note_id": note_id}

    # ==================== BRAND GUIDE EXPORT ====================

    @router.get("/api/brand/guide")
    async def get_brand_guide() -> Dict[str, Any]:
        """Get complete brand guide suitable for export or AI processing."""
        project = get_project()
        if not project:
            raise HTTPException(status_code=404, detail="No project loaded")

        try:
            from ...brand import load_brand_profile

            profile = load_brand_profile(project.root)
            voice = profile.voice

            guide = {
                "project": project.name,
                "generated": datetime.now().isoformat(),
                "identity": {
                    "name": profile.name,
                    "taglines": getattr(profile.identity, "taglines", None) if profile.identity else None,
                    "legal": {
                        "copyright": profile.identity.legal.copyright if profile.identity and profile.identity.legal else None,
                    } if profile.identity else None,
                },
                "visual_identity": {
                    "colors": {
                        "brand": {
                            "primary": {"hex": profile.colors.brand.primary, "usage": "Main brand color, primary buttons, links"},
                            "secondary": {"hex": profile.colors.brand.secondary, "usage": "Secondary actions, accents"},
                            "accent": {"hex": profile.colors.brand.accent, "usage": "Highlights, call-to-actions"},
                        },
                        "semantic": {
                            "success": {"hex": profile.colors.semantic.success, "usage": "Success states, confirmations"},
                            "warning": {"hex": profile.colors.semantic.warning, "usage": "Warnings, cautions"},
                            "error": {"hex": profile.colors.semantic.error, "usage": "Errors, destructive actions"},
                            "info": {"hex": profile.colors.semantic.info, "usage": "Informational messages"},
                        },
                    },
                    "typography": {
                        "heading": {
                            "family": profile.typography.heading.family,
                            "usage": "Headlines, titles, section headers",
                        },
                        "body": {
                            "family": profile.typography.body.family,
                            "usage": "Body text, paragraphs, descriptions",
                        },
                        "code": {
                            "family": profile.typography.code.family,
                            "usage": "Code snippets, technical content, monospace text",
                        },
                    },
                    "logos": {
                        variant: {
                            "path": str(logo.path) if logo.path else None,
                            "usage": f"Use on {'dark' if variant == 'dark' else 'light'} backgrounds",
                        }
                        for variant, logo in [
                            ("primary", profile.logos.primary),
                            ("dark", profile.logos.dark),
                            ("icon", profile.logos.icon),
                        ]
                        if logo
                    },
                },
                "voice_guidelines": None,
                "notes": _load_brand_notes(project.root)["notes"],
            }

            if voice:
                guide["voice_guidelines"] = {
                    "personality": voice.personality,
                    "tone": voice.tone,
                    "formality": {
                        "level": voice.formality_level,
                        "description": {
                            1: "Very casual - friendly, conversational",
                            2: "Casual - approachable, relaxed",
                            3: "Professional - polished but warm",
                            4: "Formal - business-like, precise",
                            5: "Very formal - academic, authoritative",
                        }.get(voice.formality_level, "Professional"),
                    },
                    "style_rules": {
                        "active_voice": f"Target {int(voice.style.active_voice_target * 100)}% active voice",
                        "sentence_length": f"Average {voice.style.sentence_length_target} words per sentence",
                        "paragraph_length": f"Maximum {voice.style.paragraph_length_max} sentences per paragraph",
                        "contractions": "Use contractions" if voice.style.use_contractions else "Avoid contractions",
                        "person": ", ".join([
                            "first person (we/our)" if voice.style.use_first_person else None,
                            "second person (you/your)" if voice.style.use_second_person else None,
                        ]),
                    },
                    "terminology": {
                        "preferred": [
                            {"use": t.prefer, "instead_of": t.avoid}
                            for t in (voice.preferred_terms or [])
                        ],
                        "avoid": voice.avoid_phrases or [],
                    },
                    "context_overrides": {
                        "by_document_type": list(voice.by_document_type.keys()) if voice.by_document_type else [],
                        "by_audience": list(voice.by_audience.keys()) if voice.by_audience else [],
                    },
                }

            return guide

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
