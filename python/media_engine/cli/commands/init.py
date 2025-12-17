"""Init command - initialize a new project."""

from datetime import datetime
from pathlib import Path

from rich.console import Console

console = Console()


def cmd_init(args):
    """Initialize a new project."""
    project_dir = Path(args.directory or ".").resolve()
    project_name = args.name or project_dir.name

    console.print(f"[bold]Initializing project: {project_name}[/bold]")

    # Create directory structure
    dirs = [
        "content/en/chapters",
        "content/en/scripts",
        "assets/brand",
        "output",
    ]

    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
        console.print(f"  [dim]Created {d}/[/dim]")

    # Create project.yaml
    project_yaml = project_dir / "project.yaml"
    if not project_yaml.exists():
        project_yaml.write_text(f"""# Media Engine Project Configuration

project:
  name: "{project_name}"
  description: ""

localization:
  source_language: "en"
  languages:
    en:
      name: "English"
      voice_id: ""

voiceover:
  provider: "elevenlabs"
  stability: 0.5
  similarity_boost: 0.75

video:
  width: 1920
  height: 1080
  fps: 30

paths:
  content: "content"
  assets: "assets"
  output: "output"
""")
        console.print("  [green]Created project.yaml[/green]")

    # Create theme.yaml
    theme_yaml = project_dir / "theme.yaml"
    if not theme_yaml.exists():
        theme_yaml.write_text("""# Design System Theme

name: "Default Theme"

colors:
  primary: "#2c2522"
  secondary: "#4a4340"
  accent: "#0066cc"
  background: "#ffffff"
  text: "#2c2522"

  dark:
    background: "#1a1a1a"
    text: "#f0f0f0"
    accent: "#3399ff"

typography:
  heading: "Georgia"
  body: "Helvetica Neue"
  code: "Menlo"
  base_size: 16
  scale: 1.25
""")
        console.print("  [green]Created theme.yaml[/green]")

    # Create sample chapter
    sample_chapter = project_dir / "content/en/chapters/01_introduction.md"
    if not sample_chapter.exists():
        sample_chapter.write_text(f"""---
title: "Introduction"
version: "0.1.0"
status: "draft"
last_modified: "{datetime.now().strftime("%Y-%m-%d")}"
freshness_days: 30
---

# Introduction

Welcome to {project_name}.

## Getting Started

This is your first chapter. Edit this file to add your content.
""")
        console.print("  [green]Created sample chapter[/green]")

    console.print("\n[bold green]Project initialized![/bold green]")
    console.print("  Run [cyan]media-engine status[/cyan] to see project status")
    console.print("  Run [cyan]media-engine build[/cyan] to build outputs")
