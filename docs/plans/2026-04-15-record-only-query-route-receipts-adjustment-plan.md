# Record-Only Query Route Receipts Adjustment Plan

> For Hermes: use this plan when adjusting route-receipt behavior away from heuristic query-time routing.

Goal: Keep route manifests and durable query receipts, but remove heuristic semantic route selection from the runtime helper so that route choice stays with the LLM/agent and the helper acts only as recorder plus deterministic guard checker.

Architecture: `scripts/query_route.py` should accept an explicit route chosen by the agent, validate that route against repo-local manifests, apply only deterministic impossible-route guards, and append a receipt to `warehouse/jsonl/query_receipts.jsonl`. It should not infer routes from keywords.

Tech stack: existing DocTology YAML manifests, YAML policies, JSONL receipts, thin Python helper, validator-backed contract discipline.

---

## Tasks

1. Replace heuristic route selection in generated `query_route.py`
- remove `detect_route(...)`
- require `--route`
- support optional `--rationale`, `--confidence`, `--seed-term`, `--note`
- keep deterministic guard checks only

2. Tighten graph guard semantics
- require usable canonical rows plus graph projection artifacts before allowing `graph_expand`
- allow fallback recording with explicit `fallback_reason`

3. Update scaffold docs
- say the helper records an agent-chosen route
- do not present it as the semantic route chooser
- update command examples to `--route <chosen-route>`

4. Update route templates
- rename lexical-looking `typical_signals` wording to descriptive `common_uses`
- keep route manifests as contract/hint documents, not executable keyword classifiers

5. Verify
- `py_compile` on modified Python files
- scaffold `wiki-plus-ontology`
- run `query_route.py --route canonical_lookup --query ...`
- run `query_route.py --route graph_expand --query ...` before and after `ontology_refresh.py`
- confirm deterministic fallback works and receipts append cleanly
- confirm `wiki-only` scaffold remains unchanged

## Definition of done
- no heuristic route chooser remains in the generated helper
- docs consistently describe the helper as recorder + guard
- receipts still work
- graph fallback is stricter than simple placeholder-file presence
- `wiki-only` flow remains clean
