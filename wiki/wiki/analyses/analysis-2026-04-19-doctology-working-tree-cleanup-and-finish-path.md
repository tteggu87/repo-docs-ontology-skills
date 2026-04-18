---
title: DocTology working tree cleanup and finish path
status: active
created: 2026-04-19
updated: 2026-04-19
type: analysis
tags:
  - doctology
  - cleanup
  - knowledge-ops
  - roadmap
sources:
  - "[[analysis-2026-04-18-doctology-production-ontology-ingest-upgrade-roadmap]]"
  - "[[analysis-2026-04-18-doctology-ontology-benchmark-pipeline-implementation-and-benchmark]]"
---

# DocTology working tree cleanup and finish path

## Summary

DocTology now has enough feature breadth to look like a real knowledge-ops harness:
- bounded graph inspect
- ontology benchmark ingest
- raw-first production ingest
- passing tests/build for those recent additions

But it is not yet a finished knowledge operations system.
The main unresolved problem is not missing modules.
It is **operational boundary blur** between:
1. public reference repo
2. private live corpus workspace
3. rebuildable runtime state

## What was verified

- tests passed for recent ontology/graph/workbench paths
- frontend tests passed
- frontend build passed
- `query_preview()` returns grounded wiki/source results and graph hints
- `graph_inspect()` returns bounded neighborhoods
- main repo canonical JSONL remains effectively empty in live verification
- `source_detail()` still shows zero canonical coverage for checked sources

## Key diagnosis

### Working-tree dirt was mostly boundary dirt
Dirty paths came from:
- agent-local folders (`.codex/`, `.hermes/`)
- local corpus content (`raw/`, top-level `wiki/sources`, `wiki/analyses`, etc.)
- rebuildable state (`wiki/state`, graph projection outputs)

This means the repo is still behaving partly like a private evolving workspace.

## Highest-priority next step

### Separate the public reference repo from the live private workspace

Public DocTology should primarily track:
- code
- tests
- templates
- docs/plans/reviews
- tiny example fixtures only

Private/live workspace should own:
- real `raw/`
- real canonical `warehouse/jsonl/`
- live source pages / analyses / daily corpus growth

Rebuildable runtime state should not be tracked by default.

## Immediate follow-up sequence

### 1. Add explicit state docs
Add:
- `docs/CURRENT_STATE.md`
- `docs/LAYERS.md`
- versioning policy for tracked vs local-only vs derived artifacts

### 2. Add a real `doctor`
It should report:
- raw count
- canonical row counts
- source pages missing `raw_path`
- duplicate raw ownership
- graph readiness
- route readiness
- working-tree contamination classes

### 3. Make production ingest the daily operator default
Use the existing raw-first production path plus shadow reconcile preview as the normal operating loop on the live workspace.

## Finish definition

DocTology becomes "finished enough" as a knowledge operations system when:
1. working tree stays clean during normal use
2. public repo and live workspace are clearly separated
3. canonical truth is non-empty on the real workspace
4. review queues are part of the normal operator loop
5. wiki promotion is explicit and reviewed
6. answer surfaces disclose route/truth/fallback clearly

## Final judgment

DocTology is already a strong **reference architecture and workbench harness**.
The next step is not more architecture.
The next step is **boundary separation, doctor-grade runtime visibility, and daily operator-loop hardening**.
