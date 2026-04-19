---
title: "Audit: internal contract catch-up across runtime, AGENTS, bootstrap snapshot, manifests, and skills"
status: draft
created: 2026-04-20
updated: 2026-04-20
owner: "Hermes"
type: review
tags:
  - review
  - doctology
  - audit
  - agents
  - bootstrap
  - manifests
  - skills
---

# Audit: internal contract catch-up across runtime, AGENTS, bootstrap snapshot, manifests, and skills

## Scope

This audit checked whether DocTology's recent runtime/contract upgrades are internally reflected across:

- live code and tests
- root docs (`README.md`, `docs/CURRENT_STATE.md`, `docs/LAYERS.md`, `docs/VERSIONING_POLICY.md`)
- root `AGENTS.md`
- root `intelligence/` manifests and policies
- the checked-in bootstrap/sample workspace under `wiki/`
- relevant Hermes skills loaded for comparison

## Verification performed

### Runtime reality checks
Ran:
- `python3 scripts/llm_wiki.py doctor --json`
- `python3 scripts/llm_wiki.py status --json`
- `/opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest tests/test_ontology_ingest.py tests/test_ontology_benchmark_ingest.py tests/test_workbench_graph_inspect.py tests/test_llm_wiki_runtime_health.py -q`
- `cd apps/workbench && npm test && npm run build`

Result:
- targeted Python suite: **50 passed**
- frontend tests: **10 passed**
- frontend build: **passed**

### Contract / doc checks
Read and compared:
- `AGENTS.md`
- `wiki/AGENTS.md`
- `README.md`
- `docs/CURRENT_STATE.md`
- `docs/LAYERS.md`
- `docs/VERSIONING_POLICY.md`
- `intelligence/policies/truth-boundaries.yaml`
- `intelligence/manifests/workbench.yaml`
- `intelligence/manifests/actions.yaml`
- `intelligence/registry/capabilities.yaml`
- `wiki/README.md`

### Skill checks
Loaded and compared:
- `living-knowledge-runtime-review`
- `llm-wiki-ontology-substrate-review`
- `evolving-knowledge-system-bootstrap`
- `llm-wiki-bootstrap-hardening`
- `doctology-production-ontology-ingest-hardening`
- `doctology-workbench-graph-inspect-sidecar`
- `doctology-ontology-benchmark-sandbox`

---

## Bottom line

## Short verdict

**부분적으로는 잘 이어졌지만, 아직 분명한 catch-up gap이 남아 있다.**

더 정확히 말하면:

- **DocTology-specific runtime/code/tests** 는 최근 계약 강화 내용을 꽤 잘 반영하고 있다.
- **root-level truth boundary docs** 도 대체로 현재 구조와 맞는다.
- 하지만 **bootstrap snapshot (`wiki/`), 일부 `AGENTS.md`, intelligence manifest/capabilities** 는 최신 runtime semantics를 충분히 따라오지 못했다.

즉 현재 상태는:

> **코드와 doctology-specific skills는 앞서 있고, bootstrap/manifest/agent contract 레이어 일부가 뒤처진 상태**

이다.

---

## What is already well aligned

### 1. Truth order is internally consistent at the root runtime layer
These currently agree well:
- `docs/LAYERS.md`
- `docs/VERSIONING_POLICY.md`
- `intelligence/policies/truth-boundaries.yaml`
- current code behavior in `scripts/ontology_ingest.py`, `scripts/llm_wiki.py`, `scripts/workbench/repository.py`

Shared position:
- `raw/` = source truth
- `warehouse/jsonl/` = canonical machine truth
- `wiki/` = human-facing synthesis
- graph projection = derived/read-only sidecar

This is a strong point. The repo is no longer philosophically split on graph truth ownership.

### 2. Recent semantic upgrades are real in code, tests, and workbench surfaces
Current code does reflect:
- claim semantics summary
- save-readiness calculation from claim semantics
- relation review packets
- supersession summary
- doctor/readiness reporting
- graph inspect and graph hints

The relevant code paths are live and tested.

### 3. Doctology-specific skills are mostly caught up
The loaded DocTology skills were notably better than expected:
- `doctology-production-ontology-ingest-hardening`
- `doctology-workbench-graph-inspect-sidecar`

These skills already describe:
- support/truth/lifecycle/temporal contract promotion
- shadow reconcile behavior
- save-readiness hardening
- relation review packet and supersession hardening
- graph as derived sidecar rather than truth owner

