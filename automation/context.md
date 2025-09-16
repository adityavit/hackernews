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
- [ ] Ensure directories exist: `ui/api/stories/<id>/comments/`
- [ ] Load top stories from `ui/api/top-stories.json` (or fetch if missing)
- [ ] For each story id, call API `/api/stories/<id>/comments/summary?max_depth=1&limit=40`
- [ ] Validate payload fields: `summary`, `top_comments`, optional `all_comments`, and `config_used`
- [ ] Atomically write prettified JSON to `ui/api/stories/<id>/comments/summary.json`
- [ ] Include `generated_at` and `source` metadata in each file
- [ ] Implement retry with exponential backoff for HTTP 5xx/timeouts
- [ ] Respect rate limiting: configurable small delay between requests
- [ ] Skip existing files unless `--force` is provided
- [ ] Optional filters/CLI flags: `--ids 1,2`, `--since <ISO>`, `--limit N`, `--params "max_depth=1&limit=40"`
- [ ] Add Makefile target `dump_summaries` that invokes the script
- [ ] Log per-story success/failure and a final summary count

## Considerations
- Add cron integration (Phase 2):
  - [ ] Create shell script `automation/dump_top_stories.sh` to invoke Python fetcher and log output
  - [ ] Add crontab entry example in README (e.g., run every hour)
  - [ ] Optional: rotate logs or prune old files
- Use Python `requests` for HTTP calls
- Fail fast for invalid or empty payloads; leave partial files intact by writing to temp and renaming
- Include timestamps in logs; record `generated_at` in JSON if helpful
- Keep I/O atomic: write to `*.tmp` then move to destination
 - UI server maps file paths under `ui/api/` to HTTP paths under `/api/`.
   - Example: file `ui/api/stories/123/comments/summary.json` is served at `/api/stories/123/comments/summary` (JSON)
