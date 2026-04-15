# Query Intent / Impact Receipt Layer Implementation Plan

> For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

Goal: Add a thin query-time routing and receipt layer to DocTology so ontology-ready workspaces can explain why a query/task went to wiki, canonical JSONL, graph projection, or refresh/operator flow.

Architecture: Keep the new layer small and contract-first. Add route vocabulary in YAML, gate/routing semantics in policy YAML, durable route receipts in JSONL, and at most one thin helper script for ontology-ready scaffolds. Do not turn this into a general workflow engine or a giant GraphRAG runtime.

Tech Stack: Existing DocTology patterns only — YAML manifests, YAML policies, JSONL registries, thin Python helper scripts, validator-backed contract checks, repo-local AGENTS/README guidance.

---

## Why this is the 1st-priority patch

1. It fills the biggest current gap without changing the product identity.
   - The ontology advice review showed that DocTology already has search-before-code, impact analysis, schema-first discipline, canonical JSONL, and derived graph projection.
   - What it still lacks most is runtime instrumentation: intent analysis, route explanation, and impact receipts.

2. It compounds the other three next-step ideas instead of competing with them.
   - Refresh lineage gets better once query/task receipts already exist.
   - Executable handler gates become safer when route selection is explicit.
   - Multi-axis retrieval becomes easier later because there is already a durable place to record route decisions and fallback reasons.

3. It is high-value and low-risk.
   - No graph DB migration.
   - No ReBAC commitment.
   - No giant runtime rewrite.
   - It fits the current repo philosophy: wiki-first surface, canonical JSONL substrate, graph as sidecar.

4. It improves operator trust immediately.
   - Users can see why a route was chosen.
   - Future evaluation can compare wiki-only answers vs ontology-backed vs graph-assisted answers.
   - It creates a durable audit trail instead of keeping route reasoning only in chat.

---

## Design target

For ontology-ready workspaces, add these canonical artifacts:
- `intelligence/manifests/routes.yaml`
- `intelligence/policies/query-routing.yaml`
- `warehouse/jsonl/query_receipts.jsonl`

Optional thin helper script in generated scaffolds:
- `scripts/query_route.py`

The minimal route families for v1 should be:
- `wiki_lookup`
- `canonical_lookup`
- `graph_expand`
- `refresh_operator`
- `mixed_lookup`

Each receipt row should be able to store:
- `receipt_id`
- `created_at`
- `query_text`
- `intent_family`
- `route_key`
- `affected_layers`
- `seed_terms`
- `fallback_route_key`
- `fallback_reason`
- `confidence`
- `used_graph_expansion`
- `notes`

Keep this v1 thin. Do not add model-generated planning chains, recursion trees, or action executors yet.

---

## Task 1: Define the route contract layer

Objective: Introduce the smallest reusable contract vocabulary for query/task routing.

Files:
- Create: `repo-docs-intelligence-bootstrap/assets/intelligence/routes.template.yaml`
- Create: `repo-docs-intelligence-bootstrap/assets/intelligence/query-routing.template.yaml`
- Modify: `repo-docs-intelligence-bootstrap/SKILL.md`
- Modify: `repo-docs-intelligence-bootstrap/assets/AGENTS.template.md`

Step 1: Create `routes.template.yaml`

Define route records like:
- `route_key`
- `purpose`
- `preferred_layers`
- `typical_signals`
- `fallback_route`
- `notes`

The initial five route keys should be:
- `wiki_lookup`
- `canonical_lookup`
- `graph_expand`
- `refresh_operator`
- `mixed_lookup`

Step 2: Create `query-routing.template.yaml`

Define policy records like:
- `policy_key`
- `applies_to_routes`
- `condition`
- `block_on_fail`
- `fallback_route`
- `notes`

Include at least these gates:
- do not use `graph_expand` when canonical ontology files are missing
- prefer `wiki_lookup` when the request is explicitly page-reading or summary-oriented
- prefer `canonical_lookup` when provenance, claim state, or evidence tracing is requested
- allow `mixed_lookup` when both readable synthesis and traceable truth are needed
- route to `refresh_operator` when the user is asking for repair, rebuild, validation, or refresh work

