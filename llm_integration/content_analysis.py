#!/usr/bin/env python3
"""
Content analysis module for LLM-based summarization of webpage content.
This module provides the LLM integration layer for content summarization.
"""

import json
from typing import Dict, Any, Optional

from .config import Config
from .ollama_client import OllamaClient


def create_content_analysis_prompt(title: str, content: str, url: str) -> str:
    """
    Create a structured prompt for analyzing webpage content.

    Args:
        title: Page title
        content: Extracted text content
        url: Source URL

    Returns:
        Formatted prompt for LLM analysis
    """
    prompt = f"""Analyze the following webpage content and provide a comprehensive summary in JSON format.

**Source URL:** {url}
**Page Title:** {title}

**Content to analyze:**
{content}

Please analyze this content and return your response as valid JSON with the following structure:

{{
    "executive_summary": "A clear 2-3 sentence overview of the main topic and key message",
    "key_points": [
        "Primary argument or point 1",
        "Primary argument or point 2",
        "Primary argument or point 3",
        "Primary argument or point 4"
    ],
    "topics": [
        "Main topic 1",
        "Main topic 2",
        "Main topic 3"
    ],
    "tone": "Overall tone (e.g., informational, persuasive, technical, opinion, educational)",
    "content_type": "Type of content (e.g., news article, blog post, research paper, documentation, tutorial)",
    "target_audience": "Likely intended audience (e.g., general public, developers, researchers, professionals)",
    "takeaways": [
        "Practical takeaway 1",
        "Practical takeaway 2",
        "Practical takeaway 3"
    ]
}}

Requirements:
- Provide 4-6 key points that capture the main arguments or information
- List 3-5 main topics or themes
- Include 2-4 practical takeaways or conclusions
- Be specific and accurate to the content
- If content is unclear or insufficient, indicate this in the executive summary
- Ensure all text is properly escaped for JSON format

Return only valid JSON, no additional text or formatting."""

    return prompt


def analyze_webpage_content(
    title: str,
    content: str,
    url: str,
    config: Config
) -> Dict[str, Any]:
    """
    Analyze webpage content using LLM and return structured summary.

    Args:
        title: Page title
        content: Extracted webpage content
        url: Source URL
        config: LLM configuration

    Returns:
        Dict containing analysis results and metadata
    """
    try:
        # Validate inputs
        if not content or len(content.strip()) < 50:
            return {
                "success": False,
                "error": "Insufficient content for analysis",
                "content_length": len(content) if content else 0
            }

        # Create the analysis prompt
        prompt = create_content_analysis_prompt(title, content, url)

        # Initialize Ollama client
        client = OllamaClient(host=config.ollama_host)

        # Generate analysis
        response = client.chat(
            model=config.chat_model,
            system="You are a helpful assistant that analyzes webpage content and provides structured summaries in JSON format.",
            user=prompt
        )

        # Parse the JSON response
        analysis_data = parse_llm_response(response)

        # Validate and clean the analysis data
        validated_analysis = validate_analysis_structure(analysis_data)

        return {
            "success": True,
            "analysis": validated_analysis,
            "llm_config": {
                "chat_model": config.chat_model,
                "embed_model": config.embed_model,
                "ollama_host": config.ollama_host
            },
            "content_length": len(content),
            "prompt_length": len(prompt)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "content_length": len(content) if content else 0
        }


def parse_llm_response(response: str) -> Dict[str, Any]:
    """
    Parse LLM response and extract JSON content.

    Args:
        response: Raw LLM response

    Returns:
        Parsed JSON data

    Raises:
        json.JSONDecodeError: If response cannot be parsed as JSON
    """
    response_text = response.strip()

    # Try to extract JSON from markdown code blocks
    if '```json' in response_text:
        json_start = response_text.find('```json') + 7
        json_end = response_text.find('```', json_start)
        if json_end > json_start:
            response_text = response_text[json_start:json_end].strip()
    elif '```' in response_text:
        json_start = response_text.find('```') + 3
        json_end = response_text.find('```', json_start)
        if json_end > json_start:
            response_text = response_text[json_start:json_end].strip()

    # Try to find JSON object boundaries
    if not response_text.startswith('{'):
        json_start = response_text.find('{')
        if json_start >= 0:
            response_text = response_text[json_start:]

    if not response_text.endswith('}'):
        json_end = response_text.rfind('}')
        if json_end >= 0:
            response_text = response_text[:json_end + 1]

    # Parse JSON
    return json.loads(response_text)


def validate_analysis_structure(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean analysis data structure.

    Args:
        analysis_data: Raw analysis data from LLM

    Returns:
        Cleaned and validated analysis data
    """
    validated = {}

    # Required string fields with defaults
    string_fields = {
        'executive_summary': 'Summary not available',
        'tone': 'unknown',
        'content_type': 'unknown',
        'target_audience': 'unknown'
    }

    for field, default in string_fields.items():
        value = analysis_data.get(field, default)
        validated[field] = str(value).strip() if value else default

    # Required list fields with defaults
    list_fields = ['key_points', 'topics', 'takeaways']
    for field in list_fields:
        value = analysis_data.get(field, [])
        if isinstance(value, list):
            # Clean and filter list items
            cleaned_items = []
            for item in value:
                if item and str(item).strip():
                    cleaned_items.append(str(item).strip())
            validated[field] = cleaned_items
        else:
            validated[field] = []

    # Ensure minimum content for lists
    if len(validated['key_points']) == 0:
        validated['key_points'] = ['No key points identified']
    if len(validated['topics']) == 0:
        validated['topics'] = ['No topics identified']
    if len(validated['takeaways']) == 0:
        validated['takeaways'] = ['No takeaways identified']

    return validated


if __name__ == "__main__":
    # Simple test function
    from .config import env_config

    sample_content = """
    This is a sample article about artificial intelligence and its impact on modern society.
    AI technologies are rapidly advancing and transforming various industries.
    Machine learning algorithms are becoming more sophisticated and capable.
    """

    config = env_config()
    result = analyze_webpage_content(
        title="Sample AI Article",
        content=sample_content,
        url="https://example.com/ai-article",
        config=config
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))