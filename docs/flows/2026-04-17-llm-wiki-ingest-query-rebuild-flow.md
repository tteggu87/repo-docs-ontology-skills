---
title: "Flow draft: LLM Wiki ingest/query/rebuild"
status: draft
created: 2026-04-17
updated: 2026-04-18
owner: "Codex"
type: flow-draft
tags:
  - flow
  - llm-wiki
  - ingest
  - query
  - rebuild
---

# Flow Draft: LLM Wiki Ingest / Query / Rebuild

This document defines the expected movement between:

- file-layer canonical truth
- SQLite operational index
- DuckDB analytical warehouse

## 1. Ingest flow

## Step 1 — register source

Input:

- raw source file

Writes:

- file layer only
  - `raw/inbox/...`
  - `wiki/sources/...` source page stub
  - `wiki/_meta/index.md`
  - `wiki/_meta/log.md`

Rules:

- raw source should not be destructively overwritten
- registration is lighter than ontology-backed ingest

## Step 2 — ontology-backed extraction

Input:

- raw source
- repo-local glossary / manifests
- extraction policy

Writes:

- canonical file layer only
  - `warehouse/jsonl/source_versions.jsonl`
  - `warehouse/jsonl/messages.jsonl`
  - `warehouse/jsonl/documents.jsonl`
  - `warehouse/jsonl/entities.jsonl`
  - `warehouse/jsonl/claims.jsonl`
  - `warehouse/jsonl/claim_evidence.jsonl`
  - `warehouse/jsonl/segments.jsonl`
  - `warehouse/jsonl/derived_edges.jsonl`

Rules:

- extracted claims are not pages
- structured truth stays under `warehouse/jsonl/`
- relations must carry provenance through claims and evidence

### Current ingest implementations

There are now two distinct implementations for this step:

- `scripts/ontology_benchmark_ingest.py`
  - source-page markdown -> `source_versions/documents/messages/entities/claims/claim_evidence/segments/derived_edges`
  - benchmark harness only
  - sandbox-first by default
- `scripts/ontology_ingest.py`
  - raw-first production ingest -> `source_versions/documents/messages/entities/claims/claim_evidence/segments/derived_edges`
  - keeps graph projection contract compatible with the current workbench
  - supports `--wiki-reconcile-mode shadow` for non-destructive wiki alignment preview
- `scripts/build_graph_projection_from_jsonl.py`
  - canonical JSONL -> `warehouse/graph_projection/nodes.jsonl` + `edges.jsonl`
- `scripts/run_ontology_graph_benchmark.py`
  - baseline vs benchmark harness vs production reproduction

Important boundary:
- benchmark path is still **sandbox-first** and architecture/performance focused
- production path is **raw-first** and intended for canonical truth generation
- both paths keep graph as a **derived read-only sidecar**, not truth ownership

## Step 3 — update wiki synthesis layer

Input:

- existing wiki pages
- canonical JSONL truth

Writes:

- markdown pages under:
  - `wiki/sources/`
  - `wiki/concepts/`
  - `wiki/entities/`
  - `wiki/people/`
  - `wiki/projects/`
  - `wiki/timelines/`
  - `wiki/analyses/`

Rules:

- pages remain synthesis surfaces
- page edits should reference sources and canonical claim surfaces where useful

## Step 4 — refresh SQLite operational index

Input:

- markdown pages under `wiki/...`

Writes:

- `state/wiki_index.sqlite`

Derived outputs:

- page registry
- backlinks
- unresolved links
- page-source mappings
- aliases
- tags
- memories
- jobs

## Step 5 — refresh DuckDB analytical warehouse

Input:

- canonical JSONL truth under `warehouse/jsonl/...`

Writes:

- `state/wiki_analytics.duckdb`

Derived outputs:

- sources/chunks/claims/entities/relations mirror
- analytical inspection surfaces
- audit-oriented tables when available

## 2. Query flow

## Query path priority

1. wiki-first lookup
2. SQLite operational assists
3. canonical JSONL verification
4. DuckDB analytical inspection

## Wiki-first lookup

Use when:

- the user wants a readable answer surface
- the query is page- or summary-oriented

Reads:

- `wiki/...`

## SQLite operational assists

Use when:

- resolving backlinks
- finding unresolved links
- locating source-to-page mappings
- resolving aliases
- checking job or memory state

Reads:

- `state/wiki_index.sqlite`

## Canonical JSONL verification

Use when:

- provenance matters
- claim status matters
- relation evidence needs inspection

Reads:

- `warehouse/jsonl/documents.jsonl`
- `warehouse/jsonl/entities.jsonl`
- `warehouse/jsonl/claims.jsonl`
- `warehouse/jsonl/claim_evidence.jsonl`
- `warehouse/jsonl/segments.jsonl`
- `warehouse/jsonl/derived_edges.jsonl`

## DuckDB analytical reads

Use when:

- checking coverage or health at scale
- looking for stale or contradiction candidates
- comparing extraction quality across runs

Reads:

- `state/wiki_analytics.duckdb`

Rules:

- DuckDB should not become the primary reading surface
- analytical reads must not overwrite canonical truth directly

## 3. Rebuild flow

## SQLite rebuild

Trigger:

- page rename
- link drift
- alias changes
- damaged/missing SQLite file

Rebuild source:

- markdown pages under `wiki/...`

Output:

- fully regenerated `state/wiki_index.sqlite`

## DuckDB rebuild

Trigger:

- canonical JSONL changes
- ontology-backed ingest rerun
- analytical drift
- damaged/missing DuckDB file

Rebuild source:

- `warehouse/jsonl/...`

Output:

- fully regenerated `state/wiki_analytics.duckdb`

## 4. Failure handling

## If SQLite is lost

- file layer remains canonical
- rebuild SQLite from `wiki/...`

## If DuckDB is lost

- canonical file surfaces remain intact
- rebuild DuckDB from `warehouse/jsonl/...`

## If wiki and JSONL drift

- run drift verification
- fix canonical JSONL or wiki synthesis depending on the truth surface at fault

## 5. Guardrails

1. files remain the canonical write surface
2. SQLite remains operational and rebuildable
3. DuckDB remains analytical and rebuildable
4. source, claim, page, relation, and memory must not collapse into one object class
5. raw source should not be overwritten except by explicit policy
