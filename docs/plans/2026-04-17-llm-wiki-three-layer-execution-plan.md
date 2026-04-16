---
title: "Execution plan: LLM Wiki three-layer architecture"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: execution-plan
tags:
  - plan
  - llm-wiki
  - sqlite
  - duckdb
---

# Execution Plan: LLM Wiki Three-Layer Architecture

This plan turns the PRD, issue breakdown, schema draft, and flow draft into an execution sequence.

## Strategic principle

Do not introduce all layers at once.

Use this progression:

- **v0:** file-first wiki
- **v1:** SQLite operational index
- **v2:** DuckDB analytical warehouse

## Phase A — Freeze concepts and contracts

### Task A1 — canonical taxonomy

Complete:

- source / claim / page / relation / memory definitions
- ownership matrix

Exit condition:

- no ambiguity remains about which object class a row or file belongs to

### Task A2 — file contract

Complete:

- directory layout
- markdown/yaml/jsonl role definitions
- path examples

Exit condition:

- canonical file surfaces are stable enough to scaffold

### Task A3 — stable ID policy

Complete:

- stable id strategy for source/page/chunk/claim/entity/relation/run

Exit condition:

- filenames and titles are clearly separate from IDs

## Phase B — Build v0 proof-of-life

### Task B1 — minimal scaffold

Implement:

- file-layer directories
- frontmatter rules
- source manifest export

Exit condition:

- a user can add sources, create pages, and maintain a readable wiki without SQLite or DuckDB

### Task B2 — page/source discipline validation

Implement:

- validation for page metadata
- validation for manifest completeness
- rules preventing source/page/claim confusion

Exit condition:

- the file-only system is coherent and usable

## Phase C — Build v1 SQLite operational layer

### Task C1 — SQLite schema

Implement:

- pages
- page_links
- page_sources
- aliases
- tags
- memories
- jobs

Exit condition:

- schema is defined and local migrations or setup logic exist

### Task C2 — SQLite rebuild path

Implement:

- deterministic rebuild from files + manifests

Exit condition:

- deleting the SQLite DB does not destroy the system

### Task C3 — operational commands

Implement:

- backlink queries
- unresolved link checks
- page/source lookup
- alias lookup
- memory and job tracking

Exit condition:

- operational pain is meaningfully lower than v0

## Phase D — Build v2 DuckDB analytical layer

### Task D1 — DuckDB schema

Implement:

- sources
- chunks
- claims
- entities
- claim_entities
- relations
- page_coverage_snapshots
- audit_events

Exit condition:

- analytical tables are defined and loadable

### Task D2 — analytical refresh path

Implement:

- rebuild from canonical exports
- snapshot/event separation

Exit condition:

- deleting the DuckDB file does not destroy analytical recoverability

### Task D3 — health metrics

Implement:

- freshness_score
- coverage_score
- source_count
- claim_count
- entity_count

Exit condition:

- page health can be inspected structurally, not guessed informally

## Phase E — Drift and recovery discipline

### Task E1 — drift verification

Implement:

- file vs SQLite drift checks
- JSONL vs DuckDB drift checks
- stale rebuild detection

### Task E2 — recovery commands

Implement:

- `reindex-sqlite`
- `refresh-duckdb`
- `verify-drift`
- `show-page-health`
- `show-broken-links`

Exit condition:

- the system is operable by documented commands rather than tribal knowledge

## Definition of done

The work is complete when:

- the file-first wiki works without DB dependency
- SQLite improves operations without becoming canonical truth
- DuckDB improves health and analytics without becoming the reading surface
- rebuild and drift commands exist
- source / claim / page / relation / memory remain clearly separated

## Recommended first implementation cut

If implementation starts immediately, prioritize:

1. taxonomy and ownership matrix
2. file contract
3. stable ID policy
4. v0 proof-of-life scaffold
5. SQLite schema and rebuild

DuckDB should come only after the operational pressure is real.

