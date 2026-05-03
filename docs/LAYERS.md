# Layers

Updated: 2026-05-02

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
5. `intelligence/`
   - contract layer for workflow, boundary, registry, relation, and meta-surface policy
   - not a second wiki
   - not a semantic claim store

## Contract layer

- `AGENTS.md`
  - repo operating contract and workflow rules
- `intelligence/glossary.yaml`
  - canonical terms
- `intelligence/manifests/*.yaml`
  - action, dataset, source-family, workbench, semantic workflow, page policy, relation, registry, and meta-surface contracts
- `intelligence/policies/*.yaml`
  - truth, mutation, entrypoint, and strict semantic boundary rules
- `intelligence/registry/capabilities.yaml`
  - action-to-implementation bindings

These files define names and boundaries. They do not replace the runtime.
They must not contain answer drafts, source summaries, or inferred semantic claims.

## Execution layer

- Python owns execution
- manifests and registry files describe contracts around that execution
- surrounding chat agent or configured helper LLM owns semantic compile/query judgment
- deterministic code owns ID generation, line ranges, citation anchors, source projection, meta navigation, and validation
- the repo currently uses a thin-wrapper / thick-core pattern for the workbench:
  - wrapper: `scripts/workbench_api.py`
  - core: `scripts/workbench/`

## Browser boundary

- browser code must not mutate `raw/`
- browser code must not directly mutate canonical registries
- browser writes are allowed only through explicit backend-gated actions
- graph views are read-only and subordinate to canonical truth
