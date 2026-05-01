# Roadmap

Updated: 2026-05-02

## Near-term

- keep `docs/` aligned whenever CLI surfaces, workbench routes, or truth boundaries change
- extend source-family coverage only through explicit manifest mappings plus tested parser support
- continue using the workbench as a bounded operator surface rather than a browser-owned authoring system
- keep strict LLM-first semantic workflows validator-backed and no-fallback
- keep `meta_surfaces.yaml` as the shared query/compile navigation contract

## Next useful additions

- add more intelligence artifacts only where they reduce confusion:
  - route-level entities if the workbench surface grows materially
  - handler docs if cross-surface workflows become harder to follow
  - schema excerpts if canonical DuckDB or graph materialization contracts become operator-facing
- keep `scripts/validate_repo_docs_intelligence.py` aligned as docs/intelligence contracts evolve
- add `scripts/validate_workbench_manifest.py` to compare `workbench.yaml` routes/actions against `scripts/workbench/server.py`
- add `frontmatter.yaml` and `proposal_lifecycle.yaml` when proposal review/apply tooling becomes explicit
- promote the stabilized contract set into `llm-wiki-bootstrap --profile llm-first-ontology`

## Known gaps

- there is a repo docs/intelligence validator, but no dedicated workbench manifest validator yet
- only `docs/CURRENT_STATE.md` existed before this refresh, so the portal is still young
- the incremental ingest path is intentionally narrow and not yet a generic multi-family ingest framework
- the workbench route set is documented, but the frontend remains optional and sidecar-only
- bootstrap profile support remains intentionally deferred until the DocTology contract set is stable
