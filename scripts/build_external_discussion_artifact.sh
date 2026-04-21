#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT/dist"
OUT_FILE="$OUT_DIR/external-discussion-brief.md"

mkdir -p "$OUT_DIR"

cat >"$OUT_FILE" <<'EOF'
# External Discussion Brief

Date: 2026-04-14
Project: llm-wiki-obsidian

## Core local conclusions so far

1. This repository is best understood as:
   - Karpathy-style LLM Wiki
   - plus a canonical JSONL truth layer
   - plus repo-local operating rules and workbench boundaries

2. The current token-avoidance stack is:
   - wiki pages compress raw sources into smaller maintained surfaces
   - `wiki/_meta/index.md` helps routing
   - `warehouse/jsonl/` helps selective verification
   - current workbench Ask preview uses local search first before any LLM answer path

3. The current repository does not primarily rely on:
   - prompt caching
   - MemGPT-style virtual paging
   - automated semantic deduplication

4. Existing local recommendation about Mem0:
   - useful only as a narrow sidecar for continuity and operator memory
   - do not let it own canonical entities, claims, evidence, glossary authority, or ontology truth

5. Existing local recommendation about Vercel's compressed AGENTS/docs-index pattern:
   - relevant as a machine-oriented retrieval map
   - not a good direct replacement for the current human-readable `wiki/_meta/index.md`
   - better as a secondary compact machine index layered on top of the current wiki

## Open design question

What is the best next architectural move for this repository?

Candidates:
- A. Keep current architecture and do nothing major
- B. Add a compact machine index inspired by Vercel's compressed AGENTS/docs-index approach
- C. Add Mem0 as a narrow continuity sidecar
- D. Combine B and a small C pilot

## Constraints

- `raw/` remains immutable source truth
- `warehouse/jsonl/` remains canonical machine truth
- `wiki/` remains human-facing synthesis
- browser/frontend must not mutate canonical truth directly
- avoid unnecessary token growth and avoid replacing readable wiki surfaces with opaque machine-only compression

## Desired external discussion style

- free-form, exploratory, and creative
- challenge local assumptions where useful
- do not assume the local conclusion is correct
- distinguish:
  - what should stay human-readable
  - what can be machine-oriented
  - what belongs in continuity memory versus canonical truth
EOF

printf '%s\n' "$OUT_FILE"
