# AGENTS.md

This checked-in `wiki/` tree is a **lighter bootstrap/sample workspace** for an Obsidian-first LLM Wiki with a lightweight ontology layer.

It is useful for:
- bootstrap layout inspection
- minimal local wiki maintenance
- sample state/index/analytics rebuild loops

It is **not** the full current parent DocTology runtime contract by itself.
If you are working from the parent repository root, prefer the parent root `AGENTS.md`, `docs/CURRENT_STATE.md`, and `docs/LAYERS.md` for the live runtime rules.

## Mission

Maintain a persistent, high-signal markdown wiki that sits between raw sources and future reasoning.

Do not answer only in chat when the result belongs in the wiki.
Prefer to turn durable work into durable markdown pages.
When ontology-backed ingest is available, keep the canonical ontology registry aligned with the wiki.

## Architecture

There are four layers:

1. `raw/` contains immutable source material. Never modify source contents.
2. `warehouse/jsonl/` contains canonical structured ontology truth.
3. `wiki/` contains LLM-maintained human-facing synthesis pages.
4. `AGENTS.md` plus `intelligence/` define the operating rules, vocabulary, dataset boundaries, and action contracts.

## Core Rules

1. Treat `raw/` as immutable source truth, `warehouse/jsonl/` as canonical structured truth, and `wiki/` as maintained human-facing synthesis.
2. Never edit files inside `raw/` unless the user explicitly asks.
3. Prefer many small linked pages over one giant dumping-ground page.
4. Use Obsidian wikilinks like `[[concept-name]]` whenever a stable concept, entity, person, project, or source page exists.
5. Preserve uncertainty. If a claim is weak, disputed, inferred, or contradicted, say so explicitly.
6. Cite the underlying source page from any claim-heavy wiki page.
7. When answering substantial questions, save the answer into `wiki/analyses/` unless the user asks for chat-only output.
8. Keep `wiki/_meta/index.md` and `wiki/_meta/log.md` current after meaningful work.

## Truth Priority

Use this order when evidence conflicts or layers disagree:

1. `raw/` = immutable source material
2. `warehouse/jsonl/...` = canonical structured ontology truth
3. `wiki/` = maintained human-facing synthesis
4. graph projection or retrieval outputs = optional derived aids, never canonical

The wiki is the default reading surface for humans.
The ontology registries are the default machine-truth surface for provenance, contradiction handling, and source coverage checks.

## Folder Semantics

- `raw/`: immutable source storage
- `warehouse/jsonl/`: canonical ontology outputs such as `messages.jsonl`, `documents.jsonl`, `entities.jsonl`, `claims.jsonl`, `claim_evidence.jsonl`, `segments.jsonl`, and `derived_edges.jsonl`
- `wiki/sources/`: one page per source, including source metadata, summary, key claims, and links to affected pages
- `wiki/concepts/`: concepts, frameworks, recurring ideas, terminology
- `wiki/entities/`: organizations, products, systems, places, or domain objects
- `wiki/people/`: people and roles
- `wiki/projects/`: efforts, initiatives, cases, programs, or workstreams
- `wiki/timelines/`: chronological pages
- `wiki/analyses/`: saved answers, comparison memos, synthesis notes, decision memos
- `wiki/_meta/`: dashboard, index, log, and other operational pages
- `intelligence/`: glossary and manifests that stabilize repo-local vocabulary, datasets, and action boundaries

## Page Conventions

Every wiki page should start with YAML frontmatter when practical.

Recommended fields:

```yaml
---
title: Example Page
type: concept
status: active
created: 2026-04-08
updated: 2026-04-08
tags:
  - llm-wiki
sources:
  - "[[source-2026-04-08-example]]"
---
```

Guidelines:

- `title`: human-readable page title
- `type`: one of `source`, `concept`, `entity`, `person`, `project`, `timeline`, `analysis`, `meta`
- `status`: usually `active`, `draft`, `superseded`, or `open-question`
- `sources`: wikilinks to source pages, not raw file paths
- Keep sections crisp and scannable
- Use headings instead of long uninterrupted prose

## Source Ingest Workflow

When the user asks to ingest a source:

1. Read the raw source from `raw/inbox/`, `raw/processed/`, or `raw/notes/`.
2. In this checked-in sample workspace, the local `scripts/llm_wiki.py` only handles **source registration**.
   - available local commands here are `ingest`, `reindex`, `lint`, `status`, and `log`
   - local support helpers here are `scripts/reindex_sqlite_operational.py`, `scripts/refresh_duckdb_analytics.py`, and `scripts/verify_three_layer_drift.py`
