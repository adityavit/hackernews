# Component: Web UI for Top Stories

## Goal
Create a simple web page that calls the `/api/top-stories` endpoint and renders the results.

## TODO
- [x] Decide fetch endpoint base URL. Default to `/api/top-stories`; when served from `:8080`, use `http://127.0.0.1:5000` automatically. Allow override via `window.API_BASE_URL`.
- [x] Build static UI scaffold: `ui/index.html`, `ui/styles.css`, `ui/app.js`.
- [x] Implement loading and error states.
- [x] Render list of stories showing: title (link), score, user, age, comments.
- [x] Basic responsive styling and accessible markup.
- [x] Verify JSON fields match `scrape_hacker_news()` output.
- [x] Integration options:
  - [ ] Serve UI via Flask (same-origin)
  - [x] Enable CORS on API to allow different origin for local dev.
- [ ] Optional: client-side sorting/filtering by score/comments.
- [x] Optional: Makefile targets to serve UI locally (added `run_ui`, `run_all`).
