---
title: "Review: DocTology working tree cleanup and knowledge-ops finish path"
status: draft
created: 2026-04-19
updated: 2026-04-19
owner: "Hermes"
type: review
tags:
  - review
  - doctology
  - cleanup
  - working-tree
  - knowledge-ops
  - roadmap
---

# Review: DocTology working tree cleanup and knowledge-ops finish path

## Summary

DocTology is no longer just a philosophy repo.
It now has:
- bounded graph inspect in the workbench
- an ontology benchmark harness
- a raw-first production ingest path
- passing backend/frontend tests for those recent additions

But it is **not yet a finished knowledge operations system**.
The main blocker is not missing feature breadth.
The main blocker is that the repository is still mixing three roles:

1. public/reference product repo
2. live local corpus workspace
3. rebuildable runtime state / agent artifacts

That role mixing is exactly what was dirtying the working tree.

## What I verified

### Git / working tree
- inspected `git status --short --branch`
- inspected current `.gitignore`
- classified dirty paths into agent-local artifacts, local live corpus, rebuildable state, and durable docs

### Current implementation state
- `git log --oneline 34ce9a1..HEAD`
- `git diff --stat 34ce9a1..HEAD`
- reviewed README, wiki AGENTS, recent docs/reviews, recent wiki meta pages
- checked current workbench routes in `scripts/workbench/repository.py` / `server.py`

