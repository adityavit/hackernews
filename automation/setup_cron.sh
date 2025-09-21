#!/usr/bin/env bash
set -euo pipefail

# Script to setup cron jobs for Hacker News automation
# This script helps install, remove, or view cron jobs for the project

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRONTAB_FILE="$REPO_DIR/automation/crontab.txt"
BACKUP_FILE="$REPO_DIR/automation/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"

show_usage() {
  cat << EOF
Usage: $(basename "$0") [COMMAND]

Commands:
  install     Install cron jobs from crontab.txt
  remove      Remove Hacker News cron jobs
  view        View current cron jobs
  backup      Backup current crontab
  help        Show this help message

Examples:
  $(basename "$0") install    # Install the cron jobs
  $(basename "$0") view       # Show current cron jobs
  $(basename "$0") remove     # Remove HN-related cron jobs
EOF
}

backup_crontab() {
  echo "Backing up current crontab to: $BACKUP_FILE"
  if crontab -l > "$BACKUP_FILE" 2>/dev/null; then
    echo "✓ Backup saved successfully"
  else
    echo "ℹ No existing crontab found"
    touch "$BACKUP_FILE"
  fi
}

install_cron() {
  echo "Installing Hacker News cron jobs..."

  # Backup existing crontab
  backup_crontab

  # Check if crontab file exists
  if [ ! -f "$CRONTAB_FILE" ]; then
    echo "Error: Crontab file not found at $CRONTAB_FILE"
    exit 1
  fi

  # Update paths in crontab file to use current repo directory
  echo "Updating crontab with current repository path: $REPO_DIR"
  sed "s|/Users/adib/Code/hackernews|$REPO_DIR|g" "$CRONTAB_FILE" > "${CRONTAB_FILE}.tmp"

  # Install the cron jobs
  if crontab "${CRONTAB_FILE}.tmp"; then
    echo "✓ Cron jobs installed successfully"
    rm -f "${CRONTAB_FILE}.tmp"
    echo ""
    echo "Installed cron jobs:"
    crontab -l | grep -v "^#" | grep -v "^$" || echo "No active cron jobs found"
  else
    echo "✗ Failed to install cron jobs"
    rm -f "${CRONTAB_FILE}.tmp"
    exit 1
  fi
}

remove_cron() {
  echo "Removing Hacker News cron jobs..."

  # Backup existing crontab
  backup_crontab

  # Remove lines containing the project path
  if crontab -l 2>/dev/null | grep -v "$REPO_DIR" | crontab -; then
    echo "✓ Hacker News cron jobs removed successfully"
    echo ""
    echo "Remaining cron jobs:"
    crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "No cron jobs remaining"
  else
    echo "ℹ No cron jobs found to remove"
  fi
}

view_cron() {
  echo "Current cron jobs:"
  echo ""
  if crontab -l 2>/dev/null; then
    echo ""
    echo "Hacker News related jobs:"
    crontab -l 2>/dev/null | grep "$REPO_DIR" || echo "No Hacker News cron jobs found"
  else
    echo "No crontab found"
  fi
}

# Main command handling
case "${1:-help}" in
  install)
    install_cron
    ;;
  remove)
    remove_cron
    ;;
  view)
    view_cron
    ;;
  backup)
    backup_crontab
    ;;
  help|--help|-h)
    show_usage
    ;;
  *)
    echo "Error: Unknown command '$1'"
    echo ""
    show_usage
    exit 1
    ;;
esac