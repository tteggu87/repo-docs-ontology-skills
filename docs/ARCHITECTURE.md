# Architecture

Updated: 2026-05-08

## Canonical entrypoints

- `scripts/llm_wiki.py`
  - local maintenance CLI for `ingest`, `reindex`, `lint`, `status`, and `log`
  - owns wiki index rebuild and wiki health checks
- `scripts/llm_full_ingest.py`
  - configured-LLM full growth CLI for `dry_run` and `--apply`
  - keeps `scripts/llm_wiki.py ingest` registration-only
  - completes source pages, creates/appends affected wiki pages, appends proposed JSONL records, refreshes index/log, and writes ingest reports
  - forbids raw mutation, accepted-truth automation, delete, rename, merge, and auto-commit
- `scripts/wiki_growth_graph.py`
  - strict LangGraph source-page growth runtime
  - requires LangGraph plus a configured ingest LLM and fails fast without semantic fallback
- `scripts/pipeline_check.py`
  - structural route checker for source registration, reports, proposed JSONL, and broader wiki projection
  - never upgrades structural presence into accepted semantic truth
- `scripts/incremental_ingest.py`
  - repeated-export ingest CLI
  - resolves source families from `intelligence/manifests/source_families.yaml`
  - upserts canonical sequential records into `warehouse/jsonl/`
  - refreshes affected wiki source pages and meta pages
- `scripts/workbench_api.py`
  - live compatibility wrapper
  - imports the actual workbench implementation from `scripts/workbench/`

## Workbench runtime split

- `scripts/workbench/server.py`
  - HTTP routes and CLI server entrypoints
  - explicit route surface such as `/api/workbench/summary`, `/api/wiki/page/<stem>`, `/api/query/preview`, and bounded POST actions
- `scripts/workbench/repository.py`
  - repository-facing read model
  - bounded write actions for analysis saves and claim review
  - bounded helper-model draft actions
  - bridges adapter requests to repo files and `scripts/llm_wiki.py`
- `scripts/workbench/common.py`
  - shared constants and helpers
  - defines explicit allowed actions and workbench write prefixes
- `scripts/workbench/llm_config.py`
  - repo-root `wikiconfig.json` loader for backend-only helper-model actions
  - normalizes a whitelisted subset only

## Data flow

### Source registration

1. Human adds a file under `raw/inbox/`
2. `python3 scripts/llm_wiki.py ingest ...` creates or reuses a source page
3. The CLI appends `wiki/_meta/log.md`
4. The CLI rebuilds `wiki/_meta/index.md`

This is source registration only. It does not imply that canonical ontology
registries, affected concept pages, or review surfaces have been fully updated.

### Closed ingest lifecycle

1. Register source identity through the local wiki-maintenance path
2. Append proposed JSONL records under `warehouse/jsonl/proposed_*.jsonl` when the configured LLM emits source-backed candidates
3. Project source-backed updates into the human-facing wiki
4. Refresh `wiki/_meta/index.md`
5. Append `wiki/_meta/log.md`
6. Run structural validation
7. Report updated, skipped, not-applicable, and pending artifacts

The lifecycle is closed by artifact coverage, not by a hardcoded semantic
router. Filename, keyword, or token-shape checks must not decide meaning.
Accepted canonical truth remains review-gated; automatic full ingest writes
proposed records only.

### Incremental ingest

1. Human adds a repeated export under `raw/inbox/`
2. `scripts/incremental_ingest.py` resolves a source family from `intelligence/manifests/source_families.yaml`
3. Runtime logic fingerprints rows and upserts canonical entries into:
   - `warehouse/jsonl/documents.jsonl`
   - `warehouse/jsonl/messages.jsonl`
   - `warehouse/jsonl/source_versions.jsonl`
4. The workflow writes or updates a source-family incremental status page under `wiki/sources/`
5. The workflow rebuilds `wiki/_meta/index.md` and appends `wiki/_meta/log.md`

### Workbench query and review flow

1. The frontend in `apps/workbench/` calls explicit adapter routes only
2. `scripts/workbench/server.py` routes the request
3. `WorkbenchRepository` reads wiki pages first, then canonical registries when needed
4. Bounded write actions may:
   - save a draft analysis under `wiki/analyses/`
   - add bounded related-analysis link-backs on confident related pages
   - update `warehouse/jsonl/claims.jsonl` review state
   - append `wiki/_meta/log.md`
   - rebuild `wiki/_meta/index.md`

### Helper-model config and draft flow

1. The backend may read `wikiconfig.json` from repo root only
2. No parent-directory or workspace-wide config crawl is allowed
3. `llmWiki.enabled` may disable helper-model API usage while keeping the repo in local-only mode
4. Only a whitelisted subset is normalized:
   - `models`
   - `embeddingsProvider`
   - `rerankerProvider`
5. The current helper-model compatibility path is limited to OpenAI-compatible chat providers
6. Browser routes must not expose provider secrets or raw provider internals
7. Workbench helper-model routes must return draft output only and must not write to `raw/` or `warehouse/jsonl/`
8. Helper-model source reads must stay under `raw/inbox/`, `raw/processed/`, or `raw/notes/`

## Configured full ingest flow

1. Human adds a source under `raw/inbox/`
2. `python3 scripts/llm_full_ingest.py raw/inbox/source.md --apply` verifies configured helper LLM availability
3. The runner registers the source through `scripts/llm_wiki.py ingest` when needed
4. The configured LLM returns JSON for source-page synthesis, affected page updates, and proposed ontology records
5. The runner prevalidates semantic output before writes:
   - affected page paths must be explicit allowed `wiki/...` paths
   - affected page actions must be `create` or `append`
   - accepted truth is rejected
6. The runner writes source-backed wiki growth and proposed JSONL only
7. The runner refreshes index/log and emits an ingest report for `git diff` review

## Current intentional legacy split

- `scripts/workbench_api.py` remains on the live runtime path for operators and tests
- the deeper package-style implementation under `scripts/workbench/` is the thicker core
- this is intentional legacy support, not dead code

## Verification signals in code

- unit tests cover incremental ingest behavior in `tests/test_incremental_ingest.py`
- route and repository behavior are covered in `tests/test_workbench_api.py`
