# DocTology vs ontology-first expert advice

## Scope
This review treats the current project as `~/Documents/my_project/DocTology`.
The question is not whether the expert advice is impressive in the abstract, but which parts DocTology has already absorbed, which parts fit as selective next evolution, and which parts would distort the product if transplanted directly.

## What I inspected
- `README.md`
- `repo-docs-intelligence-bootstrap/SKILL.md`
- `lightweight-ontology-core/SKILL.md`
- `lg-ontology/SKILL.md`
- `llm-wiki-ontology-ingest/SKILL.md`
- `llm-wiki-bootstrap/references/scaffold-spec.md`
- `repo-docs-intelligence-bootstrap/assets/AGENTS.template.md`
- `repo-docs-intelligence-bootstrap/assets/intelligence/{capabilities,handler,policy,schema}.template`
- `lightweight-ontology-core/scripts/{retrieve_with_chroma.py,_ontology_core_support.py}`
- `lg-ontology/scripts/compare_graph_modes.py`

## Lightweight runtime verification
Confirmed runnable entrypoints:
- `python3 repo-docs-intelligence-bootstrap/scripts/validate_repo_docs_intelligence.py --help`
- `python3 lightweight-ontology-core/scripts/validate_ontology_graph.py --help`
- `python3 lg-ontology/scripts/compare_graph_modes.py --help`

## Bottom line
DocTology has already absorbed the best practical discipline from the advice much more than it may look at first glance.
But it has absorbed it in a bounded, local-first, wiki-first form.
That is a strength, not a weakness.

The highest-value next step is not "becoming a full Palantir-like ontology platform."
The highest-value next step is strengthening three thin layers:
1. query-time intent/impact receipts
2. richer active metadata around source families and refresh lineage
3. rule-backed routing/gating between wiki, ontology, retrieval, and graph modes

## What DocTology has already absorbed well

### 1. Search before code
This is already explicitly embedded in the repo-docs discipline.
Evidence:
- `repo-docs-intelligence-bootstrap/SKILL.md` has a dedicated `Search Before Code` section.
- `repo-docs-intelligence-bootstrap/assets/AGENTS.template.md` includes `Search before code.` as a working rule.

This means the expert's advice is not foreign to the project; it is already one of the repo's strongest operator contracts.

### 2. Impact analysis before structural change
Also already absorbed strongly.
Evidence:
- `repo-docs-intelligence-bootstrap/SKILL.md` has `Impact Analysis First`.
- The AGENTS template says impact analysis must happen before schemas, manifests, handlers, or graph/materialization changes.
- The validator script exists to check docs/intelligence alignment after structural work.

This is one of the clearest overlaps with the expert's advice.

### 3. Ontology-first / schema-first sequencing
This is already a core rule in DocTology's docs-and-intelligence layer.
Evidence:
- `repo-docs-intelligence-bootstrap/SKILL.md` defines order as glossary -> action/dataset -> policy or SQL -> Python implementation link.
- The AGENTS template repeats: define glossary/action/schema before implementation.

So the project already shares the expert's basic belief that code should come after contract.

### 4. Small named units instead of monoliths
DocTology is already structured as small bounded units:
- `llm-wiki-bootstrap`
- `llm-wiki-ontology-ingest`
- `lightweight-ontology-core`
- `lg-ontology`
- `ontology-pipeline-operator`
- `repo-docs-intelligence-bootstrap`

This is much closer to the expert's `smallest nameable unit` advice than to a monolithic 20k-line file design.

### 5. Manifest/capability/policy separation
This is already meaningfully present.
Evidence from `repo-docs-intelligence-bootstrap`:
- glossary
- manifests
- handlers
- policies
- schemas
- capability bindings

And the recommended minimum pattern explicitly says:
- datasets define canonical shapes
- actions map reusable contracts
- handlers describe event chains and impact flow
- policies describe rules and gates
- SQL mirrors contract excerpts
- capability bindings connect action keys to Python execution points

That is already very close to the expert's Glossary / Manifest / Capability / Logic / Binding worldview.

