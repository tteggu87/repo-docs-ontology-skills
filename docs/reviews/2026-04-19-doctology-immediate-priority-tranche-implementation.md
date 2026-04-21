---
title: "Review: DocTology immediate-priority tranche implementation"
status: draft
created: 2026-04-19
updated: 2026-04-19
owner: "Hermes"
type: review
tags:
  - review
  - doctology
  - ontology
  - uncertainty
  - temporal-state
  - relation-semantics
---

# Review: DocTology immediate-priority tranche implementation

## Goal

Implement the three immediate priorities from the PDF-reflected roadmap v2 with minimum safe scope:

1. uncertainty contract promotion
2. temporal/state semantics promotion
3. relation-semantics promotion

## Implemented

### 1. Canonical claim uncertainty contract promoted

Updated `scripts/ontology_ingest.py` so canonical claim rows now carry:

- `support_status`
- `truth_basis`
- `evidence_count`
- `lifecycle_state`
- `state_updated_at`
- `temporal_scope`

Current shape:
- `truth_basis = raw_segment`
- `temporal_scope = ingest_snapshot`
- contradiction candidates promote to:
  - `support_status = disputed`
  - `lifecycle_state = contested`
- non-approved, non-contradictory claims default to:
  - `support_status = provisional`
  - `lifecycle_state = draft`

### 2. Relation semantics promoted into derived edges and graph projection

Updated `scripts/ontology_ingest.py` and `scripts/build_graph_projection_from_jsonl.py` so derived edges and graph-projection edges preserve richer relation semantics:

- `relation_type`
- `truth_basis`
- `relation_state`
- `source_claim_id`
- `relation_origin`
- `confidence`
- `support_status`
- `temporal_scope`

Current origin families:
- `claim_projection`
- `entity_aggregation`
- `contradiction_detection`

This keeps graph derived/read-only while making it semantically less shallow.

### 3. Workbench surfaces now expose the new contract

Updated `scripts/workbench/repository.py` so:

- `query_preview()` contract now includes:
  - `uncertainty.claim_hit_count`
  - `uncertainty.support_status_counts`
  - `uncertainty.truth_basis_counts`
  - `uncertainty.lifecycle_state_counts`
  - `temporal_scope.dominant_scope`
  - `temporal_scope.counts`
- draft answers now mention:
  - claim support standing
  - truth basis standing
  - dominant temporal scope
- `review_summary()` low-confidence / contradiction items now include:
  - `support_status`
  - `truth_basis`
  - `lifecycle_state`
  - `temporal_scope`
  - `evidence_count` (low-confidence lane)
- `source_detail()` now includes:
  - `knowledge_state_summary`
  - `coverage.derived_edge_count`
  - enriched `review_queue` fields
  - `relation_type_counts`

## Why this tranche is the right size

This change does **not** implement a full probabilistic ontology engine.
It instead upgrades the current canonical/runtime contract so future probabilistic / temporal / relation-aware features have a proper substrate.

That keeps the repo aligned with the current product boundary:
- raw-first source truth
- canonical JSONL machine-truth
- derived graph sidecar
- workbench as operator/review surface

## Verification

Executed and passed:

```bash
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py tests/test_ontology_benchmark_ingest.py tests/test_workbench_graph_inspect.py tests/test_llm_wiki_runtime_health.py -q
npm test
npm run build
```

Observed results:
- Python: `46 passed`
- Frontend tests: `10 passed`
- Workbench build: passed

## Next best tranche

Recommended next implementation tranche:

1. make uncertainty/save-readiness gates explicitly depend on support-status bands
2. surface contested/superseded lifecycle transitions more strongly in doctor/status flows
3. add bounded relation review packets and relation-type drift summaries
4. only after that, add taxonomy-candidate assist lane
