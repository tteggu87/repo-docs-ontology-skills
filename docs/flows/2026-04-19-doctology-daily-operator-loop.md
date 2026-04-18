---
title: "Flow: DocTology daily operator loop"
status: active
created: 2026-04-19
updated: 2026-04-19
owner: "Hermes"
type: flow
tags:
  - flow
  - doctology
  - operator
  - ingest
  - review
  - promotion
---

# Flow: DocTology daily operator loop

This is the safe default daily operator loop for a **live workspace**.
It is intentionally stricter than the public reference repo posture.

## Core rule

Do work in this order:

1. `raw/` source truth
2. `warehouse/jsonl/` canonical structured truth
3. review / shadow reconcile
4. explicit human-approved wiki promotion

Do **not** let ontology output silently rewrite the wiki.

## Step 0 — Check readiness first

```bash
python3 scripts/llm_wiki.py doctor
```

Confirm at minimum:
- raw files are present
- production ingest entrypoint exists
- working tree is in an expected state
- docs/layer policy is understood

## Step 1 — Add or backfill source truth

Place new material under the appropriate `raw/` lane.
Typical cases:
- `raw/inbox/` for fresh sources
- `raw/processed/` for accepted stable snapshots
- `raw/notes/` for supporting notes

## Step 2 — Run production ingest in shadow-safe mode

```bash
python3 scripts/ontology_ingest.py \
  --root /path/to/live-workspace \
  --allow-main-repo \
  --build-graph-projection \
  --wiki-reconcile-mode shadow
```

Expected outcomes:
- canonical rows refresh under `warehouse/jsonl/`
- graph projection refreshes under `warehouse/graph_projection/`
- wiki shadow preview is produced instead of silent page rewrite

## Step 3 — Inspect shadow reconcile output

```bash
python3 scripts/llm_wiki.py reconcile-shadow --root /path/to/live-workspace
```

Review:
- affected source pages
- whether the candidate changes should remain draft-only
- whether some pages need explicit human editing instead of automation

## Step 4 — Review operator surfaces

Check:
- source coverage / review queue
- low-confidence claims
- contradiction candidates
- merge candidates
- query preview contract and fallback reasons
- bounded graph inspect only as a derived support surface

Recommended live checks:
- workbench source lane
- workbench review lane
- query preview for the current question surface

## Step 5 — Promote reviewed synthesis only

Only after review:
- update human-facing wiki pages
- save durable analyses worth keeping
- leave questionable changes in review state instead of forcing promotion

## Step 6 — Re-check health

```bash
python3 scripts/llm_wiki.py doctor
python3 scripts/llm_wiki.py status
```

The operator loop is healthy when:
- canonical truth is populated
- review queues are visible
- wiki promotion is explicit
- working-tree dirt matches intended tracked changes only

## What stays out of this loop

Do not confuse these with truth ownership:
- graph projection
- SQLite mirrors
- DuckDB mirrors
- agent-local planning folders

They may support the operator, but they do not outrank raw or canonical file truth.
