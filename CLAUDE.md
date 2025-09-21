# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a Hacker News newsletter project with three main components:

1. **API Integration Layer** (`api_integration/`):
   - Hacker News scraping and comment fetching
   - Flask API server at port 5000
   - Main endpoints: `/api/top-stories`, `/api/stories/<id>/comments/summary`

2. **LLM Integration Layer** (`llm_integration/`):
   - Local comment analysis using Ollama
   - FastAPI service (default port 8080)
   - CLI tool for batch analysis (`comments-analyze`)
   - Requires local Ollama server running

3. **UI Layer** (`ui/`):
   - Static HTML/CSS/JS frontend
   - Flask server at port 8081 for serving static files
   - Auto-detects API base URL when running on port 8081

## Common Development Commands

### Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .  # For LLM integration CLI
```

### Running Services
```bash
make run_api          # Start API only (port 5000)
make run_ui           # Start UI only (port 8081)
make run_all          # Start both API and UI
make stop_all         # Stop both services by port
```

### Testing
```bash
make test                # Run all tests (pytest or unittest fallback)
make test_content_only   # Run only content analysis tests
make validate_tests      # Validate test infrastructure without running tests
pytest tests/            # Direct pytest execution (if available)
```

### Data Operations
```bash
make dump_top_stories           # Dump top stories JSON to ui/api/top-stories.json
make dump_comment_summaries     # Fetch top stories + generate comment summaries for all stories
make cleanup_old_stories        # Remove old story directories not in current top stories
make cleanup_old_stories_dry_run # Show what old directories would be removed (dry run)
make full_pipeline              # Complete automation: cleanup + fetch stories + generate summaries
```

### Automation & Scheduling
```bash
bash automation/setup_cron.sh install  # Install cron jobs to run pipeline every 4 hours
bash automation/setup_cron.sh view     # View current cron jobs
bash automation/setup_cron.sh remove   # Remove automation cron jobs
bash automation/setup_cron.sh backup   # Backup current crontab
```

### CLI Tools
```bash
python api_integration/scraper.py                    # Scrape top stories
python api_integration/comment_scraper.py <story_id> # Scrape story comments
python api_integration/content_summarizer.py <url>   # Analyze webpage content with LLM
comments-analyze analyze --input comments.json       # Analyze comments with LLM
```

### Content Analysis
```bash
make fetch_content URL=<webpage_url>                 # Fetch and extract webpage content (no LLM)
make analyze_content URL=<webpage_url>               # Analyze webpage content using LLM
make test_content_analysis                           # Test LLM content analysis with sample data
```

## Key Dependencies

- **Python 3.10+** required
- **Flask/FastAPI**: API servers
- **Ollama**: Required for LLM comment analysis (must be running locally)
- **requests/beautifulsoup4**: Web scraping
- **scikit-learn/pandas**: Comment analysis and ranking

## Architecture Notes

- The main Flask API (`api_integration/api.py`) integrates both HN scraping and LLM analysis
- Comment analysis requires an Ollama server running locally (default: http://localhost:11434)
- UI auto-configures API base URL based on its own port
- CORS is configured to allow UI-to-API communication between different ports
- The project uses a hybrid Flask (main API) + FastAPI (LLM service) architecture

## Port Configuration

- API: 5000 (configurable via API_PORT env var)
- UI: 8081 (configurable via UI_PORT env var)
- LLM Service: 8080 (separate FastAPI service)

## Testing Strategy

Tests use pytest with integration-style testing for API endpoints. Mock external dependencies like Hacker News API calls when needed.