So the problem is **not** that every skill is stale.
The problem is more specific: **generic bootstrap / manifest / repo-internal contract surfaces lag behind the current runtime.**

### 4. Checked-in versioning policy is conceptually aligned with git reality
A quick `git ls-files` check showed:
- tracked `raw/`: 0
- tracked `warehouse/jsonl/`: 0
- tracked `warehouse/graph_projection/`: 0

This means the repo's public/reference policy is not obviously contradicted by tracked corpus truth.
That part is healthier than it first appears.

---

## Gaps found

## Gap A — High severity
### Root repo has a dual-wiki ambiguity that is not explained sharply enough
Evidence:
- root `AGENTS.md` startup says to read `wiki/wiki/_meta/index.md` and `wiki/wiki/_meta/log.md`
- but live workbench/runtime code uses root `wiki/` as the active wiki surface:
  - `WorkbenchRepository.wiki_dir -> root / "wiki"`
  - `sources_dir -> root/wiki/sources`
  - `meta_dir -> root/wiki/_meta`
- `docs/LAYERS.md` and `docs/CURRENT_STATE.md` also speak as if root `wiki/` is the human-facing layer

Why this matters:
- one part of the repo treats `wiki/` as the active runtime wiki
- another part of the startup guidance points agents to the nested bootstrap/sample vault under `wiki/wiki/`
- an agent can easily read/update the wrong wiki tree

This is currently the **biggest conceptual drift**.
Not because the model is wrong, but because the repo contains:
1. the root DocTology runtime wiki surface
2. a checked-in bootstrap/sample workspace under `wiki/`

and the distinction is not made explicit enough.

## Gap B — High severity
### The checked-in bootstrap/sample workspace under `wiki/` is stale relative to current runtime contracts
This is the most concrete catch-up failure.

#### B1. `wiki/AGENTS.md` references commands that do not exist in that workspace
`wiki/AGENTS.md` instructs operators to use:
- `scripts/ontology_ingest.py`
- `scripts/ontology_benchmark_ingest.py`
- `python scripts/llm_wiki.py reconcile-shadow --root <repo>`

But inside `DocTology/wiki/scripts/`:
- `ontology_ingest.py` is absent
- `ontology_benchmark_ingest.py` is absent
- local `llm_wiki.py` supports only `ingest`, `reindex`, `lint`, `status`, `log`
- it does **not** support `doctor` or `reconcile-shadow`

This means the checked-in bootstrap workspace's own AGENTS contract is currently **not self-consistent**.

#### B2. The bootstrap README also reflects an older, lighter stage
`wiki/README.md` still frames the starter as:
- no graph tooling by default
- graph projection added later
- ontology ingest available only later through an external skill

That is reasonable for a minimal bootstrap,
but it does **not** reflect the stronger operator contract that the current main DocTology runtime now embodies.

If `wiki/` is meant to be the repo's bootstrap exemplar, it is now lagging behind the current reality.

## Gap C — High severity
### `intelligence/manifests/actions.yaml` overpromises ontology ingest behavior compared with the actual production ingest contract
Current `actions.yaml` still describes `ingest_with_ontology` as if it:
- updates canonical registries
- refreshes affected wiki pages
- writes broadly into `wiki/`

But the current hardened production ingest path is more careful:
- canonical JSONL refresh is real
- wiki reconcile is **shadow-first**
- source pages should **not** be silently rewritten
- preview goes to `wiki/state/ontology_reconcile_preview.json`

So the manifest is behind the actual safety contract.

This matters because `actions.yaml` is supposed to be a compact operating contract.
Right now it teaches a broader mutation model than the code actually wants.

## Gap D — Medium severity
### `intelligence/manifests/workbench.yaml` and `intelligence/registry/capabilities.yaml` lag behind current workbench reality
Concrete findings:

#### D1. `workbench.yaml` does not list `/api/graph/inspect`
Actual backend route exists:
- `/api/graph/inspect`

Manifest route list does not include it.

#### D2. `workbench.yaml` still says doctor/graph contracts may exist in the backend without being mounted in the default frontend
But the current frontend already mounts:
- doctor lane
- graph lane
- review lane
- source lane
- warehouse lane

So this manifest is behind the UI reality.

#### D3. `capabilities.yaml` is missing newer surfaced capabilities
It currently lists:
- status
- reindex
- lint
- register source
- incremental ingest
- query preview
- analysis save
- claim review

But it does **not** list explicit capabilities for:
- doctor
- graph inspect
- source detail
- review summary
- warehouse summary

So the registry/capability layer is lagging behind what the runtime actually exposes.

