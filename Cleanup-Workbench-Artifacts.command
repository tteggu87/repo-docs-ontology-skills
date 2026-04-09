#!/bin/bash
set -euo pipefail

REPO_DIR="/Users/hoyasung007hotmail.com/Documents/my_project/DocTology"
SCRIPT_PATH="$REPO_DIR/scripts/cleanup_workbench_artifacts.sh"

cd "$REPO_DIR"

clear
echo "============================================"
echo " DocTology Workbench Artifact Cleanup"
echo "============================================"
echo ""
echo "Repo: $REPO_DIR"
echo "Script: $SCRIPT_PATH"
echo ""

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "ERROR: cleanup script not found"
  echo "$SCRIPT_PATH"
  echo ""
  read -n 1 -s -r -p "Press any key to close..."
  exit 1
fi

bash "$SCRIPT_PATH"

echo ""
echo "============================================"
echo " Cleanup complete"
echo "============================================"
echo ""
read -n 1 -s -r -p "Press any key to close..."
