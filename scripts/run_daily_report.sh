#!/bin/zsh

set -euo pipefail

export TZ=Asia/Shanghai
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

PROJECT_ROOT="/Users/yugugaode/Documents/New project"
PYTHON_BIN="/usr/bin/python3"
PREPARE_SCRIPT="$PROJECT_ROOT/scripts/prepare_iteration_report.py"
RENDER_SCRIPT="$PROJECT_ROOT/scripts/render_iteration_report.py"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/daily-report.log"
REPORT_DATE="${REPORT_DATE_OVERRIDE:-$(date '+%Y-%m-%d')}"

mkdir -p "$LOG_DIR"

{
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] start daily report sync for $REPORT_DATE"
  "$PYTHON_BIN" "$PREPARE_SCRIPT" --date "$REPORT_DATE"
  "$PYTHON_BIN" "$RENDER_SCRIPT" --date "$REPORT_DATE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] finished daily report sync for $REPORT_DATE"
} >> "$LOG_FILE" 2>&1
