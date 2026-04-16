<p align="center">
  <img src="apps/workbench/public/doctology-logo.jpeg" alt="DocTology logo" width="460">
</p>

# DocTology

[English](README.md) | [한국어](README.ko.md)

DocTology is a **wiki-first knowledge operating system for humans and agents**.

It helps you build a repository where:

- humans read and maintain a durable wiki
- agents verify claims against canonical JSONL truth
- graph and operator workflows remain optional support layers instead of becoming the product face

The core idea is simple:

- start with an Obsidian-first wiki that people can actually read
- add canonical ontology truth only when stronger provenance or contradiction handling becomes useful
- add graph or operator workflows only when deeper structure or repeated maintenance really earns its keep

In one repository, DocTology gives you:

- a portable skill pack for bootstrap, ontology, and operator workflows
- a runnable local reference runtime with an LLM Wiki CLI and optional workbench UI
- a clean baseline for bootstrapping your own private workspace without committing corpus data

## What this is

DocTology is not just a notes repo, not just an ontology toolkit, and not just a graph experiment.

It is a way to build a knowledge system where:

- the **wiki** is the front surface for human reading and synthesis
- **canonical JSONL** is the back surface for machine-truth, provenance, and review state
- **graph/operator layers** are optional extensions, not mandatory complexity on day one

## Who this is for

Use DocTology if you want:

- a readable knowledge base, not just a vector index or raw context dump
- stronger provenance than plain notes
- a system that can grow from personal wiki -> ontology-backed verification -> optional graph/operator workflows

This repository is best for teams or individuals who want their knowledge system to stay readable for humans **and** reliable for agents.

![DocTology workbench question workspace](assets/readme/doctology-workbench-question-workspace.jpg)

_DocTology workbench question workspace — review the current wiki, inspect repo-local query previews, and save bounded analysis pages._

Current workbench reality: this is primarily a read-and-review surface for the generated wiki and related previews. It is not yet a freeform, actively conversational LLM chat workspace.

![Reference example: knowledge growing into a wiki](assets/readme/doctology-reference-obsidian-notes-forming-a-wiki.jpg)

_Reference example — a view of knowledge growing into a wiki as previously unlinked Obsidian notes begin to form visible structure and neighborhoods._

## Default path

If you are unsure where to start, use the default DocTology path:

1. bootstrap a wiki-first workspace
2. ingest sources into wiki + canonical ontology
3. use route receipts and operator workflows only as complexity grows

That default path is the main product promise:

- readable wiki first
- verifiable truth second
- graph/operator complexity only when it becomes genuinely useful

## Choose your starting path first

### 1) Do you want to start with an LLM Wiki?
Then start with `llm-wiki-bootstrap`.

The flow is simple:

- run the wiki bootstrap
- put documents into the generated `raw/inbox/`
- run `llm-wiki-ontology-ingest`
- keep growing the wiki through question and analysis workflows

Current ontology-profile bootstrap behavior now also ships lightweight local rebuild helpers and state paths for longer-lived repos:

- `state/wiki_index.sqlite`
- `state/analytics.duckdb`
- `scripts/reindex_sqlite_operational.py`
- `scripts/refresh_duckdb_analytics.py`
- `scripts/verify_three_layer_drift.py`

In other words, the first step is always **wiki-first**.

### 2) Do you want to redefine ontology relationships inside the generated wiki?
Then use `lightweight-ontology-core`.

At this stage you are:

- refining the canonical ontology layer under the wiki
- tightening entities, claims, evidence, and relations in JSONL truth
- and, when needed, extending into graph / neighborhood workflows later with `lg-ontology`

This is the stage for strengthening structure after the wiki already exists.

### 3) Do you want a project-specific memory store instead?
Then use `repo-docs-intelligence-bootstrap`.

This path is better for:

- capturing the current state of a specific codebase or project
- building agent-readable project memory
- establishing AGENTS and intelligence contracts in a repo-docs intelligence style

In other words, this is an **alternative starting bootstrap**, not something you stack on top of the wiki bootstrap.

## Caution

**Use only one bootstrap to start.**

If you run multiple bootstraps in sequence, `AGENTS.md` can be overwritten and the earlier operating rules may be invalidated.

Choose first:

- do you want to grow an LLM Wiki?
- or do you want repo-focused intelligence / project memory?

Both matter, but the initial bootstrap should be only one.

## Core skill paths

- `llm-wiki-bootstrap`
  - start an Obsidian-first LLM Wiki
- `llm-wiki-ontology-ingest`
  - ingest inbox documents into an ontology-backed wiki
- `lightweight-ontology-core`
  - refine canonical ontology truth beneath the wiki
- `lg-ontology`
  - extend into ontology graph / neighborhood exploration
- `repo-docs-intelligence-bootstrap`
  - bootstrap project-specific memory / repo intelligence

## Three-layer operating model

For longer-lived wiki systems, the recommended layering is:

1. **files as canonical truth**
   - markdown, yaml, and jsonl remain the durable truth surface
2. **SQLite as operational index**
   - backlinks, unresolved links, aliases, memories, and jobs
3. **DuckDB as analytical warehouse**
   - claims, entities, relations, coverage snapshots, and audit-oriented inspection

The intended rollout is:

- v0: file-first wiki
- v1: SQLite operational index
- v2: DuckDB analytical warehouse

This keeps the wiki readable for humans, trustworthy for agents, and rebuildable when derived layers fail.

## About the checked-in reference runtime

The workbench included in this repository is currently closer to a read-and-review surface than a freeform conversational LLM app.

Its role today is mainly to:

- inspect the generated wiki
- review repo-local previews
- save bounded analysis pages

So the main point of this README is not detailed runtime setup. It is understanding **which bootstrap to choose and which memory layer you want to build first**.
