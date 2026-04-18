---
title: Log
type: meta
status: active
created: 2026-04-17
updated: 2026-04-18
---

# Log

## [2026-04-17] setup | Initialized LLM Wiki scaffold

- Created the Obsidian-first project structure
- Added `AGENTS.md`, CLI tools, templates, and meta pages

## [2026-04-17] analysis | DocTology product direction and layer boundary

- Saved a durable product-direction analysis page
- Clarified bootstrap as start-here and ingest as daily path

## [2026-04-17] analysis | DuckDB contract draft for DocTology

- Saved a draft decision memo for DuckDB contract alignment
- Captured options for single-vs-dual DuckDB and ownership boundaries

## [2026-04-17] analysis | Implemented bootstrap wiki analytics DuckDB naming

- Renamed bootstrap-layer DuckDB semantics to wiki analytics
- Kept ontology-core and lg ontology mirror semantics separate

## [2026-04-17] analysis | DocTology implementation progress

- Saved an implementation progress memo for recent bootstrap and DuckDB work
- Captured completed changes, current architecture snapshot, and remaining gaps

## [2026-04-18] analysis | DocTology Ladybug ROI and issue breakdown

- Saved a DocTology-specific Ladybug ROI and priority review in `docs/reviews/`
- Saved a GitHub-issue-style implementation breakdown in `docs/issues/`
- Added a durable wiki analysis page for DocTology Ladybug implementation priority

## [2026-04-18] implementation | Added Issue 1 bounded graph inspect panel

- Added a new bounded `/api/graph/inspect` adapter route for seeded page/source/claim graph inspect
- Added workbench graph seed helpers and a read-only GraphInspectPanel UI
- Added backend and frontend tests plus a workbench `npm test` script for graph inspect behavior

## [2026-04-18] implementation | Completed Issue 2-5 graph sidecar tranche

- Added query-preview graph hints and persisted graph context into saved analysis pages
- Enriched review and source lanes with graph-aware hints and direct drilldowns for page/source/claim contexts
- Expanded graph seed generation to include related entity/project page drilldowns from current page and source context

## [2026-04-18] benchmark | Ontology-backed graph benchmark for DocTology

- Compared the imported-corpus baseline against a separate ontology-backed benchmark sandbox.
- Generated heuristic benchmark canonical registries and rebuilt graph projection in the sandbox.
- Saved the benchmark review at `docs/reviews/2026-04-18-doctology-ontology-backed-graph-benchmark.md`.

## [2026-04-18] planning | Production ontology ingest upgrade roadmap

- Saved a GitHub-issue-style production promotion breakdown in `docs/issues/2026-04-18-doctology-production-ontology-ingest-upgrade-issue-breakdown.md`.
- Saved a durable wiki roadmap summary for the production ontology ingest upgrade path.

## [2026-04-18] implementation | Hardened production ontology ingest safeguards

- Production source-version hashing now tracks raw content only, so wiki-only edits do not create new canonical export versions.
- Production ingest now fails loudly on duplicate `raw_path` source-page mappings.
- Markdown raw preprocessing now strips frontmatter / headings / URL scaffolding before claim extraction.
- Updated Kuzu source-page mapping to remove duplicate production raw-path ownership.

## [2026-04-18] implementation | Added production ontology ingest path

- Added `scripts/ontology_registry_common.py` for shared registry helpers and safety rules.
- Added `scripts/ontology_ingest.py` for raw-first production canonical ingest with shadow wiki reconciliation preview.
- Updated workbench review surfaces with contradiction and merge candidates.
- Extended benchmark runner to compare baseline vs benchmark harness vs production.

## [2026-04-18] implementation | Completed ontology benchmark pipeline MVP

- Added `scripts/ontology_benchmark_ingest.py` for sandbox-first canonical benchmark ingest.
- Added `scripts/build_graph_projection_from_jsonl.py` and `scripts/run_ontology_graph_benchmark.py`.
- Added `tests/test_ontology_benchmark_ingest.py` and verified workbench compatibility against ontology-backed sandbox outputs.
