# Deep heuristic audit after record-only route patch

## Scope
Repository: `~/Documents/my_project/DocTology`

This review answers two questions:
1. did the record-only route-receipt patch land correctly?
2. are there any other heuristic or brittle shortcut sites that conflict with a wiki-first, LLM-led reasoning philosophy?

## What changed in this patch
The route helper was moved from heuristic route choosing toward record-only behavior.

Current intent:
- the agent chooses the route
- `scripts/query_route.py` records that choice
- the helper only applies deterministic impossible-route guards
- the helper no longer acts as the primary semantic route chooser

## Verification performed
- `python3 -m py_compile llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py`
- `python3 -m py_compile repo-docs-intelligence-bootstrap/scripts/validate_repo_docs_intelligence.py`
- ontology-ready scaffold generation in a temp directory
- `scripts/query_route.py --route canonical_lookup --query ...` before refresh
- `scripts/query_route.py --route graph_expand --query ...` before refresh
- `scripts/ontology_refresh.py`
- same route commands after refresh
- validator on `fixture_repo_query_routing_minimal`
- `wiki-only` scaffold generation
- independent subagent audit of remaining heuristic sites

## Post-patch result
The helper is now materially safer.

Observed behavior:
- before ontology files exist, `canonical_lookup` is downgraded to `mixed_lookup` with an explicit `fallback_reason`
- before graph artifacts exist, `graph_expand` is downgraded to `canonical_lookup` with an explicit `fallback_reason`
- after `ontology_refresh.py`, `canonical_lookup` remains allowed
- after `ontology_refresh.py`, `graph_expand` still falls back because usable rows/graph artifacts are still absent

This is better than the previous state because the helper no longer pretends to semantically understand the query by itself.

## Confirmed problematic or philosophy-risk heuristic sites

### 1. Deterministic fallback guards in generated `query_route.py`
File:
- `llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py`

Current status:
- not a heuristic semantic router anymore
- but still a runtime shortcut layer because it may rewrite a chosen route based on readiness checks

Assessment:
- acceptable as a bounded guardrail
- but still worth watching because route readiness is determined by file/row/artifact checks, not deeper semantic inspection

Verdict:
- not philosophically broken
- but still the main runtime shortcut site in the current design

### 2. Lexical seed matching in `compare_graph_modes.py`
File:
- `lg-ontology/scripts/compare_graph_modes.py`

What it does:
- matches user query text to entity ids/labels/aliases with exact/substr checks before graph comparison

Assessment:
- this is still heuristic
- but it is an operator/eval graph inspection tool, not the main answer runtime

Verdict:
- acceptable as an operator utility for now
- should not be copied into the main query path

## Borderline sites to watch

### 1. Built-in default routes when YAML/PyYAML are unavailable
File:
- `llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py`

Assessment:
- the helper can fall back to built-in route definitions if YAML cannot be read
- this is less dangerous now because the helper no longer chooses routes semantically
- but it still means repo-local contracts can be bypassed in degraded environments

Verdict:
- borderline only
- acceptable if treated as degraded-mode validation, not full contract fidelity

### 2. Route manifests still contain descriptive use hints
Files:
- `repo-docs-intelligence-bootstrap/assets/intelligence/routes.template.yaml`
- generated `routes.yaml` from bootstrap

Assessment:
- these hints are now `common_uses`, not lexical `typical_signals`
- they are descriptive, not executable
- safe unless future code starts parsing them as classification rules

Verdict:
- currently acceptable
- future regression risk if someone later wires them into runtime routing naively

### 3. Retrieval defaults like `top_k_default` and `include_statuses`
Files:
- `lightweight-ontology-core/scripts/_ontology_core_support.py`
- `lg-ontology/scripts/_ontology_core_support.py`
- retrieval templates

Assessment:
- these are heuristics in the broad sense, but they are normal retrieval/index defaults rather than semantic route choices
- they do not decide wiki vs canonical vs graph at the query-runtime control-plane level

Verdict:
- acceptable
- not a philosophy conflict in the current architecture

## Acceptable non-problematic defaults

### 1. Validator route checks
File:
- `repo-docs-intelligence-bootstrap/scripts/validate_repo_docs_intelligence.py`

Why acceptable:
- structural contract validation only
- no semantic routing decision

### 2. Accepted-only graph materialization and graph projection guardrails
Files:
- `lightweight-ontology-core/scripts/materialize_derived_edges.py`
- `lg-ontology/scripts/export_graph_projection.py`
- related YAML/rules assets

Why acceptable:
- these are truth-boundary and governance rules, not lexical query routers

### 3. Heading detection in segment builders
Files:
- `lightweight-ontology-core/scripts/build_segments.py`
- `lg-ontology/scripts/build_segments.py`

Why acceptable:
- parser/layout heuristics
- not semantic route steering

## Main philosophical conclusion
After this patch, I do not see a live primary heuristic query router in the main ontology-ready scaffold path.
That was the biggest concern, and it is now materially reduced.

The repo still contains some heuristics in the broad sense, but most of them are one of:
- parser defaults
- retrieval defaults
- validator contract checks
- operator/eval-only graph inspection helpers

Those are not the same thing as a brittle query-time semantic pre-router.

## Remaining caution
The current helper is now much better aligned with the repo philosophy, but two cautions remain:
1. deterministic guards can still overrule an agent-chosen route if readiness checks are too shallow
2. future contributors should not turn `common_uses` or route/policy prose back into a lexical classifier

## Final verdict
- the requested patch direction was correct
- the current result is substantially better aligned with your anti-heuristic stance
- I do not find another equally serious philosophy-breaking heuristic in the main runtime path
- the main remaining shortcut to watch is deterministic route fallback readiness, not lexical route classification
