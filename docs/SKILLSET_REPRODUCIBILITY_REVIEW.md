# Skillset Reproducibility Review

Updated: 2026-05-03

## Purpose

This document records the current review of how DocTology's reusable skillset
should be represented in GitHub.

The immediate question is not whether the live DocTology runtime works.  The
runtime is already relatively mature.  The higher-leverage question is:

> Can a fresh GitHub clone reproduce the DocTology LLM Wiki / ontology bootstrap
> workflow without relying on hidden machine-local skill files?

Current answer after the vendoring implementation: **yes for the repo-local
bootstrap path, guarded by smoke tests**.

## Current State

The repository now tracks project-local skill surfaces and the full bootstrap
generator package under:

```text
.agents/skills/
  README.md
  llm-wiki-bootstrap/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/bootstrap_llm_wiki.py
    scripts/refresh_duckdb_analytics.py
    scripts/reindex_sqlite_operational.py
    scripts/verify_three_layer_drift.py
  llm-wiki-ontology-ingest/
    SKILL.md
  ontology-pipeline-operator/
    SKILL.md
    evals/evals.json
    references/operating-model.md
```

This replaces the previous temporary state where GitHub contained the skill
surface but the project-local `llm-wiki-bootstrap` script delegated to an
installed local generator under `~/.codex/skills`.

The repo-local generator is now exercised by
`tests/test_bootstrap_skill_reproducibility.py`, including an empty-`HOME`
bootstrap run that cannot accidentally depend on `~/.codex/skills`.

## Ralplan Consensus

### Decision Drivers

1. **Reproducibility**
   - A GitHub clone should contain the materials needed to bootstrap the same
     LLM-first ontology workspace.
2. **Source-of-truth clarity**
   - `.codex/` is local runtime state and must stay ignored.
   - `.agents/skills/` should be the project-local, commit-ready skill surface.
3. **No hidden dependency on one machine**
   - The bootstrap path should not require the original developer's
     `~/.codex/skills` directory.
4. **Drift prevention**
   - The repository needs smoke tests so future skill edits do not silently
     break generated repos.

### Viable Options Considered

#### Option A. Keep the thin launcher

Pros:

- avoids copying a large generator file into the repository
- avoids immediate duplicated generator implementations
- works on the original machine where the installed skill exists

Cons:

- GitHub clone is not self-contained
- new users or future agents cannot reliably bootstrap from the repo alone
- contradicts the goal of making DocTology a reusable skill-backed project

Verdict: **Rejected as the long-term shape**.

#### Option B. Commit the full bootstrap skill package under `.agents/skills`

Pros:

- GitHub clone becomes self-contained for the bootstrap workflow
- `.agents/skills` becomes the visible project-local skill source of truth
- future changes can be reviewed, tested, and committed like normal code
- better matches the goal of reusable LLM Wiki / ontology scaffolding

Cons:

- larger diff
- the installed local skill copy can drift unless sync rules are documented

Verdict: **Chosen**.

#### Option C. Keep only docs and require manual skill installation

Pros:

- smallest repository footprint
- no generator-copy maintenance

Cons:

- not enough for a reproducible project
- makes the most important entrypoint external to the repo

Verdict: **Rejected**.

## Gstack Engineering Review

The highest-impact gap is not in the query or ingest runtime.  The higher-impact
gap is distribution and reproducibility of the skillset.

Recommended target layout:

```text
.agents/skills/llm-wiki-bootstrap/
  SKILL.md
  agents/
    openai.yaml
  references/
    scaffold-spec.md
    three-layer-file-contract.md
    three-layer-taxonomy.md
  scripts/
    bootstrap_llm_wiki.py
    refresh_duckdb_analytics.py
    reindex_sqlite_operational.py
    verify_three_layer_drift.py

.agents/skills/llm-wiki-ontology-ingest/
  SKILL.md

.agents/skills/ontology-pipeline-operator/
  SKILL.md
  references/
    operating-model.md
  evals/
    evals.json
```

Recommended source-of-truth rule:

> Treat `.agents/skills` in this repository as the canonical DocTology skill
> package.  Treat `~/.codex/skills` as an installed copy, not as the primary
> source.

