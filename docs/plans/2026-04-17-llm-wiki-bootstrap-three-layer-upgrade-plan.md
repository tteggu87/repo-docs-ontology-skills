---
title: "Patch plan: upgrade llm-wiki-bootstrap for three-layer support"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: execution-plan
tags:
  - plan
  - llm-wiki-bootstrap
  - sqlite
  - duckdb
  - three-layer
  - bootstrap
---

# Patch Plan: Upgrade LLM Wiki Bootstrap For Three-Layer Support

This plan assumes the chosen design baseline is:

- `raw/` canonical source artifacts
- `wiki/` human-facing synthesis
- `warehouse/jsonl/` canonical machine-truth
- `state/` rebuildable SQLite and DuckDB state

## Strategic principle

Do not change philosophy and runtime at the same time without locking the path contract first.

Patch in this order:

1. freeze the path contract
2. align helpers to that contract
3. update the scaffold
4. add validation proving the new contract actually works

## Phase A — Freeze the shared contract

### Task A1 — ratify path design

Complete:

- confirm canonical roots: `raw/`, `wiki/`, `warehouse/jsonl/`, `intelligence/`, `state/`
- reject `wiki/pages/` as the default page root
- reject `wiki/exports/` as canonical truth

Exit condition:

- one design doc is accepted as the canonical baseline

### Task A2 — inventory all conflicting references

Complete:

- bootstrap script path assumptions
- README assumptions
- helper script assumptions
- review/checklist assumptions

Exit condition:

- every conflicting path is listed before code changes begin

## Phase B — Align helper scripts first

### Task B1 — patch SQLite helper

Implement:

- make `reindex_sqlite_operational.py` scan current wiki sections directly
- store output at `state/wiki_index.sqlite`
- stop depending on `wiki/pages/...`

Acceptance criteria:

- helper indexes pages from the scaffolded repo without manual restructuring

### Task B2 — patch DuckDB helper

Implement:

- make `refresh_duckdb_analytics.py` read from `warehouse/jsonl/...`
- normalize table loading against canonical JSONL datasets
- store output at `state/analytics.duckdb`

Acceptance criteria:

- helper can refresh DuckDB from scaffold-compatible JSONL paths

### Task B3 — patch drift checker

Implement:

- make `verify_three_layer_drift.py` inspect the canonical path set
- verify `state/wiki_index.sqlite`
- verify `state/analytics.duckdb`
- compare against real wiki and warehouse roots

Acceptance criteria:

- drift verification is meaningful on a real scaffolded repo

## Phase C — Upgrade bootstrap output

### Task C1 — add state directory

Implement:

- generate `state/` in ontology-ready bootstrap
- document the role of rebuildable DB state

Acceptance criteria:

- fresh bootstrap contains the non-canonical state root

### Task C2 — surface three-layer scripts in scaffold

Implement:

- ship or copy three-layer helper scripts into the generated repo when ontology profile is used
- ensure README mentions they are optional rebuildable helpers

Acceptance criteria:

- a user can discover the SQLite and DuckDB rebuild path from the scaffold itself

### Task C3 — align README and AGENTS

Implement:

- describe `warehouse/jsonl/` as canonical structured truth
- describe `state/` as rebuildable DB state only
- remove ambiguous wording that implies runtime support without actual generated paths

Acceptance criteria:

- generated repo docs match the real file layout

## Phase D — Prove end-to-end viability

### Task D1 — bootstrap validation fixture

Implement:

- create a temporary ontology-profile scaffold
- verify expected roots exist
- verify no obsolete path assumptions remain

Acceptance criteria:

- scaffold test passes without manual edits

### Task D2 — SQLite rebuild validation

Implement:

- create a few sample wiki pages
- run SQLite rebuild
- verify `state/wiki_index.sqlite` exists and has expected rows

Acceptance criteria:

- SQLite helper works on fresh bootstrap output

### Task D3 — DuckDB refresh validation

Implement:

- create or seed minimal canonical JSONL fixture files
- run DuckDB refresh
- verify `state/analytics.duckdb` exists and contains expected tables

Acceptance criteria:

- DuckDB helper works on fresh ontology-ready bootstrap output

### Task D4 — drift validation

Implement:

- run drift verification after successful SQLite and DuckDB generation
- ensure expected pass state or explicit staged warnings

Acceptance criteria:

- drift checker no longer encodes obsolete path assumptions

## Phase E — Cleanup and migration notes

### Task E1 — update references

Complete:

- `SKILL.md`
- README references
- three-layer references
- any old issue docs that still teach obsolete paths

### Task E2 — define migration note for older scaffolds

Complete:

- note how an existing scaffold using older assumptions should migrate
- include path remaps if needed

Acceptance criteria:

- users can upgrade old bootstrap outputs without guessing

## Recommended implementation order

1. design contract
2. SQLite helper
3. DuckDB helper
4. drift checker
5. bootstrap generator
6. generated docs
7. end-to-end tests
8. migration note

## Out of scope for this patch

- making SQLite canonical
- making DuckDB canonical
- adding mandatory vector infrastructure
- adding graph DB as part of bootstrap default
- solving all ontology ingest logic inside the bootstrap step

## Ship condition

The patch is complete only when:

- ontology bootstrap output and helper scripts share one path contract
- SQLite rebuild runs on fresh scaffold output
- DuckDB refresh runs on fresh scaffold output
- drift checker understands the same layout
- generated docs describe exactly what the scaffold really supports
