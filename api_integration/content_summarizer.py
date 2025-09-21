#!/usr/bin/env python3
"""
Content summarizer module for generating LLM-based summaries of webpage content.
Integrates with the existing LLM infrastructure to provide content analysis.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from llm_integration.config import env_config, override_config
from llm_integration.content_analysis import analyze_webpage_content
from api_integration.content_fetcher import fetch_webpage_content, validate_url


# Legacy function - kept for backward compatibility
def create_content_summary_prompt(title: str, content: str, url: str) -> str:
    """
    Create a prompt for summarizing webpage content.
    This function is deprecated - use llm_integration.content_analysis instead.
    """
    # This is now handled by llm_integration.content_analysis
    return f"Legacy prompt for {title} at {url}"


def summarize_webpage_content(
    url: str,
    content_data: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate an LLM-based summary of webpage content.

    Args:
        url: URL to analyze
        content_data: Pre-fetched content data (optional)
        config: LLM configuration overrides (optional)

    Returns:
        Dict containing summary and metadata
    """
    try:
        # Fetch content if not provided
        if content_data is None:
            if not validate_url(url):
                raise ValueError(f"Invalid URL: {url}")
            content_data = fetch_webpage_content(url)

        # Check if content fetch was successful
        if not content_data.get('success', False):
            return {
                'url': url,
                'success': False,
                'error': f"Failed to fetch content: {content_data.get('error', 'Unknown error')}",
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

        # Extract content components
        title = content_data.get('title', 'Untitled')
        content = content_data.get('content', '')

        if not content or len(content.strip()) < 100:
            return {
                'url': url,
                'success': False,
                'error': 'Insufficient content for summarization',
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

        # Prepare LLM configuration
        base_cfg = env_config()
        if config:
            cfg = override_config(base_cfg, **config)
        else:
            cfg = base_cfg

        # Use the llm_integration module for content analysis
        analysis_result = analyze_webpage_content(title, content, url, cfg)

        if not analysis_result.get('success', False):
            return {
                'url': url,
                'success': False,
                'error': analysis_result.get('error', 'LLM analysis failed'),
                'error_type': analysis_result.get('error_type'),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

        # Extract the analysis data
        summary_data = analysis_result.get('analysis', {})

        # Return complete result
        result = {
            'url': url,
            'final_url': content_data.get('final_url', url),
            'success': True,
            'content_metadata': {
                'title': title,
                'description': content_data.get('description', ''),
                'content_length': content_data.get('content_length', 0),
                'content_type': content_data.get('content_type', ''),
                'fetched_at': content_data.get('fetched_at')
            },
            'summary': summary_data,
            'llm_config': analysis_result.get('llm_config', {}),
            'analysis_metadata': {
                'content_length': analysis_result.get('content_length', 0),
                'prompt_length': analysis_result.get('prompt_length', 0)
            },
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

        return result

    except Exception as e:
        return {
            'url': url,
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }


# validate_summary_structure function moved to llm_integration.content_analysis


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python content_summarizer.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    result = summarize_webpage_content(url)
    print(json.dumps(result, indent=2, ensure_ascii=False))