---
name: llm-wiki-ontology-ingest
description: Use this skill when an existing Obsidian-first LLM Wiki repository needs source ingest that updates both the human-facing wiki and a canonical lightweight ontology layer. Trigger on requests to ingest files from raw/inbox, process new chat logs or notes into wiki plus warehouse/jsonl, refresh ontology-backed source pages, or run the repeated source-processing workflow for an ontology-backed LLM Wiki. Do not use this to scaffold a brand-new repo or to tune ontology schemas in isolation.
---

# LLM Wiki Ontology Ingest

## Overview

This is the user-facing ingest skill for an ontology-backed LLM Wiki.

Use it when the repository already has:

- `raw/`
- `wiki/`
- repo-local `AGENTS.md`
- ideally `warehouse/jsonl/` and `intelligence/`

This skill is the adapter between a repo-local wiki workflow and the reusable ontology engine.
It should feel simple to the human:

1. put a source in `raw/inbox/`
2. run ingest
3. ask questions from the improved wiki

Internally, this skill should:

1. honor the repo-local `AGENTS.md`
2. use `lightweight-ontology-core` for canonical ontology extraction
3. project the resulting structured truth back into `wiki/`
4. refresh `wiki/_meta/index.md` and `wiki/_meta/log.md`

## Use This Skill For

- ingesting a new raw source into an existing LLM Wiki repo
- updating `warehouse/jsonl/...` and `wiki/...` together
- refreshing source, people, concept, entity, project, and analysis pages after new evidence arrives
- running the repeated source-processing workflow in ontology-backed LLM Wiki repos

## Do Not Use This Skill For

- scaffolding a brand-new repo from scratch
- converting a plain DocTology repo with no existing `wiki/` layer into an LLM Wiki from zero
- repo-only docs cleanup with no source ingest
- ontology schema design or low-level validator debugging in isolation
- answering a question when no new source ingest is needed

For lower-level ontology work, use `lightweight-ontology-core` directly.
For new repo setup, use `llm-wiki-bootstrap`.
For graph-style inspection, layer `lg-ontology` on top of the canonical ontology outputs after the ingest path is stable.

## Inputs

- one or more new sources under `raw/inbox/`
- repo-local operating contract from `AGENTS.md`
- when present:
  - `intelligence/glossary.yaml`
  - `intelligence/manifests/datasets.yaml`
  - `intelligence/manifests/actions.yaml`
  - `intelligence/manifests/relations.yaml`
  - `intelligence/manifests/source_families.yaml`
  - `intelligence/policies/truth-boundaries.yaml`

## Expected Outputs

Canonical ontology outputs:

- `warehouse/jsonl/messages.jsonl` when the source is conversational or sequential
- `warehouse/jsonl/documents.jsonl`
- `warehouse/jsonl/source_versions.jsonl` when the source family is recurring or export-based
- `warehouse/jsonl/entities.jsonl`
- `warehouse/jsonl/claims.jsonl`
- `warehouse/jsonl/claim_evidence.jsonl`
- `warehouse/jsonl/segments.jsonl`
- `warehouse/jsonl/derived_edges.jsonl`

Wiki outputs:

- `wiki/sources/...`
- affected `wiki/people/...`
- affected `wiki/concepts/...`
- affected `wiki/entities/...`
- affected `wiki/projects/...`
- optional `wiki/analyses/...` when the ingest naturally produces a durable synthesis memo
- refreshed `wiki/_meta/index.md`
- appended `wiki/_meta/log.md`

## Expected Repo Shape

Use this skill when the repository already has most of these:

- `raw/`
- `wiki/`
- repo-local `AGENTS.md`
- ideally `warehouse/jsonl/` and `intelligence/`

If some ontology-ready folders are still missing, do not pretend the repo is already healthy.
Report the gap clearly.
Create only small missing support artifacts inside an already wiki-shaped repo.
Do not bootstrap a plain repository into an LLM Wiki from this skill.

## Operating Model

Treat these layers separately:

- `raw/` as immutable source material
- `warehouse/jsonl/` as canonical structured ontology truth
- `wiki/` as human-facing markdown synthesis
- graph projection, retrieval, or reports as optional derived layers

Do not let wiki summaries become the canonical fact store.
Do not dump canonical JSONL verbatim into wiki pages.
This skill is an adapter, not a bootstrapper.

