#!/usr/bin/env bash
# git-orchestrator dashboard — start/stop wrapper
# Usage: bash scripts/start-dashboard.sh [start|stop|status] [--port N]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
PORT="${GIT_DASHBOARD_PORT:-7777}"
PID_FILE="$REPO_ROOT/.claude/dashboard.pid"

# Parse args
ACTION="${1:-start}"
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

cmd_start() {
  if is_running; then
    echo "[dashboard] Already running (PID $(cat "$PID_FILE")) → http://localhost:$PORT"
    return 0
  fi
  if ! command -v python3 &>/dev/null; then
    echo "[dashboard] python3 not found — cannot start dashboard." >&2
    return 1
  fi
  GIT_DASHBOARD_PORT="$PORT" python3 "$SCRIPT_DIR/dashboard.py" &
  echo $! > "$PID_FILE"
  echo "[dashboard] Started (PID $!) → http://localhost:$PORT"
}

cmd_stop() {
  if ! is_running; then
    echo "[dashboard] Not running."
    rm -f "$PID_FILE"
    return 0
  fi
  kill "$(cat "$PID_FILE")" && rm -f "$PID_FILE"
  echo "[dashboard] Stopped."
}

cmd_status() {
  if is_running; then
    echo "[dashboard] Running (PID $(cat "$PID_FILE")) → http://localhost:$PORT"
  else
    echo "[dashboard] Not running."
    rm -f "$PID_FILE" 2>/dev/null || true
  fi
}

case "$ACTION" in
  start)  cmd_start  ;;
  stop)   cmd_stop   ;;
  status) cmd_status ;;
  *)
    echo "Usage: $0 {start|stop|status} [--port N]"
    exit 1
    ;;
esac
