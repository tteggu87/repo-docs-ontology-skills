---
title: DocTology Ladybug ROI and priority
type: analysis
status: active
created: 2026-04-18
updated: 2026-04-18
tags:
  - doctology
  - ladybug
  - graph
  - roi
  - priority
sources:
  - "[[analysis-2026-04-17-doctology-product-direction]]"
  - "[[analysis-2026-04-17-doctology-implementation-progress]]"
---

# DocTology Ladybug ROI And Priority

## Short verdict

For immediate Ladybug implementation ROI across the three nearby repos, the working order remains:

1. `little_world`
2. `DocTology`
3. `little-crab`

Inside `DocTology` itself, the best next move is still to add a **read-only graph workbench sidecar**, not a graph-owned ontology core.

## Why DocTology is still worth doing now

- implementation is comparatively light because graph can stay derived and read-only
- the workbench is already the strongest human-facing graph surface in the portfolio
- this path aligns with current product direction rather than fighting it

## Main limiter

The main limiter is current corpus thinness.
Even a well-designed graph panel will underperform if:
- raw input remains empty
- canonical JSONL remains empty
- graph projection remains empty

So graph UI work should be paired with a minimal graphable corpus path.

## Best-fit implementation order

1. graph inspect panel
2. query-preview graph hints
3. review-summary graph enrichment
4. saved-analysis graph context
5. source/entity/project graph drilldowns

## Positioning rule

DocTology should use Ladybug as:
- a secondary instrument
- a human-facing graph review surface
- a bounded context aid

DocTology should not use Ladybug as:
- canonical truth owner
- homepage identity
- ontology mutation core

## Practical takeaway

If implementation starts with DocTology, the first tranche should optimize for visible operator value:
- page-first
- review-first
- graph-second

That keeps product identity intact while still making graph capability tangible.
