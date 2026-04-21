---
title: "DocTology ontology benchmark pipeline implementation and benchmark"
status: active
created: 2026-04-18
updated: 2026-04-18
owner: "Hermes"
type: analysis
tags:
  - doctology
  - ontology
  - benchmark
  - graph
  - implementation
---

# DocTology ontology benchmark pipeline implementation and benchmark

## Goal

Finish the benchmark-path ontology ingest so DocTology can be measured as:

- source-page markdown -> canonical JSONL
- canonical JSONL -> graph projection
- baseline vs ontology benchmark

## Implemented files

- `scripts/ontology_benchmark_ingest.py`
- `scripts/build_graph_projection_from_jsonl.py`
- `scripts/run_ontology_graph_benchmark.py`
- `tests/test_ontology_benchmark_ingest.py`
- `docs/issues/2026-04-18-doctology-ontology-benchmark-pipeline-issue-breakdown.md`

## Sandbox-first rule now implemented

The benchmark ingest path is sandbox-first by default.

- main repo root writes are refused unless `--allow-main-repo`
- intended benchmark target remains a separate sandbox root
- this keeps benchmark truth and production truth from being casually mixed

## What the benchmark ingest now produces

Under `warehouse/jsonl/`:
- `source_versions.jsonl`
- `documents.jsonl`
- `messages.jsonl`
- `entities.jsonl`
- `claims.jsonl`
- `claim_evidence.jsonl`
- `segments.jsonl`
- `derived_edges.jsonl`

Under `warehouse/graph_projection/`:
- `nodes.jsonl`
- `edges.jsonl`

## Latest measured ontology sandbox outputs

- source_versions: 17
- documents: 17
- messages: 438
- entities: 27
- claims: 51
- claim_evidence: 51
- segments: 438
- derived_edges: 209
- graph nodes: 95
- graph edges: 209

## Benchmark result highlights

### Query preview
Canonical registry hits moved from zero in the baseline to non-zero in the ontology sandbox:
- `neo4j kuzu ladybug` -> 15
- `ontology graphrag framework` -> 15
- `little-crab doctology little_world` -> 13

Latency rose only slightly.

### Review
Low-confidence claims moved from 0 in the baseline to 5 in the ontology sandbox.
This means review surfaces are no longer structurally empty once canonical rows exist.

### Source detail
For `source-kuzu-docs`:
- baseline document/entity/claim/segment counts were all zero
- ontology sandbox produced:
  - document_count: 1
  - entity_count: 2
  - claim_count: 2
  - segment_count: 16
  - review_queue_count: 2

Interpretation:
- source detail now behaves like an ontology-backed operator surface rather than a placeholder shell

## Key architectural conclusion

Method B is now implemented as a **benchmark-path ontology ingest harness**.

That means:
- benchmark-only canonical truth path exists
- graph remains derived and read-only
- workbench can consume the resulting canonical rows and projection
- extraction quality can be upgraded later without discarding the pipeline shape

## Important caveat

This is **not yet production-grade authoritative ontology ingest**.

It is still:
- source-page heuristic extraction
- benchmark-oriented claim/evidence generation
- architecture/performance validation, not final truth quality

## Recommended next step after this milestone

Keep this path as the benchmark harness.
Then separately improve extraction quality while preserving:
- canonical JSONL contract
- projection builder contract
- workbench consumer compatibility