## Workflow

### 1. Read Local Repo Contracts First

Before doing anything:

1. read repo-root `AGENTS.md`
2. read `wiki/_meta/index.md`
3. if present, read:
   - `intelligence/glossary.yaml`
   - `intelligence/manifests/datasets.yaml`
   - `intelligence/manifests/actions.yaml`
   - `intelligence/manifests/relations.yaml`
   - `intelligence/manifests/source_families.yaml`
   - `intelligence/policies/truth-boundaries.yaml`

Treat the repo-local contract as authoritative for page style, truth priority, and save behavior.

### 2. Confirm Source Scope

Work from sources already present in `raw/inbox/`, `raw/processed/`, or `raw/notes/`.
Prefer explicit filenames from the user when possible.

If a source has not been registered into `wiki/sources/` yet, create or refresh the source page stub before deeper synthesis work.

Important:

- a local CLI `ingest` command may only be source registration
- do not assume local CLI ingest already performs ontology-backed extraction
- if the repo lacks a real `wiki/` layer, stop and ask for the wiki scaffold or equivalent structure first
- the local CLI `python scripts/llm_wiki.py ingest ...` may still be source registration only

### 3. Build Canonical Ontology Truth

Use `lightweight-ontology-core` concepts and conventions to update canonical truth.

Read the compact contract layer first when it exists:
- `intelligence/manifests/relations.yaml` for stable relation vocabulary and graph-like hop hints
- `intelligence/manifests/source_families.yaml` for recurring source identity and incremental-ingest assumptions
- `intelligence/policies/truth-boundaries.yaml` for source/canonical/wiki/derived layer separation

At minimum, preserve or create:

- document or message registration
- entity registry updates
- claim extraction
- claim-to-evidence links
- stable segment references
- derived edges only as derived outputs

Keep `warehouse/jsonl/...` canonical and machine-oriented.
If the corpus is conversational or sequential, preserve full-fidelity message or event coverage.
Do not let wiki summaries become the canonical truth layer.

### 4. Project Back Into The Wiki

Once canonical truth is updated:

1. update the source page in `wiki/sources/`
2. refresh affected concept, people, entity, project, and timeline pages
3. create thin stubs for important missing pages instead of skipping them
4. preserve uncertainty and contradictions explicitly
5. cite the relevant source page from claim-heavy pages

Keep the wiki human-facing and easy to scan.
Do not dump raw JSONL into markdown pages.

### 5. Refresh Meta Pages And Minimal Derived State

After meaningful ingest work:

1. refresh `wiki/_meta/index.md`
2. append a clear log entry to `wiki/_meta/log.md`
3. if the repo has `scripts/ontology_refresh.py`, run it to:
   - ensure canonical registry files exist
   - emit a compact refresh summary
   - rebuild lightweight repo state after ontology changes

This refresh step is intentionally minimal.
It does not replace full ontology extraction, graph export, or validator-heavy operator workflows.

If the ingest changed how the repo should be interpreted, update `AGENTS.md` or a durable analysis page rather than leaving that insight only in chat.

## User-Facing Routine

The normal human workflow should look like this:

1. scaffold once with `llm-wiki-bootstrap`, or confirm equivalent `raw/`, `wiki/`, and repo-local `AGENTS.md` layout already exists
2. place a source in `raw/inbox/`
3. run this ingest skill
4. ask a question from the wiki

The human should not need to call `lightweight-ontology-core` directly for normal ingest.
That lower-level skill remains available for advanced tuning, debugging, or operator workflows.

## Success Criteria

The ingest succeeded when:

- source coverage is reflected in `wiki/sources/`
- canonical ontology truth is updated under `warehouse/jsonl/`
- affected wiki pages are refreshed or created
- uncertainty is preserved
- `wiki/_meta/index.md` and `wiki/_meta/log.md` reflect the new work
- if `scripts/ontology_refresh.py` exists, its refresh summary runs cleanly and reports the expected registry presence

## Notes

- Prefer `ingest` language with the user; keep `adapter` or `bridge` as internal mental models only.
- Prefer repo-local `AGENTS.md` over generic habits when they conflict.
- If the repo does not yet have ontology-ready folders, fall back gracefully and say what is missing.
