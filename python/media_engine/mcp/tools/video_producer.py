"""Video Producer MCP tools.

Core video production tools for AI-assisted video creation:
- Script planning and generation
- Scene visual suggestions
- Timing optimization
- Script validation
"""

import json


def register_video_producer_tools(mcp, server_instance):
    """Register video producer MCP tools."""

    @mcp.tool()
    async def plan_video_from_content(
        content_path: str,
        video_type: str = "explainer",
        target_duration: int = 60,
        language: str = None,
    ) -> str:
        """
        Analyze content and propose a video structure.

        Args:
            content_path: Path to markdown content to base video on
            video_type: Type of video (explainer, demo, promotional, tutorial)
            target_duration: Target duration in seconds
            language: Language for the video (default: source language)

        Returns:
            JSON with proposed video structure including scenes, timing, and suggestions
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(content_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Content file not found: {content_path}"}, indent=2)

        lang = language or server_instance.project.source_language

        # Read content
        content = validated_path.read_text()

        # Extract key points from content
        lines = content.split("\n")
        title = ""
        headings = []
        bullet_points = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# ") and not title:
                title = stripped[2:]
            elif stripped.startswith("## "):
                headings.append(stripped[3:])
            elif stripped.startswith("- ") or stripped.startswith("* "):
                bullet_points.append(stripped[2:])

        # Calculate timing based on content
        num_sections = max(len(headings), 1)
        intro_duration = min(5, target_duration * 0.1)
        outro_duration = min(5, target_duration * 0.1)
        content_duration = target_duration - intro_duration - outro_duration
        section_duration = content_duration / num_sections

        # Build proposed structure
        scenes = []

        # Intro scene
        scenes.append({
            "id": "intro",
            "type": "intro",
            "duration": round(intro_duration),
            "title": title or "Introduction",
            "background": "aurora",
            "transition_in": "glitch",
            "text_effect": "bounce",
            "suggestions": {
                "voiceover": f"Welcome to {title}" if title else "Welcome",
                "visual_focus": "Brand identity, attention-grabbing animation",
            }
        })

        # Content scenes based on headings
        for i, heading in enumerate(headings[:6]):  # Max 6 content scenes
            scene_type = "feature" if i < 3 else "demo"
            relevant_bullets = bullet_points[i*2:(i+1)*2] if bullet_points else []

            scenes.append({
                "id": f"section_{i+1}",
                "type": scene_type,
                "duration": round(section_duration),
                "title": heading,
                "background": "grid" if scene_type == "feature" else "dark",
                "transition_in": "slide-left" if i % 2 == 0 else "fade",
                "bullets": relevant_bullets,
                "suggestions": {
                    "voiceover_focus": heading,
                    "visual_elements": "Icons, diagrams, or demo footage",
                }
            })

        # Outro scene
        scenes.append({
            "id": "outro",
            "type": "outro",
            "duration": round(outro_duration),
            "title": "Get Started",
            "background": "aurora",
            "transition_in": "aurora-sweep",
            "cta": "Learn more",
            "suggestions": {
                "voiceover": "Thank you for watching. Get started today!",
                "visual_focus": "Clear call-to-action, brand reinforcement",
            }
        })

        return json.dumps({
            "status": "planned",
            "source_content": str(validated_path),
            "video_type": video_type,
            "language": lang,
            "target_duration": target_duration,
            "estimated_duration": sum(s["duration"] for s in scenes),
            "scene_count": len(scenes),
            "proposed_structure": {
                "title": title,
                "scenes": scenes,
            },
            "next_steps": [
                "Review and adjust scene durations",
                "Add voiceover text to each scene",
                "Select appropriate demo clips if needed",
                "Generate the video script with generate_video_script",
            ]
        }, indent=2)

    @mcp.tool()
    async def generate_video_script(
        title: str,
        scenes: str,
        language: str = None,
        output_path: str = None,
    ) -> str:
        """
        Create a YAML video script from a scene outline.

        Args:
            title: Video title
            scenes: JSON string of scenes array with id, type, duration, title, voiceover
            language: Language for the script (default: source language)
            output_path: Where to save the script (optional)

        Returns:
            JSON with script content and save location
        """
        import yaml

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        lang = language or server_instance.project.source_language

        try:
            scenes_data = json.loads(scenes)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid scenes JSON: {e}"}, indent=2)

        # Build script structure
        script = {
            "title": title,
            "language": lang,
            "metadata": {
                "version": "1.0.0",
                "status": "draft",
                "author": "AI Video Producer",
            },
            "settings": {
                "fps": 30,
                "width": 1920,
                "height": 1080,
            },
            "scenes": []
        }

        # Process scenes
        for scene in scenes_data:
            scene_entry = {
                "id": scene.get("id", f"scene_{len(script['scenes'])+1}"),
                "type": scene.get("type", "feature"),
                "duration": scene.get("duration", 5),
            }

            # Add optional fields
            if "title" in scene:
                scene_entry["title"] = scene["title"]
            if "voiceover" in scene:
                scene_entry["voiceover"] = scene["voiceover"]
            if "background" in scene:
                scene_entry["background"] = scene["background"]
            if "transition_in" in scene:
                scene_entry["transition_in"] = scene["transition_in"]
            if "text_effect" in scene:
                scene_entry["text_effect"] = scene["text_effect"]
            if "bullets" in scene:
                scene_entry["bullets"] = scene["bullets"]
            if "demo_clip" in scene:
                scene_entry["demo_clip"] = scene["demo_clip"]

            script["scenes"].append(scene_entry)

        # Generate YAML content
        yaml_content = yaml.dump(script, default_flow_style=False, allow_unicode=True, sort_keys=False)

        # Save if path provided
        saved_path = None
        if output_path:
            try:
                save_path = server_instance._validate_path(output_path)
            except ValueError:
                save_path = server_instance.project.content_dir / lang / "scripts" / output_path

            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(yaml_content)
            saved_path = str(save_path)

        return json.dumps({
            "status": "generated",
            "title": title,
            "language": lang,
            "scene_count": len(script["scenes"]),
            "total_duration": sum(s["duration"] for s in script["scenes"]),
            "saved_to": saved_path,
            "content": yaml_content,
        }, indent=2)

    @mcp.tool()
    async def suggest_scene_visuals(
        scene_type: str,
        title: str = None,
        content: str = None,
        brand_personality: str = "professional",
    ) -> str:
        """
        Get AI-powered visual recommendations for a scene.

        Args:
            scene_type: Type of scene (intro, feature, demo, split, outro)
            title: Scene title or topic
            content: Additional content context
            brand_personality: Brand style (professional, playful, technical, minimal)

        Returns:
            JSON with visual recommendations
        """
        from ..tools.video_design_knowledge import (
            MOTION_DESIGN_PRINCIPLES,
            SCENE_TYPE_RECOMMENDATIONS,
        )

        recommendations = SCENE_TYPE_RECOMMENDATIONS.get(scene_type, SCENE_TYPE_RECOMMENDATIONS["feature"])

        # Adjust based on brand personality
        personality_adjustments = {
            "professional": {
                "backgrounds": ["dark", "grid", "pulse"],
                "text_effects": ["fade-up", "scale-pop"],
                "transitions": ["fade", "slide-left", "wipe"],
            },
            "playful": {
                "backgrounds": ["aurora", "particles", "waves"],
                "text_effects": ["bounce", "elastic", "wave"],
                "transitions": ["glitch", "zoom-burst", "liquid"],
            },
            "technical": {
                "backgrounds": ["cyber", "grid", "dark"],
                "text_effects": ["glitch", "split"],
                "transitions": ["pixel-dissolve", "grid-reveal", "slice"],
            },
            "minimal": {
                "backgrounds": ["dark"],
                "text_effects": ["fade-up"],
                "transitions": ["fade", "wipe"],
            },
        }

        adjustments = personality_adjustments.get(brand_personality, personality_adjustments["professional"])

        return json.dumps({
            "scene_type": scene_type,
            "title": title,
            "brand_personality": brand_personality,
            "recommendations": {
                "duration": recommendations["duration"],
                "backgrounds": adjustments["backgrounds"],
                "suggested_background": adjustments["backgrounds"][0],
                "transitions": adjustments["transitions"],
                "suggested_transition": recommendations.get("transition_in", adjustments["transitions"])[0] if isinstance(recommendations.get("transition_in"), list) else recommendations.get("transition_in", adjustments["transitions"][0]),
                "text_effects": adjustments["text_effects"],
                "suggested_text_effect": adjustments["text_effects"][0],
                "guidelines": recommendations["guidelines"],
            },
            "design_principles": {
                "timing": MOTION_DESIGN_PRINCIPLES["timing"]["ease_in_out"],
                "composition": MOTION_DESIGN_PRINCIPLES["composition"]["focal_point"],
                "pacing": MOTION_DESIGN_PRINCIPLES["pacing"]["hook"] if scene_type == "intro" else MOTION_DESIGN_PRINCIPLES["pacing"]["breathing"],
            }
        }, indent=2)

    @mcp.tool()
    async def optimize_timing(script_path: str, target_duration: int = None) -> str:
        """
        Optimize scene timing for better pacing.

        Args:
            script_path: Path to video script YAML
            target_duration: Target total duration in seconds (optional)

        Returns:
            JSON with timing optimization suggestions
        """
        import yaml

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(script_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Script not found: {script_path}"}, indent=2)

        with open(validated_path) as f:
            script = yaml.safe_load(f)

        scenes = script.get("scenes", [])
        if not scenes:
            return json.dumps({"error": "No scenes in script"}, indent=2)

        current_duration = sum(s.get("duration", 5) for s in scenes)
        target = target_duration or current_duration

        # Analyze timing issues
        issues = []
        optimized_scenes = []

        for i, scene in enumerate(scenes):
            duration = scene.get("duration", 5)
            scene_type = scene.get("type", "feature")
            voiceover = scene.get("voiceover", "")

            # Estimate voiceover time (roughly 150 words per minute)
            if voiceover:
                word_count = len(voiceover.split())
                vo_duration = (word_count / 150) * 60
                if vo_duration > duration:
                    issues.append({
                        "scene": scene.get("id", f"scene_{i+1}"),
                        "issue": "voiceover_too_long",
                        "voiceover_duration": round(vo_duration, 1),
                        "scene_duration": duration,
                    })

            # Check scene type durations
            if scene_type == "intro" and duration > 7:
                issues.append({
                    "scene": scene.get("id", f"scene_{i+1}"),
                    "issue": "intro_too_long",
                    "suggestion": "Intro should be 3-7 seconds to maintain attention",
                })
            elif scene_type == "outro" and duration > 10:
                issues.append({
                    "scene": scene.get("id", f"scene_{i+1}"),
                    "issue": "outro_too_long",
                    "suggestion": "Outro should be 5-10 seconds",
                })

            optimized_scenes.append({
                **scene,
                "duration": duration,
            })

        # Calculate scale factor if target differs
        if target != current_duration:
            scale = target / current_duration
            for scene in optimized_scenes:
                scene["duration"] = round(scene["duration"] * scale)

        optimized_duration = sum(s["duration"] for s in optimized_scenes)

        return json.dumps({
            "status": "analyzed",
            "script_path": str(validated_path),
            "current_duration": current_duration,
            "target_duration": target,
            "optimized_duration": optimized_duration,
            "scene_count": len(scenes),
            "issues": issues,
            "optimized_scenes": optimized_scenes,
            "pacing_tips": [
                "First 3 seconds are critical for retention",
                "Add breathing room after dense information",
                "Build intensity toward the climax",
                "Cool down before the end",
            ]
        }, indent=2)

    @mcp.tool()
    async def validate_video_script(script_path: str) -> str:
        """
        Check a video script for errors and best practices.

        Args:
            script_path: Path to video script YAML

        Returns:
            JSON with validation results and improvement suggestions
        """
        import yaml

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        try:
            validated_path = server_instance._validate_path(script_path)
        except ValueError as e:
            return json.dumps({"error": str(e)}, indent=2)

        if not validated_path.exists():
            return json.dumps({"error": f"Script not found: {script_path}"}, indent=2)

        errors = []
        warnings = []
        info = []

        try:
            with open(validated_path) as f:
                script = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return json.dumps({
                "status": "invalid",
                "errors": [{"type": "yaml_error", "message": str(e)}],
            }, indent=2)

        # Check required fields
        if not script.get("title"):
            errors.append({"type": "missing_field", "field": "title", "message": "Script must have a title"})

        if not script.get("scenes"):
            errors.append({"type": "missing_field", "field": "scenes", "message": "Script must have scenes"})
        else:
            scenes = script["scenes"]
            scene_ids = set()
            total_duration = 0
            has_intro = False
            has_outro = False

            for i, scene in enumerate(scenes):
                scene_id = scene.get("id", f"scene_{i+1}")

                # Check for duplicate IDs
                if scene_id in scene_ids:
                    errors.append({"type": "duplicate_id", "scene": scene_id})
                scene_ids.add(scene_id)

                # Check for required scene fields
                if "duration" not in scene:
                    warnings.append({"type": "missing_duration", "scene": scene_id, "default": 5})

                duration = scene.get("duration", 5)
                total_duration += duration

                # Check scene types
                scene_type = scene.get("type", "feature")
                if scene_type == "intro":
                    has_intro = True
                elif scene_type == "outro":
                    has_outro = True

                # Check voiceover
                if not scene.get("voiceover") and scene_type not in ["demo"]:
                    warnings.append({
                        "type": "missing_voiceover",
                        "scene": scene_id,
                        "message": "Scene has no voiceover text"
                    })

            # Structure warnings
            if not has_intro:
                warnings.append({"type": "no_intro", "message": "Video has no intro scene"})
            if not has_outro:
                warnings.append({"type": "no_outro", "message": "Video has no outro scene"})

            # Duration info
            if total_duration < 15:
                info.append({"type": "short_video", "duration": total_duration, "message": "Very short video"})
            elif total_duration > 180:
                warnings.append({"type": "long_video", "duration": total_duration, "message": "Video may be too long for engagement"})

        is_valid = len(errors) == 0

        return json.dumps({
            "status": "valid" if is_valid else "invalid",
            "script_path": str(validated_path),
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "summary": {
                "error_count": len(errors),
                "warning_count": len(warnings),
                "is_valid": is_valid,
            }
        }, indent=2)

    @mcp.tool()
    async def get_camera_presets() -> str:
        """
        List all available camera animation presets.

        Returns:
            JSON with camera presets and their configurations
        """
        from ...video.camera_presets import CAMERA_PRESETS

        presets = {}
        for preset_id, preset in CAMERA_PRESETS.items():
            presets[preset_id] = {
                "name": preset.name,
                "description": preset.description,
                "pattern": preset.pattern,
                "default_zoom": preset.default_zoom,
                "default_duration": preset.default_duration,
                "default_hold": preset.default_hold,
                "default_easing": preset.default_easing,
            }

        return json.dumps({
            "presets": presets,
            "count": len(presets),
            "patterns": ["sequential", "zoom_out", "focus_main", "flow", "overview"],
            "usage_example": {
                "yaml": """visual:
  camera:
    mode: animated
    preset: "guided_tour"  # Use preset name here
    capture_scale: 2.0
    # Or define manual focus sequence:
    focus_sequence:
      - target: "fullpage"
        zoom: 1.0
        duration: 0.5
      - target: "#sidebar"
        zoom: 2.5
        duration: 1.2
        hold: 2.0
        easing: "easeInOutCubic"
