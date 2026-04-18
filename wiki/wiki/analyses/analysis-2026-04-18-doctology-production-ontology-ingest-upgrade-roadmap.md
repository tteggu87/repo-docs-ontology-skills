---
title: DocTology production ontology ingest upgrade roadmap
status: active
created: 2026-04-18
updated: 2026-04-18
type: analysis
tags:
  - doctology
  - ontology
  - ingest
  - production
  - roadmap
sources:
  - "[[analysis-2026-04-18-doctology-ontology-benchmark-pipeline-implementation-and-benchmark]]"
---

# DocTology production ontology ingest upgrade roadmap

## Summary

DocTology now has a runnable **raw-first production ontology ingest path** alongside the existing benchmark harness.

Current split:
- `scripts/ontology_benchmark_ingest.py` = benchmark harness, source-page heuristic, sandbox-first
- `scripts/ontology_ingest.py` = production-oriented raw-first ingest, canonical JSONL truth path
- `warehouse/graph_projection/` = derived read-only sidecar, not truth ownership
- `wiki/state/ontology_reconcile_preview.json` = shadow reconciliation preview, not automatic wiki overwrite

## Core operating rule

Promotion should happen through the production path while keeping the benchmark harness alive for comparison and regression detection.

Truth order stays:
1. `raw/`
2. `warehouse/jsonl/`
3. `wiki/`
4. graph projection / retrieval outputs

## Rollout sequence

### 1. Sandbox first
```bash
python scripts/ontology_ingest.py \
  --root /path/to/DocTology-sandbox \
  --clean \
  --build-graph-projection \
  --wiki-reconcile-mode shadow
```

### 2. Compare baseline vs benchmark vs production
```bash
python scripts/run_ontology_graph_benchmark.py \
  --baseline-root /path/to/DocTology \
  --sandbox-root /path/to/DocTology-benchmark-sandbox-ontology
```

### 3. Main repo shadow mode only
```bash
python scripts/ontology_ingest.py \
  --root /path/to/DocTology \
  --allow-main-repo \
  --build-graph-projection \
  --wiki-reconcile-mode shadow
python scripts/llm_wiki.py reconcile-shadow --root /path/to/DocTology
```

## Verification commands

```bash
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py -q
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_benchmark_ingest.py -q
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_workbench_graph_inspect.py -q
npm test
npm run build
```

## Review surfaces added

The production path now feeds:
- low-confidence claims
- contradiction candidates
- merge candidates
- source detail review queues
- graph projection compatibility for bounded inspect

## Non-goals still in force

- no graph-truth ownership migration
- no silent wiki rewrite
- no claim auto-approval
- no promise of perfect extraction quality yet

## Next safe default

Use the production path for canonical truth generation, but keep wiki reconciliation in `shadow` mode until explicit human-reviewed write-back rules are added.
