---
title: "DocTology ontology benchmark pipeline implementation and benchmark"
status: active
created: 2026-04-18
updated: 2026-04-18
owner: "Hermes"
type: review
tags:
  - review
  - doctology
  - ontology
  - benchmark
  - graph
  - implementation
---

# DocTology Ontology Benchmark Pipeline Implementation And Benchmark

## Goal

Finish the remaining Method B work so DocTology has a real benchmark-only ontology ingest path:

- source-page markdown -> canonical JSONL
- canonical JSONL -> graph projection
- baseline vs ontology benchmark runner
- workbench compatibility verification

## What was implemented

### New scripts
- `scripts/ontology_benchmark_ingest.py`
  - sandbox-first benchmark ingest pipeline
  - generates:
    - `warehouse/jsonl/source_versions.jsonl`
    - `warehouse/jsonl/documents.jsonl`
    - `warehouse/jsonl/messages.jsonl`
    - `warehouse/jsonl/entities.jsonl`
    - `warehouse/jsonl/claims.jsonl`
    - `warehouse/jsonl/claim_evidence.jsonl`
    - `warehouse/jsonl/segments.jsonl`
    - `warehouse/jsonl/derived_edges.jsonl`
  - supports optional `--build-graph-projection`
  - refuses main repo root writes unless `--allow-main-repo`

- `scripts/build_graph_projection_from_jsonl.py`
  - builds `warehouse/graph_projection/nodes.jsonl`
  - builds `warehouse/graph_projection/edges.jsonl`
  - keeps graph projection as a derived read-only sidecar layer

- `scripts/run_ontology_graph_benchmark.py`
  - recreates a sandbox from the baseline corpus
  - runs ontology benchmark ingest + projection build
  - measures:
    - `query_preview()`
    - `graph_inspect()`
    - `review_summary()`
    - `source_detail()`
  - writes JSON artifact under sandbox `benchmark_artifacts/`

### Tests
- `tests/test_ontology_benchmark_ingest.py`
  - source-page -> document/source_version generation
  - rerun stability
  - YAML date serialization
  - metadata-change -> export_version change
  - main repo safety guard
  - segment generation
  - entity generation from source pages + wikilinks
  - claim + claim evidence generation
  - derived edge generation
  - graph projection build
  - workbench consumer compatibility via source detail / preview / inspect

### Issue breakdown
- `docs/issues/2026-04-18-doctology-ontology-benchmark-pipeline-issue-breakdown.md`

## Benchmark setup

### Baseline
- current imported Playground/wiki corpus in main DocTology repo
- graph projection already present
- canonical JSONL largely empty

### Ontology sandbox
- root: `/Users/hoyasung007hotmail.com/Documents/my_project/DocTology-benchmark-sandbox-ontology`
- baseline `raw/` + `wiki/` copied into sandbox
- benchmark ingest generated canonical JSONL and graph projection in sandbox

## Generated ontology sandbox data

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

## Measured benchmark results

### Query preview

| Query | Baseline avg ms | Ontology avg ms | Baseline canonical hits | Ontology canonical hits |
| --- | ---: | ---: | ---: | ---: |
| `neo4j kuzu ladybug` | 318.20 | 328.37 | 0 | 15 |
| `ontology graphrag framework` | 322.87 | 326.34 | 0 | 15 |
| `little-crab doctology little_world` | 321.28 | 324.70 | 0 | 13 |

Interpretation:
- query latency rises only slightly once canonical registries are non-empty
- query preview now surfaces real canonical registry hits instead of zero-count placeholders

### Graph inspect

| Seed | Baseline avg ms | Ontology avg ms | Baseline nodes/edges | Ontology nodes/edges |
| --- | ---: | ---: | --- | --- |
| `page:neo4j-vs-kuzu-vs-ladybug-for-graph-truth-layer` | 38.47 | 37.48 | 8/12 | 8/8 |
| `source:source-kuzu-docs` | 35.88 | 35.42 | 8/12 | 8/8 |

Interpretation:
- bounded graph inspect stays fast after ontology-backed projection
- projection shape changes, but the bounded sidecar contract still holds

### Review summary

- Baseline review avg ms: 408.45
- Ontology review avg ms: 411.86
- Baseline low-confidence claims: 0
- Ontology low-confidence claims: 5

Interpretation:
- review latency stays close to baseline
- ontology-backed claims make review surfaces materially richer

### Source detail (`source-kuzu-docs`)

#### Baseline
- avg ms: 33.48
- document_count: 0
- entity_count: 0
- claim_count: 0
- segment_count: 0
- review_queue_count: 0

#### Ontology sandbox
- avg ms: 35.09
- document_count: 1
- entity_count: 2
- claim_count: 2
- segment_count: 16
- review_queue_count: 2

Interpretation:
- source detail is no longer an empty shell in the ontology sandbox
- the benchmark ingest path gives source detail real canonical coverage and review queue state

## Compatibility verification

Verified green:
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_benchmark_ingest.py -q`
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_workbench_graph_inspect.py -q`
- `npm test`
- `npm run build`

## Design judgment

This completes the benchmark-path version of Method B.

Important boundary:
- this is still a **benchmark extractor MVP**, not production-grade authoritative ontology truth
- graph remains a **derived read-only sidecar**, not truth ownership

What is now true:
1. DocTology has a runnable benchmark-only ontology ingest path
2. workbench consumers can read its outputs
3. benchmark measurements are reproducible from a script
4. future work can upgrade extraction quality without discarding the pipeline shape

## Remaining non-goals after this implementation

Not solved here:
- production-grade entity normalization / merge
- contradiction-aware claim consolidation
- multilingual alias handling
- high-quality semantic extraction from raw sources beyond source-page heuristics

## Recommendation

Use this implemented path as the benchmark and architecture harness.

Next production-oriented step should be:
- replace the heuristic source-page extractor with a stronger real ontology ingest path
- keep the same canonical JSONL contract and graph projection builder when possible
