---
name: repo-docs-intelligence-bootstrap
description: Use when a repository needs a lightweight ontology and documentation layer that evolves with the codebase to reduce drift, prevent structural mistakes, and keep current repository truth explicit. Trigger for requests to refresh current-state or architecture docs from live code, classify or archive older docs, create or update a root AGENTS.md, or introduce or maintain minimal glossary/manifests/handlers/policies/schemas/capabilities without rewriting the runtime.
---

# Repo Docs + Intelligence Bootstrap

Use this skill when a repository has grown through experiments and now needs a lightweight ontology layer to grow alongside the implementation.
Bootstrap is only the starting point; the real goal is ongoing alignment that keeps repository truth explicit, reduces drift, and prevents repeated structural mistakes.

## Use This Skill For

- refreshing repository docs so they match the live codebase
- reorganizing a messy or transitional docs tree around current vs legacy truth
- archiving or classifying superseded docs instead of silently deleting them
- creating or updating a root `AGENTS.md` aligned with current repository rules
- introducing or maintaining a minimal schema-first intelligence layer
- keeping glossary/manifests/handlers/policies/schemas/capabilities synchronized as the project evolves

## Do Not Use This Skill For

- isolated bug fixes with no repository-wide documentation or contract impact
- small feature work that does not affect docs, guidance, or canonical contracts
- greenfield architecture design or speculative redesigns
- replacing the runtime with a manifest-driven execution system
- purely local ontology work that does not require repository-wide alignment

## What This Skill Optimizes For

- current documentation that matches real code
- archived or classified older docs instead of silent deletion
- a small schema-first intelligence layer that stays lightweight and useful
- thin-wrapper / thick-core guidance
- an `AGENTS.md` file that captures repository working rules
- a repeatable validator-backed self-check loop instead of documentation by hope

This skill is for incremental refactors. Do not turn it into a greenfield rewrite.

## What This Skill Produces

The usual target output is:

- a `docs/README.md` portal
- current-state architecture docs that reflect actual code
- `docs/archive/` for superseded material with a status banner
- optional `docs/reviews/` and `docs/experiments/`
- a minimal `intelligence/` directory with glossary, manifests, handlers, policies, schemas, and capabilities
- a root `AGENTS.md`
- an impact summary describing what changed, what stayed legacy, and what drift still remains
- a validator result summary when `scripts/validate_repo_docs_intelligence.py` is available

## Core Rules

### Search Before Code

Before writing anything new, search for:

- current entrypoints
- existing CLI surfaces
- existing schema SQL
- existing wrappers
- existing docs that can be reused or moved
- existing glossary or policy files

Prefer reuse and relabeling over inventing a parallel structure.

### Impact Analysis First

Before changing docs, schema contracts, manifests, handlers, or graph/materialization code:

1. identify the live entrypoints
2. identify the current source-of-truth files
3. identify legacy paths that still matter
4. note what the change will replace and what it will not replace

Always leave an impact summary when structural changes are made.

### Schema First

If you are introducing a new behavior, define it in this order:

1. glossary term
2. action or dataset contract
3. policy or SQL contract
4. Python implementation link

Do not add Python orchestration first and invent the contract later.

### Update The Smallest Canonical Truth First

When a concept, action, boundary, or workflow changes, first update the smallest canonical artifact that names it clearly:

- glossary term
- manifest entry
- handler or policy contract
- schema excerpt
- then implementation and docs references

The ontology should stay lightweight. Add only what reduces ambiguity, drift, or repeated mistakes.

### Treat Drift As A Bug

Drift is not documentation debt to defer indefinitely.
If code, docs, manifests, policies, or `AGENTS.md` disagree on current truth, resolve the mismatch or explicitly record it in the same task.

### Prefer Living Alignment Over Big Design

Do not wait for a large redesign before correcting terminology, contracts, or repository guidance.
Make small, explicit updates that keep current truth aligned with real implementation.

### Keep Layers Separate

- YAML stores meaning, contracts, and relationships.
- SQL stores schema, canonical shapes, or materialized contract excerpts.
- policy files store gates and rule semantics.
- Python stores execution only.

Do not make YAML into a second programming language.

## Workflow

### 1. Detect The Live Change Surface

Figure out:

- what the real package root is
- whether an official CLI already exists
- where wrappers live
- what the current docs layout looks like
- whether note graph and ontology truth graph are distinct or still mixed
- whether a declarative layer already exists in any form
- which current concepts, datasets, handlers, policies, or schemas are affected
- which legacy paths still matter and why

### 2. Analyze Impact Before Editing

Before changing code, docs, contracts, handlers, or schemas:

1. identify the live entrypoints
2. identify the current source-of-truth artifacts
3. identify what layers and datasets are affected
4. identify what will remain intentionally legacy
5. identify likely drift points if the change is applied incompletely

### 3. Refresh Current Docs And Classify Existing Material

Create or refresh current docs from code, not memory:

- `docs/README.md`
- `docs/CURRENT_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/LAYERS.md`
- `docs/SKILLS_INTEGRATION.md`
- `docs/ROADMAP.md`
- `docs/IMPACT_SUMMARY.md`

Then classify older material into:

- `docs/adr/`
- `docs/reviews/`
- `docs/experiments/`
- `docs/archive/`

Do not delete old docs unless they are obviously duplicated and the user explicitly wants deletion.

If a file goes to `docs/archive/`, prepend a status banner:

```md
> Status: Archived
> Source of Truth: No
> Last Updated: YYYY-MM-DD
> Superseded By: `docs/CURRENT_STATE.md`, `docs/ARCHITECTURE.md`
```

Always verify:

- official entrypoints
- package or script ownership
- schema authority
- whether legacy paths still exist
- default graph materializer and retrieval provider behavior

