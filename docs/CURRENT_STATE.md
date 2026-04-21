# CURRENT_STATE

_Last updated: 2026-04-20_

## Product posture

DocTology is currently a **wiki-first knowledge-ops reference runtime**.

That means:
- the repo already contains runnable code for wiki/query/review/graph-inspect/operator-support paths
- the repo is credible as a **reference harness** for a local-first knowledge operating system
- the repo is **not yet** a finished daily-use knowledge-ops system in this checked-in public reference state

The main remaining gap is not missing feature breadth.
The main remaining gap is **operational closure**:
- public reference repo vs private live workspace separation
- explicit tracked/local/derived versioning policy
- doctor-grade runtime visibility
- a daily operator loop that keeps canonical truth and reviewed wiki promotion aligned

## What is implemented now

### 1. Wiki-first reference runtime
- local `scripts/llm_wiki.py` CLI
- `ingest`, `reindex`, `lint`, `status`, `reconcile-shadow`, `log`
- `doctor` runtime/working-tree diagnostics
- durable wiki under `wiki/`

### 2. Workbench UI / backend
- workbench API routes in `scripts/workbench/server.py`
- repository-side read/review/query helpers in `scripts/workbench/repository.py`
- React/Vite workbench under `apps/workbench/`
- bounded graph inspect panel and graph seed drilldowns
- audited doctor-action surface in the workbench

### 3. Ontology ingest paths
- benchmark harness: `scripts/ontology_benchmark_ingest.py`
- production-oriented raw-first ingest: `scripts/ontology_ingest.py`
- shared helpers: `scripts/ontology_registry_common.py`
- graph projection builder: `scripts/build_graph_projection_from_jsonl.py`
- benchmark runner: `scripts/run_ontology_graph_benchmark.py`

### 4. Review-oriented ontology surfaces
- source detail coverage and review queue
- low-confidence claim surfacing
- contradiction candidates
- merge candidates
- graph hints inside query preview and review surfaces

## What is verified at current HEAD

### Python tests
Verified green during the closeout tranche:
- `tests/test_llm_wiki_runtime_health.py`
- `tests/test_ontology_ingest.py`
- `tests/test_ontology_benchmark_ingest.py`
- `tests/test_workbench_graph_inspect.py`

### Frontend
Verified green during the closeout tranche:
- `npm test`
- `npm run build`

## Checked-in reference repo reality

### Two wiki surfaces to keep straight
DocTology currently contains both:
- the **active runtime-facing wiki surface** under root `wiki/` (especially `wiki/_meta/`, `wiki/sources/`, and sibling directories used by the workbench and local CLI)
- a **deeper checked-in bootstrap/sample or historical subtree** under `wiki/wiki/`

The checked-in `wiki/` sample workspace should currently be treated as a **lighter/minimal scaffold snapshot**, not as the fully hardened ontology-ready bootstrap contract.

For current runtime work:
- prefer root `wiki/_meta/`, `wiki/sources/`, and sibling directories first
- consult `wiki/wiki/` only when the task explicitly targets the checked-in sample workspace or historical internal analyses stored there

### Strong surfaces already present
- graph inspect works as a bounded derived sidecar
- query preview works against wiki/source material and can emit graph hints
- benchmark + production ingest entrypoints both exist
- review surfaces exist for claim/source/operator work

### Important limitation in this public checked-in state
The checked-in reference repo still has effectively empty mainline canonical registries under `warehouse/jsonl/`.

In other words:
- the **structure** for canonical truth is implemented
- the **daily operator loop** for a real live corpus should run in a live workspace
- the current public repo should not be mistaken for a richly populated production corpus by default

## What this repo should be treated as right now

Treat the current repository as:
- a product/spec/reference runtime
- a reusable local-first architecture baseline
- a safe place to evolve the code, docs, and verified operator contracts

Do **not** treat it as:
- the authoritative long-lived private corpus itself
- the place where all live raw data and daily generated runtime state must be committed
- a graph-truth-owner product

## Highest-leverage next work

1. keep the public/reference repo boundary explicit
2. keep the live workspace separate for real corpus growth
3. use `doctor` as the runtime health entrypoint
4. keep production ingest + shadow reconcile as the daily operator default
5. only promote reviewed outputs into the human-facing wiki