This reverses the current partial arrangement and eliminates the hidden local
dependency.

## Whiplash Review

### Reviewer Challenge

The thin launcher solved a narrow problem: avoiding a broken command path.

It did not solve the actual product problem:

> A future clone should be able to bootstrap a DocTology-style LLM-first
> ontology workspace from the repository itself.

Therefore the launcher is an acceptable temporary bridge, but should not be the
final implementation.

### Required Correction

Replace the thin launcher with the full generator package and commit all
non-generated skill support files needed by the generator.

Do not commit:

- `__pycache__/`
- `results.tsv`
- local runtime state
- `.codex/`
- machine-specific config or credentials

### Pass Condition

The review passes only when:

1. a clean clone contains the full bootstrap generator under `.agents/skills`
2. running the repo-local bootstrap command creates a new `llm-first-ontology`
   workspace
3. the generated workspace passes its validators
4. the repository tests still pass
5. docs clearly state that `.agents/skills` is the canonical committed skillset

## Implemented PR Scope

### P0. Vendor the full bootstrap package

Replace:

```text
.agents/skills/llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py
```

with the full generator from the installed skill package.

Also add the bootstrap support files:

```text
.agents/skills/llm-wiki-bootstrap/agents/openai.yaml
.agents/skills/llm-wiki-bootstrap/references/scaffold-spec.md
.agents/skills/llm-wiki-bootstrap/references/three-layer-file-contract.md
.agents/skills/llm-wiki-bootstrap/references/three-layer-taxonomy.md
.agents/skills/llm-wiki-bootstrap/scripts/refresh_duckdb_analytics.py
.agents/skills/llm-wiki-bootstrap/scripts/reindex_sqlite_operational.py
.agents/skills/llm-wiki-bootstrap/scripts/verify_three_layer_drift.py
```

### P0. Add repo-local bootstrap smoke validation

Add a test that runs the repo-local generator into a temporary directory and
checks that the strict profile is usable.

Minimum acceptance:

```bash
python3 .agents/skills/llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py "$TMPDIR/new-wiki"
cd "$TMPDIR/new-wiki"
python3 scripts/validate_intelligence.py
python3 scripts/validate_profiles.py
python3 scripts/validate_registries.py
```

The smoke test should verify:

- default profile is `llm-first-ontology`
- `wikiconfig.example.json` exists
- local ignored `wikiconfig.json` exists with helper LLM disabled
- helper-disabled semantic paths emit agent handoff material rather than
  heuristic semantic success
- `scripts/query_analysis.py` exists for durable saved answers
- proposal lifecycle and contract manifests exist

### P1. Sync the remaining skill support files

Add support files for `ontology-pipeline-operator` if they are part of the
installed skill package and are not generated artifacts:

```text
.agents/skills/ontology-pipeline-operator/references/operating-model.md
.agents/skills/ontology-pipeline-operator/evals/evals.json
```

### P1. Document canonical skill update flow

Add or update a short section in `docs/SKILLS_INTEGRATION.md`:

1. edit `.agents/skills` first
2. run bootstrap smoke tests
3. run repository tests
4. only then sync to any local installed skill directory if desired

### P2. Optional install/sync helper

Only after the canonical layout is stable, consider a helper script that copies
from `.agents/skills` to the local installed skill directory.

That helper must not make `~/.codex/skills` the source of truth.

## Non-Goals

Do not use this work to:

- change the LLM-first semantic philosophy
- reintroduce heuristic semantic fallback
- make `content_units` behave like RAG chunks
- auto-apply compile proposals to active concept/entity/project pages
- commit `.codex/` runtime state
- make YAML contain semantic judgments

## Final Assessment

The current implementation is good enough as a temporary bridge, but not good
enough as the final GitHub skill distribution model.

The highest-leverage next fix is:

> Make `.agents/skills/llm-wiki-bootstrap` self-contained by committing the full
> generator package and validating it with a repo-local bootstrap smoke test.

This is more important than further tuning query/ingest behavior right now,
because it determines whether DocTology can reproduce itself from GitHub.
