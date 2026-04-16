# LLM Wiki for Obsidian

An Obsidian-first, agent-maintained living knowledge workspace inspired by Andrej Karpathy's `LLM Wiki` idea:
[LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

This repository is no longer just a starter scaffold.
It already contains:

- an Obsidian-first wiki workspace
- a canonical JSONL warehouse for structured truth
- a minimal local CLI for wiki maintenance
- a lightweight incremental ingest path for recurring exports
- repo-local operating rules in `AGENTS.md` and `intelligence/`
- an optional local sidecar workbench in `apps/workbench/` backed by `scripts/workbench_api.py`

## What This System Is

This is not a generic RAG chatbot.

It is a persistent knowledge base with four layers:

1. `raw/`: immutable source material you collect
2. `warehouse/jsonl/`: canonical structured ontology truth
3. `wiki/`: markdown pages the LLM creates and updates for human reading
4. `AGENTS.md` plus `intelligence/`: the operating contract that tells the LLM how to work

You read and curate.
The agent registers sources, updates canonical truth when ontology-backed or incremental ingest is available, projects synthesis into the wiki, and keeps the workspace healthy.

## Current Repository Reality

At the time of this update, the repo already includes:

- a real Agent Korea KakaoTalk source corpus in `raw/inbox/`
- canonical records under `warehouse/jsonl/`
- populated `wiki/people/`, `wiki/concepts/`, `wiki/sources/`, `wiki/analyses/`, and `wiki/timelines/`
- incremental ingest tooling for repeated export files of a known source family

So treat this repo as an active knowledge workspace, not an empty template.

## Folder Layout

```text
llm-wiki-obsidian/
├── AGENTS.md
├── README.md
├── apps/
│   └── workbench/
├── raw/
│   ├── inbox/
│   ├── processed/
│   ├── assets/
│   └── notes/
├── intelligence/
│   ├── glossary.yaml
│   └── manifests/
├── warehouse/
│   ├── jsonl/
│   └── graph_projection/
├── scripts/
│   ├── llm_wiki.py
│   ├── incremental_ingest.py
│   ├── incremental_support.py
│   └── migrate_incremental_jsonl.py
├── templates/
│   └── source_page_template.md
└── wiki/
    ├── _meta/
    ├── analyses/
    ├── concepts/
    ├── entities/
    ├── people/
    ├── projects/
    ├── sources/
    └── timelines/
```

## Dependency Notes

Core wiki maintenance uses the Python standard library.

However, incremental ingest currently requires:

- `PyYAML` for `scripts/incremental_ingest.py`

Recommended setup:

```bash
cd /path/to/your/llm-wiki-obsidian
python3 -m venv .venv
source .venv/bin/activate
pip install pyyaml
```

For the optional workbench:

```bash
cd apps/workbench
npm ci
```

Windows batch helpers:

- `install_windows.bat`
  - creates `.venv`
  - upgrades `pip`
  - installs `pyyaml`
  - runs `npm ci` in `apps/workbench`
- `run_windows_workbench.bat`
  - starts `python scripts\workbench_api.py --serve`
  - starts the Vite frontend on `http://127.0.0.1:4174/#home`

If you are on Windows, run:

```bat
install_windows.bat
run_windows_workbench.bat
```

## Quick Start

### 1. Open This Folder As An Obsidian Vault

In Obsidian:

1. `Open folder as vault`
2. Select `/path/to/your/llm-wiki-obsidian`

Recommended Obsidian settings:

- Files and Links -> `New link format`: `Relative path to file`
- Files and Links -> `Use [[Wikilinks]]`: enabled
- Files and Links -> `Attachment folder path`: `raw/assets`

Helpful plugins:

- `Dataview`
- `Web Clipper`
- `Templater` (optional)
- `Marp` (optional for decks)

### 2. Check Current State

```bash
python3 scripts/llm_wiki.py status
python3 scripts/llm_wiki.py lint
python3 -m unittest -q
```

### 3. Add Sources

Drop files into `raw/inbox/`.

Examples:

- Markdown clipped from a web article
- Notes exported from Obsidian or Apple Notes
- Meeting transcripts
- Research summaries
- Plain text files
- Repeated export files for a known source family

If a source is a PDF, web page, or image-heavy document, keep the raw file in `raw/inbox/` and either:

- also save a companion markdown/text note into `raw/notes/`, or
- ask the agent to read the file directly and write the wiki updates

## Workflows

### A. Register A One-Off Source

Run:

```bash
python3 scripts/llm_wiki.py ingest raw/inbox/my-source.md --title "My Source Title"
```

This does three things:

- creates a source page stub in `wiki/sources/`
- appends an ingest entry to `wiki/_meta/log.md`
- rebuilds `wiki/_meta/index.md`

This is source registration only.
It does not auto-summarize the source or perform ontology-backed extraction.
That synthesis is still expected from the agent.

### B. Run Incremental Ingest For A Repeated Export

For recurring exports of a known source family:

```bash
python3 scripts/incremental_ingest.py raw/inbox/<export-file>
```

This workflow:

- resolves the source family from `intelligence/manifests/source_families.yaml`
- registers an export version in `warehouse/jsonl/source_versions.jsonl`
- upserts canonical records such as `messages.jsonl` and `documents.jsonl`
- refreshes the related wiki source status page and meta pages
- returns explicit lineage and affected-surface signals so operators can see which canonical registries and wiki surfaces changed

Important:

- the current implementation is lightweight and intentionally narrow
- today it is effectively specialized around the Agent Korea KakaoTalk export family
- the manifest makes expansion easier, but generic parser coverage is not finished yet

### C. Ask The Agent To Maintain The Wiki

Use prompts like:

- `Use AGENTS.md. Read raw/inbox/my-source.md and fully ingest it into the wiki.`
- `Use AGENTS.md. Update the relevant concept, entity, and project pages based on the new source.`
- `Use AGENTS.md. Create any missing pages that should exist after this ingest.`
- `Use AGENTS.md. Run a wiki health check and fix broken or missing cross-links.`
- `Use AGENTS.md. Answer my question using the wiki, then save the answer under wiki/analyses/.`

Before substantial wiki work in a fresh conversation, the agent should:

1. read `AGENTS.md`
2. read `wiki/_meta/index.md`
3. scan the newest relevant entries in `wiki/_meta/log.md`

### D. Use The Optional Sidecar Workbench

In one terminal:

```bash
python3 scripts/workbench_api.py --serve
```

In another:

```bash
cd apps/workbench
npm run dev
```

Current workbench scope:

- dashboard summary
- operator review surfaces for low-coverage, stale, and uncertainty candidates
- live wiki and source reader
- source coverage and claim review queues from canonical registries
- warehouse summary
- guarded `status` / `reindex` / `lint` actions
- repo-local Ask preview with provenance sections, related page suggestions, bounded analysis draft saves, and confident related-page link-back
- related-page navigation from Ask, Pages, and Sources panels
- backend-gated claim approve/reject actions from operator review surfaces
- optional backend-gated helper-model draft actions loaded from repo-root `wikiconfig.json`

The workbench is additive. Obsidian and `wiki/` remain the default reading/editing surface.

If helper-model config is introduced:

- keep the live file at repo root as `wikiconfig.json`
- keep it server-side only
- use `llmWiki.enabled: false` to disable helper-model API usage and stay in local-only mode
- keep the current compatibility layer limited to OpenAI-compatible chat endpoints
- do not let the browser read or own provider secrets
- keep helper-model outputs draft-only

## Commands

### Status

```bash
python3 scripts/llm_wiki.py status
```

Shows counts for raw files, wiki pages, log entries, and index entries.

### Rebuild Index

```bash
python3 scripts/llm_wiki.py reindex
```

Recreates `wiki/_meta/index.md` from the current wiki pages while preserving the existing `created` date.

### Lint

```bash
python3 scripts/llm_wiki.py lint
```

Checks for:

- broken wikilinks
- orphan pages
- pages without YAML frontmatter
- pages missing from the index
- oversized pages
- duplicate titles

### Append A Log Entry

```bash
python3 scripts/llm_wiki.py log query "Compared two vendors" "Saved the result to wiki/analyses/."
```

## Design Notes

### What Is Strong Today

- durable markdown synthesis as the main human interface
- explicit truth separation between raw source, canonical structured truth, and human-facing pages
- repo-local rules in `AGENTS.md` so future agents can resume with less drift
- lightweight operational tooling that is easy to inspect and modify
- a sidecar workbench that can inspect the repo through explicit backend routes instead of browser-side file or model hacks

### What Is Still Early

- incremental ingest is not yet broadly generalized beyond the current known family
- higher-order semantic extraction remains sparse compared with message/event coverage
- `warehouse/graph_projection/` is still optional and mostly a placeholder layer
- the Ask workspace now saves bounded analysis drafts and performs confident related-page link-back, but it is not yet a full durable answer loop with richer synthesis policies
- this is not yet a full retrieval product or graph reasoning runtime

## Current Quality Policy

- duplicate page titles are lint-worthy and should be resolved or intentionally renamed
- oversized analyses are allowed temporarily, but are tracked refactor targets rather than hidden debt
- new workbench API surfaces should land with route-level tests
- the browser must not mutate `raw/` or `warehouse/jsonl/` directly

## Suggested Operating Rhythm

### Ingest One Source Carefully

1. Put a source into `raw/inbox/`
2. If it is a one-off source, register it with `python3 scripts/llm_wiki.py ingest ...`
3. If it is a repeated export from a known family, run `python3 scripts/incremental_ingest.py ...`
4. Ask the agent to update canonical truth and/or wiki pages
5. Review the changed pages in Obsidian
6. Move the raw file into `raw/processed/` when you are happy

### Query / Review Cycle

1. Ask a question against the current wiki
2. Save durable answers into `wiki/analyses/`
3. Re-run `lint` periodically
4. Refactor page structure when a page becomes too large or too mixed

## Scaling Later

As the repo grows, likely next additions are:

- broader source-family coverage
- stronger claim and segment extraction
- derived edges or graph projection that earns its keep
- retrieval utilities over canonical JSONL plus curated wiki pages
- richer dashboards and review workflows

Until then, the current combination of `AGENTS.md`, `intelligence/`, `warehouse/jsonl/`, `wiki/_meta/index.md`, and `wiki/_meta/log.md` is the real operating surface.
