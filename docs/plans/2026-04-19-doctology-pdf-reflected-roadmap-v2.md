# DocTology PDF-Reflected Roadmap v2

> **For Hermes:** Treat this as the next roadmap after the knowledge-ops closeout tranche. Keep the current raw-first / canonical-truth / derived-graph boundary intact while promoting uncertainty, temporal state, and relation semantics into first-class product/runtime surfaces.

**Goal:** Absorb the useful parts of `TalkFile_ontology_statistics_models_list_ko.pdf` into a realistic DocTology roadmap for a personal daily-driver knowledge system.

**Architecture:** Do not turn DocTology into a statistics lab or full probabilistic reasoner. Instead, promote three missing layers above the current baseline: (1) explicit uncertainty semantics, (2) temporal/state semantics for claims/pages/entities, and (3) richer relation semantics beyond simple graph sidecar hints. Keep graph projection derived, keep canonical JSONL as machine-truth, and use the workbench as the operator-facing review surface.

**Tech Stack:** Python CLI + JSONL registries, React/TypeScript workbench, markdown docs, bounded derived graph projection.

---

## 1. What changed after reading the PDF

The PDF is not mainly about "LLM vs heuristics." It is a structured map of how ontology systems can be strengthened by statistical / probabilistic / relational / temporal model families.

The biggest roadmap implication is:

> DocTology should not only improve ask quality and trust UX. It should also evolve its knowledge representation layer in four directions: **uncertainty**, **temporal state**, **relation semantics**, and **taxonomy induction assistance**.

### High-value model families from the PDF

These are the parts worth absorbing conceptually:

- **Bayesian Network / PRM / SRL**
  - argues for relation-aware, uncertainty-aware ontology structure
- **MLN / PSL**
  - argues for soft truth, defeasible relation support, and non-binary ontology edges
- **HMM / DBN / Markov / Multi-state**
  - argues for state-transition-aware ontology, not just static snapshot truth
- **Hierarchical Clustering / LCA / LPA / hLDA**
  - argues for taxonomy/class induction support, not ontology-by-hand only
- **SBM / ERGM / latent-space graph models**
  - argues that graph should also be used to inspect macro structure, not just answer garnish
- **KG embedding / RESCAL / tensor factorization**
  - useful later for missing-relation discovery, but should stay research-track for now
- **SCM / causal BN / path analysis**
  - useful as a long-term schema direction for causal relation types, not an immediate implementation target

---

## 2. Current baseline DocTology already has useful precursors

The PDF does **not** imply a restart. The repo already has seeds of the right direction:

### Already present
- `scripts/ontology_ingest.py`
  - emits claim-level `confidence`
  - emits `review_state`
  - emits contradiction candidates
- `scripts/workbench/repository.py`
  - already surfaces uncertainty candidates
  - already surfaces low-confidence claims
  - already surfaces contradiction / merge candidates
- `scripts/build_graph_projection_from_jsonl.py`
  - already keeps graph as a derived layer from canonical truth
- `scripts/llm_wiki.py`
  - already carries doctor/status/operator contract surfaces
- workbench query/review surfaces
  - already expose route/truth/fallback and graph signals

### Missing promotion
Those signals exist, but they are still mostly:
- operator-side diagnostics
- local heuristics
- review aids
- derived UI annotations

They are **not yet** a coherent ontology/runtime contract for:
- uncertainty states
- temporal state transitions
- relation lifecycle / scope / confidence
- taxonomy-candidate generation

---

## 3. Keep / change / add

## Keep

### 3.1 Raw-first truth ownership
Keep the current boundary:
- `raw/` = immutable source truth
- `warehouse/jsonl/` = canonical machine-truth
- `warehouse/graph_projection/` = derived exploration layer
- `wiki/` = human synthesis / explanation layer

### 3.2 Planner/judge direction for ask semantics
The earlier recommendation still stands:
- avoid endless lexical/rule accumulation as the primary semantic engine
- use deterministic recall for bounds and cheap filtering
- use stronger planner/judge logic for meaning, route choice, and explanation

### 3.3 Graph as bounded optional assist
The PDF strengthens graph importance, but it does **not** justify making graph the truth owner.

---

## Change

### 3.4 Upgrade uncertainty from side signal to schema
Today uncertainty is mostly a review/debugging signal.
It should become a stable ontology/runtime field family.

### 3.5 Upgrade status from document hygiene to state ontology
Today status exists at page/source workflow level.
It should expand into a more explicit state-transition model for claims/entities/relations.

### 3.6 Upgrade relation from extracted edge to managed asset
Today relations are mostly canonical rows plus derived graph hints.
They should become first-class assets with more semantics.

---

## Add

