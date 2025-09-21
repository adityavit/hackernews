# Makefile for the Hacker News Letter project

# Activate the virtual environment
VENV_ACTIVATE = source .venv/bin/activate

# UI port (can be overridden: `make run_ui UI_PORT=3000`)
UI_PORT ?= 8081
API_PORT ?= 5000

# Command to run the Flask server (API)
RUN_SERVER = $(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && python api_integration/api.py

# Command to serve the UI (Flask app for static + JSON under /api)
RUN_UI = cd ui && UI_PORT=$(UI_PORT) flask --app server run --host 0.0.0.0 --port $(UI_PORT)

# Command to run the tests (try pytest first, fallback to unittest)
RUN_TESTS = $(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && (pytest tests/ -v 2>/dev/null || python3 -m unittest discover tests/ -v)

# Target to run only the API server
run_api:
	@echo "Starting the API server on http://127.0.0.1:5000 ..."
	@$(RUN_SERVER)

# Target to run only the UI server
run_ui:
	@echo "Serving UI on http://127.0.0.1:$(UI_PORT) ..."
	@$(RUN_UI)

# Target to run both API and UI servers
run_all:
	@echo "Starting API (5000) and UI ($(UI_PORT)) servers..."
	@bash -c '$(RUN_SERVER) & PID_API=$$!; cd ui && UI_PORT=$(UI_PORT) flask --app server run --host 0.0.0.0 --port $(UI_PORT) & PID_UI=$$!; wait $$PID_API $$PID_UI'

# Target to run the tests
test:
	@echo "Running the tests..."
	@$(RUN_TESTS)

# Backwards-compatibility: `make run` still starts the API server
run: run_api

.PHONY: run run_api run_ui run_all

# Stop all running services (by port)
stop_all:
	@echo "Stopping services on API $(API_PORT) and UI $(UI_PORT) ports..."
	@bash -c 'pids=$$(lsof -ti tcp:$(API_PORT)); if [ -n "$$pids" ]; then echo "Stopping API (PIDs: $$pids)"; kill $$pids || true; sleep 0.5; pids2=$$(lsof -ti tcp:$(API_PORT)); [ -n "$$pids2" ] && kill -9 $$pids2 || true; else echo "No process on port $(API_PORT)"; fi'
	@bash -c 'pids=$$(lsof -ti tcp:$(UI_PORT)); if [ -n "$$pids" ]; then echo "Stopping UI (PIDs: $$pids)"; kill $$pids || true; sleep 0.5; pids2=$$(lsof -ti tcp:$(UI_PORT)); [ -n "$$pids2" ] && kill -9 $$pids2 || true; else echo "No process on port $(UI_PORT)"; fi'

.PHONY: stop_all

# Dump top stories JSON for UI via automation script
dump_top_stories:
	@echo "Dumping top stories JSON to ui/api/top-stories.json ..."
	@bash automation/dump_top_stories.sh

# Dump comment summaries for all top stories (depends on dump_top_stories)
dump_comment_summaries: dump_top_stories
	@echo "Dumping comment summaries for all top stories ..."
	@$(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && python automation/dump_comment_summaries.py

# Clean up old story directories not in current top stories
cleanup_old_stories:
	@echo "Cleaning up old story directories ..."
	@$(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && python automation/cleanup_old_stories.py --update-top-stories

# Dry run cleanup to see what would be removed
cleanup_old_stories_dry_run:
	@echo "Dry run: showing old story directories that would be removed ..."
	@$(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && python automation/cleanup_old_stories.py --update-top-stories --dry-run

# Full automation pipeline: cleanup + fetch stories + generate summaries
full_pipeline:
	@echo "Running full automation pipeline: cleanup -> fetch -> summaries ..."
	@bash automation/full_pipeline.sh

# Fetch webpage content without LLM analysis (requires URL parameter)
fetch_content:
	@if [ -z "$(URL)" ]; then \
		echo "Usage: make fetch_content URL=<webpage_url>"; \
		echo "Example: make fetch_content URL=https://example.com"; \
		exit 1; \
	fi
	@echo "Fetching content from $(URL) ..."
	@$(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && python api_integration/content_fetcher.py "$(URL)"

# Analyze webpage content using LLM (requires URL parameter)
analyze_content:
	@if [ -z "$(URL)" ]; then \
		echo "Usage: make analyze_content URL=<webpage_url>"; \
		echo "Example: make analyze_content URL=https://example.com"; \
		exit 1; \
	fi
	@echo "Analyzing content from $(URL) ..."
	@$(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && python api_integration/content_summarizer.py "$(URL)"

# Test LLM content analysis with sample content
test_content_analysis:
	@echo "Testing LLM content analysis with sample content ..."
	@$(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && python llm_integration/content_analysis.py

# Validate test infrastructure without running actual tests
validate_tests:
	@echo "Validating test infrastructure ..."
	@python3 test_runner.py

# Run only content analysis tests
test_content_only:
	@echo "Running content analysis tests only ..."
	@$(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && (pytest tests/test_content_analysis.py tests/test_content_summarizer.py -v 2>/dev/null || echo "pytest not available, use 'make test' instead")

.PHONY: dump_top_stories dump_comment_summaries cleanup_old_stories cleanup_old_stories_dry_run full_pipeline fetch_content analyze_content test_content_analysis validate_tests test_content_only test
