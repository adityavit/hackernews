# Makefile for the Hacker News Letter project

# Activate the virtual environment
VENV_ACTIVATE = source .venv/bin/activate

# UI port (can be overridden: `make run_ui UI_PORT=3000`)
UI_PORT ?= 8081

# Command to run the Flask server (API)
RUN_SERVER = $(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd) && python api_integration/api.py

# Command to serve the UI (static server)
RUN_UI = cd ui && python -m http.server $(UI_PORT)

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
	@bash -c '$(RUN_SERVER) & PID_API=$$!; cd ui && python -m http.server $(UI_PORT) & PID_UI=$$!; wait $$PID_API $$PID_UI'

# Target to run the tests
test:
	@echo "Running the tests..."
	@$(RUN_TESTS)

# Backwards-compatibility: `make run` still starts the API server
run: run_api

.PHONY: run run_api run_ui run_all test
