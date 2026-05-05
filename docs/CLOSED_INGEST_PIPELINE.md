# Closed Ingest Pipeline

Updated: 2026-05-05

## Purpose

The closed ingest contract exists to prevent source processing from stopping at
registration.

`python3 scripts/llm_wiki.py ingest ...` is a **source registration** tool. It
creates or updates the source page and meta surfaces, but it is not the whole
ontology-backed ingest loop.

A full ingest should close the artifact lifecycle:

1. register the source identity
2. update canonical JSONL registries when ontology-backed ingest applies
3. project the source and canonical updates into the human-facing wiki
4. refresh meta pages
5. run structural validation
6. report what changed, what was skipped, and what remains uncertain

## Lifecycle

### 1. Source registration

- read source material from `raw/inbox/`, `raw/processed/`, or `raw/notes/`
- keep `raw/` immutable
- create or update the matching `wiki/sources/` page
- append `wiki/_meta/log.md`
- refresh `wiki/_meta/index.md`

### 2. Canonical JSONL update

When ontology-backed ingest applies, update relevant registries under
`warehouse/jsonl/` before broad wiki synthesis.

Typical targets include:

- `documents.jsonl`
- `messages.jsonl`
- `entities.jsonl`
- `claims.jsonl`
- `claim_evidence.jsonl`
- `segments.jsonl`
- `derived_edges.jsonl`
- `source_versions.jsonl`

Not every source requires every registry. The report must distinguish:

- updated
- skipped
- not applicable
- pending manual or model-backed review

### 3. Wiki projection

After source registration and applicable canonical updates, update the
human-facing wiki:

- `wiki/sources/`
- affected `wiki/concepts/`
- affected `wiki/entities/`
- affected `wiki/people/`
- affected `wiki/projects/`
- affected `wiki/timelines/`
- durable analyses under `wiki/analyses/` when useful

The wiki remains the human reading and synthesis surface. It is not a dump of
raw chunks or graph edges.

### 4. Meta refresh

Refresh operational surfaces after meaningful changes:

- `wiki/_meta/index.md`
- `wiki/_meta/log.md`

Optional review pages may be refreshed when the repository maintains them, but
they are still derived review aids rather than canonical truth.

### 5. Structural validation

Validation may check:

- JSONL parseability
- required fields
- duplicate IDs
- source and segment references
- broken wikilinks
- orphan pages
- stale pages
- index/log freshness
- derived-edge references to reviewed claim status

Validation must not claim to determine semantic truth.

## Semantic judgment boundary

The closed pipeline is a lifecycle contract, not a heuristic semantic router.

Allowed deterministic work:

- file discovery
- ID generation
- source registration
- line or segment reference bookkeeping
- JSONL syntax and required-field checks
- link integrity checks
- meta index/log refresh
- structural completion reporting

Forbidden deterministic work:

- filename keyword routing as semantic judgment
- token-shape routing as semantic judgment
- automatic page selection by regex as if it were understanding
- automatic claim acceptance without review metadata
- graph projection as canonical truth
- retrieval result as truth
- browser direct mutation of `raw/` or broad `warehouse/jsonl/` registries

The agent or a configured helper model may help decide affected pages, claims,
entities, contradictions, and open questions. Those judgments must remain
grounded in source evidence and repository rules.

## Claim review boundary

`warehouse/jsonl/claims.jsonl` may contain draft or pending claims. A claim
should be treated as accepted only when review metadata and supporting evidence
make that state explicit.

Derived edges may be materialized from canonical records, but the projection is
not the authority. When a projection conflicts with canonical JSONL, canonical
JSONL wins.

## Reporting contract

A closed ingest report should state:

- source registered
- canonical registries updated, skipped, or not applicable
- wiki pages created or updated
- meta pages refreshed
- validation run and result
- unresolved uncertainties
- follow-up actions

Do not report registration-only work as a completed ontology-backed ingest.

## Relationship to stricter profiles

This contract is intentionally smaller than a strict LLM-first proposal system.
It does not require:

- proposal registries
- a manifest-driven executor
- helper-model-only semantic paths
- automatic rejection of local agent processing

It does require that deterministic scripts stay structural and that semantic
judgment is not smuggled into filename, keyword, token, YAML, graph, retrieval,
or workbench shortcuts.