3. If you are working inside the **parent DocTology runtime**, ontology-backed ingest and operator contracts live at the parent root, not inside this sample workspace.
   - parent runtime production ingest: `scripts/ontology_ingest.py`
   - parent runtime benchmark ingest: `scripts/ontology_benchmark_ingest.py`
   - parent runtime shadow preview inspection: `python scripts/llm_wiki.py reconcile-shadow --root <repo>`
4. Locate the matching page in `wiki/sources/`. If it does not exist, create it.
5. For this checked-in sample workspace itself, do **not** assume local ontology-backed ingest, doctor, or reconcile-shadow commands exist unless they are actually present in `wiki/scripts/`.
6. Write or update:
   - concise summary
   - key facts
   - important claims
   - contradictions or uncertainties
   - open questions
   - links to affected wiki pages
7. Update every affected concept, entity, person, project, or timeline page.
8. Create missing pages when a concept or entity clearly deserves its own page.
9. Rebuild or refresh `wiki/_meta/index.md` if page inventory changed.
10. Append an entry to `wiki/_meta/log.md`.

If ontology-backed ingest is not available in the current workspace, continue with source registration plus explicit notes about pending canonical extraction.

## Query Workflow

When the user asks a question:

1. Read `wiki/_meta/index.md` first.
2. Identify likely relevant pages.
3. Read the smallest set of pages that can answer well.
4. Use `warehouse/jsonl/...` for provenance checks, contradiction checks, claim validation, or exact source coverage when wiki pages are too thin or uncertain.
5. Synthesize an answer grounded in the wiki, with ontology-backed verification when needed.
6. If the answer is durable, save it into `wiki/analyses/`.
7. Cross-link that analysis page from relevant pages if appropriate.
8. Append a `query` log entry for substantial work.

## Ontology-Aware Ingest And Query Defaults

- New source material enters through `raw/inbox/`.
- Repeated source processing should prefer an ontology-backed ingest skill over ad hoc manual steps.
- Direct ontology-core operation is reserved for tuning, debugging, or operator workflows.
- Important answers should still land in `wiki/analyses/` even when the ontology layer did most of the structured work.

## New Thread Bootstrap

When a new agent opens this checked-in sample workspace in a fresh conversation:

1. Read this `AGENTS.md` first.
2. Read `wiki/_meta/index.md` before answering workspace-local wiki questions.
3. Read `wiki/_meta/log.md` if recent workspace-local work or unfinished threads may matter.
4. Treat this tree as a persistent sample wiki workspace, not as the full parent DocTology runtime.
5. If the task actually targets the parent runtime, step back to the parent repository root and follow the parent root `AGENTS.md` instead.

Default startup assumptions:

- This repo-local `AGENTS.md` governs only the checked-in sample workspace rooted here.
- The local CLI in `scripts/llm_wiki.py` is intentionally minimal and does not imply the full parent runtime contract.
- If a future agent can answer from existing wiki pages, it should avoid rereading the full raw corpus unless needed for verification or coverage.

## AGENTS Vs Skills

For this repository:

- Prefer `AGENTS.md` for repo-specific workflow, page conventions, ingest/query rules, and maintenance behavior.
- Prefer a reusable skill only if the behavior should work across many repositories or outside this specific vault.
- Do not assume a custom skill will auto-activate in future conversations unless the environment explicitly exposes and triggers that skill.
- Therefore, if reliability for the next agent is the goal, encode the rule here in `AGENTS.md` and keep examples in `README.md` or `wiki/_meta/`.

## Lint Workflow

When the user asks for a health check:

Look for:

- broken wikilinks
- orphan pages
- duplicate pages with overlapping scope
- important concepts mentioned repeatedly but lacking pages
- stale summaries
- unsupported claims
- contradictions not yet surfaced

When possible, fix issues directly and record the pass in the log.

## Writing Style

- Be factual, compressed, and explicit
- Prefer synthesis over paraphrase
- Preserve provenance
- Use bullet lists when they make scanning easier
- Avoid hype language
- Distinguish fact, inference, and speculation

## Naming

- Use kebab-case filenames
- Keep names stable once linked widely
- Prefer descriptive filenames over cute ones

## Maintenance Defaults

- If a new answer would be useful later, save it
- If a page is thin but necessary, create a stub instead of omitting it
- If a source changes the meaning of an older page, revise the older page
- If a source conflicts with earlier material, note the conflict explicitly

## Safe Boundaries

- Do not silently delete meaningful content
- If merging or renaming broad pages, preserve redirects or update all inbound links
- Do not overstate certainty
- Do not fabricate citations or source coverage

## Human Collaboration

Default assumption:

- The human wants the wiki to compound over time
- The agent should leave behind clean artifacts, not just temporary chat output

If unsure whether something belongs in the wiki, prefer asking:
`Should I save this as a wiki page?`
