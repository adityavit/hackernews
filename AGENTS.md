# Repository Guidelines

## Project Structure & Module Organization
- `api_integration/`: Flask API, story scraper, and comment fetcher used by the UI and automation jobs.
- `llm_integration/`: FastAPI analysis service, Typer CLI, and config helpers for the Ollama-backed summarizer.
- `ui/`: Flask static server plus `index.html` (renders the fetch timestamp), `app.js`, `styles.css`, and cached responses in `ui/api/`.
- `automation/`, `email_delivery/`, `html_generator/`, `post_processing/`: orchestrate scrape → render → deliver.
- `tests/`: pytest suites with fixtures in `tests/fixtures/`; temp artifacts stay in `logs/`.

## Build, Test, and Development Commands
- `uv pip install -r requirements.txt` (or `pip`): install shared Python dependencies for API, UI, and analyzers.
- `make run_api`, `make run_ui`, `make run_all`: start the Flask API, the static UI, or both with proper `PYTHONPATH` exports.
- `make test`: invokes `pytest tests/`, covering scrapers, API handlers, and analysis helpers.
- `python -m llm_integration.api` or `uvicorn llm_integration.api:app`: run the comment-summary microservice while iterating on LLM features.
- `bash automation/dump_top_stories.sh`: refresh `ui/api/top-stories.json` for demos without hitting Hacker News live.

## Coding Style & Naming Conventions
Follow PEP 8: four-space indentation, `snake_case` functions, and descriptive module names (`comment_scraper`, `analysis`). Keep Flask views thin—delegate parsing to helpers and handle HTTP failures explicitly. Use dataclasses for config (`llm_integration/config.py`), add type hints on public functions, and prefer short docstrings to inline comments. Front-end logic embraces vanilla JS with camelCase helpers and delegated event handlers; keep DOM IDs stable for tests. Store generated files in `logs/` or `ui/api/`.

## Testing Guidelines
Extend the pytest suite alongside new code; mirror module names (`test_comment_scraper.py`, etc.) and store canned HTML in `tests/fixtures/`. Use `pytest-mock` to isolate network calls, and cover both success and fallback branches for scraper failures, API 4xx, and summarizer overrides. Record CLI or API regressions with integration tests before landing major refactors.

## Commit & Pull Request Guidelines
Commits follow a Conventional Commits dialect (`feat(ui): add summary toggle`, `refactor(api): tighten config parsing`). Keep subjects imperative and under 72 characters, and group related changes per commit. PRs should describe intent, list manual verification commands (`make test`, `make run_all`), link issues, and attach screenshots or terminal captures for UI or CLI changes. Call out new environment variables (`OLLAMA_HOST`, `CHAT_MODEL`, etc.) so reviewers can reproduce locally.

## Configuration Notes
The LLM stack reads overrides from `OLLAMA_HOST`, `CHAT_MODEL`, `EMBED_MODEL`, `TOPK`, and `MAX_SUMMARY_COMMENTS`; document additions in the README. Store secrets in ignored `.env` files and never commit outputs dropped in `logs/` or `ui/api/`.
