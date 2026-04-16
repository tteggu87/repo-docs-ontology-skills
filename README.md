<p align="center">
  <img src="apps/workbench/public/doctology-logo.jpeg" alt="DocTology logo" width="460">
</p>

# DocTology

[English](README.md) | [한국어](README.ko.md)

DocTology is not just an LLM Wiki. It is a personal knowledge-management starter kit that combines an Obsidian-first wiki with a canonical ontology layer and repo-intelligence contracts.

Its core direction is:

- keep note growth more manageable for agents by pairing the wiki with an ontology layer instead of forcing everything through raw page reading
- support ontology graph and neighborhood expansion when deeper structure is needed
- provide agent-readable project memory through wiki pages, JSONL ontology registries, and intelligence contracts
- package a reusable skill pack, a local reference runtime, and a private-workspace bootstrap baseline in one repository

In one repository, DocTology gives you:

- a portable `.agent/skills/` pack for bootstrap, ontology, and operator workflows
- a runnable local reference runtime with an LLM Wiki CLI and optional workbench UI
- a clean baseline for bootstrapping your own private workspace without committing corpus data

![DocTology workbench question workspace](assets/readme/doctology-workbench-question-workspace.jpg)

_DocTology workbench question workspace — review the current wiki, inspect repo-local query previews, and save bounded analysis pages._

Current workbench reality: this is primarily a read-and-review surface for the generated wiki and related previews. It is not yet a freeform, actively conversational LLM chat workspace.

![Reference example: knowledge growing into a wiki](assets/readme/doctology-reference-obsidian-notes-forming-a-wiki.jpg)

_Reference example — a view of knowledge growing into a wiki as previously unlinked Obsidian notes begin to form visible structure and neighborhoods._

## Choose your starting path first

### 1) Do you want to start with an LLM Wiki?
Then start with `llm-wiki-bootstrap`.

The flow is simple:

- run the wiki bootstrap
- put documents into the generated `raw/inbox/`
- run `llm-wiki-ontology-ingest`
- keep growing the wiki through question and analysis workflows

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

## About the checked-in reference runtime

The workbench included in this repository is currently closer to a read-and-review surface than a freeform conversational LLM app.

Its role today is mainly to:

- inspect the generated wiki
- review repo-local previews
- save bounded analysis pages

So the main point of this README is not detailed runtime setup. It is understanding **which bootstrap to choose and which memory layer you want to build first**.
