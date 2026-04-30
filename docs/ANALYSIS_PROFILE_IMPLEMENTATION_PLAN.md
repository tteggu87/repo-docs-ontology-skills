# Analysis Profile Implementation Plan (Built-in First, Pack-Ready Later)

Updated: 2026-04-30

## Decision Summary

DocTology will **not** implement a full external ontology-pack plugin runtime in the current phase.
Instead, it will implement three built-in analysis profiles:

- `email-analysis`
- `education-analysis`
- `report-consistency-analysis`

The implementation will keep pack-ready boundaries so these profiles can be promoted to ontology-pack v1 later.

## In Scope Now

- built-in profiles declared under `intelligence/packs/<profile-id>/pack.yaml`
- common registries shared by all profiles (`content_units`, `observations`, `analysis_runs`, `analysis_findings`)
- profile manifest loader and validators
- generic md/txt ingest pipeline
- profile-specific observation and analysis writers
- wiki projection templates with standardized citation formatting

## Explicitly Out Of Scope Now

- external pack install/uninstall CLI
- pack marketplace
- dynamic plugin loading from external paths
- dependency resolver for packs
- runtime YAML executor
- hot-swap pack runtime
- arbitrary user-provided Python plugin execution

## Why This Boundary

- Hardcoded per-feature scripts create siloed ontologies and weak reuse.
- Full plugin infrastructure now would be premature and slow delivery.
- Built-in profiles plus contract/registry gives immediate practical value while preserving future migration paths.

## Promotion Criteria To Pack v1

Promote built-in profile(s) to full pack runtime only when most conditions are true:

1. multiple repositories or teams need portable pack distribution,
2. versioned pack compatibility policy is required,
3. external pack lifecycle controls are operationally necessary,
4. validator and migration tooling are stable for cross-pack evolution,
5. security model for third-party execution is explicitly approved.

## Execution Sequence (Recommended)

1. Architecture & naming decisions (Issue 1-3)
2. Common registry foundation (Issue 4-6)
3. Profile manifest and validation (Issue 7-9)
4. Generic md/txt ingest (Issue 10-15)
5. Profile analyzers (Issue 16-19)
6. Pipeline + wiki projection (Issue 20-22)
7. Fixtures + end-to-end tests (Issue 25-26)
8. Workbench support (Issue 23-24)
9. User/developer docs (Issue 27-28)

## Definition Of Done (Cross-Cutting)

- do not modify `raw/`
- keep `warehouse/jsonl/` as canonical structured truth
- keep `wiki/` human-facing synthesis oriented
- do not treat graph/retrieval output as canonical truth
- report changed files and affected registry/wiki paths
- include/refresh validator or tests as needed
- update README/AGENTS/docs where behavior contracts changed
