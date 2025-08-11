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
*   [ ] Add more robust error handling for network requests and parsing.
    *   [ ] Handle `requests.exceptions.RequestException` for network errors.
    *   [ ] Handle `AttributeError` and `TypeError` during parsing to gracefully skip stories with unexpected structures.
*   [ ] Add logging to the script.
*   [ ] Add unit tests for the `parse_age_to_timestamp` function and the scraping logic.
    *   [ ] Create a `tests` directory.
    *   [ ] Create `test_scraper.py`.
    *   [ ] Use a mocking library (like `pytest-mock`) to mock the `requests.get` call and provide a sample HTML file for testing the parsing logic.

## Remaining Tasks

*   **Error Handling:** The current error handling is basic. More specific error handling for different network and parsing errors should be added.
*   **Logging:** There is no logging in the script. Logging should be added to provide better insights into the script's execution and to help with debugging.
*   **Unit Tests:** Unit tests should be added to ensure the correctness of the `parse_age_to_timestamp` function and the scraping logic.