# Roadmap

Updated: 2026-05-02

## Near-term

- keep `docs/` aligned whenever CLI surfaces, workbench routes, or truth boundaries change
- extend source-family coverage only through explicit manifest mappings plus tested parser support
- continue using the workbench as a bounded operator surface rather than a browser-owned authoring system
- keep strict LLM-first semantic workflows validator-backed and no-fallback
- keep `meta_surfaces.yaml` as the shared query/compile navigation contract
- use `proposal_review.py` for human-reviewed proposal application instead of automatic semantic page edits

## Next useful additions

- add more intelligence artifacts only where they reduce confusion:
  - route-level entities if the workbench surface grows materially
  - handler docs if cross-surface workflows become harder to follow
  - schema excerpts if canonical DuckDB or graph materialization contracts become operator-facing
- keep `scripts/validate_repo_docs_intelligence.py` aligned as docs/intelligence contracts evolve
- add `frontmatter.yaml` when proposal review/apply tooling becomes explicit
- keep the promoted `llm-wiki-bootstrap --profile llm-first-ontology` scaffold aligned with DocTology's stabilized contract set

## Known gaps

- the automated bootstrap implementation exists in the installed `llm-wiki-bootstrap` skill and defaults to `llm-first-ontology`
- only `docs/CURRENT_STATE.md` existed before this refresh, so the portal is still young
- the incremental ingest path is intentionally narrow and not yet a generic multi-family ingest framework
- the workbench route set is documented, but the frontend remains optional and sidecar-only
- bootstrap profile support is no longer deferred; future changes should be validated in DocTology before promotion into the reusable scaffold
