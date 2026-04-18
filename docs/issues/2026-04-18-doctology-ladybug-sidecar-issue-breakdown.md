---
title: "Issue breakdown: DocTology Ladybug workbench sidecar"
status: draft
created: 2026-04-18
updated: 2026-04-18
owner: "Hermes"
type: issue-breakdown
tags:
  - issues
  - doctology
  - ladybug
  - graph
  - workbench
---

# Issue Breakdown: DocTology Ladybug Workbench Sidecar

This document converts the current Ladybug review into GitHub-issue-style work items for `DocTology`.

## Priority order

1. Graph inspect panel
2. Query-preview graph hints
3. Review-summary graph enrichment
4. Saved-analysis graph context
5. Source/entity/project graph drilldowns

---

## Issue 1 — Add a bounded graph inspect panel to the workbench

### Goal
Expose a read-only graph panel for selected pages, claims, and sources.

### Why
This is the highest-ROI Ladybug addition inside DocTology because it creates immediate visible value without changing truth ownership.

### Deliverables
- workbench graph panel UI
- seed-based graph request contract
- empty-state / unavailable-state handling
- bounded node/edge caps and explanation copy

### Acceptance criteria
- graph panel is optional and not the homepage
- graph opens from a selected page/claim/source, not from an unseeded global graph
- if graph projection/runtime is unavailable, UI shows explicit non-error fallback
- graph panel can show at least one bounded neighborhood and one path-style explanation

---

## Issue 2 — Add graph hints to `query_preview()`

### Goal
Attach bounded graph context to the existing ask/review preview path.

### Why
`query_preview()` already exists, so this is a low-to-medium difficulty upgrade with good operator payoff.

### Deliverables
- graph hint block in preview payload
- fields such as related entities, contradiction path flag, timeline path flag, neighborhood summary
- clear optionality when graph data is absent

### Acceptance criteria
- preview remains useful even with no graph data
- graph hints are bounded and readable
- graph does not replace the current page/source/canonical evidence bundle
- preview output can distinguish `graph unavailable`, `graph empty`, and `graph available`

---

## Issue 3 — Enrich `review_summary()` with graph context

### Goal
Use graph context to explain review categories such as low coverage, uncertainty, and stale pages.

### Why
Review is already one of DocTology's strongest surfaces; graph should strengthen it rather than compete with it.

### Deliverables
- graph-gap hints for low-coverage pages
- structural neighborhood hints for uncertainty candidates
- updated-cluster hints for stale pages
- bounded contradiction/support signals for low-confidence claims

### Acceptance criteria
- review categories stay primary
- graph context is supplemental, never authoritative by itself
- output remains compact enough for workbench review panels
- no direct graph mutation is introduced

---

## Issue 4 — Add graph context blocks to `save_query_analysis()`

### Goal
Save durable analysis pages that include bounded graph context when available.

### Why
This is a cheap win after query-preview graph hints exist.

### Deliverables
- analysis-page section for graph context
- optional provenance/path summary block
- graph availability note in saved output

### Acceptance criteria
- saved analyses remain readable without graph knowledge
- graph section is omitted or explicitly marked unavailable when no graph data exists
- page-first human readability is preserved

---

## Issue 5 — Add source/entity/project graph drilldown routes

### Goal
Let operators open richer graph subviews from source and page contexts.

### Why
Useful, but lower priority than the first four issues.

### Deliverables
- source -> entity/project graph drilldown
- claim -> provenance path drilldown
- page -> related-concept neighborhood drilldown

### Acceptance criteria
- drilldowns are seeded and bounded
- route-level empty/unavailable states are explicit
- workbench remains page/review-first

---

## Out of scope for this tranche

- making Ladybug canonical truth owner in DocTology
- graph-first homepage
- direct ontology mutation/write workflows from the graph shell
- replacing the current wiki/query/review surface with graph-only UX
- full ontology-core migration into the workbench layer

---

## Recommended execution sequence

1. implement Issue 1
2. implement Issue 2
3. implement Issue 3
4. implement Issue 4
5. implement Issue 5 only if graph data density and operator value justify it
