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
