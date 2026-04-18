---
title: "Review: DocTology production ontology ingest upgrade roadmap"
status: draft
created: 2026-04-18
updated: 2026-04-18
owner: "Hermes"
type: review
tags:
  - review
  - doctology
  - ontology
  - ingest
  - production
  - rollout
---

# Review: DocTology production ontology ingest upgrade roadmap

## Summary

DocTology now has two distinct ontology ingest paths:

1. `scripts/ontology_benchmark_ingest.py`
   - benchmark harness
   - source-page heuristic based
   - sandbox-first architecture/performance validation path
2. `scripts/ontology_ingest.py`
   - production-oriented raw-first ingest path
   - preserves canonical JSONL and graph projection contracts
   - keeps wiki reconciliation in shadow mode by default

This is the intended promotion shape:
- `raw/` stays immutable source truth
- `warehouse/jsonl/` becomes production canonical structured truth
- `warehouse/graph_projection/` stays derived and read-only
- the wiki remains the human-facing synthesis layer

## Implemented production path

### New code surfaces
- `scripts/ontology_registry_common.py`
  - shared registry helpers, path safety, stable IDs, raw/source page discovery
- `scripts/ontology_ingest.py`
  - raw-first production ingest
  - span-aware messages/segments
  - entity alias normalization
  - raw-first claims + evidence linkage
  - contradiction / merge review signals
  - shadow wiki reconcile preview
- `scripts/run_ontology_graph_benchmark.py`
  - compares `baseline` vs `benchmark_harness` vs `production`
- `scripts/llm_wiki.py reconcile-shadow`
  - prints current shadow reconciliation preview

### Workbench behavior preserved
- `query_preview()` still reads canonical registries and graph hints
- `source_detail()` still reports coverage and review queue
- `review_summary()` now also surfaces:
  - `contradiction_candidates`
  - `merge_candidates`
- `graph_inspect()` continues to read bounded derived graph projection only

## Rollout plan

### Phase 0 — sandbox verification
Run production ingest in a non-main sandbox first.

```bash
python scripts/ontology_ingest.py \
  --root /path/to/DocTology-sandbox \
  --clean \
  --build-graph-projection \
  --wiki-reconcile-mode shadow
```

Verify:
- `warehouse/jsonl/*.jsonl` generated
- `warehouse/graph_projection/{nodes,edges}.jsonl` generated
- `wiki/state/ontology_reconcile_preview.json` generated
- no source pages were silently rewritten

### Phase 1 — benchmark comparison
Compare baseline vs benchmark harness vs production path.

```bash
python scripts/run_ontology_graph_benchmark.py \
  --baseline-root /path/to/DocTology \
  --sandbox-root /path/to/DocTology-benchmark-sandbox-ontology
```

Verify:
- `comparisons.query_preview`
- `comparisons.graph_inspect`
- `comparisons.review_summary`
- `comparisons.source_detail`
- `baseline`, `benchmark_harness`, and `production` all exist in artifact output

### Phase 2 — main repo shadow mode
Only after sandbox validation:

```bash
python scripts/ontology_ingest.py \
  --root /path/to/DocTology \
  --allow-main-repo \
  --build-graph-projection \
  --wiki-reconcile-mode shadow
python scripts/llm_wiki.py reconcile-shadow --root /path/to/DocTology
```

Verify:
- canonical registries refresh successfully
- graph projection refreshes successfully
- shadow preview lists affected source pages
- wiki markdown remains untouched unless a later explicit write path is added

## Verification checklist

Run all of these before calling the promotion stable:

```bash
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py -q
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_benchmark_ingest.py -q
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_workbench_graph_inspect.py -q
npm test
npm run build
/opt/homebrew/opt/python@3.14/bin/python3.14 -m py_compile \
  scripts/ontology_registry_common.py \
  scripts/ontology_ingest.py \
  scripts/run_ontology_graph_benchmark.py \
  scripts/llm_wiki.py \
  scripts/workbench/repository.py
```

## Rollback / disable path

If production ingest causes regressions:

1. stop running `scripts/ontology_ingest.py`
2. keep using `scripts/ontology_benchmark_ingest.py` for harness-only experiments
3. regenerate graph projection from the last known-good canonical JSONL if needed
4. inspect `wiki/state/ontology_reconcile_preview.json` instead of changing wiki pages
5. revert production-ingest-specific code paths if necessary without changing graph-sidecar ownership rules

## Remaining non-goals

Still intentionally not solved:
- perfect semantic extraction quality
- full multilingual canonicalization
- fully automatic wiki rewrite from ontology output
- making graph projection the truth owner
- eliminating operator review for merge / contradiction work

## Recommendation

Use the benchmark harness and production path side-by-side for now.

The safe operational default is:
- raw-first production ingest for canonical truth
- graph projection rebuild immediately after
- wiki reconciliation in `shadow` mode only
- explicit human review before any future wiki write-back automation
