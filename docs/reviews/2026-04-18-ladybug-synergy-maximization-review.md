---
title: DocTology Ladybug synergy maximization review
date: 2026-04-18
status: active
source_of_truth: no
---

# DocTology Ladybug synergy maximization review

## Scope

This memo records the current recommendation for how `DocTology` should use Ladybug most effectively relative to:

- `DocTology`
- `little-crab`
- `little_world`

Working comparison assumption for this review:
- treat `Ladybug` and `Kuzu` as effectively the same embedded graph-runtime family unless later evidence proves a meaningful difference
- prefer discussing role fit over micro-differences in engine branding

## Grounded current state

Checked local signals show:

- `scripts/workbench/repository.py`
  - already treats `warehouse/graph_projection/` as a bounded graph surface
  - has strong review and query-preview surfaces
  - includes `review_summary()`, `query_preview()`, `save_query_analysis()`, and `draft_source_summary()`
- `python3 scripts/workbench/server.py --route /api/workbench/summary`
  - current checked-in corpus is thin
  - `graph_projection.available: false`
  - warning includes `graph_projection_empty`
- wiki product-direction docs state:
  - graph stays optional
  - canonical structured truth remains `warehouse/jsonl/`
  - SQLite / DuckDB / graph remain derived layers

Interpretation:
- `DocTology` is not the right place to make Ladybug the core ontology runtime
- `DocTology` is the best place to make Ladybug useful to humans through review and workbench surfaces

## Recommended role for Ladybug in DocTology

## Short verdict

In `DocTology`, Ladybug should be maximized as a **read-only graph workbench sidecar**.

It should strengthen the workbench, not redefine truth ownership.

## What Ladybug should own here

### 1. Graph inspect surface in the workbench
Ladybug should back graph views such as:
- selected page neighborhood
- selected claim provenance path
- selected source to entity/project subgraph
- related concept/entity inspection

### 2. Review-summary enrichment
Ladybug should enrich, not replace, review surfaces like:
- oversized pages with structural neighborhood hints
- low coverage pages with missing-link context
- uncertainty candidates with graph-gap context
- stale pages with nearby updated clusters
- low-confidence claims with nearby supporting/contradicting structures

### 3. Query-preview side context
For `query_preview()` and saved analyses, Ladybug should provide bounded additions such as:
- key linked entities
- contradiction path exists / does not exist
- timeline path exists / does not exist
- small neighborhood summaries

### 4. Human-facing graph panel
The graph panel should be:
- optional
- seed-based
- bounded
- explainable
- page-first, not graph-first

## What DocTology should NOT do with Ladybug

- do not promote Ladybug to canonical truth owner
- do not move ontology mutation/write authority into the graph shell
- do not make graph the homepage or product face
- do not absorb little-crab's ontology-core role into the workbench layer
- do not replace review/query surfaces with graph-only UX

## Highest-value cross-repo synergy

If the nearby repos are used together, `DocTology` should contribute:

### From little-crab
- graph truth read-adapter consumption
- provenance/path-oriented ontology answers
- graph-backed semantic inspection

### From little_world
- bounded graph operator summaries
- graph-aware analysis/save-back patterns
- “graph as operational aid, not canonical truth” communication discipline

## Final recommendation

Use `DocTology` as the portfolio's **human-facing Ladybug surface**.

Best phrase for this repo:
- pages remain primary
- review remains primary
- graph becomes the best secondary instrument

That is where Ladybug creates the most value in DocTology without collapsing its wiki-first identity.
