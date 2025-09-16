#!/usr/bin/env bash
set -euo pipefail

# Repo root (absolute path for cron)
REPO_DIR="/Users/adib/Code/hackernews"
VENV_DIR="$REPO_DIR/.venv"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/top_stories_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

iso_ts() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

{
  echo "[$(iso_ts)] Starting top stories dump"
  cd "$REPO_DIR"

  # Ensure PYTHONPATH so imports resolve if needed
  export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"

  # Optional: override API base via env HN_API_BASE
  # Example: HN_API_BASE=http://127.0.0.1:5000

  # Prefer uv if available; fallback to venv python or system python
  if command -v uv >/dev/null 2>&1; then
    RUN_CMD=(uv run --no-project --with requests automation/fetch_top_stories.py)
  else
    # Activate venv if present, else use system python
    if [ -f "$VENV_DIR/bin/activate" ]; then
      # shellcheck disable=SC1090
      source "$VENV_DIR/bin/activate"
      PY_BIN="python"
    elif [ -x "$VENV_DIR/bin/python" ]; then
      PY_BIN="$VENV_DIR/bin/python"
    else
      PY_BIN="python"
    fi
    RUN_CMD=("$PY_BIN" automation/fetch_top_stories.py)
  fi

  API_BASE="${HN_API_BASE:-http://127.0.0.1:5000}"
  OUTPUT="$REPO_DIR/ui/api/top-stories.json"

  CMD_STR=$(printf "%q " "${RUN_CMD[@]}"; printf -- "--api-base %q --output %q" "$API_BASE" "$OUTPUT")
  echo "[$(iso_ts)] Running: $CMD_STR"

  "${RUN_CMD[@]}" --api-base "$API_BASE" --output "$OUTPUT"
  echo "[$(iso_ts)] Completed top stories dump"
} >> "$LOG_FILE" 2>&1


