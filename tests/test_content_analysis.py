import pytest
import json
from unittest.mock import patch, Mock
from pathlib import Path

from llm_integration.content_analysis import (
    analyze_webpage_content,
    create_content_analysis_prompt,
    parse_llm_response,
    validate_analysis_structure
)
from llm_integration.config import Config
from api_integration.content_fetcher import extract_readable_content


class TestContentAnalysis:
    """Test suite for LLM content analysis functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return Config(
            ollama_host="http://localhost:11434",
            chat_model="test-model",
            embed_model="test-embed-model",
            topk=10,
            max_summary_comments=40,
            weights=(0.4, 0.4, 0.2)
        )

    @pytest.fixture
    def sample_article_html(self):
        """Load sample article HTML fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_article.html"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def sample_blog_html(self):
        """Load sample blog post HTML fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_blog_post.html"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return f.read()

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response in JSON format."""
        return """```json
{
    "executive_summary": "This article provides a comprehensive overview of artificial intelligence, covering its definition, key components, industry applications, challenges, and future prospects.",
    "key_points": [
        "AI simulates human intelligence in machines that can think and learn",
        "Key components include machine learning, neural networks, NLP, and computer vision",
        "Applications span healthcare, finance, and transportation with remarkable results",
        "Challenges include transparency, bias, job displacement, and ethical considerations",
        "Future trends include AGI development and improved human-AI collaboration"
    ],
    "topics": [
        "Artificial Intelligence",
        "Machine Learning",
        "Industry Applications",
        "AI Ethics",
        "Future Technology"
    ],
    "tone": "informational",
    "content_type": "educational article",
    "target_audience": "general public and technology professionals",
    "takeaways": [
        "AI is transforming multiple industries with significant benefits",
        "Careful consideration of ethical implications is crucial for AI development",
        "Success in AI requires both technical expertise and wisdom in application"
    ]
}
```"""

    def test_create_content_analysis_prompt(self):
        """Test that content analysis prompt is properly formatted."""
        title = "Test Article"
        content = "This is test content about AI and technology."
        url = "https://example.com/test"

        prompt = create_content_analysis_prompt(title, content, url)

        assert title in prompt
        assert content in prompt
        assert url in prompt
        assert "executive_summary" in prompt
        assert "key_points" in prompt
        assert "JSON" in prompt

    def test_parse_llm_response_json_markdown(self, mock_llm_response):
        """Test parsing LLM response with JSON markdown blocks."""
        result = parse_llm_response(mock_llm_response)

        assert isinstance(result, dict)
        assert "executive_summary" in result
        assert "key_points" in result
        assert isinstance(result["key_points"], list)
        assert len(result["key_points"]) == 5

    def test_parse_llm_response_plain_json(self):
        """Test parsing plain JSON response."""
        json_response = {
            "executive_summary": "Test summary",
            "key_points": ["Point 1", "Point 2"],
            "topics": ["Topic 1"],
            "tone": "informational",
            "content_type": "article",
            "target_audience": "general",
            "takeaways": ["Takeaway 1"]
        }

        result = parse_llm_response(json.dumps(json_response))
        assert result == json_response

    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON response raises appropriate error."""
        invalid_response = "This is not valid JSON at all"

        with pytest.raises(json.JSONDecodeError):
            parse_llm_response(invalid_response)

    def test_validate_analysis_structure_complete(self):
        """Test validation with complete analysis data."""
        analysis_data = {
            "executive_summary": "Complete summary",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "topics": ["Topic A", "Topic B"],
            "tone": "informational",
            "content_type": "article",
            "target_audience": "professionals",
            "takeaways": ["Takeaway 1", "Takeaway 2"]
        }

        result = validate_analysis_structure(analysis_data)

        assert result["executive_summary"] == "Complete summary"
        assert len(result["key_points"]) == 3
        assert len(result["topics"]) == 2
        assert result["tone"] == "informational"

    def test_validate_analysis_structure_missing_fields(self):
        """Test validation with missing fields provides defaults."""
        analysis_data = {
            "executive_summary": "Summary only"
        }

        result = validate_analysis_structure(analysis_data)

        assert result["executive_summary"] == "Summary only"
        assert result["tone"] == "unknown"
        assert result["content_type"] == "unknown"
        assert result["target_audience"] == "unknown"
        assert result["key_points"] == ["No key points identified"]
        assert result["topics"] == ["No topics identified"]
        assert result["takeaways"] == ["No takeaways identified"]

    def test_validate_analysis_structure_empty_lists(self):
        """Test validation with empty lists provides defaults."""
        analysis_data = {
            "executive_summary": "Test summary",
            "key_points": [],
            "topics": [],
            "takeaways": [],
            "tone": "neutral",
            "content_type": "blog",
            "target_audience": "developers"
        }

        result = validate_analysis_structure(analysis_data)

        assert result["key_points"] == ["No key points identified"]
        assert result["topics"] == ["No topics identified"]
        assert result["takeaways"] == ["No takeaways identified"]

    @patch('llm_integration.content_analysis.OllamaClient')
    def test_analyze_webpage_content_success(self, mock_ollama_client, mock_config, mock_llm_response):
        """Test successful webpage content analysis."""
        # Setup mock
        mock_client_instance = Mock()
        mock_client_instance.chat.return_value = mock_llm_response
        mock_ollama_client.return_value = mock_client_instance

        title = "Test Article"
        content = "This is a test article about artificial intelligence and machine learning."
        url = "https://example.com/test"

        result = analyze_webpage_content(title, content, url, mock_config)

        assert result["success"] is True
        assert "analysis" in result
        assert "llm_config" in result
        assert result["content_length"] == len(content)

        analysis = result["analysis"]
        assert "executive_summary" in analysis
        assert "key_points" in analysis
        assert isinstance(analysis["key_points"], list)

    @patch('llm_integration.content_analysis.OllamaClient')
    def test_analyze_webpage_content_insufficient_content(self, mock_ollama_client, mock_config):
        """Test analysis with insufficient content."""
        title = "Short"
        content = "Too short"  # Less than 50 characters
        url = "https://example.com/test"

        result = analyze_webpage_content(title, content, url, mock_config)

        assert result["success"] is False
        assert "error" in result
        assert "Insufficient content" in result["error"]

    @patch('llm_integration.content_analysis.OllamaClient')
    def test_analyze_webpage_content_llm_error(self, mock_ollama_client, mock_config):
        """Test analysis when LLM client raises an error."""
        # Setup mock to raise exception
        mock_client_instance = Mock()
        mock_client_instance.chat.side_effect = Exception("LLM connection failed")
        mock_ollama_client.return_value = mock_client_instance

        title = "Test Article"
        content = "This is a test article with sufficient content length for analysis."
        url = "https://example.com/test"

        result = analyze_webpage_content(title, content, url, mock_config)

        assert result["success"] is False
        assert "error" in result
        assert "LLM connection failed" in result["error"]

    def test_analyze_webpage_content_with_fixture_article(self, sample_article_html, mock_config):
        """Test content analysis with actual HTML fixture."""
        # Extract content from HTML fixture
        extracted = extract_readable_content(sample_article_html, "https://example.com")

        title = extracted["title"]
        content = extracted["content"]
        url = "https://example.com/ai-guide"

        # Mock the LLM response
        with patch('llm_integration.content_analysis.OllamaClient') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = """
            {
                "executive_summary": "A comprehensive guide explaining artificial intelligence concepts and applications",
                "key_points": [
                    "AI simulates human intelligence in machines",
                    "Key components include ML, neural networks, NLP, and computer vision",
                    "Applications span healthcare, finance, and transportation",
                    "Challenges include transparency, bias, and ethical considerations"
                ],
                "topics": ["Artificial Intelligence", "Machine Learning", "Technology Applications"],
                "tone": "educational",
                "content_type": "technical guide",
                "target_audience": "technology professionals and general public",
                "takeaways": [
                    "AI is transforming multiple industries",
                    "Ethical considerations are crucial for AI development"
                ]
            }
            """
            mock_ollama.return_value = mock_client

            result = analyze_webpage_content(title, content, url, mock_config)

            assert result["success"] is True
            assert "Understanding Artificial Intelligence" in title
            assert len(content) > 1000  # Should have substantial content
            assert "artificial intelligence" in content.lower()

    def test_analyze_webpage_content_with_fixture_blog(self, sample_blog_html, mock_config):
        """Test content analysis with blog post fixture."""
        # Extract content from HTML fixture
        extracted = extract_readable_content(sample_blog_html, "https://example.com")

        title = extracted["title"]
        content = extracted["content"]
        url = "https://example.com/python-data-science"

        # Mock the LLM response
        with patch('llm_integration.content_analysis.OllamaClient') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = """
            {
                "executive_summary": "An analysis of why Python remains the preferred language for data science work",
                "key_points": [
                    "Python has clean and intuitive syntax",
                    "Rich ecosystem of data science libraries",
                    "Large and active community support",
                    "Strong industry adoption by major tech companies"
                ],
                "topics": ["Python Programming", "Data Science", "Programming Languages"],
                "tone": "persuasive",
                "content_type": "blog post",
                "target_audience": "data scientists and programmers",
                "takeaways": [
                    "Python's simplicity and ecosystem make it ideal for data science",
                    "Community support and industry adoption create positive feedback loops"
                ]
            }
            """
            mock_ollama.return_value = mock_client

            result = analyze_webpage_content(title, content, url, mock_config)

            assert result["success"] is True
            assert "Python" in title
            assert "data science" in content.lower()
            assert "numpy" in content.lower()  # Should extract library mentions