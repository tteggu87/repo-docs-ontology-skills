# Docs Portal

This directory is the repository-facing documentation portal for the live `llm-wiki-obsidian` implementation.

Start here when you need current truth from the codebase rather than historical discussion:

- [`CURRENT_STATE.md`](./CURRENT_STATE.md): current product surfaces, write boundaries, and supported operator flows
- [`ARCHITECTURE.md`](./ARCHITECTURE.md): runtime components, entrypoints, and data flow
- [`LAYERS.md`](./LAYERS.md): source-vs-canonical-vs-human-facing-vs-derived boundaries
- [`SKILLS_INTEGRATION.md`](./SKILLS_INTEGRATION.md): how repo rules, skills, and local tooling fit together
- [`ROADMAP.md`](./ROADMAP.md): near-term alignment work and known gaps
- [`IMPACT_SUMMARY.md`](./IMPACT_SUMMARY.md): current refresh summary, checked files, and remaining drift

Current repository posture:

- canonical local wiki-maintenance CLI: `scripts/llm_wiki.py`
- canonical repeated-export ingest path: `scripts/incremental_ingest.py`
- optional local sidecar workbench: `apps/workbench/` via `scripts/workbench_api.py`
- declarative contracts live under `intelligence/`, but execution still lives in Python

Legacy note:

- `scripts/workbench_api.py` is still live, but it is intentionally a compatibility wrapper over the package-style modules in `scripts/workbench/`
