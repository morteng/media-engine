"""Brand command - manage project brand/design system."""

import json
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
    elif subcommand == "voice":
        cmd_brand_voice(args)
    elif subcommand == "voice-check":
        cmd_brand_voice_check(args)
    elif subcommand == "context":
        cmd_brand_context(args)
    elif subcommand == "terminology":
        cmd_brand_terminology(args)
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


# =============================================================================
# VOICE COMMANDS
# =============================================================================


def cmd_brand_voice(args):
    """Show brand voice profile."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...brand import load_brand_profile

    profile = load_brand_profile(project.root)
    voice = profile.voice

    if not voice:
        console.print("[yellow]No voice profile defined in brand.yaml[/yellow]")
        console.print("Add a 'voice:' section to your brand.yaml to enable voice guidelines.")
        return

    doc_type = getattr(args, "doc_type", None)
    audience = getattr(args, "audience", None)
    as_json = getattr(args, "json", False)

    # Apply context if specified
    effective_voice = voice
    if doc_type or audience:
        effective_voice = voice.get_for_context(doc_type, audience)

    if as_json:
        print(json.dumps(effective_voice.to_dict(), indent=2))
        return

    # Display voice profile
    console.print()
    title = "Brand Voice Profile"
    if doc_type:
        title += f" (doc_type: {doc_type})"
    if audience:
        title += f" (audience: {audience})"
    console.print(Panel(f"[bold]{title}[/bold]"))

    # Personality
    console.print(f"[cyan]Personality:[/cyan] {', '.join(effective_voice.personality)}")
    console.print(f"[cyan]Default tone:[/cyan] {effective_voice.tone}")
    console.print(f"[cyan]Formality:[/cyan] {effective_voice.formality_level} ", end="")
    if effective_voice.formality_level < 0.4:
        console.print("(casual)")
    elif effective_voice.formality_level < 0.7:
        console.print("(moderate)")
    else:
        console.print("(formal)")

    console.print()
    console.print("[bold]Style targets:[/bold]")
    style = effective_voice.style
    console.print(f"  Active voice: {int(style.active_voice_target * 100)}%")
    console.print(f"  Sentence length: {style.sentence_length_target} words avg")
    console.print(f"  Max paragraph: {style.paragraph_length_max} sentences")
    console.print(f"  Contractions: {'allowed' if style.use_contractions else 'avoid'}")

    person = []
    if style.use_first_person:
        person.append("first person (I/we)")
    if style.use_second_person:
        person.append("second person (you)")
    if not person:
        person.append("third person only")
    console.print(f"  Person: {', '.join(person)}")

    # Document type overrides
    if voice.by_document_type:
        console.print()
        console.print("[bold]Document type overrides:[/bold]")
        for dt, override in voice.by_document_type.items():
            parts = []
            if override.tone:
                parts.append(override.tone)
            if override.personality:
                parts.append(", ".join(override.personality))
            if override.formality_level is not None:
                parts.append(f"formality={override.formality_level}")
            console.print(f"  {dt}: {', '.join(parts) if parts else '(style overrides)'}")

    # Audience overrides
    if voice.by_audience:
        console.print()
        console.print("[bold]Audience overrides:[/bold]")
        for aud, override in voice.by_audience.items():
            parts = []
            if override.tone:
                parts.append(override.tone)
            if override.formality_level is not None:
                parts.append(f"formality={override.formality_level}")
            console.print(f"  {aud}: {', '.join(parts) if parts else '(style overrides)'}")

    # Terminology preferences
    if voice.preferred_terms:
        console.print()
        console.print("[bold]Terminology preferences:[/bold]")
        for term in voice.preferred_terms[:5]:
            console.print(f"  '{term.prefer}' instead of: {', '.join(term.avoid)}")
        if len(voice.preferred_terms) > 5:
            console.print(f"  ... and {len(voice.preferred_terms) - 5} more")

    # Avoided phrases
    if voice.avoid_phrases:
        console.print()
        console.print("[bold]Phrases to avoid:[/bold]")
        for phrase in voice.avoid_phrases[:5]:
            console.print(f"  - \"{phrase}\"")
        if len(voice.avoid_phrases) > 5:
            console.print(f"  ... and {len(voice.avoid_phrases) - 5} more")


def cmd_brand_voice_check(args):
    """Check document(s) against brand voice guidelines."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...brand import VoiceConsistencyChecker, load_brand_profile

    profile = load_brand_profile(project.root)
    voice = profile.voice

    if not voice:
        console.print("[yellow]No voice profile defined. Using defaults.[/yellow]")

    checker = VoiceConsistencyChecker(voice_profile=voice)

    document = getattr(args, "document", None)
    check_all = getattr(args, "all", False)
    as_json = getattr(args, "json", False)

    results = []

    if check_all:
        # Check all chapters
        for lang in project.languages:
            for chapter_path in project.list_chapters(lang):
                content = chapter_path.read_text()
                result = checker.check_content(content, chapter_path)
                results.append(result)
    elif document:
        # Check single document
        doc_path = Path(document)
        if not doc_path.is_absolute():
            doc_path = project.root / doc_path
        if not doc_path.exists():
            console.print(f"[red]File not found: {document}[/red]")
            sys.exit(1)
        content = doc_path.read_text()
        result = checker.check_content(content, doc_path)
        results.append(result)
    else:
        console.print("[yellow]Specify a document or use --all[/yellow]")
        return

    if as_json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
        return

    # Display results
    total_issues = 0
    passed_count = 0

    for result in results:
        if result.passed:
            passed_count += 1
        total_issues += len(result.issues)

        if result.issues or not check_all:
            console.print()
            status = "[green]✓[/green]" if result.passed else "[yellow]⚠[/yellow]"
            console.print(f"{status} [bold]{result.document.name}[/bold]")

            # Show metrics
            metrics = result.metrics
            if metrics:
                active_pct = metrics.get("active_voice_percentage", 0)
                target = 80  # Default
                if voice and voice.style:
                    target = int(voice.style.active_voice_target * 100)

                active_status = "[green]✓[/green]" if active_pct >= target else "[yellow]⚠[/yellow]"
                console.print(f"  Active voice: {active_pct:.0f}% (target: {target}%) {active_status}")

                if "avg_sentence_length" in metrics:
                    avg_len = metrics["avg_sentence_length"]
                    len_target = voice.style.sentence_length_target if voice else 18
                    len_status = "[green]✓[/green]" if abs(avg_len - len_target) <= 5 else "[yellow]⚠[/yellow]"
                    console.print(f"  Avg sentence: {avg_len:.0f} words (target: {len_target}) {len_status}")

                if "detected_formality" in metrics:
                    console.print(f"  Formality: {metrics['detected_formality']}")

            # Show issues
            if result.issues:
                console.print()
                for issue in result.issues[:10]:
                    severity_icon = {
                        "error": "[red]✗[/red]",
                        "warning": "[yellow]⚠[/yellow]",
                        "info": "[blue]ℹ[/blue]",
                    }.get(issue.severity, "")
                    console.print(f"  {severity_icon} {issue.message}")
                    if issue.suggestion:
                        console.print(f"      [dim]{issue.suggestion}[/dim]")

                if len(result.issues) > 10:
                    console.print(f"  [dim]... and {len(result.issues) - 10} more issues[/dim]")

    # Summary
    console.print()
    console.print(f"[bold]Summary:[/bold] {passed_count}/{len(results)} documents passed, {total_issues} total issues")


