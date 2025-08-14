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

## Next Tasks

1.  Fetch comments for each story
    - For each story in the top list, request the story discussion page on Hacker News (e.g., `https://news.ycombinator.com/item?id=<story_id>`).
    - Parse the comments tree and extract for each comment:
      - Comment id, author (hnuser), age/time, text (HTML converted to plain text), parent id (if needed for threading), and top-level vs nested info.
    - Consider pagination/hidden comments and depth; start with top N comments or a reasonable depth (e.g., depth <= 2) to keep runtime manageable.
    - Add a new API route to return comments per story id (e.g., `GET /api/stories/<id>/comments`).
    - Add unit tests with fixture HTML for a story page to validate parsing.

2.  Summarize comments using LLMs
    - Use an LLM to generate a short summary of the main discussion points for each story based on the fetched comments.
    - Implementation notes:
      - Add a provider-agnostic interface (e.g., environment-driven) so we can swap providers (OpenAI, Anthropic, local) without code changes.
      - Chunk and cap comments input to stay within token limits; prioritize top-level comments by score/time or length.
      - Prompt suggestions: ask for 3-5 bullet points capturing consensus, disagreements, notable insights, and caveats.
      - Add a new API route (e.g., `GET /api/stories/<id>/summary`) that returns a cached summary for the story; compute on-demand if missing.
      - Cache summaries (in-memory dict initially) keyed by story id with a TTL to avoid repeated calls.
    - Add unit tests to validate the controller flow with the LLM client mocked.

## TODO (Next Tasks)

### 1) Fetch comments for each story
- [x] Define API contract for comments: `GET /api/stories/<id>/comments`
- [x] Fetch story page HTML: `https://news.ycombinator.com/item?id=<story_id>`
- [x] Parse comments tree: id, author, age, text (plain), parent id, depth
- [x] Implement depth/size limits (e.g., top N or depth <= 2)
- [x] Normalize text (strip tags, decode entities, handle links/code)
- [x] Return JSON schema and include minimal metadata
- [x] Add error handling, network timeouts, retries/backoff
- [x] Unit tests with fixture HTML for various edge cases (deleted, dead, collapsed)
- [ ] Performance pass (avoid N+1 network calls where possible)

### 2) Summarize comments using LLMs
- [ ] Create provider-agnostic LLM client interface
- [ ] Add environment-driven config (API keys, model names, timeouts)
- [ ] Design summarization prompt (bullet points, consensus, disagreements, insights)
- [ ] Implement input selection/chunking for comments (token budget aware)
- [ ] Implement caching with TTL keyed by story id
- [ ] Add API route: `GET /api/stories/<id>/summary` (on-demand compute + cache)
- [ ] Unit tests with mocked LLM client (success, failure, cache hit)
- [ ] Handle provider errors, rate limits, and fallbacks gracefully
