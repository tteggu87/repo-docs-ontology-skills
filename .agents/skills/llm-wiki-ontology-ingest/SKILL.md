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
2. prefer the repo's configured full ingest runner when available
3. append proposed ontology records rather than accepted truth
4. project source-backed synthesis back into `wiki/`
5. refresh `wiki/_meta/index.md` and `wiki/_meta/log.md`

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

For new repo setup, use [`llm-wiki-bootstrap`](../llm-wiki-bootstrap/SKILL.md).
For lower-level ontology work, use [`lightweight-ontology-core`](../lightweight-ontology-core/SKILL.md) directly.

## Inputs

- one or more new sources under `raw/inbox/`
- repo-local operating contract from `AGENTS.md`
- when present:
  - `intelligence/glossary.yaml`
  - `intelligence/manifests/datasets.yaml`
  - `intelligence/manifests/actions.yaml`

## Expected Outputs

Canonical ontology outputs:

- `warehouse/jsonl/proposed_entities.jsonl`
- `warehouse/jsonl/proposed_claims.jsonl`
- `warehouse/jsonl/proposed_evidence.jsonl`
- optional `warehouse/jsonl/proposed_relations.jsonl`
- accepted/canonical registries only after explicit review or a repo-specific promotion workflow

Wiki outputs:

- `wiki/sources/...`
- affected `wiki/people/...`
- affected `wiki/concepts/...`
- affected `wiki/entities/...`
- affected `wiki/projects/...`
- optional `wiki/analyses/...` when the ingest naturally produces a durable synthesis memo
- refreshed `wiki/_meta/index.md`
- appended `wiki/_meta/log.md`

## Closed Pipeline Contract

This skill must complete the full ingest lifecycle unless the user explicitly
requests a partial operation.

Required stages:

1. Register source identity.
2. Append applicable proposed JSONL records.
3. Project canonical/source-backed synthesis into wiki pages.
4. Refresh meta surfaces.
5. Validate structural integrity or report why validation could not run.
6. Report changed files, uncertainty, and remaining open questions.

This pipeline closes the lifecycle, not semantic judgment.

Do not replace semantic judgment with deterministic keyword routing. Use
deterministic scripts only for registration, indexing, logging, JSONL
integrity, and structural validation.

Semantic no-fallback rule: if source-page synthesis, affected-page selection,
claim extraction, contradiction handling, or wiki projection requires agent or
configured LLM judgment, unavailable, failed, or invalid judgment must be
reported as failed, partial, or pending. Do not replace it with lexical
diagnostics, retrieval output, graph projection, structural validation,
filename/keyword summaries, or deterministic fallback prose and call semantic
ingest complete. Transport fallback for the same configured LLM request is
allowed; semantic fallback that changes the judgment owner is not.

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
- when available, use `python scripts/llm_full_ingest.py raw/inbox/source.md --apply`
  as the minimal configured-LLM full growth loop
- `--apply` may update source pages, affected wiki pages, proposed JSONL, index,
  log, and ingest reports
- `--apply` must not modify raw sources, create accepted truth, delete content,
  rename pages, merge pages, or auto-commit

### 3. Build Proposed Ontology Truth

Use [`lightweight-ontology-core`](../lightweight-ontology-core/SKILL.md) concepts and conventions to draft proposed ontology truth.

At minimum, preserve or create:

- document/message registration
- entity registry updates
- claim extraction
- claim-to-evidence links
- stable segment references
- derived edges only as derived outputs

Keep `warehouse/jsonl/...` canonical and machine-oriented.
Do not let wiki summaries become the canonical truth layer.
For automatic ingest, write records as proposed/needs_review unless the user has
explicitly requested and reviewed accepted promotion.

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

1. scaffold once with [`llm-wiki-bootstrap`](../llm-wiki-bootstrap/SKILL.md)
2. place a source in `raw/inbox/`
3. run `python scripts/llm_full_ingest.py raw/inbox/source.md --apply`
4. ask a question from the wiki

The human should not need to call `lightweight-ontology-core` directly for normal ingest.
That lower-level skill remains available for advanced tuning, debugging, or operator workflows.

## Success Criteria

The ingest succeeded when:

- source coverage is reflected in `wiki/sources/`
- proposed ontology truth is updated under `warehouse/jsonl/`
- affected wiki pages are refreshed or created
- uncertainty is preserved
- `wiki/_meta/index.md` and `wiki/_meta/log.md` reflect the new work
- the completion report distinguishes proposed JSONL emitted, appended, and skipped_existing counts

## Completion Report

Report:

1. Source registered
2. Proposed JSONL records emitted, appended, and skipped_existing
3. Wiki pages updated or created
4. Claims proposed, accepted, disputed, or left pending
5. Evidence coverage
6. Validation result
7. Open questions and uncertainty
8. Files changed

## Notes

- Prefer `ingest` language with the user; keep `adapter` or `bridge` as internal mental models only.
- Prefer repo-local `AGENTS.md` over generic habits when they conflict.
- If the repo does not yet have ontology-ready folders, fall back gracefully, say what is missing, and do not report the result as completed ontology-backed ingest.
- Keep `warehouse/jsonl/` as canonical truth and treat markdown pages as the human-facing projection layer.
