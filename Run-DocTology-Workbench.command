#!/bin/bash
set -euo pipefail

REPO_DIR="/Users/hoyasung007hotmail.com/Documents/my_project/DocTology"
SCRIPT_PATH="$REPO_DIR/scripts/run_doctology_workbench.sh"
URL="http://127.0.0.1:4173"

cd "$REPO_DIR"

clear
echo "============================================"
echo " Run DocTology Workbench GUI"
echo "============================================"
echo ""
echo "Repo:   $REPO_DIR"
echo "Script: $SCRIPT_PATH"
echo "URL:    $URL"
echo ""

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "ERROR: launcher script not found"
  echo "$SCRIPT_PATH"
  echo ""
  read -n 1 -s -r -p "Press any key to close..."
  exit 1
fi

open "$URL" || true
bash "$SCRIPT_PATH"

echo ""
echo "Workbench stopped."
echo ""
read -n 1 -s -r -p "Press any key to close..."
