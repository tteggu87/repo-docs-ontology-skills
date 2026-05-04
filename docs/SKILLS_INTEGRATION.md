# Skills Integration

Updated: 2026-04-13

## Repo-local source of truth

For this repository, `AGENTS.md` is the primary working contract.

That means:

- the wiki maintenance workflow lives here, not only in reusable skills
- future agents should read `AGENTS.md`, then `wiki/_meta/index.md`, then recent `wiki/_meta/log.md`
- durable repo behavior should be encoded in this repository before depending on external skill memory

## Relevant reusable skills

- `.agents/skills/repo-docs-intelligence-bootstrap`
  - use for repository-level docs and intelligence alignment
- `.agents/skills/llm-wiki-ontology-ingest`
  - use when processing new sources into canonical registries plus wiki pages
- `.agents/skills/ontology-pipeline-operator`
  - use when refreshing existing ontology artifacts and repeated maintenance flows

The repo-local skillset lives under `.agents/skills/`. Installed copies under
`~/.codex/skills` are local conveniences only; they are not the canonical
checked-in skill surface for this repository.

## Current repo/runtime fit

- `scripts/llm_wiki.py` is support tooling but still a real local entrypoint
- `scripts/incremental_ingest.py` is the current repeated-export ingest path
- `scripts/workbench_api.py` is the compatibility shell for the local workbench adapter
- reusable skills should align to these live paths instead of inventing new ones

## What skills should not do here

- they should not rewrite the truth hierarchy
- they should not promote graph projection to canonical truth
- they should not treat the browser workbench as the primary ownership surface
- they should not create a second manifest/runtime system parallel to the existing Python paths
- they should not treat `intelligence/` YAML as a second semantic wiki
