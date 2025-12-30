"""
Cascade Regeneration Module

Handles automatic regeneration of downstream video components when
upstream components change. Maintains dependency order and tracks
progress through WebSocket events.

Usage:
    from media_engine.video.cascade import CascadeRegenerator

    regenerator = CascadeRegenerator(project, video_project)
    affected = await regenerator.on_component_changed("script_abc123")
    # All downstream components are now queued for regeneration

Component Dependency Graph:
    script → voiceover → captions
          → demo_clips → props → render

When a component changes:
1. Mark all downstream components as stale
2. Queue regeneration in dependency order
3. Track progress and report via callbacks
4. Handle errors gracefully (don't block siblings)
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from .project import (
    COMPONENT_DEPENDENCIES,
    ComponentStatus,
    ComponentType,
    VideoComponent,
    VideoProject,
    VideoProjectRegistry,
)

if TYPE_CHECKING:
    from ..core.project import Project


class RegenerationStatus(str, Enum):
    """Status of a regeneration operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class RegenerationTask:
    """A single component regeneration task."""
    component_id: str
    component_type: ComponentType
    status: RegenerationStatus = RegenerationStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class RegenerationResult:
    """Result of a cascade regeneration."""
    success: bool
    affected_components: list[str]
    regenerated: list[str]
    failed: list[str]
    skipped: list[str]
    duration: float = 0.0
    error: Optional[str] = None


