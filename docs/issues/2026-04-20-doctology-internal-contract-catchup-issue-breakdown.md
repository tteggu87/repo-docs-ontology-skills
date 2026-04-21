---
title: "Issue breakdown: DocTology internal contract catch-up"
status: draft
created: 2026-04-20
updated: 2026-04-20
owner: "Hermes"
type: issue-breakdown
tags:
  - issues
  - doctology
  - agents
  - bootstrap
  - manifests
  - contract-catchup
---

# Issue Breakdown: DocTology Internal Contract Catch-Up

This tranche turns the internal-coherence audit into GitHub-issue-style work.
The goal is not new backend capability.
The goal is to make **runtime, AGENTS, bootstrap snapshot, manifests, and skills describe the same system**.

## Boundary

- Keep `raw/` as immutable source truth.
- Keep `warehouse/jsonl/` as canonical structured truth.
- Keep `wiki/` as human-facing synthesis.
- Keep graph projection as derived/read-only.
- Do **not** promote graph to truth owner.
- Do **not** add a new semantics/backend tranche in this pass.
- Treat this as a **contract catch-up and drift-reduction** tranche.

## Recommended execution order

1. dual-wiki clarification
2. bootstrap/sample workspace contract repair
3. manifest catch-up for ingest/workbench/capabilities
4. bootstrap exemplar alignment or explicit downgrading
5. end-to-end drift check for future regression prevention

---

## Issue 1 — Clarify root runtime wiki vs nested bootstrap/sample wiki

### Why
DocTology currently contains a dual-wiki situation:
- root runtime/workbench code reads `wiki/`, `wiki/_meta/`, `wiki/sources/`
- root `AGENTS.md` startup still points future agents to `wiki/wiki/_meta/...`

This creates avoidable confusion about which wiki tree is the active runtime surface.

### Scope
- patch root `AGENTS.md`
- patch `docs/CURRENT_STATE.md`
- patch `docs/LAYERS.md` or add a short companion note
- explicitly define:
  - root `wiki/` runtime surface
  - nested `wiki/wiki/` bootstrap/sample or historical workspace role

### Acceptance criteria
- a new agent can tell, from root docs alone, which wiki tree the live runtime actually uses
- root `AGENTS.md` no longer sends agents to the wrong tree by default
- docs explicitly explain why both wiki trees exist
- workbench/runtime file paths and startup guidance no longer contradict each other

### Verification
- manual read-through of `AGENTS.md`, `docs/CURRENT_STATE.md`, and `docs/LAYERS.md`
- confirm consistency with `scripts/workbench/repository.py`
- confirm consistency with the current audit note

---

## Issue 2 — Repair or downgrade the checked-in bootstrap/sample workspace contract

### Why
`wiki/AGENTS.md` currently instructs operators to use commands that do not exist inside `DocTology/wiki/scripts/`, including:
- `scripts/ontology_ingest.py`
- `scripts/ontology_benchmark_ingest.py`
- `reconcile-shadow`

That makes the checked-in bootstrap/sample workspace internally inconsistent.

### Scope
Choose one explicit direction:

#### Option A — Repair the bootstrap/sample workspace
- add missing command surfaces or wrappers so `wiki/AGENTS.md` becomes executable as written

#### Option B — Downgrade the contract
- patch `wiki/AGENTS.md`
- patch `wiki/README.md`
- clearly state that this snapshot is a lighter/minimal scaffold and does not include the full current DocTology runtime contract

### Acceptance criteria
- every command named in `wiki/AGENTS.md` exists in that workspace
  - or the document explicitly says the command belongs to the parent/root runtime, not the local scaffold
- `wiki/README.md` and `wiki/AGENTS.md` describe the same maturity level
- no impossible instructions remain inside the checked-in bootstrap/sample workspace

### Verification
- `cd wiki && python3 scripts/llm_wiki.py --help`
- manual check that every referenced script actually exists
- manual read-through of `wiki/README.md` + `wiki/AGENTS.md`

---

## Issue 3 — Catch up ontology/action manifests to the shadow-first production ingest contract

### Why
`intelligence/manifests/actions.yaml` still describes ontology ingest too broadly, as if it refreshes wiki pages directly.
But current hardened production behavior is:
- canonical JSONL refresh is real
- wiki reconcile is `shadow`-first
- source pages should not be silently rewritten

### Scope
- patch `intelligence/manifests/actions.yaml`
- patch any related intelligence docs if needed
- ensure action descriptions match current production ingest safety rules:
  - canonical refresh first
  - shadow reconcile preview
  - explicit review before wiki promotion
  - graph remains derived/read-only

### Acceptance criteria
- `ingest_with_ontology` no longer implies silent wiki rewrite
- manifest language matches `scripts/ontology_ingest.py`
- action contract explicitly mentions shadow reconcile when describing wiki-facing promotion
- action manifest no longer overstates write scope relative to current code

