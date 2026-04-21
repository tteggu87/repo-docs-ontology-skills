---
name: llm-wiki-bootstrap
description: Use this skill when the user wants to scaffold a new Obsidian-first LLM Wiki workspace, bootstrap Andrej Karpathy-style LLM Wiki structure, create raw/wiki/AGENTS.md layout in a fresh project, or standardize a markdown-first knowledge vault with scripts, templates, and meta pages. Trigger on requests to set up an LLM wiki, knowledge vault, research wiki, persistent markdown memory repo, or repo-local AGENTS-driven wiki workflow, and not for existing wiki analysis-only work or ingest one source into an existing wiki.
---

# LLM Wiki Bootstrap

Create a fresh markdown-first LLM Wiki workspace that is ready for Codex-style maintenance.
The skill scaffolds the folder structure, `AGENTS.md`, starter `README.md`, local CLI, template files, and meta pages so the next agent can operate the vault consistently.
It supports both a plain wiki scaffold and an ontology-ready scaffold.

## Use This Skill For

- creating a brand-new Obsidian-first LLM Wiki repo
- setting up `raw/`, `wiki/`, and repo-local `AGENTS.md` conventions quickly
- bootstrapping a reusable wiki workspace instead of copying files by hand
- preparing a repo that future agents can reopen and maintain consistently

## Do Not Use This Skill For

- ingesting a single source into an already existing wiki
- retrofitting a mature repo without first deciding whether it should become an LLM Wiki
- ontology schema tuning in isolation

For repeated source processing inside an existing ontology-backed wiki, use `llm-wiki-ontology-ingest`.

## Workflow

1. Confirm the target directory and whether it is new or already contains files.
2. If the directory is non-empty, avoid destructive overwrite unless the user explicitly wants replacement.
3. Choose the profile:
   - `wiki-only` for a plain Obsidian-first wiki
   - `wiki-plus-ontology` when the repo should also start with `warehouse/jsonl/` and minimal intelligence manifests
4. Run `scripts/bootstrap_llm_wiki.py <target-dir> --profile <profile>` from this skill directory.
5. Inspect the generated tree and verify that these exist:
   - `AGENTS.md`
   - `README.md`
   - `raw/`
   - `wiki/`
   - `scripts/llm_wiki.py`
   - `templates/source_page_template.md`
   - `wiki/_meta/index.md`, `dashboard.md`, `log.md`
   - for `wiki-plus-ontology`, also verify:
     - `intelligence/glossary.yaml`
     - `intelligence/manifests/datasets.yaml`
     - `intelligence/manifests/actions.yaml`
     - `warehouse/jsonl/`
6. Tell the user what was created and what the next maintenance prompt should look like.

## Default Commands

Plain scaffold:

```bash
python3 scripts/bootstrap_llm_wiki.py /absolute/path/to/new-project --profile wiki-only
```

Ontology-ready scaffold:

```bash
python3 scripts/bootstrap_llm_wiki.py /absolute/path/to/new-project --profile wiki-plus-ontology
```

Add `--force` only when the user explicitly wants overwrites.

## What The Script Generates

- Obsidian-first folder layout
- repo-local `AGENTS.md`
- starter `README.md`
- minimal CLI for `ingest`, `reindex`, `lint`, `status`, `log`
- source-page template
- starter dashboard, index, and log pages
- optional ontology-ready `warehouse/jsonl/` and `intelligence/` starter files

## Customization Guidance

- If the user already has a preferred wiki policy, edit the generated `AGENTS.md` after bootstrap instead of bloating the bootstrap script with many flags.
- Keep the scaffold opinionated and small. This skill is for the first 80 percent, not every possible customization switch.
- Prefer the profile flag over adding many one-off scaffold flags.
- For details on generated files and safety boundaries, read `references/scaffold-spec.md`.

## Validation

After changes to this skill:

1. Run a quick skill validation if your environment provides one.
2. Run the bootstrap script in a temporary directory for `wiki-only`.
3. Run the bootstrap script in a second temporary directory for `wiki-plus-ontology`.
4. Verify the expected files exist for both profiles.
5. Spot-check `AGENTS.md`, `README.md`, `scripts/llm_wiki.py`, and the ontology starter manifests.

Prefer deterministic script validation over vague chat-only claims.
