# Local Comment Analysis Service (Ollama) - Context

## Goal
Build a local-only service (API + CLI) that analyzes a JSON array of comments using a local Ollama instance and returns a structured summary and rankings.

## Deliverables
- [ ] Production-ready Python package in `llm_integration/` with:
  - [ ] `config.py` (defaults + overrides)
  - [ ] `ollama_client.py` (thin HTTP wrapper)
  - [ ] `analysis.py` (embeddings, novelty, controversy, MMR, summary, ranking)
  - [ ] `api.py` (FastAPI app with `/health`, `/analyze`)
  - [ ] `cli.py` (Typer CLI `comments-analyze`)
- [ ] `pyproject.toml` with deps and console script
- [ ] README quickstart, examples
- [ ] Update root `requirements.txt` with needed deps

## TODO
- [x] Create `llm_integration/` package and context.md
- [ ] Implement `config.py` with precedence (API payload > CLI > env > defaults)
- [ ] Implement `ollama_client.py` with `/api/chat` and `/api/embed` + retries
- [ ] Implement `analysis.py`:
  - [ ] `embed_texts`
  - [ ] `novelty_scores`
  - [ ] `classify_stance`
  - [ ] `controversy_scores`
  - [ ] `mmr`
  - [ ] `generate_summary`
  - [ ] `score_and_rank`
  - [ ] `analyze_comments`
- [ ] Implement `api.py` (FastAPI) with models and CORS allow-list
- [ ] Implement `cli.py` (Typer) with JSON in/out, optional CSV/MD writers
- [ ] Add `pyproject.toml` with console script `comments-analyze`
- [ ] Update root `README.md` with quickstart and examples
- [ ] Add minimal sample JSON in README and curl example

## Acceptance Criteria
- [ ] API `POST /analyze` returns valid schema given sample input
- [ ] CLI prints same JSON; optional CSV/MD outputs
- [ ] Config overrides work (env, CLI, API payload)
- [ ] No external network except Ollama

## Completed
- [x] Created `llm_integration/` and this context document
- [x] Implement `config.py` with precedence (API payload > CLI > env > defaults)
- [x] Implement `ollama_client.py` with `/api/chat` and `/api/embed` + retries
- [x] Implement `analysis.py`:
  - [x] `embed_texts`
  - [x] `novelty_scores`
  - [x] `classify_stance`
  - [x] `controversy_scores`
  - [x] `mmr`
  - [x] `generate_summary`
  - [x] `score_and_rank`
  - [x] `analyze_comments`
- [x] Implement `api.py` (FastAPI) with models and CORS allow-list
- [x] Implement `cli.py` (Typer) with JSON in/out, optional CSV/MD writers
- [x] Add `pyproject.toml` with console script `comments-analyze`
- [x] Update root `README.md` with quickstart and examples
- [x] Add minimal sample JSON in README and curl example
- [x] API `POST /analyze` returns valid schema given sample input
- [x] CLI prints same JSON; optional CSV/MD outputs
- [x] Config overrides work (env, CLI, API payload)
- [x] No external network except Ollama

### Additional Tasks Completed (Content Analysis)
- [x] Create `content_analysis.py` module for webpage content analysis
- [x] Implement `analyze_webpage_content()` function with LLM integration
- [x] Design structured prompts for comprehensive content analysis
- [x] Add response parsing and validation for JSON/markdown LLM responses
- [x] Support for content metadata extraction (tone, topics, audience, etc.)
- [x] Error handling for insufficient content and LLM connection failures
- [x] Integration with existing Ollama client and configuration system
- [x] Comprehensive test suite with HTML fixtures and mock LLM responses
