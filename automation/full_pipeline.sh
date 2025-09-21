#!/usr/bin/env bash
set -euo pipefail

# Full automation pipeline script
# 1. Clean up old story directories not in current top stories
# 2. Fetch latest top stories
# 3. Generate comment summaries for all top stories

# Repo root (absolute path for cron or external execution)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$REPO_DIR/.venv"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/full_pipeline_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$LOG_DIR"

iso_ts() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log_and_echo() {
  echo "[$(iso_ts)] $1" | tee -a "$LOG_FILE"
}

run_python_script() {
  local script="$1"
  shift  # Remove script name from arguments
  local args=("$@")

  log_and_echo "Running: $script ${args[*]}"

  # Prefer uv if available; fallback to venv python or system python
  if command -v uv >/dev/null 2>&1; then
    uv run --no-project --with requests "$script" "${args[@]}" >> "$LOG_FILE" 2>&1
  else
    # Activate venv if present, else use system python
    if [ -f "$VENV_DIR/bin/activate" ]; then
      # shellcheck disable=SC1090
      source "$VENV_DIR/bin/activate"
      python "$script" "${args[@]}" >> "$LOG_FILE" 2>&1
    elif [ -x "$VENV_DIR/bin/python" ]; then
      "$VENV_DIR/bin/python" "$script" "${args[@]}" >> "$LOG_FILE" 2>&1
    else
      python "$script" "${args[@]}" >> "$LOG_FILE" 2>&1
    fi
  fi
}

# Change to repo directory
cd "$REPO_DIR"

# Ensure PYTHONPATH so imports resolve
export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"

# API base configuration
API_BASE="${HN_API_BASE:-http://127.0.0.1:5000}"

log_and_echo "Starting full automation pipeline"
log_and_echo "API Base: $API_BASE"
log_and_echo "Repository: $REPO_DIR"

# Step 1: Clean up old story directories
log_and_echo "Step 1: Cleaning up old story directories..."
if run_python_script "automation/cleanup_old_stories.py" --api-base "$API_BASE" --update-top-stories; then
  log_and_echo "✓ Cleanup completed successfully"
else
  log_and_echo "✗ Cleanup failed, continuing anyway..."
fi

# Step 2: Fetch latest top stories
log_and_echo "Step 2: Fetching latest top stories..."
if run_python_script "automation/fetch_top_stories.py" --api-base "$API_BASE" --output "ui/api/top-stories.json"; then
  log_and_echo "✓ Top stories fetch completed successfully"
else
  log_and_echo "✗ Top stories fetch failed"
  exit 1
fi

# Step 3: Generate comment summaries for all stories
log_and_echo "Step 3: Generating comment summaries for all stories..."
if run_python_script "automation/dump_comment_summaries.py" --api-base "$API_BASE"; then
  log_and_echo "✓ Comment summaries generation completed successfully"
else
  log_and_echo "✗ Comment summaries generation failed"
  exit 1
fi

# Final summary
log_and_echo "Full automation pipeline completed successfully!"

# Show summary stats
if [ -f "ui/api/top-stories.json" ]; then
  story_count=$(python -c "import json; data=json.load(open('ui/api/top-stories.json')); print(len(data.get('data', data)))" 2>/dev/null || echo "unknown")
  log_and_echo "Total stories processed: $story_count"
fi

stories_dir="ui/api/stories"
if [ -d "$stories_dir" ]; then
  summary_count=$(find "$stories_dir" -name "summary.json" | wc -l)
  log_and_echo "Total summaries available: $summary_count"
fi

log_and_echo "Pipeline log: $LOG_FILE"

# Show last few lines to console
echo ""
echo "Pipeline completed! Last few log entries:"
tail -10 "$LOG_FILE"