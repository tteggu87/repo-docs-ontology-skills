#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

git rm -r --cached apps/doctology-workbench/node_modules \
  apps/doctology-workbench/dist \
  apps/doctology-workbench/tsconfig.tsbuildinfo \
  apps/doctology-workbench/tsconfig.node.tsbuildinfo \
  apps/doctology-workbench/vite.config.js \
  apps/doctology-workbench/vite.config.d.ts

git add .gitignore

git commit -m "chore: remove generated workbench artifacts from git"

git status --short
