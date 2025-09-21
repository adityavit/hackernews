# Context for Automation

## Goal
Automate fetching and persisting API responses for UI consumption.

## Tasks (Phase 1)

1) Store top stories JSON in `ui/api/top-stories.json`
- [x] Create directory if missing: `ui/api/`
- [x] Read API base URL from env (default `http://127.0.0.1:5000`)
- [x] GET `/api/top-stories`
- [x] Validate payload (array of stories with id/title/url/score/user/comments)
- [x] Write prettified JSON to `ui/api/top-stories.json`
- [x] Log status and errors; exit non-zero on failure
- [x] Optional: support `--output` flag to override destination

2) Store per-story comment summaries under `ui/api/stories/<id>/comments/summary.json`
- [x] Ensure directories exist: `ui/api/stories/<id>/comments/`
- [x] Load top stories from `ui/api/top-stories.json` (or fetch if missing)
- [x] For each story id, call API `/api/stories/<id>/comments/summary?max_depth=1&limit=40`
- [x] Validate payload fields: `summary`, `top_comments`, optional `all_comments`, and `config_used`
- [x] Atomically write prettified JSON to `ui/api/stories/<id>/comments/summary.json`
- [x] Include `generated_at` and `source` metadata in each file
- [x] Implement retry with exponential backoff for HTTP 5xx/timeouts
- [x] Respect rate limiting: configurable small delay between requests
- [x] Skip existing files unless `--force` is provided
- [x] Optional filters/CLI flags: `--ids 1,2`, `--since <ISO>`, `--limit N`, `--params "max_depth=1&limit=40"`
- [x] Add Makefile target `dump_summaries` that invokes the script
- [x] Log per-story success/failure and a final summary count

## Considerations
- Add cron integration (Phase 2):
  - [x] Create shell script `automation/dump_top_stories.sh` to invoke Python fetcher and log output
  - [x] Add crontab entry example in README (e.g., run every hour)
  - [x] Optional: rotate logs or prune old files

## Additional Tasks Completed (Session Updates)

3) **UI Integration & Static File Serving**
- [x] Modified UI to fetch summaries from static JSON files (`/api/stories/<id>/comments/summary.json`)
- [x] Updated `SUMMARY_URL` function to use static file paths instead of live API
- [x] Removed query parameters from summary requests

4) **Data Cleanup & Management**
- [x] Created `cleanup_old_stories.py` script to remove obsolete story directories
- [x] Added smart cleanup logic that preserves only current top stories
- [x] Implemented dry-run mode for safe preview of cleanup actions
- [x] Added automatic top-stories.json updating before cleanup
- [x] Created Makefile targets: `cleanup_old_stories`, `cleanup_old_stories_dry_run`

5) **Full Automation Pipeline**
- [x] Created `full_pipeline.sh` comprehensive automation script
- [x] Integrated cleanup → fetch stories → generate summaries workflow
- [x] Added comprehensive logging with timestamped entries
- [x] Implemented error handling and graceful fallbacks
- [x] Added environment detection (uv/venv/system python)
- [x] Created Makefile target: `full_pipeline`

6) **Cron Job Automation**
- [x] Created `crontab.txt` configuration for 4-hour automated runs
- [x] Built `setup_cron.sh` management script for easy installation/removal
- [x] Added automatic path detection and crontab backup protection
- [x] Included alternative scheduling options (6hr, daily, etc.)

7) **Documentation & Project Setup**
- [x] Created comprehensive `CLAUDE.md` file for future Claude Code instances
- [x] Documented project architecture, common commands, and workflows
- [x] Added automation scheduling section with cron management commands
- [x] Updated context.md files with completed tasks
- Use Python `requests` for HTTP calls
- Fail fast for invalid or empty payloads; leave partial files intact by writing to temp and renaming
- Include timestamps in logs; record `generated_at` in JSON if helpful
- Keep I/O atomic: write to `*.tmp` then move to destination
 - UI server maps file paths under `ui/api/` to HTTP paths under `/api/`.
   - Example: file `ui/api/stories/123/comments/summary.json` is served at `/api/stories/123/comments/summary` (JSON)
