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

# Command to run the tests
RUN_TESTS = $(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && pytest tests/

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

.PHONY: run run_api run_ui run_all test

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

.PHONY: dump_top_stories
