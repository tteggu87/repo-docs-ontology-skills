---
title: "Design: canonical path contract for llm-wiki-bootstrap three-layer support"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: design
tags:
  - design
  - llm-wiki-bootstrap
  - sqlite
  - duckdb
  - three-layer
  - paths
---

# Design: Canonical Path Contract For LLM Wiki Bootstrap Three-Layer Support

## Goal

Define one path model that:

- keeps files canonical
- supports ontology-ready bootstrap by default
- allows SQLite to remain operational only
- allows DuckDB to remain analytical only
- matches the repo's current philosophy

## Design choice

Use the existing ontology-ready bootstrap layout as the canonical file contract.

### Canonical surfaces

- `raw/` = immutable source material
- `wiki/` = human-facing maintained synthesis
- `intelligence/` = repo-local glossary and manifests
- `warehouse/jsonl/` = canonical structured machine-truth

### Rebuildable state surfaces

- `state/wiki_index.sqlite` = operational SQLite index
- `state/analytics.duckdb` = analytical DuckDB mirror

## Why this choice

This preserves the most coherent existing direction:

1. bootstrap already creates `raw/`, `wiki/`, `intelligence/`, and `warehouse/jsonl/`
2. `AGENTS.md` already teaches `warehouse/jsonl/` as canonical structured truth
3. `lightweight-ontology-core` already treats canonical JSONL as truth and DuckDB as mirror
4. the file-first philosophy remains intact

## Recommended canonical layout

```text
<repo>/
  AGENTS.md
  README.md
  intelligence/
    glossary.yaml
    manifests/
      actions.yaml
      datasets.yaml
  raw/
    inbox/
    processed/
    assets/
    notes/
  scripts/
    llm_wiki.py
    reindex_sqlite_operational.py
    refresh_duckdb_analytics.py
    verify_three_layer_drift.py
  state/
    wiki_index.sqlite
    analytics.duckdb
  templates/
    source_page_template.md
    llm-wiki-three-layer/
      sqlite_operational.schema.sql
      duckdb_analytical.schema.sql
  warehouse/
    jsonl/
      documents.jsonl
      entities.jsonl
      claims.jsonl
      claim_evidence.jsonl
      segments.jsonl
      derived_edges.jsonl
      messages.jsonl
  wiki/
    _meta/
      dashboard.md
      index.md
      log.md
    analyses/
    concepts/
    entities/
    people/
    projects/
    sources/
    timelines/
```

## Key rulings

### 1. Do not introduce `wiki/pages/`

Reason:

- the current wiki layout is already human-friendly
- `wiki/concepts`, `wiki/entities`, and peers are clearer than a second `pages/` nesting level
- changing the bootstrap to `wiki/pages/...` would force all current docs and user expectations to shift

Decision:

- SQLite should adapt to the current wiki directory layout
- not the other way around

### 2. Do not use `wiki/exports/` as canonical structured truth

Reason:

- current repo language now treats `warehouse/jsonl/` as canonical
- `wiki/exports/` sounds like a derivative output surface
- keeping both as peers creates ambiguity

Decision:

- `warehouse/jsonl/` is canonical
- any export or report layer should be derived from it

### 3. Keep DBs outside canonical file surfaces

Reason:

- SQLite and DuckDB must stay rebuildable
- putting them under `state/` makes their non-canonical nature obvious
- this also avoids conflating them with the warehouse file layer

Decision:

- SQLite path: `state/wiki_index.sqlite`
- DuckDB path: `state/analytics.duckdb`

## Ownership matrix

- `raw/` owns source artifacts
- `warehouse/jsonl/` owns structured machine-truth
- `wiki/` owns human-facing synthesis
- `state/` owns non-canonical operational and analytical indexes
- `intelligence/` owns vocabulary, dataset roles, and action boundaries

## SQLite contract

SQLite should read from:

- `wiki/**/*.md` for maintained page state
- optionally `warehouse/jsonl/...` or `intelligence/...` only when required for operational joins

SQLite should write only:

- `state/wiki_index.sqlite`

SQLite must not become:

- source of truth
- required for cold-start readability

## DuckDB contract

DuckDB should read from:

- `warehouse/jsonl/...`
- optional derived audit logs
- optional operational events only when they are explicitly non-canonical inputs

DuckDB should write only:

- `state/analytics.duckdb`

DuckDB must not become:

- source of truth
- primary editing surface
- human reading default

## Drift verification contract

Drift verification should compare:

1. `wiki/**/*.md`
2. `warehouse/jsonl/...`
3. `state/wiki_index.sqlite`
4. `state/analytics.duckdb`

It should not expect:

- `wiki/pages/`
- `wiki/exports/`
- `wiki/sources/manifests/`

unless the repo explicitly decides to add those later as derived compatibility layers.

## Compatibility stance

Preferred stance:

- adapt helpers to the bootstrap contract
- avoid adding compatibility shim directories unless a real downstream consumer requires them

This keeps the surface area smaller and prevents dual-truth confusion.

## Recommendation

Adopt this path contract as the single shared design baseline for:

- bootstrap
- README
- `AGENTS.md`
- SQLite helper
- DuckDB helper
- drift checker
- future ontology ingest and operator workflows
