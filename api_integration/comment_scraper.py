import logging
from typing import List, Dict, Optional
import argparse
import json
import os
import sys

import requests
from bs4 import BeautifulSoup

try:
    # When executed as a module: `python -m api_integration.comment_scraper ...`
    from .scraper import parse_age_to_timestamp
except Exception:  # When executed as a script: `python api_integration/comment_scraper.py ...`
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from api_integration.scraper import parse_age_to_timestamp


logger = logging.getLogger(__name__)


HACKER_NEWS_ITEM_URL = "https://news.ycombinator.com/item?id={story_id}"


def _extract_comment_depth(comment_row) -> int:
    """
    Hacker News encodes depth via an image width inside the indentation cell.
    Each level is typically 40px.
    """
    try:
        indent_cell = comment_row.find("td", class_="ind")
        if not indent_cell:
            return 0
        img = indent_cell.find("img")
        if not img:
            return 0
        width_str = img.get("width", "0")
        width_val = int(width_str)
        return width_val // 40
    except Exception:
        return 0


def _extract_parent_id(comment_row) -> Optional[str]:
    try:
        # Look for an anchor with text 'parent'
        parent_link = comment_row.find("a", string=lambda s: s and s.strip().lower() == "parent")
        if parent_link and parent_link.has_attr("href"):
            href = parent_link["href"]
            # href looks like 'item?id=40767890'
            if "item?id=" in href:
                return href.split("item?id=")[-1]
        return None
    except Exception:
        return None


def _extract_comment_fields(comment_row) -> Optional[Dict]:
    try:
        comment_id = comment_row.get("id")

        # Author
        user_element = comment_row.find("a", class_="hnuser")
        author = user_element.text.strip() if user_element else None

        # Age
        age_element = comment_row.find("span", class_="age")
        age_string = age_element.text.strip() if age_element else None
        timestamp = parse_age_to_timestamp(age_string) if age_string else None

        # Comment text
        # Comment text can be inside span or div with class 'commtext' and may have multiple classes
        text_element = comment_row.select_one(".commtext")
        if text_element:
            # Normalize whitespace and extract visible text
            text = text_element.get_text(" ", strip=True)
            if text == "":
                text = None
        else:
            # Deleted or dead comment
            text = None

        parent_id = _extract_parent_id(comment_row)
        depth = _extract_comment_depth(comment_row)

        return {
            "id": comment_id,
            "author": author,
            "age": age_string,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "text": text,
            "parent_id": parent_id,
            "depth": depth,
        }
    except Exception as exc:
        logger.warning("Failed to parse comment row: %s", exc)
        return None


def fetch_story_comments(
    story_id: str,
    *,
    max_depth: Optional[int] = 2,
    limit: Optional[int] = None,
    timeout_seconds: int = 10,
) -> List[Dict]:
    """
    Fetch and parse comments for a Hacker News story by scraping the item page.

    Args:
        story_id: Hacker News story id as a string.
        max_depth: If provided, only include comments with depth <= max_depth.
        limit: If provided, cap the number of comments returned.
        timeout_seconds: Network timeout for the request.

    Returns:
        List of comment dictionaries.
    """
    url = HACKER_NEWS_ITEM_URL.format(story_id=story_id)
    logger.info("Fetching comments for story %s", story_id)

    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error("Error fetching story page: %s", exc)
        return []

    soup = BeautifulSoup(response.content, "html.parser")

    comment_rows = soup.find_all("tr", class_="athing comtr")
    comments: List[Dict] = []

    for row in comment_rows:
        parsed = _extract_comment_fields(row)
        if not parsed:
            continue

        if max_depth is not None and parsed.get("depth", 0) > max_depth:
            continue

        comments.append(parsed)

        if limit is not None and len(comments) >= limit:
            break

    logger.info("Parsed %d comments for story %s", len(comments), story_id)
    return comments


def fetch_story_details(story_id: str, timeout_seconds: int = 10) -> Dict:
    """
    Fetch story details (title, url, score, user, age, timestamp) from the item page.
    """
    url = HACKER_NEWS_ITEM_URL.format(story_id=story_id)
    logger.info("Fetching story details for %s", story_id)

    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error("Error fetching story page for details: %s", exc)
        return {"id": story_id, "title": None, "url": None, "score": 0, "user": None, "age": None, "timestamp": None}

    soup = BeautifulSoup(response.content, "html.parser")

    try:
        titleline = soup.find("span", class_="titleline")
        a = titleline.find("a") if titleline else None
        title = a.text if a else None
        target_url = a["href"] if a and a.has_attr("href") else None

        # Find subtext associated with the story header
        subtext = soup.find("td", class_="subtext")

        score_element = subtext.find("span", class_="score") if subtext else None
        score = int(score_element.text.split()[0]) if score_element else 0

        user_element = subtext.find("a", class_="hnuser") if subtext else None
        user = user_element.text if user_element else None

        age_element = subtext.find("span", class_="age") if subtext else None
        age_string = age_element.text if age_element else None
        timestamp = parse_age_to_timestamp(age_string) if age_string else None

        return {
            "id": story_id,
            "title": title,
            "url": target_url,
            "score": score,
            "user": user,
            "age": age_string,
            "timestamp": timestamp.isoformat() if timestamp else None,
        }
    except Exception as exc:
        logger.warning("Failed to parse story details: %s", exc)
        return {"id": story_id, "title": None, "url": None, "score": 0, "user": None, "age": None, "timestamp": None}


def main():
    parser = argparse.ArgumentParser(description="Scrape Hacker News comments and story details for a given story id.")
    parser.add_argument("story_id", help="Hacker News story id (e.g., 12345678)")
    parser.add_argument("--max-depth", type=int, default=2, dest="max_depth", help="Maximum comment depth to include (default: 2)")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of comments returned")
    parser.add_argument("-o", "--output", help="Output file path (JSON). If omitted, prints to stdout.")
    parser.add_argument("--no-pretty", action="store_true", help="Output minified JSON (no pretty print)")

    args = parser.parse_args()

    story = fetch_story_details(args.story_id)
    comments = fetch_story_comments(args.story_id, max_depth=args.max_depth, limit=args.limit)

    payload = {"story": story, "comments": comments}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=None if args.no_pretty else 2, ensure_ascii=False)
    else:
        print(json.dumps(payload, indent=None if args.no_pretty else 2, ensure_ascii=False))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()

