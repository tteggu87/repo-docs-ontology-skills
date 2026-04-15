# Query routing receipts post-merge review

## Scope
Review target:
- compare `94cb568` -> `e64b8bd`
- repository: `~/Documents/my_project/DocTology`

Question:
- what improved versus the previous state?
- did the patch introduce new weaknesses?
- do I see regressions or likely regressions?

## What I checked

### Diff review
Inspected the actual change set across:
- `README.md`
- `llm-wiki-bootstrap/SKILL.md`
- `llm-wiki-bootstrap/references/scaffold-spec.md`
- `llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py`
- `llm-wiki-ontology-ingest/SKILL.md`
- `repo-docs-intelligence-bootstrap/SKILL.md`
- `repo-docs-intelligence-bootstrap/assets/AGENTS.template.md`
- `repo-docs-intelligence-bootstrap/scripts/validate_repo_docs_intelligence.py`
- new route/query-routing templates
- new validator fixture
- new plan/review docs

### Runtime checks
Ran:
- `python3 -m py_compile llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py`
- `python3 -m py_compile repo-docs-intelligence-bootstrap/scripts/validate_repo_docs_intelligence.py`
- ontology-ready scaffold generation in a temp dir
- generated `scripts/query_route.py` with multiple queries
- generated `scripts/ontology_refresh.py`
- validator on `fixture_repo_query_routing_minimal`
- `wiki-only` scaffold generation to check for regressions in the non-ontology path

### Independent review
Also used an isolated reviewer to inspect the patch and look for hidden regressions/design weaknesses.

## What clearly improved

### 1. Query/task routing is now a first-class contract
Before this patch, route selection lived only in operator intuition and chat reasoning.
Now the scaffold can generate:
- `intelligence/manifests/routes.yaml`
- `intelligence/policies/query-routing.yaml`
- `warehouse/jsonl/query_receipts.jsonl`
- `scripts/query_route.py`

That is a real improvement in explainability, not just more docs.

### 2. The change is coherent across the stack
The patch did not stop at one script.
It updated:
- scaffold generation
- scaffold spec
- bootstrap skill docs
- ingest skill docs
- top-level README
- repo-docs intelligence guidance
- AGENTS template
- validator rules
- validator fixture

So this is not a dangling feature. It is meaningfully integrated.

### 3. Operator trust improved
Actual runtime receipts now show why a route was chosen.
Observed examples:
- `show the evidence for this claim` -> `canonical_lookup`
- `refresh broken ontology outputs` -> `refresh_operator`
- `show the relation path around this entity` -> preferred `graph_expand`, then fallback to `canonical_lookup` with explicit `fallback_reason`

This is exactly the kind of durable route explanation the previous review said was missing.

### 4. The ontology-ready scaffold is more complete
The ontology profile now contains a better minimal control plane:
- route vocabulary
- route policy
- durable receipt registry
- a helper script to write receipts

This makes the scaffold more obviously “operator-ready” than before.

### 5. Validator coverage improved
The validator now catches route-bundle drift such as:
- routes without query-routing
- query-routing without routes
- missing receipt registry when route contracts exist
- unknown fallback routes
- invalid `applies_to_routes`

That is a net win for contract consistency.

### 6. No obvious regression in the wiki-only path
I explicitly re-ran `wiki-only` scaffold generation.
Results:
- `scripts/llm_wiki.py` still generated correctly
- `scripts/query_route.py` was not incorrectly added
- `intelligence/` was not incorrectly created

So the non-ontology profile did not get polluted by the new feature.

## Did new downsides appear?
Yes, but they are manageable.

### 1. The route runtime is thinner than the docs may suggest
The new runtime helper reads the route and policy files, but real routing logic is still mostly hardcoded keyword heuristics.
That means:
- repo-local edits to `typical_signals` in YAML do not currently drive routing
- only a narrow part of policy is truly enforced at runtime
- the contract is ahead of the runtime

This is not fatal, but it means the new layer is currently “receipt-first” rather than “fully policy-driven.”

### 2. More files means more maintenance burden
The ontology scaffold now has additional moving parts:
- routes manifest
- query-routing policy
- receipts registry
- helper script
- validator checks

This is still acceptable, but it does increase surface area.
The good news is the added complexity is still much smaller than a full event engine or GraphRAG runtime.

### 3. Query text is now durably stored
`query_receipts.jsonl` stores the raw query text.
That helps auditing and eval, but it also means:
- more operational noise in `warehouse/jsonl/`
- possible privacy/sensitivity issues if prompts contain private material
- eventual need for retention/redaction policy

This is not a blocker, but it should be documented later.

## Did I find regressions or likely regressions?

### Confirmed: no major regression in existing verified flows
I did not find a regression in these previously working paths:
- `wiki-only` scaffold
- `wiki-plus-ontology` scaffold generation
- `ontology_refresh.py`
- validator basic execution
- previous ontology-ready bootstrap behavior

So at the level of “did earlier working paths break?” the answer is mostly no.

### Likely/real weakness 1: graph readiness gating is too shallow
This is the main technical weakness.
Current behavior checks file presence more than actual graph usability.
That means a repo can have empty placeholder ontology files and still look partly route-ready.

In my runtime test, the graph-oriented query did fallback correctly in a fresh scaffold because graph prerequisites were still absent before refresh.
But the independent review pointed out an important edge case:
- after `ontology_refresh.py` creates empty placeholder files,
- a graph-style route may become “available” based on existence checks rather than meaningful content.

So the graph route gate is still fragile.
This is the biggest likely regression/quality risk, though I did not hit a user-visible failure in the exact run I performed.

### Likely/real weakness 2: validator-contract mismatch on repo-docs side
The validator now requires `warehouse/jsonl/query_receipts.jsonl` when route contracts exist.
But the repo-docs bootstrap side adds route templates, not a full scaffold path with a receipt file template.

Meaning:
- a repo can adopt the new route templates exactly as provided,
- then hit validator pressure to also create `query_receipts.jsonl` manually.

This is not a regression in existing flows, but it is a new contract mismatch.

### Likely weakness 3: silent YAML fallback behavior
The helper script uses YAML if available, otherwise falls back quietly.
That means on a machine without PyYAML:
- repo-local route/policy customization may be ignored
- the script still runs
- the operator may not realize it is using defaults

Again, not a broken flow, but a correctness/explainability risk.

## Overall verdict

### What got better
- DocTology now has a real, durable route-receipt layer instead of implicit routing only in chat.
- The scaffold is more complete and more operator-friendly.
- The validator is stronger.
- The non-ontology path does not appear to regress.

### What got worse
- Slightly more maintenance overhead.
- Some runtime behavior is still thinner than the new contracts imply.
- Raw query persistence introduces future privacy/noise concerns.

### Regressions
- I did not find a major regression in previously working scaffold/refresh flows.
- I do see two meaningful correctness risks:
  1. graph readiness checks are too shallow
  2. repo-docs bootstrap assets and validator requirements are not perfectly aligned

## Recommendation
Do not revert this patch.
It is a net improvement.

But the next cleanup pass should probably do these two things:
1. tighten graph route gating so it requires usable graph/canonical state, not just placeholder files
2. align repo-docs bootstrap assets with validator expectations around `query_receipts.jsonl`

After that, the patch will feel much more finished.
