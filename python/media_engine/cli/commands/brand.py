"""Brand command - manage project brand/design system."""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...core import find_project

console = Console()


def cmd_brand(args):
    """Brand management commands."""
    subcommand = getattr(args, "brand_command", None)

    if subcommand == "status":
        cmd_brand_status(args)
    elif subcommand == "migrate":
        cmd_brand_migrate(args)
    elif subcommand == "validate":
        cmd_brand_validate(args)
    elif subcommand == "export-css":
        cmd_brand_export_css(args)
    elif subcommand == "init":
        cmd_brand_init(args)
    else:
        # Default: show status
        cmd_brand_status(args)


def cmd_brand_status(args):
    """Show brand/design system status."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    # Load brand profile
    from ...brand import load_brand_profile

    profile = load_brand_profile(project.root)

    console.print()
    console.print(Panel(f"[bold]{profile.name}[/bold]", title="Brand Profile"))

    # Colors table
    colors_table = Table(title="Colors", show_header=True)
    colors_table.add_column("Category", style="cyan")
    colors_table.add_column("Property", style="white")
    colors_table.add_column("Value", style="green")

    colors_table.add_row("Brand", "Primary", profile.colors.brand.primary)
    colors_table.add_row("Brand", "Secondary", profile.colors.brand.secondary)
    colors_table.add_row("Brand", "Accent", profile.colors.brand.accent)
    colors_table.add_row("Semantic", "Success", profile.colors.semantic.success)
    colors_table.add_row("Semantic", "Warning", profile.colors.semantic.warning)
    colors_table.add_row("Semantic", "Error", profile.colors.semantic.error)
    colors_table.add_row("Semantic", "Info", profile.colors.semantic.info)

    console.print(colors_table)

    # Typography table
    typo_table = Table(title="Typography", show_header=True)
    typo_table.add_column("Role", style="cyan")
    typo_table.add_column("Family", style="white")
    typo_table.add_column("Source", style="dim")
    typo_table.add_column("Weights")

    typo_table.add_row(
        "Heading",
        profile.typography.heading.family,
        profile.typography.heading.source,
        ", ".join(str(w) for w in profile.typography.heading.weights),
    )
    typo_table.add_row(
        "Body",
        profile.typography.body.family,
        profile.typography.body.source,
        ", ".join(str(w) for w in profile.typography.body.weights),
    )
    typo_table.add_row(
        "Code",
        profile.typography.code.family,
        profile.typography.code.source,
        ", ".join(str(w) for w in profile.typography.code.weights),
    )

    console.print(typo_table)

    # Logo status
    logos_table = Table(title="Logos", show_header=True)
    logos_table.add_column("Variant", style="cyan")
    logos_table.add_column("Status", style="white")
    logos_table.add_column("Path")

    for variant in ["primary", "dark", "square", "icon"]:
        logo = profile.logos.get(variant)
        if logo.exists():
            logos_table.add_row(variant, "[green]Found[/green]", str(logo.path))
        else:
            logos_table.add_row(variant, "[dim]Not found[/dim]", "-")

    console.print(logos_table)

    # Check if using legacy theme.yaml
    brand_yaml = project.root / "brand.yaml"
    theme_yaml = project.root / "theme.yaml"

    if not brand_yaml.exists() and theme_yaml.exists():
        console.print()
        console.print(
            "[yellow]Using legacy theme.yaml. Run 'media-engine brand migrate' to upgrade.[/yellow]"
        )


def cmd_brand_migrate(args):
    """Migrate theme.yaml to brand.yaml."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...brand.loader import migrate_theme_to_brand

    dry_run = getattr(args, "dry_run", False)

    result = migrate_theme_to_brand(project.root, dry_run=dry_run)

    if result is None:
        console.print(
            "[yellow]Nothing to migrate (no theme.yaml or brand.yaml already exists)[/yellow]"
        )
        return

    if dry_run:
        console.print(f"[dim]Would create: {result}[/dim]")
    else:
        console.print(f"[green]Created: {result}[/green]")
        console.print()
        console.print("Next steps:")
        console.print("  1. Review brand.yaml and customize as needed")
        console.print("  2. Move logos to brand/logos/ directory")
        console.print("  3. Remove theme.yaml when ready")