""",
            },
        }, indent=2)

    @mcp.tool()
    async def get_effect_presets() -> str:
        """
        List all available visual effects presets.

        Returns:
            JSON with effects presets and their configurations
        """
        from ...video.camera_effects import EFFECT_PRESETS

        presets = {}
        for name, config in EFFECT_PRESETS.items():
            enabled_effects = []
            if config.vignette.enabled:
                enabled_effects.append("vignette")
            if config.perspective_tilt.enabled:
                enabled_effects.append("perspective_tilt")
            if config.camera_shake.enabled:
                enabled_effects.append("camera_shake")
            if config.depth_of_field.enabled:
                enabled_effects.append("depth_of_field")
            if config.parallax.enabled:
                enabled_effects.append("parallax")
            if config.motion_blur.enabled:
                enabled_effects.append("motion_blur")

            presets[name] = {
                "enabled_effects": enabled_effects,
                "effect_count": len(enabled_effects),
            }

        return json.dumps({
            "presets": presets,
            "count": len(presets),
            "all_effect_types": [
                "vignette",
                "perspective_tilt",
                "camera_shake",
                "depth_of_field",
                "parallax",
                "motion_blur",
            ],
            "usage_example": {
                "yaml": """visual:
  camera:
    mode: animated
    effects_preset: "cinematic"  # Use preset name here
    effects:  # Optional: override specific settings
      vignette:
        intensity: 0.6
