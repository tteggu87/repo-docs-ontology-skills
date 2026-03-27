---
name: ontology-pipeline-operator
description: Operate and maintain a repository that already uses the DocTology stack. Use this skill whenever the user asks to refresh ontology artifacts, rebuild reports, compare raw vs jsonl quality, check graph projection regressions, sync CURRENT_STATE or IMPACT docs, or add a single-entry pipeline on top of existing `repo-docs-intelligence-bootstrap`, `lightweight-ontology-core`, or `lg-ontology` outputs. Prefer this skill when the repo already has canonical JSONL, derived edges, graph projection artifacts, and multiple scripts that operators are manually running in sequence.
---

# Ontology Pipeline Operator

Use this skill after a repository already has a DocTology-style structure.
This skill is for operating, refreshing, and regression-checking that structure, not for inventing the ontology from scratch.

## Use This Skill For

- rebuilding canonical ontology outputs after source documents change
- keeping reports, graph projection, and docs sync on one canonical execution path
- comparing raw-source mode and jsonl-only mode when report quality is questioned
- catching regressions where graph consumers silently fall back to claims or top-N summaries
- wiring a thin `pipeline_refresh.py` or equivalent single-entry operator command
- wiring a thin docs sync script such as `sync_current_state.py`

## Do Not Use This Skill For

- greenfield repo bootstrap with no ontology layer yet
- replacing `repo-docs-intelligence-bootstrap`, `lightweight-ontology-core`, or `lg-ontology`
- turning YAML into a full runtime executor
- promoting graph projection artifacts to canonical truth

## First Checks

Before editing anything, find:

- the current raw-source SSOT
- the current exploration SSOT
- the current report entrypoint
- whether docs sync exists
- whether validators already check relation-family and docs drift

If the repo already has a canonical single-entry script, prefer strengthening it over inventing a second one.

## Operating Model

Treat these as separate layers:

- raw source truth
- canonical JSONL or equivalent registries
- derived edges
- graph projection
- reports
- current-state / impact docs
- validators

When the corpus is conversational or sequential:

- keep a full-fidelity `messages.jsonl` or equivalent event registry
- do not use `claims` as the speaker/activity SSOT
- preserve full participant coverage in segments

## Recommended Workflow

### 1. Rebuild canonical outputs

Use the repo's existing extraction script or entrypoint first.

### 2. Rebuild derived graph artifacts

Re-materialize derived edges and re-export graph projection.

### 3. Rebuild reports

If both raw and structured modes exist, regenerate both when quality is in doubt.

### 4. Sync docs

Regenerate `CURRENT_STATE`, `IMPACT_SUMMARY`, or their equivalents from live artifacts.

### 5. Validate

Run validators last so they check the final current state, not an intermediate one.

## What To Add When Missing

If the repo lacks them, consider adding:

- `scripts/pipeline_refresh.py`
- `scripts/sync_current_state.py`
- docs drift validation
- relation-family regression checks
- raw-vs-structured comparison notes for reports

Keep these additions thin and execution-oriented.

## Report Back With

1. canonical entrypoint used or added
2. outputs refreshed
3. validation result
4. raw vs structured quality difference, if relevant
5. remaining operational risks
