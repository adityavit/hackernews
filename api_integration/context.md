# API Integration (Web Scraping Approach)

## Objective

To scrape the Hacker News website to get the top stories from the last 24 hours and expose them through a local API.

## Technical Functionality

*   **Website to scrape:** `https://news.ycombinator.com/`
*   **Libraries:**
    *   `requests` to fetch the HTML content.
    *   `BeautifulSoup4` to parse the HTML.
    *   `Flask` or `FastAPI` to create a simple API to serve the scraped data.
*   **Data to extract for each story:**
    *   Title
    *   URL
    *   Score (points)
    *   Author
    *   Number of comments
    *   Timestamp of the post

## TODO List

*   [ ] Create a Python script `scraper.py` in the `api_integration` directory.
*   [ ] Use `requests` to fetch the HTML from `https://news.ycombinator.com/`.
*   [ ] Use `BeautifulSoup4` to parse the HTML and extract the story details.
    *   Identify the HTML tags and classes that contain the story information.
    *   Handle cases where some information might be missing (e.g., no URL for "Ask HN" posts).
*   [ ] Filter the stories to include only those posted within the last 24 hours.
    *   The "age" of the post is given in relative terms (e.g., "2 hours ago"). This needs to be parsed and converted to an absolute timestamp.
*   [ ] Create a simple API using `Flask` or `FastAPI`.
    *   The API should have an endpoint like `/api/top-stories`.
    *   This endpoint should return the list of scraped and filtered stories in JSON format.
*   [ ] Add error handling for network requests and parsing.
*   [ ] Add logging to the script.
*   [ ] Create a `requirements.txt` file and add `requests`, `beautifulsoup4`, and `flask` (or `fastapi`) to it.