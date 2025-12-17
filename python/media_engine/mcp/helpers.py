"""Helper functions for MCP server."""


def get_health_summary(project) -> dict:
    """Get project health summary."""
    if not project:
        return {}

    # Check translations
    try:
        from ..cms.translation import TranslationTracker

        tracker = TranslationTracker(project)
        outdated = tracker.get_outdated_translations()
        trans_status = "all_synced" if not outdated else f"{len(outdated)}_outdated"
    except Exception:
        trans_status = "unknown"

    # Check quality
    try:
        from ..quality import run_quality_checks

        report = run_quality_checks(project, console_output=False)
        if report.error_count > 0:
            quality_status = f"{report.error_count}_errors"
        elif report.warning_count > 0:
            quality_status = f"{report.warning_count}_warnings"
        else:
            quality_status = "passed"
    except Exception:
        quality_status = "unknown"

    return {
        "translation_status": trans_status,
        "quality_status": quality_status,
    }


def version_diff(old: str, new: str) -> str:
    """Calculate version difference description."""
    try:
        old_parts = [int(x) for x in old.split(".")]
        new_parts = [int(x) for x in new.split(".")]

        # Pad to same length
        while len(old_parts) < 3:
            old_parts.append(0)
        while len(new_parts) < 3:
            new_parts.append(0)

        if new_parts[0] > old_parts[0]:
            return f"{new_parts[0] - old_parts[0]} major"
        elif new_parts[1] > old_parts[1]:
            return f"{new_parts[1] - old_parts[1]} minor"
        elif new_parts[2] > old_parts[2]:
            return f"{new_parts[2] - old_parts[2]} patch"
        return "same"
    except Exception:
        return "unknown"
