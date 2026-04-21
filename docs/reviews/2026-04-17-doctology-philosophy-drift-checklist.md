---
title: "Checklist: DocTology philosophy drift"
status: draft
created: 2026-04-17
updated: 2026-04-17
owner: "Codex"
type: checklist
tags:
  - checklist
  - philosophy
  - drift
---

# Checklist: DocTology Philosophy Drift

Use this checklist when reviewing future changes for philosophy drift.

## Wiki-first

- [ ] README still treats the wiki as the front surface for humans
- [ ] new features do not quietly demote the wiki behind a DB or graph layer
- [ ] page synthesis remains a first-class maintained surface

## Canonical truth

- [ ] JSONL/canonical file surfaces remain the machine-truth layer
- [ ] SQLite is not described as canonical truth
- [ ] DuckDB is not described as canonical truth
- [ ] graph and analytical artifacts remain rebuildable

## Optional graph/operator

- [ ] graph is still presented as optional support
- [ ] operator workflows are still additive rather than mandatory
- [ ] product messaging does not turn graph into the main face

## Heuristics

- [ ] heuristic helpers are not promoted into primary semantic decision-makers
- [ ] route receipts remain trace/guard surfaces rather than hidden semantic authority
- [ ] fallback/default logic is clearly labeled where it exists

## Runtime honesty

- [ ] README product promise still matches shipped runtime reality
- [ ] reference runtime is not overstated as a full conversational product
- [ ] stubs and templates are not described as complete runtime implementations

## Three-layer model

- [ ] files remain canonical
- [ ] SQLite remains operational
- [ ] DuckDB remains analytical
- [ ] new code does not blur ownership between the three layers

