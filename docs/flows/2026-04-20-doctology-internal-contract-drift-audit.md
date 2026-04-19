---
title: "Flow: DocTology internal contract drift audit"
status: draft
created: 2026-04-20
updated: 2026-04-20
owner: "Hermes"
type: flow
tags:
  - flow
  - doctology
  - audit
  - agents
  - manifests
  - bootstrap
---

# Flow: DocTology internal contract drift audit

Use this after any tranche that changes one or more of:

- runtime routes
- AGENTS startup rules
- bootstrap/sample workspace messaging
- workbench contract manifests
- capability registry
- ontology ingest safety language

## Goal

Catch the specific drift class that has happened before in DocTology:
- runtime/code moves forward
- AGENTS / manifests / bootstrap snapshot do not catch up

This flow is intentionally lightweight.
It is not a substitute for tests.
It is a **contract-layer alignment check**.

## What it checks

`python3 scripts/audit_internal_contract_drift.py --json`
currently checks high-value points such as:

1. root startup guidance
   - root `AGENTS.md` should point to the current runtime-facing `wiki/_meta/*`
   - root `AGENTS.md` should require `docs/CURRENT_STATE.md`
   - root `AGENTS.md` should not default to the deeper `wiki/wiki/_meta/*`

2. dual-wiki explanation
   - `docs/CURRENT_STATE.md`
   - `docs/LAYERS.md`
   should both explain the deeper `wiki/wiki/` sample/historical subtree

3. checked-in sample workspace messaging
   - `wiki/AGENTS.md`
   - `wiki/README.md`
   should clearly say this tree is a lighter sample workspace and not the full parent runtime contract

4. ontology ingest contract language
   - `intelligence/manifests/actions.yaml` should mention:
     - shadow-first behavior
     - `ontology_reconcile_preview.json`
     - no silent wiki rewrite

5. workbench contract coverage
   - `intelligence/manifests/workbench.yaml` should include the currently exposed routes and actions
   - `intelligence/registry/capabilities.yaml` should include the current runtime-facing capability keys

## Commands

From the repo root:

```bash
python3 scripts/audit_internal_contract_drift.py
python3 scripts/audit_internal_contract_drift.py --json
```

## Interpreting results

### Pass
- no high-value drift warnings detected
- proceed with normal review / commit flow

### Warning
- contract layers have fallen behind runtime reality
- patch docs/manifests/AGENTS before treating the tranche as complete

## Minimum follow-up after a warning

1. patch the stale contract files
2. rerun:

```bash
python3 scripts/audit_internal_contract_drift.py --json
```

3. then rerun the normal verification set for the touched area, for example:

```bash
/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py tests/test_ontology_benchmark_ingest.py tests/test_workbench_graph_inspect.py tests/test_llm_wiki_runtime_health.py -q
cd apps/workbench && npm test && npm run build
```

## Important boundary

This audit does **not** decide product architecture.
It only checks whether the surrounding contract layers still describe the implemented system honestly.

## Safe default

When in doubt:
- update runtime docs
- update AGENTS
- update manifests
- update the bootstrap/sample workspace wording
- rerun the audit

Do not leave a tranche in a state where tests are green but the repo teaches the wrong operating contract.
