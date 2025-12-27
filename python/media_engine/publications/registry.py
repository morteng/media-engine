"""
Publication registry - manages all publications in a project.

Handles:
- Loading publications from project.yaml
- Tracking build status
- Computing staleness
- Managing derivation relationships
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

from ..core import compute_file_hash
from .models import (
    ComponentType,
    DerivationMode,
    OutputFormat,
    Publication,
    PublicationBuild,
    PublicationComponent,
    PublicationPart,
    PublicationStatus,
    PublicationType,
)

if TYPE_CHECKING:
    from ..core.project import Project

logger = logging.getLogger(__name__)


class PublicationRegistry:
    """
    Registry of all publications in a project.

    Loads publications from project.yaml and tracks their status,
    builds, and component freshness.
    """

    def __init__(self, project: "Project"):
        self.project = project
        self.publications: dict[str, Publication] = {}
        self.builds: dict[str, list[PublicationBuild]] = {}
        self._registry_path = project.root / ".media-engine" / "publications.json"
        self._load()

    def _load(self) -> None:
        """Load publications from project config and registry."""
        # Load publication definitions from project.yaml
        self._load_from_config()

        # Load build history from registry
        self._load_registry()

    def _load_from_config(self) -> None:
        """Load publications from project.yaml."""
        config_path = self.project.root / "project.yaml"
        if not config_path.exists():
            return

        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        publications_config = config.get("publications", {})

        # Support both list and dict formats
        if isinstance(publications_config, list):
            # List format: [{ id: "pub-id", ... }, ...]
            for pub_data in publications_config:
                pub_id = pub_data.get("id", f"pub-{len(self.publications)}")
                pub = self._parse_publication(pub_id, pub_data)
                self.publications[pub_id] = pub
        elif isinstance(publications_config, dict):
            # Dict format: { "pub-id": { ... }, ... }
            for pub_id, pub_data in publications_config.items():
                pub_data["id"] = pub_id
                pub = self._parse_publication(pub_id, pub_data)
                self.publications[pub_id] = pub

        # If no publications defined, create a default one from content
        if not self.publications:
            self._create_default_publication()

    def _parse_publication(self, pub_id: str, data: dict) -> Publication:
        """Parse publication from config data."""
        # Parse structure into parts and components
        parts = []
        components = []
        order = 0

        # Support multiple structure formats:
        # 1. "structure" key with flat/nested items
        # 2. "parts" key with explicit part definitions
        # 3. "components" key with flat component list

        if "parts" in data:
            # Explicit parts format: parts: [{ id, title, components: [...] }, ...]
            for part_data in data.get("parts", []):
                part_components = []
                for comp_data in part_data.get("components", []):
                    if isinstance(comp_data, str):
                        comp = self._create_component(comp_data, order)
                        part_components.append(comp)
                    elif isinstance(comp_data, dict):
                        comp = self._create_component_from_dict(comp_data, order)
                        part_components.append(comp)
                    order += 1
                parts.append(
                    PublicationPart(
                        id=part_data.get("id", f"part_{len(parts)}"),
                        title=part_data.get("title", "Untitled Part"),
                        components=part_components,
                    )
                )

        if "components" in data:
            # Flat components format
            for comp_data in data.get("components", []):
                if isinstance(comp_data, str):
                    comp = self._create_component(comp_data, order)
                    components.append(comp)
                elif isinstance(comp_data, dict):
                    comp = self._create_component_from_dict(comp_data, order)
                    components.append(comp)
                order += 1

        if "structure" in data:
            # Legacy structure format
            for item in data.get("structure", []):
                if isinstance(item, str):
                    # Simple source reference
                    comp = self._create_component(item, order)
                    components.append(comp)
                    order += 1
                elif isinstance(item, dict):
                    if "part" in item:
                        # This is a part with nested items
                        part_components = []
                        for part_item in item.get("items", []):
                            if isinstance(part_item, str):
                                comp = self._create_component(part_item, order)
                                part_components.append(comp)
                            elif isinstance(part_item, dict):
                                comp = self._create_component_from_dict(part_item, order)
                                part_components.append(comp)
                            order += 1
                        parts.append(
                            PublicationPart(
                                id=item.get("id", f"part_{len(parts)}"),
                                title=item["part"],
                                components=part_components,
                            )
                        )
                    elif "source" in item:
                        # Component with options
                        comp = self._create_component_from_dict(item, order)
                        components.append(comp)
                        order += 1

        # Parse formats
        formats = []
        for fmt in data.get("formats", ["html"]):
            try:
                formats.append(OutputFormat(fmt))
            except ValueError:
                logger.warning(f"Unknown format: {fmt}")

        return Publication(
            id=pub_id,
            title=data.get("title", pub_id),
            publication_type=PublicationType(data.get("type", "book")),
            description=data.get("description"),
            formats=formats,
            languages=data.get("languages", ["en"]),
            parts=parts,
            components=components,
            derives_from=data.get("derives_from"),
            derivation_mode=DerivationMode(data.get("derivation_mode", "manual")),
            status=PublicationStatus(data.get("status", "draft")),
            version=data.get("version", "1.0.0"),
            authors=data.get("authors", []),
            tags=data.get("tags", []),
        )

    def _create_component(self, source: str, order: int) -> PublicationComponent:
        """Create component from source path string."""
        path = Path(source)
        comp_type = self._infer_component_type(path)
        return PublicationComponent(
            source=path,
            component_type=comp_type,
            order=order,
        )

    def _create_component_from_dict(
        self, data: dict, order: int
    ) -> PublicationComponent:
        """Create component from dictionary."""
        source = Path(data["source"])
        comp_type = ComponentType(data.get("type", self._infer_component_type(source).value))
        return PublicationComponent(
            source=source,
            component_type=comp_type,
            title=data.get("title"),
            render_as=data.get("render_as"),
            options=data.get("options", {}),
            order=order,
        )

    def _infer_component_type(self, path: Path) -> ComponentType:
        """Infer component type from file path."""
        suffix = path.suffix.lower()
        name = path.name.lower()

        if suffix == ".md":
            if "slide" in name or "deck" in name:
                return ComponentType.SLIDE
            if "script" in name:
                return ComponentType.SCRIPT
            return ComponentType.CHAPTER
        elif suffix in (".yaml", ".yml"):
            if "diagram" in name or path.parent.name == "diagrams":
                return ComponentType.DIAGRAM
            return ComponentType.DATA
        elif suffix in (".png", ".jpg", ".jpeg", ".svg", ".gif", ".mp4", ".webm"):
            return ComponentType.ASSET
        elif suffix in (".csv", ".json"):
            return ComponentType.DATA
        else:
            return ComponentType.ASSET

    def _create_default_publication(self) -> None:
        """Create default publication from content directory."""
        content_dir = self.project.content_dir
        if not content_dir.exists():
            return

        # Find all markdown files
        components = []
        order = 0
        for md_file in sorted(content_dir.rglob("*.md")):
            rel_path = md_file.relative_to(self.project.root)
            comp = PublicationComponent(
                source=rel_path,
                component_type=ComponentType.CHAPTER,
                order=order,
            )
            components.append(comp)
            order += 1

        if components:
            pub = Publication(
                id="default",
                title=self.project.name or "Documentation",
                publication_type=PublicationType.BOOK,
                formats=[OutputFormat.HTML, OutputFormat.PDF],
                languages=self.project.languages or ["en"],
                components=components,
                status=PublicationStatus.DRAFT,
            )
            self.publications["default"] = pub

    def _load_registry(self) -> None:
        """Load build history from registry file."""
        if not self._registry_path.exists():
            return

        try:
            with open(self._registry_path) as f:
                data = json.load(f)

            for pub_id, builds in data.get("builds", {}).items():
                self.builds[pub_id] = [
                    PublicationBuild.from_dict(b) for b in builds
                ]
        except Exception as e:
            logger.warning(f"Failed to load publication registry: {e}")

    def save(self) -> None:
        """Save registry to disk."""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "builds": {
                pub_id: [b.to_dict() for b in builds]
                for pub_id, builds in self.builds.items()
            },
            "updated_at": datetime.now().isoformat(),
        }

        with open(self._registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, pub_id: str) -> Optional[Publication]:
        """Get publication by ID."""
        return self.publications.get(pub_id)

    def list(self) -> list[Publication]:
        """List all publications."""
        return list(self.publications.values())

    def get_builds(self, pub_id: str) -> list[PublicationBuild]:
        """Get all builds for a publication."""
        return self.builds.get(pub_id, [])

    def get_latest_build(
        self,
        pub_id: str,
        format: Optional[OutputFormat] = None,
        language: Optional[str] = None,
    ) -> Optional[PublicationBuild]:
        """Get the latest build for a publication."""
        builds = self.builds.get(pub_id, [])
        if not builds:
            return None

        # Filter by format and language if specified
        filtered = builds
        if format:
            filtered = [b for b in filtered if b.format == format]
        if language:
            filtered = [b for b in filtered if b.language == language]

        if not filtered:
            return None

        # Return most recent
        return max(filtered, key=lambda b: b.completed_at or datetime.min)

    def record_build(self, build: PublicationBuild) -> None:
        """Record a new build."""
        if build.publication_id not in self.builds:
            self.builds[build.publication_id] = []
        self.builds[build.publication_id].append(build)
        self.save()

    def get_stale_components(self, pub_id: str) -> list[PublicationComponent]:
        """Get components that have changed since last build."""
        pub = self.publications.get(pub_id)
        if not pub:
            return []

        latest_build = self.get_latest_build(pub_id)
        if not latest_build:
            return pub.get_all_components()  # All components need building

        stale = []
        for comp in pub.get_all_components():
            source_path = self.project.root / comp.source
            if source_path.exists():
                current_hash = compute_file_hash(source_path)
                stored_hash = latest_build.component_hashes.get(str(comp.source))
                if current_hash != stored_hash:
                    stale.append(comp)
            else:
                stale.append(comp)

        return stale

    def get_publication_status(self, pub_id: str) -> dict:
        """Get comprehensive status for a publication."""
        pub = self.publications.get(pub_id)
        if not pub:
            return {"error": f"Publication not found: {pub_id}"}

        all_components = pub.get_all_components()
        stale_components = self.get_stale_components(pub_id)

        # Check build status per format/language
        build_status = {}
        for fmt in pub.formats:
            build_status[fmt.value] = {}
            for lang in pub.languages:
                latest = self.get_latest_build(pub_id, fmt, lang)
                if latest:
                    build_status[fmt.value][lang] = {
                        "status": latest.status.value,
                        "built_at": latest.completed_at.isoformat()
                        if latest.completed_at
                        else None,
                        "is_stale": len(stale_components) > 0,
                    }
                else:
                    build_status[fmt.value][lang] = {
                        "status": "not_built",
                        "is_stale": True,
                    }

        return {
            "id": pub_id,
            "title": pub.title,
            "type": pub.publication_type.value,
            "status": pub.status.value,
            "component_count": len(all_components),
            "stale_component_count": len(stale_components),
            "stale_components": [str(c.source) for c in stale_components],
            "formats": [f.value for f in pub.formats],
            "languages": pub.languages,
            "build_status": build_status,
            "derives_from": pub.derives_from,
        }

    def get_document_usage(self, doc_path: Path) -> dict:
        """Get which publications use a document."""
        rel_path = doc_path
        if doc_path.is_absolute():
            try:
                rel_path = doc_path.relative_to(self.project.root)
            except ValueError:
                pass

        usage = []
        for pub in self.publications.values():
            for comp in pub.get_all_components():
                if comp.source == rel_path or str(comp.source) == str(rel_path):
                    usage.append({
                        "publication_id": pub.id,
                        "publication_title": pub.title,
                        "component_type": comp.component_type.value,
                        "order": comp.order,
                    })

        return {
            "document": str(rel_path),
            "used_in": usage,
            "usage_count": len(usage),
        }