## Gap E — Medium severity
### Bootstrap hardening skill expectations are not reflected in the checked-in bootstrap snapshot
The loaded skill `llm-wiki-bootstrap-hardening` expects the ontology-ready bootstrap profile to include at least:
- `intelligence/manifests/relations.yaml`
- `intelligence/manifests/source_families.yaml`
- `intelligence/policies/truth-boundaries.yaml`
- `scripts/ontology_refresh.py`

But the checked-in bootstrap/sample workspace under `wiki/` is missing all of those.
It only has:
- `intelligence/glossary.yaml`
- `intelligence/manifests/actions.yaml`
- `intelligence/manifests/datasets.yaml`

So there is a direct mismatch between:
- the hardened bootstrap skill guidance
- the repo's bootstrap/sample snapshot

This is exactly the kind of "skill catch-up failure" the user warned about.

## Gap F — Low to medium severity
### README skill naming is stronger than repo-local auditability
The root README repeatedly points users to skill names like:
- `llm-wiki-bootstrap`
- `llm-wiki-ontology-ingest`
- `lightweight-ontology-core`
- `lg-ontology`

But within this repo checkout, those skill definitions are not directly inspectable as local `SKILL.md` artifacts.
So the product framing is understandable, but the repo does not give a self-contained way to audit whether those named skills still match the code.

This is more an **auditability gap** than a runtime bug.

---

## Overall assessment by layer

### Code / tests
**Healthy**

### Root truth-boundary docs
**Mostly healthy**

### Doctology-specific skills
**Healthy / mostly caught up**

### Intelligence manifests / capability registry
**Partially stale**

### Checked-in bootstrap/sample workspace under `wiki/`
**Clearly stale**

### Root AGENTS startup guidance
**Conceptually ambiguous because of dual-wiki structure**

---

## Priority fixes

## Priority 1 — Clarify the two wiki surfaces explicitly
Add one short doc or section in root docs explaining:
- root `wiki/` = active DocTology runtime/wiki surface used by workbench
- nested `wiki/` workspace contents (especially `wiki/wiki/`) = bootstrap/sample scaffold or historical internal workspace

Then patch root `AGENTS.md` so future agents do not confuse them.

## Priority 2 — Fix `wiki/AGENTS.md` or downgrade its claims
Choose one:
1. make the nested bootstrap workspace self-consistent by adding the referenced commands/contracts
2. or simplify `wiki/AGENTS.md` so it only references commands actually present in `DocTology/wiki/scripts/`

Current state is worse than either option because it gives impossible instructions.

## Priority 3 — Update `intelligence/manifests/actions.yaml`
Bring it up to current production reality:
- ontology ingest refreshes canonical JSONL
- wiki reconcile is shadow-first
- direct wiki rewrite is not the default contract
- graph remains derived/read-only

## Priority 4 — Update `intelligence/manifests/workbench.yaml` and `capabilities.yaml`
At minimum add or reconcile:
- `/api/graph/inspect`
- explicit doctor capability/action
- source detail capability
- review summary capability
- warehouse summary capability
- note that doctor and graph are already mounted in the current frontend

## Priority 5 — Bring the checked-in bootstrap snapshot up to the hardened bootstrap contract, or mark it intentionally minimal
If `wiki/` is meant as the ontology-ready bootstrap exemplar, add the missing hardening files.
If not, label it clearly as an older/minimal scaffold so agents do not over-trust it.

---

## Final judgment

The repo is **not in a broken state**.
The core runtime, tests, truth boundaries, and DocTology-specific skills are in reasonably good shape.

But the user's historical concern is still valid here:

> **the drift has moved outward**

It is no longer mainly code vs code.
Now the main drift is:
- runtime/code/contracts advanced
- bootstrap/sample workspace + manifests + some AGENTS guidance lagged behind

So the highest-value next move is **not another backend feature tranche**.
It is a **contract catch-up / internal coherence pass** across:
- root `AGENTS.md`
- `wiki/AGENTS.md`
- `intelligence/manifests/actions.yaml`
- `intelligence/manifests/workbench.yaml`
- `intelligence/registry/capabilities.yaml`
- bootstrap/sample `wiki/README.md`

## One-line conclusion

> **현재 DocTology는 핵심 runtime은 앞서가 있지만, bootstrap/sample workspace와 manifest/AGENTS contract 레이어가 그 발전을 완전히 따라오지 못해 내부 괴리가 남아 있다. 가장 큰 문제는 dual-wiki ambiguity와 stale bootstrap contract다.**
