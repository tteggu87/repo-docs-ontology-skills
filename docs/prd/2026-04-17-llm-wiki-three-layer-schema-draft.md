---
title: "Schema draft: LLM Wiki three-layer architecture"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: schema-draft
tags:
  - schema
  - llm-wiki
  - sqlite
  - duckdb
  - jsonl
  - yaml
---

# Schema Draft: LLM Wiki Three-Layer Architecture

This document translates the three-layer PRD into concrete storage contracts.

## 1. Canonical file-layer contract

## 1.1 Directory contract

```text
wiki/
  pages/
    concepts/
    entities/
    people/
    projects/
    timelines/
    analyses/
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
    relation.schema.yaml
  policies/
    AGENTS.md
    naming_rules.md
    linking_rules.md
    extraction_policy.yaml
    routing_policy.yaml
  exports/
    claims.jsonl
    relations.jsonl
    entities.jsonl
    ingest_runs.jsonl
  state/
    wiki_index.sqlite
    analytics.duckdb
```

## 1.2 Markdown page frontmatter draft

```yaml
---
page_id: page-concept-graph-rag
title: Graph RAG
page_type: concept
status: active
created_at: 2026-04-17
updated_at: 2026-04-17
aliases:
  - graph retrieval augmented generation
source_ids:
  - src-web-2026-04-17-001
tags:
  - retrieval
  - graph
canonical_claim_ids:
  - clm-2026-04-17-001
---
```

### Required fields

- `page_id`
- `title`
- `page_type`
- `status`
- `created_at`
- `updated_at`

### Optional fields

- `aliases`
- `source_ids`
- `tags`
- `canonical_claim_ids`

## 1.3 Page type enum draft

- `concept`
- `entity`
- `person`
- `project`
- `timeline`
- `analysis`
- `source`

## 2. Canonical object IDs

Stable IDs should exist for:

- `source_id`
- `page_id`
- `chunk_id`
- `claim_id`
- `entity_id`
- `relation_id`
- `run_id`
- `memory_id`
- `job_id`

### ID principles

1. filename is not the stable ID
2. page title is not the stable ID
3. rename must not invalidate the object
4. exported JSONL IDs and DB IDs must be aligned

## 3. JSONL contract

## 3.1 `source_manifest.jsonl`

Role:

- canonical machine-readable registry of source artifacts

Suggested row shape:

```json
{
  "source_id": "src-web-2026-04-17-001",
  "source_type": "web",
  "raw_path": "wiki/sources/raw/web/example.md",
  "canonical_uri": "https://example.com/post",
  "title": "Example source",
  "checksum": "sha256:...",
  "created_at": "2026-04-17T00:00:00Z",
  "ingest_status": "registered"
}
```

## 3.2 `claims.jsonl`

Role:

- canonical exported claims with provenance

Suggested row shape:

```json
{
  "claim_id": "clm-2026-04-17-001",
  "source_id": "src-web-2026-04-17-001",
  "chunk_id": "chk-2026-04-17-001",
  "claim_text": "DuckDB is best treated as an analytical warehouse layer.",
  "confidence": 0.82,
  "provenance_offsets": {"start": 220, "end": 310},
  "extraction_run_id": "run-extract-2026-04-17-001",
  "status": "draft"
}
```

## 3.3 `relations.jsonl`

Role:

- canonical exported relation rows

Suggested row shape:

```json
{
  "relation_id": "rel-2026-04-17-001",
  "source_entity_id": "ent-duckdb",
  "relation_type": "supports",
  "target_entity_id": "ent-warehouse",
  "evidence_claim_id": "clm-2026-04-17-001",
  "confidence": 0.77,
  "extraction_run_id": "run-extract-2026-04-17-001"
}
```

## 3.4 `entities.jsonl`

Role:

- canonical exported entities

Suggested row shape:

```json
{
  "entity_id": "ent-duckdb",
  "canonical_name": "DuckDB",
  "entity_type": "technology",
  "first_seen_source_id": "src-web-2026-04-17-001",
  "status": "active"
}
```

## 3.5 `ingest_runs.jsonl`

Role:

- append-only operational history for ingest and extraction runs

Suggested row shape:

```json
{
  "run_id": "run-ingest-2026-04-17-001",
  "phase": "extract_claims",
  "status": "success",
  "detail": "Claims extracted and export files updated.",
  "started_at": "2026-04-17T10:00:00Z",
  "finished_at": "2026-04-17T10:01:12Z"
}
```

## 4. YAML rule contract

YAML is used for:

- page frontmatter
- page type rules
- ontology hints
- extraction policy
- routing config

### `page.schema.yaml`

Should define:

- required frontmatter keys
- allowed page types
- optional arrays

### `claim.schema.yaml`

Should define:

- required exported claim fields
- confidence range
- provenance requirement

### `relation.schema.yaml`

Should define:

