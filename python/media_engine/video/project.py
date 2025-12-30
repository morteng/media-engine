"""
Video Project Model

Manages video production projects with component tracking and dependency management.
Each project represents a complete video production with script, demo clips, voiceover,
captions, and final render - all tracked as components with status and dependencies.

Usage:
    from media_engine.video.project import VideoProject, VideoProjectRegistry

    registry = VideoProjectRegistry(project)
    video_project = registry.create("dashboard-demo", "en", ["content/en/chapters/01.md"])
    video_project.add_component("script", ComponentType.SCRIPT, Path("script.yaml"))
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional
import json
import uuid

from ..core.hashing import compute_file_hash, compute_short_hash

if TYPE_CHECKING:
    from ..core.project import Project


class ProjectStatus(str, Enum):
    """Status of a video project."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    RENDERING = "rendering"
    PUBLISHED = "published"


class ComponentType(str, Enum):
    """Type of video component."""
    SCRIPT = "script"
    DEMO_DEFINITION = "demo_definition"
    DEMO_CLIP = "demo_clip"
    VOICEOVER = "voiceover"
    CAPTIONS = "captions"
    PROPS = "props"
    RENDER = "render"


class ComponentStatus(str, Enum):
    """Status of a video component."""
    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    STALE = "stale"
    ERROR = "error"


# Component dependency graph: each type depends on these upstream types
COMPONENT_DEPENDENCIES: dict[ComponentType, list[ComponentType]] = {
    ComponentType.SCRIPT: [],
    ComponentType.DEMO_DEFINITION: [ComponentType.SCRIPT],
    ComponentType.DEMO_CLIP: [ComponentType.DEMO_DEFINITION],
    ComponentType.VOICEOVER: [ComponentType.SCRIPT],
    ComponentType.CAPTIONS: [ComponentType.VOICEOVER],
    ComponentType.PROPS: [ComponentType.DEMO_CLIP, ComponentType.CAPTIONS],
    ComponentType.RENDER: [ComponentType.PROPS],
}


@dataclass
class VideoComponent:
    """
    A component in a video project (script, clip, voiceover, etc.).

    Tracks the file path, content hash, status, and dependencies.
    When a dependency changes, downstream components are marked stale.
    """
    id: str
    type: ComponentType
    path: Path
    content_hash: str = ""
    status: ComponentStatus = ComponentStatus.PENDING
    scene_id: Optional[str] = None  # For per-scene components like clips
    depends_on: list[str] = field(default_factory=list)  # Component IDs
    generated_at: Optional[datetime] = None
    generated_by: Optional[str] = None  # "ai", "human", "system"
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "id": self.id,
            "type": self.type.value,
            "path": str(self.path),
            "content_hash": self.content_hash,
            "status": self.status.value,
            "scene_id": self.scene_id,
            "depends_on": self.depends_on,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "generated_by": self.generated_by,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoComponent":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            type=ComponentType(data["type"]),
            path=Path(data["path"]),
            content_hash=data.get("content_hash", ""),
            status=ComponentStatus(data.get("status", "pending")),
            scene_id=data.get("scene_id"),
            depends_on=data.get("depends_on", []),
            generated_at=datetime.fromisoformat(data["generated_at"]) if data.get("generated_at") else None,
            generated_by=data.get("generated_by"),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
        )

    def update_hash(self) -> bool:
        """
        Update content hash from file. Returns True if hash changed.
        """
        if not self.path.exists():
            return False
        new_hash = compute_file_hash(self.path)
        if new_hash != self.content_hash:
            self.content_hash = new_hash
            return True
        return False

    def mark_ready(self, generated_by: str = "system"):
        """Mark component as ready."""
        self.status = ComponentStatus.READY
        self.generated_at = datetime.now()
        self.generated_by = generated_by
        self.error_message = None
        self.update_hash()

    def mark_stale(self):
        """Mark component as stale (needs regeneration)."""
        self.status = ComponentStatus.STALE

    def mark_generating(self):
        """Mark component as currently generating."""
        self.status = ComponentStatus.GENERATING

    def mark_error(self, message: str):
        """Mark component as errored."""
        self.status = ComponentStatus.ERROR
        self.error_message = message