class CascadeRegenerator:
    """
    Manages cascade regeneration of video project components.

    When an upstream component changes, automatically marks downstream
    components as stale and queues them for regeneration in the correct
    dependency order.
    """

    def __init__(
        self,
        project: "Project",
        video_project: VideoProject,
        on_progress: Optional[Callable[[str, RegenerationStatus, Optional[str]], None]] = None,
    ):
        """
        Initialize the cascade regenerator.

        Args:
            project: Media Engine project
            video_project: Video project to regenerate
            on_progress: Optional callback for progress updates
                         (component_id, status, optional_message)
        """
        self.project = project
        self.video_project = video_project
        self.on_progress = on_progress
        self._tasks: dict[str, RegenerationTask] = {}

    def _report_progress(
        self,
        component_id: str,
        status: RegenerationStatus,
        message: Optional[str] = None,
    ):
        """Report progress to callback if registered."""
        if self.on_progress:
            self.on_progress(component_id, status, message)

    def get_downstream_components(self, component_id: str) -> list[str]:
        """
        Get all components that depend on the given component.

        Performs a breadth-first traversal of the dependency graph
        to find all transitive dependents.

        Args:
            component_id: Starting component ID

        Returns:
            List of component IDs that depend on this component
        """
        return self.video_project.get_downstream_components(component_id)

    def get_regeneration_order(self, component_ids: list[str]) -> list[str]:
        """
        Sort components into regeneration order based on dependencies.

        Components with fewer dependencies come first.

        Args:
            component_ids: List of component IDs to sort

        Returns:
            Sorted list with dependencies before dependents
        """
        # Build a map of component to dependency count
        components = {
            cid: self.video_project.components[cid]
            for cid in component_ids
            if cid in self.video_project.components
        }

        # Count dependencies within the set
        dep_counts = {}
        for cid, comp in components.items():
            count = sum(1 for dep in comp.depends_on if dep in component_ids)
            dep_counts[cid] = count

        # Sort by dependency count (fewest first)
        return sorted(component_ids, key=lambda cid: dep_counts.get(cid, 0))

    def mark_stale(self, component_id: str, cascade: bool = True) -> list[str]:
        """
        Mark a component (and optionally its dependents) as stale.

        Args:
            component_id: Component to mark stale
            cascade: Whether to also mark downstream components

        Returns:
            List of all component IDs marked stale
        """
        affected = [component_id]

        if cascade:
            downstream = self.get_downstream_components(component_id)
            affected.extend(downstream)

        for cid in affected:
            if cid in self.video_project.components:
                self.video_project.components[cid].mark_stale()

        return affected

    async def regenerate_component(self, component: VideoComponent) -> bool:
        """
        Regenerate a single component.

        This is the core regeneration logic. Override in subclasses
        to implement actual generation for each component type.

        Args:
            component: Component to regenerate

        Returns:
            True if regeneration succeeded
        """
        self._report_progress(component.id, RegenerationStatus.IN_PROGRESS)

        try:
            component.mark_generating()

            # Dispatch to type-specific generator
            success = await self._dispatch_regeneration(component)

            if success:
                component.mark_ready(generated_by="cascade")
                self._report_progress(component.id, RegenerationStatus.COMPLETED)
            else:
                component.mark_error("Regeneration failed")
                self._report_progress(component.id, RegenerationStatus.FAILED)

            return success

        except Exception as e:
            component.mark_error(str(e))
            self._report_progress(component.id, RegenerationStatus.FAILED, str(e))
            return False

    async def _dispatch_regeneration(self, component: VideoComponent) -> bool:
        """
        Dispatch regeneration to type-specific handler.

        Args:
            component: Component to regenerate

        Returns:
            True if regeneration succeeded
        """
        handlers = {
            ComponentType.SCRIPT: self._regenerate_script,
            ComponentType.DEMO_DEFINITION: self._regenerate_demo_definition,
            ComponentType.DEMO_CLIP: self._regenerate_demo_clip,
            ComponentType.VOICEOVER: self._regenerate_voiceover,
            ComponentType.CAPTIONS: self._regenerate_captions,
            ComponentType.PROPS: self._regenerate_props,
            ComponentType.RENDER: self._regenerate_render,
        }

        handler = handlers.get(component.type)
        if handler:
            return await handler(component)

        # Unknown type - mark as skipped
        return True

    async def _regenerate_script(self, component: VideoComponent) -> bool:
        """Regenerate a script component (usually manual or AI-generated)."""
        # Scripts are typically modified manually or by AI
        # For now, just validate the file exists
        return component.path.exists()

    async def _regenerate_demo_definition(self, component: VideoComponent) -> bool:
        """Regenerate a demo definition (usually manual or AI-generated)."""
        # Demo definitions are typically modified manually
        return component.path.exists()

    async def _regenerate_demo_clip(self, component: VideoComponent) -> bool:
        """Regenerate a demo clip by re-capturing."""
        from .video_capture import VideoCaptureEngine, RecordingConfig
        from .demo_capture import load_demo_definition

        # Find the demo definition for this clip
        demo_def_comp = None
        for dep_id in component.depends_on:
            dep = self.video_project.components.get(dep_id)
            if dep and dep.type == ComponentType.DEMO_DEFINITION:
                demo_def_comp = dep
                break

        if not demo_def_comp or not demo_def_comp.path.exists():
            return False

        # Load demo definition
        definition = load_demo_definition(demo_def_comp.path)

        # Get state ID from component metadata or scene_id
        state_id = component.scene_id or component.metadata.get("state_id")
        if not state_id or state_id not in definition.states:
            return False

        # Capture the state as video
        config = RecordingConfig(
            width=definition.viewport_width,
            height=definition.viewport_height,
        )

        async with VideoCaptureEngine(config=config) as engine:
            result = await engine.capture_demo_state(
                demo_definition=definition,
                state_id=state_id,
                output_path=component.path,
            )

        return result.success

    async def _regenerate_voiceover(self, component: VideoComponent) -> bool:
        """Regenerate voiceover audio."""
        from .voiceover import generate_voiceover_for_script

        # Find the script component
        script_comp = None
        for dep_id in component.depends_on:
            dep = self.video_project.components.get(dep_id)
            if dep and dep.type == ComponentType.SCRIPT:
                script_comp = dep
                break

        if not script_comp or not script_comp.path.exists():
            return False

        try:
            result = await generate_voiceover_for_script(
                script_path=script_comp.path,
                output_path=component.path,
                cache_dir=self.project.cache_dir / "voiceover",
            )
            return result.success
        except Exception:
            return False

    async def _regenerate_captions(self, component: VideoComponent) -> bool:
        """Regenerate captions from voiceover timing."""
        from .captions import generate_captions_for_script

        # Find the voiceover component for timing
        voiceover_comp = None
        for dep_id in component.depends_on:
            dep = self.video_project.components.get(dep_id)
            if dep and dep.type == ComponentType.VOICEOVER:
                voiceover_comp = dep
                break

        # Find the script component for text
        script_comp = None
        for comp in self.video_project.components.values():
            if comp.type == ComponentType.SCRIPT:
                script_comp = comp
                break

        if not script_comp or not script_comp.path.exists():
            return False

        try:
            generate_captions_for_script(
                script_path=script_comp.path,
                output_path=component.path,
            )
            return component.path.exists()
        except Exception:
            return False

    async def _regenerate_props(self, component: VideoComponent) -> bool:
        """Regenerate Remotion props JSON."""
        from .builder import VideoBuilder

        # Find script component
        script_comp = None
        for comp in self.video_project.components.values():
            if comp.type == ComponentType.SCRIPT:
                script_comp = comp
                break

        if not script_comp or not script_comp.path.exists():
            return False

        try:
            builder = VideoBuilder(self.project)
            props = builder.generate_props(script_comp.path)

            # Write props to file
            import json
            component.path.parent.mkdir(parents=True, exist_ok=True)
            component.path.write_text(json.dumps(props, indent=2))

            return True
        except Exception:
            return False

    async def _regenerate_render(self, component: VideoComponent) -> bool:
        """Regenerate final video render."""
        # Find props component
        props_comp = None
        for dep_id in component.depends_on:
            dep = self.video_project.components.get(dep_id)
            if dep and dep.type == ComponentType.PROPS:
                props_comp = dep
                break

        if not props_comp or not props_comp.path.exists():
            return False

        # Render is typically done via Remotion CLI
        # For now, mark as pending for manual trigger
        return False  # Requires manual render trigger

    async def on_component_changed(
        self,
        component_id: str,
        cascade: bool = True,
    ) -> RegenerationResult:
        """
        Handle a component change and cascade regeneration.

        Args:
            component_id: ID of the changed component
            cascade: Whether to cascade to downstream components

        Returns:
            RegenerationResult with details of what was regenerated
        """
        start_time = datetime.now()
        regenerated = []
        failed = []
        skipped = []

        # Mark affected components as stale
        affected = self.mark_stale(component_id, cascade=cascade)

        # Get regeneration order (skip the changed component itself)
        to_regenerate = [cid for cid in affected if cid != component_id]
        ordered = self.get_regeneration_order(to_regenerate)

        # Regenerate each component
        for cid in ordered:
            component = self.video_project.components.get(cid)
            if not component:
                skipped.append(cid)
                continue

            # Check if dependencies are ready
            deps_ready = all(
                self.video_project.components.get(dep_id, VideoComponent(
                    id="", type=ComponentType.SCRIPT, path=Path("")
                )).status == ComponentStatus.READY
                for dep_id in component.depends_on
                if dep_id in self.video_project.components
            )

            if not deps_ready:
                # Skip if dependencies not ready
                skipped.append(cid)
                self._report_progress(cid, RegenerationStatus.SKIPPED, "Dependencies not ready")
                continue

            # Regenerate
            success = await self.regenerate_component(component)
            if success:
                regenerated.append(cid)
            else:
                failed.append(cid)

        # Save updated project
        registry = VideoProjectRegistry(self.project)
        registry.update(self.video_project)

        duration = (datetime.now() - start_time).total_seconds()

        return RegenerationResult(
            success=len(failed) == 0,
            affected_components=affected,
            regenerated=regenerated,
            failed=failed,
            skipped=skipped,
            duration=duration,
            error=f"{len(failed)} components failed" if failed else None,
        )

    async def regenerate_all_stale(self) -> RegenerationResult:
        """
        Regenerate all stale components in the project.

        Returns:
            RegenerationResult with details
        """
        start_time = datetime.now()
        regenerated = []
        failed = []
        skipped = []

        # Get all stale components
        stale = self.video_project.get_stale_components()
        if not stale:
            return RegenerationResult(
                success=True,
                affected_components=[],
                regenerated=[],
                failed=[],
                skipped=[],
            )

        # Order by dependencies
        stale_ids = [c.id for c in stale]
        ordered = self.get_regeneration_order(stale_ids)

        # Regenerate each
        for cid in ordered:
            component = self.video_project.components.get(cid)
            if not component:
                continue

            # Check dependencies
            deps_ready = all(
                self.video_project.components.get(dep_id, VideoComponent(
                    id="", type=ComponentType.SCRIPT, path=Path("")
                )).status == ComponentStatus.READY
                for dep_id in component.depends_on
                if dep_id in self.video_project.components
            )

            if not deps_ready:
                skipped.append(cid)
                continue

            success = await self.regenerate_component(component)
            if success:
                regenerated.append(cid)
            else:
                failed.append(cid)

        # Save
        registry = VideoProjectRegistry(self.project)
        registry.update(self.video_project)

        duration = (datetime.now() - start_time).total_seconds()

        return RegenerationResult(
            success=len(failed) == 0,
            affected_components=stale_ids,
            regenerated=regenerated,
            failed=failed,
            skipped=skipped,
            duration=duration,
        )


async def cascade_regenerate(
    project: "Project",
    video_project_id: str,
    changed_component_id: str,
) -> RegenerationResult:
    """
    Convenience function to trigger cascade regeneration.

    Args:
        project: Media Engine project
        video_project_id: Video project ID
        changed_component_id: ID of the changed component

    Returns:
        RegenerationResult with details
    """
    registry = VideoProjectRegistry(project)
    video_project = registry.get(video_project_id)

    if not video_project:
        return RegenerationResult(
            success=False,
            affected_components=[],
            regenerated=[],
            failed=[],
            skipped=[],
            error=f"Video project '{video_project_id}' not found",
        )

    regenerator = CascadeRegenerator(project, video_project)
    return await regenerator.on_component_changed(changed_component_id)
