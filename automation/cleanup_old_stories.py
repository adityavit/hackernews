#!/usr/bin/env python3
"""
Cleanup automation script that:
1. Fetches the current top stories
2. Identifies story directories in ui/api/stories that are no longer in top stories
3. Removes those old directories to free up space
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set

import requests


DEFAULT_API_BASE = os.getenv("HN_API_BASE", "http://127.0.0.1:5000").rstrip("/")
DEFAULT_TOP_STORIES_PATH = Path("ui/api/top-stories.json")
DEFAULT_STORIES_DIR = Path("ui/api/stories")
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def fetch_current_story_ids(api_base: str, top_stories_path: Path) -> Set[str]:
    """Fetch current top story IDs, either from API or existing file."""
    # First try to fetch fresh data from API
    try:
        print(f"Fetching fresh top stories from {api_base}/api/top-stories...")
        resp = requests.get(f"{api_base}/api/top-stories", timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Handle both direct array and wrapped format
        stories = data if isinstance(data, list) else data.get("data", [])
        story_ids = {str(story["id"]) for story in stories if "id" in story}
        print(f"Fetched {len(story_ids)} current story IDs from API")
        return story_ids

    except Exception as e:
        print(f"Failed to fetch from API: {e}", file=sys.stderr)

        # Fallback to existing top-stories.json file
        if top_stories_path.exists():
            print(f"Falling back to existing file: {top_stories_path}")
            with top_stories_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            stories = data.get("data", []) if isinstance(data, dict) else data
            story_ids = {str(story["id"]) for story in stories if "id" in story}
            print(f"Loaded {len(story_ids)} story IDs from existing file")
            return story_ids
        else:
            raise Exception(f"No API access and no existing file at {top_stories_path}")


def find_existing_story_dirs(stories_dir: Path) -> Set[str]:
    """Find all existing story directories in ui/api/stories."""
    if not stories_dir.exists():
        print(f"Stories directory {stories_dir} does not exist")
        return set()

    story_dirs = set()
    for item in stories_dir.iterdir():
        if item.is_dir() and item.name.isdigit():
            story_dirs.add(item.name)

    print(f"Found {len(story_dirs)} existing story directories")
    return story_dirs


def cleanup_old_stories(stories_dir: Path, current_ids: Set[str], dry_run: bool = False) -> List[str]:
    """Remove story directories that are not in current top stories."""
    existing_dirs = find_existing_story_dirs(stories_dir)
    old_dirs = existing_dirs - current_ids

    if not old_dirs:
        print("No old story directories to clean up")
        return []

    print(f"Found {len(old_dirs)} old story directories to remove")

    removed = []
    for story_id in sorted(old_dirs):
        story_dir = stories_dir / story_id

        if dry_run:
            print(f"[DRY RUN] Would remove: {story_dir}")
        else:
            try:
                print(f"Removing: {story_dir}")
                shutil.rmtree(story_dir)
                removed.append(story_id)
            except Exception as e:
                print(f"Failed to remove {story_dir}: {e}", file=sys.stderr)

    return removed


def update_top_stories_file(api_base: str, top_stories_path: Path, force_update: bool = False):
    """Update the top-stories.json file with fresh data."""
    if not force_update and top_stories_path.exists():
        # Check if file is recent (less than 1 hour old)
        mtime = datetime.fromtimestamp(top_stories_path.stat().st_mtime, tz=timezone.utc)
        age = datetime.now(timezone.utc) - mtime
        if age.total_seconds() < 3600:  # 1 hour
            print(f"Top stories file is recent ({age.total_seconds():.0f}s old), skipping update")
            return

    try:
        print(f"Updating top stories file: {top_stories_path}")
        resp = requests.get(f"{api_base}/api/top-stories", timeout=30)
        resp.raise_for_status()
        stories = resp.json()

        # Ensure proper format
        if isinstance(stories, list):
            payload = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": f"{api_base}/api/top-stories",
                "data": stories,
            }
        else:
            payload = stories
            if "generated_at" not in payload:
                payload["generated_at"] = datetime.now(timezone.utc).isoformat()

        # Atomic write
        top_stories_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = top_stories_path.with_suffix(top_stories_path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        tmp_path.replace(top_stories_path)

        print(f"Updated top stories file with {len(payload.get('data', []))} stories")

    except Exception as e:
        print(f"Failed to update top stories file: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Cleanup old story directories not in current top stories.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE,
                       help="API base URL (default from HN_API_BASE or http://127.0.0.1:5000)")
    parser.add_argument("--top-stories", default=str(DEFAULT_TOP_STORIES_PATH),
                       help="Path to top-stories.json file")
    parser.add_argument("--stories-dir", default=str(DEFAULT_STORIES_DIR),
                       help="Path to stories directory")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be removed without actually removing")
    parser.add_argument("--update-top-stories", action="store_true",
                       help="Update top-stories.json file before cleanup")
    parser.add_argument("--force-update", action="store_true",
                       help="Force update top-stories.json even if recent")
    args = parser.parse_args()

    api_base = str(args.api_base).rstrip("/")
    top_stories_path = Path(args.top_stories)
    stories_dir = Path(args.stories_dir)

    try:
        # Update top stories file if requested
        if args.update_top_stories:
            update_top_stories_file(api_base, top_stories_path, args.force_update)

        # Get current story IDs
        current_ids = fetch_current_story_ids(api_base, top_stories_path)

        if not current_ids:
            print("No current story IDs found, aborting cleanup", file=sys.stderr)
            sys.exit(1)

        # Perform cleanup
        removed = cleanup_old_stories(stories_dir, current_ids, args.dry_run)

        if args.dry_run:
            print(f"\n[DRY RUN] Would remove {len(removed)} directories")
        else:
            print(f"\nCleanup completed: removed {len(removed)} old story directories")

        # Show summary
        remaining_dirs = find_existing_story_dirs(stories_dir)
        print(f"Current story directories: {len(remaining_dirs)}")
        print(f"Current top stories: {len(current_ids)}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()