---
title: "DocTology ontology-backed graph benchmark"
status: draft
created: 2026-04-18
updated: 2026-04-18
owner: "Hermes"
type: review
tags:
  - benchmark
  - doctology
  - graph
  - ontology
  - performance
---

# DocTology ontology-backed graph benchmark

## Goal

Compare the current imported-corpus baseline against an ontology-backed benchmark sandbox.

- **Baseline**: imported Playground/wiki corpus + markdown-link graph projection, canonical JSONL mostly empty
- **Ontology sandbox**: same corpus copied into a separate sandbox, plus heuristic benchmark `warehouse/jsonl/*.jsonl` and a graph projection rebuilt from canonical rows

## Sandbox

- Path: `/Users/hoyasung007hotmail.com/Documents/my_project/DocTology-benchmark-sandbox-ontology`
- JSON artifact: `benchmark_artifacts/ontology_graph_benchmark_results.json`

## Generated benchmark data

### Canonical registries generated in sandbox

- source_versions: 17
- documents: 17
- messages: 0
- entities: 51
- claims: 85
- claim_evidence: 85
- segments: 136
- derived_edges: 418

### Graph projection generated in sandbox

- nodes: 153
- edges: 673

## Baseline vs ontology summary

### Baseline
- raw total: 15
- wiki page count: 63
- graph available: True
- graph file count: 2
- warehouse counts: {"source_versions": 0, "documents": 0, "messages": 0, "entities": 0, "claims": 0, "claim_evidence": 0, "segments": 0, "derived_edges": 0}

### Ontology sandbox
- raw total: 15
- wiki page count: 63
- graph available: True
- graph file count: 2
- warehouse counts: {"source_versions": 17, "documents": 17, "messages": 0, "entities": 51, "claims": 85, "claim_evidence": 85, "segments": 136, "derived_edges": 418}

## Query benchmark

| Query | Baseline avg ms | Ontology avg ms | Baseline canonical hits | Ontology canonical hits | Baseline graph hints | Ontology graph hints |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `neo4j kuzu ladybug` | 273.26 | 279.39 | 0 | 15 | True (4 seeds) | True (5 seeds) |
| `ontology graphrag framework` | 274.12 | 284.89 | 0 | 15 | True (4 seeds) | True (5 seeds) |
| `little-crab doctology little_world` | 276.16 | 278.08 | 0 | 13 | True (4 seeds) | True (5 seeds) |

## Graph inspect benchmark

| Seed | Baseline avg ms | Ontology avg ms | Baseline mode | Ontology mode | Baseline nodes/edges | Ontology nodes/edges |
| --- | ---: | ---: | --- | --- | --- | --- |
| `page:neo4j-vs-kuzu-vs-ladybug-for-graph-truth-layer` | 34.76 | 32.55 | available | available | 8/12 | 8/12 |
| `source:source-kuzu-docs` | 30.4 | 30.57 | available | available | 8/12 | 8/12 |


## Review benchmark

- Baseline review avg ms: 350.71
- Ontology review avg ms: 361.47
- Baseline low-confidence claims: 0
- Ontology low-confidence claims: 5

## Source detail benchmark (`source-kuzu-docs`)

### Baseline
- avg ms: 28.58
- document_count: 0
- entity_count: 0
- claim_count: 0
- segment_count: 0
- review_queue_count: 0

### Ontology sandbox
- avg ms: 29.46
- document_count: 1
- entity_count: 1
- claim_count: 6
- segment_count: 8
- review_queue_count: 5

## Interpretation

1. The ontology sandbox makes `warehouse/jsonl/` non-empty and gives `source_detail()` real canonical coverage instead of zero-count placeholders.
2. Query latency increases because the workbench now scans non-empty `entities`, `claims`, and `segments` registries in addition to wiki pages.
3. Graph inspect remains bounded and stays relatively fast because the graph lane still caps nodes/edges even when the underlying graph is ontology-backed.
4. The generated canonical rows are **heuristic benchmark data**, not authoritative truth. They are suitable for performance and UX validation, not for production truth ownership.

## Recommended next step

If the goal is a more faithful ontology benchmark, replace the heuristic benchmark generator with a real ingest/export pipeline that populates canonical JSONL from raw sources, then rebuild graph projection from those canonical registries.