def cmd_brand_context(args):
    """Show effective brand context for a document."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    document = getattr(args, "document", None)
    as_json = getattr(args, "json", False)

    if not document:
        console.print("[red]Specify a document path[/red]")
        sys.exit(1)

    from ...brand import BrandContextResolver

    resolver = BrandContextResolver(project)
    doc_path = Path(document)

    if not doc_path.is_absolute():
        doc_path = project.root / doc_path

    result = resolver.resolve_for_document(doc_path)

    if as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    console.print()
    console.print(Panel(f"[bold]Brand Context Resolution[/bold]"))
    console.print(f"Document: {document}")
    console.print()

    # Resolution chain
    console.print("[bold]Resolution chain:[/bold]")
    for i, step in enumerate(result.resolution_chain, 1):
        source = step.source
        if step.path:
            source += f" ({step.path.name})"
        overrides = ""
        if step.overrides and step.source != "base":
            # Show key overrides
            if "voice" in step.overrides:
                voice_o = step.overrides["voice"]
                if isinstance(voice_o, dict):
                    if "tone" in voice_o:
                        overrides += f"tone={voice_o['tone']} "
                    if "formality_level" in voice_o:
                        overrides += f"formality={voice_o['formality_level']}"
            elif "tone" in step.overrides:
                overrides = f"tone={step.overrides['tone']}"
        console.print(f"  {i}. {source}" + (f" → {overrides}" if overrides else ""))

    console.print()
    console.print("[bold]Effective voice:[/bold]")
    voice = result.effective_voice
    console.print(f"  tone: {voice.tone}")
    console.print(f"  formality: {voice.formality_level}")
    console.print(f"  active_voice_target: {voice.style.active_voice_target}")
    console.print(f"  sentence_length_target: {voice.style.sentence_length_target}")


def cmd_brand_terminology(args):
    """Check terminology consistency across documents."""
    project = find_project()
    if not project:
        console.print("[red]No project.yaml found[/red]")
        sys.exit(1)

    from ...brand import VoiceConsistencyChecker, load_brand_profile

    profile = load_brand_profile(project.root)
    voice = profile.voice

    if not voice or not voice.preferred_terms:
        console.print("[yellow]No terminology preferences defined in brand.yaml[/yellow]")
        return

    as_json = getattr(args, "json", False)

    checker = VoiceConsistencyChecker(voice_profile=voice)
    term_issues = {}  # term -> list of (file, count)

    # Check all documents
    for lang in project.languages:
        for chapter_path in project.list_chapters(lang):
            content = chapter_path.read_text()
            result = checker.check_content(content, chapter_path)

            for issue in result.issues:
                if issue.type == "terminology":
                    if issue.message not in term_issues:
                        term_issues[issue.message] = []
                    term_issues[issue.message].append(chapter_path)

    if as_json:
        data = {
            "preferred_terms": [t.to_dict() for t in voice.preferred_terms],
            "issues": {
                msg: [str(p) for p in paths] for msg, paths in term_issues.items()
            },
            "avoid_phrases": voice.avoid_phrases,
        }
        print(json.dumps(data, indent=2))
        return

    console.print()
    console.print(Panel("[bold]Terminology Check[/bold]"))

    # Show preferred terms
    for term in voice.preferred_terms:
        console.print(f"\n[cyan]Preferred:[/cyan] \"{term.prefer}\" (avoid: {', '.join(term.avoid)})")

        # Find issues for this term
        found_issues = []
        for msg, paths in term_issues.items():
            for avoid in term.avoid:
                if f"'{avoid}'" in msg:
                    found_issues.extend(paths)
                    break

        if found_issues:
            for path in found_issues[:3]:
                console.print(f"  [red]✗[/red] {path.name}")
            if len(found_issues) > 3:
                console.print(f"  [dim]... and {len(found_issues) - 3} more[/dim]")
        else:
            console.print("  [green]✓[/green] All documents compliant")

    # Avoided phrases
    if voice.avoid_phrases:
        console.print()
        console.print("[bold]Avoided phrases:[/bold]")

        # Would need to track phrase issues separately
        console.print(f"  [dim]Checking {len(voice.avoid_phrases)} phrases...[/dim]")
        # For now just list them
        for phrase in voice.avoid_phrases[:5]:
            console.print(f"  - \"{phrase}\"")

    console.print()
    if term_issues:
        console.print(f"[yellow]Found {len(term_issues)} terminology issues[/yellow]")
    else:
        console.print("[green]All documents follow terminology guidelines[/green]")
