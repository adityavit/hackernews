import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


DEFAULT_API_BASE = os.getenv("HN_API_BASE", "http://127.0.0.1:5000").rstrip("/")
DEFAULT_OUTPUT = Path("ui/api/top-stories.json")


def validate_stories(payload):
    if not isinstance(payload, list):
        raise ValueError("Payload is not a list")
    required = {"id", "title", "url", "score", "user", "comments"}
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Story at index {idx} is not an object")
        missing = required - set(item.keys())
        if missing:
            raise ValueError(f"Story {item.get('id', idx)} missing fields: {', '.join(sorted(missing))}")


def atomic_write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(path)


def fetch_top_stories(api_base: str, timeout: int = 20):
    url = f"{api_base}/api/top-stories"
    resp = requests.get(url, timeout=timeout, headers={"Accept": "application/json"})
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Fetch top stories and store JSON for UI consumption.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL (default from HN_API_BASE or http://127.0.0.1:5000)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path (default ui/api/top-stories.json)")
    args = parser.parse_args()

    api_base = str(args.api_base).rstrip("/")
    output_path = Path(args.output)

    try:
        stories = fetch_top_stories(api_base)
        validate_stories(stories)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": f"{api_base}/api/top-stories",
            "data": stories,
        }
        atomic_write_json(output_path, payload)
        print(f"Wrote {len(stories)} stories to {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"HTTP error fetching top stories: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