### Verification
- compare `intelligence/manifests/actions.yaml` against `scripts/ontology_ingest.py`
- `python3 scripts/ontology_ingest.py --help`
- manual read-through of `docs/LAYERS.md` + manifest consistency

---

## Issue 4 — Catch up workbench manifest and capability registry to current backend/frontend reality

### Why
Current runtime exposes more than the manifest/capability layer describes.
Observed gaps include:
- `/api/graph/inspect` missing from `intelligence/manifests/workbench.yaml`
- workbench manifest still implies doctor/graph may exist only in backend
- `intelligence/registry/capabilities.yaml` omits current capabilities such as doctor and graph inspect

### Scope
- patch `intelligence/manifests/workbench.yaml`
- patch `intelligence/registry/capabilities.yaml`
- reconcile current backend/frontend surface, including at minimum:
  - doctor
  - graph inspect
  - source detail
  - review summary
  - warehouse summary
  - explicit note that doctor and graph lanes are already mounted in the current frontend

### Acceptance criteria
- all currently exposed workbench routes are represented in the manifest
- capability registry covers the current audited runtime surface, not just the early subset
- manifest frontend/backed notes match current `apps/workbench/src/App.tsx` and `scripts/workbench/server.py`
- graph route and doctor capability are no longer invisible at the contract layer

### Verification
- compare `intelligence/manifests/workbench.yaml` with `scripts/workbench/server.py`
- compare `intelligence/registry/capabilities.yaml` with current App/API types
- `python3 scripts/workbench_api.py --describe`
- `cd apps/workbench && npm test && npm run build`

---

## Issue 5 — Decide whether the checked-in bootstrap exemplar should match the hardened ontology-ready bootstrap

### Why
The loaded bootstrap-hardening skill expects an ontology-ready scaffold to include files such as:
- `intelligence/manifests/relations.yaml`
- `intelligence/manifests/source_families.yaml`
- `intelligence/policies/truth-boundaries.yaml`
- `scripts/ontology_refresh.py`

But the checked-in bootstrap/sample workspace under `wiki/` does not include them.
So the repo currently shows a mismatch between:
- hardened bootstrap skill expectations
- checked-in bootstrap/sample exemplar

### Scope
Choose one explicit direction:

#### Option A — Upgrade the checked-in bootstrap exemplar
- add the missing ontology-ready files to `wiki/`
- ensure its README/AGENTS reflect the hardened ontology-ready contract

#### Option B — Keep it intentionally minimal
- document that `wiki/` is a lighter bootstrap snapshot
- explicitly say it is not the full ontology-ready hardened scaffold
- prevent future agents from mistaking it for the fully up-to-date bootstrap contract

### Acceptance criteria
- the checked-in exemplar and the intended bootstrap story no longer contradict each other
- future agents can tell whether `wiki/` is:
  - a minimal sample scaffold
  - or the current ontology-ready bootstrap exemplar
- bootstrap-related docs stop implying stronger local capability than the checked-in exemplar actually has

### Verification
- inspect `wiki/intelligence/` and `wiki/scripts/`
- compare against the chosen documented bootstrap stance
- manual read-through of `README.md`, `wiki/README.md`, and bootstrap-related notes

---

## Issue 6 — Add a lightweight contract-drift audit check so this mismatch does not recur silently

### Why
The current drift was not primarily a code bug.
It was a **contract-layer lag** problem:
- runtime changed
- manifests / AGENTS / bootstrap snapshot did not fully catch up

Without an explicit audit loop, this will happen again.

### Scope
- add one lightweight audit doc or script-assisted checklist under `docs/` or `scripts/`
- define the required comparison set:
  - runtime routes vs workbench manifest
  - ingest safety behavior vs action manifest
  - root AGENTS vs actual runtime tree
  - bootstrap exemplar commands vs files actually present
- the goal is not a heavy validator, just a repeatable anti-drift check

### Acceptance criteria
- the repo has a repeatable procedure for checking contract drift after major runtime changes
- the procedure explicitly includes AGENTS + manifest + bootstrap exemplar checks, not just tests
- the next agent can run the audit without rediscovering the comparison scope from scratch

### Verification
- run the documented audit procedure once after writing it
- confirm it would catch the concrete drift found in the 2026-04-20 audit

---

## Out of scope for this tranche

- new ontology semantics
- new graph database integration
- graph truth-owner promotion
- large UI redesign
- production corpus backfill/re-ingest
- MCP expansion beyond current documented surfaces

---

## Suggested issue titles for actual GitHub creation

1. `Clarify DocTology root runtime wiki vs nested bootstrap wiki surfaces`
2. `Repair stale bootstrap workspace AGENTS contract under wiki/`
3. `Align ontology action manifests with shadow-first production ingest`
4. `Catch up workbench manifest and capability registry to current runtime`
5. `Decide and document whether wiki/ is a minimal scaffold or hardened bootstrap exemplar`
6. `Add a lightweight internal contract-drift audit for DocTology`
