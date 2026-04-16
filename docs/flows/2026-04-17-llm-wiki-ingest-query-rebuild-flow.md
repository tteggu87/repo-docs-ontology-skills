---
title: "Flow draft: LLM Wiki ingest/query/rebuild"
status: draft
created: 2026-04-17
updated: 2026-04-17
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
  - `wiki/sources/raw/...`
  - `wiki/sources/manifests/source_manifest.jsonl`

Rules:

- raw source should not be destructively overwritten
- source gets a stable `source_id`

## Step 2 — extract claims and entities

Input:

- raw source
- extraction policy

Writes:

- file layer only
  - `wiki/exports/claims.jsonl`
  - `wiki/exports/entities.jsonl`
  - `wiki/exports/relations.jsonl`
  - `wiki/exports/ingest_runs.jsonl`

Rules:

- extracted claims are not pages
- relations must carry provenance through claims

## Step 3 — update page layer

Input:

- existing pages
- source manifest
- extracted claims/entities/relations

Writes:

- markdown pages under `wiki/pages/...`
- page frontmatter updates

Rules:

- pages remain synthesis surfaces
- page edits should reference sources and canonical claim ids where useful

## Step 4 — refresh SQLite operational index

Input:

- markdown pages
- source manifest
- policies

Writes:

- `wiki/state/wiki_index.sqlite`

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

- source manifest
- exports jsonl
- optional SQLite runtime events

Writes:

- `wiki/state/analytics.duckdb`

Derived outputs:

- sources/chunks/claims/entities/relations warehouse
- page coverage snapshots
- audit events

## 2. Query flow

## Query path priority

1. page-first lookup
2. SQLite operational assists
3. JSONL exact verification
4. DuckDB analytical health / audit queries

## Page-first lookup

Use when:

- the user wants a readable answer surface
- the query is page- or summary-oriented

Reads:

- `wiki/pages/...`
- page frontmatter

## SQLite operational assists

Use when:

- resolving backlinks
- finding unresolved links
- locating source-to-page mappings
- resolving aliases
- checking job or memory state

Reads:

- `wiki_index.sqlite`

## JSONL exact verification

Use when:

- provenance matters
- claim status matters
- relation evidence needs inspection

Reads:

- `claims.jsonl`
- `relations.jsonl`
- `entities.jsonl`
- `source_manifest.jsonl`

## DuckDB analytical reads

Use when:

- checking page health at scale
- looking for stale or contradiction candidates
- comparing extraction quality across runs

Reads:

- `analytics.duckdb`

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

- markdown pages
- frontmatter
- source manifest
- policies

Output:

- fully regenerated `wiki_index.sqlite`

## DuckDB rebuild

Trigger:

- export schema changes
- extraction rerun
- analytical drift
- damaged/missing DuckDB file

Rebuild source:

- source manifest
- claims/entities/relations exports
- ingest run logs
- optional SQLite events if required for ops analysis

Output:

- fully regenerated `analytics.duckdb`

## 4. Failure handling

## If SQLite is lost

- file layer remains canonical
- rebuild SQLite from files and manifests

## If DuckDB is lost

- file layer and JSONL exports remain canonical
- rebuild DuckDB from manifests and exports

## If exports drift from pages

- run drift verification
- re-extract or re-export before analytical refresh

## 5. Guardrails

1. files remain the canonical write surface
2. SQLite remains operational and rebuildable
3. DuckDB remains analytical and rebuildable
4. source, claim, page, relation, and memory must not collapse into one object class
5. raw source should not be overwritten except by explicit policy

