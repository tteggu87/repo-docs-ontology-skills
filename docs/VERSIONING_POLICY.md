# VERSIONING_POLICY

_Last updated: 2026-04-19_

## Purpose

DocTology needs a strict policy for what belongs in git.
Without this, the repo accumulates mixed concerns:
- product code
- private corpus growth
- rebuildable runtime state
- agent-local scratch artifacts

This policy exists to keep the working tree stable and the product posture honest.

---

## Category A — Track in the public/reference repo

Track these by default:
- source code under `scripts/`, `apps/`, and related product/runtime paths
- tests under `tests/`
- stable docs under `docs/`
- reusable templates and schema files
- durable wiki/meta docs that describe the product/runtime contract
- small intentional example fixtures used for tests or demos

Track these because they are part of the reusable product/reference artifact.

---

## Category B — Usually keep in a private live workspace, not in the public repo

Prefer **not** to track these in the public reference repo by default:
- real long-lived `raw/` corpus contents
- real populated `warehouse/jsonl/` outputs for a private corpus
- ongoing private `wiki/sources/` and `wiki/analyses/` growth tied to that corpus
- daily operator outputs that mainly describe one user’s evolving knowledge base

These are valuable, but they are usually workspace truth, not public product truth.

---

## Category C — Rebuildable / derived / operational artifacts

Do not treat these as canonical tracked truth by default:
- `warehouse/graph_projection/`
- `wiki/state/*.sqlite`
- `wiki/state/*.duckdb`
- cache-like derived summaries or mirrors
- regenerated preview/state files unless explicitly chosen as fixtures

These may be committed only when they are intentionally curated as:
- tiny fixtures for tests
- reproducible demo artifacts
- stable examples needed for public documentation

Otherwise, regenerate them instead of normalizing them into git history.

---

## Category D — Never treat as product truth

These should stay local or ignored:
- `.codex/` planning/context artifacts
- `.hermes/` local plans or scratch outputs
- other agent-local temporary coordination files
- `__pycache__/`, `.pyc`, and similar runtime detritus

---

## Decision rules

### If a file is part of reusable product/runtime behavior
Track it.

### If a file is tied to one evolving private corpus
Prefer keeping it in a live workspace repo or private branch/worktree, not the public reference repo.

### If a file can be deterministically rebuilt from higher-truth layers
Treat it as derived and do not track it by default.

### If a file exists only because an agent/tool ran locally
Keep it out of the durable product history.

---

## Recommended repo split

### Public/reference DocTology repo
Owns:
- product code
- tests
- docs
- templates
- stable contracts
- tiny fixtures

### Private/live workspace
Owns:
- real corpus
- real canonical outputs
- daily wiki growth
- operator history tied to that corpus

This split is the cleanest way to avoid repeated working-tree contamination.

---

## Practical operator rule

Before committing, ask:

1. Is this reusable product/reference truth?
2. Is this just my current live corpus?
3. Is this derived and rebuildable?
4. Is this merely local agent/runtime scratch?

Only category 1 should be a default public-repo commit.
Categories 2–4 should require explicit justification.
