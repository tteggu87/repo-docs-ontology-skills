---
title: "Gap checklist: llm-wiki-bootstrap vs three-layer runtime"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: issue-breakdown
tags:
  - issues
  - llm-wiki-bootstrap
  - sqlite
  - duckdb
  - three-layer
  - gap
---

# Gap Checklist: LLM Wiki Bootstrap Vs Three-Layer Runtime

This document converts the identified support gap into concrete issue-style checkpoints.

## Short verdict

The current repository has a real gap:

- repo philosophy and runtime references now describe a three-layer model
- `llm-wiki-bootstrap` still generates a lighter ontology-ready scaffold
- SQLite, DuckDB, and drift helpers do not yet align with the bootstrap output paths

---

## Issue 1 — Unify canonical directory contract

### Goal

Choose one canonical path contract for the bootstrap and all follow-on runtime helpers.

### Why

The current codebase mixes these incompatible surfaces:

- `wiki/concepts`, `wiki/entities`, `wiki/sources`
- `wiki/pages/...`
- `wiki/exports/...`
- `warehouse/jsonl/...`
- `wiki/state/...`
- `warehouse/ontology.duckdb`

### Acceptance criteria

- one path contract is explicitly marked canonical
- bootstrap output matches that contract
- SQLite and DuckDB helpers read from that contract without translation ambiguity

---

## Issue 2 — Resolve page-path mismatch

### Goal

Align page storage used by the bootstrap with page storage expected by the SQLite helper.

### Why

`reindex_sqlite_operational.py` currently scans `wiki/pages/...`, while the bootstrap creates pages directly under:

- `wiki/concepts/`
- `wiki/entities/`
- `wiki/people/`
- `wiki/projects/`
- `wiki/timelines/`
- `wiki/analyses/`
- `wiki/sources/`

### Acceptance criteria

- either bootstrap creates `wiki/pages/...` or SQLite helper reads the generated directories directly
- no runtime helper points at a directory the scaffold never creates

---

## Issue 3 — Resolve canonical export mismatch

### Goal

Align DuckDB refresh inputs with the current canonical machine-truth surface.

### Why

Current ontology-ready bootstrap establishes `warehouse/jsonl/...` as canonical structured truth, but the DuckDB refresh helper still reads:

- `wiki/sources/manifests/source_manifest.jsonl`
- `wiki/exports/claims.jsonl`
- `wiki/exports/entities.jsonl`
- `wiki/exports/relations.jsonl`
- `wiki/exports/ingest_runs.jsonl`

### Acceptance criteria

- one canonical export surface is chosen
- DuckDB helper reads from the chosen surface
- generated README and `AGENTS.md` describe the same truth owner

---

## Issue 4 — Resolve state DB location mismatch

### Goal

Choose stable locations for SQLite and DuckDB outputs.

### Why

Current references disagree:

- SQLite helper writes `wiki/state/wiki_index.sqlite`
- bootstrap three-layer references mention `wiki/state/analytics.duckdb`
- `lightweight-ontology-core` mirrors into `warehouse/ontology.duckdb`

### Acceptance criteria

- SQLite path is explicitly frozen
- DuckDB path is explicitly frozen
- rebuild docs, helpers, and bootstrap references all use the same paths

---

## Issue 5 — Decide whether bootstrap should ship runtime DB scaffolding

### Goal

Make the product boundary explicit.

### Why

Right now the repo sends mixed signals:

- docs increasingly describe SQLite and DuckDB as part of the mature model
- bootstrap skill still describes them as follow-on guidance only

### Acceptance criteria

- explicit decision: bootstrap-only, bootstrap-plus-runtime-ready, or bootstrap-plus-upgrade-step
- docs no longer imply a stronger default than the code actually ships

---

## Issue 6 — Make drift verification valid for scaffolded repos

### Goal

Ensure `verify_three_layer_drift.py` can produce meaningful results for a fresh scaffold.

### Why

The current drift checker expects paths and artifacts that the scaffold does not generate.

### Acceptance criteria

- drift checker knows the chosen canonical paths
- running drift verification on a freshly scaffolded repo yields an expected result rather than false failures or silent irrelevance

---

## Issue 7 — Add end-to-end bootstrap validation

### Goal

Test the real upgrade path, not only file existence.

### Why

Current validation is mostly scaffold existence validation. It does not prove:

- bootstrap -> ingest-ready ontology paths
- bootstrap -> SQLite rebuild
- bootstrap -> DuckDB refresh
- bootstrap -> drift verification

### Acceptance criteria

- test fixture proves bootstrap output can feed the chosen SQLite helper
- test fixture proves bootstrap output can feed the chosen DuckDB helper
- drift verification passes or reports expected staged warnings

---

## Priority order

1. canonical path contract
2. page-path mismatch
3. canonical export mismatch
4. state DB location mismatch
5. bootstrap product boundary
6. drift validation
7. end-to-end tests

## Recommended disposition

- treat this as a real architecture integration gap
- do not patch docs only
- do not patch helpers only
- fix the shared contract first
