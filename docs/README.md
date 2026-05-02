# Docs Portal

This directory is the repository-facing documentation portal for the live DocTology LLM Wiki / ontology implementation.

Start here when you need current truth from the codebase rather than historical discussion:

- [`CURRENT_STATE.md`](./CURRENT_STATE.md): current product surfaces, write boundaries, and supported operator flows
- [`ARCHITECTURE.md`](./ARCHITECTURE.md): runtime components, entrypoints, and data flow
- [`LAYERS.md`](./LAYERS.md): source-vs-canonical-vs-human-facing-vs-derived boundaries
- [`SKILLS_INTEGRATION.md`](./SKILLS_INTEGRATION.md): how repo rules, skills, and local tooling fit together
- [`ROADMAP.md`](./ROADMAP.md): near-term alignment work and known gaps
- [`IMPACT_SUMMARY.md`](./IMPACT_SUMMARY.md): current refresh summary, checked files, and remaining drift
- [`LLM_FIRST_ONTOLOGY_BOOTSTRAP_PROFILE.md`](./LLM_FIRST_ONTOLOGY_BOOTSTRAP_PROFILE.md): promoted default `llm-wiki-bootstrap --profile llm-first-ontology` contract

Current repository posture:

- canonical local wiki-maintenance CLI: `scripts/llm_wiki.py`
- profile-aware source ingest path: `scripts/generic_ingest.py`
- canonical repeated-export ingest path: `scripts/incremental_ingest.py`
- strict LLM source compile workflow: `scripts/llm_compile_source.py`
- strict LLM query workflow: `scripts/llm_query.py`
- human-reviewed proposal lifecycle workflow: `scripts/proposal_review.py`
- optional local sidecar workbench: `apps/workbench/` via `scripts/workbench_api.py`
- declarative contracts live under `intelligence/`, but execution still lives in Python
- contract entrypoint: `intelligence/contract_index.yaml`
- contract validators: `scripts/validate_intelligence.py`, `scripts/validate_workbench_manifest.py`, `scripts/validate_profiles.py`, `scripts/validate_registries.py`

Legacy note:

- `scripts/workbench_api.py` is still live, but it is intentionally a compatibility wrapper over the package-style modules in `scripts/workbench/`

Strict LLM-first note:

- deterministic code may create citation anchors, source pages, indexes, and validation reports
- semantic compile/query must use an LLM; if no helper LLM is configured, local scripts emit agent handoff bundles/prompts for the surrounding chat agent instead of claiming semantic success
- explicit prompt/bundle emission flags are inspection surfaces, not semantic success
- unreviewed compile proposals are draft pages and must not become query evidence
- active wiki updates from compile output require explicit human-reviewed content