- allowed relation types
- required entity references
- evidence_claim_id expectation

## 5. SQLite operational schema draft

## 5.1 `pages`

Purpose:

- primary runtime registry for known pages

Suggested columns:

- `id TEXT PRIMARY KEY`
- `path TEXT UNIQUE NOT NULL`
- `title TEXT NOT NULL`
- `page_type TEXT NOT NULL`
- `updated_at TEXT NOT NULL`
- `checksum TEXT NOT NULL`

## 5.2 `page_links`

Purpose:

- backlink and unresolved-link index

Suggested columns:

- `from_page_id TEXT NOT NULL`
- `to_page_id TEXT`
- `to_link_text TEXT NOT NULL`
- `status TEXT NOT NULL`
- `created_at TEXT NOT NULL`

Recommended `status` enum:

- `resolved`
- `unresolved`

## 5.3 `page_sources`

Purpose:

- map maintained pages to supporting sources

Suggested columns:

- `page_id TEXT NOT NULL`
- `source_id TEXT NOT NULL`
- `relation_type TEXT NOT NULL`

Recommended `relation_type` enum:

- `primary`
- `supporting`
- `mentioned`

## 5.4 `aliases`

Purpose:

- alias lookup for pages and entities

Suggested columns:

- `alias_text TEXT NOT NULL`
- `target_type TEXT NOT NULL`
- `target_id TEXT NOT NULL`

Recommended `target_type` enum:

- `page`
- `entity`

## 5.5 `tags`

Purpose:

- runtime tag lookup

Suggested columns:

- `page_id TEXT NOT NULL`
- `tag TEXT NOT NULL`

## 5.6 `memories`

Purpose:

- non-canonical operational memory

Suggested columns:

- `id TEXT PRIMARY KEY`
- `memory_type TEXT NOT NULL`
- `subject TEXT`
- `content TEXT NOT NULL`
- `source_ref TEXT`
- `confidence REAL`
- `created_at TEXT NOT NULL`

Recommended `memory_type` enum:

- `preference`
- `active_context`
- `agent_note`
- `task_memory`
- `working_fact`

## 5.7 `jobs`

Purpose:

- track runtime work such as ingest and rebuilds

Suggested columns:

- `id TEXT PRIMARY KEY`
- `job_type TEXT NOT NULL`
- `status TEXT NOT NULL`
- `started_at TEXT`
- `finished_at TEXT`
- `detail TEXT`

Recommended `job_type` enum:

- `register_source`
- `reindex_sqlite`
- `refresh_duckdb`
- `extract_claims`
- `audit_health`

Recommended `status` enum:

- `queued`
- `running`
- `success`
- `failed`

## 6. DuckDB analytical schema draft

## 6.1 `sources`

Suggested columns:

- `source_id`
- `source_type`
- `uri`
- `created_at`
- `raw_checksum`

## 6.2 `chunks`

Suggested columns:

- `chunk_id`
- `source_id`
- `chunk_index`
- `text`
- `token_count`

## 6.3 `claims`

Suggested columns:

- `claim_id`
- `source_id`
- `chunk_id`
- `claim_text`
- `confidence`
- `extraction_run_id`

## 6.4 `entities`

Suggested columns:

- `entity_id`
- `canonical_name`
- `entity_type`

## 6.5 `claim_entities`

Suggested columns:

- `claim_id`
- `entity_id`
- `role`

## 6.6 `relations`

Suggested columns:

- `relation_id`
- `source_entity_id`
- `relation_type`
- `target_entity_id`
- `evidence_claim_id`
- `relation_confidence`
- `extraction_run_id`

## 6.7 `page_coverage_snapshots`

Purpose:

- derived per-page health state over time

Suggested columns:

- `page_id`
- `run_id`
- `source_count`
- `claim_count`
- `entity_count`
- `freshness_score`
- `coverage_score`
- `captured_at`

## 6.8 `audit_events`

Purpose:

- event log for health and rebuild checks

Suggested columns:

- `run_id`
- `phase`
- `status`
- `detail`
- `page_id`
- `severity`
- `created_at`

## 7. Ownership matrix

| Layer | Owns canonical truth? | Can be rebuilt? | Main role |
|---|---:|---:|---|
| Markdown/YAML/JSONL files | Yes | N/A | human-readable truth + machine-readable export |
| SQLite | No | Yes | operational index |
| DuckDB | No | Yes | analytics and health inspection |

## 8. Required commands (draft)

- `register-source`
- `extract-claims`
- `reindex-sqlite`
- `refresh-duckdb`
- `verify-drift`
- `show-page-health`
- `show-broken-links`

## 9. Open decisions

1. should `state/` be renamed to `runtime/` or `indexes/`?
2. should `analytics.duckdb` live under `state/` or `warehouse/`?
3. what exact formulas define `freshness_score` and `coverage_score`?
4. which relation types are allowed at v0 versus v1?

