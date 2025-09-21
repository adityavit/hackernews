import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import requests


DEFAULT_API_BASE = os.getenv("HN_API_BASE", "http://127.0.0.1:5000").rstrip("/")
DEFAULT_TOP_STORIES_PATH = Path("ui/api/top-stories.json")
DEFAULT_PARAMS = "max_depth=1&limit=40"
DEFAULT_DELAY = 0.5  # seconds between requests
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def validate_summary_payload(payload, story_id: str):
    """Validate the comment summary payload structure."""
    if not isinstance(payload, dict):
        raise ValueError(f"Summary payload for story {story_id} is not an object")

    required = {"summary", "top_comments"}
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(f"Summary for story {story_id} missing fields: {', '.join(sorted(missing))}")

    # Optional fields: all_comments, config_used
    # Just check they exist if present
    for field in ["all_comments", "config_used"]:
        if field in payload and not isinstance(payload[field], (dict, list, str)):
            raise ValueError(f"Summary for story {story_id} has invalid {field} field")


def atomic_write_json(path: Path, data):
    """Atomically write JSON data to a file via temp file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(path)


def fetch_comment_summary(api_base: str, story_id: str, params: str = DEFAULT_PARAMS, timeout: int = 30):
    """Fetch comment summary for a single story with retry logic."""
    url = f"{api_base}/api/stories/{story_id}/comments/summary"
    if params:
        url += f"?{params}"

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=timeout, headers={"Accept": "application/json"})
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"Timeout fetching summary for story {story_id}, retrying... (attempt {attempt + 1})", file=sys.stderr)
            time.sleep(RETRY_BACKOFF ** attempt)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                if attempt == MAX_RETRIES - 1:
                    raise
                print(f"Server error {e.response.status_code} for story {story_id}, retrying... (attempt {attempt + 1})", file=sys.stderr)
                time.sleep(RETRY_BACKOFF ** attempt)
            else:
                # Client error, don't retry
                raise


def load_story_ids(top_stories_path: Path, api_base: str) -> List[str]:
    """Load story IDs from top-stories.json file or fetch if missing."""
    if not top_stories_path.exists():
        print(f"Top stories file {top_stories_path} not found, fetching from API...", file=sys.stderr)
        # Import and use the existing fetch function
        from fetch_top_stories import fetch_top_stories, validate_stories, atomic_write_json

        stories = fetch_top_stories(api_base)
        validate_stories(stories)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": f"{api_base}/api/top-stories",
            "data": stories,
        }
        atomic_write_json(top_stories_path, payload)
        print(f"Fetched and saved {len(stories)} stories to {top_stories_path}")
        return [story["id"] for story in stories]

    with top_stories_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "data" not in data or not isinstance(data["data"], list):
        raise ValueError(f"Invalid top stories format in {top_stories_path}")

    return [story["id"] for story in data["data"] if "id" in story]


def main():
    parser = argparse.ArgumentParser(description="Dump comment summaries for all top stories.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL (default from HN_API_BASE or http://127.0.0.1:5000)")
    parser.add_argument("--top-stories", default=str(DEFAULT_TOP_STORIES_PATH), help="Path to top-stories.json file")
    parser.add_argument("--force", action="store_true", help="Overwrite existing summary files")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Delay between requests in seconds")
    parser.add_argument("--params", default=DEFAULT_PARAMS, help="Query parameters for summary API")
    parser.add_argument("--ids", help="Comma-separated list of specific story IDs to process")
    parser.add_argument("--limit", type=int, help="Limit number of stories to process")
    args = parser.parse_args()

    api_base = str(args.api_base).rstrip("/")
    top_stories_path = Path(args.top_stories)

    try:
        # Load story IDs
        if args.ids:
            story_ids = [id_.strip() for id_ in args.ids.split(",") if id_.strip()]
        else:
            story_ids = load_story_ids(top_stories_path, api_base)

        if args.limit:
            story_ids = story_ids[:args.limit]

        print(f"Processing {len(story_ids)} stories...")

        success_count = 0
        failure_count = 0
        skipped_count = 0

        for i, story_id in enumerate(story_ids):
            print(f"[{i+1}/{len(story_ids)}] Processing story {story_id}...")

            # Define output path
            output_path = Path(f"ui/api/stories/{story_id}/comments/summary.json")

            # Skip if file exists and not forcing
            if output_path.exists() and not args.force:
                print(f"  Skipping {story_id} (file exists, use --force to overwrite)")
                skipped_count += 1
                continue

            try:
                # Fetch summary
                summary_data = fetch_comment_summary(api_base, story_id, args.params)
                validate_summary_payload(summary_data, story_id)

                # Add metadata
                output_data = {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source": f"{api_base}/api/stories/{story_id}/comments/summary",
                    "story_id": story_id,
                    **summary_data
                }

                # Write file
                atomic_write_json(output_path, output_data)
                print(f"  ✓ Wrote summary for story {story_id}")
                success_count += 1

            except Exception as e:
                print(f"  ✗ Failed to process story {story_id}: {e}", file=sys.stderr)
                failure_count += 1

            # Rate limiting delay
            if i < len(story_ids) - 1 and args.delay > 0:
                time.sleep(args.delay)

        print(f"\nSummary: {success_count} successful, {failure_count} failed, {skipped_count} skipped")

        if failure_count > 0:
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()