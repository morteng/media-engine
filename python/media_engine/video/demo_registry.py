"""
Demo Registry Module

Manages named demo states for scene-based video capture.
Demo definitions specify a URL and named states with JavaScript setup actions.

Usage:
    registry = DemoRegistry(project)
    demo = registry.load("platform-demo")
    state = demo.states["dashboard"]
    # state.setup contains JS to execute
    # state.wait_for contains CSS selector to await
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import yaml

if TYPE_CHECKING:
    from ..core.project import Project


@dataclass
class DemoState:
    """A named state in a demo with setup action."""

    name: str
    description: str = ""
    setup: Optional[str] = None  # JavaScript to execute
    wait_for: Optional[str] = None  # CSS selector to await


@dataclass
class DemoDefinition:
    """Complete demo definition with URL and named states."""

    name: str
    url: str
    states: dict[str, DemoState] = field(default_factory=dict)
    viewport: dict = field(default_factory=lambda: {"width": 1920, "height": 1080})
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "DemoDefinition":
        """Load demo definition from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        states = {}
        for state_name, state_data in data.get("states", {}).items():
            if isinstance(state_data, str):
                # Simple format: just a description
                states[state_name] = DemoState(
                    name=state_name,
                    description=state_data,
                )
            else:
                # Full format
                states[state_name] = DemoState(
                    name=state_name,
                    description=state_data.get("description", ""),
                    setup=state_data.get("setup"),
                    wait_for=state_data.get("wait_for"),
                )

        viewport = data.get("viewport", {"width": 1920, "height": 1080})

        return cls(
            name=data.get("name", path.stem),
            url=data.get("url", ""),
            states=states,
            viewport=viewport,
            metadata=data.get("metadata", {}),
        )

    def get_state(self, name: str) -> DemoState:
        """Get a state by name, raising KeyError if not found."""
        if name not in self.states:
            available = ", ".join(self.states.keys())
            raise KeyError(
                f"State '{name}' not found in demo '{self.name}'. Available: {available}"
            )
        return self.states[name]


class DemoRegistry:
    """
    Registry for loading and managing demo definitions.

    Searches for demo YAML files in:
    - content/{lang}/demos/
    - demos/
    """

    def __init__(self, project: "Project" = None):
        self.project = project
        self._cache: dict[str, DemoDefinition] = {}

    def load(self, demo_name: str, language: str = "en") -> DemoDefinition:
        """
        Load a demo definition by name.

        Args:
            demo_name: Name of the demo (filename without extension)
            language: Language for localized demos

        Returns:
            DemoDefinition with states

        Raises:
            FileNotFoundError: If demo file not found
        """
        cache_key = f"{language}/{demo_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        demo_path = self._find_demo_file(demo_name, language)
        demo = DemoDefinition.from_yaml(demo_path)
        self._cache[cache_key] = demo
        return demo

    def _find_demo_file(self, demo_name: str, language: str) -> Path:
        """Find demo YAML file in search paths."""
        search_paths = []

        if self.project:
            content_dir = getattr(self.project.config.paths, "content", "content")
            project_root = self.project.root

            # Language-specific demos
            search_paths.append(
                project_root / content_dir / language / "demos" / f"{demo_name}.yaml"
            )
            # Shared demos
            search_paths.append(project_root / "demos" / f"{demo_name}.yaml")
            search_paths.append(project_root / content_dir / "demos" / f"{demo_name}.yaml")

        # Current directory fallback
        search_paths.append(Path.cwd() / "demos" / f"{demo_name}.yaml")

        for path in search_paths:
            if path.exists():
                return path

        searched = "\n  ".join(str(p) for p in search_paths)
        raise FileNotFoundError(f"Demo '{demo_name}' not found. Searched:\n  {searched}")

    def list_demos(self, language: str = "en") -> list[str]:
        """List available demo names."""
        demos = set()

        if self.project:
            content_dir = getattr(self.project.config.paths, "content", "content")
            project_root = self.project.root

            # Language-specific demos
            lang_demos = project_root / content_dir / language / "demos"
            if lang_demos.exists():
                for f in lang_demos.glob("*.yaml"):
                    demos.add(f.stem)

            # Shared demos
            shared_demos = project_root / "demos"
            if shared_demos.exists():
                for f in shared_demos.glob("*.yaml"):
                    demos.add(f.stem)

        return sorted(demos)

    def clear_cache(self):
        """Clear the demo definition cache."""
        self._cache.clear()
