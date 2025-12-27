"""
Publication tracker - tracks changes and their impact on publications.

Provides:
- Change impact analysis
- Staleness detection
- Translation status per publication
- Derivation tracking
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.project import Project
    from .registry import PublicationRegistry

logger = logging.getLogger(__name__)


class PublicationTracker:
    """
    Tracks publication state and changes.

    Provides analysis of how changes to source files affect publications,
    including translations and derived publications.
    """

    def __init__(self, project: "Project", registry: "PublicationRegistry"):
        self.project = project
        self.registry = registry

    def analyze_change_impact(self, changed_file: Path) -> dict:
        """
        Analyze the impact of a file change on publications.

        Args:
            changed_file: Path to the changed file

        Returns:
            Dictionary with impact analysis
        """
        rel_path = changed_file
        if changed_file.is_absolute():
            try:
                rel_path = changed_file.relative_to(self.project.root)
            except ValueError:
                pass

        # Find which publications use this file
        usage = self.registry.get_document_usage(rel_path)
        affected_publications = usage.get("used_in", [])

        # Analyze each affected publication
        impacts = {
            "changed_file": str(rel_path),
            "immediate_impacts": [],
            "downstream_impacts": [],
            "suggested_tasks": [],
        }

        for pub_usage in affected_publications:
            pub = self.registry.get(pub_usage["publication_id"])
            if not pub:
                continue

            # Direct impact on this publication
            impacts["immediate_impacts"].append({
                "type": "publication_stale",
                "publication_id": pub.id,
                "publication_title": pub.title,
                "component_type": pub_usage["component_type"],
                "action_required": "rebuild",
            })

            # Check for translation impacts
            for lang in pub.languages:
                if lang == "en":  # Assuming EN is source
                    continue
                impacts["immediate_impacts"].append({
                    "type": "translation_may_be_stale",
                    "publication_id": pub.id,
                    "language": lang,
                    "action_required": "review_translation",
                })
                impacts["suggested_tasks"].append({
                    "type": "review_translation",
                    "target": str(rel_path),
                    "language": lang,
                    "priority": "high",
                })

            # Check for derivation impacts
            for other_pub in self.registry.list():
                if other_pub.derives_from == pub.id:
                    impacts["downstream_impacts"].append({
                        "type": "derived_publication_affected",
                        "publication_id": other_pub.id,
                        "publication_title": other_pub.title,
                        "derivation_mode": other_pub.derivation_mode.value,
                        "action_required": "review" if other_pub.derivation_mode.value == "manual" else "auto_update",
                    })
                    impacts["suggested_tasks"].append({
                        "type": "review_derivative",
                        "publication_id": other_pub.id,
                        "priority": "medium",
                    })

        return impacts

    def get_stale_publications(self) -> list[dict]:
        """Get all publications with stale components."""
        stale = []
        for pub in self.registry.list():
            stale_components = self.registry.get_stale_components(pub.id)
            if stale_components:
                stale.append({
                    "publication_id": pub.id,
                    "title": pub.title,
                    "stale_count": len(stale_components),
                    "stale_components": [str(c.source) for c in stale_components],
                })
        return stale

    def get_translation_status(self, pub_id: str) -> dict:
        """Get translation status for a publication."""
        pub = self.registry.get(pub_id)
        if not pub:
            return {"error": f"Publication not found: {pub_id}"}

        status = {
            "publication_id": pub_id,
            "title": pub.title,
            "primary_language": "en",
            "languages": {},
        }

        for lang in pub.languages:
            if lang == "en":
                status["languages"][lang] = {"status": "source", "components": []}
                continue

            lang_status = {
                "status": "complete",
                "components": [],
                "complete_count": 0,
                "missing_count": 0,
                "stale_count": 0,
            }

            for comp in pub.get_all_components():
                # Check if translation exists
                source_path = self.project.root / comp.source
                lang_path = self._get_translation_path(comp.source, lang)

                if not lang_path.exists():
                    lang_status["components"].append({
                        "source": str(comp.source),
                        "status": "missing",
                    })
                    lang_status["missing_count"] += 1
                else:
                    # Check if translation is stale
                    is_stale = self._check_translation_stale(source_path, lang_path)
                    if is_stale:
                        lang_status["components"].append({
                            "source": str(comp.source),
                            "translation": str(lang_path),
                            "status": "stale",
                        })
                        lang_status["stale_count"] += 1
                    else:
                        lang_status["components"].append({
                            "source": str(comp.source),
                            "translation": str(lang_path),
                            "status": "complete",
                        })
                        lang_status["complete_count"] += 1

            # Determine overall status
            if lang_status["missing_count"] > 0:
                lang_status["status"] = "incomplete"
            elif lang_status["stale_count"] > 0:
                lang_status["status"] = "stale"

            status["languages"][lang] = lang_status

        return status

    def _get_translation_path(self, source_path: Path, language: str) -> Path:
        """Get the expected translation path for a source file."""
        # Assume structure: content/en/... -> content/{lang}/...
        parts = source_path.parts
        if "en" in parts:
            idx = parts.index("en")
            new_parts = list(parts)
            new_parts[idx] = language
            return self.project.root / Path(*new_parts)
        else:
            # Default: prepend language to path
            return self.project.root / "content" / language / source_path.name

    def _check_translation_stale(self, source: Path, translation: Path) -> bool:
        """Check if a translation is stale compared to source."""
        if not source.exists() or not translation.exists():
            return True

        # Check modification times
        if source.stat().st_mtime > translation.stat().st_mtime:
            return True

        # Could also check frontmatter source_hash if available
        return False

    def get_publication_overview(self) -> dict:
        """Get overview of all publications."""
        publications = []
        for pub in self.registry.list():
            stale = self.registry.get_stale_components(pub.id)
            publications.append({
                "id": pub.id,
                "title": pub.title,
                "type": pub.publication_type.value,
                "status": pub.status.value,
                "formats": [f.value for f in pub.formats],
                "languages": pub.languages,
                "component_count": len(pub.get_all_components()),
                "stale_count": len(stale),
                "derives_from": pub.derives_from,
            })

        return {
            "total": len(publications),
            "publications": publications,
        }

    def get_build_queue(self) -> list[dict]:
        """Get publications that need building."""
        queue = []
        for pub in self.registry.list():
            stale = self.registry.get_stale_components(pub.id)
            if not stale:
                continue

            for fmt in pub.formats:
                for lang in pub.languages:
                    latest = self.registry.get_latest_build(pub.id, fmt, lang)
                    if not latest or len(stale) > 0:
                        queue.append({
                            "publication_id": pub.id,
                            "title": pub.title,
                            "format": fmt.value,
                            "language": lang,
                            "stale_components": len(stale),
                            "last_built": latest.completed_at.isoformat()
                            if latest and latest.completed_at
                            else None,
                        })

        return queue