### 6. Graph as derived, not canonical
DocTology has already made a mature design choice here.
Evidence:
- `lightweight-ontology-core` keeps YAML + JSONL canonical.
- `lg-ontology` explicitly says graph projection is derived, read-only, and must not replace canonical JSONL truth.
- `compare_graph_modes.py` exists to compare baseline lookup vs graph-style expansion before overcommitting.

This is an important strength: it absorbs graph reasoning without surrendering truth ownership to the graph layer.

### 7. Retrieval as helper, not truth
Also already explicit.
Evidence:
- `lightweight-ontology-core/SKILL.md` separates canonical JSONL from semantic retrieval in Chroma.
- README says retrieval is a helper layer, not canonical truth.

This is a strong antidote to GraphRAG hype and keeps the stack auditable.

## What is only partially absorbed today

### 1. Event-driven thinking exists, but mostly as contract, not live runtime
There is real progress here, but it is still thin.
Evidence:
- handler templates exist
- handler contracts describe `event_key`, action chains, gates, and follow-on alignment work
- `llm-wiki-bootstrap` now includes `ontology_refresh.py`

But the current posture is still mostly:
- documented event chains
- thin operator scripts
- manual or semi-manual refresh loops

Not yet:
- always-on event sourcing
- a live event bus
- system-wide automatic writeback orchestration

This is a good place for selective growth.

### 2. Source lineage exists, but active metadata is still narrow
There are signs of lineage maturity:
- `source_versions.jsonl`
- `source_families.yaml`
- truth boundary policies
- claim/evidence/segment/document separation

But it is not yet the richer "active metadata runtime" implied by the expert advice.
Current metadata is good enough for:
- provenance
- refresh identity
- some filtering

But not yet strong in:
- operator-facing freshness receipts
- dependency impact receipts
- query-time route explanations
- multi-view metadata states beyond the current canonical/proposed/accepted style

### 3. Search is implemented, but not yet multi-axis
Current retrieval is mostly:
- embedding-based segment retrieval in Chroma
- metadata filters such as document type / status
- graph-style neighborhood expansion after structured seed identification

Evidence:
- `retrieve_with_chroma.py` uses one retrieval collection plus metadata filters
- `_ontology_core_support.py` defines one collection and a compact set of metadata fields
- `compare_graph_modes.py` compares baseline accepted-claim lookup with graph expansion

What is missing relative to the expert advice:
- explicit multi-axis query decomposition
- category-layer similarity
- narrative-layer similarity
- intent-layer similarity
- task/impact/risk axes
- recursive query expansion receipts

So the project has search + graph, but not the expert's stronger "many axes of similarity before traversal" model.

### 4. Rule as code exists, but mainly as validator-backed contract discipline
This is partially there.
Evidence:
- policies YAML exists
- capability bindings exist
- validator scripts exist
- inference rules exist in ontology packs

But the rules do not yet look like a hard global execution governor across the whole stack.
They are closer to:
- repository contract enforcement
- ontology integrity checks
- derived edge materialization constraints

Not yet:
- runtime-wide action authorization
- mandatory preflight gating for all agent actions
- policy-driven route denial or permissioning

## What is mostly missing

### 1. ReBAC / ABAC / RBAC-style access-control layer
I found essentially no meaningful ReBAC presence in the current project.
This is one of the clearest gaps relative to the expert's architecture.

Important nuance:
for DocTology as a local-first skill pack, this is not automatically a flaw.
It becomes important only if the project moves toward:
- multi-user collaboration
- agent delegation with scoped permissions
- shared corpora with per-document restrictions
- MCP-exposed action surfaces that need trust boundaries

### 2. Intent analysis as a first-class artifact
Impact analysis is present.
Intent analysis is not yet a first-class saved product.

A strong next move would be to make every non-trivial query or task produce a tiny structured receipt like:
- inferred task family
- likely affected layers
- preferred route: wiki / canonical / graph / docs / refresh
- confidence and fallback reasons

That would absorb a lot of the expert's practical wisdom without dragging in a huge platform.

### 3. Adaptive UX/UI and mobile-connected operating surface
That advice is more platform-level than DocTology-level right now.
DocTology is a skill pack and scaffolding system, not yet a full operator console like the expert's Nebula/Antigravity/Tailscale setup.
Trying to absorb that whole stack into DocTology itself would likely bloat the project.

