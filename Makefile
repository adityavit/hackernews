# Makefile for the Hacker News Letter project

# Activate the virtual environment
VENV_ACTIVATE = source .venv/bin/activate

# Command to run the Flask server
RUN_SERVER = $(VENV_ACTIVATE) && python hacker-news-letter/api_integration/scraper.py

# Command to run the tests
RUN_TESTS = $(VENV_ACTIVATE) && export PYTHONPATH=$(PYTHONPATH):$(shell pwd)/hacker-news-letter && pytest hacker-news-letter/tests/

# Target to run the server
run:
	@echo "Starting the Flask server..."
	@$(RUN_SERVER)

# Target to run the tests
test:
	@echo "Running the tests..."
	@$(RUN_TESTS)

.PHONY: run test
