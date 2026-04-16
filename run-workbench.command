#!/bin/zsh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKBENCH_DIR="$REPO_DIR/apps/workbench"
API_HOST="127.0.0.1"
API_PORT="8765"
WEB_HOST="127.0.0.1"
WEB_PORT="4174"
TMP_DIR="$REPO_DIR/.agent/tmp"
API_LOG="$TMP_DIR/workbench-api.log"
WEB_LOG="$TMP_DIR/workbench-web.log"
WEB_URL="http://$WEB_HOST:$WEB_PORT"
API_READY_URL="http://$API_HOST:$API_PORT/api/workbench/summary"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

port_listener() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | head -n 1 || true
}

process_command() {
  ps -p "$1" -o command= 2>/dev/null || true
}

listener_matches_fragment() {
  local pid="$1"
  local fragment="$2"
  local command
  command="$(process_command "$pid")"
  [ -n "$command" ] && [[ "$command" == *"$fragment"* ]]
}

api_listener_matches_repo() {
  local pid="$1"
  local reported_root

  if ! listener_matches_fragment "$pid" "$REPO_DIR/scripts/workbench_api.py"; then
    return 1
  fi

  if ! listener_matches_fragment "$pid" "--root $REPO_DIR"; then
    return 1
  fi

  reported_root="$(curl -fsS "$API_READY_URL" | python3 -c 'import json, sys; print(json.load(sys.stdin).get("root", ""))' 2>/dev/null || true)"
  [ "$reported_root" = "$REPO_DIR" ]
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-40}"
  local delay="${3:-0.25}"
  local count=0

  while [ "$count" -lt "$attempts" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
    count=$((count + 1))
  done

  return 1
}

start_api() {
  local listener
  listener="$(port_listener "$API_PORT")"
  if [ -n "$listener" ]; then
    if wait_for_url "$API_READY_URL" 4 0.25; then
      if api_listener_matches_repo "$listener"; then
        echo "Workbench API already listening on $API_PORT (pid $listener)"
        return 0
      fi
      echo "Workbench API listener on $API_PORT belongs to a different repo. Restarting (pid $listener)"
    else
      echo "Workbench API listener on $API_PORT is unhealthy. Restarting (pid $listener)"
    fi
    kill "$listener" 2>/dev/null || true
    sleep 0.5
  fi

  echo "Starting Workbench API on $API_HOST:$API_PORT"
  nohup python3 "$REPO_DIR/scripts/workbench_api.py" \
    --root "$REPO_DIR" \
    --serve \
    --host "$API_HOST" \
    --port "$API_PORT" \
    >"$API_LOG" 2>&1 &

  if ! wait_for_url "$API_READY_URL" 60 0.25; then
    echo "Workbench API did not become ready. Check: $API_LOG"
    exit 1
  fi

  listener="$(port_listener "$API_PORT")"
  if [ -z "$listener" ] || ! api_listener_matches_repo "$listener"; then
    echo "Workbench API became reachable, but the listener does not match this repo. Check: $API_LOG"
    exit 1
  fi
}

start_web() {
  local listener
  listener="$(port_listener "$WEB_PORT")"

  if [ ! -d "$WORKBENCH_DIR/node_modules" ]; then
    echo "Installing workbench dependencies"
    (
      cd "$WORKBENCH_DIR"
      npm install
    )
  fi

  if [ -n "$listener" ]; then
    if wait_for_url "$WEB_URL" 4 0.25; then
      if listener_matches_fragment "$listener" "$WORKBENCH_DIR"; then
        echo "Workbench web UI already listening on $WEB_PORT (pid $listener)"
        return 0
      fi
      echo "Workbench web UI listener on $WEB_PORT belongs to a different repo. Restarting (pid $listener)"
    else
      echo "Workbench web UI listener on $WEB_PORT is unhealthy. Restarting (pid $listener)"
    fi
    kill "$listener" 2>/dev/null || true
    sleep 0.5
  fi

  echo "Starting Workbench web UI on $WEB_HOST:$WEB_PORT"
  (
    cd "$WORKBENCH_DIR"
    nohup npm run dev -- --host "$WEB_HOST" --port "$WEB_PORT" >"$WEB_LOG" 2>&1 &
  )

  if ! wait_for_url "$WEB_URL" 80 0.25; then
    echo "Workbench web UI did not become ready. Check: $WEB_LOG"
    exit 1
  fi

  listener="$(port_listener "$WEB_PORT")"
  if [ -z "$listener" ] || ! listener_matches_fragment "$listener" "$WORKBENCH_DIR"; then
    echo "Workbench web UI became reachable, but the listener does not match this repo. Check: $WEB_LOG"
    exit 1
  fi
}

main() {
  require_command python3
  require_command npm
  require_command curl
  require_command lsof

  mkdir -p "$TMP_DIR"

  echo "Repo: $REPO_DIR"
  start_api
  start_web

  echo "Opening $WEB_URL"
  open "$WEB_URL"
  echo ""
  echo "Workbench is ready."
  echo "API log: $API_LOG"
  echo "Web log: $WEB_LOG"
}

main "$@"