@dataclass
class VideoProject:
    """
    A video production project with tracked components.

    Manages the full lifecycle from source documents through script,
    demo captures, voiceover, and final render.
    """
    id: str
    name: str
    language: str
    status: ProjectStatus = ProjectStatus.DRAFT
    script_path: Optional[Path] = None
    demo_definition_path: Optional[Path] = None
    source_documents: list[Path] = field(default_factory=list)
    components: dict[str, VideoComponent] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "status": self.status.value,
            "script_path": str(self.script_path) if self.script_path else None,
            "demo_definition_path": str(self.demo_definition_path) if self.demo_definition_path else None,
            "source_documents": [str(p) for p in self.source_documents],
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoProject":
        """Deserialize from dictionary."""
        components = {}
        for comp_id, comp_data in data.get("components", {}).items():
            components[comp_id] = VideoComponent.from_dict(comp_data)

        return cls(
            id=data["id"],
            name=data["name"],
            language=data.get("language", "en"),
            status=ProjectStatus(data.get("status", "draft")),
            script_path=Path(data["script_path"]) if data.get("script_path") else None,
            demo_definition_path=Path(data["demo_definition_path"]) if data.get("demo_definition_path") else None,
            source_documents=[Path(p) for p in data.get("source_documents", [])],
            components=components,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            modified_at=datetime.fromisoformat(data["modified_at"]) if data.get("modified_at") else datetime.now(),
            metadata=data.get("metadata", {}),
        )

    def add_component(
        self,
        name: str,
        comp_type: ComponentType,
        path: Path,
        scene_id: Optional[str] = None,
        depends_on: Optional[list[str]] = None,
    ) -> VideoComponent:
        """
        Add a component to the project.

        Args:
            name: Human-readable name for the component
            comp_type: Type of component
            path: Path to the component file
            scene_id: Optional scene ID for per-scene components
            depends_on: Optional list of component IDs this depends on

        Returns:
            The created VideoComponent
        """
        # Generate unique ID
        comp_id = f"{comp_type.value}"
        if scene_id:
            comp_id = f"{comp_type.value}_{scene_id}"
        comp_id = f"{comp_id}_{compute_short_hash(f'{self.id}_{name}_{comp_type.value}')}"

        # Auto-resolve dependencies if not specified
        if depends_on is None:
            depends_on = self._resolve_dependencies(comp_type, scene_id)

        component = VideoComponent(
            id=comp_id,
            type=comp_type,
            path=path,
            scene_id=scene_id,
            depends_on=depends_on,
        )

        if path.exists():
            component.update_hash()
            component.status = ComponentStatus.READY

        self.components[comp_id] = component
        self.modified_at = datetime.now()
        return component

    def _resolve_dependencies(
        self,
        comp_type: ComponentType,
        scene_id: Optional[str] = None,
    ) -> list[str]:
        """Auto-resolve component dependencies based on type."""
        dep_types = COMPONENT_DEPENDENCIES.get(comp_type, [])
        deps = []

        for dep_type in dep_types:
            # Find matching components of this type
            for comp in self.components.values():
                if comp.type == dep_type:
                    # For scene-specific deps, match scene_id
                    if scene_id and comp.scene_id:
                        if comp.scene_id == scene_id:
                            deps.append(comp.id)
                    else:
                        deps.append(comp.id)

        return deps

    def get_component(self, comp_id: str) -> Optional[VideoComponent]:
        """Get a component by ID."""
        return self.components.get(comp_id)

    def get_components_by_type(self, comp_type: ComponentType) -> list[VideoComponent]:
        """Get all components of a specific type."""
        return [c for c in self.components.values() if c.type == comp_type]

    def get_downstream_components(self, comp_id: str) -> list[str]:
        """
        Get all components that depend on this component (directly or transitively).
        """
        downstream = []
        to_check = [comp_id]
        checked = set()

        while to_check:
            current = to_check.pop(0)
            if current in checked:
                continue
            checked.add(current)

            for comp in self.components.values():
                if current in comp.depends_on and comp.id not in downstream:
                    downstream.append(comp.id)
                    to_check.append(comp.id)

        return downstream

    def mark_component_stale(self, comp_id: str) -> list[str]:
        """
        Mark a component and all downstream components as stale.

        Returns list of component IDs that were marked stale.
        """
        affected = [comp_id]
        downstream = self.get_downstream_components(comp_id)
        affected.extend(downstream)

        for cid in affected:
            if cid in self.components:
                self.components[cid].mark_stale()

        self.modified_at = datetime.now()
        return affected

    def get_stale_components(self) -> list[VideoComponent]:
        """Get all stale components that need regeneration."""
        return [c for c in self.components.values() if c.status == ComponentStatus.STALE]

    def get_pending_components(self) -> list[VideoComponent]:
        """Get all pending components."""
        return [c for c in self.components.values() if c.status == ComponentStatus.PENDING]

    def get_ready_components(self) -> list[VideoComponent]:
        """Get all ready components."""
        return [c for c in self.components.values() if c.status == ComponentStatus.READY]

    def check_component_hashes(self) -> list[str]:
        """
        Check all component hashes and mark stale if changed.

        Returns list of component IDs that changed.
        """
        changed = []
        for comp in self.components.values():
            if comp.path.exists() and comp.update_hash():
                changed.append(comp.id)
                # Mark downstream components stale
                self.mark_component_stale(comp.id)

        return changed

    @property
    def is_complete(self) -> bool:
        """Check if all components are ready."""
        return all(c.status == ComponentStatus.READY for c in self.components.values())

    @property
    def progress(self) -> float:
        """Get completion progress as percentage."""
        if not self.components:
            return 0.0
        ready = sum(1 for c in self.components.values() if c.status == ComponentStatus.READY)
        return (ready / len(self.components)) * 100


