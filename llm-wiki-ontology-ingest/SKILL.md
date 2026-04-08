---
name: llm-wiki-ontology-ingest
description: Use this skill when an existing Obsidian-first LLM Wiki repository needs source ingest that updates both the human-facing wiki and a canonical lightweight ontology layer. Trigger on requests to ingest files from raw/inbox, process new chat logs or notes into wiki plus warehouse/jsonl, refresh ontology-backed source pages, or run the repeated source-processing workflow for an ontology-backed LLM Wiki. Do not use this to scaffold a brand-new repo or to tune ontology schemas in isolation.
---

# LLM Wiki Ontology Ingest

Use this skill as a wiki-facing adapter on top of `lightweight-ontology-core`.
The goal is to keep canonical ontology truth under `warehouse/jsonl/` while also maintaining human-facing markdown synthesis under `wiki/`.

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

For lower-level ontology work, use `lightweight-ontology-core` directly.
For graph-style inspection, layer `lg-ontology` on top of the canonical ontology outputs after the ingest path is stable.

## Expected Repo Shape

Use this skill when the repository already has most of these:

- `raw/`
- `wiki/`
- repo-local `AGENTS.md`
- ideally `warehouse/jsonl/` and `intelligence/`

If some ontology-ready folders are still missing, do not pretend the repo is already healthy.
Report the gap and either create the minimum required structure or fall back carefully.

## Operating Model

Treat these layers separately:

- `raw/` as immutable source material
- `warehouse/jsonl/` as canonical structured ontology truth
- `wiki/` as human-facing markdown synthesis
- graph projection, retrieval, or reports as optional derived layers

Do not let wiki summaries become the canonical fact store.
Do not dump canonical JSONL verbatim into wiki pages.

## Workflow

### 1. Read Local Repo Contracts First

Before doing anything:

1. read repo-root `AGENTS.md`
2. read `wiki/_meta/index.md` if it exists
3. if present, read:
   - `intelligence/glossary.yaml`
   - `intelligence/manifests/datasets.yaml`
   - `intelligence/manifests/actions.yaml`

Treat the repo-local contract as authoritative for page style, truth priority, and save behavior.

### 2. Confirm Source Scope

Work from sources already present in `raw/inbox/`, `raw/processed/`, or `raw/notes/`.
Prefer explicit filenames from the user when possible.

If a source has not been registered into `wiki/sources/` yet, create or refresh the source page stub before deeper synthesis work.

Important:

- a local CLI `ingest` command may only be source registration
- do not assume local CLI ingest already performs ontology-backed extraction

### 3. Build Canonical Ontology Truth

Use `lightweight-ontology-core` concepts and conventions to update canonical truth.

At minimum, preserve or create:

- document or message registration
- entity registry updates
- claim extraction
- claim-to-evidence links
- stable segment references
- derived edges only as derived outputs

Keep `warehouse/jsonl/...` canonical and machine-oriented.
If the corpus is conversational or sequential, preserve full-fidelity message or event coverage.

### 4. Project Back Into The Wiki

Once canonical truth is updated:

1. update the source page in `wiki/sources/`
2. refresh affected concept, people, entity, project, and timeline pages
3. create thin stubs for important missing pages instead of skipping them
4. preserve uncertainty and contradictions explicitly
5. cite the relevant source page from claim-heavy pages

Keep the wiki human-facing and easy to scan.

### 5. Refresh Meta Pages

After meaningful ingest work:

1. refresh `wiki/_meta/index.md`
2. append a clear log entry to `wiki/_meta/log.md`

If the ingest changes how the repo should be interpreted, update `AGENTS.md` or a durable analysis page instead of leaving that insight only in chat.

## User-Facing Routine

The normal human workflow should look like this:

1. place a source in `raw/inbox/`
2. run this ingest skill
3. ask a question from the improved wiki

The human should not need to call `lightweight-ontology-core` directly for normal ingest.
That lower-level skill remains available for advanced tuning, debugging, or operator workflows.

## Success Criteria

The ingest succeeded when:

- source coverage is reflected in `wiki/sources/`
- canonical ontology truth is updated under `warehouse/jsonl/`
- affected wiki pages are refreshed or created
- uncertainty is preserved
- `wiki/_meta/index.md` and `wiki/_meta/log.md` reflect the new work