### Runtime verification
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py tests/test_ontology_benchmark_ingest.py tests/test_workbench_graph_inspect.py -q`
- `npm test`
- `npm run build`
- live calls to:
  - `warehouse_summary()`
  - `review_summary()`
  - `query_preview()`
  - `graph_inspect()`
  - `source_detail()`

## Cleanup action performed now

I applied a **local-only cleanup boundary** via `.git/info/exclude` and restored repo-tracked transient changes.

What this did:
- hid local agent/runtime artifacts such as `.codex/context/`, `.codex/plans/`, `.hermes/`
- hid local live-corpus workspace paths such as `raw/`, `warehouse/`, and the untracked top-level `wiki/...` workspace content
- hid rebuildable runtime state such as `wiki/state/`
- restored `.gitignore` and the tracked `.codex/ralph/*` files to remove accidental dirty tracked deletions

Important boundary:
- this cleanup is **local Git hygiene**, not a final product-policy decision
- the public repo still needs an explicit documented rule for what is tracked vs local-only vs rebuildable

## Working tree diagnosis

### Dirty paths were coming from four different classes

#### 1. Agent-local artifacts
Examples:
- `.codex/context/`
- `.codex/plans/`
- `.hermes/`

These should not be part of product truth.
They should be ignored locally or removed from tracked history if already committed.

#### 2. Local live corpus content
Examples:
- `raw/processed/...`
- top-level `wiki/sources/...`
- top-level `wiki/analyses/...`
- top-level `wiki/warehouse/...`

These are valuable, but they behave like a **private evolving workspace corpus**, not like stable public reference-repo assets.

#### 3. Rebuildable runtime state
Examples:
- `wiki/state/wiki_index.sqlite`
- `wiki/state/wiki_analytics.duckdb`
- `warehouse/graph_projection/*.jsonl`

These should have an explicit versioning rule:
- either tracked as a tiny example fixture
- or ignored as rebuildable outputs
- but not left ambiguous

#### 4. Durable product/review docs
Examples:
- philosophy drift review/checklist docs
- recent tracked review and roadmap docs

These are commit-worthy when they describe stable architecture or operator guidance.

## Current reality check

### What is genuinely working
- graph inspect route exists and returns bounded neighborhoods
- query preview returns wiki/source-grounded results and graph hints
- benchmark and production ingest code paths exist
- recent tests/build all pass

### What is still incomplete
- main repo canonical JSONL is still effectively empty in live verification
  - `source_versions/documents/messages/entities/claims/claim_evidence/segments/derived_edges = 0`
- `source_detail()` still reports zero canonical coverage for checked sources
- review surfaces exist, but with empty canonical truth they cannot yet act like a real daily knowledge-ops control tower
- there is no explicit `docs/CURRENT_STATE.md`
- there is no explicit `docs/LAYERS.md`
- there is no repo-level `doctor` command that reports route readiness, count density, path drift, and tracked-vs-local boundary health
- README still presents a strong promise, but live daily operation is split between reference runtime and private local corpus behavior

## Strong conclusion

DocTology already has **enough layers**.
What it lacks is **operational closure**.

Update after the closeout tranche implementation:
- `doctor` now exists in `scripts/llm_wiki.py` with human-readable and JSON output
- `docs/CURRENT_STATE.md`, `docs/LAYERS.md`, and `docs/VERSIONING_POLICY.md` now pin repo/runtime ownership
- query previews now expose an explicit route/truth/fallback contract
- the remaining finish work after this tranche is mostly iterative hardening, not first-pass scaffolding

The finish path is not:
- add more graph features first
- add more MCP polish first
- add more benchmark variants first

The finish path is:

> make one clean, repeatable daily operator loop where raw source -> canonical truth -> review queue -> bounded human-facing wiki update works without dirtying the product repo or blurring truth ownership.

## Highest-priority next step

## 1. Separate the public reference repo from the live private workspace

This is the biggest leverage move because it solves both:
- working tree cleanliness
- product/runtime honesty

### Recommended rule

#### Public/reference DocTology repo tracks:
- product code
- reusable scripts
- tests
- docs/reviews/plans
- tiny fixture examples only
- explicit templates / schemas / sample manifests

#### Private/live workspace tracks separately:
- real `raw/`
- real canonical `warehouse/jsonl/`
- live wiki/source/analysis pages
- operator logs / daily corpus growth

#### Rebuildable local state is not tracked by default:
- SQLite operational mirrors
- DuckDB analytics mirrors
- graph projection caches unless intentionally shipped as a fixture
- agent planning folders

Without this split, DocTology keeps behaving as both product and personal notebook, and the working tree will keep drifting.

## Immediate sequence

### A. Document truth ownership and versioning policy
Add:
- `docs/CURRENT_STATE.md`
- `docs/LAYERS.md`
- `docs/VERSIONING_POLICY.md` or equivalent section

Must answer explicitly:
- what is canonical truth?
- what is derived?
- what is local-only?
- what is safe to track in git?
- what belongs only in a private workspace?

### B. Formalize a `doctor` command
The repo needs a first-class health report that checks at least:
- raw source count
- canonical registry row counts
- source pages with/without `raw_path`
- duplicate `raw_path` ownership
- graph projection readiness
- workbench route readiness
- drift between README promise and runtime reality
- working-tree contamination classes (agent/local/runtime/tracked)

### C. Promote the production ingest path from “available” to “daily operator default”
The current code already supports the right direction:
- `scripts/ontology_ingest.py`
- shadow wiki reconcile preview
- benchmark comparison runner

What is still missing is the operating contract:
- when to run it
- where to run it
- what counts as success/failure
- how contradiction and merge candidates are reviewed
- how approved changes reach the human-facing wiki

## Next wave

### 2. Make the answer path knowledge-ops complete
Current workbench query preview is useful, but a finished knowledge-ops system needs a richer answer contract.

Each substantial answer should expose:
- route used
- truth layers touched
- source pages used
- canonical coverage available/missing
- contradiction/merge review signals
- graph assist reason (if any)
- fallback reason when canonical truth is empty

### 3. Add an operator promotion loop
Needed states:
- extracted candidate
- needs review
- approved
- rejected
- merged/superseded

The system is close, because review surfaces already expose:
- low-confidence claims
- contradiction candidates
- merge candidates

But it still needs a stable daily operator workflow and explicit persistence semantics.

### 4. Decide the role of graph projection artifacts
Current ambiguity:
- graph inspect is valuable and works
- graph projection is clearly derived
- but git policy for those artifacts is still unclear

Recommendation:
- keep graph projection rebuildable by default
- ship only tiny example fixtures if a public demo needs them
- do not let graph artifacts become accidental public truth

## Later

### 5. Upgrade from review surface to full knowledge-ops cockpit
Only after the boundary and ingest loop are clean:
- richer ask workspace
- queue-based review UI
- receipt viewer
- operator action history
- source-to-claim-to-wiki promotion UX

### 6. MCP/server standardization comes after answer quality and operator closure
MCP is valuable, but not the first blocker here.
The first blocker is that canonical truth in the main verified path is still empty, so protocol polish comes after operational truth density.

## Recommended finish definition

Call DocTology “finished enough” as a knowledge operations system only when all of these are true:

1. public repo and live workspace are clearly separated
2. working tree stays clean during ordinary daily use
3. `doctor` reports real counts and route readiness
4. raw-first ingest produces non-empty canonical truth on the real workspace
5. review queue is part of the normal operating loop
6. wiki updates happen through explicit reviewed promotion, not silent drift
7. answer surfaces disclose route/truth/fallback/uncertainty clearly

## Final judgment

DocTology is now a credible **reference knowledge-ops architecture and workbench harness**.
It is not yet the finished operating system because the daily operational boundary is still fuzzy and the main verified canonical layer is still empty in the checked repo.

So the next move is not more architecture.
The next move is **operational hardening plus boundary separation**.
