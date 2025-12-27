"""Motion Design Knowledge Base.

Professional motion graphics principles and recommendations for AI-assisted video creation.
This knowledge enables the video producer agent to make professional design decisions autonomously.
"""

MOTION_DESIGN_PRINCIPLES = {
    "timing": {
        "rule_of_thirds": "Key moments at 1/3 and 2/3 of duration",
        "ease_in_out": "Natural acceleration/deceleration for smooth motion",
        "anticipation": "Small movement before main action builds expectation",
        "follow_through": "Elements settle after main action for realism",
        "secondary_action": "Supporting movements enhance primary action",
        "hold_frames": "Pause at key poses for readability",
    },
    "composition": {
        "visual_hierarchy": "Guide eye with size, contrast, and position",
        "negative_space": "Breathing room enhances focus on key elements",
        "rule_of_thirds": "Place key elements on grid intersections",
        "z_depth": "Layering creates depth perception and visual interest",
        "focal_point": "One clear subject per scene for clarity",
        "balance": "Distribute visual weight across the frame",
        "alignment": "Consistent element positioning creates order",
    },
    "transitions": {
        "match_cut": "Visual similarity bridges scenes seamlessly",
        "j_cut_l_cut": "Audio leads or trails video for continuity",
        "whip_pan": "Fast motion hides cut for energy",
        "morph": "Shape transformation creates continuity",
        "rhythm": "Cuts align with audio beats for impact",
        "motivation": "Transitions should have purpose, not decoration",
    },
    "pacing": {
        "hook": "First 3 seconds critical for viewer retention",
        "breathing": "Pause after information-dense sections",
        "crescendo": "Build intensity toward climax",
        "resolution": "Cool-down period before end",
        "rhythm": "Consistent timing creates flow",
        "variety": "Mix fast and slow sections for engagement",
    },
    "typography": {
        "legibility": "Minimum 2 seconds for text on screen",
        "hierarchy": "Title > subtitle > body sizing",
        "animation": "Text reveals match reading speed",
        "contrast": "Ensure readability on any background",
        "positioning": "Keep text in safe zones",
        "kinetic": "Motion enhances meaning, not distracts",
    },
    "color": {
        "consistency": "Use brand colors throughout",
        "contrast": "Sufficient contrast for accessibility",
        "mood": "Colors evoke emotional response",
        "hierarchy": "Primary actions use primary colors",
        "animation": "Color transitions should be subtle",
    },
}

SCENE_TYPE_RECOMMENDATIONS = {
    "intro": {
        "duration": "3-7 seconds",
        "duration_range": (3, 7),
        "background": ["aurora", "cyber", "particles"],
        "transition_in": ["glitch", "aurora-sweep", "zoom-burst"],
        "text_effect": ["bounce", "elastic", "scale-pop"],
        "guidelines": "Bold, attention-grabbing, establish brand identity quickly",
        "elements": ["Logo", "Title", "Tagline"],
        "pacing": "Fast, energetic, immediate impact",
    },
    "feature": {
        "duration": "8-15 seconds per feature",
        "duration_range": (8, 15),
        "background": ["grid", "dark", "pulse"],
        "transition_in": ["slide-left", "slice", "fade"],
        "text_effect": ["fade-up", "wave"],
        "guidelines": "Clear hierarchy, icon + text pairing, one concept per scene",
        "elements": ["Icon", "Title", "Bullet points", "Visual"],
        "pacing": "Measured, allow time for comprehension",
    },
    "demo": {
        "duration": "Match voiceover exactly",
        "duration_range": (10, 30),
        "background": ["dark"],  # Demo content is focus
        "transition_in": ["fade", "wipe"],
        "text_effect": ["fade-up"],
        "guidelines": "Let demo breathe, minimal overlays, focus on action",
        "elements": ["Demo video", "Subtle highlights", "Minimal text"],
        "pacing": "Follow the action, don't rush",
    },
    "split": {
        "duration": "10-20 seconds",
        "duration_range": (10, 20),
        "split_angle": "12-18 degrees",
        "demo_width": "55-65%",
        "background": ["dark", "grid"],
        "transition_in": ["diagonal-split", "slice"],
        "text_effect": ["fade-up"],
        "guidelines": "Balance demo visibility with context, clear visual separation",
        "elements": ["Demo video", "Text overlay", "Bullets"],
        "pacing": "Synchronized with demo and narration",
    },
    "stats": {
        "duration": "5-10 seconds",
        "duration_range": (5, 10),
        "background": ["dark", "grid", "pulse"],
        "transition_in": ["fade", "scale-pop"],
        "text_effect": ["counter", "scale-pop"],
        "guidelines": "Numbers should animate, provide context for metrics",
        "elements": ["Large number", "Label", "Context"],
        "pacing": "Allow time to read and process",
    },
    "testimonial": {
        "duration": "10-20 seconds",
        "duration_range": (10, 20),
        "background": ["dark", "gradient"],
        "transition_in": ["fade"],
        "text_effect": ["fade-up"],
        "guidelines": "Authentic feel, readable quotes, credibility elements",
        "elements": ["Quote", "Name", "Title", "Company/Photo"],
        "pacing": "Match reading speed of quote",
    },
    "comparison": {
        "duration": "8-15 seconds",
        "duration_range": (8, 15),
        "background": ["grid", "dark"],
        "transition_in": ["slide-left", "split"],
        "text_effect": ["fade-up"],
        "guidelines": "Clear visual distinction between options",
        "elements": ["Side-by-side elements", "Labels", "Highlights"],
        "pacing": "Give equal time to each option",
    },
    "outro": {
        "duration": "5-10 seconds",
        "duration_range": (5, 10),
        "background": ["aurora", "waves", "particles"],
        "transition_in": ["aurora-sweep", "fade"],
        "text_effect": ["fade-up", "bounce"],
        "guidelines": "Clear CTA, memorable brand moment, sense of completion",
        "elements": ["CTA button", "Logo", "Contact info"],
        "pacing": "Calm, resolved, inviting action",
    },
}

