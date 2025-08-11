import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup

from api_integration.scraper import parse_age_to_timestamp, scrape_hacker_news

# Sample HTML for testing
SAMPLE_HTML = """
<html>
<body>
  <table>
    <tr class='athing' id='382383'>
      <td class='title'><span class='titleline'><a href='http://example.com/1'>Story 1</a></span></td>
    </tr>
    <tr>
      <td class='subtext'>
        <span class='score' id='score_382383'>100 points</span>
        by <a href='user?id=testuser1' class='hnuser'>testuser1</a>
        <span class='age' title='2023-10-27T10:00:00'><a href='item?id=382383'>2 hours ago</a></span>
        | <a href='item?id=382383'>10 comments</a>
      </td>
    </tr>
    <tr class='athing' id='382384'>
      <td class='title'><span class='titleline'><a href='http://example.com/2'>Story 2</a></span></td>
    </tr>
    <tr>
      <td class='subtext'>
        <span class='score' id='score_382384'>50 points</span>
        by <a href='user?id=testuser2' class='hnuser'>testuser2</a>
        <span class='age' title='2023-10-27T12:00:00'><a href='item?id=382384'>30 minutes ago</a></span>
        | <a href='item?id=382384'>5 comments</a>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def test_parse_age_to_timestamp():
    now = datetime.now()
    assert parse_age_to_timestamp("2 hours ago") is not None
    assert now - parse_age_to_timestamp("2 hours ago") > timedelta(hours=1, minutes=59)
    assert now - parse_age_to_timestamp("30 minutes ago") > timedelta(minutes=29)
    assert parse_age_to_timestamp("1 day ago") is not None
    assert parse_age_to_timestamp("invalid string") is None

@patch('requests.get')
def test_scrape_hacker_news(mock_get):
    # Mock the response from requests.get
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = SAMPLE_HTML
    mock_get.return_value = mock_response

    stories = scrape_hacker_news()

    assert len(stories) == 2

    assert stories[0]['title'] == "Story 1"
    assert stories[0]['url'] == "http://example.com/1"
    assert stories[0]['score'] == 100
    assert stories[0]['user'] == "testuser1"
    assert stories[0]['comments'] == 10

    assert stories[1]['title'] == "Story 2"
    assert stories[1]['url'] == "http://example.com/2"
    assert stories[1]['score'] == 50
    assert stories[1]['user'] == "testuser2"
    assert stories[1]['comments'] == 5
