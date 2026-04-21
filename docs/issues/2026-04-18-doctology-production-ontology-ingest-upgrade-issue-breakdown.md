---
title: "Issue breakdown: DocTology production ontology ingest upgrade"
status: draft
created: 2026-04-18
updated: 2026-04-18
owner: "Hermes"
type: issue-breakdown
tags:
  - issues
  - doctology
  - ontology
  - ingest
  - production
  - graph
---

# Issue Breakdown: DocTology Production Ontology Ingest Upgrade

This document converts the post-benchmark promotion work into GitHub-issue-style tasks.

## Boundary

- `raw/` remains immutable source truth.
- `warehouse/jsonl/` becomes the production canonical structured truth.
- `warehouse/graph_projection/` remains a derived read-only sidecar.
- The goal is to **replace the heuristic source-page benchmark extractor with a stronger raw-first ontology ingest path** while preserving the current workbench and graph contracts where possible.
- The benchmark path stays alive as a harness until the production path proves parity or better.

## Suggested issue labels

- `enhancement`
- `ontology`
- `ingest`
- `production`
- `priority:high`
- `area:workbench` (when UI/backend consumer changes are involved)
- `area:wiki` (when wiki reconciliation changes are involved)

## Recommended order

1. Freeze production boundary + new entrypoint
2. Lock raw-first fixture corpus and tests
3. Implement raw-first document/source-version/message ingest
4. Add segment/span provenance
5. Add production entity extraction + normalization
6. Add production claim/evidence extraction + uncertainty fields
7. Surface alias/merge/contradiction review signals
8. Harden incremental rerun + supersession semantics
9. Add wiki reconciliation / shadow-write workflow
10. Verify workbench + graph projection parity and regressions
11. Record rollout docs and operator runbook

---

## Issue 1 — Freeze the production ingest boundary and add a new entrypoint

### Goal
Create a production-oriented ingest entrypoint without destroying the benchmark harness.

### Why
Right now `scripts/ontology_benchmark_ingest.py` is explicitly benchmark-only. Promotion should happen through a new production path, not by silently changing the meaning of the benchmark script.

### Files
- Create: `scripts/ontology_ingest.py`
- Create: `scripts/ontology_registry_common.py`
- Modify: `scripts/ontology_benchmark_ingest.py`
- Modify: `docs/flows/2026-04-17-llm-wiki-ingest-query-rebuild-flow.md`

### Acceptance criteria
- a new production CLI entrypoint exists: `scripts/ontology_ingest.py`
- shared JSONL ID / writer / safety helpers move into a reusable module
- `scripts/ontology_benchmark_ingest.py` stays runnable as benchmark harness
- CLI help clearly distinguishes `benchmark` vs `production` ingest
- graph remains derived; no graph-truth ownership migration is introduced

### Dependencies
- none

---

## Issue 2 — Add raw-first fixture corpus and failing contract tests

### Goal
Lock the production ingest contract against raw inputs instead of source-page summaries.

### Why
The current benchmark path extracts from `wiki/sources/*.md`. Production promotion must be test-anchored on raw material so quality work does not regress into page-summary heuristics.

### Files
- Create: `tests/test_ontology_ingest.py`
- Create: `tests/fixtures/ontology_ingest/raw/`
- Create: `tests/fixtures/ontology_ingest/wiki/`
- Modify: `tests/test_ontology_benchmark_ingest.py`

### Acceptance criteria
- fixture corpus includes at least:
  - one single-source markdown/raw pair
  - one multi-paragraph raw source with repeated entities
  - one contradictory or ambiguity-heavy source
  - one multilingual or alias-heavy source
- failing tests cover raw-first ingest, not source-page fallback
- tests define expected row shapes for `documents`, `source_versions`, `messages`, `segments`, `entities`, `claims`, and `claim_evidence`
- tests explicitly assert that source-page-only heuristics are insufficient for production mode

### Dependencies
- Issue 1

---

## Issue 3 — Implement raw-first document, source-version, and message ingest

### Goal
Build the first real production slice: canonical document / source-version / message rows from raw source material.

### Why
If the production path still begins from wiki source pages, promotion is fake. The first real cut is reading `raw/` directly and producing stable canonical rows.

