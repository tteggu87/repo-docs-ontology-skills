---
title: "Rebuild matrix: LLM Wiki three-layer architecture"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: rebuild-matrix
tags:
  - rebuild
  - drift
  - sqlite
  - duckdb
---

# Rebuild Matrix: LLM Wiki Three-Layer Architecture

> Superseded for current active paths by:
> - `docs/prd/2026-04-17-llm-wiki-bootstrap-canonical-path-design.md`
> - `docs/flows/2026-04-17-llm-wiki-ingest-query-rebuild-flow.md`
>
> Keep this file as historical rebuild planning context unless it is updated to the current canonical contract.

## Canonical principle

- files are canonical
- SQLite is rebuildable operational state
- DuckDB is rebuildable analytical state

## Trigger matrix

### Page content or frontmatter changed

- rebuild SQLite: yes
- refresh DuckDB: only if exports or health inputs changed

### Source manifest changed

- rebuild SQLite: yes
- refresh DuckDB: yes

### Claims / entities / relations exports changed

- rebuild SQLite: no, unless page/source mappings are affected
- refresh DuckDB: yes

### Memory or jobs changed

- rebuild SQLite: no
- refresh DuckDB: no

### SQLite missing or corrupted

- rebuild SQLite from files and manifests

### DuckDB missing or corrupted

- refresh DuckDB from manifests and exports

## Recovery rule

No operator action should require SQLite or DuckDB to remain the sole surviving copy of knowledge truth.
