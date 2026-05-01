---
title: "Current State"
status: active
source_of_truth: yes
updated: 2026-05-02
---

# Current State

## Product surfaces

- **Primary human reading surface:** `wiki/` inside the Obsidian vault
- **Canonical machine truth:** `warehouse/jsonl/`
- **Optional local sidecar workbench:** `apps/workbench/` via `scripts/workbench_api.py`
- **Current shipped frontend focus:** `Ask` lexical diagnostics plus `Wiki` reader
- **Strict semantic path:** helper-LLM compile/query over wiki, ontology, meta surfaces, and citation anchors

The workbench is additive. It does not replace the vault and it must not mutate canonical truth directly.

## Truth boundaries

1. `raw/` is immutable source truth
2. `warehouse/jsonl/` is canonical structured ontology truth
3. `wiki/` is maintained human-facing synthesis
4. `warehouse/graph_projection/` is derived and read-only
5. `intelligence/` is a contract layer, not a semantic truth layer

## Strict LLM-first semantic workflow

Semantic judgment has exactly one default path:

1. source material is ingested into source pages and citation-anchored content units
2. `scripts/wiki_graph_navigation.py` refreshes map surfaces such as MOC, link map, contradiction review, orphan review, and source coverage
3. `scripts/llm_compile_source.py` reads the source page, content units, related pages, and `meta_surfaces.yaml`-declared compile surfaces
4. compile output is saved only as a draft human-review proposal under `wiki/analyses/`
5. reviewed wiki/ontology pages become the primary reasoning surface
6. `scripts/llm_query.py` uses page metadata and query selection meta surfaces first, then reads selected page bodies for the answer step

If no helper LLM is configured, compile/query fails. Deterministic lexical preview remains diagnostics only and must not become a semantic answer path.

## Contract layer

The current YAML contract entrypoint is `intelligence/contract_index.yaml`.

Important contracts:

- `intelligence/policies/semantic_boundary.yaml`
- `intelligence/policies/proposal_lifecycle.yaml`
- `intelligence/manifests/semantic_workflows.yaml`
- `intelligence/manifests/page_policy.yaml`
- `intelligence/manifests/meta_surfaces.yaml`
- `intelligence/manifests/relation_types.yaml`
- `intelligence/manifests/registries.yaml`

These files define boundaries, policies, workflow contracts, relation vocabulary, and registry shape. They must not contain source summaries, answer drafts, or semantic claims.

## Workbench write contract

Current bounded browser-triggered actions remain intentionally narrow:

- allowed:
  - `python3 scripts/llm_wiki.py status`
  - `python3 scripts/llm_wiki.py reindex`
  - `python3 scripts/llm_wiki.py lint`
- allowed backend-gated helper flow:
  - read repo-root `wikiconfig.json` for bounded helper-model actions
  - return draft-only output without mutating canonical truth
- allowed write targets from workbench-triggered actions:
  - `wiki/_meta/log.md`
  - `wiki/_meta/index.md`
- explicitly disallowed from query/save surfaces:
  - direct browser writes to `raw/`
  - direct browser writes to `warehouse/jsonl/`
  - hidden model orchestration or browser-side API keys
  - parent or workspace config crawl for helper-model inputs

## Query workspace v1

The local Ask workspace now operates as a **repo-local lexical diagnostics surface**:

- it searches existing wiki pages first
- it surfaces related source pages and canonical registry hits
- it must show thin/empty coverage states honestly
- it must not present lexical matching as a semantic answer draft
- it must not save analysis pages from deterministic preview output
- it supports related-page navigation from Ask and the current Wiki reader

Semantic answers and durable answer saves belong to the strict LLM query workflow plus human review.

## Current validators

- `python3 scripts/validate_intelligence.py`
- `python3 scripts/validate_workbench_manifest.py`
- `python3 scripts/validate_profiles.py`
- `python3 scripts/validate_registries.py`
- `python3 -m pytest -q`

The validator suite guards the no-fallback semantic boundary, proposal lifecycle, Workbench route/policy boundaries, profile compile targets, pack manifests, queryable page policy, relation type policy shape, registry shapes, and registry references.

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