### Files
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/ontology_registry_common.py`
- Modify: `tests/test_ontology_ingest.py`

### Acceptance criteria
- production ingest reads from `raw/` directly
- `documents.jsonl` and `source_versions.jsonl` are generated without depending on `wiki/sources` summaries
- `messages.jsonl` is generated from raw-source chunking
- every row has stable IDs on rerun
- `source_family_id` and `supersedes_export_version_id` semantics are preserved
- rerun without source changes produces byte-stable outputs

### Dependencies
- Issue 2

---

## Issue 4 — Add segment extraction with source spans and provenance offsets

### Goal
Upgrade segment extraction so segments point back to raw-source spans rather than only page-level text snippets.

### Why
Production reviewability depends on exact provenance. Segment rows must be traceable to raw offsets or raw-local positions.

### Files
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/ontology_registry_common.py`
- Modify: `tests/test_ontology_ingest.py`

### Acceptance criteria
- `segments.jsonl` is generated from raw messages/content
- each segment includes stable source-local provenance fields such as paragraph index, message index, or character span
- segments remain deterministic on rerun
- very short/noisy spans are filtered consistently
- evidence rows can point to a segment without losing source traceability

### Dependencies
- Issue 3

---

## Issue 5 — Implement production entity extraction and normalization

### Goal
Promote entities from page-link heuristics to raw-first canonical entities with basic normalization.

### Why
The current benchmark entities are useful for graph paths but too weak for production truth. Promotion needs stable canonical labels, aliases, and source attribution.

### Files
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/ontology_registry_common.py`
- Modify: `scripts/workbench/repository.py`
- Modify: `tests/test_ontology_ingest.py`

### Acceptance criteria
- entities can be extracted from raw content even when no matching wiki concept page exists yet
- trivial duplicates (case/punctuation/spacing variants) are merged deterministically
- entity rows preserve `aliases`, `source_document_ids`, and canonical label
- shared entities are attributed to all contributing source documents
- workbench consumers can still count entities per source without order-sensitive distortion

### Dependencies
- Issue 4

---

## Issue 6 — Implement production claim extraction and evidence linkage

### Goal
Create production-grade claim rows from raw sources with explicit evidence and uncertainty fields.

### Why
The benchmark path creates reviewable claims, but production promotion requires claims grounded in raw evidence rather than source-page section heuristics.

### Files
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/ontology_registry_common.py`
- Modify: `scripts/workbench/repository.py`
- Modify: `tests/test_ontology_ingest.py`

### Acceptance criteria
- claims are extracted from raw messages/segments, not from `Important Claims` markdown sections
- every claim links to at least one evidence row with a raw-traceable segment
- claims include explicit uncertainty metadata such as `confidence`, `review_state`, `extraction_method`, and quoted-vs-inferred distinction when available
- `source_detail()` and `review_summary()` surface non-zero production claim coverage
- rerun remains deterministic for claim IDs when source text is unchanged

### Dependencies
- Issue 5

---

## Issue 7 — Surface alias, merge, and contradiction review signals

### Goal
Expose the first production-quality review surfaces for entity merge risk and conflicting claims.

### Why
Promotion is not just better extraction; it also needs structured operator review signals. This is where the ontology layer becomes materially more useful than the benchmark MVP.

### Files
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/workbench/repository.py`
- Modify: `tests/test_ontology_ingest.py`
- Modify: `tests/test_workbench_graph_inspect.py`

### Acceptance criteria
- alias-collision or merge-candidate signals can be derived from canonical rows
- conflicting or low-confidence claims appear in review-oriented outputs
- review surfaces distinguish fact vs inference vs contradiction candidate
- additive fields or registries do not break current workbench consumers
- graph sidecar remains bounded and read-only

### Dependencies
- Issue 6

---

## Issue 8 — Harden incremental rerun, supersession, and idempotence semantics

### Goal
Make production ingest safe for repeated operation over evolving raw corpora.

### Why
A production path must survive daily reruns, partial updates, and source revisions without row duplication or unstable IDs.

### Files
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/ontology_registry_common.py`
- Modify: `tests/test_ontology_ingest.py`
- Modify: `docs/flows/2026-04-17-llm-wiki-ingest-query-rebuild-flow.md`

