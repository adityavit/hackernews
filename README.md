# Hacker News Letter

A project to create a daily newsletter of the top posts from Hacker News.

## Features

*   Fetch the top posts from Hacker News from the last 24 hours.
*   Filter and rank posts based on popularity (score, comments) and importance.
*   Generate a static HTML webpage for the newsletter.
*   Create a mailing list of the top posts.
*   Email the newsletter daily.

## Project Plan

### Phase 1: Core Functionality

1.  **Hacker News API Integration:**
    *   Fetch top story IDs from the Hacker News API.
    *   For each story, fetch its details (title, URL, score, author, number of comments).
2.  **Post Filtering and Ranking:**
    *   Implement a scoring algorithm to rank stories based on a combination of votes and comments.
    *   Filter stories to include only those from the last 24 hours.
    *   Select the top N stories for the newsletter.
3.  **HTML Newsletter Generation:**
    *   Create a simple, clean HTML template for the newsletter.
    *   Populate the template with the ranked stories.
    *   Save the generated newsletter as an HTML file.

### Phase 2: Automation and Delivery

1.  **Web Page for the Newsletter:**
    *   Serve the generated HTML file using a simple web server.
2.  **Emailing:**
    *   Integrate with an email service provider (e.g., SendGrid, Mailgun).
    *   Create a script to send the HTML newsletter to a predefined list of recipients.
3.  **Automation:**
    *   Set up a daily cron job or a scheduler (like GitHub Actions) to run the entire process automatically.

## Technology Stack (Proposed)

*   **Backend:** Python
    *   `requests` for making API calls.
    *   `Jinja2` for HTML templating.
*   **Frontend:** HTML & CSS for the newsletter template.
*   **Automation:** GitHub Actions or a system cron job.

## How to Run

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    ```

2.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Start the Flask server (API):**
    ```bash
    python api_integration/api.py
    ```
    The server will be running at `http://127.0.0.1:5000`.
    You can access the API at `http://127.0.0.1:5000/api/top-stories`.
    
    Comment analysis (summary) endpoint (requires local Ollama running):
    
    ```bash
    curl "http://127.0.0.1:5000/api/stories/<story_id>/comments/summary?max_depth=1&limit=30&chat_model=llama3.1:8b-instruct&embed_model=nomic-embed-text&weights=0.45,0.45,0.10"
    ```

5.  **Use the scraper as a CLI (top stories):**
    - Print JSON to stdout
      ```bash
      python api_integration/scraper.py
      ```
    - Write JSON to a file
      ```bash
      python api_integration/scraper.py --output output.json
      ```
    - Minified JSON
      ```bash
      python api_integration/scraper.py --no-pretty
      ```

6.  **Use the comment scraper as a CLI (story details + comments):**
    - Print story and comments to stdout
      ```bash
      python api_integration/comment_scraper.py <story_id>
      ```
    - Limit number of comments and depth
      ```bash
      python api_integration/comment_scraper.py <story_id> --limit 20 --max-depth 1
      ```
    - Write output to a file (pretty-printed)
      ```bash
      python api_integration/comment_scraper.py <story_id> -o comments.json
      ```
    - Minified JSON
      ```bash
      python api_integration/comment_scraper.py <story_id> --no-pretty
      ```

7.  **Make targets:**
    - Start API only
      ```bash
      make run_api
      ```
    - Start UI only (served at `http://127.0.0.1:8080`)
      ```bash
      make run_ui
      ```
    - Start both API (5000) and UI (8080)
      ```bash
      make run_all
      ```
    - Legacy alias (API only)
      ```bash
      make run
      ```

    The UI auto-detects if it's running on port `8080` and will call the API at `http://127.0.0.1:5000`. You can override the API base URL by setting `window.API_BASE_URL` before `app.js` runs.

8.  **Stop running services:**

## LLM Integration (Local Comment Analysis Service)

This component lives in `llm_integration/` and provides both a FastAPI service and a Typer CLI to analyze comment arrays using a local Ollama server.

### Install dependencies

```bash
uv pip install -r requirements.txt
uv pip install -e .
```

Or with pip:

```bash
pip install -r requirements.txt
pip install -e .
```

### Start API

```bash
python -m llm_integration.api
# or
uvicorn llm_integration.api:app --host 0.0.0.0 --port 8080
```

Health:

```bash
curl http://localhost:8080/health
```

Analyze:

```bash
curl -X POST http://localhost:8080/analyze \
  -H 'Content-Type: application/json' \
  -d '{
        "comments": [
          {"id":"1","author":"alice","text":"I agree with the post and add a point"},
          {"id":"2","author":"bob","text":"I disagree strongly for reasons X and Y"}
        ],
        "original_post": "Short description of the post",
        "chat_model": "llama3.1:8b-instruct",
        "embed_model": "nomic-embed-text",
        "topk": 10,
        "max_summary_comments": 40,
        "weights": [0.45,0.45,0.10]
      }'
```

### CLI usage

```bash
comments-analyze analyze \
  --input comments.json \
  --original-post post.txt \
  --ollama-host http://localhost:11434 \
  --chat-model llama3.1:8b-instruct \
  --embed-model nomic-embed-text \
  --topk 10 \
  --max-summary-comments 40 \
  --weights "0.45,0.45,0.10" \
  --out-json results.json \
  --out-csv results.csv \
  --out-md results.md
```

If `--input -` (or omitted), the tool reads JSON from stdin. `--original-post` is optional and, if provided, reads the text file.

### Configuration

Default constants (top of `llm_integration/config.py`):

```text
OLLAMA_HOST_DEFAULT = "http://localhost:11434"
CHAT_MODEL_DEFAULT = "gpt-oss:20b"
EMBED_MODEL_DEFAULT = "nomic-embed-text"
TOPK_DEFAULT = 10
MAX_SUMMARY_COMMENTS_DEFAULT = 40
```

Override precedence:
1) API payload fields, 2) CLI flags, 3) env vars (`OLLAMA_HOST`, `CHAT_MODEL`, `EMBED_MODEL`), 4) defaults.

### Sample input

```json
[
  {
    "id": "44902240",
    "author": "canyon289",
    "text": "Hi all, I built these models with a great team...",
    "age": "2 days ago",
    "timestamp": "2025-08-14T13:22:29.296614",
    "depth": 0,
    "parent_id": null
  }
]
```

    - Stop both API and UI by their ports (defaults: API 5000, UI 8081)
      ```bash
      make stop_all
      ```
    - Override ports if needed
      ```bash
      make stop_all API_PORT=5000 UI_PORT=3000
      ```