TRANSITION_CATALOG = {
    "fade": {
        "energy": "low",
        "use_for": ["any scene change", "calm transitions"],
        "avoid_for": ["high-energy sequences"],
    },
    "wipe": {
        "energy": "medium",
        "use_for": ["directional flow", "progression"],
        "avoid_for": ["random placement"],
    },
    "glitch": {
        "energy": "high",
        "use_for": ["tech content", "intros", "emphasis"],
        "avoid_for": ["calm sections", "professional/conservative brands"],
    },
    "aurora-sweep": {
        "energy": "medium",
        "use_for": ["brand moments", "intros/outros"],
        "avoid_for": ["technical demos"],
    },
    "slice": {
        "energy": "high",
        "use_for": ["dynamic reveals", "feature highlights"],
        "avoid_for": ["subtle transitions"],
    },
    "zoom-burst": {
        "energy": "high",
        "use_for": ["emphasis", "reveals", "intros"],
        "avoid_for": ["frequent use", "calm content"],
    },
    "diagonal-split": {
        "energy": "medium",
        "use_for": ["split screen", "comparisons"],
        "avoid_for": ["single-focus scenes"],
    },
    "liquid": {
        "energy": "medium",
        "use_for": ["organic feel", "creative content"],
        "avoid_for": ["technical content", "formal brands"],
    },
    "pixel-dissolve": {
        "energy": "medium",
        "use_for": ["tech/digital themes", "data visualization"],
        "avoid_for": ["organic content"],
    },
    "grid-reveal": {
        "energy": "medium",
        "use_for": ["structured content", "data", "lists"],
        "avoid_for": ["emotional content"],
    },
    "radial": {
        "energy": "medium",
        "use_for": ["focus reveals", "centered content"],
        "avoid_for": ["edge-to-edge content"],
    },
}

BACKGROUND_CATALOG = {
    "dark": {
        "mood": "professional",
        "use_for": ["demos", "text-heavy scenes", "focus content"],
        "contrast": "high",
    },
    "aurora": {
        "mood": "dynamic",
        "use_for": ["intros", "outros", "brand moments"],
        "contrast": "medium",
    },
    "grid": {
        "mood": "technical",
        "use_for": ["features", "data", "structured content"],
        "contrast": "high",
    },
    "particles": {
        "mood": "energetic",
        "use_for": ["intros", "highlights", "transitions"],
        "contrast": "medium",
    },
    "pulse": {
        "mood": "active",
        "use_for": ["features", "stats", "action"],
        "contrast": "medium",
    },
    "cyber": {
        "mood": "futuristic",
        "use_for": ["tech content", "innovation themes"],
        "contrast": "high",
    },
    "waves": {
        "mood": "calm",
        "use_for": ["outros", "testimonials", "soft content"],
        "contrast": "medium",
    },
}

