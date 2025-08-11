# API Integration (Web Scraping Approach)

## Objective

To scrape the Hacker News website to get the top stories from the last 24 hours and expose them through a local API.

## Technical Functionality

*   **Website to scrape:** `https://news.ycombinator.com/`
*   **Libraries:**
    *   `requests` to fetch the HTML content.
    *   `BeautifulSoup4` to parse the HTML.
    *   `Flask` to create a simple API to serve the scraped data.
*   **Data to extract for each story:**
    *   Title
    *   URL
    *   Score (points)
    *   Author
    *   Number of comments
    *   Timestamp of the post

## TODO List

*   [x] Create a Python script `scraper.py` in the `api_integration` directory.
*   [x] Use `requests` to fetch the HTML from `https://news.ycombinator.com/`.
*   [x] Use `BeautifulSoup4` to parse the HTML and extract the story details.
*   [x] Filter the stories to include only those posted within the last 24 hours.
*   [x] Create a simple API using `Flask`.
*   [x] Create a `requirements.txt` file and add `requests`, `beautifulsoup4`, and `flask` to it.
*   [x] Add more robust error handling for network requests and parsing.
    *   [x] Handle `requests.exceptions.RequestException` for network errors.
    *   [x] Handle `AttributeError` and `TypeError` during parsing to gracefully skip stories with unexpected structures.
*   [x] Add logging to the script.
*   [x] Add unit tests for the `parse_age_to_timestamp` function and the scraping logic.
    *   [x] Create a `tests` directory.
    *   [x] Create `test_scraper.py`.
    *   [x] Use a mocking library (like `pytest-mock`) to mock the `requests.get` call and provide a sample HTML file for testing the parsing logic.

## Remaining Tasks

*   **Logging:** The logging is basic. More advanced logging configuration can be added, for example, logging to a file.
