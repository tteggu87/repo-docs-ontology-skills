# Impact Summary

Updated: 2026-05-02

## Repository analysis summary

- The repo already had partial alignment across `README.md`, `AGENTS.md`, `docs/CURRENT_STATE.md`, the intelligence manifests, and the live Python runtime.
- The biggest new gap was docs/intelligence drift after strict LLM-first compile/query and YAML contract validators were introduced.
- The workbench split is transitional but real: `scripts/workbench_api.py` is still live while `scripts/workbench/` contains the thicker implementation.

## Docs structure changes

Updated:

- `docs/README.md`
- `docs/CURRENT_STATE.md`
- `docs/ARCHITECTURE.md`
- `docs/LAYERS.md`
- `docs/ROADMAP.md`
- `docs/IMPACT_SUMMARY.md`
- `docs/LLM_FIRST_ONTOLOGY_BOOTSTRAP_PROFILE.md`

Checked and left unchanged:

- `README.md`
- `docs/SKILLS_INTEGRATION.md`

## Tooling changes

Created:

- `scripts/validate_repo_docs_intelligence.py`
- `scripts/validate_workbench_manifest.py`
- `scripts/proposal_review.py`

## Intelligence layer changes

Updated:

- `intelligence/glossary.yaml`
- `intelligence/manifests/actions.yaml`
- `intelligence/manifests/datasets.yaml`
- `intelligence/registry/capabilities.yaml`
- `intelligence/policies/proposal_lifecycle.yaml`

Recently created and now documented as current contract surface:

- `intelligence/contract_index.yaml`
- `intelligence/policies/semantic_boundary.yaml`
- `intelligence/policies/proposal_lifecycle.yaml`
- `intelligence/manifests/semantic_workflows.yaml`
- `intelligence/manifests/page_policy.yaml`
- `intelligence/manifests/meta_surfaces.yaml`
- `intelligence/manifests/relation_types.yaml`
- `intelligence/manifests/registries.yaml`

Checked and left unchanged:

- `intelligence/manifests/source_families.yaml`
- `intelligence/manifests/workbench.yaml`

## Legacy vs current split

- Current canonical local entrypoints:
  - `scripts/llm_wiki.py`
  - `scripts/generic_ingest.py`
  - `scripts/incremental_ingest.py`
- `scripts/llm_compile_source.py`
- `scripts/llm_query.py`
- `scripts/proposal_review.py`
  - `scripts/wiki_graph_navigation.py`
  - `scripts/workbench/server.py` plus `scripts/workbench/repository.py` as the workbench core
- Intentional legacy/transitional support:
  - `scripts/workbench_api.py` remains a live compatibility wrapper and should not be archived as dead

## Drift resolved

- Missing docs portal pages for architecture, layers, skills integration, roadmap, and impact reporting
- Missing intelligence artifacts for named runtime surfaces, capability bindings, and explicit truth/mutation policies
- Missing action contracts for current workbench query-preview, save-analysis, review-claim, and maintenance flows
- Missing docs coverage for strict no-fallback LLM compile/query workflows
- Missing dataset/action/glossary coverage for the YAML contract layer
- Capability action drift for lexical diagnostics
- Missing safe proposal review/apply loop for human-reviewed active wiki updates

## Remaining drift

- `frontmatter.yaml` remains deferred
- `llm-wiki-bootstrap --profile llm-first-ontology` is now promoted as the default strict bootstrap scaffold after the DocTology contract set, proposal lifecycle, registries, validators, and strict route tests stabilized
- The promoted default now also generates the lightweight three-layer helper scripts and schema templates for rebuildable SQLite operational state and DuckDB wiki analytics mirrors
- The intelligence layer remains intentionally minimal and does not document every workbench route as a first-class entity
- Installed bootstrap skill promotion is complete; future changes should still stabilize in DocTology before being copied into the reusable bootstrap profile

## Validator status

- Current validator suite:
  - `python3 scripts/validate_repo_docs_intelligence.py`
  - `python3 scripts/validate_intelligence.py`
  - `python3 scripts/validate_workbench_manifest.py`
  - `python3 scripts/validate_profiles.py`
  - `python3 scripts/validate_registries.py`
  - `python3 -m pytest -q`
- The dedicated Workbench manifest validator is now present; a broader browser UI text regression remains a follow-up

## Cautions

- Do not promote `scripts/workbench_api.py` to the primary workbench truth surface; it is a live wrapper, not the thicker core
- Do not let browser flows mutate `raw/` or broad canonical registries directly
- Do not expand the intelligence layer just for completeness; add only contracts that reduce real ambiguity
- Do not let YAML become a second wiki; YAML stays contract-only
