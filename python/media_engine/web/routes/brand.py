"""
Brand API Routes

Provides brand/design system configuration to the dashboard.
"""

from typing import TYPE_CHECKING, Any, Callable, Dict

if TYPE_CHECKING:
    from fastapi import APIRouter

    from ...core.project import Project
    from ..websocket import ConnectionManager


def register_brand_routes(
    router: "APIRouter",
    get_project: Callable[[], "Project"],
    manager: "ConnectionManager",
) -> None:
    """Register brand-related routes."""
    from fastapi import HTTPException

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