""",
            },
        }, indent=2)

    @mcp.tool()
    async def list_video_scripts(language: str = None) -> str:
        """
        List all video scripts in the project.

        Args:
            language: Filter by language (optional)

        Returns:
            JSON with list of video scripts
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        import yaml

        scripts = []
        languages = [language] if language else list(server_instance.project.languages.keys())

        for lang in languages:
            scripts_dir = server_instance.project.content_dir / lang / "scripts"
            if not scripts_dir.exists():
                continue

            for script_path in scripts_dir.glob("*.yaml"):
                try:
                    with open(script_path) as f:
                        data = yaml.safe_load(f)

                    total_duration = sum(s.get("duration", 5) for s in data.get("scenes", []))

                    scripts.append({
                        "id": f"{lang}/{script_path.stem}",
                        "name": data.get("title", script_path.stem),
                        "language": lang,
                        "path": str(script_path.relative_to(server_instance.project.root)),
                        "scenes": len(data.get("scenes", [])),
                        "duration": total_duration,
                        "status": data.get("metadata", {}).get("status", "draft"),
                    })
                except Exception as e:
                    scripts.append({
                        "id": f"{lang}/{script_path.stem}",
                        "path": str(script_path.relative_to(server_instance.project.root)),
                        "error": str(e),
                    })

        return json.dumps({
            "scripts": scripts,
            "count": len(scripts),
        }, indent=2)

    @mcp.tool()
    async def get_video_script(script_id: str) -> str:
        """
        Get a single video script with full parsed details.

        Args:
            script_id: Script identifier (e.g., "en/intro")

        Returns:
            JSON with full script details including scenes, settings, and metadata
        """
        import yaml

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        # Parse script_id
        parts = script_id.split("/", 1)
        if len(parts) != 2:
            return json.dumps({"error": "Invalid script_id format. Use 'language/script_name'"}, indent=2)

        lang, name = parts
        script_path = server_instance.project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            return json.dumps({"error": f"Script not found: {script_id}"}, indent=2)

        try:
            with open(script_path) as f:
                script = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return json.dumps({"error": f"YAML parse error: {e}"}, indent=2)

        # Calculate totals
        scenes = script.get("scenes", [])
        total_duration = sum(s.get("duration", 5) for s in scenes)
        scenes_with_vo = sum(1 for s in scenes if s.get("voiceover"))

        # Check for associated files
        props_path = script_path.with_suffix(".props.json")
        has_props = props_path.exists()

        audio_path = server_instance.project.output_dir / lang / "videos" / f"{name}.mp3"
        has_audio = audio_path.exists()

        video_path = server_instance.project.output_dir / lang / "videos" / f"{name}.mp4"
        has_video = video_path.exists()

        return json.dumps({
            "id": script_id,
            "name": script.get("title", name),
            "language": lang,
            "path": str(script_path.relative_to(server_instance.project.root)),
            "metadata": script.get("metadata", {}),
            "settings": script.get("settings", {}),
            "scenes": scenes,
            "statistics": {
                "scene_count": len(scenes),
                "total_duration": total_duration,
                "scenes_with_voiceover": scenes_with_vo,
                "has_props": has_props,
                "has_audio": has_audio,
                "has_video": has_video,
            },
            "associated_files": {
                "props": str(props_path) if has_props else None,
                "audio": str(audio_path) if has_audio else None,
                "video": str(video_path) if has_video else None,
            },
        }, indent=2)

    @mcp.tool()
    async def get_video_props(script_id: str) -> str:
        """
        Get the props.json configuration for a video script.

        Props contain the computed layout, timing, and visual data needed for rendering.

        Args:
            script_id: Script identifier (e.g., "en/intro")

        Returns:
            JSON with props data or instructions to generate if missing
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        # Parse script_id
        parts = script_id.split("/", 1)
        if len(parts) != 2:
            return json.dumps({"error": "Invalid script_id format. Use 'language/script_name'"}, indent=2)

        lang, name = parts

        # Check multiple possible locations for props
        script_path = server_instance.project.content_dir / lang / "scripts" / f"{name}.yaml"
        props_path = script_path.with_suffix(".props.json")

        # Also check in remotion public folder
        remotion_props = server_instance.project.root / "remotion" / "public" / "props.json"

        if props_path.exists():
            try:
                props = json.loads(props_path.read_text())
                return json.dumps({
                    "script_id": script_id,
                    "source": str(props_path.relative_to(server_instance.project.root)),
                    "props": props,
                }, indent=2)
            except json.JSONDecodeError as e:
                return json.dumps({"error": f"Invalid props JSON: {e}"}, indent=2)

        if remotion_props.exists():
            try:
                props = json.loads(remotion_props.read_text())
                return json.dumps({
                    "script_id": script_id,
                    "source": "remotion/public/props.json",
                    "note": "Using global props file",
                    "props": props,
                }, indent=2)
            except json.JSONDecodeError as e:
                return json.dumps({"error": f"Invalid props JSON: {e}"}, indent=2)

        return json.dumps({
            "error": "Props not found",
            "script_id": script_id,
            "searched_paths": [
                str(props_path.relative_to(server_instance.project.root)),
                "remotion/public/props.json",
            ],
            "hint": "Run 'media-engine video build-props' to generate props from the script",
        }, indent=2)

    @mcp.tool()
    async def get_video_assets(asset_type: str = None) -> str:
        """
        List all video assets in the project.

        Args:
            asset_type: Filter by type (demo_clips, voiceover, captions, output, all)

        Returns:
            JSON with list of assets grouped by type
        """
        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        assets = {
            "demo_clips": [],
            "voiceover": [],
            "captions": [],
            "output": [],
        }

        # Check demo/demos folder
        demos_dir = server_instance.project.root / "demo" / "demos"
        if demos_dir.exists():
            for f in demos_dir.glob("**/*.mp4"):
                assets["demo_clips"].append({
                    "name": f.stem,
                    "path": str(f.relative_to(server_instance.project.root)),
                    "size": f.stat().st_size,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                })

        # Also check remotion/public/demos
        remotion_demos = server_instance.project.root / "remotion" / "public" / "demos"
        if remotion_demos.exists():
            for f in remotion_demos.glob("**/*.mp4"):
                assets["demo_clips"].append({
                    "name": f.stem,
                    "path": str(f.relative_to(server_instance.project.root)),
                    "size": f.stat().st_size,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                })

        # Check for voiceover audio
        for lang_dir in server_instance.project.output_dir.glob("*"):
            if not lang_dir.is_dir():
                continue
            audio_dir = lang_dir / "audio"
            if audio_dir.exists():
                for f in audio_dir.glob("*.mp3"):
                    assets["voiceover"].append({
                        "name": f.stem,
                        "language": lang_dir.name,
                        "path": str(f.relative_to(server_instance.project.root)),
                        "size": f.stat().st_size,
                    })

        # Check for captions
        for lang_dir in server_instance.project.output_dir.glob("*"):
            if not lang_dir.is_dir():
                continue
            captions_dir = lang_dir / "captions"
            if captions_dir.exists():
                for f in captions_dir.glob("*.srt"):
                    assets["captions"].append({
                        "name": f.stem,
                        "language": lang_dir.name,
                        "path": str(f.relative_to(server_instance.project.root)),
                    })
                for f in captions_dir.glob("*.vtt"):
                    assets["captions"].append({
                        "name": f.stem,
                        "language": lang_dir.name,
                        "path": str(f.relative_to(server_instance.project.root)),
                    })

        # Check for rendered output
        for lang_dir in server_instance.project.output_dir.glob("*"):
            if not lang_dir.is_dir():
                continue
            videos_dir = lang_dir / "videos"
            if videos_dir.exists():
                for f in videos_dir.glob("*.mp4"):
                    assets["output"].append({
                        "name": f.stem,
                        "language": lang_dir.name,
                        "path": str(f.relative_to(server_instance.project.root)),
                        "size": f.stat().st_size,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    })

        # Filter by type if specified
        if asset_type and asset_type != "all":
            if asset_type not in assets:
                return json.dumps({
                    "error": f"Unknown asset type: {asset_type}",
                    "valid_types": list(assets.keys()) + ["all"],
                }, indent=2)
            filtered = {asset_type: assets[asset_type]}
            total_count = len(assets[asset_type])
        else:
            filtered = assets
            total_count = sum(len(v) for v in assets.values())

        return json.dumps({
            "assets": filtered,
            "total_count": total_count,
            "counts_by_type": {k: len(v) for k, v in assets.items()},
        }, indent=2)

    @mcp.tool()
    async def generate_voiceover(
        script_id: str,
        voice: str = "onyx",
        force: bool = False,
    ) -> str:
        """
        Generate voiceover audio from a video script.

        Args:
            script_id: Script identifier (e.g., "en/intro")
            voice: Voice to use (onyx, alloy, echo, fable, nova, shimmer)
            force: Regenerate even if audio exists

        Returns:
            JSON with generation status and output path
        """
        import yaml

        if not server_instance.project:
            return json.dumps({"error": "No project found"}, indent=2)

        # Parse script_id
        parts = script_id.split("/", 1)
        if len(parts) != 2:
            return json.dumps({"error": "Invalid script_id format. Use 'language/script_name'"}, indent=2)

        lang, name = parts
        script_path = server_instance.project.content_dir / lang / "scripts" / f"{name}.yaml"

        if not script_path.exists():
            return json.dumps({"error": f"Script not found: {script_id}"}, indent=2)

        # Check if output already exists
        output_dir = server_instance.project.output_dir / lang / "audio"
        output_path = output_dir / f"{name}.mp3"

        if output_path.exists() and not force:
            return json.dumps({
                "status": "exists",
                "script_id": script_id,
                "output_path": str(output_path.relative_to(server_instance.project.root)),
                "message": "Audio already exists. Use force=true to regenerate.",
            }, indent=2)

        # Load script and extract voiceover text
        try:
            with open(script_path) as f:
                script = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return json.dumps({"error": f"YAML parse error: {e}"}, indent=2)

        scenes = script.get("scenes", [])
        voiceover_texts = []

        for scene in scenes:
            vo = scene.get("voiceover")
            if vo:
                voiceover_texts.append({
                    "scene_id": scene.get("id", "unknown"),
                    "text": vo,
                    "duration": scene.get("duration", 5),
                })

        if not voiceover_texts:
            return json.dumps({
                "status": "no_voiceover",
                "script_id": script_id,
                "message": "Script has no voiceover text in any scene",
            }, indent=2)

        # Calculate total word count and estimated duration
        total_words = sum(len(t["text"].split()) for t in voiceover_texts)
        estimated_duration = (total_words / 150) * 60  # ~150 words per minute

        # Note: Actual TTS generation would require API integration
        # This returns the plan for what would be generated
        return json.dumps({
            "status": "ready",
            "script_id": script_id,
            "voice": voice,
            "available_voices": ["onyx", "alloy", "echo", "fable", "nova", "shimmer"],
            "output_path": str(output_dir / f"{name}.mp3"),
            "scenes_with_voiceover": len(voiceover_texts),
            "total_words": total_words,
            "estimated_duration_seconds": round(estimated_duration),
            "voiceover_segments": voiceover_texts,
            "note": "Use 'media-engine video voiceover' CLI command to generate the actual audio",
        }, indent=2)
