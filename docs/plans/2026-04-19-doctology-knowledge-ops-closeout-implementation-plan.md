# DocTology Knowledge-Ops Closeout Implementation Plan

> **For Hermes:** Execute this plan with strict TDD. Keep one workstream in progress at a time and verify narrowly before broad suite runs.

**Goal:** Close the highest-leverage knowledge-ops gaps by shipping truth-state docs, doctor-grade diagnostics, a production daily-operator runbook, and an explicit query contract.

**Architecture:** Reuse the existing `scripts/llm_wiki.py` CLI as the operator entrypoint, the existing workbench action surface as the audited UI bridge, and the current workbench repository/query-preview path as the contract surface. Keep changes additive and derived-layer-safe.

**Tech Stack:** Python 3 CLI + unittest/pytest, TypeScript/React workbench, markdown docs.

---

## Task 1: Capture issue breakdown and GitHub issues

**Objective:** Save the local issue breakdown and create matching GitHub issues.

**Files:**
- Create: `docs/issues/2026-04-19-doctology-knowledge-ops-closeout-issue-breakdown.md`

**Verify:**
- `gh issue list --state open --limit 10`

---

## Task 2: Add failing doctor tests

**Objective:** Lock the desired doctor contract before writing implementation code.

**Files:**
- Create: `tests/test_llm_wiki_runtime_health.py`
- Modify: `scripts/llm_wiki.py`
- Modify: `scripts/workbench/common.py`

**Test targets:**
- doctor human-readable output includes raw/canonical/graph/docs/working-tree sections
- doctor JSON output includes machine-readable keys
- working-tree contamination classes are stable
- status command stays backward-compatible

**Verify:**
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_llm_wiki_runtime_health.py -q` (must fail first)

---

## Task 3: Implement doctor command in the CLI

**Objective:** Add `doctor` and `doctor --json` to `scripts/llm_wiki.py` without regressing `status`, `lint`, or `reindex`.

**Files:**
- Modify: `scripts/llm_wiki.py`

**Verify:**
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_llm_wiki_runtime_health.py -q`
- `python3 scripts/llm_wiki.py doctor`
- `python3 scripts/llm_wiki.py doctor --json`

---

## Task 4: Wire doctor into workbench action plumbing

**Objective:** Make the workbench action surface understand the new doctor action.

**Files:**
- Modify: `scripts/workbench/common.py`
- Modify: `apps/workbench/src/lib/api.ts`
- Modify: `apps/workbench/src/App.tsx`

**Verify:**
- `npm test`
- `npm run build`

---

## Task 5: Add truth-state and versioning docs

**Objective:** Make repo/runtime ownership explicit and discoverable.

**Files:**
- Create: `docs/CURRENT_STATE.md`
- Create: `docs/LAYERS.md`
- Create: `docs/VERSIONING_POLICY.md`
- Modify: `README.md`
- Modify: `README.ko.md`

**Verify:**
- `python3 scripts/llm_wiki.py status`
- `python3 scripts/llm_wiki.py doctor`

---

## Task 6: Publish the production daily-operator loop

**Objective:** Turn the production ingest path into an explicit runbook rather than an implied roadmap note.

**Files:**
- Create: `docs/flows/2026-04-19-doctology-daily-operator-loop.md`
- Modify: `docs/reviews/2026-04-18-doctology-production-ontology-ingest-upgrade-roadmap.md`
- Modify: `scripts/llm_wiki.py`

**Verify:**
- `python3 scripts/ontology_ingest.py --help`
- `python3 scripts/llm_wiki.py doctor`

---

## Task 7: Add failing query-contract tests

**Objective:** Lock explicit route/truth/fallback metadata before changing query preview payloads.

**Files:**
- Modify: `tests/test_workbench_graph_inspect.py`
- Modify: `scripts/workbench/repository.py`
- Modify: `apps/workbench/src/lib/api.ts`
- Modify: `apps/workbench/src/App.tsx`

**Test targets:**
- supported/thin/none/empty query payloads carry a contract block
- save-analysis persists the contract block
- graph-hint behavior remains unchanged

**Verify:**
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_workbench_graph_inspect.py -q` (must fail first)

---

## Task 8: Implement the query contract and analysis persistence

**Objective:** Add explicit route/truth/fallback/save-readiness metadata to previews and saved analyses.

**Files:**
- Modify: `scripts/workbench/repository.py`
- Modify: `apps/workbench/src/lib/api.ts`
- Modify: `apps/workbench/src/App.tsx`

**Verify:**
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_workbench_graph_inspect.py -q`
- `npm test`
- `npm run build`

---

## Task 9: Sync durable review/wiki docs

**Objective:** Save the new capability and operating-boundary knowledge in durable markdown.

**Files:**
- Modify: `docs/reviews/2026-04-19-doctology-working-tree-cleanup-and-knowledge-ops-finish-review.md`
- Modify: `wiki/wiki/analyses/analysis-2026-04-19-doctology-working-tree-cleanup-and-finish-path.md`
- Modify: `wiki/wiki/_meta/index.md`
- Modify: `wiki/wiki/_meta/log.md`

**Verify:**
- `python3 scripts/llm_wiki.py reindex`
- manual read-through of updated docs

---

## Task 10: Full verification and closeout

**Objective:** Prove the whole tranche works end-to-end, then commit/push and close GitHub issues.

**Files:**
- Modify as needed from prior tasks only

**Verify:**
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_llm_wiki_runtime_health.py -q`
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_workbench_graph_inspect.py -q`
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py tests/test_ontology_benchmark_ingest.py tests/test_workbench_graph_inspect.py tests/test_llm_wiki_runtime_health.py -q`
- `npm test`
- `npm run build`
- `python3 scripts/llm_wiki.py doctor`
- `python3 scripts/llm_wiki.py doctor --json`
- `git status --short`
- `gh issue list --state open --limit 10`
