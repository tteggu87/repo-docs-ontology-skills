# Workbench App Boundary

This directory is reserved for the optional repository workbench frontend.

Story `S1` locks this location so later stories can implement the UI without reopening the architecture question.

## Scope

- render the operator workbench shell
- read repo state only through the Python adapter
- keep the main reading surface aligned with `wiki/`
- keep `Ask` behind an explicit repo-local query contract or backend-gated write contract
- allow bounded analysis draft saves only through explicit backend-gated actions

## Non-scope

- direct filesystem ownership
- browser-side model API keys
- direct edits to `raw/` or `warehouse/jsonl/`
- graph-first home screen behavior
- fake browser-side chat or model-secret flows

## Current v1 reality

- `Ask` is now a local query preview that searches wiki pages first and surfaces provenance sections
- save actions remain bounded to `wiki/analyses/`, `wiki/_meta/log.md`, and `wiki/_meta/index.md`
- the browser still must not write to `raw/` or `warehouse/jsonl/` directly

## Contract Source

See `intelligence/manifests/workbench.yaml` for the planned API surfaces and mutation rules.
