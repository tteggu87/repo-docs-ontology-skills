---
title: "Issue breakdown: LLM Wiki three-layer architecture"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: issue-breakdown
tags:
  - issues
  - llm-wiki
  - architecture
  - sqlite
  - duckdb
---

# Issue Breakdown: LLM Wiki Three-Layer Architecture

This document converts the architecture proposal into GitHub-issue-style work items.

---

## Issue 1 — Define canonical object taxonomy

### Goal
Lock in the top-level semantic split between:

- source
- claim
- page
- relation
- memory

### Why
If these object types are mixed, provenance and trust contracts will collapse.

### Deliverables

- one canonical taxonomy doc
- one ownership matrix
- one glossary update

### Acceptance criteria

- every object class has a one-sentence definition
- every object class has an allowed-write surface
- pages and claims are explicitly separated
- memory is explicitly marked non-canonical

---

## Issue 2 — Define file-layer directory contract

### Goal
Freeze the file-layer layout for:

- pages
- sources
- manifests
- policies
- schemas
- exports

### Why
The file layer is the canonical truth and must be readable, stable, and rebuildable.

### Deliverables

- directory contract doc
- naming rules
- path examples

### Acceptance criteria

- canonical file paths are documented
- source/page/policy/export surfaces are not conflated
- path naming examples exist

---

## Issue 3 — Define markdown + yaml contract

### Goal
Specify what belongs in markdown body versus YAML frontmatter.

### Why
Without this, page metadata will drift into body text or arbitrary sidecars.

### Deliverables

- page frontmatter schema draft
- page type rules
- example pages

### Acceptance criteria

- required frontmatter keys are documented
- page body vs metadata boundaries are explicit
- at least one example per main page type exists

---

## Issue 4 — Define JSONL export contract

### Goal
Specify where JSONL is used and what counts as canonical export versus event log.

### Why
JSONL should be used for machine-readable append-friendly artifacts, not as an undifferentiated dump surface.

### Deliverables

- source manifest spec
- claims export spec
- relations export spec
- ingestion log spec

### Acceptance criteria

- every JSONL file has a declared role
- append-only versus replaceable exports are distinguished
- JSONL <-> DuckDB relationship is documented

---

## Issue 5 — Design SQLite operational schema

### Goal
Define the operational index schema for wiki runtime behavior.

### Tables

- pages
- page_links
- page_sources
- aliases
- tags
- memories
- jobs

### Acceptance criteria

- each table has a key, purpose, and ownership rule
- unresolved/resolved link state is supported
- memory_type and job_type enums are proposed
- schema is clearly marked rebuildable from canonical surfaces plus runtime events

---

## Issue 6 — Design DuckDB analytical schema

### Goal
Define the analytical warehouse schema for coverage, health, and provenance inspection.

### Tables

- sources
- chunks
- claims
- entities
- claim_entities
- relations
- page_coverage_snapshots
- audit_events

### Acceptance criteria

- snapshot tables and event tables are separated
- confidence fields are object-specific, not overloaded
- relation provenance is explicit
- page-health metrics have draft formulas

---

## Issue 7 — Define stable ID policy

### Goal
Create a durable ID strategy across files, SQLite, and DuckDB.

### Why
Filename, title, page id, and entity id must not collapse into the same identifier.

### Acceptance criteria

- stable id rules for source/page/chunk/claim/entity/relation/run
- rename-safe policy for pages
- deterministic ID generation guidance where appropriate

---

## Issue 8 — Define rebuild and sync contracts

### Goal
Document how SQLite and DuckDB are rebuilt or refreshed from canonical sources.

### Why
Without explicit rebuild rules, three layers become three drift sources.

### Deliverables

- rebuild matrix
- sync matrix
- failure recovery notes

### Acceptance criteria

- file -> SQLite update rules are stated
- file/JSONL -> DuckDB refresh rules are stated
- stale index detection is defined
- recovery steps exist for SQLite loss and DuckDB loss