### 3.7 Taxonomy induction assistance
DocTology needs a bounded lane that proposes concept groups / candidate taxonomies from the corpus.
This should remain assistive, reviewable, and non-destructive.

### 3.8 Graph structural diagnostics
Graph should gain a second job:
- not only answer support
- but also structure diagnosis (clusters, hubs, bridge concepts, unstable regions)

---

## 4. Roadmap v2 priorities

## Phase A — Immediate absorption (highest value, lowest conceptual risk)

### A1. Establish an explicit uncertainty contract

**Why this comes first:**
The PDF strongly supports probabilistic/soft ontology thinking, and the repo already has partial signals (`confidence`, `review_state`, contradiction candidates). This is the cheapest meaningful upgrade.

**Target outcome:**
Every claim / relation / source-facing answer can distinguish:
- evidence sufficiency
- review status
- extraction confidence
- contradiction pressure
- provisional vs stable vs disputed standing

**Suggested contract fields:**
- `review_state`
- `confidence`
- `evidence_count`
- `contradiction_candidate`
- `support_status` (`provisional`, `supported`, `disputed`, `rejected`)
- `truth_basis` (`raw_span`, `canonical_claim`, `wiki_summary`, `graph_only`)

**Primary files:**
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/workbench/repository.py`
- Modify: `scripts/build_graph_projection_from_jsonl.py`
- Modify: `apps/workbench/src/lib/api.ts`
- Modify: `apps/workbench/src/App.tsx`
- Test: `tests/test_ontology_ingest.py`
- Test: `tests/test_workbench_graph_inspect.py`

**Verification:**
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py -q`
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_workbench_graph_inspect.py -q`
- `npm test`
- `npm run build`

---

### A2. Add temporal/state semantics for knowledge objects

**Why this comes next:**
The PDF repeatedly emphasizes HMM / DBN / Markov / multi-state thinking. For DocTology, the practical interpretation is not heavy sequence modeling first; it is an explicit state ontology for claims, entities, relations, and source pages.

**Target outcome:**
Knowledge objects can express lifecycle and transition, e.g.:
- `draft`
- `active`
- `contested`
- `superseded`
- `archived`
- `rejected`

**Minimum viable scope:**
- add stable state vocabulary
- record timestamps / provenance for state changes where already possible
- expose state counts and transition-relevant warnings in doctor / review surfaces

**Primary files:**
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/llm_wiki.py`
- Modify: `scripts/workbench/repository.py`
- Modify: `docs/CURRENT_STATE.md`
- Modify: `docs/VERSIONING_POLICY.md`
- Test: `tests/test_ontology_ingest.py`
- Test: `tests/test_llm_wiki_runtime_health.py`

**Verification:**
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py tests/test_llm_wiki_runtime_health.py -q`
- `python3 scripts/llm_wiki.py doctor`
- `python3 scripts/llm_wiki.py doctor --json`

---

### A3. Promote relation semantics to first-class canonical assets

**Why this matters:**
The PDF’s strongest ontology-specific section is relation-aware statistical modeling (PRM, SRL, MLN, PSL, Bayesian networks). DocTology should reflect that by promoting relation semantics, not merely entity extraction.

**Target outcome:**
Relations carry more explicit structure:
- relation type
- direction
- provenance span(s)
- confidence
- state / review standing
- optional temporal scope
- optional inferred-vs-explicit marker

**Primary files:**
- Modify: `scripts/ontology_ingest.py`
- Modify: `scripts/ontology_registry_common.py`
- Modify: `scripts/build_graph_projection_from_jsonl.py`
- Modify: `scripts/workbench/repository.py`
- Test: `tests/test_ontology_ingest.py`
- Test: `tests/test_workbench_graph_inspect.py`

**Verification:**
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py tests/test_workbench_graph_inspect.py -q`
- rerun ingest on bounded real data and inspect JSONL diffs

---

## Phase B — Medium-term absorption (high value, needs tighter product design)

### B1. Add taxonomy-candidate generation as an assist lane

**Why this is useful:**
The PDF strongly supports class/taxonomy induction via hierarchical clustering, latent classes, topic hierarchies, etc. In DocTology form, this should become a reviewable suggestion lane, not an auto-rewrite engine.

**Target outcome:**
Workbench/operator can ask:
- what concept clusters are emerging?
- which pages/entities appear to belong together?
- what parent/child concept candidates appear repeatedly?

**Recommended shape:**
- create a non-destructive candidate registry
- show candidate cluster / taxonomy suggestions in workbench
- require explicit human promotion into durable ontology pages/schema

**Likely files:**
- Modify: `scripts/workbench/repository.py`
- Modify: `scripts/workbench/common.py`
- Modify: `apps/workbench/src/App.tsx`
- Create: `docs/flows/2026-04-19-doctology-taxonomy-candidate-review-loop.md`
- Test: `tests/test_workbench_graph_inspect.py`