Step 3: Update the repo-docs bootstrap skill text

Add explicit mention that the intelligence layer can include:
- route manifests
- query-routing policies
- durable query/task receipts as optional registries

Step 4: Update `assets/AGENTS.template.md`

Add change-sync reminders for:
- `intelligence/manifests/routes.yaml`
- `intelligence/policies/query-routing.yaml`
- `warehouse/jsonl/query_receipts.jsonl`

Step 5: Verify by reading the files back

Manual verification:
- the template names are consistent with the generated target paths
- the route keys are small, product-aligned, and not GraphRAG-hype jargon

Commit suggestion:
- `docs: add route and query-routing intelligence templates`

---

## Task 2: Emit the new artifacts from ontology-ready scaffolds

Objective: Make `wiki-plus-ontology` repos generate the route contract layer and receipt registry by default.

Files:
- Modify: `llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py`
- Modify: `llm-wiki-bootstrap/references/scaffold-spec.md`
- Modify: `llm-wiki-bootstrap/SKILL.md`

Step 1: Add generated files to the scaffold tree

Update the bootstrap generator so `wiki-plus-ontology` also creates:
- `intelligence/manifests/routes.yaml`
- `intelligence/policies/query-routing.yaml`
- `warehouse/jsonl/query_receipts.jsonl`

Step 2: Add generation helpers in `bootstrap_llm_wiki.py`

Create helper functions similar to the existing YAML emitters for:
- `routes_yaml()`
- `query_routing_yaml()`

For `query_receipts.jsonl`, initialize as an empty file.

Step 3: Update generated README/AGENTS wording

The generated ontology-ready README should explain:
- routes describe which knowledge layer to inspect first
- query-routing policy defines constraints and fallback behavior
- query receipts are durable operator/audit records, not canonical truth themselves

Step 4: Update scaffold spec and skill verification rules

In `scaffold-spec.md` and `SKILL.md`, add verification expectations for the new files.

Step 5: Verify with a temp scaffold run

Run:
- `python3 -m py_compile llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py`
- scaffold a temp repo with `--profile wiki-plus-ontology`
- confirm the new files exist

Expected result:
- no syntax errors
- scaffold contains the three new route/receipt artifacts

Commit suggestion:
- `feat: add query routing artifacts to ontology-ready scaffold`

---

## Task 3: Add one thin helper script for route receipts

Objective: Make the new layer minimally usable, not just decorative.

Files:
- Modify: `llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py`
- Generated file: `scripts/query_route.py`
- Modify: `llm-wiki-ontology-ingest/SKILL.md`
- Modify: `README.md`

Step 1: Generate `scripts/query_route.py`

This helper should stay intentionally small.
It should:
- load `intelligence/manifests/routes.yaml`
- load `intelligence/policies/query-routing.yaml`
- accept `--query` and optional `--intent-family`
- choose a route using simple v1 heuristics
- append one row to `warehouse/jsonl/query_receipts.jsonl`
- print a compact JSON receipt

Step 2: Keep heuristics bounded

Suggested heuristic rules for v1:
- if query mentions evidence, citation, provenance, claim, contradiction -> `canonical_lookup`
- if query mentions page, summary, wiki, note, explain simply -> `wiki_lookup`
- if query mentions path, neighborhood, hop, relation, connected -> `graph_expand`
- if query mentions refresh, rebuild, validate, repair, missing, drift -> `refresh_operator`
- otherwise -> `mixed_lookup`

If a route is blocked by policy or missing files, write:
- `fallback_route_key`
- `fallback_reason`

Step 3: Update docs and skill guidance

Update README and `llm-wiki-ontology-ingest/SKILL.md` so they mention:
- route receipts are optional but recommended
- they support future eval and operator trust
- they do not replace ontology extraction or answer generation

Step 4: Verify helper behavior in a temp scaffold

Run:
- scaffold a temp ontology-ready repo
- `python3 scripts/query_route.py --query "show the evidence for this claim"`
- `python3 scripts/query_route.py --query "refresh broken ontology outputs"`

