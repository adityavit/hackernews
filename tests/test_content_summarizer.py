import pytest
import json
from unittest.mock import patch, Mock
from pathlib import Path

from api_integration.content_summarizer import summarize_webpage_content
from api_integration.content_fetcher import fetch_webpage_content, extract_readable_content


class TestContentSummarizer:
    """Test suite for API content summarizer functionality."""

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
    def mock_successful_content_data(self):
        """Mock successful content fetch data."""
        return {
            'url': 'https://example.com/test',
            'final_url': 'https://example.com/test',
            'status_code': 200,
            'content_type': 'text/html',
            'success': True,
            'title': 'Test Article Title',
            'description': 'Test article description',
            'content': 'This is a comprehensive test article about artificial intelligence and machine learning technologies. It covers various aspects of AI development, implementation, and future prospects.',
            'content_length': 150,
            'extracted_at': '2025-01-01T12:00:00Z',
            'fetched_at': '2025-01-01T12:00:00Z'
        }

    @pytest.fixture
    def mock_llm_analysis_result(self):
        """Mock successful LLM analysis result."""
        return {
            'success': True,
            'analysis': {
                'executive_summary': 'A comprehensive overview of artificial intelligence technologies and their impact',
                'key_points': [
                    'AI is transforming multiple industries',
                    'Machine learning is a core component of modern AI',
                    'Ethical considerations are important for AI development',
                    'Future prospects include AGI and improved automation'
                ],
                'topics': ['Artificial Intelligence', 'Machine Learning', 'Technology', 'Ethics'],
                'tone': 'informational',
                'content_type': 'technical article',
                'target_audience': 'technology professionals',
                'takeaways': [
                    'AI requires careful ethical consideration',
                    'The technology is rapidly evolving across industries'
                ]
            },
            'llm_config': {
                'chat_model': 'test-model',
                'embed_model': 'test-embed',
                'ollama_host': 'http://localhost:11434'
            },
            'content_length': 150,
            'prompt_length': 500
        }

    def test_summarize_webpage_content_with_valid_url(self, mock_successful_content_data, mock_llm_analysis_result):
        """Test successful content summarization with valid URL."""
        url = "https://example.com/test-article"

        with patch('api_integration.content_summarizer.fetch_webpage_content') as mock_fetch, \
             patch('api_integration.content_summarizer.analyze_webpage_content') as mock_analyze:

            mock_fetch.return_value = mock_successful_content_data
            mock_analyze.return_value = mock_llm_analysis_result

            result = summarize_webpage_content(url)

            assert result['success'] is True
            assert result['url'] == url
            assert 'summary' in result
            assert 'content_metadata' in result
            assert 'llm_config' in result
            assert 'analysis_metadata' in result

            # Verify summary structure
            summary = result['summary']
            assert 'executive_summary' in summary
            assert 'key_points' in summary
            assert isinstance(summary['key_points'], list)
            assert len(summary['key_points']) == 4

    def test_summarize_webpage_content_with_invalid_url(self):
        """Test content summarization with invalid URL."""
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com",
            None
        ]

        for url in invalid_urls:
            with patch('api_integration.content_summarizer.validate_url') as mock_validate:
                mock_validate.return_value = False

                result = summarize_webpage_content(url)

                assert result['success'] is False
                assert 'error' in result
                assert 'Invalid URL' in result['error']

    def test_summarize_webpage_content_fetch_failure(self):
        """Test content summarization when webpage fetch fails."""
        url = "https://example.com/test-article"
        failed_content_data = {
            'url': url,
            'success': False,
            'error': 'Connection timeout',
            'error_type': 'TimeoutError'
        }

        with patch('api_integration.content_summarizer.fetch_webpage_content') as mock_fetch:
            mock_fetch.return_value = failed_content_data

            result = summarize_webpage_content(url)

            assert result['success'] is False
            assert 'error' in result
            assert 'Failed to fetch content' in result['error']

    def test_summarize_webpage_content_insufficient_content(self, mock_successful_content_data):
        """Test content summarization with insufficient content."""
        url = "https://example.com/short-article"

        # Create content data with very short content
        short_content_data = mock_successful_content_data.copy()
        short_content_data['content'] = "Short"  # Less than 100 characters

        with patch('api_integration.content_summarizer.fetch_webpage_content') as mock_fetch:
            mock_fetch.return_value = short_content_data

            result = summarize_webpage_content(url)

            assert result['success'] is False
            assert 'error' in result
            assert 'Insufficient content' in result['error']

    def test_summarize_webpage_content_llm_analysis_failure(self, mock_successful_content_data):
        """Test content summarization when LLM analysis fails."""
        url = "https://example.com/test-article"
        failed_analysis_result = {
            'success': False,
            'error': 'LLM connection failed',
            'error_type': 'ConnectionError'
        }

        with patch('api_integration.content_summarizer.fetch_webpage_content') as mock_fetch, \
             patch('api_integration.content_summarizer.analyze_webpage_content') as mock_analyze:

            mock_fetch.return_value = mock_successful_content_data
            mock_analyze.return_value = failed_analysis_result

            result = summarize_webpage_content(url)

            assert result['success'] is False
            assert 'error' in result
            assert 'LLM connection failed' in result['error']

    def test_summarize_webpage_content_with_config_overrides(self, mock_successful_content_data, mock_llm_analysis_result):
        """Test content summarization with LLM configuration overrides."""
        url = "https://example.com/test-article"
        config_overrides = {
            'chat_model': 'custom-model',
            'ollama_host': 'http://custom-host:11434'
        }

        with patch('api_integration.content_summarizer.fetch_webpage_content') as mock_fetch, \
             patch('api_integration.content_summarizer.analyze_webpage_content') as mock_analyze, \
             patch('api_integration.content_summarizer.env_config') as mock_env_config, \
             patch('api_integration.content_summarizer.override_config') as mock_override:

            mock_fetch.return_value = mock_successful_content_data
            mock_analyze.return_value = mock_llm_analysis_result
            mock_env_config.return_value = Mock()
            mock_override.return_value = Mock()

            result = summarize_webpage_content(url, config=config_overrides)

            assert result['success'] is True
            mock_override.assert_called_once()

    def test_summarize_webpage_content_with_provided_content_data(self, mock_successful_content_data, mock_llm_analysis_result):
        """Test content summarization with pre-fetched content data."""
        url = "https://example.com/test-article"

        with patch('api_integration.content_summarizer.analyze_webpage_content') as mock_analyze:
            mock_analyze.return_value = mock_llm_analysis_result

            result = summarize_webpage_content(url, content_data=mock_successful_content_data)

            assert result['success'] is True
            # Should not call fetch_webpage_content since content_data is provided
            mock_analyze.assert_called_once()

    def test_summarize_webpage_content_with_html_fixture_article(self, sample_article_html):
        """Test content summarization using actual HTML fixture - AI article."""
        url = "https://example.com/ai-article"

        # Extract real content from fixture
        extracted_content = extract_readable_content(sample_article_html, url)
        content_data = {
            'url': url,
            'final_url': url,
            'status_code': 200,
            'content_type': 'text/html',
            'success': True,
            'title': extracted_content['title'],
            'description': extracted_content['description'],
            'content': extracted_content['content'],
            'content_length': extracted_content['content_length'],
            'extracted_at': extracted_content['extracted_at'],
            'fetched_at': '2025-01-01T12:00:00Z'
        }

        # Mock the LLM analysis
        mock_analysis_result = {
            'success': True,
            'analysis': {
                'executive_summary': 'A comprehensive guide to artificial intelligence covering definitions, components, applications, and future prospects',
                'key_points': [
                    'AI simulates human intelligence in machines for thinking and learning',
                    'Key components include machine learning, neural networks, NLP, and computer vision',
                    'Applications span healthcare diagnostics, financial fraud detection, and autonomous vehicles',
                    'Challenges include ensuring transparency, addressing bias, and managing job displacement',
                    'Future developments focus on AGI and improved human-AI collaboration'
                ],
                'topics': ['Artificial Intelligence', 'Machine Learning', 'Healthcare Technology', 'Autonomous Systems', 'AI Ethics'],
                'tone': 'educational',
                'content_type': 'comprehensive guide',
                'target_audience': 'technology professionals and general public',
                'takeaways': [
                    'AI development requires balancing technical advancement with ethical considerations',
                    'Success in AI requires both technical expertise and wisdom in application',
                    'AI will continue evolving but must be developed thoughtfully'
                ]
            },
            'llm_config': {
                'chat_model': 'test-model',
                'embed_model': 'test-embed',
                'ollama_host': 'http://localhost:11434'
            },
            'content_length': len(extracted_content['content']),
            'prompt_length': 1000
        }

        with patch('api_integration.content_summarizer.analyze_webpage_content') as mock_analyze:
            mock_analyze.return_value = mock_analysis_result

            result = summarize_webpage_content(url, content_data=content_data)

            assert result['success'] is True
            assert 'Understanding Artificial Intelligence' in result['content_metadata']['title']
            assert 'artificial intelligence' in result['content_metadata']['description'].lower()
            assert len(result['summary']['key_points']) == 5
            assert 'artificial intelligence' in result['summary']['executive_summary'].lower()

    def test_summarize_webpage_content_with_html_fixture_blog(self, sample_blog_html):
        """Test content summarization using actual HTML fixture - Python blog post."""
        url = "https://example.com/python-blog"

        # Extract real content from fixture
        extracted_content = extract_readable_content(sample_blog_html, url)
        content_data = {
            'url': url,
            'final_url': url,
            'status_code': 200,
            'content_type': 'text/html',
            'success': True,
            'title': extracted_content['title'],
            'description': extracted_content['description'],
            'content': extracted_content['content'],
            'content_length': extracted_content['content_length'],
            'extracted_at': extracted_content['extracted_at'],
            'fetched_at': '2025-01-01T12:00:00Z'
        }

        # Mock the LLM analysis
        mock_analysis_result = {
            'success': True,
            'analysis': {
                'executive_summary': 'An analysis of why Python continues to be the preferred programming language for data science despite growing competition',
                'key_points': [
                    'Python offers clean and intuitive syntax that focuses on problem-solving over complex code',
                    'Rich ecosystem includes NumPy, Pandas, Matplotlib, Scikit-learn, and deep learning libraries',
                    'Large active community provides extensive documentation and learning resources',
                    'Major tech companies like Google, Netflix, and Spotify drive industry adoption',
                    'Seamless integration with databases, APIs, and cloud platforms'
                ],
                'topics': ['Python Programming', 'Data Science', 'Programming Languages', 'Software Development'],
                'tone': 'persuasive',
                'content_type': 'opinion blog post',
                'target_audience': 'data scientists and software developers',
                'takeaways': [
                    'Python\'s combination of simplicity and powerful ecosystem makes it ideal for data science',
                    'Community support and industry adoption create positive feedback loops for continued development'
                ]
            },
            'llm_config': {
                'chat_model': 'test-model',
                'embed_model': 'test-embed',
                'ollama_host': 'http://localhost:11434'
            },
            'content_length': len(extracted_content['content']),
            'prompt_length': 800
        }

        with patch('api_integration.content_summarizer.analyze_webpage_content') as mock_analyze:
            mock_analyze.return_value = mock_analysis_result

            result = summarize_webpage_content(url, content_data=content_data)

            assert result['success'] is True
            assert 'Python' in result['content_metadata']['title']
            assert 'data science' in result['content_metadata']['description'].lower()
            assert len(result['summary']['topics']) == 4
            assert 'Python' in result['summary']['executive_summary']

    def test_content_metadata_structure(self, mock_successful_content_data, mock_llm_analysis_result):
        """Test that content metadata is properly structured in the response."""
        url = "https://example.com/test"

        with patch('api_integration.content_summarizer.fetch_webpage_content') as mock_fetch, \
             patch('api_integration.content_summarizer.analyze_webpage_content') as mock_analyze:

            mock_fetch.return_value = mock_successful_content_data
            mock_analyze.return_value = mock_llm_analysis_result

            result = summarize_webpage_content(url)

            assert result['success'] is True

            # Verify content metadata structure
            metadata = result['content_metadata']
            assert 'title' in metadata
            assert 'description' in metadata
            assert 'content_length' in metadata
            assert 'content_type' in metadata
            assert 'fetched_at' in metadata

            # Verify analysis metadata structure
            analysis_metadata = result['analysis_metadata']
            assert 'content_length' in analysis_metadata
            assert 'prompt_length' in analysis_metadata

    def test_exception_handling(self):
        """Test that unexpected exceptions are properly handled."""
        url = "https://example.com/test"

        with patch('api_integration.content_summarizer.fetch_webpage_content') as mock_fetch:
            mock_fetch.side_effect = Exception("Unexpected error")

            result = summarize_webpage_content(url)

            assert result['success'] is False
            assert 'error' in result
            assert 'error_type' in result
            assert result['error_type'] == 'Exception'