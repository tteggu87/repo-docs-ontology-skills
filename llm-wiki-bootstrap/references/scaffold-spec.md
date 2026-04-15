# Scaffold Spec

This skill bootstraps a small, opinionated LLM Wiki workspace.
It supports two profiles:

- `wiki-only`
- `wiki-plus-ontology`

## Generated Tree

```text
<target>/
  AGENTS.md
  README.md
  raw/
    inbox/
    processed/
    assets/
    notes/
  scripts/
    llm_wiki.py
  templates/
    source_page_template.md
  wiki/
    _meta/
      dashboard.md
      index.md
      log.md
    analyses/
    concepts/
    entities/
    people/
    projects/
    sources/
    timelines/
```

## Generated Tree: wiki-plus-ontology

```text
<target>/
  AGENTS.md
  README.md
  intelligence/
    glossary.yaml
    manifests/
      actions.yaml
      datasets.yaml
      relations.yaml
      source_families.yaml
    policies/
      truth-boundaries.yaml
  raw/
    inbox/
    processed/
    assets/
    notes/
  scripts/
    llm_wiki.py
    ontology_refresh.py
  templates/
    source_page_template.md
  warehouse/
    jsonl/
  wiki/
    _meta/
      dashboard.md
      index.md
      log.md
    analyses/
    concepts/
    entities/
    people/
    projects/
    sources/
    timelines/
```

## Design Intent

- `raw/` is immutable source storage.
- `wiki/` is maintained synthesis.
- `warehouse/jsonl/` is optional canonical structured truth for ontology-ready repos.
- `AGENTS.md` is the repo-local contract for future agents.
- `intelligence/` is optional repo-local vocabulary plus dataset/action contracts.
- For ontology-ready repos, `intelligence/` also includes relation vocabulary, source-family hints, and truth-boundary policies.
- `scripts/llm_wiki.py` handles lightweight maintenance tasks only.
- `scripts/ontology_refresh.py` is the minimal ontology-ready refresh helper; it does not replace full ontology extraction.
- The scaffold should be immediately usable without third-party Python dependencies.

## Safety Rules

- Do not overwrite non-empty targets unless the user explicitly approves and the command uses `--force`.
- Do not add heavy infra by default.
- Do not assume embeddings or vector search are required.
- Do not treat ontology-ready scaffolding as a requirement for every repo.
- Keep the generated README understandable for a human opening the repo for the first time.

## Suggested Follow-Up

After scaffolding:

1. Open the folder as an Obsidian vault.
2. Add the first source to `raw/inbox/`.
3. Ask Codex to use the repo-local `AGENTS.md`.
4. Register the source with the local CLI.
5. If the repo uses `wiki-plus-ontology`, run ontology-backed ingest from there.
6. Run `python scripts/ontology_refresh.py` to refresh minimal ontology-ready state.
