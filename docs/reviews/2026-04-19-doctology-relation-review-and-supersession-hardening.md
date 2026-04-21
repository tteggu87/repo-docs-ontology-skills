---
title: "Review: DocTology relation review and supersession hardening"
status: draft
created: 2026-04-19
updated: 2026-04-19
owner: "Hermes"
type: review
tags:
  - review
  - doctology
  - relations
  - supersession
  - doctor
---

# Review: DocTology relation review and supersession hardening

## Summary

This tranche hardens the next practical gap after uncertainty/save-readiness promotion:

1. relation review should be packetized instead of left as scattered low-level edges
2. supersession/version-chain drift should be explicit in source/detail and doctor surfaces

## Implemented

### 1. Relation review packets in workbench surfaces

`review_summary()` now emits `relation_review_packets` built from canonical `derived_edges.jsonl`.

Each packet carries:
- `relation_type`
- `support_status`
- `relation_state`
- `edge_count`
- `source_claim_count`
- `source_pages`
- `truth_basis_counts`
- `sample_edges`

This turns relation review into a bounded grouped surface rather than raw edge inspection.

### 2. Supersession summaries in source detail

`source_detail()` now emits:
- `supersession_summary`
- `relation_review_packets`

`supersession_summary` currently includes:
- `family_version_count`
- `superseded_version_count`
- `history_status`
- `latest_export_version_id`
- `supersedes_export_version_id`

This makes version-chain drift visible without forcing manual interpretation of raw version rows.

### 3. Doctor now reports supersession health

`llm_wiki doctor` now emits and renders:
- `supersession_health.version_count`
- `supersession_health.family_count`
- `supersession_health.multi_version_family_count`
- `supersession_health.superseded_version_count`
- `supersession_health.history_status`

Operator next steps now also point to `source_detail()` supersession summaries when version-chain history exists.

## Why this matters

The prior tranches made claim uncertainty and save-readiness more honest.
This tranche does the same for:
- relation review burden
- source/version drift visibility

That is important for a personal daily-driver system because unresolved relation drift and silent supersession chains are exactly the kind of things that make a knowledge base feel "almost trustworthy" instead of operationally trustworthy.

## Verification

Executed and passed:

```bash
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py tests/test_ontology_benchmark_ingest.py tests/test_workbench_graph_inspect.py tests/test_llm_wiki_runtime_health.py -q
npm test
npm run build
```

Observed results:
- Python: `50 passed`
- Frontend tests: `10 passed`
- Workbench build: passed

## Recommended next step

Best next tranche:

1. surface relation review packets and supersession warnings in the workbench UI directly
2. add relation-type drift thresholds / operator warnings
3. add taxonomy-candidate assist packets after relation review burden is more compressed
