"""Motion Design MCP tools.

Motion graphics and design tools for AI-assisted video creation:
- Component catalog browsing
- Transition recommendations
- Brand application
- Title sequence design
- Scene composition
"""

import json


def register_motion_design_tools(mcp, server_instance):
    """Register motion design MCP tools."""

    @mcp.tool()
    async def list_motion_components(category: str = None) -> str:
        """
        List available Remotion motion graphics components.

        Args:
            category: Filter by category (title, text, layout, data, background, transition)

        Returns:
            JSON with component catalog including props and usage guidelines
        """
        from .video_design_knowledge import (
            BACKGROUND_CATALOG,
            TEXT_EFFECT_CATALOG,
            TRANSITION_CATALOG,
        )

        # Component definitions
        components = [
            {
                "id": "TitleCard",
                "name": "Title Card",
                "category": "title",
                "description": "Animated title sequence with gradient text and glow effects",
                "props": ["title", "tagline", "variant", "delay"],
                "variants": ["gradient", "glow", "minimal", "bold"],
                "usage": "Use for video intros and section headers",
            },
            {
                "id": "TextReveal",
                "name": "Text Reveal",
                "category": "text",
                "description": "Kinetic typography with multiple animation styles",
                "props": ["text", "effect", "delay", "size", "color"],
                "effects": list(TEXT_EFFECT_CATALOG.keys()),
                "usage": "Use for voiceover sync, key messages, and callouts",
            },
            {
                "id": "FeatureCard",
                "name": "Feature Card",
                "category": "layout",
                "description": "Animated feature showcase with icon and bullets",
                "props": ["title", "icon", "bullets", "highlight", "layout"],
                "layouts": ["left", "right", "center", "split"],
                "usage": "Use for feature highlights and benefit lists",
            },
            {
                "id": "StatCounter",
                "name": "Stat Counter",
                "category": "data",
                "description": "Animated number counter with label",
                "props": ["value", "label", "prefix", "suffix", "duration"],
                "usage": "Use for metrics, statistics, and numerical emphasis",
            },
            {
                "id": "Background",
                "name": "Background",
                "category": "background",
                "description": "Animated backgrounds for scene atmosphere",
                "props": ["variant", "intensity", "color"],
                "variants": list(BACKGROUND_CATALOG.keys()),
                "usage": "Use as scene backdrop to set mood and brand identity",
            },
            {
                "id": "Transition",
                "name": "Transition",
                "category": "transition",
                "description": "Scene transitions between content",
                "props": ["type", "direction", "duration", "color"],
                "types": list(TRANSITION_CATALOG.keys()),
                "usage": "Use between scenes to maintain flow and add energy",
            },
            {
                "id": "SplitScreenDemo",
                "name": "Split Screen Demo",
                "category": "layout",
                "description": "Diagonal split between demo video and motion graphics",
                "props": ["demoClipPath", "title", "bullets", "splitAngle", "demoWidth"],
                "usage": "Use for product demos with context overlay",
            },
            {
                "id": "ComparisonView",
                "name": "Comparison View",
                "category": "layout",
                "description": "Side-by-side comparison of two options",
                "props": ["leftTitle", "rightTitle", "leftItems", "rightItems", "highlight"],
                "usage": "Use for before/after or option comparisons",
            },
            {
                "id": "QuoteCard",
                "name": "Quote Card",
                "category": "layout",
                "description": "Animated testimonial or quote display",
                "props": ["quote", "author", "title", "company", "avatar"],
                "usage": "Use for testimonials and social proof",
            },
            {
                "id": "CallToAction",
                "name": "Call To Action",
                "category": "layout",
                "description": "Animated CTA button with attention effects",
                "props": ["text", "url", "style", "animation"],
                "styles": ["primary", "secondary", "outline", "gradient"],
                "usage": "Use in outros to drive viewer action",
            },
        ]

        # Filter by category if specified
        if category:
            components = [c for c in components if c["category"] == category]

        # Add catalog info
        return json.dumps({
            "components": components,
            "count": len(components),
            "categories": ["title", "text", "layout", "data", "background", "transition"],
            "backgrounds": list(BACKGROUND_CATALOG.keys()),
            "transitions": list(TRANSITION_CATALOG.keys()),
            "text_effects": list(TEXT_EFFECT_CATALOG.keys()),
        }, indent=2)

    @mcp.tool()
    async def suggest_transitions(
        from_scene_type: str,
        to_scene_type: str,
        energy_level: str = "medium",
        brand_personality: str = "professional",
    ) -> str:
        """
        Get context-aware transition recommendations between scenes.

        Args:
            from_scene_type: Type of the outgoing scene (intro, feature, demo, etc.)
            to_scene_type: Type of the incoming scene
            energy_level: Desired energy (low, medium, high)
            brand_personality: Brand style (professional, playful, technical, minimal)

        Returns:
            JSON with ranked transition recommendations
        """
        from .video_design_knowledge import BRAND_PERSONALITY_STYLES, TRANSITION_CATALOG

        brand_transitions = BRAND_PERSONALITY_STYLES.get(
            brand_personality, BRAND_PERSONALITY_STYLES["professional"]
        )["transitions"]

        # Score transitions based on context
        scored_transitions = []
        for name, info in TRANSITION_CATALOG.items():
            score = 0

            # Energy match
            if info["energy"] == energy_level:
                score += 3
            elif (energy_level == "medium" and info["energy"] in ["low", "high"]):
                score += 1

            # Brand match
            if name in brand_transitions:
                score += 2

            # Scene type considerations
            if from_scene_type == "intro" and info["energy"] == "high":
                score += 1
            if to_scene_type == "outro" and info["energy"] in ["low", "medium"]:
                score += 1
            if from_scene_type == "demo" and name in ["fade", "wipe"]:
                score += 1

            scored_transitions.append({
                "name": name,
                "score": score,
                "energy": info["energy"],
                "use_for": info["use_for"],
                "avoid_for": info["avoid_for"],
            })

        # Sort by score
        scored_transitions.sort(key=lambda x: x["score"], reverse=True)

        return json.dumps({
            "context": {
                "from_scene": from_scene_type,
                "to_scene": to_scene_type,
                "energy_level": energy_level,
                "brand_personality": brand_personality,
            },
            "recommendations": scored_transitions[:5],
            "best_choice": scored_transitions[0]["name"] if scored_transitions else "fade",
        }, indent=2)

    @mcp.tool()
    async def apply_brand_to_video(script_path: str) -> str:
        """
        Ensure brand consistency in a video script.

        Args:
            script_path: Path to video script YAML

        Returns:
            JSON with brand analysis and suggestions
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

        # Get brand context if available
        brand_colors = {}
        if hasattr(server_instance.project, 'brand_context'):
            brand = server_instance.project.brand_context
            brand_colors = {
                "primary": brand.get_color("brand.primary") if hasattr(brand, 'get_color') else None,
                "secondary": brand.get_color("brand.secondary") if hasattr(brand, 'get_color') else None,
            }

        scenes = script.get("scenes", [])
        suggestions = []
        brand_elements_found = []

        for i, scene in enumerate(scenes):
            scene_id = scene.get("id", f"scene_{i+1}")
            scene_type = scene.get("type", "feature")

            # Check intro/outro for brand elements
            if scene_type == "intro":
                if not scene.get("logo"):
                    suggestions.append({
                        "scene": scene_id,
                        "suggestion": "Add logo to intro scene",
                        "priority": "high",
                    })
                else:
                    brand_elements_found.append({"scene": scene_id, "element": "logo"})

            if scene_type == "outro":
                if not scene.get("cta"):
                    suggestions.append({
                        "scene": scene_id,
                        "suggestion": "Add call-to-action to outro",
                        "priority": "high",
                    })
                if not scene.get("logo"):
                    suggestions.append({
                        "scene": scene_id,
                        "suggestion": "Add logo to outro for brand reinforcement",
                        "priority": "medium",
                    })

            # Check for brand color usage
            background = scene.get("background", "")
            if background and "brand" in str(background).lower():
                brand_elements_found.append({"scene": scene_id, "element": "brand_background"})

        # Consistency check
        backgrounds_used = [s.get("background") for s in scenes if s.get("background")]
        transitions_used = [s.get("transition_in") for s in scenes if s.get("transition_in")]

        if len(set(backgrounds_used)) > 3:
            suggestions.append({
                "scene": "all",
                "suggestion": "Consider using fewer background variants for visual consistency",
                "priority": "medium",
            })

        return json.dumps({
            "script_path": str(validated_path),
            "brand_elements_found": brand_elements_found,
            "suggestions": suggestions,
            "consistency_analysis": {
                "unique_backgrounds": len(set(backgrounds_used)),
                "unique_transitions": len(set(transitions_used)),
                "backgrounds": list(set(backgrounds_used)),
                "transitions": list(set(transitions_used)),
            },
            "brand_colors": brand_colors,
        }, indent=2)

    @mcp.tool()
    async def design_title_sequence(
        title: str,
        tagline: str = None,
        style: str = "professional",
        duration: int = 5,
    ) -> str:
        """
        Generate title card configuration for video intro.

        Args:
            title: Main title text
            tagline: Optional tagline or subtitle
            style: Visual style (professional, playful, technical, minimal, bold)
            duration: Duration in seconds

        Returns:
            JSON with complete title sequence configuration
        """
        from .video_design_knowledge import BRAND_PERSONALITY_STYLES

        style_config = BRAND_PERSONALITY_STYLES.get(style, BRAND_PERSONALITY_STYLES["professional"])

        # Title animation timing
        title_delay = 0.3  # seconds
        tagline_delay = 1.0 if tagline else 0

        # Choose appropriate effects
        text_effect = style_config["text_effects"][0]
        background = style_config["backgrounds"][0]
        transition = style_config["transitions"][0]

        config = {
            "scene": {
                "id": "title_sequence",
                "type": "intro",
                "duration": duration,
                "background": background,
                "transition_in": transition,
            },
            "title": {
                "text": title,
                "effect": text_effect,
                "delay": title_delay,
                "size": "large",
                "position": "center",
            },
        }

        if tagline:
            config["tagline"] = {
                "text": tagline,
                "effect": "fade-up",
                "delay": tagline_delay,
                "size": "medium",
                "position": "below_title",
            }

        config["animation_timeline"] = [
            {"time": 0, "event": "background_start"},
            {"time": title_delay, "event": "title_animate_in"},
            {"time": tagline_delay if tagline else title_delay + 0.5, "event": "tagline_animate_in" if tagline else "title_settle"},
            {"time": duration - 0.5, "event": "prepare_transition"},
        ]

        config["style_notes"] = {
            "style": style,
            "pacing": style_config["pacing"],
            "color_intensity": style_config["color_intensity"],
            "recommended_audio": "upbeat intro music" if style == "playful" else "professional ambiance",
        }

        return json.dumps(config, indent=2)

    @mcp.tool()
    async def compose_scene_layout(
        scene_type: str,
        elements: str,
        aspect_ratio: str = "16:9",
    ) -> str:
        """
        Get visual composition suggestions for a scene.

        Args:
            scene_type: Type of scene (feature, demo, split, stats, etc.)
            elements: JSON array of elements to include (e.g., ["title", "icon", "bullets"])
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)

        Returns:
            JSON with layout composition recommendations
        """
        from .video_design_knowledge import MOTION_DESIGN_PRINCIPLES, SCENE_TYPE_RECOMMENDATIONS

        try:
            element_list = json.loads(elements)
        except json.JSONDecodeError:
            element_list = [e.strip() for e in elements.split(",")]

        scene_rec = SCENE_TYPE_RECOMMENDATIONS.get(
            scene_type, SCENE_TYPE_RECOMMENDATIONS["feature"]
        )

        # Define grid zones based on aspect ratio
        if aspect_ratio == "16:9":
            zones = {
                "top_left": {"x": "0-33%", "y": "0-33%"},
                "top_center": {"x": "33-66%", "y": "0-33%"},
                "top_right": {"x": "66-100%", "y": "0-33%"},
                "middle_left": {"x": "0-33%", "y": "33-66%"},
                "middle_center": {"x": "33-66%", "y": "33-66%"},
                "middle_right": {"x": "66-100%", "y": "33-66%"},
                "bottom_left": {"x": "0-33%", "y": "66-100%"},
                "bottom_center": {"x": "33-66%", "y": "66-100%"},
                "bottom_right": {"x": "66-100%", "y": "66-100%"},
            }
            safe_zone = {"margin": "5%"}
        elif aspect_ratio == "9:16":
            zones = {
                "top": {"x": "10-90%", "y": "0-25%"},
                "upper_middle": {"x": "10-90%", "y": "25-45%"},
                "center": {"x": "10-90%", "y": "35-65%"},
                "lower_middle": {"x": "10-90%", "y": "55-75%"},
                "bottom": {"x": "10-90%", "y": "75-100%"},
            }
            safe_zone = {"margin": "10%"}
        else:  # 1:1
            zones = {
                "top": {"x": "10-90%", "y": "0-33%"},
                "center": {"x": "10-90%", "y": "33-66%"},
                "bottom": {"x": "10-90%", "y": "66-100%"},
            }
            safe_zone = {"margin": "8%"}

        # Suggest element placement
        element_placement = []
        available_zones = list(zones.keys())

        for element in element_list:
            if element == "title":
                zone = "middle_center" if aspect_ratio == "16:9" else "center"
                element_placement.append({"element": element, "zone": zone, "priority": 1})
            elif element == "icon":
                zone = "middle_left" if aspect_ratio == "16:9" else "top"
                element_placement.append({"element": element, "zone": zone, "priority": 2})
            elif element == "bullets":
                zone = "middle_right" if aspect_ratio == "16:9" else "lower_middle"
                element_placement.append({"element": element, "zone": zone, "priority": 3})
            elif element == "demo":
                zone = "middle_left" if scene_type == "split" else "middle_center"
                element_placement.append({"element": element, "zone": zone, "priority": 1})
            elif element == "stats":
                zone = "middle_center"
                element_placement.append({"element": element, "zone": zone, "priority": 1})
            elif element == "cta":
                zone = "bottom_center" if aspect_ratio == "16:9" else "bottom"
                element_placement.append({"element": element, "zone": zone, "priority": 2})
            elif element == "logo":
                zone = "bottom_right" if aspect_ratio == "16:9" else "bottom"
                element_placement.append({"element": element, "zone": zone, "priority": 3})
            else:
                element_placement.append({"element": element, "zone": available_zones[0] if available_zones else "center", "priority": 4})

        return json.dumps({
            "scene_type": scene_type,
            "aspect_ratio": aspect_ratio,
            "grid_zones": zones,
            "safe_zone": safe_zone,
            "element_placement": element_placement,
            "composition_principles": {
                "focal_point": MOTION_DESIGN_PRINCIPLES["composition"]["focal_point"],
                "visual_hierarchy": MOTION_DESIGN_PRINCIPLES["composition"]["visual_hierarchy"],
                "negative_space": MOTION_DESIGN_PRINCIPLES["composition"]["negative_space"],
            },
            "scene_guidelines": scene_rec["guidelines"],
            "recommended_elements": scene_rec.get("elements", []),
        }, indent=2)

    @mcp.tool()
    async def get_design_knowledge(topic: str) -> str:
        """
        Get motion design knowledge and best practices.

        Args:
            topic: Topic to get knowledge about (timing, composition, transitions, pacing, typography, color, all)

        Returns:
            JSON with design principles and recommendations
        """
        from .video_design_knowledge import (
            BACKGROUND_CATALOG,
            MOTION_DESIGN_PRINCIPLES,
            SCENE_TYPE_RECOMMENDATIONS,
            TEXT_EFFECT_CATALOG,
            TRANSITION_CATALOG,
        )

        if topic == "all":
            return json.dumps({
                "motion_design_principles": MOTION_DESIGN_PRINCIPLES,
                "scene_types": list(SCENE_TYPE_RECOMMENDATIONS.keys()),
                "transitions": list(TRANSITION_CATALOG.keys()),
                "backgrounds": list(BACKGROUND_CATALOG.keys()),
                "text_effects": list(TEXT_EFFECT_CATALOG.keys()),
            }, indent=2)

        if topic in MOTION_DESIGN_PRINCIPLES:
            return json.dumps({
                "topic": topic,
                "principles": MOTION_DESIGN_PRINCIPLES[topic],
            }, indent=2)

        if topic == "transitions":
            return json.dumps({
                "topic": "transitions",
                "catalog": TRANSITION_CATALOG,
            }, indent=2)

        if topic == "backgrounds":
            return json.dumps({
                "topic": "backgrounds",
                "catalog": BACKGROUND_CATALOG,
            }, indent=2)

        if topic == "text_effects":
            return json.dumps({
                "topic": "text_effects",
                "catalog": TEXT_EFFECT_CATALOG,
            }, indent=2)

        if topic == "scenes":
            return json.dumps({
                "topic": "scene_types",
                "recommendations": SCENE_TYPE_RECOMMENDATIONS,
            }, indent=2)

        return json.dumps({
            "error": f"Unknown topic: {topic}",
            "available_topics": ["timing", "composition", "transitions", "pacing", "typography", "color", "backgrounds", "text_effects", "scenes", "all"],
        }, indent=2)
