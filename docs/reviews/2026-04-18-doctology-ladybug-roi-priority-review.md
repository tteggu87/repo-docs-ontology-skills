---
title: "Review: DocTology Ladybug ROI, difficulty, and implementation priority"
status: draft
created: 2026-04-18
updated: 2026-04-18
owner: "Hermes"
type: review
tags:
  - review
  - doctology
  - ladybug
  - graph
  - roi
  - priority
---

# Review: DocTology Ladybug ROI, Difficulty, And Implementation Priority

## Question

- If Ladybug is attached to `DocTology`, where does it create the highest value?
- What should be implemented first?
- How does `DocTology` compare against `little_world` and `little-crab` in implementation difficulty and expected payoff?

## Grounded inputs used for this review

### Current local DocTology state
- `python3 scripts/workbench/server.py --route /api/workbench/summary`
  - `graph_projection.available: false`
  - warning includes `graph_projection_empty`
  - current corpus is still thin
- `scripts/workbench/repository.py`
  - already has strong bounded read/review surfaces:
    - `review_summary()`
    - `query_preview()`
    - `save_query_analysis()`
    - `draft_source_summary()`
- project wiki notes:
  - `analysis-2026-04-17-doctology-product-direction.md`
  - `analysis-2026-04-17-doctology-implementation-progress.md`

### Cross-repo comparison assumptions already established
- `little_world`
  - Ladybug is already live and operationally ready as a derived graph runtime
- `little-crab`
  - Ladybug is architecturally central, but local operability is currently less stable on this machine
- working comparison assumption:
  - treat `Ladybug` and `Kuzu` as effectively the same embedded graph-runtime family unless later evidence proves a meaningful difference

## Short verdict

For **immediate implementation ROI**, the current ranking remains:

1. `little_world`
2. `DocTology`
3. `little-crab`

That means `DocTology` is **not** the cheapest place overall to push Ladybug, but it is the **best next surface-first target** if the goal is to make graph capability visible to humans quickly without destabilizing truth ownership.

## Why DocTology is worth doing now anyway

### Strong reasons
1. **Low-to-medium implementation difficulty**
   - graph can remain read-only and sidecar-only
   - no need to redesign canonical truth
   - no need to let graph own ingest or ontology writes
2. **High user-facing visibility**
   - the workbench is already the best place to expose graph context to humans
3. **Good fit with current product direction**
   - product docs already position graph as optional and derived
   - Ladybug can strengthen that optional workbench layer without philosophy drift

### Limiting factor
The main limiter is not code shape but **corpus thinness**.
Even a good graph sidecar will look weak if the repo has:
- no raw corpus
- no populated canonical JSONL
- no graph projection artifacts

So graph work should be paired with at least a minimal non-empty graphable sample corpus.

## Recommended DocTology role for Ladybug

Ladybug should be attached as a **read-only graph workbench sidecar**, not as a truth owner.

### Best-fit functions
1. graph inspect panel in the workbench
2. review-summary enrichment
3. query-preview graph hints
4. saved analysis pages with bounded graph context

### Functions to avoid
- graph-owned canonical mutation
- graph-first homepage
- ontology-core write workflows inside the workbench
- replacing the wiki/page/review surface with graph-only UX

## ROI analysis by candidate function inside DocTology

### 1. Graph inspect panel
**Difficulty:** medium
**Effect:** high
**ROI:** highest inside DocTology

Why:
- the frontend already has a graph surface concept
- the workbench summary already exposes graph projection availability
- a seed-based graph inspect panel creates immediate visible value

### 2. Query preview graph hints
**Difficulty:** low-to-medium
**Effect:** medium-high
**ROI:** high

Why:
- `query_preview()` already exists
- adding bounded graph context is incremental, not architectural
- easy to keep page-first rather than graph-first

### 3. Review-summary enrichment with graph context
**Difficulty:** medium
**Effect:** medium-high
**ROI:** high

Why:
- `review_summary()` already computes the right categories
- graph helps explain *why* low coverage / uncertainty / staleness matters
- strong operator value without changing truth ownership

### 4. Save-analysis graph context blocks
**Difficulty:** low
**Effect:** medium
**ROI:** medium-high

Why:
- `save_query_analysis()` already exists
- adding graph-backed context snippets is cheap
- value is strongest after graph inspect/query hint exists

### 5. Graph-backed source->entity/project views
**Difficulty:** medium
**Effect:** medium
**ROI:** medium

Why:
- useful, but less immediate than graph inspect + query hints
- better as follow-on after basic graph panel exists

## Comparative ranking against the other two repos

| Repo | Difficulty to extend Ladybug now | Expected payoff now | ROI now | Main reason |
| --- | --- | --- | --- | --- |
| `little_world` | low-medium | medium-high | **1st** | already operational and already wired into multiple workflows |
| `DocTology` | low-medium | medium | **2nd** | easy surface-side win, but corpus is thin |
| `little-crab` | high | very high | **3rd** | deepest upside, but highest stabilization and integration cost |

## Recommended execution order for DocTology

1. add graph inspect panel
2. add query-preview graph hints
3. enrich review-summary with graph context
4. add saved-analysis graph context blocks
5. only later add richer source/entity subgraph drilldowns

## Final recommendation

`DocTology` should be treated as the **human-facing Ladybug surface** in the portfolio.

That means:
- do it after or alongside `little_world` graph-runtime refinement
- do it before large `little-crab` graph-core rework
- optimize for visible graph understanding, not for graph ownership
