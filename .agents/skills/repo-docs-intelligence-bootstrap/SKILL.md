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
- helping a repo-wide docs/intelligence layer coexist with a project-local wiki contract when both are present

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
- a root contract that can coexist with a deeper `wiki/AGENTS.md` without conceptually overwriting it
- a repeatable validator-backed self-check loop instead of documentation by hope

This skill is for incremental refactors. Do not turn it into a greenfield rewrite.

## What This Skill Produces

The usual target output is:

- a `docs/README.md` portal
- current-state architecture docs that reflect actual code
- `docs/archive/` for superseded material with a status banner
- optional `docs/reviews/` and `docs/experiments/`
- a minimal `intelligence/` directory with glossary, manifests, handlers, policies, schemas, and capabilities
- optional `scripts/pipeline_refresh.py` and `scripts/sync_current_state.py` when the repo needs a single entry and doc-sync path
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
When entrypoints disagree, verify the canonical surface from live registration points first, such as:

- `pyproject.toml` script entries
- package CLI modules like `pkg/cli.py`
- shell wrappers in `scripts/` or `bin/`
- imports that show whether a wrapper is only delegating to a deeper entrypoint

Do not promote a wrapper, bootstrap script, or operator convenience command to primary truth unless the repository actually treats it as canonical.
Make the official CLI or package-owned command the primary entrypoint when package metadata, imports, or registration points show that it is the real canonical surface.
Keep wrappers visible as a secondary transitional surface when operators still rely on them, but do not document them as the primary or canonical entrypoint.

### Coexist With A Wiki Contract

If a repository already has a project-local wiki workspace:

- treat root `AGENTS.md` as the repo-wide contract
- treat `wiki/AGENTS.md` as the governing contract for files under `wiki/`
- treat `wiki/wiki/_meta/index.md` and recent `wiki/wiki/_meta/log.md` entries as durable context sources before meaningful code, architecture, or product-direction changes
- do not conceptually overwrite or erase wiki-specific operating rules when refreshing root guidance

Preferred product stance:

- recommended order may exist for onboarding
- but the implementation should tolerate either order
- root guidance should merge with wiki guidance, not replace it

### Impact Analysis First

Before changing docs, schema contracts, manifests, handlers, or graph/materialization code:

1. identify the live entrypoints
2. identify the current source-of-truth files
3. identify legacy paths that still matter
4. note what the change will replace and what it will not replace

Always leave an impact summary when structural changes are made.
If a legacy path is still imported, delegated to, or required by the current runtime, record it as intentional legacy or transitional support rather than hiding it as dead code.
Treat a still-live legacy path as visible current context even when it is no longer preferred, and never archive it away while it remains on the runtime path.
If a dependency is still live in imports, runtime delegation, or operator workflows, say that it is still live and intentionally legacy instead of implying it has already been removed.

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
If an intelligence layer already exists, preserve current keys, term identities, dataset names, and capability bindings unless code evidence shows they are wrong.
Preserve existing keys and do not rename canonical keys just to make the structure feel cleaner.
Extend the existing layer in place before creating any new parallel manifest, glossary term, or replacement capability name.
Do not recreate the intelligence layer under a second set of keys when the current structure already captures the same meaning.

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
- whether imported legacy helpers are still on the live runtime path

If the repo is transitional, say so directly.
Do not archive, downplay, or relabel a still-imported path as historical just because it is no longer preferred.

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
- if the repo already has multiple ontology/report scripts, add a single-entry pipeline contract instead of leaving operators to memorize command order

Do not expand the ontology for completeness alone.
Only add artifacts that reduce ambiguity, drift, or implementation mistakes.
When an action already has Python implementation but lacks schema-first context, prefer filling the missing glossary, dataset, policy, or schema contracts around that action instead of inventing a new runtime abstraction.

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

Good repo-level maintenance additions:

- a thin `pipeline_refresh.py` that calls existing focused scripts in the canonical order
- a thin `sync_current_state.py` that regenerates current-state and impact docs from live artifacts

### 6. Synchronize Code, Docs, And Guidance In The Same Task

When code changes, update the corresponding docs and intelligence artifacts in the same task.

You must always check whether these files need updates:

- `docs/CURRENT_STATE.md` when behavior, entrypoints, providers, defaults, or runtime flow changes
- `docs/ARCHITECTURE.md` when component roles, data flow, or storage responsibilities change
- `docs/LAYERS.md` when boundaries between Raw/Core/Derived/Search/Graph/Serve change
- `docs/SKILLS_INTEGRATION.md` when CLI, skill wrappers, or external entrypoints change
- `docs/IMPACT_SUMMARY.md` and `docs/CURRENT_STATE.md` when ontology/report/graph counts or canonical execution paths change
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
If a repo already has current docs or intelligence artifacts, explicitly note which files were checked and intentionally left unchanged so the reader can distinguish stable truth from missed work.

### 7. Add Or Refresh AGENTS.md

Create a root `AGENTS.md` if missing, or update it if drifted.

Include:

- working style
- repository rules
- documentation rules
- wiki coexistence rules when a wiki workspace exists
- definition of done

Keep it aligned with the actual architecture and docs structure.
If `wiki/AGENTS.md` exists, explicitly add or preserve a wiki-aware block describing:

- deeper-scope precedence for files under `wiki/`
- wiki meta files as durable context sources
- root guidance extending wiki guidance rather than replacing it

Do not treat refreshing root `AGENTS.md` as permission to conceptually clobber a deeper wiki contract.

## Recommended Order vs Supported Order

Do not force one absolute bootstrap order for every repository.

Instead:

- provide a preferred order in docs when it improves onboarding
- but keep the implementation order-tolerant when `llm-wiki-bootstrap` and `repo-docs-intelligence-bootstrap` are both used

Recommended scenarios:

- existing codebase first, then wiki layer: `repo-docs-intelligence-bootstrap` -> `llm-wiki-bootstrap`
- wiki-first local knowledge surface, then repo-wide docs alignment: `llm-wiki-bootstrap` -> `repo-docs-intelligence-bootstrap`

The key invariant is:

- merge, not overwrite

### 8. Run The Validator As A Self-Check

If `scripts/validate_repo_docs_intelligence.py` is available, run it against the repository root after structural changes:

```bash
python scripts/validate_repo_docs_intelligence.py --repo-root <path>
```

If you can derive a changed-file list from the environment, pass it with `--changed-files <path>`.
Do not claim success if the validator reports hard failures.
If the validator reports warnings, surface them under remaining drift or cautions.
If the validator cannot be run, say why and fall back to a manual drift check rather than implying validator-clean alignment.

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

Minimum impact summary content:

- changed files or newly created artifacts
- checked-but-unchanged files
- current vs intentional legacy split
- remaining drift, warnings, or follow-up work
- validator status, including unresolved warnings

## Guardrails

Do not:

- claim a CLI or package surface exists if it does not
- claim wrappers are thin if they still own logic
- claim a wrapper is canonical when package metadata or direct imports show otherwise
- silently hide legacy paths still used in production
- archive or describe a still-imported path as dead, removed, or superseded
- create speculative manifests for runtime features that do not exist
- rename existing action, dataset, entity, glossary, or capability keys without code evidence
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