Expected result:
- JSON output printed twice
- `warehouse/jsonl/query_receipts.jsonl` has two rows
- the second route should prefer `refresh_operator`

Commit suggestion:
- `feat: add minimal query route receipt helper`

---

## Task 4: Add validator coverage for the new contract bundle

Objective: Prevent the new layer from drifting into dead docs.

Files:
- Modify: `repo-docs-intelligence-bootstrap/scripts/validate_repo_docs_intelligence.py`
- Create: `repo-docs-intelligence-bootstrap/evals/files/fixture_repo_query_routing_minimal/FIXTURE.md`
- Create: `repo-docs-intelligence-bootstrap/evals/files/fixture_repo_query_routing_minimal/intelligence/manifests/routes.yaml`
- Create: `repo-docs-intelligence-bootstrap/evals/files/fixture_repo_query_routing_minimal/intelligence/policies/query-routing.yaml`
- Create: `repo-docs-intelligence-bootstrap/evals/files/fixture_repo_query_routing_minimal/warehouse/jsonl/query_receipts.jsonl`

Step 1: Add a narrow validator rule

The validator should only check this when route contracts are present.
Suggested rule:
- if `intelligence/manifests/routes.yaml` exists, then `intelligence/policies/query-routing.yaml` must exist too
- if either exists, `warehouse/jsonl/query_receipts.jsonl` should exist for ontology-ready repos or be explicitly absent in docs

Step 2: Add one positive fixture

Create a minimal fixture repo that passes the new contract shape.
Do not overbuild it.

Step 3: Run validator manually

Run:
- `python3 repo-docs-intelligence-bootstrap/scripts/validate_repo_docs_intelligence.py --repo-root repo-docs-intelligence-bootstrap/evals/files/fixture_repo_query_routing_minimal --format json`

Expected result:
- validator reports success or no hard failures

Commit suggestion:
- `feat: validate query routing contract bundle`

---

## Task 5: Add one end-to-end operator-facing review note

Objective: Make the patch legible to future maintainers.

Files:
- Modify: `README.md`
- Create or update: `docs/reviews/2026-04-15-ontology-advice-absorption-review.md`
- Optional create: `docs/notes/query-routing-receipts.md`

Step 1: Update the top-level README

Add one short section describing:
- what route manifests are
- what query-routing policies are
- why receipts exist
- how this supports ontology-first discipline without enterprise bloat

Step 2: Add or extend a review note

Record:
- why this was the first-priority patch
- what it does not do yet
- what becomes easier next because it exists

Step 3: Verify docs consistency

Manual verification:
- README terminology matches the scaffold and templates
- route names are consistent everywhere
- receipts are clearly marked as audit records, not truth owners

Commit suggestion:
- `docs: explain query routing receipts and scope`

---

## Definition of done

This patch is done when all of the following are true:
- ontology-ready scaffolds emit `routes.yaml`, `query-routing.yaml`, and `query_receipts.jsonl`
- one thin helper can write route receipts locally
- repo docs and skill docs explain the feature in the same vocabulary
- the validator has at least narrow awareness of the new contract bundle
- the new layer remains small, auditable, and non-executive by default

## Explicit guardrails

Do not do these in v1:
- do not add a full planner/executor runtime
- do not add model-generated route trees
- do not add ReBAC or actor-scoped permissions yet
- do not replace answer generation with route classification
- do not make query receipts canonical truth
- do not force graph expansion for every query
- do not add more than the minimal five route families

## Why this patch wins over the other three right now

Versus refresh-lineage-first:
- lineage matters, but route receipts create the more general audit backbone first
- once route receipts exist, refresh lineage can reuse the same receipt discipline

Versus executable-handler-first:
- handlers are riskier to operationalize before route intent is explicit
- routing receipts clarify what should happen before execution is automated

Versus multi-axis-retrieval-first:
- multi-axis retrieval without receipts becomes harder to evaluate and explain
- receipts give a stable measurement and comparison point before ranking logic gets more complex

## Suggested execution order after this plan

After this patch lands, the next likely sequence should be:
1. refresh lineage receipts
2. executable handler gates
3. multi-axis reranking before graph expansion
4. actor-scoped governance only if the product becomes multi-actor