def cmd_brand_validate(args):
    """Validate brand.yaml configuration."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    brand_yaml = project.root / "brand.yaml"
    if not brand_yaml.exists():
        console.print("[yellow]No brand.yaml found. Using theme.yaml fallback.[/yellow]")
        return

    from ...brand import load_brand

    try:
        profile = load_brand(brand_yaml)
        console.print("[green]brand.yaml is valid[/green]")
        console.print(f"  Name: {profile.name}")
        console.print(f"  Colors: {len(vars(profile.colors.brand))} brand colors defined")
        console.print(
            f"  Fonts: {profile.typography.heading.family}, {profile.typography.body.family}"
        )
    except Exception as e:
        console.print(f"[red]Validation error: {e}[/red]")
        sys.exit(1)


def cmd_brand_export_css(args):
    """Export CSS variables from brand configuration."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...brand import BrandContext, load_brand_profile

    profile = load_brand_profile(project.root)
    ctx = BrandContext(profile=profile)

    output = getattr(args, "output", None)
    dark_mode = getattr(args, "dark", False)

    css = ctx.generate_complete_css(include_fonts=False, dark_mode=dark_mode)

    if output:
        from pathlib import Path

        output_path = Path(output)
        output_path.write_text(css)
        console.print(f"[green]CSS exported to: {output_path}[/green]")
    else:
        print(css)


def cmd_brand_init(args):
    """Initialize brand.yaml from template."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    brand_yaml = project.root / "brand.yaml"
    if brand_yaml.exists():
        console.print("[yellow]brand.yaml already exists[/yellow]")
        return

    # Create brand directory structure
    brand_dir = project.root / "brand"
    logos_dir = brand_dir / "logos"
    fonts_dir = brand_dir / "fonts"

    logos_dir.mkdir(parents=True, exist_ok=True)
    fonts_dir.mkdir(parents=True, exist_ok=True)

    # Create template brand.yaml
    template = """name: "{project_name}"

# === IDENTITY ===
identity:
  logos:
    primary:
      path: "brand/logos/logo.svg"
      alt: "{project_name} Logo"
    dark:
      path: "brand/logos/logo-dark.svg"
    icon:
      path: "brand/logos/icon.png"
      sizes: [16, 32, 64, 128, 256]
  legal:
    copyright: ""
    tagline: ""

# === COLORS ===
colors:
  brand:
    primary: "#6366f1"
    secondary: "#8b5cf6"
    accent: "#06b6d4"

  semantic:
    success: "#10b981"
    warning: "#f59e0b"
    error: "#ef4444"
    info: "#3b82f6"

  text:
    primary: "#1f2937"
    secondary: "#4b5563"
    muted: "#9ca3af"
    inverse: "#ffffff"

  background:
    primary: "#ffffff"
    secondary: "#f9fafb"
    tertiary: "#f3f4f6"

  dark:
    text:
      primary: "#f9fafb"
      muted: "#9ca3af"
    background:
      primary: "#111827"
      secondary: "#1f2937"

# === TYPOGRAPHY ===
typography:
  fonts:
    heading:
      family: "Inter"
      weights: [500, 600, 700]
      source: "google"
    body:
      family: "Inter"
      weights: [400, 500]
      source: "google"
    code:
      family: "JetBrains Mono"
      weights: [400, 500]
      source: "google"

  scale:
    xs: 12
    sm: 14
    base: 16
    lg: 18
    xl: 20
    2xl: 24
    3xl: 30
    4xl: 36
    display: 72

# === SPACING ===
spacing:
  unit: 4
  scale:
    0: 0
    1: 4
    2: 8
    3: 12
    4: 16
    6: 24
    8: 32
    12: 48

# === BORDERS ===
borders:
  radius:
    sm: 2
    md: 4
    lg: 8
    xl: 12
    full: 9999

# === SHADOWS ===
shadows:
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
  lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
"""

    brand_yaml.write_text(template.format(project_name=project.name))
    console.print(f"[green]Created: {brand_yaml}[/green]")
    console.print(f"[green]Created: {logos_dir}[/green]")
    console.print(f"[green]Created: {fonts_dir}[/green]")
    console.print()
    console.print("Next steps:")
    console.print("  1. Add logo files to brand/logos/")
    console.print("  2. Customize colors and typography in brand.yaml")
    console.print("  3. Run 'media-engine brand status' to verify")