### 4. Full enterprise GraphRAG stack
DocTology deliberately does not do this.
That is probably correct.
The repo is intentionally designed to avoid graph-database-first overreach.

## What should be absorbed next

### A. Add intent/impact receipts as small canonical artifacts
Best next absorption.

Add a tiny contract layer for query planning, for example:
- `intelligence/manifests/routes.yaml`
- `intelligence/policies/query-routing.yaml`
- `warehouse/jsonl/query_receipts.jsonl`

Each receipt could store:
- query id
- inferred intent
- chosen route
- affected layers
- whether graph expansion was used
- why the route was chosen
- what fallback happened

Why this fits:
- absorbs the expert's intent/impact analysis idea
- strengthens explainability
- stays local-first and lightweight
- improves operator trust without requiring a giant runtime rewrite

### B. Strengthen active metadata around source families and refresh lineage
Second-best next absorption.

DocTology already has the seed pieces:
- `source_families.yaml`
- `source_versions.jsonl`
- truth boundaries

What to add:
- refresh lineage records
- per-run dependency/affected-artifact summary
- freshness expectations by source family
- operator-visible last-good-state metadata

This would make ontology refresh much more inspectable and would bring the project closer to "active metadata" without enterprise bloat.

### C. Turn documented handlers into optional executable gates
Third-best next absorption.

Right now handler chains are mostly documented contracts.
A good next step is not a full event bus.
It is a thin executor that can optionally run documented chains when the repo actually has the referenced actions.

Example direction:
- keep handlers declarative
- resolve action keys through capability bindings
- enforce policy gates before execution
- emit a receipt for what ran and what was blocked

This would be the cleanest bridge from current docs-first discipline toward real rule-backed workflow.

### D. Add multi-axis retrieval incrementally, not as a new religion
Absorb this selectively.

Good fit:
- introduce extra query-axis manifests such as domain, artifact kind, temporal intent, or workflow intent
- score or filter retrieval candidates with those axes before graph expansion
- log which axes mattered for a result set

Bad fit:
- rebuilding the entire product around a giant GraphRAG ideology
- pretending every query needs fractal recursion

The right DocTology version is probably:
- vector recall first
- axis-aware reranking second
- graph expansion third
- receipt explaining which route won

### E. Add a thin action-governance layer before considering ReBAC
ReBAC is probably too early for DocTology core.
A better sequence is:
1. policy-backed action classes
2. route constraints
3. source-family constraints
4. optional actor scopes later

Only after that should a real ReBAC/ABAC layer be considered.

## What should NOT be absorbed directly

### 1. Full Neo4j/enterprise platform architecture
Not a good direct fit.
DocTology's strength is bounded local-first structure, not enterprise sprawl.

### 2. Forcing graph DB ownership of truth
This would directly weaken one of DocTology's best design decisions.
Keep JSONL canonical.
Keep graph projection derived.

### 3. Mandatory ontology-meta-ontology completion before any coding
As a strict universal law, this is too heavy.
It would likely slow the project and overformalize early experiments.

A better DocTology interpretation is:
- no non-trivial structural coding without updating glossary/manifest/policy/schema
- but allow bounded experimental coding before the ontology is perfect

### 4. Over-expanding YAML into a programming language
The project already knows this danger.
It should keep YAML as meaning and contract, not execution complexity.

## Best synthesis
The expert's advice is most valuable when translated into DocTology as:
- operator contract discipline
- thin canonical manifests
- explicit routing and impact receipts
- bounded graph sidecars
- stronger metadata lineage
- optional action gating

Not as:
- enterprise platform imitation
- graph-database-first architecture
- maximal ontology formalism before useful work begins

## Practical recommendation
If you want the next real evolution step, the best order is:

1. query route + intent/impact receipt layer
2. refresh lineage / active metadata layer
3. optional executable handler-chain runner with policy gates
4. multi-axis reranking before graph expansion
5. only then revisit access control / ReBAC if the system becomes multi-actor

## Final verdict
DocTology already absorbed the best process-level parts of the expert's ontology-first advice.
What it has not yet absorbed is not the philosophy, but the runtime instrumentation layer around that philosophy.

So the next move is not to make the repo much bigger.
The next move is to make its existing ontology/wiki/graph pipeline produce better receipts, better routing, and better active metadata.
