---
title: "Current State"
status: active
source_of_truth: yes
updated: 2026-05-08
---

# Current State

## Product surfaces

- **Primary human reading surface:** `wiki/` inside the Obsidian vault
- **Canonical machine truth:** `warehouse/jsonl/`
- **Optional local sidecar workbench:** `apps/workbench/` via `scripts/workbench_api.py`
- **Current shipped frontend focus:** `Ask` query preview plus `Wiki` reader

The workbench is additive. It does not replace the vault and it must not mutate canonical truth directly.

## Truth boundaries

1. `raw/` is immutable source truth
2. `warehouse/jsonl/` is canonical structured ontology truth
3. `wiki/` is maintained human-facing synthesis
4. `warehouse/graph_projection/` is derived and read-only

## Workbench write contract

Current bounded browser-triggered actions remain intentionally narrow:

- allowed:
  - `python3 scripts/llm_wiki.py status`
  - `python3 scripts/llm_wiki.py reindex`
  - `python3 scripts/llm_wiki.py lint`
- allowed backend-gated save flow:
  - persist a query preview into `wiki/analyses/`
  - append the matching `wiki/_meta/log.md` entry
  - refresh `wiki/_meta/index.md`
- allowed backend-gated helper flow:
  - read repo-root `wikiconfig.json` for bounded helper-model actions
  - return draft-only output without mutating canonical truth
- allowed write targets from workbench-triggered actions:
  - `wiki/analyses/`
  - `wiki/_meta/log.md`
  - `wiki/_meta/index.md`
- explicitly disallowed from query/save surfaces:
  - direct browser writes to `raw/`
  - direct browser writes to `warehouse/jsonl/`
  - hidden model orchestration or browser-side API keys
  - parent or workspace config crawl for helper-model inputs

## Query workspace v1

The local Ask workspace now operates as a **repo-local query preview plus bounded save loop**:

- it searches existing wiki pages first
- it surfaces related source pages and canonical registry hits
- it must show thin/empty coverage states honestly
- it may save a deterministic analysis draft through the backend into `wiki/analyses/`
- it may add bounded link-back entries on confident related wiki pages
- it supports related-page navigation from Ask and the current Wiki reader

This keeps the product useful without pretending browser-side generation is already safe or canonical.

## Operator review surfaces

The backend adapter still supports operator-facing triage data for:

- low-coverage pages in the wiki
- stale pages
- uncertainty candidates
- low-confidence or not-yet-approved claims from canonical registries
- source-local coverage counts and review queues
- backend-gated claim approve/reject actions that write only to canonical claims plus the meta log

The current shipped React frontend does not yet mount those broader operator surfaces as first-class tabs.

## Repository health policies

- duplicate page titles are lint-worthy and should be resolved or intentionally renamed
- oversized analyses are allowed temporarily, but they are now a tracked refactor target rather than invisible debt
- route-level tests are required for new workbench adapter surfaces

## Incremental ingest groundwork

The incremental ingest path now emits:

- explicit `supersedes_export_version_id` lineage
- affected canonical registry paths
- affected wiki surface paths

This is groundwork for later ingest-promotion and operator-review flows without changing the truth hierarchy.

## Configured full ingest runtime

`scripts/llm_full_ingest.py --apply` is now the minimal configured-LLM wiki
growth loop.

It keeps `scripts/llm_wiki.py ingest` as registration-only, then uses the
configured helper LLM to produce source-page synthesis, affected wiki page
updates, and proposed ontology records.

The automatic apply path may write:

- `wiki/sources/`
- affected `wiki/concepts/`, `wiki/entities/`, `wiki/people/`, `wiki/projects/`, `wiki/timelines/`, or `wiki/analyses/`
- `warehouse/jsonl/proposed_*.jsonl`
- `wiki/_meta/index.md`
- `wiki/_meta/log.md`
- `wiki/_meta/ingest_reports/`

It must fail rather than fall back when helper LLM semantic output is missing,
invalid, or unavailable. It must not modify `raw/`, create accepted truth,
delete content, rename pages, merge pages, or auto-commit.

## Closed ingest contract

`scripts/llm_wiki.py ingest` is intentionally a source-registration step, not a
complete ontology-backed ingest by itself.

A full source-processing pass should continue through:

- proposed JSONL appends under `warehouse/jsonl/`
- affected wiki source, concept, entity, person, project, timeline, or analysis pages
- `wiki/_meta/index.md` and `wiki/_meta/log.md`
- structural validation and a completion report

Deterministic scripts may check structure, provenance shape, links, indexes,
and required fields. They must not replace agent or model judgment for page
selection, claim interpretation, contradiction handling, or open-question
synthesis.

The detailed contract lives in `docs/CLOSED_INGEST_PIPELINE.md` and the
lightweight stage manifest lives in `intelligence/manifests/pipelines.yaml`.
