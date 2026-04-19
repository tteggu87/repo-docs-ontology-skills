# LAYERS

_Last updated: 2026-04-20_

## Truth order

DocTology uses this truth priority:

1. `raw/` — immutable source truth
2. `warehouse/jsonl/` — canonical structured truth
3. `wiki/` — maintained human-facing synthesis
4. graph projection / SQLite / DuckDB / other runtime helpers — derived or operational layers only

This order is the core safety rule.
If two layers disagree, the higher layer in this list wins.

---

## Layer 1 — Raw source truth

**Path:** `raw/`

**Role:**
- immutable source material
- the only place where original collected content lives
- the starting point for production ingest

**Allowed behavior:**
- add new sources
- preserve snapshots
- move between inbox/processed/notes/assets by explicit operator action

**Not allowed:**
- silently rewrite source contents during ontology or wiki refresh

---

## Layer 2 — Canonical structured truth

**Path:** `warehouse/jsonl/`

**Role:**
- machine-verifiable structured truth
- provenance, claim, segment, entity, evidence, and review state
- the substrate used for stronger operator checks and future controlled promotion

**Canonical registries:**
- `source_versions.jsonl`
- `documents.jsonl`
- `messages.jsonl`
- `entities.jsonl`
- `claims.jsonl`
- `claim_evidence.jsonl`
- `segments.jsonl`

**Derived registry inside the same directory:**
- `derived_edges.jsonl`

**Important rule:**
`warehouse/jsonl/` is the machine-truth layer, but `derived_edges.jsonl` is still derived from canonical rows rather than a truth owner by itself.

---

## Layer 3 — Human-facing maintained wiki

**Path:** `wiki/`

**Role:**
- the reading surface for humans
- analyses, source pages, concepts, entities, project pages, timelines, and meta pages
- durable synthesis that remains inspectable and editable

**Important rule:**
The wiki is not raw truth and not canonical machine truth.
It is the reviewed, human-readable synthesis layer.

**Promotion rule:**
Ontology output should not silently overwrite wiki pages.
Use reviewed promotion and shadow reconcile patterns instead.

**Repo-local note:**
For current DocTology runtime work, treat root `wiki/_meta/`, `wiki/sources/`, and sibling directories as the primary maintained wiki surface.
The deeper `wiki/wiki/` subtree is retained as checked-in sample/historical content and should not be treated as the default operator surface unless the task explicitly targets it.

---

## Layer 4 — Derived and operational support layers

### Graph projection
**Path:** `warehouse/graph_projection/`

**Role:**
- bounded graph inspect
- graph hints and neighborhood/path support
- derived read-only sidecar

**Not allowed:**
- becoming the truth owner
- overriding canonical JSONL decisions

### SQLite operational mirrors
**Path:** typically `wiki/state/*.sqlite`

**Role:**
- rebuildable operational index
- lightweight local navigation/support state

### DuckDB analytical mirrors
**Path:** typically `wiki/state/*.duckdb`

**Role:**
- rebuildable analytical mirror
- coverage/audit/operator support

**Important rule for both SQLite and DuckDB:**
They may improve usability, but they do not outrank raw or canonical file truth.

---

## Public reference repo vs live workspace

This is the most important operating distinction.

### Public/reference repo should primarily own
- code
- tests
- templates
- flows/reviews/plans
- small examples/fixtures
- reusable product/runtime contracts

### Live/private workspace should primarily own
- real corpus `raw/`
- real populated canonical `warehouse/jsonl/`
- live source/analysis/wiki growth
- daily operator state tied to a private corpus

### Rebuildable local state should usually remain outside tracked truth
- graph projection caches unless intentionally shipped as fixtures
- SQLite/DuckDB mirrors
- temporary review/runtime state
- agent-local planning artifacts

---

## Layer anti-patterns to avoid

### 1. Graph drift
Treating graph projection as if it were canonical truth.

### 2. DB drift
Treating SQLite or DuckDB as if they outranked `raw/` or `warehouse/jsonl/`.

### 3. Workspace drift
Letting the public reference repo slowly become the private daily corpus repo.

### 4. Silent wiki rewrite drift
Letting ontology outputs overwrite the human-facing wiki without explicit review.

---

## Safe default

Use this operational pattern:
- collect or backfill source truth under `raw/`
- run production ingest to refresh canonical truth under `warehouse/jsonl/`
- rebuild derived graph/projection helpers
- inspect shadow reconcile / review surfaces
- promote only reviewed synthesis into the wiki