If the repo is transitional, say so directly.

### 4. Maintain Minimal Intelligence Artifacts

Keep the intelligence layer minimal, current, and useful.
Update or extend only the artifacts needed to express the change clearly and reduce repeated confusion.

The minimum useful set is:

- `intelligence/glossary.yaml`
- `intelligence/manifests/actions.yaml`
- `intelligence/manifests/entities.yaml`
- `intelligence/manifests/datasets.yaml`
- `intelligence/handlers/*.yaml`
- `intelligence/policies/*.yaml`
- `intelligence/schemas/*.sql`
- `intelligence/registry/capabilities.yaml`

Recommended minimum pattern:

- glossary defines canonical terms, aliases, deprecations, and layer meanings
- entities define the named things the repository reasons about
- datasets define canonical data shapes, owners, and freshness expectations
- actions map reusable contracts to current Python callables
- handlers describe event chains and impact flow, even if they are documented-only
- policies describe repository rules, gates, and stopping conditions
- SQL files mirror current contract excerpts and point to the authoritative implementation
- capability bindings connect action keys to Python execution points

Do not expand the ontology for completeness alone.
Only add artifacts that reduce ambiguity, drift, or implementation mistakes.

### 5. Keep Python Linking Minimal

If you add Python support, keep it small.

Good examples:

- a registry loader that reads the intelligence files
- a CLI command that describes actions, capabilities, or handlers
- a helper that resolves action keys to Python callables
- a capability binding that maps an action contract to a pure implementation function

Bad examples:

- replacing the whole runtime with a new manifest executor
- rewriting orchestration around YAML

### 6. Synchronize Code, Docs, And Guidance In The Same Task

When code changes, update the corresponding docs and intelligence artifacts in the same task.

You must always check whether these files need updates:

- `docs/CURRENT_STATE.md` when behavior, entrypoints, providers, defaults, or runtime flow changes
- `docs/ARCHITECTURE.md` when component roles, data flow, or storage responsibilities change
- `docs/LAYERS.md` when boundaries between Raw/Core/Derived/Search/Graph/Serve change
- `docs/SKILLS_INTEGRATION.md` when CLI, skill wrappers, or external entrypoints change
- `docs/ROADMAP.md` when phased cleanup or deferred drift changes materially
- `docs/IMPACT_SUMMARY.md` when structural changes or validator findings need explicit reporting
- `intelligence/glossary.yaml` when a new domain term or canonical concept is introduced or renamed
- `intelligence/manifests/actions.yaml` when an action is added, removed, renamed, or its contract changes
- `intelligence/manifests/entities.yaml` when the set of named entities changes
- `intelligence/manifests/datasets.yaml` when a canonical dataset or shape changes
- `intelligence/handlers/*.yaml` when event chains or orchestration flow changes
- `intelligence/policies/*.yaml` when gate, policy, or rule semantics change
- `intelligence/registry/capabilities.yaml` when Python capability bindings change
- `intelligence/schemas/*.sql` when canonical schema, views, or materialization logic changes
- `AGENTS.md` when working style, repository rules, or documentation expectations drift from current practice

Do not finish a refactor after updating code only.

### 7. Add Or Refresh AGENTS.md

Create a root `AGENTS.md` if missing, or update it if drifted.

Include:

- working style
- repository rules
- documentation rules
- definition of done

Keep it aligned with the actual architecture and docs structure.

### 8. Run The Validator As A Self-Check

If `scripts/validate_repo_docs_intelligence.py` is available, run it against the repository root after structural changes:

```bash
python scripts/validate_repo_docs_intelligence.py --repo-root <path>
```

If you can derive a changed-file list from the environment, pass it with `--changed-files <path>`.
Do not claim success if the validator reports hard failures.
If the validator reports warnings, surface them under remaining drift or cautions.

### 9. Report Drift Status

## Reporting Format

When you finish, report in this order:

1. repository analysis summary
2. docs structure changes
3. intelligence layer changes
4. legacy vs current split
5. validator summary
6. drift resolved vs remaining
7. cautions
8. next steps

Before ending the task, explicitly report:

1. which docs/intelligence files were updated
2. which were checked but did not need changes
3. any remaining drift or legacy exceptions
4. validator errors or warnings, or why the validator was not run

## Guardrails

Do not:

- claim a CLI or package surface exists if it does not
- claim wrappers are thin if they still own logic
- silently hide legacy paths still used in production
- create speculative manifests for runtime features that do not exist
- overdesign the intelligence layer
- expand the ontology without a concrete ambiguity, drift, or reuse problem to solve
- ignore validator warnings and still report the repository as fully aligned

## Bundled Templates

Use these bundled files when useful:

- `assets/AGENTS.template.md`
- `assets/docs/README.template.md`
- `assets/docs/CURRENT_STATE.template.md`
- `assets/docs/ARCHITECTURE.template.md`
- `assets/docs/LAYERS.template.md`
- `assets/docs/SKILLS_INTEGRATION.template.md`
- `assets/docs/ROADMAP.template.md`
- `assets/docs/IMPACT_SUMMARY.template.md`
- `assets/intelligence/glossary.template.yaml`
- `assets/intelligence/actions.template.yaml`
- `assets/intelligence/entities.template.yaml`
- `assets/intelligence/datasets.template.yaml`
- `assets/intelligence/handler.template.yaml`
- `assets/intelligence/policy.template.yaml`
- `assets/intelligence/capabilities.template.yaml`
- `assets/intelligence/schema.template.sql`

## Bundled Scripts

- `scripts/validate_repo_docs_intelligence.py`

Adapt the templates to the repo. Do not paste them blindly.
Use the validator as a guardrail, not as a substitute for impact analysis.
