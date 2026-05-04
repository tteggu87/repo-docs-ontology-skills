# LLM-First Ontology Bootstrap Profile

Updated: 2026-05-02

## Purpose

`llm-wiki-bootstrap --profile llm-first-ontology` creates a new Obsidian-first LLM Wiki workspace that starts with the same strict semantic boundaries that DocTology now uses.

This profile is for new repositories. It must not be run over the current DocTology repository as a re-init mechanism.

As of 2026-05-02, this profile is the promoted default in the installed `llm-wiki-bootstrap` skill. The legacy `wiki-plus-ontology` profile remains available only for compatibility and emits a deprecation warning.

## Generated directory tree

The profile should generate:

```text
raw/
  inbox/
  processed/
  notes/
wiki/
  sources/
  concepts/
  entities/
  projects/
  analyses/
  _meta/
warehouse/
  jsonl/
  graph_projection/
intelligence/
  contract_index.yaml
  glossary.yaml
  manifests/
  policies/
  packs/
  registry/
  schemas/
scripts/
  reindex_sqlite_operational.py
  refresh_duckdb_analytics.py
  verify_three_layer_drift.py
state/
templates/
  llm-wiki-three-layer/
tests/
docs/
AGENTS.md
README.md
.gitignore
wikiconfig.example.json
wikiconfig.json
```

## Generated YAML contracts

The profile should generate contract-only YAML files:

- `intelligence/contract_index.yaml`
- `intelligence/policies/semantic_boundary.yaml`
- `intelligence/policies/proposal_lifecycle.yaml`
- `intelligence/manifests/semantic_workflows.yaml`
- `intelligence/manifests/page_policy.yaml`
- `intelligence/manifests/meta_surfaces.yaml`
- `intelligence/manifests/relation_types.yaml`
- `intelligence/manifests/registries.yaml`
- `intelligence/manifests/source_families.yaml`
- `intelligence/manifests/actions.yaml`
- `intelligence/manifests/datasets.yaml`
- `intelligence/manifests/entities.yaml`
- `intelligence/manifests/workbench.yaml`
- `intelligence/registry/capabilities.yaml`

These YAML files must not contain source summaries, answer drafts, inferred facts, or semantic scores.

## Generated scripts

The minimum generated scripts should be thin execution surfaces:

- `scripts/generic_ingest.py`
- `scripts/llm_compile_source.py`
- `scripts/llm_query.py`
- `scripts/wiki_graph_navigation.py`
- `scripts/validate_intelligence.py`
- `scripts/validate_workbench_manifest.py`
- `scripts/validate_profiles.py`
- `scripts/validate_registries.py`
- `scripts/validate_repo_docs_intelligence.py`
- `scripts/proposal_review.py`
- `scripts/reindex_sqlite_operational.py`
- `scripts/refresh_duckdb_analytics.py`
- `scripts/verify_three_layer_drift.py`

Python owns execution, validation, IDs, line ranges, citation anchors, source projection, indexes, logs, and navigation pages.

The three-layer helper scripts are derived-state maintenance helpers:

- `reindex_sqlite_operational.py` rebuilds `state/wiki_index.sqlite` from canonical wiki files
- `refresh_duckdb_analytics.py` refreshes `state/wiki_analytics.duckdb` from canonical JSONL and wiki files
- `verify_three_layer_drift.py` checks coarse drift across file truth, SQLite state, and DuckDB analytics

They must not become canonical truth owners.

## Default no-fallback behavior

The generated workspace must default to:

- semantic LLM required for semantic compile/query
- helper LLM optional for semantic compile/query
- compile without helper LLM emits an agent handoff bundle and does not claim semantic success
- query without helper LLM emits an agent handoff prompt and does not claim semantic success
- prompt bundle emission only through explicit flags
- no regex/lexical fallback for semantic selection or answers
- deterministic preview surfaces labeled as diagnostics only
- unreviewed compile proposals excluded from query evidence
- `wikiconfig.example.json` committed as the format reference
- `wikiconfig.json` generated as a local disabled placeholder and ignored by `.gitignore`

`llmWiki.enabled=false` means local scripts will not call a helper-model API. It does not silently fall back to a regex heuristic. Instead, local scripts emit an agent handoff prompt/bundle for the surrounding chat agent, which can perform the semantic work according to `AGENTS.md` and save a proposal or reviewed page intentionally.

`llmWiki.enabled=true` means strict compile/query uses `models[0]` from `wikiconfig.json` as the backend helper LLM.

## Generated proposal lifecycle

Compile proposals should start as:

```yaml
status: draft
analysis_method: llm_compile_proposal
trust_level: human_review_required
```

Allowed lifecycle:

```text
draft -> accepted | rejected
accepted -> applied
rejected -> terminal
applied -> terminal
```

Before human review, proposals are not active wiki truth and are not query evidence.

## Smoke test after bootstrap

After generating a new repo, the profile should run or instruct the operator to run:

```bash
python3 scripts/validate_repo_docs_intelligence.py
python3 scripts/validate_intelligence.py
python3 scripts/validate_workbench_manifest.py
python3 scripts/validate_profiles.py
python3 scripts/validate_registries.py
python3 -m pytest -q
```

Strict LLM smoke:

```bash
python3 scripts/llm_query.py "smoke test"
# expected: agent_handoff without helper LLM; not semantic success

python3 scripts/llm_query.py "smoke test" --emit-selection-prompt
# expected: zero, selection prompt only
```

Compile smoke should be run after a source page exists:

```bash
python3 scripts/llm_compile_source.py --source-page wiki/sources/<source>.md
# expected: agent_handoff without helper LLM; not semantic success

python3 scripts/llm_compile_source.py --source-page wiki/sources/<source>.md --emit-bundle
# expected: zero, prompt bundle only
```

Three-layer helper smoke:

```bash
python3 scripts/reindex_sqlite_operational.py --repo-root .
python3 scripts/verify_three_layer_drift.py --repo-root .

# Optional when duckdb is installed:
python3 scripts/refresh_duckdb_analytics.py --repo-root .
python3 scripts/verify_three_layer_drift.py --repo-root .
```

## What not to generate

The bootstrap profile must not generate:

- heuristic semantic analyzers
- deterministic answer drafts
- automatic concept/entity/project page rewrites from LLM output
- top-k RAG answer chunk logic as the primary semantic path
- browser routes that directly mutate `raw/` or broad `warehouse/jsonl/`
- YAML files that contain asserted source facts or reasoning summaries

## Promotion status

DocTology remains the stabilization source. The current profile has been promoted because the proposal lifecycle, registries, validators, and strict route tests have been implemented in DocTology and verified.

Future changes should still be stabilized in DocTology first, then copied into the bootstrap profile after validation.
