# Growth-wiki P0 post-commit review

_Date: 2026-04-21_

## Commit

- `5dba585` — `feat: restore growth-wiki p0 operator contract and ingest path`

## What improved after P0

### 1. Root operator contract exists again
Restored:
- `AGENTS.md`
- `docs/CURRENT_STATE.md`
- `docs/LAYERS.md`
- `docs/VERSIONING_POLICY.md`
- root `intelligence/` manifests and policies

This means the restored growth-wiki branch now has an explicit truth order and repo-root operator contract instead of only the bootstrap/sample wiki surface.

### 2. Root operator health tooling works
Restored:
- `scripts/llm_wiki.py`

Verified:
- `python3 scripts/llm_wiki.py doctor`
- `python3 scripts/llm_wiki.py status`

Current doctor output confirms:
- working tree clean
- docs ready
- production ingest entrypoint present
- graph projection available
- shadow reconcile preview present

### 3. Production ingest path works again
Restored:
- `scripts/ontology_ingest.py`
- `scripts/ontology_registry_common.py`
- `scripts/build_graph_projection_from_jsonl.py`
- `scripts/incremental_support.py`
- minimal `scripts/workbench/common.py`

Minimal regression tests pass:
- `pytest -q` -> `2 passed`

### 4. Growth-wiki base remains intact
Not restored in P0:
- `scripts/doctology.py`
- `scripts/workbench/repository.py`
- `scripts/workbench/server.py`
- `scripts/workbench/llm_config.py`
- `scripts/workbench_api.py`
- `scripts/ontology_benchmark_ingest.py`
- `scripts/run_ontology_graph_benchmark.py`

So P0 strengthened operator safety and ingest, without re-promoting preview/ask runtime logic.

## Additional scripts worth reviewing next

### Highest priority
1. `scripts/workbench/repository.py`
2. `scripts/workbench/llm_config.py`

Reason:
- doctor currently recommends reviewing `source_detail()` and `review_summary()` surfaces
- those surfaces live in `repository.py`
- without them, the root operator loop stops at doctor/status/reconcile-shadow and lacks read/review convenience

### Next priority
3. `scripts/ontology_benchmark_ingest.py`
4. `scripts/run_ontology_graph_benchmark.py`

Reason:
- doctor reports `Benchmark ingest entrypoint: False`
- these are needed for repeatable benchmark/validation runs
- useful if we want to measure the restored branch against known corpora before adding more runtime code

### Optional after that
5. `scripts/doctology.py`

Reason:
- only if we want a single-entry operator CLI again
- should be reintroduced selectively, keeping operator commands first and avoiding preview-as-answer regression

### Not needed yet
- `scripts/workbench/server.py`
- `scripts/workbench_api.py`

Reason:
- UI/API layer is not required to keep the growth-wiki/operator loop alive

## Ratel question validation on the current state

### What was tested
- `python3 scripts/llm_wiki.py --help`
- `python3 scripts/llm_wiki.py ask --help`
- file presence check for `scripts/doctology.py`
- content search in current `raw/` for `라텔|개미|가재|카피바라`

### Result
Current P0 state cannot run the old-style automated Ratel ask validation.

Why:
1. `scripts/llm_wiki.py` has no `ask` subcommand.
2. `scripts/doctology.py` is absent.
3. `scripts/workbench/repository.py` is absent.
4. current repo `raw/` does not contain the Ratel corpus terms used in the earlier Kakao validation.

### Precise interpretation
This is not a P0 failure.
It means the branch is currently in a **growth-wiki + operator recovery** state, not yet in a **query-runtime validation** state.

## Bottom line

P0 successfully restored:
- root contract
- operator health visibility
- production ingest path
- graph projection generation
- clean commit state

But to run Ratel-style query validation again, the smallest next useful additions are:
- `scripts/workbench/repository.py`
- `scripts/workbench/llm_config.py`
- optionally benchmark scripts before any ask/runtime surface is restored
