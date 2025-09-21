#!/usr/bin/env python3
"""
Content fetcher module for extracting and processing webpage content.
Fetches webpage content, extracts readable text, and prepares it for LLM summarization.
"""

import re
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString


# Default configuration
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_CONTENT_LENGTH = 50000  # Limit content to prevent token overflow
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; HN-Newsletter-Bot/1.0)"
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def extract_readable_content(html: str, base_url: str = "") -> Dict[str, Any]:
    """
    Extract readable content from HTML, focusing on main text content.

    Args:
        html: Raw HTML content
        base_url: Base URL for resolving relative links

    Returns:
        Dict containing extracted content metadata
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
        element.decompose()

    # Extract metadata
    title = ""
    if soup.title:
        title = soup.title.string.strip() if soup.title.string else ""

    # Try to get meta description
    description = ""
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        description = meta_desc['content'].strip()

    # Extract main content (prioritize article, main, or content areas)
    content_selectors = [
        'article',
        'main',
        '[role="main"]',
        '.content',
        '.main-content',
        '.post-content',
        '.entry-content',
        '#content',
        '#main'
    ]

    main_content = None
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break

    # If no main content area found, use body
    if not main_content:
        main_content = soup.body if soup.body else soup

    # Extract text content
    text_content = ""
    if main_content:
        # Get text but preserve some structure
        text_parts = []
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']):
            text = element.get_text(strip=True)
            if text and len(text) > 10:  # Skip very short snippets
                text_parts.append(text)

        text_content = '\n\n'.join(text_parts)

    # Clean up the text
    text_content = clean_text_content(text_content)

    # Truncate if too long
    if len(text_content) > DEFAULT_MAX_CONTENT_LENGTH:
        text_content = text_content[:DEFAULT_MAX_CONTENT_LENGTH] + "\n\n[Content truncated...]"

    return {
        'title': title,
        'description': description,
        'content': text_content,
        'content_length': len(text_content),
        'extracted_at': datetime.now(timezone.utc).isoformat()
    }


def clean_text_content(text: str) -> str:
    """Clean and normalize extracted text content."""
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove common noise patterns
    noise_patterns = [
        r'^\s*Advertisement\s*$',
        r'^\s*ADVERTISEMENT\s*$',
        r'^\s*Skip to main content\s*$',
        r'^\s*Loading\.\.\.\s*$',
        r'^\s*Please enable JavaScript\s*$'
    ]

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            cleaned_lines.append('')
            continue

        # Skip noise patterns
        is_noise = False
        for pattern in noise_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_noise = True
                break

        if not is_noise:
            cleaned_lines.append(line)

    # Remove consecutive empty lines
    result_lines = []
    prev_empty = False
    for line in cleaned_lines:
        if line.strip():
            result_lines.append(line)
            prev_empty = False
        elif not prev_empty:
            result_lines.append('')
            prev_empty = True

    return '\n'.join(result_lines).strip()


def fetch_webpage_content(url: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """
    Fetch webpage content from URL with retry logic and error handling.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Dict containing fetched content and metadata
    """
    if not url or not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL: {url}")

    headers = {
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                raise ValueError(f"Content type not supported: {content_type}")

            # Extract content
            content_data = extract_readable_content(response.text, url)

            # Add fetch metadata
            result = {
                'url': url,
                'final_url': response.url,
                'status_code': response.status_code,
                'content_type': content_type,
                'fetched_at': datetime.now(timezone.utc).isoformat(),
                'success': True,
                **content_data
            }

            return result

        except requests.exceptions.Timeout as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF ** attempt)
                continue

        except requests.exceptions.RequestException as e:
            last_exception = e
            # Don't retry for client errors (4xx)
            if hasattr(e, 'response') and e.response and 400 <= e.response.status_code < 500:
                break
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF ** attempt)
                continue

        except Exception as e:
            last_exception = e
            break

    # Return error result
    return {
        'url': url,
        'success': False,
        'error': str(last_exception),
        'error_type': type(last_exception).__name__,
        'fetched_at': datetime.now(timezone.utc).isoformat()
    }


def validate_url(url: str) -> bool:
    """Validate if URL is properly formatted and accessible."""
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc and parsed.scheme in ('http', 'https'))
    except Exception:
        return False


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python content_fetcher.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    result = fetch_webpage_content(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))