class VideoProjectRegistry:
    """
    Registry for managing video projects.

    Projects are stored in .media-engine/video/projects.json
    """

    def __init__(self, project: "Project"):
        self.project = project
        self._storage_path = project.root / ".media-engine" / "video" / "projects.json"
        self._projects: dict[str, VideoProject] = {}
        self._load()

    def _load(self):
        """Load projects from storage."""
        if self._storage_path.exists():
            data = json.loads(self._storage_path.read_text())
            for proj_data in data.get("projects", []):
                proj = VideoProject.from_dict(proj_data)
                self._projects[proj.id] = proj

    def _save(self):
        """Save projects to storage."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "projects": [p.to_dict() for p in self._projects.values()],
            "modified_at": datetime.now().isoformat(),
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def create(
        self,
        name: str,
        language: str = "en",
        source_documents: Optional[list[Path]] = None,
    ) -> VideoProject:
        """
        Create a new video project.

        Args:
            name: Project name
            language: Language code
            source_documents: Source document paths

        Returns:
            Created VideoProject
        """
        project_id = f"vp_{compute_short_hash(f'{name}_{datetime.now().isoformat()}')}"

        project = VideoProject(
            id=project_id,
            name=name,
            language=language,
            source_documents=source_documents or [],
        )

        self._projects[project_id] = project
        self._save()
        return project

    def get(self, project_id: str) -> Optional[VideoProject]:
        """Get a project by ID."""
        return self._projects.get(project_id)

    def list(self, status: Optional[ProjectStatus] = None) -> list[VideoProject]:
        """
        List all projects, optionally filtered by status.
        """
        projects = list(self._projects.values())
        if status:
            projects = [p for p in projects if p.status == status]
        return sorted(projects, key=lambda p: p.modified_at, reverse=True)

    def update(self, project: VideoProject) -> VideoProject:
        """Update a project."""
        project.modified_at = datetime.now()
        self._projects[project.id] = project
        self._save()
        return project

    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self._projects:
            del self._projects[project_id]
            self._save()
            return True
        return False

    def get_by_name(self, name: str) -> Optional[VideoProject]:
        """Get a project by name."""
        for project in self._projects.values():
            if project.name == name:
                return project
        return None


def generate_project_id(name: str) -> str:
    """Generate a unique project ID."""
    return f"vp_{compute_short_hash(f'{name}_{uuid.uuid4().hex}')}"
