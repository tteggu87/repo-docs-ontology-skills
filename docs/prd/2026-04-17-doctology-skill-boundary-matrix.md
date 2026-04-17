---
title: "DocTology skill boundary matrix"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: design
tags:
  - doctology
  - skills
  - boundaries
  - bootstrap
  - ontology
  - graph
---

# DocTology Skill Boundary Matrix

## Purpose

Clarify what each major DocTology skill owns, what it should not own, and how the default user path should move through the stack.

## Short version

- `llm-wiki-bootstrap` = start here
- `llm-wiki-ontology-ingest` = daily path
- `lightweight-ontology-core` = advanced canonical engine
- `lg-ontology` = optional graph extension

## Canonical truth boundary

All major skills should respect this shared truth hierarchy:

1. `raw/` = immutable source input
2. `warehouse/jsonl/` = canonical structured truth
3. `wiki/` = human-facing maintained projection
4. SQLite / DuckDB / graph projection = derived and rebuildable layers

## Boundary matrix

## 1. `llm-wiki-bootstrap`

### Owns

- project-local wiki scaffold
- repo-local `AGENTS.md`
- starter `README.md`
- `raw/`, `wiki/`, `intelligence/`, `warehouse/jsonl/`, `state/`
- local helper scripts for SQLite / wiki analytics refresh

### Does not own

- long-term ontology schema semantics
- graph projection semantics
- repository-specific ingest decisions after scaffold creation
- canonical ontology mirror ownership

### User-facing role

- start here

## 2. `llm-wiki-ontology-ingest`

### Owns

- repeated ingest orchestration
- raw source -> canonical JSONL -> wiki projection workflow
- repo-local wiki refresh and meta refresh

### Does not own

- ontology schema design
- graph projection semantics
- primary bootstrap contract

### User-facing role

- daily path

## 3. `lightweight-ontology-core`

### Owns

- canonical ontology generation semantics
- claims / evidence / segments / derived edges model
- ontology mirror semantics
- retrieval support semantics

### Does not own

- repo-local wiki page taxonomy
- markdown projection rules for one vault
- bootstrap UX

### User-facing role

- advanced canonical engine

## 4. `lg-ontology`

### Owns

- graph projection artifacts
- graph comparison workflows
- optional graph-style exploration layer

### Does not own

- canonical truth
- wiki projection
- bootstrap onboarding

### User-facing role

- optional graph extension

## DuckDB boundary

Current preferred interpretation:

- `state/wiki_index.sqlite` = operational wiki index
- `state/wiki_analytics.duckdb` = bootstrap-layer local wiki analytics mirror
- `warehouse/ontology.duckdb` = ontology-core / lg ontology mirror

This means:

- bootstrap-layer DuckDB is not the canonical ontology mirror
- bootstrap-layer DuckDB should stay focused on source registry, page coverage snapshots, and audit-style inspection
- ontology-core remains the owner of ontology mirror semantics
- any future unification must be explicit and repo-wide

## Default user path

1. `llm-wiki-bootstrap`
2. `llm-wiki-ontology-ingest`
3. `lightweight-ontology-core` when deeper canonical refinement is needed
4. `lg-ontology` when graph-style exploration is justified

## Anti-patterns

Avoid these mistakes:

- treating all four skills as equal starting points
- treating wiki summaries as canonical truth
- treating bootstrap-layer DuckDB as ontology-core truth
- treating graph projection as canonical

## Recommended next step

Keep using this matrix as the active role contract unless and until a repo-wide DuckDB unification decision is explicitly adopted.