---

### B2. Add contradiction + uncertainty compression for human review

**Why this matters:**
The user’s personal-tool goal requires lower review burden, not just more semantic sophistication.

**Target outcome:**
Instead of a flat queue of weak claims, the system surfaces compact review packets:
- duplicated claim families
- contested relation groups
- low-confidence but high-centrality nodes
- unresolved concept naming collisions

**Likely files:**
- Modify: `scripts/workbench/repository.py`
- Modify: `apps/workbench/src/App.tsx`
- Modify: `scripts/llm_wiki.py`
- Test: `tests/test_workbench_graph_inspect.py`
- Test: `tests/test_llm_wiki_runtime_health.py`

---

### B3. Add graph structural diagnostics lane

**Why this matters:**
The PDF suggests graph-level analysis should inspect concept-group structure, not merely provide answer path hints.

**Target outcome:**
Graph tools can answer:
- what are the hub concepts?
- where are bridge concepts between topic regions?
- which clusters are weakly connected or noisy?
- which relation families dominate a region?

**Important constraint:**
This remains a derived diagnostics lane. It does not replace canonical truth review.

**Likely files:**
- Modify: `scripts/build_graph_projection_from_jsonl.py`
- Modify: `scripts/workbench/repository.py`
- Modify: `apps/workbench/src/components/GraphInspectPanel.tsx`
- Test: `tests/test_workbench_graph_inspect.py`
- Test: `apps/workbench/src/components/GraphInspectPanel.test.tsx`

---

## Phase C — Research-track absorption (useful, but do not prematurely operationalize)

### C1. Soft truth / defeasible reasoning lane
Possible inspiration from PDF:
- MLN
- PSL
- probabilistic soft logic ideas

**DocTology interpretation:**
- do not implement a full MLN/PSL engine yet
- instead design schema hooks for soft/inferred/disputed relations
- later test whether a bounded scoring or reasoning layer improves human review

### C2. Missing relation discovery / completion experiments
Possible inspiration from PDF:
- KG embedding
- RESCAL
- tensor factorization

**DocTology interpretation:**
- run offline experiments only
- treat outputs as candidate suggestions, never as direct truth
- keep this out of the core operator loop until false-positive behavior is well understood

### C3. Causal relation typing
Possible inspiration from PDF:
- SCM
- causal BN
- path analysis

**DocTology interpretation:**
- useful as a future ontology relation type family
- not yet a broad ingestion/runtime priority

---

## 5. Recommended roadmap order

If only three new tranches are funded, do them in this order:

1. **Uncertainty contract promotion**
2. **Temporal/state ontology promotion**
3. **Relation-semantics promotion**

If a fourth tranche is possible:

4. **Taxonomy-candidate assist lane**

If a fifth tranche is possible:

5. **Graph structural diagnostics lane**

This order is recommended because it:
- reuses existing signals already present in the repo
- improves trust and operator clarity first
- expands knowledge representation before speculative modeling work
- keeps graph derived and bounded
- avoids prematurely turning DocTology into a research-heavy probabilistic engine

---

## 6. What not to absorb directly from the PDF right now

Do **not** translate the PDF into a giant implementation backlog of named models.

Avoid immediate productization of:
- heavy Bayesian nonparametric stacks
- full causal discovery pipelines
- advanced spatial modeling
- full survival/event-process modeling
- production KG embedding inference in the daily loop

These are useful as conceptual lenses, not immediate build commitments.

---

## 7. Final recommendation

The PDF is valuable because it reveals a missing middle layer in DocTology’s roadmap.

The roadmap should no longer be framed only as:
- ask quality
- planner/judge semantics
- graph optionality
- trust UX

It should now explicitly include:
- **uncertainty ontology**
- **temporal/state ontology**
- **relation ontology**
- **taxonomy induction assistance**
- **graph structure diagnostics**

That is the absorbable core.

The right next step is **not** implementing named statistical models one by one.
The right next step is upgrading DocTology’s schema and review/runtime contracts so those model families become meaningful future extensions rather than disconnected ideas.

---

## 8. Practical next tranche recommendation

If execution starts immediately, the best next implementation plan is:

### Tranche 1
- uncertainty contract promotion
- support status vocabulary
- workbench surfacing for truth basis / evidence sufficiency

### Tranche 2
- temporal/state vocabulary for claims/entities/relations/pages
- doctor/status visibility for lifecycle drift
- review flow updates for contested/superseded transitions

### Tranche 3
- relation schema enrichment
- graph projection alignment with richer relation semantics
- bounded graph structural diagnostics