TEXT_EFFECT_CATALOG = {
    "fade-up": {
        "energy": "low",
        "readability": "high",
        "use_for": ["any text", "professional content"],
    },
    "bounce": {
        "energy": "high",
        "readability": "medium",
        "use_for": ["intros", "emphasis", "playful brands"],
    },
    "elastic": {
        "energy": "high",
        "readability": "medium",
        "use_for": ["intros", "playful content"],
    },
    "wave": {
        "energy": "medium",
        "readability": "medium",
        "use_for": ["lists", "multi-word reveals"],
    },
    "split": {
        "energy": "high",
        "readability": "low",
        "use_for": ["emphasis", "key words only"],
    },
    "scale-pop": {
        "energy": "high",
        "readability": "high",
        "use_for": ["numbers", "stats", "emphasis"],
    },
    "rotate": {
        "energy": "medium",
        "readability": "low",
        "use_for": ["single words", "logos"],
    },
    "glitch": {
        "energy": "high",
        "readability": "low",
        "use_for": ["tech content", "brief emphasis"],
    },
}

# Brand personality to visual style mapping
BRAND_PERSONALITY_STYLES = {
    "professional": {
        "backgrounds": ["dark", "grid", "pulse"],
        "transitions": ["fade", "slide-left", "wipe"],
        "text_effects": ["fade-up", "scale-pop"],
        "pacing": "measured",
        "color_intensity": "moderate",
    },
    "playful": {
        "backgrounds": ["aurora", "particles", "waves"],
        "transitions": ["glitch", "zoom-burst", "bounce"],
        "text_effects": ["bounce", "elastic", "wave"],
        "pacing": "fast",
        "color_intensity": "high",
    },
    "technical": {
        "backgrounds": ["cyber", "grid", "dark"],
        "transitions": ["pixel-dissolve", "grid-reveal", "slice"],
        "text_effects": ["glitch", "split", "fade-up"],
        "pacing": "precise",
        "color_intensity": "moderate",
    },
    "minimal": {
        "backgrounds": ["dark"],
        "transitions": ["fade", "wipe"],
        "text_effects": ["fade-up"],
        "pacing": "slow",
        "color_intensity": "low",
    },
    "luxury": {
        "backgrounds": ["dark", "gradient"],
        "transitions": ["fade", "radial"],
        "text_effects": ["fade-up", "scale-pop"],
        "pacing": "slow",
        "color_intensity": "moderate",
    },
    "startup": {
        "backgrounds": ["aurora", "particles", "grid"],
        "transitions": ["glitch", "slice", "zoom-burst"],
        "text_effects": ["bounce", "scale-pop", "wave"],
        "pacing": "fast",
        "color_intensity": "high",
    },
}


def get_scene_recommendation(scene_type: str, brand_personality: str = "professional") -> dict:
    """Get combined scene and brand recommendations."""
    scene_rec = SCENE_TYPE_RECOMMENDATIONS.get(scene_type, SCENE_TYPE_RECOMMENDATIONS["feature"])
    brand_style = BRAND_PERSONALITY_STYLES.get(brand_personality, BRAND_PERSONALITY_STYLES["professional"])

    return {
        "scene_type": scene_type,
        "brand_personality": brand_personality,
        "duration": scene_rec["duration"],
        "duration_range": scene_rec.get("duration_range", (5, 15)),
        "backgrounds": brand_style["backgrounds"],
        "transitions": brand_style["transitions"],
        "text_effects": brand_style["text_effects"],
        "pacing": brand_style["pacing"],
        "guidelines": scene_rec["guidelines"],
        "elements": scene_rec.get("elements", []),
    }


def validate_scene_timing(scenes: list) -> list:
    """Validate scene timing and return issues."""
    issues = []
    total_duration = 0

    for i, scene in enumerate(scenes):
        scene_type = scene.get("type", "feature")
        duration = scene.get("duration", 5)
        total_duration += duration

        rec = SCENE_TYPE_RECOMMENDATIONS.get(scene_type, SCENE_TYPE_RECOMMENDATIONS["feature"])
        duration_range = rec.get("duration_range", (5, 15))

        if duration < duration_range[0]:
            issues.append({
                "scene_index": i,
                "scene_id": scene.get("id", f"scene_{i+1}"),
                "issue": "too_short",
                "current": duration,
                "recommended_min": duration_range[0],
            })
        elif duration > duration_range[1]:
            issues.append({
                "scene_index": i,
                "scene_id": scene.get("id", f"scene_{i+1}"),
                "issue": "too_long",
                "current": duration,
                "recommended_max": duration_range[1],
            })

    return issues
