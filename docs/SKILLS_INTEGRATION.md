# Skills Integration

Updated: 2026-04-13

## Repo-local source of truth

For this repository, `AGENTS.md` is the primary working contract.

That means:

- the wiki maintenance workflow lives here, not only in reusable skills
- future agents should read `AGENTS.md`, then `wiki/_meta/index.md`, then recent `wiki/_meta/log.md`
- durable repo behavior should be encoded in this repository before depending on external skill memory
- project-local reusable skills should be committed under `.agents/skills/`;
  installed copies under `~/.codex/skills` are local installs, not the canonical
  GitHub source

## Relevant reusable skills

- `repo-docs-intelligence-bootstrap`
  - use for repository-level docs and intelligence alignment
- `llm-wiki-bootstrap`
  - use for new repositories that should start with the promoted strict `llm-first-ontology` contract scaffold
- `llm-wiki-ontology-ingest`
  - use when processing new sources into canonical registries plus wiki pages
- `ontology-pipeline-operator`
  - use when refreshing existing ontology artifacts and repeated maintenance flows

See also:

- [`SKILLSET_REPRODUCIBILITY_REVIEW.md`](./SKILLSET_REPRODUCIBILITY_REVIEW.md)
  for the current plan to make the DocTology skillset fully reproducible from a
  clean GitHub clone.

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
- bootstrap changes should be promoted only after the equivalent DocTology contract/runtime path is implemented and validated here

## Skill update flow

When updating DocTology skills:

1. Treat `.agents/skills` as the committed project-local source of truth.
2. Do not commit `.codex/`; it is local runtime/install state.
3. Update the repo-local skill files first.
4. Run a repo-local bootstrap smoke test when `llm-wiki-bootstrap` changes.
5. Run repository tests.
6. Sync to `~/.codex/skills` only as a local install step after the repository
   copy is correct.
