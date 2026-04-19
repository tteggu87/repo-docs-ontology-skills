---
title: "Review: DocTology save-readiness and doctor/state hardening"
status: draft
created: 2026-04-19
updated: 2026-04-19
owner: "Hermes"
type: review
tags:
  - review
  - doctology
  - save-readiness
  - doctor
  - state-contract
---

# Review: DocTology save-readiness and doctor/state hardening

## Summary

This tranche hardened the immediate-priority contract from the previous uncertainty/relation/state promotion.

The key shift is:

- query/save readiness is no longer based only on coarse coverage
- doctor/status now expose claim-contract state bands directly

## Implemented

### 1. Save readiness now respects support-status bands

`query_preview()` now downgrades save readiness when in-scope claim support is not fully settled.

Current behavior:
- `blocked`
  - no direct evidence / `coverage == none`
- `review_required`
  - any in-scope claim is `disputed`
  - or any in-scope claim is `provisional`
  - or supported coverage still lacks stable supported claim backing
- `ready`
  - supported coverage + supported claim backing + no disputed/provisional bands

This prevents broad lexical coverage from being mistaken for save-safe truth.

### 2. Workbench review actions now keep derived claim state in sync

`review_claim()` now also updates:
- `support_status`
- `lifecycle_state`
- `state_updated_at`

This keeps the claim contract internally consistent after manual review actions.

### 3. `status` now reports claim-state summary

`llm_wiki status` payload/rendering now includes:
- support-status counts
- lifecycle-state counts
- dominant temporal scope

### 4. `doctor` now reports claim-contract health and a save-readiness floor

`llm_wiki doctor` now includes:
- `claim_contract_health`
  - support-status counts
  - lifecycle-state counts
  - temporal-scope counts
  - truth-basis counts
- `operator_readiness.save_readiness_floor`
  - `blocked`
  - `review_required`
  - `ready`
- next-step hints that explicitly mention disputed/provisional claim groups when present

## Why this matters

The previous tranche gave claims and relations richer semantics.
This tranche makes those semantics operational:

- the ask surface becomes more honest about when save is safe
- the operator surfaces become more explicit about why the repo is not yet save-ready

That closes an important trust gap between ontology structure and personal daily-use workflow.

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

Best next tranche after this one:

1. surface claim-contract health in workbench doctor cards / Ask UI
2. add relation-review packets and relation-type drift summaries
3. make source-detail and review-summary explicitly highlight contested transitions and supersession drift
4. then start the bounded taxonomy-candidate assist lane
