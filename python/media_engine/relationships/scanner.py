"""
Relationship Scanner for Media Engine

Comprehensive scanning of ALL content types:
- Markdown documents (chapters, research)
- YAML video scripts → demo clips, voiceover files
- Demo definitions → states, captured videos
- Props.json → demo clip paths
- Publications → components, assets
- Slides → images, diagrams
- Diagrams → generated outputs

Tracks relationships:
- Structural hierarchy (parent_document)
- Semantic derivation (derived_from)
- Translation (source_document)
- Content references (markdown links)
- Assets (images, video clips, audio)
- Anchors (consistency constraints)
- Explicit dependencies (depends_on)
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import yaml

from ..core import compute_document_hash, compute_file_hash
from .types import DocumentNode, EdgeType, RelationshipEdge

if TYPE_CHECKING:
    from .registry import UnifiedRegistry


class RelationshipScanner:
    """
    Scans documents and populates the unified registry.

    Detects relationships from:
    - Document frontmatter (explicit relationships)
    - Document content (implicit relationships)
    - File structure (language organization)
    """

    def __init__(self, project, registry: "UnifiedRegistry"):
        self.project = project
        self.registry = registry
        self.content_dir = project.content_dir

    def full_scan(self):
        """Scan ALL content types and populate the registry."""
        # Scan all languages - markdown chapters
        for lang in self.project.languages:
            chapters = self.project.list_chapters(lang)
            for chapter_path in chapters:
                self.scan_document(chapter_path)

        # Scan markdown in research
        for pattern in ["research/**/*.md"]:
            for doc_path in self.content_dir.glob(pattern):
                if doc_path.is_file():
                    self.scan_document(doc_path)

        # Scan all YAML configurations
        for lang in self.project.languages:
            lang_dir = self.content_dir / lang

            # Video scripts
            for script_path in lang_dir.glob("scripts/*.yaml"):
                self._scan_video_script(script_path)

            # Demo definitions
            for demo_path in lang_dir.glob("demos/*.yaml"):
                self._scan_demo_definition(demo_path)

            # Publications
            for pub_path in lang_dir.glob("publications/*.yaml"):
                self._scan_publication(pub_path)

            # Slides
            for slide_path in lang_dir.glob("slides/*.yaml"):
                self._scan_slides(slide_path)

            # Diagrams (YAML and D2)
            for diag_path in lang_dir.glob("diagrams/*.yaml"):
                self._scan_diagram(diag_path)
            for diag_path in lang_dir.glob("diagrams/*.d2"):
                self._scan_d2_diagram(diag_path)

        # Scan props.json files in remotion
        remotion_dir = self.project.root / "remotion"
        if remotion_dir.exists():
            for props_path in remotion_dir.glob("**/props.json"):
                self._scan_props_json(props_path)

        # Track all assets to detect orphans
        self._scan_all_assets()

    def scan_document(self, doc_path: Path):
        """
        Scan a single document for all relationships.

        Creates:
        - DocumentNode for the document
        - RelationshipEdge for each detected relationship
        """
        from ..cms.document import Document

        try:
            doc = Document.load(doc_path)
        except Exception as e:
            print(f"Warning: Could not load {doc_path}: {e}")
            return

        # Create or update document node
        node = self._create_node(doc_path, doc)
        self.registry.add_node(node)

        # Clear existing edges for this document (we'll re-detect them)
        self.registry.remove_edges(doc_path)

        # Detect all relationship types
        self._detect_parent(doc_path, doc)
        self._detect_derived_from(doc_path, doc)
        self._detect_translation(doc_path, doc)
        self._detect_depends_on(doc_path, doc)
        self._detect_references(doc_path, doc)
        self._detect_assets(doc_path, doc)
        self._detect_anchors(doc_path, doc)
        self._detect_anchor_refs(doc_path, doc)

    def _create_node(self, doc_path: Path, doc) -> DocumentNode:
        """Create a DocumentNode from a document."""
        metadata = doc.metadata

        # Determine language from path
        language = None
        try:
            rel_path = doc_path.relative_to(self.content_dir)
            parts = rel_path.parts
            if parts and parts[0] in self.project.languages:
                language = parts[0]
        except ValueError:
            pass

        # Compute content hash
        content_hash = compute_document_hash(doc_path)

        # Parse anchors from frontmatter
        anchors = {}
        for key, value in metadata.get("anchors", {}).items():
            if isinstance(value, dict):
                anchors[key] = value
            else:
                anchors[key] = {"value": value, "type": type(value).__name__}

        return DocumentNode(
            path=doc_path,
            title=metadata.get("title", doc_path.stem),
            language=language,
            doc_type=metadata.get("doc_type", "chapter"),
            lifecycle=metadata.get("lifecycle", "living"),
            status=metadata.get("status", "draft"),
            content_hash=content_hash,
            last_modified=datetime.now(),
            owner=metadata.get("owner"),
            approvers=metadata.get("approvers", []),
            anchors=anchors,
        )

    def _detect_parent(self, doc_path: Path, doc):
        """Detect parent_document relationship."""
        parent = doc.metadata.get("parent_document")
        if not parent:
            return

        target = self._resolve_path(doc_path, parent)
        if target and target.exists():
            edge = RelationshipEdge(
                source=doc_path,
                target=target,
                edge_type=EdgeType.PARENT,
                target_hash=compute_document_hash(target) if target.exists() else None,
                recorded_at=datetime.now(),
            )
            self.registry.add_edge(edge, save=False)

    def _detect_derived_from(self, doc_path: Path, doc):
        """Detect derived_from relationships."""
        derived_from = doc.metadata.get("derived_from", [])
        if isinstance(derived_from, dict):
            derived_from = [derived_from]

        for item in derived_from:
            if isinstance(item, str):
                # Simple path string
                path = item
                relationship = "implements"
                version = None
            else:
                # Dict with path, relationship, version
                path = item.get("path")
                relationship = item.get("relationship", "implements")
                version = item.get("version")

            if not path:
                continue

            target = self._resolve_path(doc_path, path)
            if target:
                edge_type = EdgeType.from_relationship_type(relationship)
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=edge_type,
                    version=version,
                    target_hash=compute_document_hash(target) if target.exists() else None,
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _detect_translation(self, doc_path: Path, doc):
        """Detect source_document (translation) relationship."""
        source_doc = doc.metadata.get("source_document")
        if not source_doc:
            return

        target = self._resolve_path(doc_path, source_doc)
        if target and target.exists():
            # Get stored hash from frontmatter
            stored_hash = doc.metadata.get("source_content_hash")
            current_hash = compute_document_hash(target)

            edge = RelationshipEdge(
                source=doc_path,
                target=target,
                edge_type=EdgeType.TRANSLATES,
                target_hash=stored_hash,
                recorded_at=datetime.now(),
                is_stale=stored_hash != current_hash if stored_hash else False,
                stale_reason="source_changed" if stored_hash and stored_hash != current_hash else None,
            )
            self.registry.add_edge(edge, save=False)

    def _detect_depends_on(self, doc_path: Path, doc):
        """Detect explicit depends_on relationships."""
        depends_on = doc.metadata.get("depends_on", [])
        if isinstance(depends_on, str):
            depends_on = [depends_on]

        for dep in depends_on:
            target = self._resolve_path(doc_path, dep)
            if target:
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=EdgeType.DEPENDS_ON,
                    target_hash=compute_document_hash(target) if target.exists() else None,
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _detect_references(self, doc_path: Path, doc):
        """Detect markdown link references."""
        content = doc.content

        # Pattern: [text](path.md) or [text](../path.md)
        link_pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"

        for match in re.finditer(link_pattern, content):
            link_text, link_path = match.groups()

            # Skip external URLs
            if link_path.startswith(("http://", "https://", "mailto:")):
                continue

            target = self._resolve_path(doc_path, link_path)
            if target:
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=EdgeType.REFERENCES,
                    context=f"Link: {link_text[:50]}",
                    target_hash=compute_document_hash(target) if target.exists() else None,
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _detect_assets(self, doc_path: Path, doc):
        """Detect image and asset references."""
        content = doc.content

        # Pattern: ![alt](path) or ![alt](path.png)
        img_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"

        for match in re.finditer(img_pattern, content):
            alt_text, img_path = match.groups()

            # Skip external URLs
            if img_path.startswith(("http://", "https://")):
                continue

            target = self._resolve_path(doc_path, img_path)
            if target:
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=EdgeType.USES_ASSET,
                    context=f"Image: {alt_text or img_path}",
                    target_hash=compute_file_hash(target) if target.exists() else None,
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _detect_anchors(self, doc_path: Path, doc):
        """Detect and register anchors defined in document."""
        anchors = doc.metadata.get("anchors", {})

        for anchor_id, value in anchors.items():
            if isinstance(value, dict):
                anchor_value = value.get("value", value)
                value_type = value.get("type", type(anchor_value).__name__)
            else:
                anchor_value = value
                value_type = type(value).__name__

            self.registry.set_anchor(anchor_id, anchor_value, value_type, doc_path)

    def _detect_anchor_refs(self, doc_path: Path, doc):
        """Detect anchor references and create edges."""
        anchor_refs = doc.metadata.get("anchor_refs", [])

        for ref in anchor_refs:
            if isinstance(ref, dict):
                source_path = ref.get("source")
                anchor_id = ref.get("anchor")
            else:
                continue

            if not source_path or not anchor_id:
                continue

            target = self._resolve_path(doc_path, source_path)
            if target:
                # Add anchor reference edge
                edge = RelationshipEdge(
                    source=doc_path,
                    target=target,
                    edge_type=EdgeType.ANCHOR_REF,
                    context=f"anchor:{anchor_id}",
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

                # Update anchor registry
                self.registry.add_anchor_reference(anchor_id, doc_path)

    def _resolve_path(self, base: Path, relative: str) -> Optional[Path]:
        """
        Resolve a relative path to an absolute path.

        Handles multiple path formats:
        - Relative to content dir: "en/chapters/01_intro.md"
        - Relative to document: "../other.md"
        - Relative to same directory: "sibling.md"
        - Path without extension: "chapters/01_intro" -> tries .md

        FIXED: No longer resolves from document's parent directory
               when path looks like it's from content root.
        """
        # Clean up the path
        relative = relative.strip()

        # Handle absolute paths from content root
        if relative.startswith("/"):
            target = self.content_dir / relative.lstrip("/")
            return self._validate_path(target)

        # Check if path starts with a language code (content-relative)
        # or known content directory name (chapters/, research/, etc.)
        known_prefixes = set(self.project.languages) | {
            "chapters", "research", "scripts", "diagrams", "slides", "data", "assets"
        }

        first_part = relative.split("/")[0] if "/" in relative else None

        if first_part and first_part in known_prefixes:
            # Path is relative to content directory
            target = self.content_dir / relative
            return self._validate_path(target)

        # Path is relative to document location
        target = (base.parent / relative).resolve()
        return self._validate_path(target)

    def _validate_path(self, target: Path) -> Optional[Path]:
        """Validate and potentially fix a path."""
        # Check if within project
        try:
            target.relative_to(self.project.root)
        except ValueError:
            return None

        # If exists, return it
        if target.exists():
            return target

        # Try adding .md extension
        if not target.suffix:
            md_target = target.with_suffix(".md")
            if md_target.exists():
                return md_target

        # Return the target even if it doesn't exist (broken reference)
        # The edge will have no hash, signaling a missing target
        return target

    def scan_incremental(self, changed_paths: list[Path]):
        """
        Incrementally update registry for changed documents.

        More efficient than full_scan when only a few documents changed.
        """
        for doc_path in changed_paths:
            if doc_path.exists():
                self.scan_document(doc_path)
            else:
                # Document was deleted
                self.registry.remove_node(doc_path)

    # =========================================================================
    # YAML Configuration Scanners
    # =========================================================================

    def _scan_video_script(self, script_path: Path):
        """
        Scan a video script YAML for demo clip references.

        Detects:
        - demo.clipPath references to video files
        - voiceover audio references
        - source document references
        """
        try:
            with open(script_path) as f:
                script = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load video script {script_path}: {e}")
            return

        if not script:
            return

        # Create node for the script
        node = DocumentNode(
            path=script_path,
            title=script.get("title", script_path.stem),
            language=self._detect_language(script_path),
            doc_type="video_script",
            content_hash=compute_file_hash(script_path),
            last_modified=datetime.now(),
        )
        self.registry.add_node(node)
        self.registry.remove_edges(script_path)

        # Scan scenes for demo clips
        scenes = script.get("scenes", [])
        demo_base = script.get("demo_base_path", "demos/")

        for scene in scenes:
            demo = scene.get("demo", {})
            clip_path = demo.get("clipPath")

            if clip_path:
                # Resolve clip path relative to remotion/public or project root
                target = self._resolve_video_clip(script_path, clip_path, demo_base)
                if target:
                    edge = RelationshipEdge(
                        source=script_path,
                        target=target,
                        edge_type=EdgeType.USES_ASSET,
                        context=f"Scene: {scene.get('id', 'unknown')}",
                        target_hash=compute_file_hash(target) if target.exists() else None,
                        recorded_at=datetime.now(),
                    )
                    self.registry.add_edge(edge, save=False)

        # Check for source documents reference
        source_docs = script.get("source_documents", [])
        for source in source_docs:
            target = self._resolve_path(script_path, source)
            if target:
                edge = RelationshipEdge(
                    source=script_path,
                    target=target,
                    edge_type=EdgeType.DEPENDS_ON,
                    context="Source document",
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _scan_demo_definition(self, demo_path: Path):
        """
        Scan a demo definition YAML for state and video mappings.

        Detects:
        - States that should have corresponding video clips
        - Sequences of states
        """
        try:
            with open(demo_path) as f:
                demo = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load demo definition {demo_path}: {e}")
            return

        if not demo:
            return

        # Create node for the demo definition
        node = DocumentNode(
            path=demo_path,
            title=demo.get("title", demo_path.stem),
            language=self._detect_language(demo_path),
            doc_type="demo_definition",
            content_hash=compute_file_hash(demo_path),
            last_modified=datetime.now(),
        )
        self.registry.add_node(node)
        self.registry.remove_edges(demo_path)

        # Scan states for expected video outputs
        states = demo.get("states", {})
        for state_id, state_config in states.items():
            # Each state may generate a video clip
            expected_clip = self.project.root / "demos" / f"{state_id}.mp4"
            if expected_clip.exists():
                edge = RelationshipEdge(
                    source=demo_path,
                    target=expected_clip,
                    edge_type=EdgeType.GENERATES,
                    context=f"State: {state_id}",
                    target_hash=compute_file_hash(expected_clip),
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _scan_publication(self, pub_path: Path):
        """
        Scan a publication YAML for component references.

        Detects:
        - Component source paths
        - Asset references
        """
        try:
            with open(pub_path) as f:
                pub = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load publication {pub_path}: {e}")
            return

        if not pub:
            return

        # Create node
        node = DocumentNode(
            path=pub_path,
            title=pub.get("title", pub_path.stem),
            language=self._detect_language(pub_path),
            doc_type="publication",
            content_hash=compute_file_hash(pub_path),
            last_modified=datetime.now(),
        )
        self.registry.add_node(node)
        self.registry.remove_edges(pub_path)

        # Scan parts and components
        parts = pub.get("parts", [])
        for part in parts:
            components = part.get("components", [])
            for comp in components:
                source = comp.get("source")
                if source:
                    target = self._resolve_path(pub_path, source)
                    if target:
                        edge = RelationshipEdge(
                            source=pub_path,
                            target=target,
                            edge_type=EdgeType.DEPENDS_ON,
                            context=f"Component: {comp.get('type', 'unknown')}",
                            target_hash=compute_file_hash(target) if target.exists() else None,
                            recorded_at=datetime.now(),
                        )
                        self.registry.add_edge(edge, save=False)

    def _scan_slides(self, slide_path: Path):
        """
        Scan a slides YAML for image and asset references.
        """
        try:
            with open(slide_path) as f:
                slides = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load slides {slide_path}: {e}")
            return

        if not slides:
            return

        # Create node
        node = DocumentNode(
            path=slide_path,
            title=slides.get("title", slide_path.stem),
            language=self._detect_language(slide_path),
            doc_type="slides",
            content_hash=compute_file_hash(slide_path),
            last_modified=datetime.now(),
        )
        self.registry.add_node(node)
        self.registry.remove_edges(slide_path)

        # Recursively find image references
        self._scan_yaml_for_images(slide_path, slides)

    def _scan_diagram(self, diag_path: Path):
        """
        Scan a diagram YAML definition.
        """
        try:
            with open(diag_path) as f:
                diag = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load diagram {diag_path}: {e}")
            return

        if not diag:
            return

        # Create node
        node = DocumentNode(
            path=diag_path,
            title=diag.get("title", diag_path.stem),
            language=self._detect_language(diag_path),
            doc_type="diagram",
            content_hash=compute_file_hash(diag_path),
            last_modified=datetime.now(),
        )
        self.registry.add_node(node)

        # Check for generated outputs
        output_dir = self.project.root / "output" / "diagrams"
        for ext in [".png", ".svg"]:
            output_file = output_dir / (diag_path.stem + ext)
            if output_file.exists():
                edge = RelationshipEdge(
                    source=diag_path,
                    target=output_file,
                    edge_type=EdgeType.GENERATES,
                    context=f"Generated {ext}",
                    target_hash=compute_file_hash(output_file),
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _scan_d2_diagram(self, diag_path: Path):
        """
        Scan a D2 diagram file.
        """
        # Create node
        node = DocumentNode(
            path=diag_path,
            title=diag_path.stem,
            language=self._detect_language(diag_path),
            doc_type="diagram_d2",
            content_hash=compute_file_hash(diag_path),
            last_modified=datetime.now(),
        )
        self.registry.add_node(node)

        # Check for generated outputs
        output_dir = self.project.root / "output" / "diagrams"
        for ext in [".png", ".svg"]:
            output_file = output_dir / (diag_path.stem + ext)
            if output_file.exists():
                edge = RelationshipEdge(
                    source=diag_path,
                    target=output_file,
                    edge_type=EdgeType.GENERATES,
                    context=f"Generated {ext}",
                    target_hash=compute_file_hash(output_file),
                    recorded_at=datetime.now(),
                )
                self.registry.add_edge(edge, save=False)

    def _scan_props_json(self, props_path: Path):
        """
        Scan a Remotion props.json for demo clip references.
        """
        try:
            with open(props_path) as f:
                props = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load props.json {props_path}: {e}")
            return

        if not props:
            return

        # Create node
        node = DocumentNode(
            path=props_path,
            title=props.get("title", "props"),
            doc_type="remotion_props",
            content_hash=compute_file_hash(props_path),
            last_modified=datetime.now(),
        )
        self.registry.add_node(node)
        self.registry.remove_edges(props_path)

        # Scan scenes for demo clips
        scenes = props.get("scenes", [])
        for scene in scenes:
            demo = scene.get("demo", {})
            clip_path = demo.get("clipPath")

            if clip_path:
                # Resolve relative to props.json location
                target = (props_path.parent / clip_path).resolve()
                if target.exists():
                    edge = RelationshipEdge(
                        source=props_path,
                        target=target,
                        edge_type=EdgeType.USES_ASSET,
                        context=f"Scene: {scene.get('id', 'unknown')}",
                        target_hash=compute_file_hash(target),
                        recorded_at=datetime.now(),
                    )
                    self.registry.add_edge(edge, save=False)

    def _scan_all_assets(self):
        """
        Scan all asset directories and register assets as nodes.

        This enables orphan detection - assets not referenced by anything.
        """
        asset_patterns = [
            ("demos/*.mp4", "video_clip"),
            ("assets/images/*.png", "image"),
            ("assets/images/*.svg", "image"),
            ("assets/images/*.jpg", "image"),
            ("brand/logos/*.png", "logo"),
            ("brand/logos/*.svg", "logo"),
        ]

        # Scan project root assets
        for pattern, asset_type in asset_patterns:
            for asset_path in self.project.root.glob(pattern):
                if asset_path.is_file():
                    self._register_asset(asset_path, asset_type)

        # Scan content assets per language
        for lang in self.project.languages:
            lang_dir = self.content_dir / lang
            for pattern, asset_type in asset_patterns:
                for asset_path in lang_dir.glob(pattern):
                    if asset_path.is_file():
                        self._register_asset(asset_path, asset_type)

        # Scan remotion assets
        remotion_dir = self.project.root / "remotion" / "public"
        if remotion_dir.exists():
            for asset_path in remotion_dir.glob("demos/*.mp4"):
                self._register_asset(asset_path, "video_clip")

    def _register_asset(self, asset_path: Path, asset_type: str):
        """Register an asset as a node for orphan detection."""
        if str(asset_path) in [str(n.path) for n in self.registry._nodes.values()]:
            return  # Already registered

        node = DocumentNode(
            path=asset_path,
            title=asset_path.name,
            doc_type=asset_type,
            content_hash=compute_file_hash(asset_path),
            last_modified=datetime.now(),
        )
        self.registry.add_node(node)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _detect_language(self, path: Path) -> Optional[str]:
        """Detect language from path."""
        try:
            rel_path = path.relative_to(self.content_dir)
            parts = rel_path.parts
            if parts and parts[0] in self.project.languages:
                return parts[0]
        except ValueError:
            pass
        return None

    def _resolve_video_clip(
        self, base: Path, clip_path: str, demo_base: str
    ) -> Optional[Path]:
        """Resolve a video clip path."""
        # Try relative to remotion/public
        remotion_public = self.project.root / "remotion" / "public"
        target = remotion_public / clip_path
        if target.exists():
            return target

        # Try relative to project demos
        target = self.project.root / "demos" / clip_path.replace(demo_base, "")
        if target.exists():
            return target

        # Try as given
        target = self.project.root / clip_path
        if target.exists():
            return target

        return None

    def _scan_yaml_for_images(self, source_path: Path, data: Any, depth: int = 0):
        """Recursively scan YAML data for image references."""
        if depth > 10:  # Prevent infinite recursion
            return

        if isinstance(data, dict):
            for key, value in data.items():
                # Check for image keys
                if key in ("image", "icon", "logo", "background", "src"):
                    if isinstance(value, str) and self._looks_like_image(value):
                        target = self._resolve_path(source_path, value)
                        if target:
                            edge = RelationshipEdge(
                                source=source_path,
                                target=target,
                                edge_type=EdgeType.USES_ASSET,
                                context=f"YAML key: {key}",
                                target_hash=compute_file_hash(target) if target.exists() else None,
                                recorded_at=datetime.now(),
                            )
                            self.registry.add_edge(edge, save=False)
                else:
                    self._scan_yaml_for_images(source_path, value, depth + 1)
        elif isinstance(data, list):
            for item in data:
                self._scan_yaml_for_images(source_path, item, depth + 1)

    def _looks_like_image(self, value: str) -> bool:
        """Check if a string looks like an image path."""
        if not isinstance(value, str):
            return False
        return value.lower().endswith((".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"))


__all__ = ["RelationshipScanner"]
