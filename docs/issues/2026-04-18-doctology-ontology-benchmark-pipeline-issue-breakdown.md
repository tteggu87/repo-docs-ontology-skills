---
title: "Issue breakdown: DocTology ontology benchmark pipeline"
status: draft
created: 2026-04-18
updated: 2026-04-18
owner: "Hermes"
type: issue-breakdown
tags:
  - issues
  - doctology
  - ontology
  - benchmark
  - graph
---

# Issue Breakdown: DocTology Ontology Benchmark Pipeline

This document converts the remaining Method B implementation work into GitHub-issue-style tasks.

## Priority order

1. Segments extraction
2. Entities extraction
3. Claims + claim evidence extraction
4. Derived edges generation
5. Graph projection builder
6. End-to-end benchmark runner
7. Workbench compatibility pass
8. Durable docs and logs

---

## Issue 4 — Add failing tests for segment extraction

### Goal
Lock the segment extraction contract before implementation.

### Acceptance criteria
- headings are excluded
- bullet lines and paragraphs can become segments
- very short lines are filtered out
- segment IDs are stable on rerun

---

## Issue 5 — Implement `segments.jsonl` generation

### Goal
Generate canonical benchmark segments from source-page markdown.

### Acceptance criteria
- writes `warehouse/jsonl/segments.jsonl`
- each segment includes `segment_id`, `document_id`, `source_document_id`, `source_page`, `text`, `position`
- rerun does not duplicate rows

---

## Issue 6 — Add failing tests for entity extraction

### Goal
Lock entity generation for source pages and wikilink targets.

### Acceptance criteria
- source page itself yields an entity
- wikilink target pages yield entities
- duplicates are deduped
- entity IDs are stable

---

## Issue 7 — Implement `entities.jsonl` generation

### Goal
Generate benchmark entities from page identity and wikilinks.

### Acceptance criteria
- writes `warehouse/jsonl/entities.jsonl`
- source-linked entity metadata is present
- linked concept/project pages can surface in benchmark graph paths

---

## Issue 8 — Add failing tests for claims and claim evidence

### Goal
Lock extraction priority and evidence linkage.

### Acceptance criteria
- `Important Claims` wins over `Key Facts`
- `Key Facts` is fallback when claims are absent
- summary fallback exists when both sections are absent
- every claim has evidence
- all benchmark claims default to `needs_review`

---

## Issue 9 — Implement `claims.jsonl` and `claim_evidence.jsonl`

### Goal
Generate reviewable benchmark claims from source pages.

### Acceptance criteria
- writes `warehouse/jsonl/claims.jsonl`
- writes `warehouse/jsonl/claim_evidence.jsonl`
- claims include deterministic `confidence`
- `source_detail()` can see non-zero claim/evidence coverage

---

## Issue 10 — Add failing tests for `derived_edges.jsonl`

### Goal
Lock the canonical edge contract before implementation.

### Acceptance criteria
- document-to-claim edges exist
- claim-to-subject edges exist
- claim-to-object edges exist when available
- entity-to-entity related edges exist from wikilinks

---

## Issue 11 — Implement `derived_edges.jsonl`

### Goal
Generate graph-friendly canonical edges for projection build.

### Acceptance criteria
- writes `warehouse/jsonl/derived_edges.jsonl`
- duplicate edges are suppressed
- output is deterministic on rerun

---

## Issue 12 — Add failing tests for canonical graph projection build

### Goal
Lock the `warehouse/jsonl` -> `warehouse/graph_projection` contract.

### Acceptance criteria
- documents, entities, and claims become nodes
- derived edges become graph edges
- output lives under `warehouse/graph_projection/`

---

## Issue 13 — Implement `build_graph_projection_from_jsonl.py`

### Goal
Generate graph projection from canonical benchmark JSONL.

### Acceptance criteria
- writes `warehouse/graph_projection/nodes.jsonl`
- writes `warehouse/graph_projection/edges.jsonl`
- `graph_inspect()` can read the projection and return `available`

---

## Issue 14 — Add end-to-end sandbox runner support

### Goal
Run ingest + projection in one sandbox-first command.

### Acceptance criteria
- benchmark ingest can optionally trigger projection build
- sandbox root remains the default intended target
- main repo writes require explicit override

---

## Issue 15 — Add reproducible ontology graph benchmark runner

### Goal
Automate baseline-vs-ontology measurement.

### Acceptance criteria
- measures `query_preview`, `graph_inspect`, `review_summary`, `source_detail`
- writes a JSON artifact with latency stats and registry counts
- can recreate a sandbox from the baseline corpus

---

## Issue 16 — Pass workbench compatibility checks

### Goal
Ensure generated canonical rows and projection are consumable by the existing workbench.

### Acceptance criteria
- `query_preview()` shows canonical registry hits
- `source_detail()` shows non-zero coverage / review queue
- `review_summary()` can surface low-confidence claims
- `graph_inspect()` remains bounded and available
- backend tests, frontend tests, and build all pass

---

## Issue 17 — Record durable docs and benchmark results

### Goal
Leave durable markdown evidence for future agents.

### Acceptance criteria
- flow/docs/review/wiki analysis pages updated
- wiki log updated
- benchmark path, caveats, and measured deltas recorded

---

## Out of scope for this tranche

- production-grade ontology extraction quality tuning
- contradiction resolution automation
- multilingual entity canonicalization
- full dedupe/merge engine
- making graph the canonical truth owner in DocTology
