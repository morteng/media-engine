"""
Release Command - Copy production videos to deliverables folder.

Only copies production-quality videos (not preview videos).
"""

import json
import shutil

from ...core.project import find_project
from ...video.quality import is_preview_video


def add_parser(subparsers):
    """Add release command parser."""
    parser = subparsers.add_parser(
        "release",
        help="Copy production videos to deliverables folder",
        description="Copy production-quality videos to the deliverables folder. "
        "Preview videos (*.preview.mp4) are automatically skipped.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without actually copying",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing files in deliverables",
    )
    parser.add_argument(
        "--lang",
        "-l",
        help="Only release videos for specific language",
    )
    parser.set_defaults(func=cmd_release)


def cmd_release(args):
    """Execute release command."""
    project = find_project()
    if not project:
        print("Error: No project found. Run from project directory or specify path.")
        return 1

    deliverables_dir = project.deliverables_dir
    output_dir = project.output_dir

    print(f"Releasing videos to: {deliverables_dir}")
    print(f"Source directory: {output_dir}")

    if args.dry_run:
        print("[DRY RUN - no files will be copied]")
    print()

    # Find all video files
    video_files = list(output_dir.rglob("*.mp4"))

    if args.lang:
        # Filter by language
        video_files = [v for v in video_files if f"/{args.lang}/" in str(v)]

    if not video_files:
        print("No video files found.")
        return 0

    # Categorize videos
    production_videos = []
    preview_videos = []

    for video_path in video_files:
        if is_preview_video(video_path.name):
            preview_videos.append(video_path)
        else:
            # Also check props.json for is_releasable
            props_path = video_path.with_name(video_path.stem + ".props.json")
            if props_path.exists():
                try:
                    props = json.loads(props_path.read_text())
                    if not props.get("is_releasable", True):
                        preview_videos.append(video_path)
                        continue
                except (json.JSONDecodeError, IOError):
                    pass
            production_videos.append(video_path)

    # Report preview videos being skipped
    if preview_videos:
        print(f"Skipping {len(preview_videos)} preview video(s):")
        for v in preview_videos[:5]:
            print(f"  - {v.name}")
        if len(preview_videos) > 5:
            print(f"  ... and {len(preview_videos) - 5} more")
        print()

    if not production_videos:
        print("No production videos to release.")
        return 0

    # Create deliverables directory
    if not args.dry_run:
        deliverables_dir.mkdir(parents=True, exist_ok=True)

    # Copy production videos
    copied = 0
    skipped = 0

    print(f"Releasing {len(production_videos)} production video(s):")
    for video_path in production_videos:
        # Determine destination path (preserve language subdirectory)
        try:
            rel_path = video_path.relative_to(output_dir)
            dest_path = deliverables_dir / rel_path
        except ValueError:
            dest_path = deliverables_dir / video_path.name

        # Check if destination exists
        if dest_path.exists() and not args.force:
            print(f"  [SKIP] {video_path.name} (already exists, use --force to overwrite)")
            skipped += 1
            continue

        if args.dry_run:
            print(f"  [WOULD COPY] {video_path.name} -> {dest_path}")
            copied += 1
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(video_path, dest_path)
            print(f"  [COPIED] {video_path.name} -> {dest_path}")
            copied += 1

    print()
    if args.dry_run:
        print(f"Would release: {copied} video(s)")
    else:
        print(f"Released: {copied} video(s)")

    if skipped:
        print(f"Skipped: {skipped} (use --force to overwrite)")

    return 0