### Acceptance criteria
- repeated reruns without source changes produce stable registry files
- changed raw content creates a new export version and records supersession cleanly
- unchanged source families preserve canonical identity
- partial ingest runs do not corrupt unrelated registry rows
- safety guards still prevent accidental destructive writes outside intended roots

### Dependencies
- Issue 7

---

## Issue 9 — Add wiki reconciliation and shadow-write workflow

### Goal
Align wiki pages with production ontology outputs without making the first rollout destructive.

### Why
DocTology’s repo contract says the wiki and canonical ontology should stay aligned. Promotion needs a safe reconciliation path, preferably shadow/diff-first before automatic page rewrites.

### Files
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/llm_wiki.py`
- Modify: `wiki/AGENTS.md`
- Modify: `tests/test_ontology_ingest.py`
- Modify: `docs/flows/2026-04-17-llm-wiki-ingest-query-rebuild-flow.md`

### Acceptance criteria
- production ingest can run in shadow/diff mode without silently overwriting wiki pages
- source page regeneration or reconciliation is explicit and operator-visible
- affected wiki pages can be listed before write-back
- wiki-facing updates preserve source boundaries and uncertainty labels
- repo docs describe when ontology-first updates should propagate into wiki pages

### Dependencies
- Issue 8

---

## Issue 10 — Verify workbench and graph projection parity on production outputs

### Goal
Prove that the new production path preserves or improves the current workbench/graph sidecar experience.

### Why
Promotion should not regress the working graph-sidecar surfaces that were already implemented and benchmarked.

### Files
- Modify: `scripts/build_graph_projection_from_jsonl.py`
- Modify: `scripts/run_ontology_graph_benchmark.py`
- Modify: `scripts/workbench/repository.py`
- Modify: `tests/test_ontology_ingest.py`
- Modify: `tests/test_workbench_graph_inspect.py`
- Modify: `apps/workbench/src/lib/graph-inspect.test.ts`
- Modify: `apps/workbench/src/components/GraphInspectPanel.test.tsx`

### Acceptance criteria
- production registries rebuild `warehouse/graph_projection/` without contract drift
- `query_preview()`, `source_detail()`, `review_summary()`, and `graph_inspect()` all stay green on production outputs
- benchmark runner can compare `baseline` vs `benchmark harness` vs `production ingest`
- production ingest does not materially degrade bounded graph inspect latency beyond an agreed threshold
- backend tests, frontend tests, and frontend build pass

### Dependencies
- Issue 9

---

## Issue 11 — Record rollout docs, operator runbook, and promotion checklist

### Goal
Leave a production-ready operating playbook instead of a code-only implementation.

### Why
The next agent or operator should be able to run, verify, and, if needed, roll back the production ingest path without re-deriving the workflow.

### Files
- Create: `docs/issues/2026-04-18-doctology-production-ontology-ingest-upgrade-issue-breakdown.md`
- Create: `docs/reviews/2026-04-18-doctology-production-ontology-ingest-upgrade-roadmap.md`
- Create: `wiki/wiki/analyses/analysis-2026-04-18-doctology-production-ontology-ingest-upgrade-roadmap.md`
- Modify: `wiki/wiki/_meta/log.md`
- Modify: `wiki/wiki/_meta/index.md`

### Acceptance criteria
- rollout steps are documented from sandbox to main-repo shadow mode to production promotion
- verification commands are documented
- rollback / disable path is documented
- remaining non-goals are documented clearly
- future agents can discover the roadmap from wiki log and index

### Dependencies
- Issue 10

---

## Non-goals for this promotion tranche

- making `warehouse/graph_projection/` the canonical truth owner
- introducing a broad multi-repo ontology platform outside DocTology scope
- attempting perfect semantic extraction before the raw-first pipeline is stable
- silently rewriting the entire wiki from canonical outputs in one destructive pass
- replacing operator review with fully automatic claim acceptance

## Expected deliverable at the end of the tranche

At the end of these issues, DocTology should have:

1. a **real raw-first production ontology ingest path**
2. stable canonical JSONL registries under `warehouse/jsonl/`
3. preserved graph-sidecar compatibility under `warehouse/graph_projection/`
4. review surfaces for uncertainty / merge / contradiction work
5. a safe wiki reconciliation path instead of benchmark-only extraction
