---
title: "Issue breakdown: DocTology knowledge-ops closeout tranche"
status: draft
created: 2026-04-19
updated: 2026-04-19
owner: "Hermes"
type: issue-breakdown
tags:
  - issues
  - doctology
  - knowledge-ops
  - closeout
  - doctor
  - docs
  - workbench
---

# Issue Breakdown: DocTology Knowledge-Ops Closeout Tranche

This tranche turns the cleanup/finish-path review into GitHub-issue-style work that can be fully implemented and verified in the local repo.

## Boundary

- Keep `raw/` as immutable source truth.
- Keep `warehouse/jsonl/` as canonical structured truth.
- Keep graph projection / SQLite / DuckDB as derived or operational layers.
- Do **not** turn graph into a truth owner.
- Do **not** silently normalize the current public repo into a private live-corpus repo.

## Recommended execution order

1. truth-state docs + versioning policy
2. doctor-grade diagnostics and workbench action support
3. production daily-operator contract and runbook surfaces
4. route/truth/fallback answer contract hardening

---

## Issue 1 — Define current state, layer ownership, and git/versioning policy

### Why
DocTology now mixes public reference-repo assets, local live-corpus content, and rebuildable runtime artifacts. The repo needs explicit ownership rules before more automation lands.

### Scope
- add `docs/CURRENT_STATE.md`
- add `docs/LAYERS.md`
- add `docs/VERSIONING_POLICY.md`
- update README pointers so the live runtime truth is discoverable

### Acceptance criteria
- `docs/CURRENT_STATE.md` describes what is actually implemented at current HEAD
- `docs/LAYERS.md` defines truth order and ownership for raw / canonical / wiki / graph / sqlite / duckdb
- `docs/VERSIONING_POLICY.md` defines tracked vs local-only vs rebuildable artifacts
- docs explicitly distinguish public reference repo vs private live workspace
- README links to the new state/layer docs without overstating runtime maturity

### Verification
- `python3 scripts/llm_wiki.py status`
- `python3 scripts/llm_wiki.py doctor`
- manual read-through of README + new docs for consistency

---

## Issue 2 — Add doctor-grade runtime and working-tree diagnostics

### Why
`status` is too shallow for a knowledge-ops system. Operators need one command that reports truth density, route readiness, drift, and contamination classes.

### Scope
- add `doctor` to `scripts/llm_wiki.py`
- support human-readable and `--json` output
- classify working-tree dirt into stable buckets
- expose doctor through workbench action APIs/types/UI
- add focused tests for doctor output and parsing

### Acceptance criteria
- `python3 scripts/llm_wiki.py doctor` reports raw counts, canonical registry counts, source-page raw-path health, graph readiness, docs/readiness checks, and working-tree contamination classes
- `python3 scripts/llm_wiki.py doctor --json` returns machine-readable structured output
- workbench doctor actions include `doctor` and parse its structured summary
- no existing status/lint/reindex behavior regresses

### Verification
- `python3 scripts/llm_wiki.py doctor`
- `python3 scripts/llm_wiki.py doctor --json`
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_llm_wiki_runtime_health.py -q`
- `npm test`
- `npm run build`

---

## Issue 3 — Publish the production daily-operator loop and readiness contract

### Why
The production ingest path exists, but the repo still lacks a crisp, repeatable operator contract for daily use.

### Scope
- add a durable runbook/flow doc for the daily operator loop
- make doctor surface the operator readiness state and recommended next commands
- ensure the contract is explicit about shadow reconcile, review queues, and no silent wiki rewrites

### Acceptance criteria
- a new doc records the daily operator loop from raw source -> ingest -> review -> shadow reconcile -> explicit promotion
- doctor output includes operator readiness and recommended next actions
- docs and runbook use the production ingest path as the canonical daily loop while keeping the benchmark harness as comparison tooling
- the contract explicitly preserves reviewed promotion rather than silent write-back

### Verification
- `python3 scripts/llm_wiki.py doctor`
- `python3 scripts/ontology_ingest.py --help`
- manual read-through of runbook and roadmap consistency

---

## Issue 4 — Make query previews expose route, truth, and fallback contract explicitly

### Why
Query previews currently give useful grounded drafts, but they still hide too much operator-relevant contract information behind prose.

### Scope
- extend query preview payload with explicit route/truth/fallback metadata
- expose the new contract in saved analysis pages and workbench UI/types
- add tests for supported / thin / none / empty-query behavior

### Acceptance criteria
- query preview payload includes an explicit contract block covering route, truth layers touched, fallback reason, and save readiness
- saved analysis pages persist the contract, not just the prose answer
- workbench API types/UI compile against the richer payload
- existing graph hints / provenance behavior remains intact

### Verification
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_workbench_graph_inspect.py -q`
- `npm test`
- `npm run build`

---

## Out of scope for this tranche

- full queue-based promotion UI
- automatic wiki write-back from ontology output
- graph-truth ownership migration
- broader MCP standardization work
- expanding ingest formats beyond the current raw-first path
