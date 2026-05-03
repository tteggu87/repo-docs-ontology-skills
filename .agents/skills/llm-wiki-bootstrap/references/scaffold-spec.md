# Scaffold Spec

This skill bootstraps a small, opinionated LLM Wiki workspace.

The project-local skill package is committed under `.agents/skills`.  The
repo-local generator is authoritative for GitHub reproducibility; installed
copies under `~/.codex/skills` are downstream local installs, not required
runtime dependencies.

It supports three profiles:

- `llm-first-ontology` — default strict LLM-first ontology profile
- `wiki-only` — plain Obsidian-first wiki profile
- `wiki-plus-ontology` — deprecated legacy three-layer ontology profile

## Generated Tree: llm-first-ontology

```text
<target>/
  AGENTS.md
  README.md
  .gitignore
  docs/
    LLM_FIRST_ONTOLOGY_BOOTSTRAP_PROFILE.md
  intelligence/
    contract_index.yaml
    manifests/
      capabilities.yaml
      document_types.yaml
      frontmatter.yaml
      meta_surfaces.yaml
      page_policy.yaml
      registries.yaml
      relation_types.yaml
      semantic_workflows.yaml
      workbench.yaml
    packs/
      generic-md-note/
        pack.yaml
    policies/
      proposal_lifecycle.yaml
      semantic_boundary.yaml
  raw/
    inbox/
    processed/
    assets/
    notes/
  scripts/
    generic_ingest.py
    llm_compile_source.py
    llm_query.py
    llm_wiki.py
    pipeline_refresh.py
    proposal_review.py
    query_analysis.py
    validate_intelligence.py
    validate_profiles.py
    validate_registries.py
    validate_repo_docs_intelligence.py
    validate_workbench_manifest.py
    wiki_graph_navigation.py
  templates/
    source_page_template.md
  warehouse/
    jsonl/
      compile_proposals.jsonl
      content_units.jsonl
      documents.jsonl
      review_events.jsonl
      source_versions.jsonl
  wiki/
    _meta/
      contradiction-review.md
      dashboard.md
      index.md
      link-map.md
      log.md
      moc.md
      orphan-review.md
      source-coverage.md
    analyses/
    concepts/
    entities/
    people/
    projects/
    sources/
    timelines/
  wikiconfig.example.json
  wikiconfig.json
```

The generated `.gitignore` must ignore `wikiconfig.json`, caches, local runtime
state, and generated databases.  The generated `wikiconfig.json` is a local
disabled helper placeholder; helper-disabled semantic workflows must emit agent
handoff material rather than claim semantic success.

## Generated Tree: wiki-only

```text
<target>/
  AGENTS.md
  README.md
  .gitignore
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
  .gitignore
  intelligence/
    glossary.yaml
    manifests/
      actions.yaml
      datasets.yaml
  raw/
    inbox/
    processed/
    assets/
    notes/
  scripts/
    llm_wiki.py
    reindex_sqlite_operational.py
    refresh_duckdb_analytics.py
    verify_three_layer_drift.py
  state/
  templates/
    source_page_template.md
    llm-wiki-three-layer/
      sqlite_operational.schema.sql
      duckdb_analytical.schema.sql
  warehouse/
    jsonl/
      messages.jsonl
      documents.jsonl
      entities.jsonl
      claims.jsonl
      claim_evidence.jsonl
      segments.jsonl
      derived_edges.jsonl
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
- `wiki/` is maintained human-facing synthesis.
- `warehouse/jsonl/` is canonical structured truth for ontology-ready repos.
- `content_units` are citation anchors, not RAG chunks.
- `state/` holds rebuildable operational and analytical DB state only.
- file-layer surfaces remain the canonical truth even when later operational or analytical DB layers are introduced.
- `AGENTS.md` is the repo-local contract for future agents.
- `intelligence/` is contract-only YAML for policies, vocabularies, manifests, and validation boundaries.
- `scripts/llm_wiki.py` handles lightweight maintenance tasks.
- deterministic code may create sources, citation anchors, indexes, and validation reports but must not create semantic answer drafts.
- helper LLMs are optional accelerators; missing or disabled helpers emit agent handoff bundles/prompts.
- ontology-ready scaffolds also ship lightweight SQLite/DuckDB rebuild helpers plus schema templates.
- The scaffold should be immediately usable without third-party Python dependencies for basic generation.

## Three-Layer Extension Path

When this scaffold later grows into a longer-lived LLM Wiki system, prefer the staged three-layer path:

1. file-first canonical wiki surface
2. SQLite operational index
3. DuckDB analytical warehouse

Supporting references:

- `references/three-layer-taxonomy.md`
- `references/three-layer-file-contract.md`
- `templates/llm-wiki-three-layer/`

Those materials are still guidance and template surfaces. The scaffold ships lightweight local rebuild helpers, not a heavy always-on runtime stack.

## Safety Rules

- Do not overwrite non-empty targets unless the user explicitly approves and the command uses `--force`.
- Do not add heavy infra by default.
- Do not assume embeddings or vector search are required.
- Do not treat ontology-ready scaffolding as a requirement for every repo.
- Do not turn helper LLM absence into heuristic semantic success.
- Do not treat unreviewed compile proposals as query evidence.
- Keep the generated README understandable for a human opening the repo for the first time.

## Suggested Follow-Up

After scaffolding:

1. Open the folder as an Obsidian vault.
2. Add the first source to `raw/inbox/`.
3. Ask Codex to use the repo-local `AGENTS.md`.
4. Register the source with the local CLI or profile-aware ingest path.
5. In `llm-first-ontology`, use LLM compile proposals and human review before active semantic page updates.
6. In `wiki-plus-ontology`, treat the profile as legacy and prefer `llm-first-ontology` for new repos.
7. If the user later wants a longer-lived architecture, consult the three-layer references before adding SQLite or DuckDB.
