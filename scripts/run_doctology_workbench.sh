#!/bin/bash
set -euo pipefail

REPO_DIR="/Users/hoyasung007hotmail.com/Documents/my_project/DocTology"
APP_DIR="$REPO_DIR/apps/doctology-workbench"

cd "$APP_DIR"

echo "============================================"
echo " DocTology Workbench GUI Launcher"
echo "============================================"
echo ""
echo "App dir: $APP_DIR"
echo ""

if [ ! -d node_modules ]; then
  echo "node_modules not found. Running npm install..."
  npm install
  echo ""
fi

echo "Starting Vite dev server..."
echo "URL: http://127.0.0.1:4173"
echo ""
echo "Press Ctrl+C to stop."
echo ""

npm run dev -- --host 127.0.0.1 --port 4173
