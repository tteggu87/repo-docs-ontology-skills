---
title: "PRD: LLM Wiki three-layer architecture"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: prd
tags:
  - prd
  - llm-wiki
  - architecture
  - sqlite
  - duckdb
---

# PRD: LLM Wiki Three-Layer Architecture

> Superseded for current bootstrap/runtime path decisions by:
> - `docs/prd/2026-04-17-llm-wiki-bootstrap-canonical-path-design.md`
> - `docs/plans/2026-04-17-llm-wiki-bootstrap-three-layer-upgrade-plan.md`
>
> Keep this file as historical product/design context, not as the current operational path contract.

## 1. Problem

Many LLM Wiki systems fail for one of two opposite reasons:

- they keep everything in files and gradually reinvent a weak warehouse inside ad hoc scripts
- they move too early into a database-centric architecture and lose the human-readable, human-correctable wiki surface

The system we want should:

- preserve files as canonical truth
- support fast operational queries for the wiki application
- support large-scale health, coverage, provenance, and contradiction analysis as the corpus grows

## 2. Product Thesis

The correct question is not whether markdown/yaml/jsonl should be replaced by SQLite or DuckDB.
The correct question is how to keep file-based canonical truth while layering:

1. a lightweight operational index for the app
2. a warehouse-like analytical surface for health and large-scale inspection

## 3. Core Principle

The architecture should be:

- **Files = canonical truth**
- **SQLite = operational index**
- **DuckDB = analytical warehouse**

This is not “use both databases because both are good.”
It is a strict role split.

## 4. Goals

### Primary goals

- keep markdown/yaml/jsonl as the human-readable and git-friendly source of truth
- make wiki operations fast enough for daily use
- make health and quality analysis possible at scale
- preserve rebuildability when any DB is lost or corrupted

### Secondary goals

- support agent-readable and human-correctable workflows
- keep provenance explicit
- avoid premature graph- or DB-first overdesign

## 5. Non-goals

- replacing the wiki with a database-native knowledge UI
- making DuckDB or SQLite the canonical truth owner
- hardening relation ontology too early
- treating memory, pages, claims, and source artifacts as the same semantic object

## 6. Canonical Data Model Separation

The system must keep these object classes distinct:

### A. Source

- original evidence-bearing artifact
- raw web clip, transcript, PDF text, note, chat log, meeting export, etc.
- closest layer to final evidence

### B. Claim

- extracted or curated proposition from source material
- must carry provenance and confidence

### C. Page

- maintained synthesis surface for humans and agents
- readable working surface
- not the same thing as source truth

### D. Relation

- link between entity / page / claim / source
- should start weak and become stronger only when justified

### E. Memory

- user preference, working context, operational state, agent continuity state
- should never be collapsed into canonical knowledge truth

## 7. Architecture

## 7.1 File layer (canonical truth)

Canonical file layer includes:

- markdown wiki pages
- page metadata and frontmatter
- yaml rules and policy files
- jsonl exports and append-only machine-readable artifacts
- raw or minimally transformed source material

### Why files remain canonical

- human-readable
- git-diffable
- easy to back up and migrate
- easy to patch with LLMs and humans
- durable even if operational or analytical databases fail

## 7.2 SQLite layer (operational index)

SQLite exists to support fast operational queries and stateful application behavior.

Examples:

- page registry
- backlink index
- unresolved links
- page-source mappings
- alias tables
- tags
- agent/user memory
- job state and ingest queue

SQLite is **not** the truth owner.
It is a rebuildable operational layer.

## 7.3 DuckDB layer (analytical warehouse)

DuckDB exists for large-scale analytical questions and health monitoring.

Examples:

- sources
- chunks
- claims
- entities
- claim-entity links
- relations
- page coverage snapshots
- stale or contradiction candidates
- rebuild and audit outputs

DuckDB is **not** the truth owner.
It is a rebuildable analytical layer.

## 8. Storage Format Responsibilities

### Markdown

- wiki page body
- human-facing synthesis

### YAML

- frontmatter
- page type rules
- ontology hints
- extraction policy
- routing and rule config

### JSONL

- source manifests
- claims export
- relations export
- ingestion logs
- append-only event-like artifacts

### SQLite

- fast operational lookup
- app/runtime state

### DuckDB

- warehouse queries
- statistics
- quality and health analysis

## 9. Recommended Directory Shape

```text
wiki/
  pages/
    concepts/
    entities/
    projects/

  sources/
    raw/
      web/
      notes/
      chats/
      pdf_text/
    manifests/
      source_manifest.jsonl

  schemas/
    page.schema.yaml
    claim.schema.yaml

  policies/
    AGENTS.md
    naming_rules.md
    linking_rules.md

  state/
    wiki_index.sqlite
    analytics.duckdb

  exports/
    claims.jsonl
    relations.jsonl
    entities.jsonl
```

Interpretation:

- `pages/`, `sources/`, `policies/` = human-facing surfaces
- `wiki_index.sqlite` = operational layer
- `analytics.duckdb` = analytical layer
- `exports/*.jsonl` = machine-readable, rebuildable artifacts

## 10. Initial Schema Direction

## 10.1 SQLite

Core operational tables:

- `pages`
- `page_links`
- `page_sources`
- `aliases`
- `tags`
- `memories`
- `jobs`

## 10.2 DuckDB

Core analytical tables:

- `sources`
- `chunks`
- `claims`
- `entities`
- `claim_entities`
- `relations`
- `page_coverage_snapshots`
- `audit_events`

## 11. Stage Plan

### v0 — file-first wiki surface

Scope:

- markdown pages
- yaml frontmatter
- source manifest jsonl

Questions to validate:

- does useful knowledge actually accumulate?
- are page boundaries natural?
- do naming and linking rules hold?

### v1 — SQLite operational index

Scope:

- backlinks
- unresolved link checks
- page-source mapping
- alias management
- agent memory
- job tracking

Questions to validate:

- does operating the wiki become easier?
- does navigation improve?
- does manual maintenance cost go down?

### v2 — DuckDB analytical warehouse

Scope:

- source/chunk/claim/relation warehouse
- coverage analysis
- stale and contradiction candidates
- rebuild and audit reporting

Questions to validate:

- can the wiki be audited structurally as scale increases?
- can health be measured instead of guessed?

## 12. Bad Patterns To Avoid

1. making a database the canonical truth too early
2. treating pages and claims as the same object
3. hardening relations into a strong ontology too early
4. mutating raw source aggressively
5. creating a system that cannot function or recover without its DB layers

## 13. Decision

The recommended architecture is:

- **v0:** file-based wiki first
- **v1:** SQLite operational index second
- **v2:** DuckDB analytical warehouse when scale and health demands justify it

This gives the best long-term tradeoff between:

- human readability
- operational usability
- analytical power
- recoverability

## 14. Next Design Step

The next concrete step after this PRD should be one of:

1. actual schema draft for markdown/yaml/jsonl/SQLite/DuckDB
2. ingest/query/rebuild flow diagram and contract

Preferred next step:

- **actual schema draft first**
