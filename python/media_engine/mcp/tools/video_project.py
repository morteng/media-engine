"""Video Project MCP tools.

Tools for AI-assisted video project management:
- Create and manage video projects
- Add and track components
- Handle review comments
- Trigger cascade regeneration
- Resolve AI-processed comments
"""

import json
from pathlib import Path


def register_video_project_tools(mcp, server_instance):
    """Register video project MCP tools."""

    @mcp.tool()
    async def create_video_project(
        name: str,
        source_documents: list[str] = None,
        language: str = "en",
        generate_script: bool = False,
    ) -> str:
        """
        Create a new video project.

        Args:
            name: Project name (e.g., "Dashboard Demo", "Feature Overview")
            source_documents: List of source document paths to base video on
            language: Language code for the video
            generate_script: Whether to auto-generate an initial script from sources

        Returns:
            JSON with created project details including ID and status
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.project import VideoProjectRegistry

            registry = VideoProjectRegistry(server_instance.project)

            # Validate source documents
            source_paths = []
            if source_documents:
                for doc_path in source_documents:
                    try:
                        validated = server_instance._validate_path(doc_path)
                        if validated.exists():
                            source_paths.append(validated)
                    except ValueError:
                        pass

            video_project = registry.create(
                name=name,
                language=language,
                source_documents=source_paths,
            )

            result = {
                "success": True,
                "project_id": video_project.id,
                "name": video_project.name,
                "language": video_project.language,
                "status": video_project.status.value,
                "source_documents": [str(p) for p in video_project.source_documents],
                "created_at": video_project.created_at.isoformat(),
            }

            if generate_script and source_paths:
                result["note"] = "Script generation requested - use generate_video_script tool"

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def get_video_project(project_id: str) -> str:
        """
        Get details of a video project.

        Args:
            project_id: Video project ID

        Returns:
            JSON with full project details including components and status
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.project import VideoProjectRegistry

            registry = VideoProjectRegistry(server_instance.project)
            video_project = registry.get(project_id)

            if not video_project:
                return json.dumps({"error": f"Project '{project_id}' not found"}, indent=2)

            return json.dumps({
                "id": video_project.id,
                "name": video_project.name,
                "language": video_project.language,
                "status": video_project.status.value,
                "progress": video_project.progress,
                "is_complete": video_project.is_complete,
                "components": {
                    k: {
                        "type": v.type.value,
                        "status": v.status.value,
                        "path": str(v.path),
                        "scene_id": v.scene_id,
                    }
                    for k, v in video_project.components.items()
                },
                "source_documents": [str(p) for p in video_project.source_documents],
                "created_at": video_project.created_at.isoformat(),
                "modified_at": video_project.modified_at.isoformat(),
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def list_video_projects(status: str = None) -> str:
        """
        List all video projects.

        Args:
            status: Optional filter by status (draft, in_review, approved, rendering, published)

        Returns:
            JSON with list of projects and their summary info
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.project import VideoProjectRegistry, ProjectStatus

            registry = VideoProjectRegistry(server_instance.project)

            status_filter = None
            if status:
                try:
                    status_filter = ProjectStatus(status)
                except ValueError:
                    return json.dumps({"error": f"Invalid status: {status}"}, indent=2)

            projects = registry.list(status=status_filter)

            return json.dumps({
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "status": p.status.value,
                        "progress": p.progress,
                        "components_count": len(p.components),
                        "modified_at": p.modified_at.isoformat(),
                    }
                    for p in projects
                ],
                "count": len(projects),
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def add_video_component(
        project_id: str,
        name: str,
        component_type: str,
        path: str,
        scene_id: str = None,
    ) -> str:
        """
        Add a component to a video project.

        Args:
            project_id: Video project ID
            name: Human-readable component name
            component_type: Type (script, demo_definition, demo_clip, voiceover, captions, props, render)
            path: Path to the component file
            scene_id: Optional scene ID for per-scene components

        Returns:
            JSON with created component details
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.project import VideoProjectRegistry, ComponentType

            registry = VideoProjectRegistry(server_instance.project)
            video_project = registry.get(project_id)

            if not video_project:
                return json.dumps({"error": f"Project '{project_id}' not found"}, indent=2)

            try:
                comp_type = ComponentType(component_type)
            except ValueError:
                return json.dumps({
                    "error": f"Invalid component type: {component_type}",
                    "valid_types": [t.value for t in ComponentType],
                }, indent=2)

            validated_path = server_instance._validate_path(path)

            component = video_project.add_component(
                name=name,
                comp_type=comp_type,
                path=validated_path,
                scene_id=scene_id,
            )

            registry.update(video_project)

            return json.dumps({
                "success": True,
                "component_id": component.id,
                "type": component.type.value,
                "status": component.status.value,
                "path": str(component.path),
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def regenerate_video_component(
        project_id: str,
        component_id: str,
        cascade: bool = True,
    ) -> str:
        """
        Trigger regeneration of a video component.

        When cascade=True (default), also regenerates all downstream
        components that depend on this one.

        Args:
            project_id: Video project ID
            component_id: Component ID to regenerate
            cascade: Whether to also regenerate dependent components

        Returns:
            JSON with regeneration results
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.project import VideoProjectRegistry
            from ...video.cascade import CascadeRegenerator

            registry = VideoProjectRegistry(server_instance.project)
            video_project = registry.get(project_id)

            if not video_project:
                return json.dumps({"error": f"Project '{project_id}' not found"}, indent=2)

            if component_id not in video_project.components:
                return json.dumps({"error": f"Component '{component_id}' not found"}, indent=2)

            regenerator = CascadeRegenerator(server_instance.project, video_project)
            result = await regenerator.on_component_changed(component_id, cascade=cascade)

            return json.dumps({
                "success": result.success,
                "affected_components": result.affected_components,
                "regenerated": result.regenerated,
                "failed": result.failed,
                "skipped": result.skipped,
                "duration": result.duration,
                "error": result.error,
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def add_video_review_comment(
        project_id: str,
        component_id: str,
        text: str,
        timestamp: float = None,
        priority: str = "normal",
    ) -> str:
        """
        Add a review comment to a video component.

        Comments can be timestamped to reference specific points in video.
        They can be queued for AI processing later.

        Args:
            project_id: Video project ID
            component_id: Component ID to comment on
            text: Comment text describing the issue or suggestion
            timestamp: Optional timestamp in seconds for video components
            priority: Priority level (low, normal, high, urgent)

        Returns:
            JSON with created comment details
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.project import VideoProjectRegistry
            from ...video.review import VideoReviewStore, CommentPriority

            # Verify project and component exist
            registry = VideoProjectRegistry(server_instance.project)
            video_project = registry.get(project_id)

            if not video_project:
                return json.dumps({"error": f"Project '{project_id}' not found"}, indent=2)

            if component_id not in video_project.components:
                return json.dumps({"error": f"Component '{component_id}' not found"}, indent=2)

            try:
                prio = CommentPriority(priority)
            except ValueError:
                prio = CommentPriority.NORMAL

            store = VideoReviewStore(server_instance.project)
            comment = store.add_comment(
                project_id=project_id,
                component_id=component_id,
                text=text,
                author="ai",
                timestamp=timestamp,
                priority=prio,
            )

            return json.dumps({
                "success": True,
                "comment_id": comment.id,
                "status": comment.status.value,
                "timestamp": comment.format_timestamp() if comment.timestamp else None,
                "created_at": comment.created_at.isoformat(),
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def resolve_video_comment(
        comment_id: str,
        resolution: str,
        changes_made: list[str] = None,
    ) -> str:
        """
        Resolve a video review comment after processing.

        Use this after making changes to address a comment.
        This marks the comment as resolved and removes it from pending.

        Args:
            comment_id: Comment ID to resolve
            resolution: Description of what was done to resolve the comment
            changes_made: Optional list of files/components that were modified

        Returns:
            JSON with resolution details
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.review import VideoReviewStore

            store = VideoReviewStore(server_instance.project)
            comment = store.get_comment(comment_id)

            if not comment:
                return json.dumps({"error": f"Comment '{comment_id}' not found"}, indent=2)

            # Build full resolution message
            full_resolution = resolution
            if changes_made:
                full_resolution += f"\n\nChanges made:\n" + "\n".join(f"- {c}" for c in changes_made)

            resolved = store.resolve_comment(
                comment_id=comment_id,
                resolution=full_resolution,
                resolved_by="ai",
            )

            if not resolved:
                return json.dumps({"error": "Failed to resolve comment"}, indent=2)

            return json.dumps({
                "success": True,
                "comment_id": comment_id,
                "status": resolved.status.value,
                "resolution": resolution,
                "resolved_at": resolved.resolved_at.isoformat() if resolved.resolved_at else None,
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def get_pending_video_comments(project_id: str = None) -> str:
        """
        Get all pending review comments that need processing.

        These are comments that haven't been resolved or rejected yet.
        Use this to find work items that need attention.

        Args:
            project_id: Optional filter to specific project

        Returns:
            JSON with list of pending comments
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.review import VideoReviewStore

            store = VideoReviewStore(server_instance.project)
            comments = store.get_pending_comments(project_id=project_id)

            return json.dumps({
                "comments": [
                    {
                        "id": c.id,
                        "project_id": c.project_id,
                        "component_id": c.component_id,
                        "text": c.text,
                        "author": c.author,
                        "timestamp": c.format_timestamp() if c.timestamp else None,
                        "priority": c.priority.value,
                        "status": c.status.value,
                        "created_at": c.created_at.isoformat(),
                    }
                    for c in comments
                ],
                "count": len(comments),
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def update_video_project_status(
        project_id: str,
        status: str,
    ) -> str:
        """
        Update a video project's status.

        Use this to move projects through the workflow:
        draft → in_review → approved → rendering → published

        Args:
            project_id: Video project ID
            status: New status (draft, in_review, approved, rendering, published)

        Returns:
            JSON with updated status
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.project import VideoProjectRegistry, ProjectStatus

            registry = VideoProjectRegistry(server_instance.project)
            video_project = registry.get(project_id)

            if not video_project:
                return json.dumps({"error": f"Project '{project_id}' not found"}, indent=2)

            try:
                new_status = ProjectStatus(status)
            except ValueError:
                return json.dumps({
                    "error": f"Invalid status: {status}",
                    "valid_statuses": [s.value for s in ProjectStatus],
                }, indent=2)

            old_status = video_project.status.value
            video_project.status = new_status
            registry.update(video_project)

            return json.dumps({
                "success": True,
                "project_id": project_id,
                "old_status": old_status,
                "new_status": new_status.value,
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)

    @mcp.tool()
    async def get_video_project_stale_components(project_id: str) -> str:
        """
        Get all stale components that need regeneration.

        Stale components are those whose upstream dependencies have
        changed and need to be regenerated.

        Args:
            project_id: Video project ID

        Returns:
            JSON with list of stale components
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            from ...video.project import VideoProjectRegistry

            registry = VideoProjectRegistry(server_instance.project)
            video_project = registry.get(project_id)

            if not video_project:
                return json.dumps({"error": f"Project '{project_id}' not found"}, indent=2)

            stale = video_project.get_stale_components()

            return json.dumps({
                "project_id": project_id,
                "stale_components": [
                    {
                        "id": c.id,
                        "type": c.type.value,
                        "path": str(c.path),
                        "scene_id": c.scene_id,
                        "depends_on": c.depends_on,
                    }
                    for c in stale
                ],
                "count": len(stale),
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