---

## Issue 9 — Define ingest flow

### Goal
Describe how new source material moves into the system.

### Scope

- raw source registration
- source manifest write
- claim extraction output
- page update
- SQLite reindex
- DuckDB analytical refresh

### Acceptance criteria

- ingest flow is described step by step
- ownership of each write is explicit
- raw-source mutation policy is explicit

---

## Issue 10 — Define query flow

### Goal
Describe how questions are answered across the three layers.

### Scope

- page-first lookup
- SQLite operational assists
- JSONL exact verification
- DuckDB analytical health queries

### Acceptance criteria

- query path does not promote DB to canonical truth
- page-reading surface remains primary
- analytics usage is bounded and justified

---

## Issue 11 — Define page health model

### Goal
Turn “wiki health” into an explicit operational model.

### Candidate metrics

- freshness_score
- coverage_score
- source_count
- claim_count
- entity_count
- unresolved link count
- audit severity counts

### Acceptance criteria

- each metric has a draft calculation rule
- health is represented as derived analytics, not canonical truth
- page health can be snapshotted over time

---

## Issue 12 — Define memory policy

### Goal
Separate operational memory from canonical knowledge.

### Scope

- user preference memory
- working context memory
- agent continuity memory
- task/job memory

### Acceptance criteria

- memory_type taxonomy exists
- memory storage is explicitly non-canonical
- memory retention/deletion policy is documented

---

## Issue 13 — Define relation-strength policy

### Goal
Prevent early over-hardening of ontology relations.

### Scope

- weak default relations
- stronger relations only when justified
- relation provenance and confidence

### Acceptance criteria

- initial allowed relation set is small
- hard ontology commitments are deferred
- relation confidence is tracked per relation row

---

## Issue 14 — Build v0 proof-of-life scaffold

### Goal
Create the minimal file-only version and validate that knowledge growth works.

### Acceptance criteria

- pages can accumulate naturally
- source manifests work
- naming and linking rules are usable
- no SQLite or DuckDB dependency is required for basic use

---

## Issue 15 — Build v1 SQLite operational layer

### Goal
Add the operational index after file-only viability is proven.

### Acceptance criteria

- backlinks work
- unresolved link checks work
- page/source lookup is fast
- memory and jobs can be tracked
- SQLite can be rebuilt from canonical surfaces plus runtime records

---

## Issue 16 — Build v2 DuckDB analytical layer

### Goal
Add the analytical warehouse only after operational pressure justifies it.

### Acceptance criteria

- sources/chunks/claims/relations can be analyzed at scale
- page-health snapshots exist
- stale and contradiction candidates can be queried
- DuckDB can be rebuilt from canonical exports and logs

---

## Issue 17 — Add validation and drift checks

### Goal
Ensure contracts remain aligned across file, SQLite, and DuckDB layers.

### Acceptance criteria

- validation commands exist
- schema drift is detectable
- missing exports or stale indexes are reported clearly

---

## Recommended execution order

1. Issue 1 — canonical object taxonomy
2. Issue 2 — file-layer directory contract
3. Issue 3 — markdown + yaml contract
4. Issue 4 — JSONL export contract
5. Issue 7 — stable ID policy
6. Issue 8 — rebuild and sync contracts
7. Issue 9 — ingest flow
8. Issue 10 — query flow
9. Issue 11 — page health model
10. Issue 12 — memory policy
11. Issue 13 — relation-strength policy
12. Issue 14 — v0 proof-of-life scaffold
13. Issue 5 — SQLite operational schema
14. Issue 15 — v1 SQLite operational layer
15. Issue 6 — DuckDB analytical schema
16. Issue 16 — v2 DuckDB analytical layer
17. Issue 17 — validation and drift checks

## Notes

- v0 must work before v1
- v1 must justify itself operationally before v2
- DuckDB should be introduced for health/analysis pressure, not for aesthetic completeness

