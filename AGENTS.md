# AGENTS.md

This repository uses the project-local wiki under `wiki/` as a durable context surface.

## Agent Entry Contract

Before making meaningful code, architecture, or product-direction changes:

1. read this root `AGENTS.md`
2. read `wiki/AGENTS.md` if the `wiki/` workspace exists
3. read `wiki/_meta/index.md` if it exists
4. read recent relevant entries in `wiki/_meta/log.md` if it exists
5. read the smallest relevant wiki pages before raw files when answering knowledge questions

Do not treat the chat transcript alone as the full source of working context when the wiki has already accumulated durable analysis.

## Operation Classifier

Classify each non-trivial request as one primary operation before acting:

- `ingest`
- `query`
- `analysis`
- `maintenance`
- `claim-review`
- `refactor`
- `tooling`

Report files read, files changed or proposed, provenance basis, post-check result, and unresolved follow-ups when the work is durable.

## Scope Guidance

- `wiki/` is the project-local knowledge workspace
- `raw/` is immutable source truth
- `warehouse/jsonl/` is canonical structured truth and provenance
- `wiki/` is human-facing synthesis
- graph projection and retrieval outputs are derived aids, never canonical truth
- `intelligence/` contains contract-only YAML; it must not become a second wiki or reasoning layer
- code, docs, and product decisions should prefer the latest durable wiki context when relevant
- if there is a conflict between this file and a deeper `AGENTS.md`, the deeper file wins for files in its scope

## LLM Wiki Growth Loop

The default growth loop is intentionally simple:

1. add or reference source material under `raw/inbox/`
2. register/project source pages and citation anchors
3. use LLM-first compile/query over the wiki, ontology, source pages, and citation anchors
4. save compile results as human-review proposals before changing active concept/entity/project pages
5. apply reviewed updates to the active wiki
6. refresh meta surfaces so future LLM sessions can navigate the wiki map before reading page bodies

This repository should feel like a wiki that grows with evidence, not like a graph platform or a YAML rule engine.

## Strict LLM-First Semantic Boundary

Deterministic code may read files, compute IDs, calculate line ranges, create citation anchors, project source pages, refresh indexes, and validate structure.

Deterministic code must not:

- generate semantic answer drafts
- infer semantic truth
- silently fall back from failed/missing LLM output to regex or lexical answer paths
- treat graph projection, retrieval output, or unreviewed compile proposals as canonical truth
- apply compile results directly to active semantic wiki pages without review

Helper LLM configuration in `wikiconfig.json` is optional. If no helper is enabled, scripts should hand off a prompt/bundle to the surrounding chat agent instead of claiming semantic success. The chat agent may perform the LLM-first work directly by reading the repo contracts, wiki, ontology, source pages, and citation anchors.

`content_units` are citation anchors. They are not RAG chunks for deterministic answer generation.

## Capability And Fallback Matrix

- If shell is available, run documented status, lint, validation, and tests.
- If helper LLM is enabled in `wikiconfig.json`, scripts may use it for bounded compile/query work.
- If helper LLM is disabled or absent, scripts must hand off prompt/bundle material to the surrounding chat agent.
- If writes are unavailable, return commit-ready markdown or patches instead of silently skipping durable work.

## Write Policy

Safe automatic writes are limited to source projections, citation anchors, wiki meta surfaces, and durable analysis pages under `wiki/analyses/`.

Review is required before rewriting active concept/entity/project/timeline pages, approving/rejecting claims, resolving contradictions, or applying compile proposals.

## Durable Answer Rule

Durable answers include comparisons, synthesis, recommendations, recurring questions, contradiction/gap findings, and decisions. Save durable answers under `wiki/analyses/` when writes are available. Active semantic page updates should remain proposed until reviewed.

## Coding Workflow

When implementing code changes:

1. recover context from the wiki first
2. make the code change
3. if the change creates durable product, architecture, or contract knowledge, update the wiki
4. if the change creates semantic wiki updates, prefer a proposal unless the user explicitly asked for direct active-page edits

## Wiki Relationship

Use the wiki for:

- product direction notes
- architecture decisions
- contract clarifications
- implementation progress
- unresolved design questions

Keep the wiki readable for future agents so they can recover context without re-deriving everything from scratch.
