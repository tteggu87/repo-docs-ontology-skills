# Layers

Updated: 2026-04-13

## Truth hierarchy

1. `raw/`
   - immutable source truth
   - human-curated evidence surface
   - do not mutate during normal agent work
2. `warehouse/jsonl/`
   - canonical structured machine truth
   - provenance and review-state surface
   - current registries include `documents`, `messages`, `entities`, `claims`, `claim_evidence`, `segments`, `derived_edges`, and `source_versions`
3. `wiki/`
   - maintained human-facing synthesis
   - default reading surface for the human
4. `warehouse/graph_projection/`
   - derived exploration layer
   - useful for graph-style inspection
   - not canonical

## Contract layer

- `AGENTS.md`
  - repo operating contract and workflow rules
- `intelligence/glossary.yaml`
  - canonical terms
- `intelligence/manifests/*.yaml`
  - action, dataset, source-family, and workbench contracts
- `intelligence/policies/*.yaml`
  - truth, mutation, and entrypoint rules
- `intelligence/registry/capabilities.yaml`
  - action-to-implementation bindings

These files define names and boundaries. They do not replace the runtime.

## Execution layer

- Python owns execution
- manifests and registry files describe contracts around that execution
- the repo currently uses a thin-wrapper / thick-core pattern for the workbench:
  - wrapper: `scripts/workbench_api.py`
  - core: `scripts/workbench/`

## Browser boundary

- browser code must not mutate `raw/`
- browser code must not directly mutate canonical registries
- browser writes are allowed only through explicit backend-gated actions
- graph views are read-only and subordinate to canonical truth
