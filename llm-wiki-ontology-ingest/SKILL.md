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
2. use [$lightweight-ontology-core](/Users/hoyasung007hotmail.com/.codex/skills/lightweight-ontology-core/SKILL.md) for canonical ontology extraction
3. project the resulting structured truth back into `wiki/`
4. refresh `wiki/_meta/index.md` and `wiki/_meta/log.md`

This skill does not require a top-level Hermes-style `SCHEMA.md`.
Repo-local `AGENTS.md` remains the governing contract.

## Use This Skill For

- ingesting a new raw source into an existing LLM Wiki repo
- updating `warehouse/jsonl/...` and `wiki/...` together
- refreshing source, people, concept, entity, project, and analysis pages after new evidence arrives
- running the repeated source-processing workflow in ontology-backed LLM Wiki repos

## Do Not Use This Skill For

- scaffolding a brand-new repo from scratch
- repo-only docs cleanup with no source ingest
- ontology schema design or low-level validator debugging in isolation
- answering a question when no new source ingest is needed

For new repo setup, use [$llm-wiki-bootstrap](/Users/hoyasung007hotmail.com/.codex/skills/llm-wiki-bootstrap/SKILL.md).
For lower-level ontology work, use [$lightweight-ontology-core](/Users/hoyasung007hotmail.com/.codex/skills/lightweight-ontology-core/SKILL.md) directly.

## Inputs

- one or more new sources under `raw/inbox/`
- repo-local operating contract from `AGENTS.md`
- when present:
  - `intelligence/glossary.yaml`
  - `intelligence/manifests/datasets.yaml`
  - `intelligence/manifests/actions.yaml`

## Expected Outputs

Canonical ontology outputs:

- `warehouse/jsonl/messages.jsonl` when the source is conversational or sequential
- `warehouse/jsonl/documents.jsonl`
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

## Workflow

### 1. Read Local Repo Contracts First

Before doing anything:

1. read repo-root `AGENTS.md`
2. read `wiki/_meta/index.md`
3. read the newest relevant entries in `wiki/_meta/log.md`
4. if present, read:
   - `intelligence/glossary.yaml`
   - `intelligence/manifests/datasets.yaml`
   - `intelligence/manifests/actions.yaml`

Treat the repo-local contract as authoritative for page style, truth priority, and save behavior.
Treat this as a startup ritual, not an optional nicety.

### 2. Confirm Source Scope

Work from sources already present in `raw/inbox/`, `raw/processed/`, or `raw/notes/`.
Prefer explicit filenames from the user when possible.

If a source has not been registered into `wiki/sources/` yet, create or refresh the source page stub before deeper synthesis work.
Before creating any new page, check whether the scope already exists so the ingest does not create duplicates for passing mentions or overlapping topics.

Important:

- the local CLI `python scripts/llm_wiki.py ingest ...` is source registration only
- it is not the full ontology-backed ingest workflow by itself

### 3. Build Canonical Ontology Truth

Use [$lightweight-ontology-core](/Users/hoyasung007hotmail.com/.codex/skills/lightweight-ontology-core/SKILL.md) concepts and conventions to update canonical truth.

At minimum, preserve or create:

- document/message registration
- entity registry updates
- claim extraction
- claim-to-evidence links
- stable segment references
- derived edges only as derived outputs

Keep `warehouse/jsonl/...` canonical and machine-oriented.
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
Do not let duplicate or weakly justified pages accumulate when an existing page can be extended instead.

### 5. Refresh Meta Pages

After meaningful ingest work:

1. refresh `wiki/_meta/index.md`
2. append a clear log entry to `wiki/_meta/log.md`

If the ingest changed how the repo should be interpreted, update `AGENTS.md` or a durable analysis page rather than leaving that insight only in chat.

## User-Facing Routine

The normal human workflow should look like this:

1. scaffold once with [$llm-wiki-bootstrap](/Users/hoyasung007hotmail.com/.codex/skills/llm-wiki-bootstrap/SKILL.md)
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

## Notes

- Prefer `ingest` language with the user; keep `adapter` or `bridge` as internal mental models only.
- Prefer repo-local `AGENTS.md` over generic habits when they conflict.
- If the repo does not yet have ontology-ready folders, fall back gracefully and say what is missing.
- Keep `warehouse/jsonl/` as canonical truth and treat markdown pages as the human-facing projection layer.
